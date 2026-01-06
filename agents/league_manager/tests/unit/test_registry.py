"""
Unit tests for registration system components.

Tests:
- TokenGenerator: Token generation, uniqueness, format, security
- AgentStore: Add, retrieve, validate agents and tokens
- RegistryManager: ID generation, capacity limits, registration flow
"""

import pytest
import string
from league_manager.registry.token_generator import (
    generate_auth_token,
    redact_token
)
from league_manager.registry.agent_store import AgentStore
from league_manager.registry.registry_manager import RegistryManager


class TestTokenGenerator:
    """Test token generation functionality."""

    def test_generate_token_format_player(self):
        """Test player token has correct format."""
        token = generate_auth_token("player", "P01")

        # Should start with tok_p
        assert token.startswith("tok_p"), "Token should start with 'tok_p'"

        # Should contain player ID in lowercase
        assert "p01" in token, "Token should contain player ID"

        # Should have underscores separating parts
        parts = token.split("_")
        assert len(parts) == 3, "Token should have 3 parts: tok_p01_random"

    def test_generate_token_format_referee(self):
        """Test referee token has correct format."""
        token = generate_auth_token("referee", "REF01")

        # Should start with tok_r
        assert token.startswith("tok_r"), "Token should start with 'tok_r'"

        # Should contain referee ID in lowercase
        assert "ref01" in token, "Token should contain referee ID"

    def test_generate_token_length(self):
        """Test token has minimum required length."""
        token = generate_auth_token("player", "P01", length=16)

        # tok_p01_ = 8 chars + 16 random chars = 24 total minimum
        assert len(token) >= 24, f"Token length {len(token)} should be >= 24"

    def test_generate_token_custom_length(self):
        """Test token respects custom length parameter."""
        short_token = generate_auth_token("player", "P01", length=8)
        long_token = generate_auth_token("player", "P01", length=32)

        assert len(short_token) < len(long_token), "Custom length should be respected"

    def test_generate_token_uniqueness(self):
        """Test that generated tokens are unique."""
        tokens = set()

        # Generate 100 tokens for the same player
        for _ in range(100):
            token = generate_auth_token("player", "P01")
            tokens.add(token)

        # All should be unique
        assert len(tokens) == 100, "All generated tokens should be unique"

    def test_generate_token_character_set(self):
        """Test token uses only allowed characters."""
        token = generate_auth_token("player", "P01", length=16)

        # Extract random suffix
        random_part = token.split("_")[-1]

        # Should only contain lowercase letters and digits
        allowed_chars = set(string.ascii_lowercase + string.digits)
        token_chars = set(random_part)

        assert token_chars.issubset(allowed_chars), \
            f"Token contains invalid characters: {token_chars - allowed_chars}"

    def test_generate_token_no_uppercase(self):
        """Test token is all lowercase (security best practice)."""
        token = generate_auth_token("player", "P01")
        assert token == token.lower(), "Token should be all lowercase"

    def test_redact_token_standard(self):
        """Test token redaction for logging."""
        token = "tok_p01_abc123xyz789"
        redacted = redact_token(token)

        assert redacted == "tok_p01_...", f"Expected 'tok_p01_...', got '{redacted}'"

    def test_redact_token_short(self):
        """Test redaction of short tokens."""
        short_token = "tok_p01"
        redacted = redact_token(short_token)

        assert redacted == "***", "Short tokens should be fully redacted"

    def test_redact_token_preserves_prefix(self):
        """Test that redaction preserves first 8 characters."""
        token = "tok_p99_verylongrandomstring"
        redacted = redact_token(token)

        assert redacted.startswith("tok_p99_"), "Redaction should preserve prefix"
        assert redacted.endswith("..."), "Redaction should end with ..."


class TestAgentStore:
    """Test agent storage functionality."""

    @pytest.fixture
    def store(self):
        """Provide fresh AgentStore for each test."""
        return AgentStore()

    def test_add_player_success(self, store):
        """Test adding a player to the store."""
        player_data = store.add_player(
            player_id="P01",
            display_name="Alice",
            endpoint="http://localhost:9001/mcp",
            auth_token="tok_p01_xyz123"
        )

        assert player_data["player_id"] == "P01"
        assert player_data["display_name"] == "Alice"
        assert player_data["endpoint"] == "http://localhost:9001/mcp"
        assert "registered_at" in player_data
        assert player_data["game_types"] == ["even_odd"]

    def test_add_player_custom_game_types(self, store):
        """Test adding player with custom game types."""
        player_data = store.add_player(
            player_id="P01",
            display_name="Alice",
            endpoint="http://localhost:9001/mcp",
            auth_token="tok_p01_xyz123",
            game_types=["even_odd", "rock_paper_scissors"]
        )

        assert player_data["game_types"] == ["even_odd", "rock_paper_scissors"]

    def test_add_referee_success(self, store):
        """Test adding a referee to the store."""
        referee_data = store.add_referee(
            referee_id="REF01",
            display_name="Referee Alpha",
            endpoint="http://localhost:8001/mcp",
            auth_token="tok_rref01_abc789",
            max_concurrent_matches=5
        )

        assert referee_data["referee_id"] == "REF01"
        assert referee_data["display_name"] == "Referee Alpha"
        assert referee_data["max_concurrent_matches"] == 5
        assert "registered_at" in referee_data

    def test_get_player_exists(self, store):
        """Test retrieving an existing player."""
        store.add_player(
            player_id="P01",
            display_name="Alice",
            endpoint="http://localhost:9001/mcp",
            auth_token="tok_p01_xyz123"
        )

        player = store.get_player("P01")
        assert player is not None
        assert player["display_name"] == "Alice"

    def test_get_player_not_exists(self, store):
        """Test retrieving a non-existent player."""
        player = store.get_player("P99")
        assert player is None

    def test_get_referee_exists(self, store):
        """Test retrieving an existing referee."""
        store.add_referee(
            referee_id="REF01",
            display_name="Referee Alpha",
            endpoint="http://localhost:8001/mcp",
            auth_token="tok_rref01_abc789"
        )

        referee = store.get_referee("REF01")
        assert referee is not None
        assert referee["display_name"] == "Referee Alpha"

    def test_get_all_players_empty(self, store):
        """Test getting all players when empty."""
        players = store.get_all_players()
        assert players == []

    def test_get_all_players_multiple(self, store):
        """Test getting all players with multiple registered."""
        store.add_player("P01", "Alice", "http://localhost:9001/mcp", "tok1")
        store.add_player("P02", "Bob", "http://localhost:9002/mcp", "tok2")
        store.add_player("P03", "Charlie", "http://localhost:9003/mcp", "tok3")

        players = store.get_all_players()
        assert len(players) == 3

        names = {p["display_name"] for p in players}
        assert names == {"Alice", "Bob", "Charlie"}

    def test_get_all_referees_multiple(self, store):
        """Test getting all referees with multiple registered."""
        store.add_referee("REF01", "Ref A", "http://localhost:8001/mcp", "tok1")
        store.add_referee("REF02", "Ref B", "http://localhost:8002/mcp", "tok2")

        referees = store.get_all_referees()
        assert len(referees) == 2

    def test_validate_player_token_correct(self, store):
        """Test validating correct player token."""
        store.add_player("P01", "Alice", "http://localhost:9001/mcp", "tok_p01_xyz123")

        is_valid = store.validate_player_token("P01", "tok_p01_xyz123")
        assert is_valid is True

    def test_validate_player_token_incorrect(self, store):
        """Test validating incorrect player token."""
        store.add_player("P01", "Alice", "http://localhost:9001/mcp", "tok_p01_xyz123")

        is_valid = store.validate_player_token("P01", "wrong_token")
        assert is_valid is False

    def test_validate_player_token_nonexistent(self, store):
        """Test validating token for non-existent player."""
        is_valid = store.validate_player_token("P99", "any_token")
        assert is_valid is False

    def test_validate_referee_token_correct(self, store):
        """Test validating correct referee token."""
        store.add_referee("REF01", "Ref A", "http://localhost:8001/mcp", "tok_rref01_abc")

        is_valid = store.validate_referee_token("REF01", "tok_rref01_abc")
        assert is_valid is True

    def test_validate_referee_token_incorrect(self, store):
        """Test validating incorrect referee token."""
        store.add_referee("REF01", "Ref A", "http://localhost:8001/mcp", "tok_rref01_abc")

        is_valid = store.validate_referee_token("REF01", "wrong_token")
        assert is_valid is False

    def test_get_player_count_empty(self, store):
        """Test player count when empty."""
        assert store.get_player_count() == 0

    def test_get_player_count_multiple(self, store):
        """Test player count with multiple players."""
        store.add_player("P01", "Alice", "http://localhost:9001/mcp", "tok1")
        store.add_player("P02", "Bob", "http://localhost:9002/mcp", "tok2")

        assert store.get_player_count() == 2

    def test_get_referee_count_empty(self, store):
        """Test referee count when empty."""
        assert store.get_referee_count() == 0

    def test_get_referee_count_multiple(self, store):
        """Test referee count with multiple referees."""
        store.add_referee("REF01", "Ref A", "http://localhost:8001/mcp", "tok1")
        store.add_referee("REF02", "Ref B", "http://localhost:8002/mcp", "tok2")
        store.add_referee("REF03", "Ref C", "http://localhost:8003/mcp", "tok3")

        assert store.get_referee_count() == 3

    def test_player_token_isolation(self, store):
        """Test that player tokens are isolated from referee tokens."""
        store.add_player("P01", "Alice", "http://localhost:9001/mcp", "player_token")
        store.add_referee("REF01", "Ref A", "http://localhost:8001/mcp", "referee_token")

        # Player token should not validate as referee
        assert store.validate_referee_token("REF01", "player_token") is False
        # Referee token should not validate as player
        assert store.validate_player_token("P01", "referee_token") is False


class TestRegistryManager:
    """Test registry manager functionality."""

    @pytest.fixture
    def manager(self):
        """Provide fresh RegistryManager for each test."""
        return RegistryManager(max_players=5, max_referees=3)

    def test_register_player_success(self, manager):
        """Test successful player registration."""
        player_id, auth_token = manager.register_player(
            display_name="Alice",
            endpoint="http://localhost:9001/mcp"
        )

        assert player_id == "P01", "First player should get ID P01"
        assert auth_token.startswith("tok_p"), "Token should be properly formatted"
        assert len(auth_token) > 20, "Token should be sufficiently long"

    def test_register_player_sequential_ids(self, manager):
        """Test that player IDs are assigned sequentially."""
        p1_id, _ = manager.register_player("Alice", "http://localhost:9001/mcp")
        p2_id, _ = manager.register_player("Bob", "http://localhost:9002/mcp")
        p3_id, _ = manager.register_player("Charlie", "http://localhost:9003/mcp")

        assert p1_id == "P01"
        assert p2_id == "P02"
        assert p3_id == "P03"

    def test_register_player_stored_correctly(self, manager):
        """Test that registered player is stored with correct data."""
        player_id, auth_token = manager.register_player(
            display_name="Alice",
            endpoint="http://localhost:9001/mcp",
            game_types=["even_odd"],
            version="1.0.0"
        )

        player = manager.agent_store.get_player(player_id)
        assert player is not None
        assert player["display_name"] == "Alice"
        assert player["endpoint"] == "http://localhost:9001/mcp"
        assert player["game_types"] == ["even_odd"]
        assert player["version"] == "1.0.0"

    def test_register_player_capacity_limit(self, manager):
        """Test that player registration respects capacity limit."""
        # Register up to max capacity (5 players)
        for i in range(5):
            manager.register_player(f"Player{i}", f"http://localhost:900{i}/mcp")

        # Attempting to register 6th player should fail
        with pytest.raises(ValueError, match="League full"):
            manager.register_player("Player6", "http://localhost:9006/mcp")

    def test_register_referee_success(self, manager):
        """Test successful referee registration."""
        referee_id, auth_token = manager.register_referee(
            display_name="Referee Alpha",
            endpoint="http://localhost:8001/mcp",
            max_concurrent_matches=5
        )

        assert referee_id == "REF01", "First referee should get ID REF01"
        assert auth_token.startswith("tok_r"), "Token should be properly formatted"

    def test_register_referee_sequential_ids(self, manager):
        """Test that referee IDs are assigned sequentially."""
        r1_id, _ = manager.register_referee("Ref A", "http://localhost:8001/mcp")
        r2_id, _ = manager.register_referee("Ref B", "http://localhost:8002/mcp")

        assert r1_id == "REF01"
        assert r2_id == "REF02"

    def test_register_referee_stored_correctly(self, manager):
        """Test that registered referee is stored with correct data."""
        referee_id, auth_token = manager.register_referee(
            display_name="Referee Alpha",
            endpoint="http://localhost:8001/mcp",
            max_concurrent_matches=5,
            game_types=["even_odd"],
            version="1.0.0"
        )

        referee = manager.agent_store.get_referee(referee_id)
        assert referee is not None
        assert referee["display_name"] == "Referee Alpha"
        assert referee["max_concurrent_matches"] == 5

    def test_register_referee_capacity_limit(self, manager):
        """Test that referee registration respects capacity limit."""
        # Register up to max capacity (3 referees)
        for i in range(3):
            manager.register_referee(f"Ref{i}", f"http://localhost:800{i}/mcp")

        # Attempting to register 4th referee should fail
        with pytest.raises(ValueError, match="Maximum .* referees"):
            manager.register_referee("Ref4", "http://localhost:8004/mcp")

    def test_player_id_formatting(self, manager):
        """Test player ID formatting with zero padding."""
        # Register 9 players
        for i in range(9):
            player_id, _ = manager.register_player(f"Player{i}", f"http://localhost:900{i}/mcp")
            expected_id = f"P{i+1:02d}"  # P01, P02, ..., P09
            assert player_id == expected_id, f"Expected {expected_id}, got {player_id}"

    def test_referee_id_formatting(self, manager):
        """Test referee ID formatting with zero padding."""
        # Register 3 referees
        for i in range(3):
            referee_id, _ = manager.register_referee(f"Ref{i}", f"http://localhost:800{i}/mcp")
            expected_id = f"REF{i+1:02d}"  # REF01, REF02, REF03
            assert referee_id == expected_id, f"Expected {expected_id}, got {referee_id}"

    def test_custom_agent_store(self):
        """Test using custom AgentStore instance."""
        custom_store = AgentStore()
        manager = RegistryManager(agent_store=custom_store)

        player_id, _ = manager.register_player("Alice", "http://localhost:9001/mcp")

        # Verify player was stored in custom store
        assert custom_store.get_player(player_id) is not None

    def test_token_uniqueness_across_players(self, manager):
        """Test that each player gets a unique token."""
        tokens = set()

        for i in range(5):
            _, token = manager.register_player(f"Player{i}", f"http://localhost:900{i}/mcp")
            tokens.add(token)

        assert len(tokens) == 5, "All tokens should be unique"

    def test_token_uniqueness_across_referees(self, manager):
        """Test that each referee gets a unique token."""
        tokens = set()

        for i in range(3):
            _, token = manager.register_referee(f"Ref{i}", f"http://localhost:800{i}/mcp")
            tokens.add(token)

        assert len(tokens) == 3, "All tokens should be unique"

    def test_default_game_types(self, manager):
        """Test that default game_types is set correctly."""
        player_id, _ = manager.register_player("Alice", "http://localhost:9001/mcp")
        player = manager.agent_store.get_player(player_id)

        assert player["game_types"] == ["even_odd"], "Default game_types should be ['even_odd']"

    def test_custom_game_types(self, manager):
        """Test registration with custom game_types."""
        player_id, _ = manager.register_player(
            "Alice",
            "http://localhost:9001/mcp",
            game_types=["even_odd", "rock_paper_scissors"]
        )
        player = manager.agent_store.get_player(player_id)

        assert player["game_types"] == ["even_odd", "rock_paper_scissors"]

    def test_zero_capacity_limit(self):
        """Test manager with zero capacity (edge case)."""
        manager = RegistryManager(max_players=0)

        with pytest.raises(ValueError):
            manager.register_player("Alice", "http://localhost:9001/mcp")
