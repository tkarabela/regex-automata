from .pattern import Pattern

__version__ = "0.1.0"


def fullmatch(pattern: str, s: str) -> bool:
    return Pattern(pattern).fullmatch(s)


def match(pattern: str, s: str) -> bool:
    return Pattern(pattern).match(s)


def search(pattern: str, s: str) -> bool:
    return Pattern(pattern).search(s)


def compile(pattern: str) -> Pattern:
    return Pattern(pattern)
