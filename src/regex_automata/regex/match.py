from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .pattern import Pattern


@dataclass(repr=False)
class Match:
    re: "Pattern"
    pos: int | None
    endpos: int | None
    match: str
    groupspandict: dict[int, tuple[int, int]]

    def group(self, *indices: int) -> (str | None) | tuple[str | None, ...]:
        match len(indices):
            case 0:
                return self._group(0)
            case 1:
                return self._group(indices[0])
            case _:
                return tuple(map(self._group, indices))

    def _group(self, i: int) -> str | None:
        start, end = self.span(i)
        if start == -1:
            return None
        else:
            match_start = self.start()
            return self.match[start - match_start : end - match_start]

    def groupdict(self) -> dict[int, str | None]:
        return {i: self._group(i) for i in self.groupspandict}

    def span(self, i: int = 0) -> tuple[int, int]:
        return self.groupspandict.get(i, (-1, -1))

    def start(self, i: int = 0) -> int:
        return self.span(i)[0]

    def end(self, i: int = 0) -> int:
        return self.span(i)[1]

    def __getitem__(self, i: int) -> str | None:
        return self._group(i)

    @property
    def string(self) -> str:
        return self.re.pattern

    def __repr__(self) -> str:
        return f"<Match span={self.span()!r}, match={self.match!r}>"
