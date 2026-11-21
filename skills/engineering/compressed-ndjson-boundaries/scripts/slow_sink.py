#!/usr/bin/env python3
"""Original local experiment. Python 3.11+, installed libzstd; no network/install.
Only creates/deletes its own TemporaryDirectory. Not a production ingestion API.
"""
import asyncio
import ctypes as C
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import tracemalloc
import unittest
import reproduce as z


def line(i):
    return json.dumps({'id': i, 'text': 'x' * 128}, separators=(',', ':')).encode() + b'\n'


class GeneratedSource:
    """At most 64 small records per generated compressed frame, never whole input."""
    def __init__(self, count, fault=None):
        self.count, self.fault = count, fault
        self.next = 0
        self.pending = b''
        self.closed = False
        self.frames_generated = 0

    def read(self, size):
        if not self.pending and self.next < self.count:
            end = min(self.next + 64, self.count)
            data = b''.join(line(i) for i in range(self.next, end))
            if self.fault == 'long' and end == self.count:
                data += b'"' + b'x' * 4096
            packed = z.frame(data)
            if end == self.count:
                if self.fault == 'corrupt':
                    packed = packed[:-1] + bytes([packed[-1] ^ 1])
                elif self.fault == 'truncated':
                    packed = packed[:-1]
            self.pending, self.next = packed, end
            self.frames_generated += 1
        data, self.pending = self.pending[:size], self.pending[size:]
        return data

    def close(self):
        self.closed = True
        self.pending = b''


def chunks(source, stats, input_size=97, output_size=251):
    ctx = z.create_d()
    if not ctx:
        raise MemoryError('decompression context')
    stats['decoder_open'] = True
    try:
        z.check(z.set_d(ctx, 100, 20))
        output = C.create_string_buffer(output_size)
        last, seen = 1, False
        while True:
            data = source.read(input_size)
            if not data:
                if not seen or last != 0:
                    raise ValueError('empty/truncated compressed stream')
                return
            seen = True
            backing = C.create_string_buffer(data)
            inp = z.Buffer(C.cast(backing, z.ptr), len(data), 0)
            while True:
                before = inp.pos
                out = z.Buffer(C.cast(output, z.ptr), output_size, 0)
                last = z.check(z.decode(ctx, C.byref(out), C.byref(inp)))
                if out.pos:
                    yield output.raw[:out.pos]
                if inp.pos == inp.size and (last == 0 or out.pos < out.size):
                    break
                if inp.pos == before and not out.pos:
                    raise ValueError('decoder made no progress')
    finally:
        z.free_d(ctx)
        stats['decoder_open'] = False


def records(decoded, limit=256, total_limit=8 << 20):
    carry, total = bytearray(), 0
    for chunk in decoded:
        total += len(chunk)
        if total > total_limit:
            raise ValueError('total decoded limit')
        start = 0
        while start < len(chunk):
            end = chunk.find(b'\n', start)
            stop = len(chunk) if end < 0 else end
            if len(carry) + stop - start > limit:
                raise ValueError('record limit')
            carry.extend(chunk[start:stop])
            if end < 0:
                break
            record = bytes(carry)
            if record.endswith(b'\r'):
                record = record[:-1]
            if not record.strip() or b'\r' in record:
                raise ValueError('blank/raw CR')
            def reject_constant(v):
                raise ValueError(v)
            json.loads(record.decode('utf-8'), parse_constant=reject_constant)
            yield record + b'\n'
            carry.clear()
            start = end + 1
    if carry:
        raise ValueError('missing final LF')


async def pipeline(source, directory, max_items=8, fail_after=None, eager=False,
                   record_limit=256, total_limit=8 << 20):
    """Publish only after BOTH tasks finish. Same-directory rename is not crash durability.
    Eager=True deliberately exposes partial output as the faulty baseline.
    """
    queue = asyncio.Queue(maxsize=max_items)
    stats = {'queue_peak': 0, 'queued_bytes': 0, 'queue_bytes_peak': 0,
             'consumed': 0, 'decoder_open': False, 'tasks_done': False}
    destination = Path(directory) / 'result.ndjson'
    staging = Path(directory) / 'stage.ndjson'
    digest = hashlib.sha256()
    sentinel = object()
    decoded = chunks(source, stats)
    framed = records(decoded, record_limit, total_limit)

    async def producer():
        try:
            for record in framed:
                await queue.put(record)  # do not create one pending task per put
                stats['queued_bytes'] += len(record)
                stats['queue_peak'] = max(stats['queue_peak'], queue.qsize())
                stats['queue_bytes_peak'] = max(stats['queue_bytes_peak'], stats['queued_bytes'])
            await queue.put(sentinel)  # only after decoder and record EOF checks
        finally:
            framed.close()
            decoded.close()
            source.close()

    async def sink():
        with (destination if eager else staging).open('wb') as out:
            while True:
                record = await queue.get()
                if record is sentinel:
                    return
                stats['queued_bytes'] -= len(record)
                if fail_after is not None and stats['consumed'] == fail_after:
                    raise OSError('injected sink failure')
                out.write(record)
                digest.update(record)
                stats['consumed'] += 1
                await asyncio.sleep(0.001 if stats['consumed'] % 16 == 0 else 0)

    producer_task = sink_task = None
    try:
        async with asyncio.TaskGroup() as group:
            producer_task = group.create_task(producer())
            sink_task = group.create_task(sink())
        # A canceled child need not make TaskGroup.__aexit__ raise. Require results.
        producer_task.result()
        sink_task.result()
        if not eager:
            os.replace(staging, destination)
        stats['digest'] = digest.hexdigest()
        return stats
    finally:
        stats['tasks_done'] = all(t is not None and t.done() for t in (producer_task, sink_task))
        staging.unlink(missing_ok=True)
        source.stats = stats


def run(count, max_items=8, fault=None, fail_after=None, eager=False, **kwargs):
    source = GeneratedSource(count, fault)
    with tempfile.TemporaryDirectory(prefix='ndjson-slow-sink-') as directory:
        try:
            result = asyncio.run(asyncio.wait_for(pipeline(source, directory, max_items,
                                     fail_after, eager, **kwargs), timeout=20))
        except BaseException as exc:
            def leaves(error):
                if isinstance(error, BaseExceptionGroup):
                    return [leaf for nested in error.exceptions for leaf in leaves(nested)]
                return [{'type': type(error).__name__, 'message': str(error)}]
            result = source.stats | {'error': str(exc), 'error_leaves': leaves(exc)}
        target = Path(directory) / 'result.ndjson'
        result['published'] = target.exists()
        result['published_bytes'] = target.stat().st_size if target.exists() else 0
        result['stage_left'] = (Path(directory) / 'stage.ndjson').exists()
        result['source_closed'] = source.closed
        result['frames_generated'] = source.frames_generated
        return result


class SlowSinkTests(unittest.TestCase):
    def test_bounded_matches_unbounded(self):
        a, b = run(256, 0), run(256, 8)
        self.assertEqual(a['digest'], b['digest'])
        self.assertEqual(a['queue_peak'], 256)
        self.assertEqual(b['queue_peak'], 8)
        self.assertLessEqual(b['queue_bytes_peak'], 8 * 257)
        self.assertEqual(b['consumed'], 256)
        self.assertTrue(b['published'])

    def test_pending_put_tasks_bypass_queue_capacity(self):
        async def bad_dispatch():
            queue = asyncio.Queue(maxsize=8)
            tasks = [asyncio.create_task(queue.put(line(i))) for i in range(256)]
            await asyncio.sleep(0)
            queued = queue.qsize()
            pending = sum(not task.done() for task in tasks)
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            return queued, pending
        self.assertEqual(asyncio.run(bad_dispatch()), (8, 248))

    def test_count_scaling_does_not_scale_queue(self):
        for count in (64, 256, 1024):
            result = run(count)
            self.assertEqual(result['queue_peak'], 8)
            self.assertEqual(result['consumed'], count)

    def test_bad_tail_never_publishes(self):
        for fault in ('corrupt', 'truncated', 'long'):
            result = run(256, fault=fault)
            expected = {'corrupt': 'checksum', 'truncated': 'truncated', 'long': 'record limit'}[fault]
            self.assertEqual([e['type'] for e in result['error_leaves']], ['ValueError'])
            self.assertIn(expected, result['error_leaves'][0]['message'])
            self.assertGreater(result['consumed'], 0)
            self.assertFalse(result['published'])
            self.assertFalse(result['stage_left'])
            self.assertFalse(result['decoder_open'])
            self.assertTrue(result['tasks_done'])
            self.assertTrue(result['source_closed'])

    def test_eager_baseline_leaks_partial_output(self):
        result = run(256, fault='corrupt', eager=True)
        self.assertEqual([e['type'] for e in result['error_leaves']], ['ValueError'])
        self.assertIn('checksum', result['error_leaves'][0]['message'])
        self.assertGreater(result['published_bytes'], 0)

    def test_sink_failure_cancels_blocked_producer(self):
        result = run(10000, fail_after=1)
        self.assertEqual(result['error_leaves'], [{'type': 'OSError', 'message': 'injected sink failure'}])
        self.assertLess(result['frames_generated'], 157)
        self.assertFalse(result['decoder_open'])
        self.assertTrue(result['tasks_done'])
        self.assertFalse(result['published'])
        self.assertFalse(result['stage_left'])
        self.assertTrue(result['source_closed'])

    def test_total_limit_failure(self):
        result = run(256, total_limit=10000)
        self.assertEqual(result['error_leaves'], [{'type': 'ValueError', 'message': 'total decoded limit'}])
        self.assertFalse(result['published'])
        self.assertFalse(result['decoder_open'])
        self.assertTrue(result['tasks_done'])


if __name__ == '__main__':
    if len(sys.argv) == 4 and sys.argv[1] == 'measure':
        if sys.platform != 'linux':
            raise SystemExit('Memory measurement requires Linux: ru_maxrss units differ elsewhere.')
        import resource
        count, capacity = map(int, sys.argv[2:])
        tracemalloc.start()
        result = run(count, capacity)
        result['python_traced_peak_bytes'] = tracemalloc.get_traced_memory()[1]
        result['linux_process_peak_rss_kib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        result['records'] = count
        result['queue_capacity'] = capacity
        result['python'] = sys.version.split()[0]
        result['libzstd'] = z.version()
        print(json.dumps(result, sort_keys=True))
    else:
        unittest.main(verbosity=2)
