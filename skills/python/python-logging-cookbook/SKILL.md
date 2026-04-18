---
name: python-logging-cookbook
description: Use when configuring Python logging beyond basicConfig — non-blocking handlers for latency-sensitive paths, multi-process log aggregation, propagation control, injecting contextual attributes, dictConfig incremental updates, level routing per handler, or library authors avoiding handler conflicts; covers QueueHandler/QueueListener, SocketHandler, LoggerAdapter vs Filter, contextvars, NullHandler for libraries
---

# Python Logging Cookbook

A `LogRecord` propagates up the logger hierarchy (unless `propagate=False`). Each handler gates by its own level + filters; the logger's level is only an initial cutoff.

## Handler routing with level caps

```python
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

Park slow handlers (SMTP, Socket, rotating-file under contention) behind a queue:

```python
from logging.handlers import QueueHandler, QueueListener
from queue import Queue
que = Queue(-1)
logging.getLogger().addHandler(QueueHandler(que))
with QueueListener(que, slow_handler, respect_handler_level=True):
    run_app()             # Py3.14+: context manager auto-starts/stops
```

Before 3.14, call `listener.start()` / `.stop()` manually.

## Multi-process logging

One `FileHandler` per process → interleaved writes corrupt output.

| Pattern | When |
|---------|------|
| `QueueHandler` + `mp.Queue` + single listener | in-tree workers |
| `SocketHandler` + aggregator | containers / separate hosts |
| `WatchedFileHandler` + external rotator (`logrotate`) | Unix, single writer |

`TimedRotatingFileHandler` is **unsafe across processes** — the rollover rename leaves other processes writing to the renamed file.

## Contextual info: Adapter vs Filter vs factory

| Mechanism | Modifies | Best for |
|-----------|----------|----------|
| `LoggerAdapter.process(msg, kwargs)` | prefixes to message | per-call ad-hoc context |
| `logging.Filter.filter(record)` | sets `record.X` attributes | structured fields used in `%(X)s` format |
| `logging.setLogRecordFactory` | every LogRecord globally | universal attributes (pid, hostname) |
| `contextvars.ContextVar` inside a Filter | async/request-scoped | web handlers, asyncio tasks |

Return `False` from `Filter.filter` to drop the record entirely.

## dictConfig: incremental + preserve libraries

```python
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,   # keep library loggers alive
    ...
})

logging.config.dictConfig({
    'version': 1,
    'incremental': True,                 # only update levels/propagate; no new handlers
    'loggers': {'urllib3': {'level': 'WARNING'}},
})
```

`incremental=True` only updates logger levels, handler levels, and propagation — it cannot add/remove handlers or formatters.

## Library author rules

```python
# mylib/__init__.py
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())   # avoid "No handlers could be found"
```

Never call `basicConfig`, `StreamHandler`, or `setLevel` in library code — the application owns those decisions.

## Pitfalls

- **Double log lines:** a child logger with its own handler still propagates to ancestors. Set `propagate = False` or remove the ancestor handler.
- **`disable_existing_loggers` defaults to True:** third-party loggers go silent on first `dictConfig`. Set `False` explicitly.
- **Same file, multiple handlers:** interleaved writes corrupt lines. One handler, attach to multiple loggers.
- **Per-connection logger names:** `logging.getLogger(f'app.conn.{id}')` leaks forever — use an Adapter or contextvars.
- **`FileHandler` opens lazily:** a config error (bad path) surfaces on first log, not at config time.
- **`exc_info=True` outside an except block:** returns `(None, None, None)` — pass the exception explicitly or use `logger.exception()` inside `except`.
- **`extra=` key collision:** keys like `message`, `asctime`, `levelname` silently drop; record-reserved names cannot be overwritten.
