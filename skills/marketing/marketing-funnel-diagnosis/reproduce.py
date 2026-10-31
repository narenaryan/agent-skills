#!/usr/bin/env python3
"""Original, offline canonical-evidence scenarios; NOT a crawler or search engine.

The input is deliberately narrow: well-formed synthetic HTML heads, already
parsed canonical response-header targets, and manually reviewed intended URLs.
No network, browser rendering, actual indexing, or causal acquisition test.
"""
from dataclasses import dataclass, replace
from html import escape
from html.parser import HTMLParser
import unittest


class HeadCanonicals(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_head = False
        self.targets = []

    def handle_starttag(self, tag, attrs):
        if tag == "head":
            self.in_head = True
        if tag == "link" and self.in_head:
            a = dict(attrs)
            if "canonical" in a.get("rel", "").lower().split():
                self.targets.append(a.get("href", ""))

    def handle_endtag(self, tag):
        if tag == "head":
            self.in_head = False


def canonicals(html):
    p = HeadCanonicals()
    p.feed(html)
    p.close()
    return tuple(p.targets)


def page(*targets):
    # Fixture template output, not browser-rendered content.
    links = ''.join('<link rel="canonical" href="' + escape(t, quote=True) + '">' for t in targets)
    return '<html><head>' + links + '</head><body>fixture</body></html>'


@dataclass(frozen=True)
class Snapshot:
    intended: str | None  # supplied after manual duplicate/content review
    original: str | None
    rendered: str | None  # synthetic post-render capture, not executed JS
    header_targets: tuple[str, ...] | None = ()  # None means not captured
    target_status: int | None = 200
    target_compatible: bool | None = True  # manual duplicate/superset review
    noindex: bool | None = False
    crawl_allowed: bool | None = True
    # Optional authorized indexed-report observation; seconds on same clock.
    indexed_selected: str | None = None
    indexed_crawl_time: int | None = None
    fix_time: int = 100


def assess(s):
    """Return independent flags, never an inferred search-engine verdict."""
    flags = set()
    if not s.intended:
        flags.add('intent_unknown')
    captures = (s.original, s.rendered, s.header_targets)
    if any(v is None for v in captures):
        flags.add('capture_incomplete')
    raw = canonicals(s.original) if s.original is not None else ()
    rendered = canonicals(s.rendered) if s.rendered is not None else ()
    header = s.header_targets or ()
    for values in (raw, rendered, header):
        if len(values) > 1:
            flags.add('multiple_declarations')
    if raw and s.rendered is not None and not rendered:
        flags.add('render_removal_needs_review')
    if raw and rendered and set(raw) != set(rendered):
        flags.add('render_conflict')
    targets = set(raw + rendered + header)
    if not targets:
        # Absence alone is not an indexing defect: engines can select a URL.
        flags.add('no_declaration_observed')
    if len(targets) > 1:
        flags.add('conflicting_signals')
    if s.intended and targets and targets != {s.intended}:
        flags.add('intended_mapping_mismatch')
    if s.target_status is None or s.target_compatible is None:
        flags.add('target_unknown')
    elif s.target_status != 200 or not s.target_compatible:
        flags.add('target_review_needed')
    if s.noindex is None or s.crawl_allowed is None:
        flags.add('directives_unknown')
    elif s.noindex or not s.crawl_allowed:
        flags.add('indexing_or_crawl_block')
    blockers = flags - {'no_declaration_observed'}
    if not blockers and targets:
        flags.add('declared_signals_match_intent')
    if s.indexed_selected is None or s.indexed_crawl_time is None:
        flags.add('indexed_selection_unknown')
    elif s.indexed_crawl_time <= s.fix_time:
        flags.add('indexed_evidence_not_postfix')
    elif not s.intended:
        flags.add('indexed_selection_uninterpretable')
    elif s.indexed_selected != s.intended:
        flags.add('postfix_indexed_selection_differs')
    else:
        flags.add('postfix_indexed_selection_matches')
    # Even matching post-fix index data proves neither rank nor business impact.
    flags.add('acquisition_effect_unproven')
    return flags


A='https://example.test/products/a'
B='https://example.test/products/b'
HOME='https://example.test/'
GOOD=Snapshot(A,page(A),page(A))


class Scenarios(unittest.TestCase):
    def test_shared_template_baseline_and_remedy(self):
        for intended in (A,B):
            broken=Snapshot(intended,page(HOME),page(HOME),target_compatible=False)
            self.assertTrue(canonicals(broken.original))  # naive baseline passes
            self.assertIn('intended_mapping_mismatch',assess(broken))
            fixed=replace(broken,original=page(intended),rendered=page(intended),target_compatible=True)
            self.assertIn('declared_signals_match_intent',assess(fixed))
            self.assertIn('indexed_selection_unknown',assess(fixed))
    def test_legitimate_duplicate(self):
        # Parameter/print variants can intentionally point at A.
        self.assertIn('declared_signals_match_intent',assess(GOOD))
    def test_content_superset_allowed(self):
        viewall='https://example.test/article/all'
        self.assertIn('declared_signals_match_intent',assess(Snapshot(viewall,page(viewall),page(viewall))))
    def test_intent_is_not_inferred_from_url(self):
        self.assertIn('intent_unknown',assess(replace(GOOD,intended=None)))
        self.assertNotIn('declared_signals_match_intent',assess(replace(GOOD,intended=None)))
    def test_header_conflict(self):
        self.assertIn('conflicting_signals',assess(replace(GOOD,header_targets=(B,))))
    def test_js_changes_existing(self):
        self.assertIn('render_conflict',assess(replace(GOOD,rendered=page(B))))
    def test_js_only_not_automatically_conflict(self):
        self.assertIn('declared_signals_match_intent',assess(replace(GOOD,original=page())))
    def test_rendered_removal_not_clean(self):
        result=assess(replace(GOOD,rendered=page()))
        self.assertIn('render_removal_needs_review',result)
        self.assertNotIn('declared_signals_match_intent',result)
    def test_missing_capture_not_clean(self):
        for field in ('original','rendered','header_targets'):
            result=assess(replace(GOOD,**{field:None}))
            self.assertIn('capture_incomplete',result)
            self.assertNotIn('declared_signals_match_intent',result)
    def test_multiple_identical_tags_need_review(self):
        self.assertIn('multiple_declarations',assess(replace(GOOD,rendered=page(A,A))))
    def test_body_tag_ignored(self):
        html=page()+f'<link rel="canonical" href="{A}">'
        self.assertEqual((),canonicals(html))
    def test_absence_not_proof_of_deindexing(self):
        result=assess(replace(GOOD,original=page(),rendered=page()))
        self.assertIn('no_declaration_observed',result)
        self.assertIn('indexed_selection_unknown',result)
        self.assertNotIn('declared_signals_match_intent',result)
    def test_header_only_supported(self):
        self.assertIn('declared_signals_match_intent',assess(replace(GOOD,original=page(),rendered=page(),header_targets=(A,))))
    def test_bad_target(self):
        for status in (301,404,500):
            self.assertIn('target_review_needed',assess(replace(GOOD,target_status=status)))
        self.assertIn('target_review_needed',assess(replace(GOOD,target_compatible=False)))
    def test_unknown_target(self):
        self.assertIn('target_unknown',assess(replace(GOOD,target_status=None)))
    def test_blocked_not_fixed_by_canonical(self):
        for change in ({'noindex':True},{'crawl_allowed':False}):
            self.assertIn('indexing_or_crawl_block',assess(replace(GOOD,**change)))
    def test_old_index_does_not_disprove_current_fix(self):
        for t in (90,100):
            r=assess(replace(GOOD,indexed_selected=HOME,indexed_crawl_time=t))
            self.assertIn('indexed_evidence_not_postfix',r)
            self.assertNotIn('postfix_indexed_selection_differs',r)
    def test_live_good_cannot_predict_index(self):
        r=assess(GOOD)
        self.assertIn('declared_signals_match_intent',r)
        self.assertIn('indexed_selection_unknown',r)
    def test_postfix_selection_differs(self):
        self.assertIn('postfix_indexed_selection_differs',assess(replace(GOOD,indexed_selected=HOME,indexed_crawl_time=101)))
    def test_selection_is_not_recovery(self):
        r=assess(replace(GOOD,indexed_selected=A,indexed_crawl_time=101))
        self.assertIn('postfix_indexed_selection_matches',r)
        self.assertIn('acquisition_effect_unproven',r)


if __name__=='__main__':
    unittest.main(verbosity=2)
