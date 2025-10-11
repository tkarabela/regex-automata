from regex_automata.automata.nfa import NFA
from regex_automata.regex.flags import PatternFlag
from regex_automata.regex.match import Match


class NFAEvaluator:
    def __init__(self, nfa: NFA, flags: PatternFlag = PatternFlag.NOFLAG) -> None:
        self.nfa = nfa
        self.states: set[int] = self.nfa.epsilon_closure({nfa.initial_state})
        self.flags = flags
        self.initial_states = self.nfa.epsilon_closure({self.nfa.initial_state})
        self.final_states = set(self.nfa.final_states)

    def match(self, text: str, start: int = 0, end: int | None = None) -> Match | None:
        if self.flags & PatternFlag.IGNORECASE:
            text = text.lower()

        end_ = end if end is not None else len(text)

        entered_final = bool(self.states & self.final_states)
        left_final = False

        for i in range(start, end_):
            c = text[i]
            new_states = self.step(ord(c), self.states)
            new_in_final = bool(new_states & self.final_states)
            entered_final = entered_final or new_in_final
            left_final = entered_final and not new_in_final

            if left_final:
                return Match.from_span_and_text(start, i, text)

            self.states = new_states

        if entered_final and not left_final:
            return Match.from_span_and_text(start, end_, text)
        else:
            return None

    def step(self, c: int, states: set[int]) -> set[int]:
        new_states = set()
        for u in states:
            u_transitions = self.nfa.transitions.get(u, {})
            for lrs, vs in u_transitions.items():
                if c in lrs.set:
                    new_states.update(vs)

        return self.nfa.epsilon_closure(new_states)
