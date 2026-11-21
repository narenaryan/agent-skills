---
name: python-time-contracts
description: Use when Python timezone-aware timestamps lose events during deduplication, elapsed durations disagree across clock changes, zero-duration arithmetic changes an instant, or local scheduling accepts missing/ambiguous times.
---

# Python wall-time and instant contracts

An aware `datetime` is not a universal instant key. Python's arithmetic and comparison semantics depend on timezone-object identity; calendar intent and elapsed time require different operations.

## Choose the contract first

| Requirement | Operation |
|---|---|
| Elapsed interval | Convert both validated endpoints to UTC before subtracting |
| Instant ordering/deduplication | Compare/key by UTC datetimes, retaining original zone separately |
| Add elapsed hours | Convert to UTC, add, then convert back |
| Same local clock tomorrow | Advance local date; resolve the resulting wall time explicitly |

With the **same `tzinfo` object**, subtraction, equality and ordering ignore `fold`. Two repeated local readings can therefore compare equal, subtract to zero and collapse into one set entry despite representing different instants. During a repeated interval, comparing a local datetime directly with its UTC conversion can also return false. Normalize **both** operands for instant comparisons.

## Resolve local input before conversion

For naive wall input and a standard-library `ZoneInfo`, enumerate candidate instants and round-trip through UTC. Run this recipe in Python 3.12 with an already-available IANA database:

```python
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

def candidates(wall, zone):
    if wall.tzinfo is not None:
        raise ValueError("expected naive wall time")
    instants = set()
    for fold in (0, 1):
        local = wall.replace(tzinfo=zone, fold=fold)
        utc = local.astimezone(UTC)
        back = utc.astimezone(zone).replace(tzinfo=None)
        if back == wall:
            instants.add(utc)
    return sorted(instants)

choices = candidates(datetime(2024, 11, 3, 1, 30),
                     ZoneInfo("America/New_York"))
```

Zero candidates means a gap; one means an unambiguous reading; two require an explicit earlier/later policy. Do not silently move missing appointments or choose a fold for the owner. Persist recurrence wall time, zone key and resolution policy separately from any resolved UTC occurrence. This recipe ignores an input naive `fold` value deliberately: it discovers choices rather than honoring a previously resolved instant.

Validate with spring gaps, autumn folds, ordinary dates and non-hour transitions. [Original executable probes and limits](SOURCES.md) distinguish observed standard-library behavior from scheduler correctness.

## Pitfalls

- Constructor/`replace(tzinfo=...)` success is not local-time validity. `astimezone` to the same zone is not a normalization pass; round-trip through UTC.
- Adding even `timedelta(0)` resets `fold` to zero; do not use arithmetic as an identity-preserving copy.
- A local day need not mean 24 elapsed hours. Do not globally replace wall arithmetic with UTC arithmetic.
- `ZoneInfo.no_cache` changes identity-sensitive behavior, not the intended contract. Keep normal caching; use UTC explicitly.
- Missing timezone data is an environment failure, not a valid empty candidate list. Record runtime/data versions; future rule changes can alter future resolutions. No leap-second handling or arbitrary custom-`tzinfo` guarantee.
