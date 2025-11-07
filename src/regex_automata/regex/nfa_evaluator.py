from regex_automata.automata.nfa import NFA
from regex_automata.regex.flags import PatternFlag
from regex_automata.regex.match import Match


class NFAEvaluator:
    def __init__(self, nfa: NFA, flags: PatternFlag = PatternFlag.NOFLAG) -> None:
        self.nfa = nfa
        self.states: set[int] = self.nfa.trivial_epsilon_closure({nfa.initial_state})
        self.flags = flags
        self.initial_states = self.nfa.trivial_epsilon_closure({self.nfa.initial_state})
        self.final_states = set(self.nfa.final_states)

    def match(self, text: str, start: int = 0, end: int | None = None) -> Match | None:
        if self.flags & PatternFlag.IGNORECASE:
            text = text.lower()

        end_ = end if end is not None else len(text)

        entered_final = bool(self.states & self.final_states)
        left_final = False

        c_previous = -1
        for i in range(min(len(text), start), min(len(text), end_)):
            c_next = ord(text[i])

            new_states = self.step_epsilon(c_previous, c_next, self.states)
            new_in_final = bool(new_states & self.final_states)
            entered_final = entered_final or new_in_final
            left_final = entered_final and not new_in_final
            if left_final:
                return Match.from_span_and_text(start, i, text)
            self.states = new_states

            new_states = self.step_read(c_previous, c_next, self.states)
            new_in_final = bool(new_states & self.final_states)
            entered_final = entered_final or new_in_final
            left_final = entered_final and not new_in_final
            if left_final:
                return Match.from_span_and_text(start, i, text)
            self.states = new_states

            c_previous = c_next

        c_next = -1
        new_states = self.step_epsilon(c_previous, c_next, self.states)
        new_in_final = bool(new_states & self.final_states)
        entered_final = entered_final or new_in_final
        left_final = entered_final and not new_in_final

        if entered_final and not left_final:
            return Match.from_span_and_text(start, end_, text)
        else:
            return None

    def step_epsilon(self, c_previous: int, c_next: int, states: set[int]) -> set[int]:
        return self.nfa.epsilon_closure(states, c_previous, c_next)

    def step_read(self, c_previous: int, c_next: int, states: set[int]) -> set[int]:
        assert c_next != -1
        new_states = set()
        for u in states:
            u_transitions = self.nfa.transitions.get(u, {})
            for p, vs in u_transitions.items():
                if p.consume_char and p.matches(c_previous, c_next):
                    new_states.update(vs)

        return new_states
