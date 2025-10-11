from ..parser.ast import AstNode, AstCharacterSet, AstConcatenation, AstUnion, AstEmpty, AstIteration
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
            case AstEmpty():
                return self.convert_AstEmpty(node)
            case AstCharacterSet():
                return self.convert_AstCharacter(node)
            case AstIteration():
                return self.convert_AstIteration(node)
            case AstUnion():
                return self.convert_AstUnion(node)
            case AstConcatenation():
                return self.convert_AstConcatenation(node)
            case _:
                raise NotImplementedError(f"Cannot convert node {node!r}")

    def convert_AstEmpty(self, _: AstEmpty) -> NFA:
        return NFA(
            states=[0],
            initial_state=0,
            final_states=[0],
            transitions={}
        )

    def convert_AstCharacter(self, node: AstCharacterSet) -> NFA:
        return NFA(
            states=[0, 1],
            initial_state=0,
            final_states=[1],
            transitions={0: {node.lrs: {1}}}
        )

    def convert_AstIteration(self, node: AstIteration) -> NFA:
        u = node.u
        nfa = self.convert(u)

        for x in nfa.final_states:
            nfa.transitions.setdefault(x, {}).setdefault(LabeledRangeSet(), set()).add(nfa.initial_state)
        nfa.final_states = list(sorted(nfa.epsilon_closure(set(nfa.final_states))))
        return nfa

    def convert_AstUnion(self, node: AstUnion) -> NFA:
        u = node.u
        v = node.v
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

    def convert_AstConcatenation(self, node: AstConcatenation) -> NFA:
        u = node.u
        v = node.v
        nfa_u = self.convert(u)
        nfa_v = self.convert(v).renumber_states(max(nfa_u.states) + 1)

        nfa = nfa_u.copy()
        nfa.states += nfa_v.states
        nfa.final_states = nfa_v.final_states
        nfa.transitions.update(nfa_v.transitions)
        for s in nfa_u.final_states:
            nfa.transitions.setdefault(s, {}).setdefault(LabeledRangeSet(), set()).add(nfa_v.initial_state)
        return nfa
