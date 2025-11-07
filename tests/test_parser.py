import pytest

from regex_automata.automata.rangeset import RangeSet
from regex_automata.errors import TokenizerError
from regex_automata.parser.ast import AstUnion, AstCharacterSet, AstConcatenation
from regex_automata.parser.parser import Parser
from regex_automata.parser.tokenizer import Tokenizer


@pytest.mark.parametrize("pattern", ["a", "aa", "aaa", "a|b", "a|b|c", "(a)(b)(c)", "a*", "(a)", "(a*)", "(a*)*",
                                     "(a|bc*)*", "lo*l", "foo|(bar|baz)|quux"])
def test_parse_regex(pattern: str):
    tokens = list(Tokenizer(pattern).get_tokens())
    Parser(tokens).parse()


def _ast_character_set(s: str) -> AstCharacterSet:
    return AstCharacterSet(RangeSet(map(ord, s)), s)


def test_parse_tree_union():
    tokens = list(Tokenizer("ab|cd").get_tokens())
    assert Parser(tokens).parse() == AstUnion(
        AstConcatenation(_ast_character_set("a"), _ast_character_set("b")),
        AstConcatenation(_ast_character_set("c"), _ast_character_set("d")),
    )


def test_parse_tree_union_parens():
    tokens = list(Tokenizer("ab|(cd|ef)|gh").get_tokens())
    assert Parser(tokens).parse() == AstUnion(
        AstConcatenation(_ast_character_set("a"), _ast_character_set("b")),
        AstUnion(
            AstUnion(
                AstConcatenation(_ast_character_set("c"), _ast_character_set("d")),
                AstConcatenation(_ast_character_set("e"), _ast_character_set("f")),
            ),
            AstConcatenation(_ast_character_set("g"), _ast_character_set("h")),
        )
    )


@pytest.mark.parametrize("pattern", ["\\", "[a", "[a-bc-", "[]",
                                     "{", "{123", "{123,", "{,123", "{,123,}", "{123,456,}"])
def test_tokenizer_errors_in_pattern_malformed(pattern):
    with pytest.raises(TokenizerError):
        list(Tokenizer(pattern).get_tokens())
