from copy import deepcopy
from dataclasses import dataclass
from typing import Self
from itertools import count

from .rangeset import RangeSet


@dataclass(frozen=True)
class TransitionPredicate:
    previous: RangeSet | None = None
    next: RangeSet | None = None

    @property
    def is_trivial(self) -> bool:
        return self.previous is None and self.next is None


@dataclass(frozen=True)
class Transition:
    predicates: tuple[TransitionPredicate, ...]
    consume_char: bool = True
    begin_group: int | None = None
    end_group: int | None = None
    label: str = ""

    def matches(self, c_previous: int, c_next: int) -> bool:
        for p in self.predicates:
            if p.next is not None and c_next not in p.next:
                continue
            if p.previous is not None and c_previous not in p.previous:
                continue
            return True
        return False

    @property
    def is_trivial_epsilon(self) -> bool:
        return (
            not self.consume_char and
            self.begin_group is None and
            self.end_group is None and
            all(p.is_trivial for p in self.predicates)
        )

    @classmethod
    def make_trivial_epsilon(cls) -> Self:
        return cls(predicates=(TransitionPredicate(),), consume_char=False, label="ε")

    @classmethod
    def make_begin_group(cls, number: int) -> Self:
        return cls(predicates=(TransitionPredicate(),), consume_char=False, label=f"⟨begin group {number}⟩",
                   begin_group=number)

    @classmethod
    def make_end_group(cls, number: int) -> Self:
        return cls(predicates=(TransitionPredicate(),), consume_char=False, label=f"⟨end group {number}⟩",
                   end_group=number)


@dataclass
class NFA:
    """
    Non-deterministic finite automaton (possibly with epsilon transitions)

    """
    states: list[int]
    initial_state: int
    final_states: set[int]
    transitions: dict[int, dict[Transition, set[int]]]

    def copy(self) -> "NFA":
        return deepcopy(self)

    def renumber_states(self, x0: int = 0) -> "NFA":
        f = dict(zip(self.states, count(x0)))
        return NFA(
            states=[f[x] for x in self.states],
            initial_state=f[self.initial_state],
            final_states={f[x] for x in self.final_states},
            transitions={
                f[x]: {p: {f[y] for y in ys} for p, ys in d.items()}
                for x, d in self.transitions.items()
            },
        )

    def epsilon_closure(self, states: set[int], c_previous: int, c_next: int) -> set[int]:
        closure = set(states)
        while True:
            new_closure = closure
            for u in closure:
                for p, vs in self.transitions.get(u, {}).items():
                    if not p.consume_char and p.matches(c_previous, c_next):
                        new_closure = new_closure | vs
            if len(closure) == len(new_closure):
                break
            closure = new_closure
        return closure

    def trivial_epsilon_closure(self, states: set[int]) -> set[int]:
        closure = set(states)
        while True:
            new_closure = closure
            for u in closure:
                for p, vs in self.transitions.get(u, {}).items():
                    if p.is_trivial_epsilon:
                        new_closure = new_closure | vs
            if len(closure) == len(new_closure):
                break
            closure = new_closure
        return closure

    def get_trivial_epsilon_free_nfa(self) -> "NFA":
        states = set(self.states)
        initial_state = self.initial_state
        final_states = set(self.final_states)
        transitions: dict[int, dict[Transition, set[int]]] = {}

        for u in self.states:
            closure = self.trivial_epsilon_closure({u})
            for v in closure:
                transitions_u = transitions.setdefault(u, {})
                for p, ws in self.transitions.get(v, {}).items():
                    if not p.is_trivial_epsilon:
                        transitions_u.setdefault(p, set()).update(ws)

                if v in self.final_states:
                    final_states.add(u)

        reachable_states = {initial_state}
        while True:
            new_reachable_states = set(reachable_states)
            for u in reachable_states:
                for vs in transitions.get(u, {}).values():
                    new_reachable_states.update(vs)
            if len(reachable_states) == len(new_reachable_states):
                break
            reachable_states = new_reachable_states

        for x in states - reachable_states:
            if x in transitions:
                transitions.pop(x)

            for u, transitions_u in transitions.items():
                for c, vs in list(transitions_u.items()):
                    if x in vs:
                        vs.remove(x)
                        if not vs:
                            transitions_u.pop(c)

        return NFA(
            states=list(sorted(reachable_states)),
            initial_state=initial_state,
            final_states=final_states,
            transitions=transitions,
        ).renumber_states()
