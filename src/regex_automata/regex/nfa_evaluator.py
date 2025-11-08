from typing import Iterator

from regex_automata.automata.nfa import NFA
from regex_automata.regex.flags import PatternFlag
from regex_automata.regex.match import Match


class NFAEvaluator:
    class Head:
        def __init__(self, evaluator: "NFAEvaluator", start: int) -> None:
            self.start = start
            self.evaluator = evaluator
            self.states: set[int] = set(self.evaluator.initial_states)
            self.entered_final = bool(self.states & self.evaluator.final_states)
            self.left_final = False

        def step_epsilon(self, c_previous: int, c_next: int) -> None:
            self.states = new_states = self._step_epsilon(c_previous, c_next, self.states)
            new_in_final = bool(new_states & self.evaluator.final_states)
            self.entered_final = self.entered_final or new_in_final
            self.left_final = self.entered_final and not new_in_final

        def _step_epsilon(self, c_previous: int, c_next: int, states: set[int]) -> set[int]:
            return self.evaluator.nfa.epsilon_closure(states, c_previous, c_next)

        def step_read(self, c_previous: int, c_next: int) -> None:
            self.states = new_states = self._step_read(c_previous, c_next, self.states)
            new_in_final = bool(new_states & self.evaluator.final_states)
            self.entered_final = self.entered_final or new_in_final
            self.left_final = self.entered_final and not new_in_final

        def _step_read(self, c_previous: int, c_next: int, states: set[int]) -> set[int]:
            assert c_next != -1
            new_states = set()
            for u in states:
                u_transitions = self.evaluator.nfa.transitions.get(u, {})
                for p, vs in u_transitions.items():
                    if p.consume_char and p.matches(c_previous, c_next):
                        new_states.update(vs)

            return new_states

        def __repr__(self) -> str:
            return f"<Head {self.start=} {self.states=} {self.entered_final=} {self.left_final=}>"

    def __init__(self, nfa: NFA, flags: PatternFlag = PatternFlag.NOFLAG) -> None:
        self.nfa = nfa
        self.initial_states = self.nfa.trivial_epsilon_closure({self.nfa.initial_state})
        self.heads: list["NFAEvaluator.Head"] = []
        self.flags = flags
        self.final_states = set(self.nfa.final_states)

    def finditer(self, text: str, start: int = 0, end: int | None = None, search: bool = True) -> Iterator[Match]:
        if self.flags & PatternFlag.IGNORECASE:
            text = text.lower()

        end_ = end if end is not None else len(text)

        self.heads.append(self.Head(self, min(len(text), start)))

        c_previous = -1
        for char_no, i in enumerate(range(min(len(text), start), min(len(text), end_))):
            match_at_position = False
            if search and char_no > 0:
                self.heads.append(self.Head(self, i))

            c_next = ord(text[i])

            for head in self.heads:
                head.step_epsilon(c_previous, c_next)
                if not match_at_position and head.left_final:
                    self.purge_heads(i-1)
                    yield Match.from_span_and_text(head.start, i-1, text)
                    match_at_position = True  # avoid returning multiple matches

            for head in self.heads:
                head.step_read(c_previous, c_next)
                if not match_at_position and head.left_final:
                    self.purge_heads(i)
                    yield Match.from_span_and_text(head.start, i, text)
                    match_at_position = True

            c_previous = c_next

        c_next = -1
        for head in self.heads:
            head.step_epsilon(c_previous, c_next)

            if head.entered_final and not head.left_final:
                yield Match.from_span_and_text(head.start, end_, text)
                return

    def purge_heads(self, start_min: int) -> None:
        self.heads = [h for h in self.heads if h.start >= start_min]
