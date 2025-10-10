from .regex.flags import PatternFlag
from .regex.match import Match
from .regex.pattern import Pattern

__version__ = "0.1.0"


def fullmatch(pattern: str, s: str, flags: PatternFlag = PatternFlag.NOFLAG) -> Match | None:
    return Pattern(pattern, flags).fullmatch(s)


def match(pattern: str, s: str, flags: PatternFlag = PatternFlag.NOFLAG) -> Match | None:
    return Pattern(pattern, flags).match(s)


def search(pattern: str, s: str, flags: PatternFlag = PatternFlag.NOFLAG) -> Match | None:
    return Pattern(pattern, flags).search(s)


def compile(pattern: str, flags: PatternFlag = PatternFlag.NOFLAG, epsilon_free: bool = True) -> Pattern:
    return Pattern(pattern, flags, epsilon_free)


NOFLAG = PatternFlag.NOFLAG
IGNORECASE = PatternFlag.IGNORECASE
DOTALL = PatternFlag.DOTALL
I = PatternFlag.I
S = PatternFlag.S
