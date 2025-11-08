from ..automata.rangeset import RangeSet, WORD_RANGESET, NONWORD_RANGESET
from ..parser.ast import AstNode, AstCharacterSet, AstConcatenation, AstUnion, AstEmpty, AstIteration, \
    AstBoundaryAssertion, AstGroup
from ..automata.nfa import NFA, Transition, TransitionPredicate
from ..parser.tokens import BoundaryAssertionSemantic


class NFABuilder:
    def __init__(self, root: AstNode) -> None:
        self.root = root

    def build(self, epsilon_free: bool) -> NFA:
        nfa = self.convert(self.root)
        if epsilon_free:
            return nfa.get_trivial_epsilon_free_nfa()
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
            case AstBoundaryAssertion():
                return self.covert_AstBoundaryAssertion(node)
            case AstGroup():
                return self.convert_AstGroup(node)
            case _:
                raise NotImplementedError(f"Cannot convert node {node!r}")

    def convert_AstEmpty(self, _: AstEmpty) -> NFA:
        return NFA(
            states=[0],
            initial_state=0,
            final_states={0},
            transitions={}
        )

    def convert_AstCharacter(self, node: AstCharacterSet) -> NFA:
        return NFA(
            states=[0, 1],
            initial_state=0,
            final_states={1},
            transitions={0: {Transition(predicates=(TransitionPredicate(next=node.rs),), label=node.label): {1}}}
        )

    def convert_AstIteration(self, node: AstIteration) -> NFA:
        u = node.u
        nfa = self.convert(u)

        for x in nfa.final_states:
            nfa.transitions.setdefault(x, {}).setdefault(Transition.make_trivial_epsilon(), set()).add(nfa.initial_state)
        nfa.final_states = nfa.trivial_epsilon_closure(set(nfa.final_states))
        return nfa

    def convert_AstUnion(self, node: AstUnion) -> NFA:
        u = node.u
        v = node.v
        nfa_u = self.convert(u)
        nfa_v = self.convert(v).renumber_states(max(nfa_u.states) + 1)

        nfa = nfa_u.copy()
        nfa.states += nfa_v.states
        nfa.final_states |= nfa_v.final_states
        nfa.transitions.update(nfa_v.transitions)
        new_initial_state = max(nfa.states) + 1
        nfa.states.append(new_initial_state)
        nfa.transitions[new_initial_state] = {Transition.make_trivial_epsilon(): {nfa_u.initial_state, nfa_v.initial_state}}
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
            nfa.transitions.setdefault(s, {}).setdefault(Transition.make_trivial_epsilon(), set()).add(nfa_v.initial_state)
        return nfa

    def covert_AstBoundaryAssertion(self, node: AstBoundaryAssertion) -> NFA:
        eof_rs = RangeSet((-1,))
        eof_or_newline_rs = RangeSet((-1, ord("\n")))

        match node.semantic:
            case BoundaryAssertionSemantic.INPUT_START:
                transition = Transition(
                    predicates=(TransitionPredicate(previous=eof_rs),),
                    consume_char=False,
                    label="input start"
                )
            case BoundaryAssertionSemantic.INPUT_END:
                transition = Transition(
                    predicates=(TransitionPredicate(next=eof_rs),),
                    consume_char=False,
                    label="input end"
                )
            case BoundaryAssertionSemantic.LINE_START:
                transition = Transition(
                    predicates=(TransitionPredicate(previous=eof_or_newline_rs),),
                    consume_char=False,
                    label="line start"
                )
            case BoundaryAssertionSemantic.LINE_END:
                transition = Transition(
                    predicates=(TransitionPredicate(next=eof_or_newline_rs),),
                    consume_char=False,
                    label="line end"
                )
            case BoundaryAssertionSemantic.WORD_BOUNDARY:
                transition = Transition(
                    predicates=(
                        TransitionPredicate(WORD_RANGESET, NONWORD_RANGESET),
                        TransitionPredicate(WORD_RANGESET, eof_rs),
                        TransitionPredicate(NONWORD_RANGESET, WORD_RANGESET),
                        TransitionPredicate(eof_rs, WORD_RANGESET),
                    ),
                    consume_char=False,
                    label="\\b"
                )
            case BoundaryAssertionSemantic.NONWORD_BOUNDARY:
                transition = Transition(
                    predicates=(
                        TransitionPredicate(WORD_RANGESET, WORD_RANGESET),
                        TransitionPredicate(NONWORD_RANGESET, NONWORD_RANGESET),
                        TransitionPredicate(NONWORD_RANGESET, eof_rs),
                        TransitionPredicate(eof_rs, NONWORD_RANGESET),
                    ),consume_char=False,
                    label="\\B"
                )
            case _:
                raise NotImplementedError

        return NFA(
            states=[0, 1],
            initial_state=0,
            final_states={1},
            transitions={0: {transition: {1}}}
        )

    def convert_AstGroup(self, node: AstGroup) -> NFA:
        nfa_u = self.convert(node.u).renumber_states(1)

        start_state = 0
        final_state = max(nfa_u.states) + 1

        nfa = nfa_u.copy()
        nfa.initial_state = start_state
        nfa.states += [start_state, final_state]
        nfa.final_states = {final_state}
        nfa.transitions[start_state] = {Transition.make_begin_group(node.number): {nfa_u.initial_state}}
        for s in nfa_u.final_states:
            nfa.transitions.setdefault(s, {}).setdefault(Transition.make_end_group(node.number), set()).add(final_state)
        return nfa
