# Source ledger and validation boundaries

Reviewed October 25, 2026. This is original synthesis and an original offline experiment, not a portable production download implementation. Source publication dates below are separate from this review date.

## Primary references

- [RFC 9110: HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html), June 2022: §§8.8.1 and 8.8.3 (validators), §13.1.5 (If-Range), §§14.1.2–14.4 (byte ranges and metadata), and §15.3.7 (partial responses). These are the normative HTTP references. The skill's stricter checkpoint policy is an implementation choice, not a claim that every rejected response violates HTTP.
- [Requests Quickstart: Raw Response Content](https://requests.readthedocs.io/en/latest/user/quickstart/#raw-response-content), continuously updated documentation, displayed version 2.34.2 when reviewed. It distinguishes automatically decoded `iter_content` from the raw stream. This is an adapter warning, not a tested Requests integration. No Requests package was installed or run.
- [curl manual: --continue-at](https://curl.se/docs/manpage.html#-C), continuously updated documentation. The automatic offset is derived from input/output files. The skill's provenance warning is our inference: a local length alone does not bind the prefix to the currently selected representation. No curl transfer was executed.
- [Cloudflare: Origin Range Requests](https://blog.cloudflare.com/origin-range-requests/), Matthew Gumport, October 23, 2026; discovered October 24, reviewed October 25. Its technical explanation of range caching and encoded-versus-decoded ranges motivated this investigation. Its product configuration and reported performance figures are not imported into the skill, generalized, or independently reproduced. This article is not the normative source for client requirements.

## Original contract and experiment

The new capability is an evidence-preserving checkpoint splice: identity and geometry gates precede mutation. In the deliberately broken baseline, concatenating an old four-byte prefix with a new four-byte suffix produces an eight-byte artifact that matches neither source. The corrected contract refuses the changed validator and preserves the prefix; the matching-version case reconstructs the expected bytes and passes a separately supplied digest check.

Run from the repository root with Python 3.10+:

```bash
python3 skills/engineering/http-resume-integrity/reproduce.py
python3 -O skills/engineering/http-resume-integrity/reproduce.py
```

Eighteen original test methods passed on Python 3.12.14 in both modes. They cover equal-length version substitution, valid reconstruction, request headers, invalid validators, full-response refusal, unsatisfied-range refusal, error statuses, range geometry, unknown/changed totals, short valid intervals, coding/context/target changes, multipart refusal, body-length inconsistencies, absent Content-Length, an iterator raising after partial progress, byte budgets, duplicate retry commits, and incorrect bytes behind an unchanged validator.

Three deliberate in-memory mutations were detected by the original tests: ignoring a changed ETag, accepting a short body, and committing a stale checkpoint. These are narrow oracle-sensitivity checks, not exhaustive fault coverage.

The fixture uses immutable Python byte strings and normalized response records, not a server or client library. Staging is bounded by the declared known total and a per-chunk cap, but no memory-RSS/throughput benchmark or timing bound was tested. The compare-and-swap function is a sequential model, not an atomic filesystem or database primitive. Replacing files, crash recovery, concurrent workers, redirect authorization, credentials, TLS, HTTP framing, transfer decoding, cancellation delivery, signature verification, and trusted-metadata acquisition are not implemented or validated. An adapter must distinguish successful stream completion from interrupted exhaustion and reject ambiguous/duplicate headers before constructing a response record.

This deliberately conservative profile requires a known total, identity coding, one contiguous range, and a supported strong ASCII ETag. It rejects legal unknown-length responses, multipart responses, non-ASCII validators, and date validators rather than pretending to support them. It does not prove the prefix was originally persisted correctly; production storage must bind bytes and metadata durably. No ETag can replace the authority of an independently obtained digest or signature.

## Overlap and authority

`compressed-ndjson-boundaries` concerns decompression/parser record boundaries, not HTTP representation identity. `dependency-artifact-integrity` establishes artifact trust before execution; this skill prevents accidental byte splicing during transport and links to it rather than duplicating package-manager policy. `ai-bug-patterns` has general stale-state/TOCTOU guidance, not the response-specific resume contract.

Research and fixture execution authorize no download from an arbitrary host, production scan, deployment, credential change, TLS bypass, or automatic execution of a retrieved artifact. Use the task's existing network and mutation permissions.
