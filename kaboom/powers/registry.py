# kaboom/powers/registry.py
from kaboom.powers.see_self import SeeSelfPower
from kaboom.powers.see_other import SeeOtherPower
from kaboom.powers.blind_swap import BlindSwapPower
from kaboom.powers.see_and_swap import SeeAndSwapPower

POWER_REGISTRY = [
    SeeSelfPower(),
    SeeOtherPower(),
    BlindSwapPower(),
    SeeAndSwapPower(),
]
