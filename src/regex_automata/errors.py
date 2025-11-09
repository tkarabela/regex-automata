from typing import Any


class RegexAutomataError(Exception):
    pass


class PatternError(RegexAutomataError):
    pass


class ParserError(RegexAutomataError):
    def __init__(self, msg: str, string_pos: int) -> None:
        super().__init__(msg)
        self.msg = msg
        self.string_pos = string_pos

    def __reduce__(self) -> Any:
        return self.__class__, (self.msg, self.string_pos)


class TokenizerError(RegexAutomataError):
    def __init__(self, msg: str, string_pos: int) -> None:
        super().__init__(msg)
        self.msg = msg
        self.string_pos = string_pos

    def __reduce__(self) -> Any:
        return self.__class__, (self.msg, self.string_pos)


class UnsupportedSyntaxError(NotImplementedError):
    def __init__(self, msg: str, string_pos: int) -> None:
        super().__init__(msg)
        self.msg = msg
        self.string_pos = string_pos

    def __reduce__(self) -> Any:
        return self.__class__, (self.msg, self.string_pos)
