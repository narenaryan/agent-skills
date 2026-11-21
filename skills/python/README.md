# python skills

Advanced Python runtime and language semantics distilled into focused skills for logging systems, Unicode correctness, object model behavior, and performance regression tests.

## Skills

- **[python-time-contracts](python-time-contracts/SKILL.md)** - preserve instant identity through folds, distinguish wall arithmetic from elapsed time, and resolve missing or ambiguous local input.

- **[python-scaling-regression-tests](python-scaling-regression-tests/SKILL.md)** - empirical growth-bound tests, meaningful input-size metrics, measurement isolation, and calibration with a deliberately slower implementation.
- **[python-descriptors-mro](python-descriptors-mro/SKILL.md)** - attribute lookup rules, descriptor precedence, `__set_name__`, `__slots__`, C3 linearization, and `super()` behavior in multiple inheritance.
- **[python-logging-cookbook](python-logging-cookbook/SKILL.md)** - logging routing and queue loss/shutdown contracts, multiprocessing aggregation, contextual fields, and `dictConfig` updates.
- **[python-unicode-gotchas](python-unicode-gotchas/SKILL.md)** - text encoding/decoding edge cases, normalization, BOM handling, round-trip safety with `surrogateescape`, and regex behavior across Unicode vs ASCII modes.

## Install

```bash
./install.sh python                   # install all
./install.sh python-logging-cookbook  # install one
```
