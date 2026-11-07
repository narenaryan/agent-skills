# Sources and validation

Reviewed November 7, 2026. This is an original bounded evidence-replay recipe, not a wallet implementation, incident reproduction or execution authorization.

## Primary sources

- [EIP-7702: Set Code for EOAs](https://eips.ethereum.org/EIPS/eip-7702), Vitalik Buterin, Sam Wilson, Ansgar Dietrichs and lightclient. Created May 7, 2024; Final status at review; update date not asserted. Specification / Behavior supports ordered authorization processing after sender nonce increment, per-tuple failure continuation, nonce/code checks, chain zero, zero-address clearing and non-rollback on execution failure. Security Considerations / Storage management explains why code changes do not establish safe storage migration. This reference is CC0; the local model is original, not copied client code.
- [Pectra](https://ethereum.org/roadmap/pectra/), ethereum.org. Page update October 16, 2026; reviewed November 7. Confirms Ethereum mainnet activation on May 7, 2025. Other chains require their own activation evidence.
- [After Binance, check what your signing systems can approve](https://blog.trailofbits.com/2026/11/06/after-binance-check-what-your-signing-systems-can-approve/), Tarun Bansal, Jaime Iglesias and Anish Naik. Published and discovered November 6, 2026; deep review November 7. Motivates separately reviewing authority changes, dedicated versus generic signing interfaces and approval binding. Incident claims are not independently reproduced here; no theft magnitude or causal attribution is asserted by this skill.

The EIP and ethereum.org are reference documentation, not additions to monitored blog registries. Local choices to preserve audit rows and mark missing state unknown are conservative evidence policy, not new protocol requirements.

## Distinction from existing coverage

Pinned main `ee9cd3fc55137a3bb021a67a29c4dffaaacfcd47` already has identity/freshness, applicability, IAM permission comparison, guarded remediation and verified closure. None supplies the EIP-7702 authorization-versus-execution rollback boundary. Open PRs 33–36 and 38–43 address unrelated buffers, encoding, retained keys, lookup, measurement, division, marketing, coalescing, sales and backports. This skill adds protocol-specific evidence interpretation, not another generic approval checklist.

## Fixture contract and counterexamples

`check_replay.py` uses trusted synthetic labels and post-sender-increment account snapshots. It models only ordered tuple decisions and nonce/delegation effects at the authorization stage, not final transaction state. Subsequent successful execution may further change account state, including nonce increments; reconcile those effects separately. Malformed envelope fields invalidate the entire transaction rather than becoming skipped tuples. `None` authority stands for a failed signature-validation result; labels never implement cryptographic recovery. Input structural bounds, envelope validity, sender increment, gas and cryptography are preconditions, not validated operations. Missing evidence raises `UnknownEvidence` without returning a clean verdict.

Baseline errors: infer no change from execution failure, stop the whole list at an invalid tuple, or retain only the first valid tuple per account. The oracle catches all three; remedies preserve each successful transition in order independent of execution status. Tests also cover chain zero, wrong chain, stale nonce, non-delegatable code, clearing, missing state, maximum nonce, multiple accounts and input-state isolation.

Run normally and with `python3 -O`. These are synthetic standard-library tests, not a consensus/client conformance suite. No actual RLP/Keccak/secp256k1, gas/refund accounting, block/reorg ingestion, live chain, signer policy enforcement, delegate execution/storage, monetary transfer, real attack, performance or production closure is validated. Approval binding and generic-interface coverage remain review obligations, not claims exercised by this fixture. No third-party code or installation is required.
