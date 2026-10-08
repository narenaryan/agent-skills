---
name: dnssec-sentinel-diagnostics
description: Use when checking DNSSEC root-key rollover readiness, interpreting root-key-sentinel SERVFAIL responses, or distinguishing an untrusted anchor from unsupported sentinel queries and resolver-path failures.
---

# DNSSEC Sentinel Diagnostics

A published DNSKEY is not evidence of a resolver's installed trust anchor. RFC 8509 deliberately turns one of two correctly signed sentinel answers into SERVFAIL. Interpret a controlled response pattern, never one successful lookup.

## Establish the measurement path

Record resolver endpoint, transport, timestamp, target key tag, and controls. A browser's Secure DNS/VPN path may differ from the application's resolver. Query one explicit endpoint; even one anycast address can hide inconsistent backends.

Use A/AAAA, exact leftmost sentinel labels, five-digit decimal tags, and checking enabled (`cd=false`). Sentinel processing requires Secure validation. `do=true` requests DNSSEC records; it does not independently validate them.

## Read the pattern

Check an ordinary signed control; require authenticated addresses for trust conclusions. Then evaluate these three queries together. Y means a matching address answer, not merely NOERROR; F means DNS SERVFAIL, not timeout/HTTP failure.

| is-ta | not-ta | Bogus control | Interpretation |
|---|---|---|---|
| Y | F | F | Consistent with trusted target |
| F | Y | F | Consistent with untrusted target |
| Y | Y | F | Sentinel unsupported/indeterminate; anchor unknown |
| Y | Y | Y | Validation not demonstrated; anchor unknown |
| Other | | | Inconclusive; investigate path/controls |

## Read-only example

Cloudflare-specific JSON DoH, with public test names:

```bash
for name in cloudflare.com dnssec-failed.org \
  root-key-sentinel-is-ta-38696.dnstest.dev \
  root-key-sentinel-not-ta-38696.dnstest.dev; do
  printf '\n%s\n' "$name"
  curl --fail --silent --show-error --max-time 15 \
    -H 'accept: application/dns-json' \
    "https://cloudflare-dns.com/dns-query?name=$name&type=A&cd=false"
done
```

Inspect DNS `Status` (0/2), address answers, and `AD`; HTTP 200 alone proves nothing. Repeat inconsistent results after relevant caches expire. Confirm missing trust through authorized operator inspection/vendor guidance before remediation; this recipe changes no settings.

## Sources and validation

[RFC 8509 §§2–4](https://www.rfc-editor.org/rfc/rfc8509.html), [Cloudflare's 2026-10-06 article](https://blog.cloudflare.com/root-ksk-2024-rollover/), and [IANA](https://www.iana.org/dnssec/files). On 2026-10-08, IANA lists 38696 for the scheduled October 11 rollover; recheck future tags/dates. [Evidence and tests](SOURCES.md) separate live observations from synthetic cases.

## Pitfalls

- Both sentinel answers succeeding does not establish readiness.
- `cd=true` bypasses sentinel preconditions; never classify that response as readiness.
- NXDOMAIN, empty NOERROR, failed controls, caching, and mixed forwarders invalidate simple conclusions.
- DoH JSON is provider-specific; one path's snapshot does not certify another resolver or future rollover success.
