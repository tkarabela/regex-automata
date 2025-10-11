import pytest

from regex_automata.automata.nfa import LabeledRangeSet
from regex_automata.automata.rangeset import RangeSet
from regex_automata.errors import TokenizerError
from regex_automata.parser.ast import AstUnion, AstCharacter, AstConcatenation
from regex_automata.parser.parser import Parser
from regex_automata.parser.tokenizer import Tokenizer


@pytest.mark.parametrize("pattern", ["a", "aa", "aaa", "a|b", "a|b|c", "(a)(b)(c)", "a*", "(a)", "(a*)", "(a*)*",
                                     "(a|bc*)*", "lo*l", "foo|(bar|baz)|quux"])
def test_parse_regex(pattern: str):
    tokens = list(Tokenizer(pattern).get_tokens())
    Parser(tokens).parse()


def _lrs(s: str) -> LabeledRangeSet:
    return LabeledRangeSet(RangeSet(map(ord, s)), s)


def test_parse_tree_union():
    tokens = list(Tokenizer("ab|cd").get_tokens())
    assert Parser(tokens).parse() == AstUnion(
        AstConcatenation(AstCharacter(_lrs("a")), AstCharacter(_lrs("b"))),
        AstConcatenation(AstCharacter(_lrs("c")), AstCharacter(_lrs("d"))),
    )

def test_parse_tree_union_parens():
    tokens = list(Tokenizer("ab|(cd|ef)|gh").get_tokens())
    assert Parser(tokens).parse() == AstUnion(
        AstConcatenation(AstCharacter(_lrs("a")), AstCharacter(_lrs("b"))),
        AstUnion(
            AstUnion(
                AstConcatenation(AstCharacter(_lrs("c")), AstCharacter(_lrs("d"))),
                AstConcatenation(AstCharacter(_lrs("e")), AstCharacter(_lrs("f"))),
            ),
            AstConcatenation(AstCharacter(_lrs("g")), AstCharacter(_lrs("h"))),
        )
    )

@pytest.mark.parametrize("pattern", ["a?", "a+", "a{1,3}", "a{1,}", "a{,3}", "^foo", "bar$"])
def test_tokenizer_errors_in_pattern_unsupported(pattern):
    with pytest.raises(TokenizerError):
        list(Tokenizer(pattern).get_tokens())


@pytest.mark.parametrize("pattern", ["\\", "[a", "[a-bc-", "[]"])
def test_tokenizer_errors_in_pattern_malformed(pattern):
    with pytest.raises(TokenizerError):
        list(Tokenizer(pattern).get_tokens())
