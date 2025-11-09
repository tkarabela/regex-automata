from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .pattern import Pattern


@dataclass(repr=False)
class Match:
    re: "Pattern"
    pos: int | None
    endpos: int | None
    match: str
    groupspandict: dict[int, tuple[int, int]]

    def group(self, *indices: int) -> Any | tuple[Any, ...]:
        match len(indices):
            case 0:
                return self._group(0)
            case 1:
                return self._group(indices[0])
            case _:
                return tuple(map(self._group, indices))

    def _group(self, i: int, default: Any = None) -> Any:
        start, end = self.span(i)
        if start == -1:
            return default
        else:
            match_start = self.start()
            return self.match[start - match_start : end - match_start]

    def groups(self, default: Any = None) -> tuple[Any, ...]:
        return tuple(self._group(i, default) for i in range(1, self.re.max_group_number+1))

    def groupdict(self, default: Any = None) -> dict[int, Any]:
        return {i: self._group(i, default) for i in self.groupspandict}

    def span(self, i: int = 0) -> tuple[int, int]:
        if i < 0 or i > self.re.max_group_number:
            raise IndexError(f"No group with index {i}")
        return self.groupspandict.get(i, (-1, -1))

    def start(self, i: int = 0) -> int:
        return self.span(i)[0]

    def end(self, i: int = 0) -> int:
        return self.span(i)[1]

    def __getitem__(self, i: int) -> Any:
        return self._group(i)

    @property
    def string(self) -> str:
        return self.re.pattern

    def __repr__(self) -> str:
        return f"<Match span={self.span()!r}, match={self.match!r}>"
