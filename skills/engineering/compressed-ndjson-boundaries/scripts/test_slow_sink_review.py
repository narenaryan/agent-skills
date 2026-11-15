"""Independent synthetic probes; no network, install, or user data."""
import asyncio
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import slow_sink as s


class ReviewTests(unittest.TestCase):
    def test_rejected_tail_preserves_existing_destination(self):
        async def probe(directory):
            target = Path(directory) / 'result.ndjson'
            target.write_bytes(b'previous verified result')
            source = s.GeneratedSource(256, 'truncated')
            with self.assertRaises(ExceptionGroup) as error:
                await asyncio.wait_for(s.pipeline(source, directory), 2)
            leaves = error.exception.exceptions
            self.assertTrue(any(isinstance(e, ValueError) and 'truncated' in str(e) for e in leaves))
            self.assertEqual(target.read_bytes(), b'previous verified result')
            self.assertFalse((Path(directory) / 'stage.ndjson').exists())
            self.assertTrue(source.closed)
            self.assertFalse(source.stats['decoder_open'])
        with tempfile.TemporaryDirectory() as d:
            asyncio.run(probe(d))

    def test_publish_failure_preserves_existing_destination(self):
        async def probe(directory):
            target = Path(directory) / 'result.ndjson'
            target.write_bytes(b'previous verified result')
            source = s.GeneratedSource(64)
            with patch.object(s.os, 'replace', side_effect=OSError('injected rename failure')):
                with self.assertRaisesRegex(OSError, 'injected rename failure'):
                    await asyncio.wait_for(s.pipeline(source, directory), 2)
            self.assertEqual(target.read_bytes(), b'previous verified result')
            self.assertFalse((Path(directory) / 'stage.ndjson').exists())
            self.assertTrue(source.closed)
            self.assertTrue(source.stats['tasks_done'])
        with tempfile.TemporaryDirectory() as d:
            asyncio.run(probe(d))

    def test_parent_cancellation_cleans_up_and_preserves_destination(self):
        async def probe(directory):
            target = Path(directory) / 'result.ndjson'
            target.write_bytes(b'previous verified result')
            source = s.GeneratedSource(10000)
            task = asyncio.create_task(s.pipeline(source, directory, max_items=1))
            for _ in range(5):
                await asyncio.sleep(0)
            self.assertFalse(task.done())
            self.assertGreater(source.frames_generated, 0)
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await asyncio.wait_for(task, 2)
            self.assertEqual(target.read_bytes(), b'previous verified result')
            self.assertFalse((Path(directory) / 'stage.ndjson').exists())
            self.assertTrue(source.closed)
            self.assertTrue(source.stats['tasks_done'])
            self.assertFalse(source.stats['decoder_open'])
            pending = [t for t in asyncio.all_tasks() if t is not asyncio.current_task() and not t.done()]
            self.assertEqual(pending, [])
        with tempfile.TemporaryDirectory() as d:
            asyncio.run(probe(d))

    def test_cancelled_child_cannot_publish(self):
        async def cancel_sleep(_delay):
            raise asyncio.CancelledError()
        async def probe(directory):
            target = Path(directory) / 'result.ndjson'
            target.write_bytes(b'previous verified result')
            source = s.GeneratedSource(64)
            # No queue wait: producer reaches clean EOF before sink self-cancels.
            # TaskGroup suppresses child cancellation; completion checks must not.
            with patch.object(s.asyncio, 'sleep', side_effect=cancel_sleep):
                with self.assertRaises(asyncio.CancelledError):
                    await asyncio.wait_for(s.pipeline(source, directory, max_items=0), 2)
            self.assertEqual(target.read_bytes(), b'previous verified result')
            self.assertFalse((Path(directory) / 'stage.ndjson').exists())
            self.assertTrue(source.closed)
            self.assertTrue(source.stats['tasks_done'])
        with tempfile.TemporaryDirectory() as d:
            asyncio.run(probe(d))

    def test_exact_record_byte_boundary(self):
        raw = s.line(0)
        self.assertEqual(list(s.records(iter([raw]), limit=len(raw)-1)), [raw])
        with self.assertRaisesRegex(ValueError, 'record limit'):
            list(s.records(iter([raw]), limit=len(raw)-2))

    def test_sink_exception_is_not_timeout(self):
        async def probe(directory):
            source = s.GeneratedSource(10000)
            with self.assertRaises(ExceptionGroup) as error:
                await asyncio.wait_for(s.pipeline(source, directory, max_items=1, fail_after=1), 2)
            self.assertTrue(any(isinstance(e, OSError) and 'injected sink' in str(e) for e in error.exception.exceptions))
            self.assertTrue(source.closed)
            self.assertTrue(source.stats['tasks_done'])
            self.assertFalse(source.stats['decoder_open'])
        with tempfile.TemporaryDirectory() as d:
            asyncio.run(probe(d))


if __name__ == '__main__':
    unittest.main(verbosity=2)
