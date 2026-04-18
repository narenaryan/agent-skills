# python skills

Advanced Python runtime and language semantics distilled into focused skills for logging systems, Unicode correctness, and object model behavior.

## Skills

- **[python-descriptors-mro](python-descriptors-mro/SKILL.md)** - attribute lookup rules, descriptor precedence, `__set_name__`, `__slots__`, C3 linearization, and `super()` behavior in multiple inheritance.
- **[python-logging-cookbook](python-logging-cookbook/SKILL.md)** - production logging patterns with handler routing, `QueueHandler`/`QueueListener`, multiprocessing-safe aggregation, contextual fields, and `dictConfig` updates.
- **[python-unicode-gotchas](python-unicode-gotchas/SKILL.md)** - text encoding/decoding edge cases, normalization, BOM handling, round-trip safety with `surrogateescape`, and regex behavior across Unicode vs ASCII modes.

## Install

```bash
./install.sh python                   # install all
./install.sh python-logging-cookbook  # install one
```
