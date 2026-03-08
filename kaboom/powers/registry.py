# kaboom/powers/registry.py
from ..cards.card import Rank
from typing import Optional
from .see_self import SeeSelfPower
from .see_other import SeeOtherPower
from .blind_swap import BlindSwapPower
from .see_and_swap import SeeAndSwapPower
from .types import PowerType

POWER_REGISTRY = {
    PowerType.SEE_SELF: SeeSelfPower(),
    PowerType.SEE_OTHER: SeeOtherPower(),
    PowerType.BLIND_SWAP: BlindSwapPower(),
    PowerType.SEE_AND_SWAP: SeeAndSwapPower(),
}

POWER_CARD_RANKS = {
    Rank.SEVEN,
    Rank.EIGHT,
    Rank.NINE,
    Rank.TEN,
    Rank.J,
    Rank.Q,
    Rank.K,
}

def get_power_for_card(rank: Rank) -> Optional[PowerType]:
    """
    Return the PowerType associated with a card rank.

    Kaboom power mapping:
    7,8  -> SeeSelf
    9,10 -> SeeOther
    J,Q  -> BlindSwap
    K    -> SeeAndSwap
    """

    if rank in {Rank.SEVEN, Rank.EIGHT}:
        return PowerType.SEE_SELF

    if rank in {Rank.NINE, Rank.TEN}:
        return PowerType.SEE_OTHER

    if rank in {Rank.J, Rank.Q}:
        return PowerType.BLIND_SWAP

    if rank == Rank.K:
        return PowerType.SEE_AND_SWAP

    return None