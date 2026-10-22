# Prompt cache boundaries: sources and validation

Reviewed 2026-10-22. This is an original diagnostic workflow, not a provider emulator or cost benchmark. The monitored blog supplied the lead; the linked documentation supplies feature semantics, not new blog subscriptions.

## Primary references

- [Ryan Skidmore, Cloudflare inference optimization](https://blog.cloudflare.com/obsessive-inference-optimization/), published 2026-10-19, discovered in the earlier daily research backlog and reread 2026-10-22. The provider-bound prefix investigation motivates inspecting assembled requests rather than templates. Its reported results concern its own reviewer; the article explicitly limits its before/after attribution and describes quality tradeoffs. No reported saving is reproduced here.
- [Claude prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching), live documentation read 2026-10-22; no publication date inferred. Boundary placement, prior-write requirement, eligibility, and concurrency sections support the recipe. Check deployed model/platform documentation again: this skill does not freeze prices, token thresholds, or model availability.
- [Tool use with prompt caching](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-use-with-prompt-caching), live documentation read 2026-10-22; no publication date inferred. Supports the prefix hierarchy and tool-definition invalidation. Deferred/server tools have additional behavior; the fixture does not model them.
- [Claude cache diagnostics](https://platform.claude.com/docs/en/build-with-claude/cache-diagnostics), live documentation read 2026-10-22; no publication date inferred. Response-format, reason-type, usage-comparison, and limitation sections support the three-way distinction between divergence, inconclusive comparison, and observed reuse. Availability is Claude-API-specific; no SDK/version compatibility was exercised.

## Original counterexamples

The Python standard-library fixture serializes a deliberately limited synthetic envelope: model, workspace label, settings, tool definitions, and text-only system blocks. Its local prefix bytes are **not** Claude's internal prompt, tokenization, fingerprint, or cache key. JSON ordering is preserved, so a difference flags an audit question rather than proving a provider miss. The fixture refuses missing or multiple system breakpoints instead of pretending to cover all valid API requests.

The weak system-only comparison accepts a changed earlier tool; the guarded comparison detects it. A combined policy/environment block changes across jobs; splitting after the policy leaves the local prefix stable while retaining the suffix. Model, workspace, settings, ordering, and serialization changes remain visible. Identical local prefixes produce only `prefix-equal-only`, never `cache-hit`.

Hand-specified diagnostic cases check null/first-turn, missing opt-in, pending, missing predecessor, unavailable, divergence with partial reuse, and explicit positive/zero/missing read-token evidence. These are decision scenarios, not responses collected from a provider. Tests use explicit unittest assertions, including under `python3 -O`.

Observed on Python 3.12.14: all 15 test methods pass normally and with `-O`. Static checks cover the 500-word skill, frontmatter, local links, indexes, and Python syntax. The installer was dry-run only in scratch, with no skill files installed. The README's referenced `test.sh` is absent; no full-suite pass is claimed.

No SDK, provider API, credentials, customer prompts, software downloads, live cache, token counter, model output, billing, latency, or quality evaluation was used. Local safety/quality gates are this synthesis's policy, not claims of provider enforcement. Runtime inference validation remains necessary before claiming operational improvement.
