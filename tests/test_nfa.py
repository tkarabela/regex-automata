from pathlib import PurePath

import pytest

from regex_automata.automata.nfa import FiniteAutomaton, NFA

DATA_DIR = PurePath(__file__).parent / "data"

def _test_lol_strings(automaton: FiniteAutomaton):
    assert automaton.accepts("lol")
    assert automaton.accepts("lool")
    assert automaton.accepts("olool")
    assert not automaton.accepts("ololol")
    assert not automaton.accepts("lolo")
    assert not automaton.accepts("xyz")
    assert automaton.accepts("l" + 1000*"o" +"l")


def test_nfa_input():
    nfa = NFA.from_file(DATA_DIR / "lol_nfa.json")
    _test_lol_strings(nfa)


def test_nfa_with_epsilon_transitions_input():
    nfa = NFA.from_file(DATA_DIR / "lol_nfa_epsilon.json")
    _test_lol_strings(nfa)


@pytest.mark.parametrize("filename", ["lol_nfa.json", "lol_nfa_epsilon.json"])
def test_serialization_dfa(tmp_path, filename: str):
    automaton = NFA.from_file(DATA_DIR / filename)
    _test_lol_strings(automaton)
    automaton.to_file(tmp_path / filename)
    automaton2 = NFA.from_file(tmp_path / filename)
    _test_lol_strings(automaton2)
