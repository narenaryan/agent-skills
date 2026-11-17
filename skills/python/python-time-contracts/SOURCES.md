# Sources and validation boundaries

Reviewed November 17, 2026. Original synthesis, not copied upstream code.

## Primary evidence

- [Python 3.12 datetime](https://docs.python.org/3.12/library/datetime.html#datetime-objects): arithmetic and comparison rules; same-zone `astimezone` behavior. The page rendered 3.12.16; the installed test runtime is CPython 3.12.14, so this is not a claim of testing 3.12.16 or every supported Python version. Page publication date not established.
- [Python 3.12 zoneinfo](https://docs.python.org/3.12/library/zoneinfo.html): fold-aware conversions, IANA data lookup, constructor caching and `no_cache` caution. The module was introduced in Python 3.9; this recipe uses `datetime.UTC`, introduced in 3.11. Data availability is a prerequisite, not part of the algorithm's gap result. Page publication date not established.
- [PEP 495](https://peps.python.org/pep-0495/), created August 2, 2015, Final, Python 3.6: permissive constructors, fold-insensitive same-zone operations, arithmetic resetting fold and the inter-zone equality exception. Historical specification, not a new publication.
- [Andrew Gallant's Jiff article](https://burntsushi.net/jiff/), published November 15, 2026, first observed November 16: retained research motivation concerning calendar intent versus elapsed time. Jiff API documentation retrieval was labeled rewritten summary; no Jiff API recipe, performance or conformance claim is made. No Rust toolchain was present.

## Original experiment

From this directory:

```sh
python -m unittest -v probe independent_probe
python -O -m unittest -v probe independent_probe
```

Ten primary and four independent methods pass in both modes on CPython 3.12.14 with system IANA data 2026b. Real standard-library operations demonstrate faulty local-key deduplication, unchecked-gap acceptance and wall-duration-as-elapsed baselines. UTC instant keys and explicit roundtrip resolution correct those tested cases. Additional cases exercise ordinary times, aware-input rejection, zero-duration fold reset and a half-hour Lord Howe transition. `no_cache` is used only to demonstrate identity sensitivity; no global cache or environment settings are changed.

The recipe enumerates PEP-495 fold choices for a `ZoneInfo` and naive wall input. It returns UTC candidates, not a decision about which occurrence a person wants. It deliberately ignores naive input `fold`; arithmetic near datetime range boundaries can raise `OverflowError`. Invalid zone keys and missing data raise rather than being converted to “no candidates.”

Independent source/content review found no blocking issues. The independent probes cover a deleted Apia day, transition-edge microseconds, exact snippet consistency and 2,880 minute-grid wall-time queries checked against a separate UTC-forward oracle. This is bounded actual-runtime evidence, not an exhaustive timezone proof.

## Limits

No general scheduler, recurrence persistence, timezone-database migration, leap-second support, custom timezone implementation, exhaustive historical/future-zone audit, performance benchmark or agent-effectiveness evaluation. No package installation, fetched third-party execution, host skill install, live calendar changes or timezone setting changes. Repository `test.sh` is absent; these are focused probes, not a full repository suite or CI pass.
