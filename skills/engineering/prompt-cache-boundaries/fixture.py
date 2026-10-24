"""Original offline byte-layout and evidence cases, NOT a provider cache emulator."""

import copy
import json
import unittest


POLICY = "Review the proposed change. Preserve authorization boundaries.\n"
TOOLS = [
    {"name": "read_file", "description": "Read an approved file.",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}}},
    {"name": "list_files", "description": "List approved paths.",
     "input_schema": {"type": "object", "properties": {}}},
]


def request(cwd="/synthetic/a", *, split=True):
    """A toy assembled envelope, never sent to any API."""
    suffix = f"Working directory: {cwd}; date: 2026-10-22.\n"
    marked = {"type": "text", "text": POLICY, "cache_control": {"type": "ephemeral"}}
    system = [marked, {"type": "text", "text": suffix}]
    if not split:
        system = [{**marked, "text": POLICY + suffix}]
    return {"model": "synthetic-model-v1", "workspace": "synthetic-workspace-a",
            "settings": {"effort": "fixed"}, "tools": copy.deepcopy(TOOLS),
            "system": system, "messages": [{"role": "user", "content": "Check change A"}]}


def prefix_bytes(envelope):
    """Conservative local representation only; one text-system breakpoint supported."""
    blocks = envelope["system"]
    marks = [i for i, b in enumerate(blocks) if "cache_control" in b]
    if len(marks) != 1 or any(b.get("type") != "text" for b in blocks):
        raise ValueError("fixture supports exactly one text-system breakpoint")
    prefix = {k: envelope[k] for k in ("model", "workspace", "settings", "tools")}
    prefix["system"] = blocks[:marks[0] + 1]
    # Preserve insertion order: canonicalizing could conceal serializer drift.
    return json.dumps(prefix, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def compare(left, right):
    if any(left[k] != right[k] for k in ("model", "workspace", "settings")):
        return "scope-or-configuration-changed"
    if prefix_bytes(left) != prefix_bytes(right):
        return "prefix-changed"
    return "prefix-equal-only"  # Never claims availability, eligibility, or a hit.


def diagnostic_state(diagnostics, *, opted_in, has_prior_id):
    """Interpret supplied synthetic observations, not a client or response adapter."""
    if not opted_in or not has_prior_id:
        return "no-comparison"
    if diagnostics is None:
        return "no-divergence-reported"
    if "cache_miss_reason" not in diagnostics:
        return "unknown"
    reason = diagnostics["cache_miss_reason"]
    if reason is None:
        return "pending"
    if not isinstance(reason, dict):
        return "unknown"
    kind = reason.get("type")
    if kind in {"previous_message_not_found", "unavailable"}:
        return "no-comparison"
    if kind in {"model_changed", "system_changed", "tools_changed", "messages_changed"}:
        return "divergence-reported"
    return "unknown"


def read_evidence(usage):
    count = usage.get("cache_read_input_tokens")
    if type(count) is not int or count < 0:
        return "unknown"
    return "read-reported" if count else "no-read-reported"


class LayoutTests(unittest.TestCase):
    def test_volatile_combined_block_changes_prefix(self):
        self.assertEqual(compare(request(split=False), request("/synthetic/b", split=False)),
                         "prefix-changed")

    def test_split_leaves_prefix_equal_and_retains_context(self):
        left, right = request(), request("/synthetic/b")
        self.assertEqual(compare(left, right), "prefix-equal-only")
        self.assertNotEqual(left["system"][1], right["system"][1])
        for cwd in ("/synthetic/a", "/synthetic/b"):
            joined = "".join(b["text"] for b in request(cwd)["system"])
            self.assertEqual(joined, request(cwd, split=False)["system"][0]["text"])
        # Text equality is not a model-quality or role-semantics test.

    def test_weak_system_only_baseline_misses_tool_change(self):
        left, right = request(), request()
        right["tools"][0]["description"] = "Read approved files with numbered lines."
        self.assertEqual(left["system"], right["system"])  # Weak check accepts.
        self.assertEqual(compare(left, right), "prefix-changed")

    def test_tool_order_changes_audit_bytes(self):
        left, right = request(), request()
        right["tools"].reverse()
        self.assertEqual(compare(left, right), "prefix-changed")

    def test_schema_key_order_is_not_silently_canonicalized(self):
        left, right = request(), request()
        schema = right["tools"][0]["input_schema"]
        right["tools"][0]["input_schema"] = dict(reversed(list(schema.items())))
        self.assertEqual(left, right)  # Structural dict equality hides order.
        self.assertEqual(compare(left, right), "prefix-changed")

    def test_model_scope_and_settings_changes_are_visible(self):
        for key, value in (("model", "synthetic-model-v2"),
                           ("workspace", "synthetic-workspace-b"),
                           ("settings", {"effort": "different"})):
            with self.subTest(key=key):
                left, right = request(), request()
                right[key] = value
                self.assertEqual(compare(left, right), "scope-or-configuration-changed")

    def test_user_suffix_change_does_not_prove_cache_hit(self):
        left, right = request(), request()
        right["messages"][0]["content"] = "Check change B"
        self.assertEqual(compare(left, right), "prefix-equal-only")

    def test_unsupported_breakpoints_fail_explicitly(self):
        for count in (0, 2):
            with self.subTest(count=count):
                value = request()
                if count == 0:
                    del value["system"][0]["cache_control"]
                else:
                    value["system"][1]["cache_control"] = {"type": "ephemeral"}
                with self.assertRaises(ValueError):
                    prefix_bytes(value)

    def test_utf8_bytes_are_not_character_counts(self):
        # Byte/character distinction only: no tokenizer is exercised.
        value = request()
        value["system"][0]["text"] += "café"
        encoded = prefix_bytes(value)
        self.assertGreater(len(encoded), len(encoded.decode("utf-8")))


class EvidenceTests(unittest.TestCase):
    def test_null_without_comparison_context_is_inconclusive(self):
        for opted_in, has_prior_id in ((False, False), (False, True), (True, False)):
            with self.subTest(opted_in=opted_in, has_prior_id=has_prior_id):
                self.assertEqual(diagnostic_state(None, opted_in=opted_in,
                                                 has_prior_id=has_prior_id), "no-comparison")

    def test_null_with_context_does_not_override_zero_reads(self):
        self.assertEqual(diagnostic_state(None, opted_in=True, has_prior_id=True),
                         "no-divergence-reported")
        self.assertEqual(read_evidence({"cache_read_input_tokens": 0}), "no-read-reported")

    def test_pending_missing_and_unavailable_are_not_mismatches(self):
        for reason, expected in ((None, "pending"),
                                 ({"type": "previous_message_not_found"}, "no-comparison"),
                                 ({"type": "unavailable"}, "no-comparison")):
            with self.subTest(reason=reason):
                self.assertEqual(diagnostic_state({"cache_miss_reason": reason},
                                 opted_in=True, has_prior_id=True), expected)

    def test_divergence_can_coexist_with_some_reads(self):
        self.assertEqual(diagnostic_state({"cache_miss_reason": {"type": "messages_changed"}},
                         opted_in=True, has_prior_id=True), "divergence-reported")
        self.assertEqual(read_evidence({"cache_read_input_tokens": 1234}), "read-reported")

    def test_missing_or_malformed_usage_is_unknown(self):
        for value in ({}, {"cache_read_input_tokens": None}, {"cache_read_input_tokens": -1},
                      {"cache_read_input_tokens": "0"}, {"cache_read_input_tokens": True}):
            with self.subTest(value=value):
                self.assertEqual(read_evidence(value), "unknown")

    def test_unrecognized_diagnostic_is_unknown(self):
        for value in ({}, {"cache_miss_reason": "unexpected"},
                      {"cache_miss_reason": {"type": "future_reason"}}):
            with self.subTest(value=value):
                self.assertEqual(diagnostic_state(value, opted_in=True, has_prior_id=True), "unknown")


if __name__ == "__main__":
    unittest.main(verbosity=2)
