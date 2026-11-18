"""Isolated CPython logging contract probes; no external sink or dependencies.

Run: python validate_logging.py -v (also repeat with python -O).
Events establish ordering. Timeouts bound test failures, not production latency.
Private listener thread access is used only to check and clean up test resources.
"""

import contextlib
import io
import logging
from logging.handlers import QueueHandler, QueueListener
from pathlib import Path
import queue
import sys
import tempfile
import threading
import unittest


def record(message="sample", level=logging.INFO):
    return logging.LogRecord("probe", level, __file__, 1, message, (), None)


class Collect(logging.Handler):
    def __init__(self):
        super().__init__()
        self.messages = []

    def emit(self, event):
        self.messages.append(event.getMessage())


class GatedCollect(Collect):
    def __init__(self):
        super().__init__()
        self.entered = threading.Event()
        self.allow_emit = threading.Event()
        self.timed_out = False

    def emit(self, event):
        self.entered.set()
        if not self.allow_emit.wait(5):
            self.timed_out = True
        super().emit(event)


class CountLoss(QueueHandler):
    def __init__(self, target):
        super().__init__(target)
        self.failed = 0

    def handleError(self, event):
        # Handler.handle serializes this fixture's calls. Never log recursively.
        # Counts all emit failures, not solely capacity drops.
        self.failed += 1


class LoggingContracts(unittest.TestCase):
    def setUp(self):
        original = logging.raiseExceptions
        self.addCleanup(setattr, logging, "raiseExceptions", original)

    def listener(self, target, sink, **kwargs):
        listener = QueueListener(target, sink, **kwargs)
        listener.start()

        def cleanup():
            if isinstance(sink, GatedCollect):
                sink.allow_emit.set()
            worker = listener._thread
            if worker is not None and worker.is_alive():
                target.put(listener._sentinel, timeout=2)
                worker.join(2)
                self.assertFalse(worker.is_alive(), "listener leaked")
            if isinstance(sink, GatedCollect):
                self.assertFalse(sink.timed_out, "gate expired rather than released")
            sink.close()

        self.addCleanup(cleanup)
        return listener

    def bounded_join(self, target):
        # Test-only bounded precondition before the real join. There are no
        # remaining producers, so the count cannot rise after this check.
        with target.all_tasks_done:
            drained = target.all_tasks_done.wait_for(
                lambda: target.unfinished_tasks == 0, timeout=2)
        self.assertTrue(drained, "unfinished queue accounting")
        target.join()

    def test_full_queue_drops_without_raising_or_diagnostic(self):
        target = queue.Queue(1)
        handler = QueueHandler(target)
        self.addCleanup(handler.close)
        target.put(record("first"))
        logging.raiseExceptions = False
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            handler.handle(record("lost"))
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(target.get_nowait().msg, "first")
        with self.assertRaises(queue.Empty):
            target.get_nowait()

    def test_explicit_failure_counter_observes_capacity_loss(self):
        target = queue.Queue(1)
        handler = CountLoss(target)
        self.addCleanup(handler.close)
        logging.raiseExceptions = False
        handler.handle(record("accepted"))
        handler.handle(record("lost"))
        self.assertEqual(handler.failed, 1)
        self.assertEqual(target.get_nowait().msg, "accepted")

    def test_stop_can_fail_to_enqueue_sentinel_when_full(self):
        target = queue.Queue(1)
        sink = GatedCollect()
        listener = self.listener(target, sink)
        target.put(record("in progress"))
        self.assertTrue(sink.entered.wait(2))
        target.put_nowait(record("queued"))
        with self.assertRaises(queue.Full):
            listener.stop()
        self.assertTrue(listener._thread.is_alive())
        sink.allow_emit.set()
        self.bounded_join(target)
        listener.stop()
        self.assertEqual(sink.messages, ["in progress", "queued"])

    def test_quiesced_finite_producer_drain_then_stop(self):
        target = queue.Queue(1)
        sink = GatedCollect()
        listener = self.listener(target, sink)
        handler = CountLoss(target)
        self.addCleanup(handler.close)

        def produce():
            handler.handle(record("in progress"))
            if sink.entered.wait(2):
                handler.handle(record("queued"))

        producer = threading.Thread(target=produce)
        producer.start()
        producer.join(3)  # Quiescence: no source can enqueue after this join.
        self.assertFalse(producer.is_alive())
        self.assertEqual(handler.failed, 0)
        self.assertTrue(sink.entered.is_set())
        sink.allow_emit.set()
        self.bounded_join(target)  # A finite healthy handler, not a stalled sink.
        listener.stop()
        self.assertEqual(sink.messages, ["in progress", "queued"])
        self.assertEqual(target.unfinished_tasks, 0)

    def test_prepare_flattens_exception_but_keeps_traceback_text(self):
        handler = QueueHandler(queue.Queue())
        self.addCleanup(handler.close)
        try:
            raise ValueError("distinct failure")
        except ValueError:
            original = logging.LogRecord("probe", logging.ERROR, __file__, 1,
                                         "failed %s", ("work",), sys.exc_info())
        prepared = handler.prepare(original)
        self.assertIsNone(prepared.exc_info)
        self.assertIsNone(prepared.exc_text)
        self.assertIsNone(prepared.args)
        self.assertIn("failed work", prepared.msg)
        self.assertIn("ValueError: distinct failure", prepared.msg)
        self.assertIn("Traceback", prepared.msg)
        self.assertIsNotNone(original.exc_info)
        self.assertIsNot(prepared, original)

    def test_listener_ignores_handler_level_by_default(self):
        for respect, expected in ((False, ["info"]), (True, [])):
            with self.subTest(respect_handler_level=respect):
                sink = Collect()
                sink.setLevel(logging.ERROR)
                self.addCleanup(sink.close)
                listener = QueueListener(queue.Queue(), sink,
                                         respect_handler_level=respect)
                listener.handle(record("info"))
                self.assertEqual(sink.messages, expected)

    def test_file_handler_is_eager_unless_delay_requested(self):
        with tempfile.TemporaryDirectory() as directory:
            eager_path = Path(directory) / "eager.log"
            eager = logging.FileHandler(eager_path)
            try:
                self.assertTrue(eager_path.exists())
                self.assertIsNotNone(eager.stream)
            finally:
                eager.close()
            delayed_path = Path(directory) / "delayed.log"
            delayed = logging.FileHandler(delayed_path, delay=True)
            try:
                self.assertFalse(delayed_path.exists())
                self.assertIsNone(delayed.stream)
                delayed.handle(record("first emit"))
                self.assertTrue(delayed_path.exists())
            finally:
                delayed.close()

    def test_reserved_extra_keys_raise_even_if_diagnostics_disabled(self):
        logging.raiseExceptions = False
        logger = logging.Logger("isolated", logging.INFO)
        handler = logging.NullHandler()
        logger.addHandler(handler)
        self.addCleanup(handler.close)
        for key in ("message", "asctime", "levelname"):
            with self.subTest(key=key), self.assertRaises(KeyError):
                logger.info("event", extra={key: "collision"})


if __name__ == "__main__":
    unittest.main()
