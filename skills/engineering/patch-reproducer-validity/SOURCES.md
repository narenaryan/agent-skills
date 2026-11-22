# Sources and validation limits

Reviewed October 23, 2026. Source publication dates below are separate from the review date.

## Primary sources

- Gunel Jahangirova, David Clark, Mark Harman, and Paolo Tonella, [“Test Oracle Assessment and Improvement”](https://discovery.ucl.ac.uk/id/eprint/1493269/), ISSTA 2016, DOI [10.1145/2931037.2931062](https://doi.org/10.1145/2931037.2931062). The authors combine generated test cases to expose false positives with mutation testing to expose false negatives, then evaluate the approach on five real-world subjects. This supports checking both what a test rejects and what it accepts. The small study does not establish a universal effectiveness gain.
- Goran Petrovic, [“Mutation Testing”](https://testing.googleblog.com/2021/04/mutation-testing.html), Google Testing Blog, April 12, 2021. The practitioner account explains killing and surviving mutants, targeted analysis during code review, and the substantial noise from redundant or equivalent mutants. Its internal Google experience is not a promise about another project's tooling or test quality.
- Goran Petrovic, Gordon Fraser, Marko Ivanković, and René Just, [“Practical Mutation Testing at Scale: A View from Google”](https://research.google/pubs/practical-mutation-testing-at-scale-a-view-from-google/), IEEE Transactions on Software Engineering, 2021. The research describes diff-focused mutation, filtering, and feedback on actionability in Google's environment. It motivates keeping a manual check focused on changed behavior; it does not require installing or running a mutation framework.

- Anish Naik and Marcelo Morales, [“Your AI agent fixed the bug, but what else did it change?”](https://blog.trailofbits.com/2026/10/21/your-ai-agent-fixed-the-bug-but-what-else-did-it-change/), Trail of Bits, October 21, 2026. The original article distinguishes newly broken reachable behavior from incomplete repairs and prior defects, and describes paired replay and a complete patch revert. Its preliminary agent-evaluation results are not validation of this skill. The linked regression-hunt page was unavailable to the web reader; no plugin was installed, executed, or copied.
- Python [3.12 unittest documentation](https://docs.python.org/3.12/library/unittest.html) and [assert statement semantics](https://docs.python.org/3.12/reference/simple_stmts.html#the-assert-statement), documentation reviewed October 23, 2026. Ordinary `assert` statements can be omitted under `-O`; the fixture uses `unittest` assertion methods and was run in both modes.

## Synthesis and limits

The skill applies the papers' test-oracle distinction to ordinary bug-fix review: hold the test and fixture constant, compare faulty and candidate behavior, use a controlled reversion as substitute baseline evidence only when the historical baseline is unavailable, and treat a mutant as a sensitivity probe rather than proof. A narrow isolated reversion for attribution is local synthesis; it is not the article’s full-patch three-arm proof. The pagination example is synthetic and illustrates an off-by-one boundary; it is not a reproduced project defect. These sources do not prove that every bug has an automated oracle, that all mutants represent real faults, or that a passing test suite proves correctness.

## Original paired scenarios

The toy API is positional pagination, not an ID cursor: offset 10 skips ten elements. Its declared contract includes a zero-length page and rejection of negative limits. `baseline_page`, `candidate_page`, `repaired_page`, and `partial_page` are deliberately imperfect local implementations; none is shipped as a usable pagination library.

| Case | Baseline / candidate | Review outcome |
|---|---|---|
| Two-item request | `[11]` / `[11, 12]` | Target case repaired |
| Zero limit, same patch | `[]` / `[11]` | Newly broken contract; revised slice restores `[]` while retaining the target fix |
| Three-item request, partial repair | `[11, 12]` / `[11, 12]` | Repair remains incomplete |
| Negative limit | Neither raises required `ValueError` | Pre-existing unresolved validation defect, not newly introduced |
| Nonempty-only oracle | Both truthy | Original off-by-one escapes the weak oracle |
| Unrelated environment, entrypoint, contract, fixture, or case changes | Nonmatching context | Attribution inconclusive |
| Setup error, no result, or inconsistent repetitions | Missing stable contract result | Attribution inconclusive |
| Private helper used outside its contract | Applicability explicitly false | Unsupported claim; not a rule dismissing hostile inputs |

`classify` consumes trusted, synthetic evidence labels. It cannot establish actual caller reachability, approval, provenance, test independence, source revisions, or environment equivalence. Its negative-input example explicitly retains a safe-rejection contract. A real workflow must gather those facts; changed output alone does not prove a defect. A new crash replacing a wrong value is explicitly tested: both labels remain failure, so reviewers must compare raw behavior and impact instead of calling the defect unchanged. Intentional dependency/configuration changes belong to the patch; only unrelated drift confounds attribution. Repeated local cases are not a statistical error-rate estimate.

This update adapts the research to the project's actual boundary: an executed library API can be appropriate evidence without requiring production access. A synthetic callable cannot prove a live application's behavior. Build failures require a separate supported-build contract; the fixture only models setup-error handling and does not execute a compiler or external project.

## Validation

From the repository root:

```bash
python3 skills/engineering/patch-reproducer-validity/reproduce.py
python3 -O skills/engineering/patch-reproducer-validity/reproduce.py
```

Fifteen original `unittest` methods pass in both modes with Python 3.12.14. They execute the pagination examples and check evidence labels, context mismatches, missing/unstable results, expected and unexpected exceptions, weak assertions, and applicability counterexamples. Only local in-memory data are used: no network, external code execution, scanners, production access, package installation, or model evaluation.

The entrypoint uses the existing standard-depth budget (650-word maximum). Static validation checks frontmatter/name/trigger, final Pitfalls, relative links and indexes, Python syntax, and whitespace. The README-referenced `test.sh` is absent; no claim is made that a repository-wide test suite ran. Historical installer dry-run evidence did not validate copied-package paths; no installer was invoked for the November 9 checks below.

## Backport coverage extension: November 6, 2026

- [Trail of Bits: Backporting security fixes at scale with Codex](https://blog.trailofbits.com/2026/11/02/backporting-security-fixes-at-scale-with-codex/), Artem Dinaburg, published November 2, 2026. Discovered November 2 and deeply reviewed November 6. Motivates adaptation, dependency investigation and separate regression review. Its preparation-time and inventory claims are not reproduced or generalized to remediation effectiveness.
- [Linux kernel: Backporting and conflict resolution](https://docs.kernel.org/process/backporting.html), Vegard Nossum; reference documentation, publication/update date not asserted. Reviewed November 6, 2026, especially prerequisite/incidental distinctions, error handling, refactored code and verification. Supports mapping an upstream helper fix to multiple older sites and inspecting error paths outside conflict hunks.
- [Linux stable release rules](https://docs.kernel.org/process/stable-kernel-rules.html); reference documentation, publication/update date not asserted. Reviewed November 6, 2026. Supports ordered prerequisite records, upstream/equivalent-fix provenance, justified adaptations and coverage across newer supported stable trees. Submission rules are Linux-specific; no submission or disclosure is authorized here.

The obligation table and executable lease/payload example are original synthesis. The model uses an eight-byte upper bound and two old implementations, not actual upstream code, kernel objects, exploits or operating-system resources. The target acquires a synthetic lease before validation; upstream after validation. One-site repair leaves the second path broken; copied rejection without release meets a weak oracle but violates the full contract. The complete variant satisfies the exercised rejection and release checks while preserving valid payloads.

Twelve new standard-library unittest methods passed normally and under -O with Python 3.12.14 on November 6, 2026. Cases cover upstream consolidation, each target baseline, partial/complete mappings, wrong cleanup, full versus weak oracles, acquisition order, valid lengths 0/1/7/8, rejected lengths 9/16/257, a deliberately omitted site check and invalid variant labels. The existing 15-method reproducer also passed in both modes unchanged.

These tests do not discover real caller paths, certify dependency completeness, reproduce a real CVE, or prove memory safety, concurrency, kernel build/boot behavior, all configurations, deployed applicability or production closure. A handwritten map can omit a site; actual project review and target runtime evidence remain necessary. No fetched code, package installation, production mutation or upstream communication occurred.


## Package-reference correction: November 9, 2026

Source review of [`install_skill` at main revision ee9cd3f](https://github.com/narenaryan/agent-skills/blob/ee9cd3fc55137a3bb021a67a29c4dffaaacfcd47/install.sh) shows that a copy destination uses the skill name, not its category path. The three `../../security/` references in the backport companion therefore left the flattened skill root. Even changing them to sibling paths would assume another skill was installed. They now use verified GitHub source URLs; local companions remain relative. This is a content correction, not an installer change or an offline guarantee for web links.

The main fixture invocation is explicitly repository-root relative. The companion's commands run from its containing directory in either layout. An already available Python interpreter is required; these instructions do not install anything.

From this skill's directory, run the original static/path-model regression checks:

```sh
python3 check_content_paths.py
python3 -O check_content_paths.py
```

Seven unittest methods passed normally and under `-O` on Python 3.12.14. These checks read only this skill's Markdown and compare string-based repository and flat-package paths. They show the old links resolve in the repository but not a flattened package, reject missing local companions and restored escaping references, preserve local links after relocation under paths containing spaces, and check the exact cross-skill source targets and command working-directory labels. They do not invoke the installer, create an installation, follow symlinks, run a browser/agent, fetch URLs, or establish end-to-end package behavior. External target contents were separately fetched from main on November 9. Kernel backport and stable-rule references were reread; technical backport advice is unchanged. Source publication dates are unchanged; this is a review/correction date.
