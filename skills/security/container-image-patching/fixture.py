"""Original offline decision-contract examples; not a Trivy JSON parser or scanner.

All identities, releases, and advisories are synthetic. `approved_release` models
an independently reviewed vendor fix; this fixture does not discover fixes,
compare ecosystem versions, attest metadata, or authorize execution/closure.
"""

from dataclasses import dataclass, replace

# (package class, ecosystem/distribution, installation path, package name)
Component = tuple[str, str, str, str]
Finding = tuple[Component, str]


@dataclass(frozen=True)
class Evidence:
    artifact: str
    platform: str
    scanner: str
    database: str
    configuration: str
    coverage_reviewed: bool
    completed: bool
    inventory: tuple[tuple[Component, str], ...]
    findings: frozenset[Finding]


def classify_upgrade(
    before: Evidence,
    after: Evidence,
    expected_before: str,
    expected_after: str,
    component: Component,
    advisory: str,
    approved_release: str,
) -> str:
    """Classify one reviewed upgrade, never global image safety or deployment."""
    if before.artifact != expected_before or after.artifact != expected_after:
        return "wrong-artifact"
    if not all((before.completed, after.completed,
                before.coverage_reviewed, after.coverage_reviewed)):
        return "unknown"
    for field in ("platform", "scanner", "database", "configuration"):
        if getattr(before, field) != getattr(after, field):
            return "incomparable"
    finding = (component, advisory)
    if finding not in before.findings:
        return "baseline-missing"
    if finding in after.findings:
        return "remaining"
    # Reject duplicate identities instead of silently keeping a dict's last row.
    for evidence in (before, after):
        keys = [key for key, _ in evidence.inventory]
        if len(keys) != len(set(keys)):
            return "ambiguous-inventory"
    old = dict(before.inventory).get(component)
    new = dict(after.inventory).get(component)
    if old is None or new != approved_release or old == new:
        return "upgrade-not-demonstrated"
    return "candidate-upgrade-evidence"


def main() -> None:
    os_package = ("os-pkgs", "fixture-distro-1", "/package-db", "libexample")
    copied_package = ("library", "fixture-ecosystem", "/app/vendor", "libexample")
    advisory = "SYNTHETIC-ADVISORY-1"
    before = Evidence(
        "fixture-manifest-before", "linux/amd64", "fixture-scanner-1",
        "fixture-db-1", "full-view-policy-1", True, True,
        ((os_package, "1.0-vendor1"),), frozenset({(os_package, advisory)}),
    )
    after = replace(
        before, artifact="fixture-manifest-after",
        inventory=((os_package, "1.0-vendor2"),), findings=frozenset(),
    )

    def evaluate(candidate: Evidence, baseline: Evidence = before) -> str:
        return classify_upgrade(
            baseline, candidate, before.artifact, after.artifact,
            os_package, advisory, "1.0-vendor2",
        )

    # A count-only oracle claims success even though the package never changed.
    hidden = replace(after, inventory=before.inventory,
                     configuration="ignore-advisory-1")
    assert not hidden.findings  # Deliberately weak oracle: false confidence.
    cases = [
        ("reviewed vendor release, same upstream version", after,
         "candidate-upgrade-evidence"),
        ("filtered disappearance without patch", hidden, "incomparable"),
        ("new database", replace(after, database="fixture-db-2"), "incomparable"),
        ("different scanner", replace(after, scanner="fixture-scanner-2"), "incomparable"),
        ("wrong platform", replace(after, platform="linux/arm64"), "incomparable"),
        ("wrong artifact", replace(after, artifact="unrelated-image"), "wrong-artifact"),
        ("failed scan with empty findings", replace(after, completed=False), "unknown"),
        ("unsupported or EOL coverage", replace(after, coverage_reviewed=False), "unknown"),
        ("unchanged package but absent finding", replace(after, inventory=before.inventory),
         "upgrade-not-demonstrated"),
        ("package vanished without removal evidence", replace(after, inventory=()),
         "upgrade-not-demonstrated"),
        ("finding still present", replace(after, findings=before.findings), "remaining"),
        ("duplicate inventory identity", replace(after, inventory=after.inventory * 2),
         "ambiguous-inventory"),
    ]
    for label, candidate, expected in cases:
        actual = evaluate(candidate)
        assert actual == expected, (label, expected, actual)
        print(f"PASS: {label}: {actual}")

    assert evaluate(after, replace(before, findings=frozenset())) == "baseline-missing"
    print("PASS: no original finding: baseline-missing")

    # Fixing the OS package must not close a separate bundled copy of the CVE.
    two_before = replace(
        before, inventory=before.inventory + ((copied_package, "1.0"),),
        findings=before.findings | {(copied_package, advisory)},
    )
    two_after = replace(
        after, inventory=after.inventory + ((copied_package, "1.0"),),
        findings=frozenset({(copied_package, advisory)}),
    )
    assert evaluate(two_after, two_before) == "candidate-upgrade-evidence"
    assert classify_upgrade(
        two_before, two_after, before.artifact, after.artifact,
        copied_package, advisory, "1.1",
    ) == "remaining"
    print("PASS: same advisory, separate copy: remains independently open")
    print("14 cases passed; synthetic decisions only, no scanner or image executed.")


if __name__ == "__main__":
    main()
