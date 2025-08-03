import os
import logging
import glob
import shutil
import pytest

from logger.log_manager import LogManager

TEST_LOG_DIR = 'temp_test_logs'

@pytest.fixture(autouse=True)
def clean_test_logs():
    """Fixture to clean log directory before and after each test."""
    if os.path.exists(TEST_LOG_DIR):
        shutil.rmtree(TEST_LOG_DIR)
    os.makedirs(TEST_LOG_DIR)
    yield
    shutil.rmtree(TEST_LOG_DIR)


def test_logger_file_creation():
    """Test that a log file is created and written to."""
    log_manager = LogManager(testname='unit_test_logger', log_dir=TEST_LOG_DIR, console=False)
    logger = log_manager.get_logger()

    logger.info("This is a test message.")

    # Ensure a log file was created
    log_files = glob.glob(os.path.join(TEST_LOG_DIR, '*.log'))
    assert len(log_files) == 1, "Expected one log file to be created."

    # Check that log message was written
    with open(log_files[0], 'r') as f:
        contents = f.read()
        assert "This is a test message." in contents


def test_logger_name_and_level():
    """Ensure logger name and level are set correctly."""
    testname = 'test_logger_name'
    log_manager = LogManager(testname=testname, log_dir=TEST_LOG_DIR, console=False)
    logger = log_manager.get_logger()

    assert logger.name == testname
    assert logger.level == logging.INFO


def test_console_logging_enabled(capsys):
    """Ensure console logging outputs messages when enabled."""
    log_manager = LogManager(testname='console_test', log_dir=TEST_LOG_DIR, console=True)
    logger = log_manager.get_logger()
    logger.info("Console logging test.")

    captured = capsys.readouterr()
    assert "Console logging test." in captured.err


def test_console_logging_disabled(capsys):
    """Ensure console logging does not output messages when disabled."""
    log_manager = LogManager(testname='console_off_test', log_dir=TEST_LOG_DIR, console=False)
    logger = log_manager.get_logger()
    logger.info("This should not appear in console.")

    captured = capsys.readouterr()
    assert "This should not appear in console." not in captured.err
