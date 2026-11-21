# Logging boundary evidence

Reviewed November 18, 2026. This is a correction and extension of an existing
skill, not a newly published article or a throughput claim.

## Primary sources

- [Python 3.12 handler reference](https://docs.python.org/3.12/library/logging.handlers.html): queue admission uses nonblocking insertion; emission errors enter `handleError`; preparation removes structured exception fields; listener level filtering is opt-in; the sentinel uses nonblocking insertion; `FileHandler` defaults to `delay=False`.
- [CPython v3.12.14 implementation](https://github.com/python/cpython/blob/v3.12.14/Lib/logging/handlers.py): `QueueHandler.emit/prepare`, `QueueListener._monitor/stop/enqueue_sentinel`. Inspected as source only; tests use the installed standard library, not downloaded code.
- [CPython v3.12.14 logging core](https://github.com/python/cpython/blob/v3.12.14/Lib/logging/__init__.py): `Logger.makeRecord` raises `KeyError` for reserved `extra` keys; `FileHandler.__init__` opens unless delayed.
- [Logging API](https://docs.python.org/3.12/library/logging.html): propagation skips ancestor logger levels and filters; extras must not collide with reserved fields.
- [Queue API](https://docs.python.org/3.12/library/queue.html): size probes are not synchronization; `join` waits for task accounting, not durability. Nonpositive capacity is unbounded.
- [Logging Cookbook](https://docs.python.org/3.12/howto/logging-cookbook.html): threaded sink offloading, process aggregation and context fields. Capture request context on the producer side, before crossing threads.
- [Incremental configuration](https://docs.python.org/3.12/library/logging.config.html#incremental-configuration): existing levels/propagation, not a replacement object graph.

## Scope and reproduction

From the repository root:

```sh
python skills/python/python-logging-cookbook/validate_logging.py
python -O skills/python/python-logging-cookbook/validate_logging.py
python skills/python/python-logging-cookbook/independent_probe.py
python -O skills/python/python-logging-cookbook/independent_probe.py
```

The original probes exercise actual installed CPython logging and a finite,
owned in-process FIFO queue. Gated handlers establish queue-full ordering
without depending on sleep timing. Shutdown recovery is tested only with sinks
that return successfully. Stop all producers before draining; `join` and `stop`
can wait forever if downstream processing hangs. Task accounting cannot certify
persistence, nor recover events dropped before admission.

No multiprocess transport, SMTP/socket integration, disk durability, process
crash, Python 3.14 context-manager runtime, performance or agent-effectiveness
proof. The reference pages render Python 3.12.16 while the test runtime is
CPython 3.12.14. No dependencies installed, host skills installed, or live logging
configuration changed. Test modifications are confined to isolated processes.

Validated on CPython 3.12.14: eight contract tests plus three independently
authored boundary probes, all passing normally and with optimization enabled.
The independent probes cover stranded task accounting after a sink exception,
accepted records after the sentinel, and preparation errors versus queue-full
loss. These demonstrate the limits, not a general recovery mechanism.
