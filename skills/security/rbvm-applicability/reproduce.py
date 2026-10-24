"""Original offline revision/cache counterexamples; not an OSV/VEX evaluator.

Only trusted synthetic dictionaries enter this example. Upstream validation,
authority, completeness, freshness, and adjudication are external obligations.
No network, package comparator, scanner, signatures, or suppression mutations.
"""

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import re
import unittest


NOW = datetime(2026, 10, 24, 12, tzinfo=timezone.utc)
OLD = "2026-10-22T09:00:00Z"
NEW = "2026-10-23T09:00:00Z"
SCOPE = ("sha256:synthetic-a", "config-a", "widget-instance-a")


class Reassess(ValueError):
    """Evidence is insufficient for reusing the reviewed decision."""


def instant(value, now=NOW, *, osv=False):
    # Deliberately narrow fixture profile: whole seconds, Z or minute offsets.
    # Not a complete RFC3339 implementation (fractional/leap seconds omitted).
    if not isinstance(value, str) or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(Z|[+-]\d{2}:\d{2})", value
    ) or (osv and not value.endswith("Z")):
        raise Reassess("unsupported timestamp")
    try:
        result = datetime.fromisoformat(value)
    except ValueError as error:
        raise Reassess("invalid timestamp") from error
    if result > now:
        raise Reassess("future timestamp")  # Zero tolerance is fixture policy.
    return result


def fingerprint(value):
    # JSON normalization is for this fixture, not a signature canonicalization.
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def select_osv(history, accepted_sources):
    """Retained history, including withdrawals; one accepted source per ID here."""
    groups = {}
    for row in history:
        identifier = row["id"]
        if accepted_sources.get(identifier) != row["source"]:
            raise Reassess("authority mismatch")
        modified = instant(row["modified"], osv=True)
        if "withdrawn" in row:
            withdrawn = instant(row["withdrawn"], osv=True)
            if withdrawn > modified:
                raise Reassess("withdrawal after record modification")
        groups.setdefault(identifier, []).append((modified, row))
    if set(groups) != set(accepted_sources):
        raise Reassess("missing expected advisory")
    selected = {}
    for identifier, revisions in groups.items():
        latest = max(revision for revision, _ in revisions)
        candidates = [row for revision, row in revisions if revision == latest]
        if len({fingerprint(row) for row in candidates}) != 1:
            raise Reassess("conflicting equal-revision payloads")
        selected[identifier] = deepcopy(candidates[0])
    return selected


def effective_time(statement, document, envelope=None):
    """Only timestamp inheritance; product inheritance is intentionally unmodeled."""
    for context in (statement, document, envelope or {}):
        if "timestamp" in context:
            return instant(context["timestamp"])
    raise Reassess("missing effective statement timestamp")


def dependency_key(scope, history, accepted_sources, vex, *, complete=True, fresh=True):
    """A binding for previously reviewed evidence, not a new applicability verdict.

    vex maps already selected (issuer, document ID) to current raw documents.
    The caller must validate schema, authority, scope, statement conflicts, and
    revision selection. No cross-document winner is inferred by this fixture.
    """
    if not complete or not fresh:
        raise Reassess("incomplete or stale retrieval")
    advisories = select_osv(history, accepted_sources)
    documents = []
    for (issuer, identifier), document in sorted(vex.items()):
        for statement in document["statements"]:
            effective_time(statement, document)
        documents.append([issuer, identifier, document])
    return fingerprint([scope, accepted_sources, advisories, documents])


def reuse_reviewed(old_key, *args, **kwargs):
    try:
        current_key = dependency_key(*args, **kwargs)
    except (Reassess, KeyError, TypeError, ValueError):
        return "reassess"
    return "eligible_for_reviewed_reuse" if old_key == current_key else "reassess"


def advisory(identifier="x_DEMO-A", modified=OLD, **changes):
    row = {
        "id": identifier, "source": "fixture-authority", "modified": modified,
        "aliases": ["x_DEMO-B"],
        "affected": [{"package": {"ecosystem": "fixture", "name": "widget"},
                      "versions": ["2.4.2"]}],
    }
    row.update(changes)
    return row


def vex_document(status="not_affected", version=1, timestamp=OLD):
    return {
        "version": version, "timestamp": timestamp,
        "statements": [{"vulnerability": "x_DEMO-A", "product": SCOPE[0],
                        "status": status, "justification": "component_not_present"}],
    }


class RevisionCases(unittest.TestCase):
    def setUp(self):
        self.history = [advisory()]
        self.authorities = {"x_DEMO-A": "fixture-authority"}
        self.vex = {("fixture-issuer", "document-a"): vex_document()}
        self.key = dependency_key(SCOPE, self.history, self.authorities, self.vex)

    def reuse(self, history=None, scope=SCOPE, vex=None, **kwargs):
        return reuse_reviewed(self.key, scope,
                             self.history if history is None else history,
                             self.authorities, self.vex if vex is None else vex,
                             **kwargs)

    def test_unchanged_reviewed_snapshot(self):
        self.assertEqual(self.reuse(), "eligible_for_reviewed_reuse")

    def test_new_affected_versions_invalidate_cve_only_cache(self):
        changed = advisory(modified=NEW, affected=[{"versions": ["2.4.2", "2.4.3"]}])
        weak_cache = {"x_DEMO-A": "not_affected"}
        self.assertEqual(weak_cache[changed["id"]], "not_affected")
        self.assertEqual(self.reuse(self.history + [changed]), "reassess")

    def test_delayed_old_delivery_does_not_replace_new_revision(self):
        new = advisory(modified=NEW)
        selected = select_osv([new, *self.history], self.authorities)
        self.assertEqual(selected["x_DEMO-A"]["modified"], NEW)

    def test_withdrawal_does_not_retire_alias_sibling(self):
        withdrawn = advisory(modified=NEW, withdrawn=NEW)
        sibling = advisory(identifier="x_DEMO-B", aliases=["x_DEMO-A"])
        sources = {**self.authorities, "x_DEMO-B": "fixture-authority"}
        selected = select_osv([withdrawn, sibling], sources)
        self.assertIn("withdrawn", selected["x_DEMO-A"])
        self.assertNotIn("withdrawn", selected["x_DEMO-B"])
        self.assertEqual(selected["x_DEMO-B"]["affected"][0]["versions"], ["2.4.2"])
        self.assertEqual(self.reuse(self.history + [withdrawn]), "reassess")

    def test_withdrawal_survives_older_replay(self):
        withdrawn = advisory(modified=NEW, withdrawn=NEW)
        selected = select_osv([withdrawn, *self.history], self.authorities)
        self.assertEqual(selected["x_DEMO-A"]["withdrawn"], NEW)

    def test_equal_revision_divergence_is_not_last_writer_wins(self):
        self.assertEqual(self.reuse([advisory(), advisory(aliases=[])]), "reassess")
        self.assertEqual(self.reuse([advisory(), advisory()]), "eligible_for_reviewed_reuse")

    def test_missing_record_and_failed_or_stale_fetch_are_not_withdrawals(self):
        self.assertEqual(self.reuse([]), "reassess")
        self.assertEqual(self.reuse(complete=False), "reassess")
        self.assertEqual(self.reuse(fresh=False), "reassess")

    def test_future_malformed_and_unzoned_dates_are_unknown(self):
        for timestamp in ("2027-01-01T00:00:00Z", "2026-02-30T00:00:00Z",
                          "2026-10-22T09:00:00", "2026-10-22T09:00:00+01:00"):
            with self.subTest(timestamp=timestamp):
                self.assertEqual(self.reuse([advisory(modified=timestamp)]), "reassess")

    def test_newer_unaccepted_source_does_not_authorize_reuse(self):
        row = advisory(modified=NEW, source="unaccepted-issuer")
        self.assertEqual(self.reuse([row]), "reassess")

    def test_artifact_configuration_and_package_instance_are_dependencies(self):
        for index in range(len(SCOPE)):
            changed = list(SCOPE)
            changed[index] += "-changed"
            self.assertEqual(self.reuse(scope=tuple(changed)), "reassess")

    def test_new_vex_under_investigation_invalidates_previous_verdict(self):
        changed = {("fixture-issuer", "document-a"):
                   vex_document("under_investigation", 2, NEW)}
        self.assertEqual(self.reuse(vex=changed), "reassess")

    def test_document_versions_do_not_rank_across_documents(self):
        documents = {**self.vex, ("other-accepted-issuer", "document-b"):
                     vex_document("under_investigation", 999, NEW)}
        self.assertEqual(self.reuse(vex=documents), "reassess")
        self.assertEqual(len(documents), 2)  # No largest-version winner retained.

    def test_statement_time_precedence_and_untouched_time(self):
        explicit = {"timestamp": OLD}
        document = {"timestamp": NEW, "last_updated": "2026-10-24T09:00:00Z"}
        self.assertEqual(effective_time(explicit, document), instant(OLD))
        self.assertEqual(effective_time({}, document), instant(NEW))
        self.assertEqual(effective_time({}, {}, {"timestamp": OLD}), instant(OLD))
        self.assertEqual(instant("2026-10-22T10:00:00+01:00"), instant(OLD))

    def test_missing_or_invalid_explicit_timestamp_does_not_fall_back(self):
        with self.assertRaises(Reassess):
            effective_time({}, {"last_updated": NEW})
        with self.assertRaises(Reassess):
            effective_time({"timestamp": "bad"}, {"timestamp": NEW})

    def test_relationship_change_invalidates_reviewed_binding(self):
        self.assertEqual(self.reuse([advisory(modified=NEW, aliases=[],
                                            related=["x_DEMO-B"])]), "reassess")


if __name__ == "__main__":
    unittest.main(verbosity=2)
