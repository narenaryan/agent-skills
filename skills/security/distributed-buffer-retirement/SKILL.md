---
name: distributed-buffer-retirement
description: Use when a distributed worker rejects or aborts work but peers may still access pooled buffers, or a tenant-isolation fix needs evidence beyond error responses, cancellation signals, and successful patch deployment.
---

# Distributed Buffer Retirement

A rejected request, a stopped producer, and reusable memory are three different states. Retirement must join local ownership with remote quiescence; an error response proves neither.

## Separate the proof obligations

| Boundary | Required evidence | Misleading substitute |
|---|---|---|
| Intake | Rejection recognized before new handoff work; original error preserved | “Not finished” means admissible |
| Re-entry | Existing ownership and resume/retraction state reach their cleanup path | Reject every object carrying an abort flag |
| Read/commit | Every readable range belongs to this request and was initialized | Allocation size or transfer-complete signal |
| Release | All possible readers/writers have stopped, or are effectively fenced | Local cancellation, send failure, elapsed timer |
| Acknowledgment | Correct lifecycle generation and every expected participant | Reused request ID or duplicate ACK count |

## Build the regression contract

1. Draw the ownership graph, including metadata, source pages, destination pages, offload readers, and every rank. Record which operation publishes remote access. Partial publication matters even when setup returns failure.
2. In an authorized isolated harness, seed a predecessor's buffers with synthetic markers. Exercise intake rejection on both sides and on each side separately. Assert no forbidden handoff, no uninitialized read, original error delivery, and eventual peer cleanup separately. A safe timeout is still a liveness failure.
3. Pause a transfer after publication. Inject client cancellation, producer failure, and transport error independently. Try to reuse its destination for another synthetic tenant before delivering the delayed write. A baseline that frees on local error should expose corruption; guarded retirement must withhold reuse.
4. Arm ACK tracking before notifications; stop new submissions, then collect drain evidence from the full participant set. Reject stale generations and duplicate/unknown senders. A transport error whose completion is unknown cannot produce a trustworthy drained ACK.
5. Exercise lost ACKs and resource exhaustion. Without a proven transport lifetime bound or effective fencing, keep reuse unproven; a timeout is an availability policy, not a universal safety proof. Escalate containment decisions rather than silently holding unlimited memory.
6. Attach build/backend/topology/configuration, failure schedule, ownership observations, and negative controls to [verified closure](../rbvm-verified-closure/SKILL.md). Separate incident fix, latency improvement, and residual hardening; no production change or risk acceptance is authorized here.

Run the local model:

```bash
python3 skills/security/distributed-buffer-retirement/reproduce.py
```

It tests event-order counterexamples, not GPU, RDMA, SGLang, or fleet isolation. [Sources and limits](SOURCES.md) distinguish upstream patch scopes.

## Pitfalls

- Enlarging a pool avoids one trigger; it does not repair rejection semantics.
- Zeroing before reuse cannot prevent a delayed remote write after zeroing.
- Checksums detect some corruption; they neither revoke writers nor establish lifetime ownership.
- Passing one transport or symmetric topology does not cover other backends or asymmetric rejection.
