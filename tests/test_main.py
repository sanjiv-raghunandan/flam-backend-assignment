import unittest
from unittest.mock import patch
from click.testing import CliRunner
from queuectl.main import cli

class TestCli(unittest.TestCase):
    def test_enqueue(self):
        runner = CliRunner()
        # The command now takes the command string directly
        result = runner.invoke(cli, ['enqueue', 'sleep 2'])
        self.assertIn("Enqueued job", result.output)

    @patch('queuectl.main.worker_manager.start_workers')
    def test_worker_start(self, mock_start_workers):
        runner = CliRunner()
        result = runner.invoke(cli, ['worker', 'start', '--count', '3'])
        # Check that our mock was called
        mock_start_workers.assert_called_once_with(3)
        # Check the updated output text
        self.assertIn("Started 3 worker(s)", result.output)

if __name__ == '__main__':
    unittest.main()
