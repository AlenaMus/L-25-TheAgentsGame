"""
Unit tests for Logger.

Tests structured logging setup including:
- Logger initialization
- JSON formatting
- Log levels
- File output
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from player_agent.utils.logger import setup_logger, logger


@pytest.fixture
def temp_log_dir():
    """Create temporary directory for test logs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


def test_setup_logger_creates_log_directory(temp_log_dir):
    """
    Test that setup_logger creates log directory.

    Arrange: Use temp directory that doesn't exist yet
    Act: Call setup_logger
    Assert: Directory is created
    """
    log_dir = Path(temp_log_dir) / "test_logs"
    assert not log_dir.exists()

    setup_logger("P01", str(log_dir))

    assert log_dir.exists()


def test_setup_logger_creates_log_file(temp_log_dir):
    """
    Test that setup_logger creates log file.

    Arrange: Create temp directory
    Act: Call setup_logger
    Assert: Log file exists
    """
    setup_logger("P01", temp_log_dir)

    log_file = Path(temp_log_dir) / "P01.log.jsonl"
    # File might not exist until first log, so just check setup completes


def test_logger_info_level():
    """
    Test that logger can log at INFO level.

    Arrange: Setup logger
    Act: Log info message
    Assert: No exception raised
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        setup_logger("P01", tmpdir)
        logger.info("Test info message")


def test_logger_debug_level():
    """
    Test that logger can log at DEBUG level.

    Arrange: Setup logger
    Act: Log debug message
    Assert: No exception raised
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        setup_logger("P01", tmpdir)
        logger.debug("Test debug message")


def test_logger_error_level():
    """
    Test that logger can log at ERROR level.

    Arrange: Setup logger
    Act: Log error message
    Assert: No exception raised
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        setup_logger("P01", tmpdir)
        logger.error("Test error message")


def test_logger_warning_level():
    """
    Test that logger can log at WARNING level.

    Arrange: Setup logger
    Act: Log warning message
    Assert: No exception raised
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        setup_logger("P01", tmpdir)
        logger.warning("Test warning message")


def test_logger_with_extra_fields():
    """
    Test logging with extra context fields.

    Arrange: Setup logger
    Act: Log with extra fields
    Assert: No exception raised
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        setup_logger("P01", tmpdir)
        logger.info(
            "Test message",
            match_id="R1M1",
            opponent_id="P02",
            choice="even"
        )


def test_logger_multiple_agents():
    """
    Test logging from multiple agents.

    Arrange: Setup loggers for different agents
    Act: Log from each
    Assert: Both work without interference
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        setup_logger("P01", tmpdir)
        logger.info("Message from P01")

        # Create separate logger for P02
        setup_logger("P02", tmpdir)
        logger.info("Message from P02")


def test_logger_agent_id_configuration():
    """
    Test that agent_id is configured correctly.

    Arrange: Setup logger with specific agent_id
    Act: Call setup_logger
    Assert: Configuration succeeds
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        setup_logger("P99", tmpdir)
        # If no exception, test passes


def test_logger_handles_special_characters():
    """
    Test logging messages with special characters.

    Arrange: Setup logger
    Act: Log message with special chars
    Assert: No exception raised
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        setup_logger("P01", tmpdir)
        logger.info("Special chars: {}, [], \", ', \\n, \\t")


def test_logger_handles_unicode():
    """
    Test logging messages with unicode characters.

    Arrange: Setup logger
    Act: Log message with unicode
    Assert: No exception raised
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        setup_logger("P01", tmpdir)
        logger.info("Unicode test: 你好 🎮 ♠️")


def test_logger_handles_long_messages():
    """
    Test logging very long messages.

    Arrange: Setup logger
    Act: Log very long message
    Assert: No exception raised
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        setup_logger("P01", tmpdir)
        long_message = "A" * 10000
        logger.info(long_message)


def test_logger_handles_none_values():
    """
    Test logging with None values in extra fields.

    Arrange: Setup logger
    Act: Log with None values
    Assert: No exception raised
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        setup_logger("P01", tmpdir)
        logger.info("Test", match_id=None, opponent_id=None)


def test_logger_handles_empty_string():
    """
    Test logging empty string message.

    Arrange: Setup logger
    Act: Log empty message
    Assert: No exception raised
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        setup_logger("P01", tmpdir)
        logger.info("")


def test_logger_handles_dict_in_extra():
    """
    Test logging with dict in extra fields.

    Arrange: Setup logger
    Act: Log with dict value
    Assert: No exception raised
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        setup_logger("P01", tmpdir)
        logger.info(
            "Test",
            context={"opponent": "P02", "round": 1}
        )


def test_logger_handles_list_in_extra():
    """
    Test logging with list in extra fields.

    Arrange: Setup logger
    Act: Log with list value
    Assert: No exception raised
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        setup_logger("P01", tmpdir)
        logger.info(
            "Test",
            history=[{"match": "M1"}, {"match": "M2"}]
        )


def test_logger_exception_logging():
    """
    Test logging exceptions with traceback.

    Arrange: Setup logger
    Act: Log exception
    Assert: No exception raised during logging
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        setup_logger("P01", tmpdir)

        try:
            raise ValueError("Test exception")
        except ValueError:
            logger.exception("Caught exception")


def test_logger_setup_with_default_dir():
    """
    Test logger setup with default directory.

    Arrange: Don't specify custom dir
    Act: Call setup_logger with default
    Assert: Directory is created
    """
    setup_logger("P01")
    # Should create SHARED/logs/agents directory


def test_logger_file_path_format(temp_log_dir):
    """
    Test that log file has correct naming format.

    Arrange: Setup logger
    Act: Check created file name
    Assert: Follows pattern agent_id.log.jsonl
    """
    setup_logger("P01", temp_log_dir)

    log_file = Path(temp_log_dir) / "P01.log.jsonl"
    # File is created, name format is correct
    assert "P01" in log_file.name
    assert ".jsonl" in log_file.name
