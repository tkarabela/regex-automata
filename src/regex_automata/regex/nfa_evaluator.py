from dataclasses import dataclass
from typing import Iterator, Self, Iterable, Set

from regex_automata.automata.nfa import NFA, Transition
from regex_automata.regex.flags import PatternFlag
from regex_automata.regex.match import Match


@dataclass(frozen=True)
class GroupMatch:
    start: int
    end: int


@dataclass(frozen=True)
class Head:
    state: int
    start: int
    position: int
    groups: tuple[GroupMatch | None, ...] = ()

    def apply_transition(self, transition: Transition, next_state: int) -> Self:
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

    def _begin_group(self, number: int) -> Self:
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

    def _end_group(self, number: int) -> Self:
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


class NFAEvaluator:
    def __init__(self, nfa: NFA, flags: PatternFlag = PatternFlag.NOFLAG) -> None:
        self.nfa = nfa
        self.flags = flags
        if len(nfa.final_states) != 1:
            raise ValueError("Expected NFA with exactly one final state (end of group 0)")
        self.final_state = next(iter(nfa.final_states))

    def finditer(self, text: str, start: int = 0, end: int | None = None, search: bool = True) -> Iterator[Match]:
        original_text = text
        if self.flags & PatternFlag.IGNORECASE:
            text = text.lower()

        end_ = end if end is not None else len(text)

        heads = {self.init_head(min(len(text), start))}

        c_previous = -1
        for char_no, i in enumerate(range(min(len(text), start), min(len(text), end_))):
            print("finditer", char_no, i)
            print(heads)
            if search and char_no > 0:
                heads.add(self.init_head(i))

            c_next = ord(text[i])

            # do epsilon transitions
            print("do epsilon transitions")
            heads = self.apply_epsilon_transitions(heads, c_previous, c_next)
            print(heads)
            yield from self.iter_matches_from_heads(heads, original_text)

            # do character transitions
            print("do character transitions")
            heads = self.apply_character_transitions(heads, c_previous, c_next)
            print(heads)
            yield from self.iter_matches_from_heads(heads, original_text)

            c_previous = c_next

        print("finished reading input, doing final epsilon transitions")
        c_next = -1
        # do epsilon transitions
        heads = self.apply_epsilon_transitions(heads, c_previous, c_next)
        print(heads)
        yield from self.iter_matches_from_heads(heads, original_text)

    def init_head(self, position: int) -> Head:
        return Head(self.nfa.initial_state, position, position)

    def apply_epsilon_transitions(self, heads: Iterable[Head], c_previous: int, c_next: int) -> Set[Head]:
        closure = set(heads)
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

    def apply_character_transitions(self, heads: Iterable[Head], c_previous: int, c_next: int) -> Set[Head]:
        new_heads = set()
        for head in heads:
            for transition, next_states in self.nfa.transitions.get(head.state, {}).items():
                if transition.consume_char and transition.matches(c_previous, c_next):
                    for next_state in next_states:
                        new_head = head.apply_transition(transition, next_state)
                        new_heads.add(new_head)

        return new_heads

    def iter_matches_from_heads(self, heads: Iterable[Head], text: str) -> Iterator[Match]:
        for head in sorted(heads, key=lambda h: (h.start, -h.position)):
            if head.state == self.final_state:
                yield Match.from_span_and_text(head.start, head.position, text)
