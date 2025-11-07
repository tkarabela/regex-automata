# ruff: noqa: E741
from enum import IntFlag


class PatternFlag(IntFlag):
    NOFLAG = 0x0
    IGNORECASE = 0x1
    DOTALL = 0x2
    MULTILINE = 0x4
    I = 0x1
    S = 0x2
    M = 0x4
