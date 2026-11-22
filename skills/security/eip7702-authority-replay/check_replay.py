"""Original evidence model; trusted decoded inputs, not an Ethereum client."""
from dataclasses import dataclass, replace
import unittest

MAX_NONCE = 2**64 - 1
ZERO = "0x" + "00" * 20


class UnknownEvidence(ValueError):
    pass


@dataclass(frozen=True)
class Account:
    nonce: int
    code_kind: str = "empty"  # empty, delegated, or other
    delegate: str | None = None


@dataclass(frozen=True)
class Authorization:
    chain: int
    delegate: str
    nonce: int
    authority: str | None  # trusted recovery result, None means invalid signature


def replay(post_sender_state, tuples, chain, execution_succeeded, *, fault=None):
    """Subset replay after valid envelope and sender increment; no EVM execution.

    State must contain every successfully recovered authority, including explicit
    empty accounts. This function cannot recover absent historical account state.
    execution_succeeded is intentionally irrelevant to authorization persistence.
    fault selects deliberately incorrect baselines solely for mutation tests.
    """
    if tuples is None or post_sender_state is None:
        raise UnknownEvidence("Missing authorization list or ordered state")
    if not tuples:
        raise ValueError("Empty list is an invalid EIP-7702 envelope, not a no-op")
    state = dict(post_sender_state)
    rows = []
    applied = set()
    for i, auth in enumerate(tuples):
        reason = None
        if auth.chain not in (0, chain):
            reason = "wrong-chain"
        elif auth.nonce >= MAX_NONCE:
            reason = "nonce-bound"
        elif auth.authority is None:
            reason = "invalid-signature"
        else:
            if auth.authority not in state:
                raise UnknownEvidence("Missing account pre-state")
            account = state[auth.authority]
            if account.code_kind not in ("empty", "delegated"):
                reason = "code-kind"
            elif account.nonce != auth.nonce:
                reason = "nonce-mismatch"
        if reason:
            rows.append((i, "skipped", reason))
            if fault == "stop-at-invalid":
                break
            continue
        if fault == "first-only" and auth.authority in applied:
            continue
        clear = auth.delegate == ZERO
        state[auth.authority] = Account(
            account.nonce + 1, "empty" if clear else "delegated",
            None if clear else auth.delegate,
        )
        applied.add(auth.authority)
        rows.append((i, "applied", auth.authority, account.delegate,
                     state[auth.authority].delegate))
    if fault == "rollback-on-failure" and not execution_succeeded:
        return dict(post_sender_state), rows
    return state, rows


class ReplayTests(unittest.TestCase):
    def setUp(self):
        self.state = {"alice": Account(4), "bob": Account(7)}
        self.auth = Authorization(1, "delegate-a", 4, "alice")

    def run_case(self, tuples, **kwargs):
        return replay(self.state, tuples, 1, False, **kwargs)

    def test_reverted_execution_preserves_change(self):
        state, rows = self.run_case([self.auth])
        self.assertEqual(state["alice"], Account(5, "delegated", "delegate-a"))
        self.assertEqual(rows[0][1], "applied")

    def test_skip_invalid_then_apply(self):
        state, rows = self.run_case([replace(self.auth, chain=2), self.auth])
        self.assertEqual([row[1] for row in rows], ["skipped", "applied"])
        self.assertEqual(state["alice"].nonce, 5)

    def test_last_valid_replaces_earlier(self):
        state, rows = self.run_case([self.auth, replace(self.auth, nonce=5, delegate="delegate-b")])
        self.assertEqual(state["alice"].delegate, "delegate-b")
        self.assertEqual(state["alice"].nonce, 6)
        self.assertEqual(len(rows), 2)

    def test_invalid_later_does_not_replace(self):
        state, _ = self.run_case([self.auth, replace(self.auth, delegate="delegate-b")])
        self.assertEqual(state["alice"].delegate, "delegate-a")

    def test_clear_preserves_nonce_progress(self):
        state, _ = self.run_case([self.auth, replace(self.auth, nonce=5, delegate=ZERO)])
        self.assertEqual(state["alice"], Account(6))

    def test_chain_zero_is_protocol_valid(self):
        state, _ = self.run_case([replace(self.auth, chain=0)])
        self.assertEqual(state["alice"].nonce, 5)

    def test_bad_signature_skips(self):
        state, rows = self.run_case([replace(self.auth, authority=None)])
        self.assertEqual(state, self.state)
        self.assertEqual(rows[0][2], "invalid-signature")

    def test_other_code_rejected(self):
        self.state["alice"] = Account(4, "other")
        state, rows = self.run_case([self.auth])
        self.assertEqual(state, self.state)
        self.assertEqual(rows[0][2], "code-kind")

    def test_missing_evidence_is_unknown(self):
        with self.assertRaises(UnknownEvidence):
            self.run_case([replace(self.auth, authority="missing")])
        with self.assertRaises(UnknownEvidence):
            self.run_case(None)

    def test_empty_list_invalid(self):
        with self.assertRaises(ValueError):
            self.run_case([])

    def test_nonce_upper_boundary(self):
        self.state["alice"] = Account(MAX_NONCE - 1)
        state, rows = self.run_case([replace(self.auth, nonce=MAX_NONCE-1),
                                    replace(self.auth, nonce=MAX_NONCE)])
        self.assertEqual(state["alice"].nonce, MAX_NONCE)
        self.assertEqual(rows[-1][2], "nonce-bound")

    def test_multiple_accounts_and_no_input_mutation(self):
        before = dict(self.state)
        state, _ = self.run_case([self.auth, replace(self.auth, authority="bob", nonce=7)])
        self.assertEqual((state["alice"].nonce, state["bob"].nonce), (5, 8))
        self.assertEqual(self.state, before)

    def test_success_and_failure_same_authorization_state(self):
        self.assertEqual(replay(self.state, [self.auth], 1, True), self.run_case([self.auth]))

    def test_detect_three_faulty_baselines(self):
        cases = [
            ("rollback-on-failure", [self.auth]),
            ("stop-at-invalid", [replace(self.auth, chain=2), self.auth]),
            ("first-only", [self.auth, replace(self.auth, nonce=5, delegate="delegate-b")]),
        ]
        for fault, tuples in cases:
            with self.subTest(fault=fault):
                expected, _ = self.run_case(tuples)
                broken, _ = self.run_case(tuples, fault=fault)
                self.assertNotEqual(expected, broken)


if __name__ == "__main__":
    unittest.main(verbosity=2)
