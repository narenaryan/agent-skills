---
name: tls-trust-path-verification
description: Use when a certificate distrust, CA-bundle update, or TLS remediation appears complete but browsers, CLI tools, containers, or long-running application clients disagree about certificate acceptance.
---

# TLS Trust-Path Verification

Trust is a runtime decision, not a package version. Evidence belongs to a specific caller, verifier, trust configuration, connection, and peer identity; another client's result cannot close that path.

## Bind the evidence

| Boundary | Record or distinguish |
|---|---|
| Caller | Running artifact, process generation, SDK/HTTP adapter, deployed environment |
| Verifier | TLS backend/version; native OS, file, bundled, or custom trust; configured overrides |
| Lifecycle | Bundle identity and load time; context/pool generation; new versus reused connection |
| Peer | Intended hostname/SNI, presented chain, route and TLS-terminating proxy |
| Oracle | Expected rejection reason plus permitted-peer and wrong-hostname controls |

## Verification recipe

1. Trace the application's actual outbound call to its verifier. Inspect explicit client options before assuming OS defaults. Requests can use `REQUESTS_CA_BUNDLE`; its manual prepared-request flow needs environment settings explicitly merged. curl's trust source depends on its backend/build. An HTTPS proxy has a separate trust path from the origin.
2. Capture the approved policy change and baseline acceptance on a controlled fixture, not an arbitrary hostile endpoint. Preserve hostname checking. Trust-anchor removal, intermediate distrust, and revocation enforcement are different policies; reproduce the relevant one.
3. Verify activation, not merely file replacement. OpenSSL reads `CAfile` when loading it, while `CApath` lookup can be lazy. Replacing a bundle does not prove an existing context changed. In Python, loading another bundle adds trust; it is not a removal operation. Use the application's documented, authorized reload/context-replacement/redeployment path.
4. Test a fresh, non-resumed handshake through that application path. Record connection/session reuse. Reject the controlled disallowed chain for the expected certificate-policy reason; a timeout, DNS failure, or unrelated protocol failure is inconclusive. Require an allowed-chain success and wrong-hostname rejection under equivalent conditions. Passing controls is bounded evidence, not exhaustive PKI assurance.
5. Join results to each affected runtime generation using [verified closure](../rbvm-verified-closure/SKILL.md). Keep stale processes, untested proxy legs, and unreachable replicas verification-pending. A successful new context does not prove every pooled client adopted it.

## Local experiment

```bash
python3 skills/security/tls-trust-path-verification/reproduce.py
```

Uses installed Python/OpenSSL, disposable fixture certificates and in-memory TLS; no sockets, downloads, host trust edits, or production credentials. Demonstrates stale versus recreated contexts and additive trust. See [source/version and validation limits](SOURCES.md).

## Pitfalls

- Never “repair” authentication by disabling certificate or hostname verification.
- A green browser/curl test proves only that client's path, not the service's.
- Existing connections may keep working without a new certificate decision.
- Removing one root does not establish intermediate revocation or eliminate alternate chains.
- Diagnostic probes do not authorize trust changes, restarts, arbitrary scanning, or production remediation.
