# ruff: noqa: E741
from typing import Iterator, Callable

from .regex.flags import PatternFlag as PatternFlag
from .regex.match import Match as Match
from .regex.pattern import Pattern as Pattern
from .common import root_logger as root_logger

__version__ = "0.3.0"


def fullmatch(pattern: str, s: str, flags: PatternFlag = PatternFlag.NOFLAG) -> Match | None:
    return Pattern(pattern, flags).fullmatch(s)


def match(pattern: str, s: str, flags: PatternFlag = PatternFlag.NOFLAG) -> Match | None:
    return Pattern(pattern, flags).match(s)


def search(pattern: str, s: str, flags: PatternFlag = PatternFlag.NOFLAG) -> Match | None:
    return Pattern(pattern, flags).search(s)


def finditer(pattern: str, s: str, flags: PatternFlag = PatternFlag.NOFLAG) -> Iterator[Match]:
    yield from Pattern(pattern, flags).finditer(s)


def compile(pattern: str, flags: PatternFlag = PatternFlag.NOFLAG, epsilon_free: bool = True) -> Pattern:
    return Pattern(pattern, flags, epsilon_free)


def findall(pattern: str, s: str, flags: PatternFlag = PatternFlag.NOFLAG) -> list[str | None] | list[tuple[str | None, ...]]:
    output = []
    for m in finditer(pattern, s, flags):
        match m.groups():
            case ():
                output.append(m.group(0))
            case (g,):
                output.append(g)
            case groups:
                output.append(groups)
    return output


def sub(pattern: str, repl: str | Callable[[Match], str], s: str, count: int = 0, flags: PatternFlag = PatternFlag.NOFLAG) -> str:
    return Pattern(pattern, flags).sub(repl, s, count)


def subn(pattern: str, repl: str | Callable[[Match], str], s: str, count: int = 0, flags: PatternFlag = PatternFlag.NOFLAG) -> tuple[str, int]:
    return Pattern(pattern, flags).subn(repl, s, count)


def split(pattern: str, s: str, maxsplit: int = 0, flags: PatternFlag = PatternFlag.NOFLAG) -> list[str | None]:
    numsplit = 0
    output: list[str | None] = []
    last_match_end = 0

    for m in finditer(pattern, s, flags):
        output.append(s[last_match_end:m.start()])
        output.extend(m.groups())
        numsplit += 1
        last_match_end = m.end()
        if maxsplit > 0 and numsplit == maxsplit:
            break

    output.append(s[last_match_end:])

    return output


NOFLAG = PatternFlag.NOFLAG
IGNORECASE = PatternFlag.IGNORECASE
DOTALL = PatternFlag.DOTALL
MULTILINE = PatternFlag.MULTILINE
I = PatternFlag.I
S = PatternFlag.S
M = PatternFlag.M
