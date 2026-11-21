---
name: python-logging-cookbook
description: Use when Python log records disappear under queue pressure, QueueListener shutdown fails, sink levels are ignored, exceptions lose structured fields, or configuring handler routing, multiprocessing aggregation, contextual fields and incremental dictConfig.
---

# Python Logging Cookbook

Propagation bypasses ancestor logger levels/filters, not handler thresholds. Queue admission, handler completion, and durable delivery are different boundaries.

## Handler routing with level caps

```python
import logging
logger = logging.getLogger('app'); logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('debug.log');   fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler();            ch.setLevel(logging.ERROR)

class MaxLevel(logging.Filter):
    def __init__(self, lvl): self.lvl = lvl
    def filter(self, r):     return r.levelno <= self.lvl
fh.addFilter(MaxLevel(logging.WARNING))   # file: DEBUG–WARNING only
logger.addHandler(fh); logger.addHandler(ch)
```

## QueueHandler + QueueListener (non-blocking)

Offload sink I/O, not producer formatting. Queuing is not delivery:

```python
import logging
from logging.handlers import QueueHandler, QueueListener
from queue import Queue
que = Queue()  # unbounded: choose overflow policy before production
logger = logging.getLogger("demo")
logger.setLevel(logging.INFO)
logger.propagate = False
logger.addHandler(QueueHandler(que))
listener = QueueListener(que, logging.StreamHandler(), respect_handler_level=True)
listener.start()
try:
    logger.info("example")
finally:
    listener.stop()  # this example has no concurrent producers
```

| Boundary | Contract |
|----------|----------|
| Bounded queue full | Default `put_nowait()` fails; `emit()` calls `handleError()`, not caller-visible `queue.Full`. With `raiseExceptions=False`, the record can disappear silently. |
| Loss accounting | Override `handleError()` to count errors out-of-band. Never report through the same queue. Distinguish full admission from preparation failures. |
| Listener filtering | `respect_handler_level=False` bypasses sink level thresholds; use `True` when those thresholds matter. |
| Exception formatting | `prepare()` embeds traceback text in the message but clears queued `exc_info`/`exc_text`; downstream custom exception formatting needs an explicit serialization contract. |

For an owned, single-process FIFO queue with task tracking and healthy, terminating sinks: stop and join every producer, then `que.join()`, then `listener.stop()`. A full queue can reject the stop sentinel; merely checking `empty()` races. Accepted records after the sentinel can remain unread. Neither join nor stop provides a deadline: a hung/failed sink needs separate supervision. A drained queue does not prove durable output or account for dropped records.

## Multi-process logging

Separate process handlers cannot coordinate writes or rotation.

| Pattern | When |
|---------|------|
| `QueueHandler` + `mp.Queue` + single listener | in-tree workers |
| `SocketHandler` + aggregator | containers / separate hosts |
| `WatchedFileHandler` + external rotator (`logrotate`) | Unix, single writer |

`TimedRotatingFileHandler` is **unsafe across processes** — the rollover rename leaves other processes writing to the renamed file.

## Contextual info: Adapter vs Filter vs factory

| Mechanism | Modifies | Best for |
|-----------|----------|----------|
| `LoggerAdapter.process(msg, kwargs)` | injects extra; override to rewrite message | per-call ad-hoc context |
| `logging.Filter.filter(record)` | sets `record.X` attributes | structured fields used in `%(X)s` format |
| `logging.setLogRecordFactory` | every LogRecord globally | universal attributes (pid, hostname) |
| `contextvars.ContextVar` inside a Filter | async/request-scoped | producer-side, before queuing |

Return `False` from `Filter.filter` to drop records.

## dictConfig: incremental + preserve libraries

Set `disable_existing_loggers=False` in full `dictConfig` configurations. With `incremental=True`, only levels and propagation are updated; formatters and filters are ignored, and new handlers cannot be created.

## Library author rules

Attach `NullHandler`; let the application configure output.

Never call `basicConfig`, `StreamHandler`, or `setLevel` in library code — the application owns those decisions.

Evidence and executable failure/remedy probes: [SOURCES.md](SOURCES.md).

## Pitfalls

- **Double log lines:** a child logger with its own handler still propagates to ancestors. Set `propagate = False` or remove the ancestor handler.
- **`disable_existing_loggers` defaults to True:** third-party loggers go silent on first `dictConfig`. Set `False` explicitly.
- **Same file, multiple handlers:** writes/rotation may conflict; centralize the writer.
- **Per-connection logger names:** `logging.getLogger(f'app.conn.{id}')` leaks forever — use an Adapter or contextvars.
- **`FileHandler` defaults to eager open:** only `delay=True` defers opening until emission.
- **`exc_info=True` outside an except block:** returns `(None, None, None)` — pass the exception explicitly or use `logger.exception()` inside `except`.
- **`extra=` key collision:** reserved keys such as `message`, `asctime`, or `levelname` raise `KeyError` when an enabled event creates its record.
