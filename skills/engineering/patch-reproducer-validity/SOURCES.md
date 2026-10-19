# Sources and validation limits

Reviewed October 19, 2026. Source publication dates below are separate from the review date.

## Primary sources

- Gunel Jahangirova, David Clark, Mark Harman, and Paolo Tonella, [“Test Oracle Assessment and Improvement”](https://discovery.ucl.ac.uk/id/eprint/1493269/), ISSTA 2016, DOI [10.1145/2931037.2931062](https://doi.org/10.1145/2931037.2931062). The authors combine generated test cases to expose false positives with mutation testing to expose false negatives, then evaluate the approach on five real-world subjects. This supports checking both what a test rejects and what it accepts. The small study does not establish a universal effectiveness gain.
- Goran Petrovic, [“Mutation Testing”](https://testing.googleblog.com/2021/04/mutation-testing.html), Google Testing Blog, April 12, 2021. The practitioner account explains killing and surviving mutants, targeted analysis during code review, and the substantial noise from redundant or equivalent mutants. Its internal Google experience is not a promise about another project's tooling or test quality.
- Goran Petrovic, Marko Ivanković, Gordon Fraser, and René Just, [“Practical Mutation Testing at Scale: A View from Google”](https://research.google/pubs/practical-mutation-testing-at-scale-a-view-from-google/), IEEE Transactions on Software Engineering, August 2021. The research describes diff-focused mutation, filtering, and feedback on actionability in Google's environment. It motivates keeping a manual check focused on changed behavior; it does not require installing or running a mutation framework.

## Synthesis and limits

The skill applies the papers' test-oracle distinction to ordinary bug-fix review: hold the test and fixture constant, compare faulty and candidate behavior, use a controlled reversion only when the historical baseline is unavailable, and treat a mutant as a sensitivity probe rather than proof. The pagination example is synthetic and illustrates an off-by-one boundary; it is not a reproduced project defect. These sources do not prove that every bug has an automated oracle, that all mutants represent real faults, or that a passing test suite proves correctness.

## Validation

- Static checks: matching frontmatter name/directory, a “Use when” trigger, final Pitfalls section, 494 whitespace-delimited skill words including frontmatter, valid local links, and no hard-coded root README counts.
- The standard-library fixture [`reproduce.py`](reproduce.py) is runnable from the repository root with `python3 skills/engineering/patch-reproducer-validity/reproduce.py`.
- Exact local run: Python 3.12.14; output was `BASELINE RED: expected [11, 12], got [11]`, `CANDIDATE GREEN: expected [11, 12], got [11, 12]`, and `WEAK ORACLE FALSE CONFIDENCE: nonempty check passes for both`.
- This is a synthetic decision-logic example only. No live application, production system, repository test suite, CI workflow, or mutation-testing tool was run.
