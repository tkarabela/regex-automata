from collections.abc import Set, Hashable
from itertools import chain
from typing import Iterable, Tuple, Iterator, Self, Any
from bisect import bisect_left


class RangeSet(Set[int], Hashable):
    def __init__(self, values: Iterable[int] = (), ranges: Iterable[Tuple[int, int]] = (), complement: bool = False) -> None:
        self._ranges = tuple(self._merge_sorted_ranges(sorted(chain(ranges, ((x, x + 1) for x in values)))))
        self._complement = complement

    @property
    def ranges(self) -> tuple[tuple[int, int], ...]:
        return self._ranges

    @property
    def complement(self) -> bool:
        return self._complement

    @property
    def empty(self) -> bool:
        return not self._ranges and not self._complement

    @staticmethod
    def _merge_sorted_ranges(ranges: Iterable[tuple[int, int]]) -> list[tuple[int, int]]:
        output: list[tuple[int, int]] = []

        for x, y in ranges:
            if not (x < y):
                continue  # empty subrange

            if not output:
                output.append((x, y))  # first subrange
            else:
                x0, y0 = output[-1]
                if x < y0:
                    assert x >= x0, "expected sorted input"
                    if y > y0:
                        output.pop()
                        output.append((x0, y))  # extend subrange - partial overlap
                    else:
                        pass  # new subrange is entirely inside previous
                elif x == y0:
                    output.pop()
                    output.append((x0, y))  # extend subrange - contiguous
                else:
                    output.append((x, y))  # new subrange

        return output

    def __len__(self) -> int:
        if self._complement:
            raise ValueError("__len__ is only implemented for non-complementary sets")
        return sum(y - x for x, y in self._ranges)

    def __iter__(self) -> Iterator[int]:
        if self._complement:
            raise ValueError("__iter__ is only implemented for non-complementary sets")
        for x, y in self._ranges:
            yield from range(x, y)

    def __contains__(self, x: object) -> bool:
        if not isinstance(x, int):
            raise TypeError("only int is supported")

        if not self._ranges:
            found = False
        else:
            ymax = self._ranges[-1][1]
            i = bisect_left(self._ranges, (x, ymax + 1)) - 1
            found = i < len(self._ranges) and self._ranges[i][0] <= x < self._ranges[i][1]
        return found if not self._complement else not found

    def __eq__(self, other: object) -> bool:
        if isinstance(other, RangeSet):
            return self._ranges == other._ranges and self._complement == other._complement
        return NotImplemented

    def __or__(self, other: object) -> Self:
        if isinstance(other, RangeSet):
            if not self._complement and not other._complement:
                return RangeSet(ranges=self._merge_sorted_ranges(sorted(chain(self._ranges, other._ranges))))  # type: ignore[return-value]
        return super().__or__(other)  # type: ignore[operator,return-value]

    def __and__(self, other: object) -> Self:
        if isinstance(other, RangeSet):
            if self._complement and other._complement:
                return RangeSet(ranges=self._merge_sorted_ranges(sorted(chain(self._ranges, other._ranges))))  # type: ignore[return-value]
        return super().__and__(other)  # type: ignore[operator,return-value]

    def __hash__(self) -> int:
        return hash((self._ranges, self._complement))

    def __repr__(self) -> str:
        if self._complement:
            return f"RangeSet({self._ranges!r}, complement={self._complement!r})"
        else:
            return f"RangeSet({self._ranges!r})"

    def to_dict(self) -> dict[str, Any]:
        return {
            "ranges": self._ranges,
            "complement": self._complement,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Self:
        return cls(
            ranges=[(x, y) for x, y in d.get("ranges", ())],
            complement=d.get("complement", False),
        )


WORD_RANGESET = RangeSet(
    values=[ord("_")],
    ranges=[(ord("a"), ord("z")+1), (ord("A"), ord("Z")+1), (ord("0"), ord("9")+1)]
)
NONWORD_RANGESET = RangeSet(ranges=WORD_RANGESET.ranges, complement=True)
WHITESPACE_RANGESET = RangeSet(
    values=map(ord, "\f\n\r\t\v\u0020\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000\ufeff")
)
NONWHITESPACE_RANGESET = RangeSet(ranges=WHITESPACE_RANGESET.ranges, complement=True)
DIGIT_RANGESET = RangeSet(ranges=[(ord("0"), ord("9")+1)])
NONDIGIT_RANGESET = RangeSet(ranges=DIGIT_RANGESET.ranges, complement=True)
