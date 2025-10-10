from enum import IntFlag


class PatternFlag(IntFlag):
    NOFLAG = 0x0
    IGNORECASE = 0x1
    DOTALL = 0x2
    I = 0x1
    S = 0x2
