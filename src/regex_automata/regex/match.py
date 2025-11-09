from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from .pattern import Pattern


@dataclass(repr=False)
class Match:
    re: "Pattern"
    pos: int | None
    endpos: int | None
    match: str
    groupspandict: dict[int, tuple[int, int]]

    def group(self, *indices: int | str) -> Any | tuple[Any, ...]:
        match len(indices):
            case 0:
                return self._group(0)
            case 1:
                return self._group(indices[0])
            case _:
                return tuple(map(self._group, indices))

    def _group(self, i: int | str, default: Any = None) -> Any:
        start, end = self.span(i)
        if start == -1:
            return default
        else:
            match_start = self.start()
            return self.match[start - match_start : end - match_start]

    def groups(self, default: Any = None) -> tuple[Any, ...]:
        return tuple(self._group(i, default) for i in range(1, self.re.max_group_number+1))

    def groupdict(self, default: Any = None) -> dict[str, Any]:
        return {i: self._group(i, default) for i in self.re.group_name_to_group_number}

    def span(self, i: int | str = 0) -> tuple[int, int]:
        if isinstance(i, str):
            i = self.re.group_name_to_group_number[i]

        if i < 0 or i > self.re.max_group_number:
            raise IndexError(f"No group with index {i}")
        return self.groupspandict.get(i, (-1, -1))

    def start(self, i: int | str = 0) -> int:
        return self.span(i)[0]

    def end(self, i: int | str = 0) -> int:
        return self.span(i)[1]

    def __getitem__(self, i: int | str) -> Any:
        return self._group(i)

    @property
    def string(self) -> str:
        return self.re.pattern

    def expand(self, template: str) -> str:
        output: list[str] = []
        last_match_end = 0

        for m in self._get_expand_pattern().finditer(template):
            output.append(template[last_match_end:m.start()])
            if m.group("number") is not None:
                i = int(m._group("number"))
                value = self._group(i)
            elif m.group("g_name_or_number") is not None:
                try:
                    i = int(m._group("g_name_or_number"))
                    value = self._group(i)
                except Exception:
                    i = m._group("g_name_or_number")
                    value = self._group(i)
            elif m._group("escape_sequence") is not None:
                tmp = m._group("escape_sequence")
                if tmp[0] in ("x", "u", "U"):
                    value = chr(int(tmp[1:], base=16))
                else:
                    value = {
                        "a": "\a", "b": "\b", "f": "\f", "n": "\n", "r": "\r", "t": "\t", "v": "\v", "\\": "\\",
                    }[tmp]
            else:
                raise RuntimeError("internal error in expand pattern match")

            if value is None:
                value = ""
            output.append(value)

            last_match_end = m.end()

        output.append(template[last_match_end:])

        return "".join(output)

    def __repr__(self) -> str:
        return f"<Match span={self.span()!r}, match={self.match!r}>"

    @classmethod
    def _get_expand_pattern(cls) -> "Pattern":
        from regex_automata import compile
        global _EXPAND_PATTERN
        if _EXPAND_PATTERN is None:
            _EXPAND_PATTERN = compile(
                r"\\g<(?P<g_name_or_number>[^>]+)>|"
                r"\\(?P<number>[0-9]+)|"
                r"\\(?P<escape_sequence>[abfnrtv]|\\|x[0-9a-fA-F]{2}|u[0-9a-fA-F]{4}|U[0-9a-fA-F]{8})"
            )
        return _EXPAND_PATTERN


_EXPAND_PATTERN: Optional["Pattern"] = None
