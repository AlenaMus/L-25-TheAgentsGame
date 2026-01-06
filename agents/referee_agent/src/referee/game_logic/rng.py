"""
Cryptographic random number generation for game draws.

Uses Python's secrets module for secure randomness.
"""

import secrets


def draw_number() -> int:
    """
    Draw a cryptographically random number between 1 and 10.

    Uses secrets.randbelow() which provides cryptographic
    randomness suitable for fair game outcomes.

    Returns:
        int: Random number in range [1, 10] inclusive

    Example:
        >>> num = draw_number()
        >>> assert 1 <= num <= 10
    """
    return secrets.randbelow(10) + 1
