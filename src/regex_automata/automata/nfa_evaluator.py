from regex_automata.automata.nfa import NFA
from regex_automata.regex.flags import PatternFlag


class NFAEvaluator:
    def __init__(self, nfa: NFA, flags: PatternFlag = PatternFlag.NOFLAG) -> None:
        self.nfa = nfa
        self.states: set[int] = self.nfa.epsilon_closure({nfa.initial_state})
        self.flags = flags

    def accepts(self, s: str) -> bool:
        if self.flags & PatternFlag.IGNORECASE:
            s = s.lower()

        for c in s:
            self.step(ord(c))
        return len(self.states.intersection(self.nfa.final_states)) > 0

    def step(self, c: int) -> None:
        new_states = set()
        for u in self.states:
            u_transitions = self.nfa.transitions.get(u, {})
            for lrs, vs in u_transitions.items():
                if c in lrs.set:
                    new_states.update(vs)

        self.states = self.nfa.epsilon_closure(new_states)
