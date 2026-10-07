#!/usr/bin/env python3
"""Local synthetic zstd/framing experiments; no downloads, network, or file changes.
Requires Python 3.10+ and an already installed libzstd >= 1.4.0.
Uses Python json as a correctness oracle, NOT simdjson or a throughput benchmark.
"""
import ctypes as C
import ctypes.util
import hashlib
import io
import json
import unittest


class Buffer(C.Structure):
    _fields_ = [('data', C.c_void_p), ('size', C.c_size_t), ('pos', C.c_size_t)]


lib = C.CDLL(ctypes.util.find_library('zstd') or 'libzstd.so.1')


def bind(name, result, *args):
    f = getattr(lib, name)
    f.restype, f.argtypes = result, args
    return f


ptr, size = C.c_void_p, C.c_size_t
version = bind('ZSTD_versionNumber', C.c_uint)
is_error = bind('ZSTD_isError', C.c_uint, size)
error_name = bind('ZSTD_getErrorName', C.c_char_p, size)
create_d = bind('ZSTD_createDCtx', ptr)
free_d = bind('ZSTD_freeDCtx', size, ptr)
set_d = bind('ZSTD_DCtx_setParameter', size, ptr, C.c_int, C.c_int)
decode = bind('ZSTD_decompressStream', size, ptr, C.POINTER(Buffer), C.POINTER(Buffer))
create_c = bind('ZSTD_createCCtx', ptr)
free_c = bind('ZSTD_freeCCtx', size, ptr)
set_c = bind('ZSTD_CCtx_setParameter', size, ptr, C.c_int, C.c_int)
bound = bind('ZSTD_compressBound', size, size)
compress = bind('ZSTD_compress2', size, ptr, ptr, size, ptr, size)


def check(n):
    if is_error(n):
        raise ValueError(error_name(n).decode())
    return n


def frame(data, *, known_size=True):
    ctx = create_c()
    if not ctx:
        raise MemoryError('compression context')
    try:
        check(set_c(ctx, 201, 1))  # ZSTD_c_checksumFlag
        check(set_c(ctx, 200, int(known_size)))  # ZSTD_c_contentSizeFlag
        out = C.create_string_buffer(bound(len(data)))
        n = check(compress(ctx, out, len(out), data, len(data)))
        return out.raw[:n]
    finally:
        free_c(ctx)


class Records:
    """Strict one-value-per-line oracle; LF required, CRLF accepted; blank lines rejected."""
    def __init__(self, limit=128, total_limit=1 << 20):
        self.limit, self.total_limit = limit, total_limit
        self.carry = bytearray()
        self.peak = self.total = self.count = 0
        self.digest = hashlib.sha256()

    def feed(self, chunk):
        self.total += len(chunk)
        if self.total > self.total_limit:
            raise ValueError('total output limit')
        # Locate delimiters before copying: no temporary oversized record allocation.
        start = 0
        while start < len(chunk):
            end = chunk.find(b'\n', start)
            stop = len(chunk) if end < 0 else end
            if len(self.carry) + stop - start > self.limit:
                raise ValueError('record limit')
            self.carry.extend(chunk[start:stop])
            self.peak = max(self.peak, len(self.carry))
            if end < 0:
                break
            line = bytes(self.carry)
            if line.endswith(b'\r'):
                line = line[:-1]
            if not line.strip() or b'\r' in line:
                raise ValueError('blank line or raw CR')
            # Python rejects trailing garbage/two values; reject its nonstandard NaN too.
            def reject_constant(value):
                raise ValueError('non-JSON constant: ' + value)
            json.loads(line.decode('utf-8'), parse_constant=reject_constant)
            self.digest.update(line + b'\n')
            self.count += 1
            self.carry.clear()
            start = end + 1

    def finish(self):
        if self.carry:
            raise ValueError('missing final LF (strict NDJSON policy)')
        return self.count, self.digest.hexdigest(), self.peak


def consume(source, *, input_chunk=11, output_chunk=7, record_limit=128,
            total_limit=1 << 20, window_log=20):
    """Return staged summary only after clean compressed EOF AND valid record EOF.
    Bounds byte buffers and decoder window; JSON object overhead is not an exact RSS bound.
    """
    if min(input_chunk, output_chunk, record_limit, total_limit) < 1:
        raise ValueError('positive limits required')
    records = Records(record_limit, total_limit)
    ctx = create_d()
    if not ctx:
        raise MemoryError('decompression context')
    try:
        check(set_d(ctx, 100, window_log))  # ZSTD_d_windowLogMax, stable API
        output = C.create_string_buffer(output_chunk)
        last, saw_input = 1, False
        while True:
            data = source.read(input_chunk)
            if not data:
                if not saw_input or last != 0:
                    raise ValueError('empty or truncated compressed input')
                return records.finish()
            saw_input = True
            backing = C.create_string_buffer(data)
            inp = Buffer(C.cast(backing, ptr), len(data), 0)
            while True:
                before = inp.pos
                out = Buffer(C.cast(output, ptr), output_chunk, 0)
                last = check(decode(ctx, C.byref(out), C.byref(inp)))
                records.feed(output.raw[:out.pos])
                if inp.pos == inp.size and (last == 0 or out.pos < out.size):
                    break
                if inp.pos == before and out.pos == 0:
                    raise ValueError('decoder made no progress')
    finally:
        free_d(ctx)


class Experiments(unittest.TestCase):
    sample = b'{"x":"escaped\\nline","u":"\xc3\xa9"}\r\n{"x":2}\n'

    def test_all_chunk_boundaries(self):
        packed = frame(self.sample)
        expected = consume(io.BytesIO(packed))[:2]
        for incoming in range(1, len(packed) + 1):
            for outgoing in range(1, len(self.sample) + 1):
                with self.subTest(incoming=incoming, outgoing=outgoing):
                    result = consume(io.BytesIO(packed), input_chunk=incoming, output_chunk=outgoing)
                    self.assertEqual(result[:2], expected)
                    self.assertLessEqual(result[2], 128)

    def test_naive_chunk_parse_fails(self):
        with self.assertRaises((ValueError, UnicodeError)):
            for i in range(0, len(self.sample), 7):
                json.loads(self.sample[i:i + 7])

    def test_frame_boundary_is_not_record_boundary(self):
        for i in range(1, len(self.sample)):
            packed = frame(self.sample[:i]) + frame(self.sample[i:])
            self.assertEqual(consume(io.BytesIO(packed))[0], 2)

    def test_unknown_content_size(self):
        self.assertEqual(consume(io.BytesIO(frame(self.sample, known_size=False)))[0], 2)

    def test_every_truncation(self):
        packed = frame(self.sample)
        for i in range(len(packed)):
            with self.subTest(i=i), self.assertRaises(ValueError):
                consume(io.BytesIO(packed[:i]))

    def test_corrupt_checksum(self):
        packed = bytearray(frame(self.sample))
        packed[-1] ^= 1
        with self.assertRaises(ValueError):
            consume(io.BytesIO(packed))

    def test_trailing_garbage(self):
        with self.assertRaises(ValueError):
            consume(io.BytesIO(frame(self.sample) + b'garbage'))

    def test_record_limit_before_newline(self):
        with self.assertRaisesRegex(ValueError, 'record limit'):
            consume(io.BytesIO(frame(b'"' + b'a' * 10000)), record_limit=32)

    def test_exact_record_limit(self):
        self.assertEqual(consume(io.BytesIO(frame(b'"abcd"\n')), record_limit=6)[0], 1)
        with self.assertRaisesRegex(ValueError, 'record limit'):
            consume(io.BytesIO(frame(b'"abcde"\n')), record_limit=6)

    def test_json_and_delimiter_errors(self):
        for data in (b'{"x":\n', b'{} {}\n', b'\n', b'NaN\n', b'"\xff"\n', b'{}', b'{\r}\n'):
            with self.subTest(data=data), self.assertRaises((ValueError, UnicodeError)):
                consume(io.BytesIO(frame(data)))

    def test_total_output_limit(self):
        with self.assertRaisesRegex(ValueError, 'total output limit'):
            consume(io.BytesIO(frame(b'{}\n' * 1000)), total_limit=100)

    def test_stream_size_does_not_grow_carry(self):
        peaks = [consume(io.BytesIO(frame(b'{}\n' * n)), total_limit=1000000)[2]
                 for n in (1, 100, 100000)]
        self.assertEqual(peaks, [2, 2, 2])

    def test_window_limit(self):
        # A single-segment frame's window equals its declared content size.
        with self.assertRaisesRegex(ValueError, 'too much memory'):
            consume(io.BytesIO(frame(b'{}\n' * 10000)), window_log=10)

    def test_empty_frame(self):
        self.assertEqual(consume(io.BytesIO(frame(b'')))[0], 0)


if __name__ == '__main__':
    if version() < 10400:
        raise SystemExit('Requires installed libzstd >= 1.4.0; nothing was installed.')
    print('libzstd version:', version(), flush=True)
    unittest.main(verbosity=2)
