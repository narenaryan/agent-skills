---
name: compressed-ndjson-boundaries
description: Use when compressed NDJSON ingestion loses trailing records, fails at chunk boundaries, grows memory on long lines, or needs safe parallel decompression with simdjson and zstd.
---

# Compressed NDJSON boundaries

Compression frames, read chunks, and JSON records are different boundaries. Fixed chunks do not bound memory: an unfinished record, decoder window, parser, or work queue can still grow.

## Boundary contract

| Layer | Required invariant |
|---|---|
| Decompressor | Check every zstd result; physical EOF is successful only after frame completion (`ZSTD_decompressStream` returns zero). Consume concatenated frames and reject trailing garbage. |
| Framer | Cut after the last LF; retain only the unfinished suffix. Impose a record-byte limit before growing/copying. Accept CRLF; explicitly choose blank-line and final-LF policies. |
| Parser | Keep input alive and padded by `SIMDJSON_PADDING`; batch size must accommodate the largest document. Check setup, iteration, field-access errors, then `truncated_bytes()` after successful exhaustion. |
| Publication | Stage results until compressed integrity and record validation succeed; otherwise earlier callbacks can leak partial success before a bad footer. |

## Recipe

1. Set independent caps: compressed input buffer, output chunk, record bytes, zstd window (`ZSTD_DCtx_setParameter(ctx, ZSTD_d_windowLogMax, 20)` limits the window to 1 MiB), total decompressed bytes, workers, and queued chunks. Include parser allocations and application-retained results in the memory budget.
2. Parse complete lines; preserve split UTF-8 bytes until a complete record exists. Reject an oversized suffix instead of repeatedly doubling storage. At EOF, distinguish a permitted complete unterminated JSONL record from a truncated JSON value.
3. With simdjson, destroy/exhaust the stream before moving/refilling its buffer. Copy retained strings; document references expire on iterator advancement. On-Demand skips validation of untouched values: fully traverse and validate every scalar and key when whole-document validity matters.
4. Parallelize independent frames only when the writer guarantees record-aligned boundaries and bounded frame sizes. Check advertised content size before allocation; unknown size requires bounded streaming or rejection. Give each worker its own parser. A generic `.zst` file does not guarantee record alignment.

From repository root:

```bash
python3 skills/engineering/compressed-ndjson-boundaries/scripts/reproduce.py
```

[Sources and validation limits](SOURCES.md): Lemire (2026-10-01), simdjson 5.0.1, zstd 1.5.7. Tests exercise installed zstd plus Python's JSON oracle; simdjson and parallel throughput remain untested.

## Pitfalls

- `truncated_bytes()==0` does not prove skipped values are valid.
- Newline alignment does not authenticate input; checksums detect corruption, not attackers.
- Bounded queues cannot compensate for uncapped per-record/frame allocations.
