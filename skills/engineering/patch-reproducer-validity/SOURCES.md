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

The entrypoint uses the existing standard-depth budget (650-word maximum). Static validation checks frontmatter/name/trigger, final Pitfalls, relative links and indexes, Python syntax, and whitespace. The README-referenced `test.sh` is absent; no claim is made that a repository-wide test suite ran. An installer dry-run checks discovery only and does not install skills.
