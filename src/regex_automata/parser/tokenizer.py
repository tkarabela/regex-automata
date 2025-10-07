from typing import Iterator

from .tokens import Token, LPar, RPar, Star, Pipe, Character


class Tokenizer:
    def __init__(self, s: str) -> None:
        self.s = s

    def get_tokens(self) -> Iterator[Token]:
        for i, c in enumerate(self.s):
            span = (i, i+1)
            match c:
                case "(":
                    yield LPar(span)
                case ")":
                    yield RPar(span)
                case "*":
                    yield Star(span)
                case "|":
                    yield Pipe(span)
                case _:
                    yield Character(span, c)
