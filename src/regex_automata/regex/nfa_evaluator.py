from dataclasses import dataclass
from typing import Iterator, Set

from regex_automata.automata.nfa import Transition
from regex_automata.regex.flags import PatternFlag
from regex_automata.regex.match import Match
from typing import TYPE_CHECKING

from ..common import root_logger

if TYPE_CHECKING:
    from .pattern import Pattern

logger = root_logger.getChild("evaluator")


@dataclass(frozen=True)
class GroupMatch:
    start: int
    end: int

    def to_span(self) -> tuple[int, int]:
        if self.end == -1:
            raise ValueError("cannot convert unfinished group to span")
        return self.start, self.end


@dataclass(frozen=True)
class Head:
    state: int
    start: int
    position: int
    groups: tuple[GroupMatch | None, ...] = ()

    def apply_transition(self, transition: Transition, next_state: int) -> "Head":
        head = self
        if transition.begin_group is not None:
            head = head._begin_group(transition.begin_group)
        if transition.end_group is not None:
            head = head._end_group(transition.end_group)
        return Head(
            next_state,
            head.start,
            head.position + (1 if transition.consume_char else 0),
            head.groups
        )

    def _begin_group(self, number: int) -> "Head":
        groups = list(self.groups)
        while len(groups) <= number:
            groups.append(None)
        m = groups[number]
        if m is not None and m.end == -1:
            raise ValueError(f"Group {number} has not been closed yet, cannot begin it again")
        groups[number] = GroupMatch(self.position, -1)
        return Head(
            self.state,
            self.start,
            self.position,
            tuple(groups)
        )

    def _end_group(self, number: int) -> "Head":
        groups = list(self.groups)
        if len(groups) < number:
            raise ValueError(f"Group {number} has never been opened, cannot close it")
        m = groups[number]
        if m is None:
            raise ValueError(f"Group {number} has never been opened, cannot close it")
        elif m.end != -1:
            raise ValueError(f"Group {number} has already been closed, cannot close it again")
        groups[number] = GroupMatch(m.start, self.position)
        return Head(
            self.state,
            self.start,
            self.position,
            tuple(groups)
        )

    @property
    def _ordering_tuple(self) -> tuple[int, int, int]:
        return self.start, self.state, self.position

    def __lt__(self, other: object) -> bool:
        if isinstance(other, Head):
            return self._ordering_tuple < other._ordering_tuple
        else:
            return NotImplemented

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Head):
            return self._ordering_tuple == other._ordering_tuple
        else:
            return NotImplemented

    def __ne__(self, other: object) -> bool:
        return not (self == other)

    def __le__(self, other: object) -> bool:
        return self == other or self < other

    def __gt__(self, other: object) -> bool:
        return not (self <= other)

    def __ge__(self, other: object) -> bool:
        return not (self < other)

    def get_groupspandict(self) -> dict[int, tuple[int, int]]:
        d = {}
        for i, m in enumerate(self.groups):
            if m is not None:
                d[i] = m.to_span()
        return d


class NFAEvaluator:
    def __init__(self, pattern: "Pattern", flags: PatternFlag = PatternFlag.NOFLAG) -> None:
        self.pattern = pattern
        self.nfa = pattern.nfa
        self.flags = flags
        if len(self.nfa.final_states) != 1:
            raise ValueError("Expected NFA with exactly one final state (end of group 0)")
        self.final_state = next(iter(self.nfa.final_states))

    def finditer(self, text: str, start: int = 0, end: int | None = None, search: bool = True) -> Iterator[Match]:
        original_text = text
        if self.flags & PatternFlag.IGNORECASE:
            text = text.lower()

        start_ = min(len(text), start)
        end_ = min(len(text), end if end is not None else len(text))
        last_match_position = -1
        buckets: dict[int, list[Head]] = {}

        for char_no, position in enumerate(range(start_, end_+1)):
            if position < end_:
                logger.info(f"{position=}, about to read {text[position]!r}")
            else:
                logger.info(f"{position=}, end of input")

            if position >= last_match_position and (char_no == 0 or (search and position <= end_)):
                queue = [self.init_head(position)]
                logger.info(f"\tadding bucket {queue=}")
                buckets[position] = queue

            for start, queue in list(buckets.items()):
                if not queue:
                    logger.info(f"\tprocessing bucket {start=}... empty, removing")
                    buckets.pop(start)
                    continue

                while True:
                    # do epsilon transitions
                    logger.info(f"\tprocessing bucket {start=}")
                    logger.info("\t\tepsilon transitions")
                    self.apply_epsilon_transitions(queue, text, start_, end_)
                    for head in queue:
                        logger.info(f"\t\t\t-> {head}")

                    # do character transitions
                    logger.info("\t\tcharacter transitions")
                    entered_final, left_final, final_heads = self.apply_character_transitions(queue, text, start_, end_)
                    for head in queue:
                        logger.info(f"\t\t\t-> {head}")

                    # do epsilon transitions
                    logger.info("\t\tepsilon transitions")
                    reentered_final = self.apply_epsilon_transitions(queue, text, start_, end_)
                    for head in queue:
                        logger.info(f"\t\t\t-> {head}")

                    if not entered_final:
                        break

                    if left_final and not reentered_final:
                        final_head = max(final_heads)
                        yield Match(
                            re=self.pattern,
                            pos=start_,
                            endpos=end_,
                            match=original_text[final_head.start:final_head.position],
                            groupspandict=final_head.get_groupspandict(),
                        )
                        logger.info(f">>>> found {final_head=} <<<<")

                        for start, queue in buckets.items():
                            if start < final_head.position:
                                logger.info(f"\tclearing bucket {start=} (less than {final_head.position=})")
                                queue.clear()
                                last_match_position = final_head.position

                        break
                    else:
                        logger.info("\tlooping due to entered_final")

        logger.info("all done")

    def init_head(self, position: int) -> Head:
        return Head(self.nfa.initial_state, position, position)

    def apply_epsilon_transitions(self, queue: list[Head], text: str, start_: int, end_: int) -> bool:
        next_heads = set()
        while queue:
            head = queue.pop()
            # logger.info(f"\t\tprocessing {head=}")
            c_previous, c_next = self.get_characters(text, start_, end_, head.position)
            next_heads.update(self._apply_epsilon_transitions(head, c_previous, c_next))
        entered_final = any(h.state == self.final_state for h in next_heads)
        queue.extend(sorted(next_heads))
        logger.info(f"\t\t\t-> {entered_final=}")
        return entered_final

    def _apply_epsilon_transitions(self, head: Head, c_previous: int, c_next: int) -> Set[Head]:
        closure = {head}
        while True:
            new_closure = closure
            for head in closure:
                for transition, next_states in self.nfa.transitions.get(head.state, {}).items():
                    if not transition.consume_char and transition.matches(c_previous, c_next):
                        new_closure = new_closure | {head.apply_transition(transition, next_state) for next_state in next_states}
            if len(closure) == len(new_closure):
                break
            closure = new_closure
        return closure

    def apply_character_transitions(self, queue: list[Head], text: str, start_: int, end_: int) -> tuple[bool, bool, set[Head]]:
        """-> entered_final, left_final, heads that were final before transition"""
        next_heads = set()
        final_heads = set()
        entered_final = False
        while queue:
            head = queue.pop()
            # logger.info(f"\t\tprocessing {head=}")
            if head.state == self.final_state:
                entered_final = True
                final_heads.add(head)
            c_previous, c_next = self.get_characters(text, start_, end_, head.position)
            if c_previous != -1 or c_next != -1:
                next_heads.update(self._apply_character_transitions(head, c_previous, c_next))
        queue.extend(sorted(next_heads))
        left_final = entered_final and all(h.state != self.final_state for h in queue)
        logger.info(f"\t\t\t-> {entered_final=}, {left_final=}, {final_heads=}")
        return entered_final, left_final, final_heads

    def _apply_character_transitions(self, head: Head, c_previous: int, c_next: int) -> Set[Head]:
        new_heads = set()
        for transition, next_states in self.nfa.transitions.get(head.state, {}).items():
            if transition.consume_char and transition.matches(c_previous, c_next):
                for next_state in next_states:
                    new_head = head.apply_transition(transition, next_state)
                    new_heads.add(new_head)

        return new_heads

    def get_characters(self, text: str, start_: int, end_: int, position: int) -> tuple[int, int]:
        prev_position = position - 1
        if start_ <= prev_position < end_:
            c_previous = ord(text[prev_position])
        else:
            c_previous = -1

        if start_ <= position < end_:
            c_next = ord(text[position])
        else:
            c_next = -1

        return c_previous, c_next
