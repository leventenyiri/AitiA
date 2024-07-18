from utils import Logger, RTC
import pytest
import logging
from datetime import datetime
import pytz
import unittest
import subprocess
from unittest.mock import patch, mock_open, MagicMock
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


class TestRTC(unittest.TestCase):
    def test_get_time_success(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = (" Local time: Thu 2023-07-18 13:34:56 UTC\n"
                              " Universal time: Thu 2023-07-18 13:34:56 UTC\n"
                              " RTC time: Thu 2023-07-18 13:34:56\n"
                              " Time zone: Etc/UTC (UTC, +0000)\n"
                              " System clock synchronized: yes\n"
                              " NTP service: active\n"
                              " RTC in local TZ: no\n")

        with patch('subprocess.run', return_value=mock_result):
            expected_time = datetime.strptime("Thu 2023-07-18 13:34:56 UTC", "%a %Y-%m-%d %H:%M:%S UTC")
            expected_time = pytz.UTC.localize(expected_time)
            result = RTC.get_time()
            self.assertEqual(result, expected_time.isoformat())

    @patch('subprocess.run')
    def test_get_time_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, 'cmd')
        # result gets the time from the datetime.now instead of the RTC
        result = RTC.get_time()

        now = datetime.now(pytz.UTC)
        result_time = datetime.fromisoformat(result)
        time_difference = abs((now - result_time).total_seconds())
        # Check if the result is close to the current time
        self.assertLess(time_difference, 0.1)

    def test_set_time_failure(self):
        time_to_set = 'Invalid time format'
        with pytest.raises(AttributeError):
            RTC.set_time(time_to_set)

    @patch('logging.info')
    @patch('subprocess.run')
    def test_set_time_success(self, mock_run, mock_logging_info):
        mock_run.return_value = MagicMock(returncode=0)
        time_to_set = datetime.now(pytz.UTC)
        RTC.set_time(time_to_set)

        # Check if logging.info was called with the correct message
        mock_logging_info.assert_called_with(f"RTC time set to {time_to_set.strftime('%H:%M:%S')}")