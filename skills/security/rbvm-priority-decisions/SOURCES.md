# Priority decisions: evidence, provenance, and policy tests

Reviewed 2026-10-10. This skill proposes a decision-record workflow; it does not create an organization-wide SLA, authorize changes, or claim a new calibrated risk model.

## Primary sources

- [CISA official KEV repository](https://github.com/cisagov/kev-data), live mirror. README establishes that it mirrors CISA's catalog and can lag the canonical source briefly. Pin the downloaded catalog revision/date and retrieval time for operational decisions. Direct CISA catalog and SSVC pages failed to load during this review; no current legal deadline or applicability is asserted from those unavailable pages.
- [FIRST EPSS overview](https://www.first.org/epss/), live documentation: daily probability and ranking percentile, 30-day horizon. [Using EPSS](https://www.first.org/epss/using-epss.html), **What EPSS measures**, clarifies that its target is exploitation observed across data partners, not local susceptibility or complete organizational risk. Save the actual model version supplied with operational data; this review did not retrieve a scored feed and does not assert a current model number.
- [FIRST CVSS v4.0 specification](https://www.first.org/cvss/v4.0/specification-document), **Supplemental Metrics**: these add context without changing the computed CVSS score. Save vectors and score nomenclature so Base and context-enriched scores are not silently conflated.
- [CERT/CC SSVC deployer decision model](https://certcc.github.io/SSVC/howto/deployer_tree/), model **ssvc:DT_DP:1.0.0** as rendered on review date. Inputs are **E:1.1.0**, **EXP:1.0.1**, **A:2.0.0**, and **HI:2.0.2**; outcomes use **DSOI:1.0.0**. Its unit of work joins remediation/mitigation to a deployed instance. Mitigations can become invalid; remediated vulnerabilities can return after rollback. Do not mix CISA coordinator-style labels with this deployer table.
- [CERT/CC gathering exploitation evidence](https://certcc.github.io/SSVC/howto/gathering_info/exploitation/), live guidance. Distinguish credible exploitation observations from forecasts or merely available demonstration code.

## Original worked scenarios

1. **Observed vs forecast:** synthetic finding A is affected, KEV-listed, and has EPSS 0.001. The local gate below returns known-exploitation review. B is affected, not known exploited, and EPSS 0.90; it proceeds to the approved decision model. This does not assert A always outranks B after mission, safety, and obligations are considered.
2. **Rank confusion:** probability 0.02 and percentile 0.95 mean a 2% modeled probability and a high relative ranking, not a 95% probability. Store both under different field names.
3. **Applicability unknown:** a KEV entry matches only a product name, with installed version unavailable. Open urgent applicability investigation and known-exploitation review in parallel. Do not claim actual compromise, silently close the finding, or wait for a perfect SBOM before involving its owner.
4. **False equivalence:** two assets share the same CVSS vector; one supports a critical service and the other is an isolated lab. Their context can justify different decisions. A naked score cannot preserve that rationale.
5. **Missing feed:** yesterday's EPSS ingest fails for one CVE. Missing must remain missing. Substituting 0 silently favors that item over findings with properly collected scores.
6. **Invalidated mitigation:** a routing change exposes a previously restricted service. Reassess the evidence and decision path; the old mitigation ticket is not proof of current protection.

## Offline policy fixture

From the repository root:

```bash
python3 skills/security/rbvm-priority-decisions/fixture.py
```

This synthetic pre-triage gate demonstrates independent queues and non-downgrade behavior. It is NOT an SSVC implementation, risk calculator, production SLA, or scanner benchmark. Approved SSVC decisions still require the full versioned decision table and validated inputs. EPSS is intentionally retained without driving this gate; it belongs in the subsequent approved prioritization policy.
