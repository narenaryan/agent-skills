# Sources and validation

Reviewed 2026-10-08. Original diagnostic synthesis, developed from the backlog;
publication date is distinct from discovery (2026-10-07) and review.

## Primary references

- [RFC 8509](https://www.rfc-editor.org/rfc/rfc8509.html), December 2018,
  sections 2–4: exact sentinel preconditions, response matrix, forwarding and
  multi-resolver ambiguity. Section 3 warns that unrelated SERVFAILs can mislead.
- [Cloudflare article](https://blog.cloudflare.com/root-ksk-2024-rollover/),
  published 2026-10-06: practical signed sentinel names and resolver-path controls.
- [Cloudflare JSON DoH API](https://developers.cloudflare.com/1.1.1.1/encryption/dns-over-https/make-api-requests/dns-json/),
  page updated 2026-05-05: GET parameters, CD/DO distinction, response fields.
  JSON is provider-specific, not an IETF-standardized DoH representation.
- [IANA trust-anchor status](https://www.iana.org/dnssec/files), checked
  2026-10-08: 38696 is KSK-2024, scheduled to replace the signer on 2026-10-11;
  20326 is KSK-2017. These dates/tags are a dated example, not permanent defaults.
- [ICANN checking guidance](https://www.icann.org/dns-resolvers-checking-current-trust-anchors):
  `dnssec-failed.org` is a deliberately invalid public validation test.

## Observed experiment

Public Cloudflare JSON DoH queries from the research environment only. No local
resolver, user network, trust store, or security setting was changed. DNS answers
are observations of that path, not proof of each backend's configuration.

On 2026-10-08 at 15:53:23–15:53:35 UTC, A queries with `cd=false` returned:

| Name | DNS Status | AD | Address present |
|---|---|---|---|
| cloudflare.com | 0 | true | yes |
| dnssec-failed.org | 2 | false | no |
| root-key-sentinel-is-ta-38696.dnstest.dev | 0 | true | yes |
| root-key-sentinel-not-ta-38696.dnstest.dev | 2 | false | no |
| root-key-sentinel-is-ta-00000.dnstest.dev | 2 | false | no |
| root-key-sentinel-not-ta-00000.dnstest.dev | 0 | true | yes |

The target pattern is consistent with trusted 38696; the deliberately different
00000 probe produced the converse pattern. Earlier queries also returned the
trusted pattern for 20326. Initial requests for two names timed out; those were
recorded as unknown, not SERVFAIL, and a subsequent complete group succeeded.

Changing only the per-query parameter to `cd=true` made both target sentinels and
the bogus control return addresses without AD. This reproduces why bypassing
checking invalidates the experiment, rather than repairing readiness. It does
not modify resolver configuration.

## Reproduction and limits

Run `python3 scripts/reproduce.py` or `python3 -O scripts/reproduce.py` from this
directory. Twelve unittest methods pass, including all eight Y/F triplets,
the positive-only false-readiness baseline, missing/transport failures, invalid
RCODEs, wrong questions, CD, truncation, empty answers, unauthenticated positives,
malformed addresses and JSON type confusion, SERVFAIL with answers, padded tags, and A/AAAA distinction.

The classifier intentionally accepts only direct, exact-owner addresses; CNAME
chains are inconclusive. It does not implement DNSSEC or validate signatures
itself. AD is a report from the chosen resolver over HTTPS. Synthetic unsupported
and malformed cases test interpretation, not a real unsupported resolver.

No server installation, local DNS configuration, rollover simulation, browser
path test, or production remediation was performed. A real trust-store repair
requires separate authorized operator work and retesting. The repository's
README-referenced `test.sh` is absent; no claim is made that it passed.

The exact shell example also ran successfully with curl 8.14.1, reproducing the
ordinary/Y/F/F control pattern. Python was 3.12.14. Names/frontmatter, 398-word
budget, source/relative links, provenance JSON, and 41-skill category/root counts
were checked. Bash syntax and an isolated installer dry-run passed (41 skills
plus one command discovered; no skills installed).
