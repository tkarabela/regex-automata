from dataclasses import dataclass
from typing import Self, Any
import json
from itertools import count

from .rangeset import RangeSet
from ..common import PathOrStr


@dataclass(frozen=True)
class LabeledRangeSet:
    set: RangeSet = RangeSet()
    label: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "set": self.set.to_dict(),
            "label": self.label,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Self:
        return cls(
            set=RangeSet.from_dict(d.get("set", {})),
            label=d.get("label", ""),
        )


@dataclass
class NFA:
    """
    Non-deterministic finite automaton (possibly with epsilon transitions)

    """
    states: list[int]
    initial_state: int
    final_states: list[int]
    transitions: dict[int, dict[LabeledRangeSet, set[int]]]

    @classmethod
    def from_file(cls, path: PathOrStr) -> Self:
        with open(path) as fp:
            data = json.load(fp)
            return cls.from_dict(data)

    def to_file(self, path: PathOrStr) -> None:
        data = self.to_dict()
        with open(path, "w") as fp:
            json.dump(data, fp, indent=4)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        transitions: dict[int, dict[LabeledRangeSet, set[int]]] = {}
        for u, lrs_, v in data["transitions"]:
            lrs = LabeledRangeSet.from_dict(lrs_)
            transitions.setdefault(u, {}).setdefault(lrs, set()).add(v)

        return cls(
            states=data["states"],
            initial_state=data["initial_state"],
            final_states=data["final_states"],
            transitions=transitions,
        )

    def to_dict(self) -> dict[str, Any]:
        transitions = []
        for u, tmp in self.transitions.items():
            for lrs, vs in tmp.items():
                for v in vs:
                    transitions.append([u, lrs.to_dict(), v])

        return {
            "states": self.states,
            "initial_state": self.initial_state,
            "final_states": self.final_states,
            "transitions": transitions,
        }

    def copy(self) -> "NFA":
        return self.from_dict(self.to_dict())

    def renumber_states(self, x0: int) -> "NFA":
        f = dict(zip(self.states, count(x0)))
        return NFA(
            states=[f[x] for x in self.states],
            initial_state=f[self.initial_state],
            final_states=[f[x] for x in self.final_states],
            transitions={
                f[x]: {lrs: {f[y] for y in ys} for lrs, ys in d.items()}
                for x, d in self.transitions.items()
            },
        )

    def epsilon_closure(self, states: set[int]) -> set[int]:
        closure = set(states)
        while True:
            new_closure = closure
            for u in closure:
                new_closure = new_closure | self.transitions.get(u, {}).get(LabeledRangeSet(), set())
            if len(closure) == len(new_closure):
                break
            closure = new_closure
        return closure

    def get_epsilon_free_nfa(self) -> "EpsilonFreeNFA":
        states = set(self.states)
        initial_state = self.initial_state
        final_states = set(self.final_states)
        transitions: dict[int, dict[LabeledRangeSet, set[int]]] = {}

        for u in self.states:
            closure = self.epsilon_closure({u})
            for v in closure:
                transitions_u = transitions.setdefault(u, {})
                for lrs, ws in self.transitions.get(v, {}).items():
                    if not lrs.set.empty:
                        transitions_u.setdefault(lrs, set()).update(ws)

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

        return EpsilonFreeNFA(
            states=list(sorted(reachable_states)),
            initial_state=initial_state,
            final_states=list(sorted(final_states)),
            transitions=transitions,
        )


@dataclass
class EpsilonFreeNFA(NFA):
    def epsilon_closure(self, states: set[int]) -> set[int]:
        return states
