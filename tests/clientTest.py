""" from client import main
from app import App
from unittest.mock import patch
import unittest
import pytest
from utils import Logger, LOG_CONFIG_PATH, CONFIG_PATH


@pytest.fixture
def logger():
    return Logger(LOG_CONFIG_PATH)


@pytest.fixture
def app():
    return App(CONFIG_PATH)


class TestMainFunction(unittest.TestCase):
    @patch('app.App')
    @patch('utils.Logger')
    @patch('utils.log_execution_time', lambda x: x)  # Bypass the decorator
    def test_main_always_on_mode(self, MockLogger, MockApp):
        mock_logger = MockLogger.return_value
        mock_app = MockApp.return_value
        mock_app.basic_config = {'mode': 'always_on'}

        main()

        mock_logger.start.assert_called_once()
        mock_app.start.assert_called_once()
        mock_app.run_always.assert_called_once() """
