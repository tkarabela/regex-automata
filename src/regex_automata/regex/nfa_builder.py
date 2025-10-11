from ..parser.ast import AstNode, AstCharacter, AstConcatenation, AstUnion, AstIteration
from ..automata.nfa import NFA, LabeledRangeSet


class NFABuilder:
    def __init__(self, root: AstNode) -> None:
        self.root = root

    def build(self, epsilon_free: bool) -> NFA:
        nfa = self.convert(self.root)
        if epsilon_free:
            return nfa.get_epsilon_free_nfa()
        else:
            return nfa

    def convert(self, node: AstNode) -> NFA:
        match node:
            case AstCharacter(lrs):
                return NFA(
                    states=[0, 1],
                    initial_state=0,
                    final_states=[1],
                    transitions={0: {lrs: {1}}}
                )
            case AstIteration(u):
                nfa = self.convert(u)
                for x in nfa.final_states:
                    nfa.transitions.setdefault(x, {}).setdefault(LabeledRangeSet(), set()).add(nfa.initial_state)
                nfa.final_states = list(sorted(nfa.epsilon_closure(set(nfa.final_states))))
                return nfa
            case AstUnion(u, v):
                nfa_u = self.convert(u)
                nfa_v = self.convert(v).renumber_states(max(nfa_u.states) + 1)
                nfa = nfa_u.copy()
                nfa.states += nfa_v.states
                nfa.final_states += nfa_v.final_states
                nfa.transitions.update(nfa_v.transitions)
                new_initial_state = max(nfa.states) + 1
                nfa.states.append(new_initial_state)
                nfa.transitions[new_initial_state] = {LabeledRangeSet(): {nfa_u.initial_state, nfa_v.initial_state}}
                nfa.initial_state = new_initial_state
                return nfa
            case AstConcatenation(u, v):
                nfa_u = self.convert(u)
                nfa_v = self.convert(v).renumber_states(max(nfa_u.states) + 1)
                nfa = nfa_u.copy()
                nfa.states += nfa_v.states
                nfa.final_states = nfa_v.final_states
                nfa.transitions.update(nfa_v.transitions)
                for s in nfa_u.final_states:
                    nfa.transitions.setdefault(s, {}).setdefault(LabeledRangeSet(), set()).add(nfa_v.initial_state)
                return nfa
            case _:
                raise NotImplementedError(f"Cannot convert node {node!r}")
