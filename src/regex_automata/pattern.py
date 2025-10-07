from .regex.regex import Regex


class Pattern:
    def __init__(self, pattern: str) -> None:
        self.pattern = pattern
        self._regex = Regex.from_pattern(pattern)

    def fullmatch(self, s: str) -> bool:
        return self._regex.fullmatch(s)

    def match(self, s: str) -> bool:
        return self._regex.match(s)

    def search(self, s: str) -> bool:
        return self._regex.search(s)
