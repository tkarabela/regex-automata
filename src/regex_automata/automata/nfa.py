from dataclasses import dataclass
from typing import Self, Any
import json
from abc import ABC, abstractmethod
from itertools import count

from ..common import PathOrStr


class FiniteAutomaton(ABC):
    """Base class for finite automata"""
    @abstractmethod
    def accepts(self, s: str) -> bool:
        raise NotImplementedError

    @classmethod
    def from_file(cls, path: PathOrStr) -> Self:
        with open(path) as fp:
            data = json.load(fp)
            return cls.from_dict(data)

    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        raise NotImplementedError

    def to_file(self, path: PathOrStr) -> None:
        data = self.to_dict()
        with open(path, "w") as fp:
            json.dump(data, fp, indent=4)

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        raise NotImplementedError


@dataclass
class NFA(FiniteAutomaton):
    """
    Non-deterministic finite automaton

    Bonus I: support epsilon transitions (transition that "reads empty string") - DONE
    """
    states: list[int]
    initial_state: int
    final_states: list[int]
    transitions: dict[int, dict[str, set[int]]]

    class Evaluator:
        def __init__(self, nfa: "NFA") -> None:
            self.nfa = nfa
            self.states: set[int] = self.nfa.epsilon_closure({nfa.initial_state})

        def step(self, c: str) -> None:
            new_states = set()
            for u in self.states:
                new_states.update(self.nfa.transitions.get(u, {}).get(c, set()))

            self.states = self.nfa.epsilon_closure(new_states)

    def accepts(self, s: str) -> bool:
        evaluator = self.Evaluator(self)
        for c in s:
            evaluator.step(c)
        return len(evaluator.states.intersection(self.final_states)) > 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        transitions: dict[int, dict[str, set[int]]] = {}
        for u, c, v in data["transitions"]:
            transitions.setdefault(u, {}).setdefault(c, set()).add(v)

        return cls(
            states=data["states"],
            initial_state=data["initial_state"],
            final_states=data["final_states"],
            transitions=transitions,
        )

    def to_dict(self) -> dict[str, Any]:
        transitions = []
        for u, tmp in self.transitions.items():
            for c, vs in tmp.items():
                for v in vs:
                    transitions.append([u, c, v])

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
                f[x]: {c: {f[y] for y in ys} for c, ys in d.items()}
                for x, d in self.transitions.items()
            },
        )

    def epsilon_closure(self, states: set[int]) -> set[int]:
        closure = set(states)
        while True:
            new_closure = closure
            for u in closure:
                new_closure = new_closure | self.transitions.get(u, {}).get("", set())
            if len(closure) == len(new_closure):
                break
            closure = new_closure
        return closure

    def get_epsilon_free_nfa(self) -> "EpsilonFreeNFA":
        states = set(self.states)
        initial_state = self.initial_state
        final_states = set(self.final_states)
        transitions: dict[int, dict[str, set[int]]] = {}

        for u in self.states:
            closure = self.epsilon_closure({u})
            for v in closure:
                transitions_u = transitions.setdefault(u, {})
                for c, ws in self.transitions.get(v, {}).items():
                    if c != "":
                        transitions_u.setdefault(c, set()).update(ws)

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
