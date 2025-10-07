from typing import Iterator

from .tokens import Token, LPar, RPar, Star, Pipe, Character


class Tokenizer:
    def __init__(self, s: str) -> None:
        self.s = s

    def get_tokens(self) -> Iterator[Token]:
        i = 0
        while i < len(self.s):
            c = self.s[i]
            span = (i, i + 1)
            match c:
                case "(":
                    yield LPar(span)
                case ")":
                    yield RPar(span)
                case "*":
                    yield Star(span)
                case "|":
                    yield Pipe(span)
                case "." | "^" | "$" | "+" | "?" | "{" | "[":
                    raise NotImplementedError(f"Special character {c!r} is not implemented")  # TODO
                case "\\":
                    span = (i, i + 2)
                    try:
                        yield Character(span, self.s[i+1])
                    except IndexError:
                        raise ValueError("Unfinished escape sequence")
                case _:
                    yield Character(span, c)
            i = span[1]
