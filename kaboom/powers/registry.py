# kaboom/powers/registry.py
from ..cards.card import Card, Rank, Suit
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

def get_power_for_rank(rank: Rank) -> Optional[PowerType]:
    """
    Return the PowerType associated with a card rank.

    Kaboom power mapping:
    7,8  -> SeeSelf
    9,10 -> SeeOther
    J,Q  -> BlindSwap
    K    -> SeeAndSwap candidate, subject to suit validation
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


def get_power_for_card(card: Card | Rank) -> Optional[PowerType]:
    """
    Return the PowerType associated with a concrete card.

    Backward compatibility:
    * if a Rank is passed, rank-only mapping is used
    * if a Card is passed, the black-king restriction for SeeAndSwap is enforced
    """
    if isinstance(card, Rank):
        return get_power_for_rank(card)

    power_type = get_power_for_rank(card.rank)
    if power_type != PowerType.SEE_AND_SWAP:
        return power_type

    if card.suit in {Suit.SPADES, Suit.CLUBS}:
        return power_type

    return None
