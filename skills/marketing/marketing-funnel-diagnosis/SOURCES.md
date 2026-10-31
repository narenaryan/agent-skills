# Sources and validation

Reviewed 2026-10-27. This is a focused extension of the existing funnel skill,
not a separate generic SEO checklist. Historical source dates are not discovery
dates. No private Search Console, analytics, or user-site evidence was used.

## Primary references

- [Hynek Schlawack, Canonical SEO Failure](https://hynek.me/articles/canonical-seo-fail/), published 2021-04-28; retained lead first recorded 2026-10-24. Original first-person account: a shared template pointed distinct pages at the homepage. The author reports different engine behavior and a long recovery. It motivates sampling multiple templates/engines; it does not establish a universal impact, timeline, or Google failure.
- [RFC 6596, The Canonical Link Relation](https://www.rfc-editor.org/rfc/rfc6596), April 2012, Informational (not Standards Track). Section 3 defines duplicate/content-superset targets, permits self-reference and cross-domain targets, and warns about multiple declarations and unsuitable targets. This is not a search-engine ranking algorithm.
- [Google: Specify canonical URLs](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls), current reference documentation reviewed 2026-10-27. Redirects, annotations and sitemaps differ in signal strength; conflicting preferences and JavaScript changes complicate diagnosis. Do not use robots blocking, URL removal, or noindex as a canonical-selection mechanism. Treat deployment, recrawl requests and campaign changes as separate authorized actions.
- [Google: Canonicalization](https://developers.google.com/search/docs/crawling-indexing/canonicalization), displayed update 2026-08-20, reviewed 2026-10-27. Selection considers multiple signals; a declaration is a preference, not a compulsory selection. Duplicate URLs are not inherently spam. Do not infer duplicate content from URL spelling alone.
- [Google: URL Inspection](https://support.google.com/webmasters/answer/9012289), reviewed 2026-10-27; no publication date asserted. Indexed and live reports answer different questions; selected canonical is an indexed-report field, not a live-test prediction. Preserve crawl timing when interpreting a recent correction.
- [Google: JavaScript SEO basics](https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics), reviewed 2026-10-27. Prefer unambiguous original markup; JavaScript-only canonical injection is possible, but changing an existing original declaration is discouraged. Capture both stages, and distinguish missing captures from observed absence.

The pre-existing [Amplitude funnel documentation](https://amplitude.com/docs/analytics/charts/funnel-analysis/funnel-analysis-interpret) and [Microsoft metric-interpretation paper](https://www.microsoft.com/en-us/research/wp-content/uploads/2020/08/2017-08-KDDMetricInterpretationPitfalls.pdf) remain the foundations for cohort/order/window and ratio interpretation. Today's experiment does not newly validate those providers or estimate a causal effect.

## Original bounded experiment

`reproduce.py` uses Python's standard-library HTML parser on generated, well-formed
HTML-head snapshots. `rendered` is a supplied synthetic post-render capture, not
an actual browser/JavaScript execution. Header targets are already parsed inputs;
intended mapping and target content compatibility are explicitly supplied after
manual review, not guessed by the fixture.

The baseline only checks for a canonical tag and accepts two distinct pages
pointing at the homepage. The remedy checks the intended mapping and detects both
mismatches. Corrected fixture output passes that local check while retaining
unknown indexed selection and unproven acquisition effect. Counterexamples cover
legitimate duplicates and content supersets, header/render conflicts, rendered removal, missing
captures, repeated tags, body-only tags, absent declarations, targets needing
review, directives, and stale versus post-fix indexed observations.

This fixture is a deterministic decision aid, not a production HTML/HTTP parser,
crawler, search simulator, content-equivalence detector or site auditor. It does
not follow redirects, resolve relative IRIs/base elements, model hreflang, execute
JavaScript, reproduce Google/Bing indexing, or measure rank, recrawl delay,
traffic, conversions or revenue. Snapshot input URLs are absolute; unsupported
or incomplete real captures need separate review, not silent normalization.

Run normal and optimized modes from the repository root:

```sh
python3 skills/marketing/marketing-funnel-diagnosis/reproduce.py
python3 -O skills/marketing/marketing-funnel-diagnosis/reproduce.py
```

Twenty original scenarios passed in both modes. Independent review and mutation
checks are recorded in the PR. No software installation, external crawling,
account access, production edit, campaign change or indexing request was made.
