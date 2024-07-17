from utils import Logger
import pytest
import logging
from unittest.mock import patch, mock_open
from static_config import LOG_CONFIG_PATH


@pytest.fixture
def logger():
    return Logger(LOG_CONFIG_PATH)


def test_logging_start(logger, caplog):
    caplog.set_level(logging.INFO)

    assert logger.filepath == LOG_CONFIG_PATH
    # Patch open, os.path.exists, yaml.safe_load, and logging.config.dictConfig
    with patch('builtins.open', mock_open()) as mocked_open, \
            patch('os.path.exists', return_value=True), \
            patch('yaml.safe_load', return_value={'version': 1}), \
            patch('logging.config.dictConfig') as mock_dictConfig:

        # Act: invoke the start method
        logger.start()

        # Assert: check if open was called with the correct filepath
        mocked_open.assert_called_once_with(LOG_CONFIG_PATH, 'r')
        mock_dictConfig.assert_called_once_with({'version': 1})
        assert "Logging started" in caplog.text
