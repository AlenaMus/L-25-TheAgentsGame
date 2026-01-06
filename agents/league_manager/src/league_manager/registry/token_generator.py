"""
Secure authentication token generation.

Generates cryptographically secure tokens for players and referees.
"""

import secrets
import string


def generate_auth_token(agent_type: str, agent_id: str, length: int = 16) -> str:
    """
    Generate a cryptographically secure authentication token.

    Args:
        agent_type: "player" or "referee"
        agent_id: Assigned agent ID (e.g., "P01", "REF01")
        length: Length of random suffix (default: 16 characters)

    Returns:
        Token string (e.g., "tok_p01_abc123xyz789")

    Security:
        Uses secrets module (CSPRNG) for cryptographic randomness.

    Example:
        >>> token = generate_auth_token("player", "P01")
        >>> token.startswith("tok_p")
        True
        >>> len(token) >= 20
        True
    """
    # Create alphabet (lowercase + digits)
    alphabet = string.ascii_lowercase + string.digits

    # Generate random suffix
    random_suffix = ''.join(secrets.choice(alphabet) for _ in range(length))

    # Format: tok_{type_initial}{id_lower}_{random}
    agent_prefix = agent_type[0].lower() + agent_id.lower()
    token = f"tok_{agent_prefix}_{random_suffix}"

    return token


def redact_token(token: str) -> str:
    """
    Redact token for safe logging.

    Args:
        token: Full authentication token

    Returns:
        Redacted token showing only first 8 characters

    Example:
        >>> redact_token("tok_p01_abc123xyz789")
        'tok_p01_...'
    """
    if len(token) <= 8:
        return "***"
    return token[:8] + "..."


__all__ = ["generate_auth_token", "redact_token"]
