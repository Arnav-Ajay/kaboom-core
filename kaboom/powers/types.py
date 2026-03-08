# kaboom/powers/types.py
from enum import Enum

class PowerType(str, Enum):
    SEE_SELF = "see_self"
    SEE_OTHER = "see_other"
    BLIND_SWAP = "blind_swap"
    SEE_AND_SWAP = "see_and_swap"