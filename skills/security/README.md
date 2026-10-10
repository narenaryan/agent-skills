# security skills

Evidence-driven security workflows, from asset identity and applicability to guarded remediation and verified closure.

## Skills

- **[container-image-patching](container-image-patching/SKILL.md)** - scan Dockerfiles or images with Trivy, upgrade only fixed vulnerable packages, enforce a 20% image-size gate, and publish `-cve-patched` images.

- **[dnssec-sentinel-diagnostics](dnssec-sentinel-diagnostics/SKILL.md)** - distinguish trusted-key sentinel patterns from unsupported queries, failed controls, and mixed resolver paths.


- **[rbvm-asset-evidence](rbvm-asset-evidence/SKILL.md)** - reconcile identity, freshness and observation coverage without merging unrelated assets.
- **[rbvm-applicability](rbvm-applicability/SKILL.md)** - distinguish package matches, ecosystem versions, backports and scoped VEX evidence.
- **[rbvm-priority-decisions](rbvm-priority-decisions/SKILL.md)** - combine exploitation evidence and local impact into explainable decisions rather than uncalibrated score arithmetic.
- **[rbvm-guarded-remediation](rbvm-guarded-remediation/SKILL.md)** - revalidate state, resolve owners, bound retries and preserve approved action scope.
- **[rbvm-risk-exceptions](rbvm-risk-exceptions/SKILL.md)** - keep accepted risk scoped, owned, expiring and subject to evidence-triggered review.
- **[rbvm-verified-closure](rbvm-verified-closure/SKILL.md)** - require fresh deployed-artifact evidence before treating remediation as complete.
- **[security-gate-rollout](security-gate-rollout/SKILL.md)** - distinguish pass, fail and unknown while promoting policy from shadow to bounded enforcement.
- **[ai-triage-evaluation](ai-triage-evaluation/SKILL.md)** - evaluate legitimate task utility, false dismissals, prompt injection and tool effects independently.

## Use together

Start with identity and applicability, then prioritize. Guarded remediation and risk exceptions describe alternate dispositions; verified closure requires independent evidence afterward. Security gates prevent new debt; AI evaluation checks proposed automation. Reuse [container-image-patching](container-image-patching/SKILL.md) for the narrow patch recipe and [AI bug patterns](../engineering/ai-bug-patterns/SKILL.md) for implementation review. These skills do not grant permission to change production systems.

Each new skill links provenance, worked counterexamples, and offline standard-library fixtures. Passing those fixtures is not a production, scanner-engine, Kubernetes, or LLM benchmark result.

## Install

```bash
./install.sh security                 # install all
./install.sh container-image-patching # install one
```
