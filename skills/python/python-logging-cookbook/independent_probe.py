"""Independent boundary probes. Standard library only; all thread waits bounded.

Internal listener/thread state is inspected for testing, not production guidance.
Run with python independent_probe.py and python -O independent_probe.py.
"""
import logging
from logging.handlers import QueueHandler, QueueListener
import queue
import threading
import unittest


def event(text):
    return logging.LogRecord('independent', logging.INFO, __file__, 1, text, (), None)


class BoundaryTests(unittest.TestCase):
    def test_sink_failure_strands_task_accounting(self):
        class Broken(logging.Handler):
            def emit(self, record):
                raise RuntimeError('deliberate sink failure')
        errors = []
        old_hook = threading.excepthook
        threading.excepthook = errors.append
        self.addCleanup(setattr, threading, 'excepthook', old_hook)
        sink = Broken()
        self.addCleanup(sink.close)
        target = queue.Queue()
        listener = QueueListener(target, sink)
        target.put(event('accepted'))
        listener.start()
        worker = listener._thread
        worker.join(2)
        self.assertFalse(worker.is_alive())
        self.assertEqual(len(errors), 1)
        self.assertIs(errors[0].exc_type, RuntimeError)
        self.assertEqual(target.unfinished_tasks, 1)
        # Do not call queue.join(): this deliberately exhibits stranded debt.
        target.task_done()

    def test_record_accepted_after_sentinel_is_not_handled(self):
        class AfterSentinel(QueueListener):
            def enqueue_sentinel(self):
                super().enqueue_sentinel()
                self.queue.put_nowait(event('too late'))
        target = queue.Queue()
        sink = logging.NullHandler()
        self.addCleanup(sink.close)
        listener = AfterSentinel(target, sink)
        listener.start()
        listener.enqueue_sentinel()
        listener._thread.join(2)
        self.assertFalse(listener._thread.is_alive())
        self.assertEqual(target.get_nowait().getMessage(), 'too late')
        self.assertEqual(target.unfinished_tasks, 1)
        target.task_done()

    def test_preparation_failure_is_not_queue_capacity_loss(self):
        class CountErrors(QueueHandler):
            failures = 0
            def handleError(self, record):
                self.failures += 1
        class BrokenFormatter(logging.Formatter):
            def format(self, record):
                raise ValueError('deliberate preparation failure')
        target = queue.Queue(1)
        handler = CountErrors(target)
        self.addCleanup(handler.close)
        handler.setFormatter(BrokenFormatter())
        handler.handle(event('not admitted'))
        self.assertEqual(handler.failures, 1)
        self.assertTrue(target.empty())
        self.assertEqual(target.unfinished_tasks, 0)


if __name__ == '__main__':
    unittest.main()
