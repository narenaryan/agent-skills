# Sources and verification

Reviewed 2026-10-07. The initiating article was published 2026-10-01; this is an archive/backlog investigation, not a newly published article alert. The skill is an original synthesis of boundary and resource contracts, not a copy of the benchmark program.

## Primary sources

- [Daniel Lemire, “Parsing compressed JSON at 40 GB/s”](https://lemire.me/blog/2026/10/01/parsing-compressed-json-at-40-gb-s/), 2026-10-01. Motivates complete-record chunks and independently decompressible, record-aligned frames. Its throughput is for synthetic repetitive data and specified hardware; no comparable speed claim is made here.
- [Compressed demo, pinned revision 960e878](https://github.com/simdjson/simdjson_compressed_demo/tree/960e8789efe5cdc4e67722b07bb32c21e6d5be94). Inspected `src/ndjson_stream.h`, `src/parallel_frames.h`, and `CMakeLists.txt`. The demo pins simdjson 5.0.1 and zstd 1.5.7. Its growable record/frame buffers need explicit application caps for an adversarial-input memory contract. We did not run or install this demo.
- [simdjson 5.0.1 iterate_many](https://github.com/simdjson/simdjson/blob/v5.0.1/doc/iterate_many.md) and [basics](https://github.com/simdjson/simdjson/blob/v5.0.1/doc/basics.md): padding, batch capacity, document/view lifetime, error handling, and final `truncated_bytes()` inspection. On-Demand is lazy; successful selected-field extraction is not full validation. No experimental parser API is required by this skill.
- [zstd 1.5.7 public header](https://github.com/facebook/zstd/blob/v1.5.7/lib/zstd.h): `ZSTD_decompressStream`, `ZSTD_DCtx_setParameter`, `ZSTD_d_windowLogMax`, frame-size sentinels, error checks and context lifetime. A positive decompression return means more decoding/flushing remains; zero means the current frame is fully decoded/flushed, not necessarily the end of a concatenated file. Window caps constrain streaming decoder memory, not total process RSS. These parameter APIs require zstd 1.4.0 or newer.
- [NDJSON specification](https://github.com/ndjson/ndjson-spec): UTF-8, LF/CRLF, no raw CR/LF within records, configurable empty-line handling. The reproduction chooses strict final-LF and no-blank-line policies. Accepting an unterminated final JSONL record would be a separate explicit policy and still requires valid JSON plus a clean compressed EOF.

## Reproduction and observed results

Run `python3 skills/engineering/compressed-ndjson-boundaries/scripts/reproduce.py` from repository root. Requires Python 3.10+ and an already installed libzstd >=1.4.0. It does not download software, contact services, modify files, or touch user data. Fixtures and compressed streams are synthetic inputs in memory.

Observed with Python 3.12.14 and libzstd 1.5.7 on Linux:

- 14 unittest methods passed, including exhaustive combinations of compressed-input and decoded-output chunk sizes for a UTF-8/CRLF/escaped-newline fixture.
- Parsing arbitrary seven-byte chunks fails; carrying the incomplete record succeeds with identical count and digest across all tested chunk sizes.
- Every possible interior split into two independently compressed frames succeeds through the sequential reader. This demonstrates why arbitrary frame boundaries cannot be handed straight to independent JSON parsers.
- Every truncation of the checked fixture, checksum corruption, trailing garbage, invalid JSON/UTF-8, missing final LF, and blank lines is rejected.
- Unknown advertised decompressed size succeeds with bounded streaming. Oversized records, excessive total decoded bytes, and a frame exceeding the window cap are rejected. Exact record-limit boundaries pass/fail as specified.
- Carry-buffer high water remains two bytes at 1, 100, and 100,000 `{}` records. This measures retained record bytes, not allocator overhead or process RSS. Fixture construction intentionally holds its test data in memory and is not a streaming-input memory benchmark.
- Summary publication occurs only after decompressor and record EOF checks. A production sink needs a bounded transactional/staging strategy; retaining all output in RAM would invalidate the memory claim.

The experiment uses Python's JSON decoder as a full-record correctness oracle. It does **not** execute simdjson, validate C++ lifetimes dynamically, measure parallel scheduling, reproduce throughput, or establish a numerical total-RSS ceiling. Those limits remain explicit; use the deployed parser/version and representative workloads for integration validation.

## Slow-sink extension, reviewed November 15, 2026

The existing carry-buffer experiment did not test a slow downstream sink. This extension isolates admission, failure lifetime and publication, rather than adding another parser or claiming faster ingestion.

Additional primary references:
- [Python 3.12 asyncio queues](https://docs.python.org/3.12/library/asyncio-queue.html): positive `maxsize` bounds queued items; awaited `put` waits for capacity.
- [Python 3.12 tasks](https://docs.python.org/3.12/library/asyncio-task.html): TaskGroup, available since 3.11, cancels siblings after a non-cancellation failure and waits for completion. Cancellation cleanup must propagate cancellation.
- [Python tracemalloc](https://docs.python.org/3.12/library/tracemalloc.html) and [resource usage](https://docs.python.org/3.12/library/resource.html): distinguish Python-traced allocations from process high-water memory.
- [Python os.replace](https://docs.python.org/3.12/library/os.html#os.replace): successful same-filesystem replacement is atomic; this experiment does not test crash durability.
- [Lemire, Reading JSON at 277 GB/s in Python](https://lemire.me/blog/2026/11/14/reading-json-at-277-gb-s-in-python/), published November 14, reviewed November 15: secondary motivation for checking output materialization and measurement boundaries. Its selected-field, free-threaded benchmark and pre-timed memory mapping are not reproduced here. No fastpysimdjson behavior or throughput claim follows from this fixture.

The original `scripts/slow_sink.py` imports the inspected existing ctypes bindings in `reproduce.py`. It generates at most 64 records per compressed frame, reads small chunks and uses an intentionally delayed sink. It writes only inside its own temporary directory and removes those files. It requires Python 3.11+ and installed libzstd; it downloads nothing. The companion's test command works from the skill directory after a single-skill copy.

Seven original methods passed normally and under `-O` on Python 3.12.14 and libzstd 1.5.7: bounded/unbounded digest agreement; queue occupancy across input sizes; 248 pending enqueue tasks hiding behind an eight-item queue; corrupt/truncated/oversized tails with no publication; eager partial-publication failure; injected sink failure canceling a capacity-blocked producer; total-output rejection. Existing 14 methods also passed unchanged in both modes.

Four fresh interpreter measurements after the cancellation/error-oracle correction observed:

| Records | Queue cap (0=unbounded) | Peak queued payload bytes | Python traced peak bytes | Linux process peak RSS KiB |
|---:|---:|---:|---:|---:|
| 256 | 0 | 38,034 | 125,828 | 21,688 |
| 256 | 8 | 1,192 | 104,832 | 21,688 |
| 16,384 | 0 | 2,462,874 | 3,369,558 | 25,300 |
| 16,384 | 8 | 1,208 | 251,849 | 21,564 |

These are single observations, not universal ceilings or performance estimates. Tracing starts after imports; RSS includes interpreter/native allocations. The bounded Python peak still changes. Queue payload bounds omit current producer/sink records, parser objects, decoder and allocator overhead. Disk staging grows with output and has a separate total-byte cap.

No simdjson/free-threaded extension, parallel decompression, throughput, adversarial filesystem, real disk-full, process crash, fsync, cross-filesystem/remote transaction, external cancellation-before-startup, production integration or agent-effectiveness validation. Synchronous calls are not preemptible. Independent review caught generic exception tests that could accept a timeout and canceled-child completion being mistaken for success. The fixture now checks exact error leaves and both task results before commit. Six committed independent probes pass normally and under `-O`: old-target preservation on truncation/rename failure, parent-cancellation cleanup, exact record cap, precise sink error, and canceled-child rejection. Memory-measurement mode is Linux-only so RSS units cannot be mislabeled on macOS.
