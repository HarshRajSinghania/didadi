import unittest
from unittest.mock import Mock, patch
from scripts.agent_worker import run_loop


class WorkerLoopTest(unittest.TestCase):
    def test_transient_failure_retries_and_interrupt_stops(self):
        iteration = Mock(side_effect=[ConnectionError('private detail'), True, KeyboardInterrupt()])
        with patch('scripts.agent_worker.time.sleep') as sleep, self.assertLogs(level='WARNING') as logs:
            with self.assertRaises(KeyboardInterrupt):
                run_loop(iteration, delay=1)
        self.assertEqual(iteration.call_count, 3)
        self.assertEqual(sleep.call_count, 2)
        self.assertNotIn('private detail', ''.join(logs.output))
