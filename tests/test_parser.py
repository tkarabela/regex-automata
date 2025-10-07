import pytest

from regex_automata.parser.ast import AstUnion, AstCharacter, AstConcatenation
from regex_automata.parser.parser import Parser
from regex_automata.parser.tokenizer import Tokenizer


@pytest.mark.parametrize("pattern", ["a", "aa", "aaa", "a|b", "a|b|c", "(a)(b)(c)", "a*", "(a)", "(a*)", "(a*)*",
                                     "(a|bc*)*", "lo*l", "foo|(bar|baz)|quux"])
def test_parse_regex(pattern: str):
    tokens = list(Tokenizer(pattern).get_tokens())
    Parser(tokens).parse()


def test_parse_tree_union():
    tokens = list(Tokenizer("ab|cd").get_tokens())
    assert Parser(tokens).parse() == AstUnion(
        AstConcatenation(AstCharacter("a"), AstCharacter("b")),
        AstConcatenation(AstCharacter("c"), AstCharacter("d")),
    )

def test_parse_tree_union_parens():
    tokens = list(Tokenizer("ab|(cd|ef)|gh").get_tokens())
    assert Parser(tokens).parse() == AstUnion(
        AstConcatenation(AstCharacter("a"), AstCharacter("b")),
        AstUnion(
            AstUnion(
                AstConcatenation(AstCharacter("c"), AstCharacter("d")),
                AstConcatenation(AstCharacter("e"), AstCharacter("f")),
            ),
            AstConcatenation(AstCharacter("g"), AstCharacter("h")),
        )
    )
