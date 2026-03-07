# kaboom/exceptions.py
class KaboomError(Exception):
    """Base exception for Kaboom engine."""
    pass

class InvalidActionError(KaboomError):
    """Raised when a player attempts an invalid action."""
    pass

class InvalidReactionError(KaboomError):
    """Raised when a reaction attempt is invalid."""
    pass

class InvariantViolationError(KaboomError):
    """Raised when game state invariants are violated."""
    pass