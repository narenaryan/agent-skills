#!/usr/bin/env python3
"""Original offline evidence-contract scenarios, NOT a tracer or output parser.

Normalized synthetic records stand in for inspected trace evidence. No privileged
calls, I/O load, packages, real device reads, kernel attachments, or networking.
"""
from dataclasses import dataclass
from math import isfinite
import unittest


@dataclass(frozen=True)
class Request:
    queued_ms: float | None
    issued_ms: float
    completed_ms: float | None
    comm: str | None = None
    origin_verified: bool = False


def spans(request):
    """Return observed boundary durations; never invent a missing timestamp."""
    times = [t for t in (request.queued_ms, request.issued_ms,
                         request.completed_ms) if t is not None]
    if any(not isfinite(t) or t < 0 for t in times):
        raise ValueError('invalid timestamp')
    if request.queued_ms is not None and request.queued_ms > request.issued_ms:
        raise ValueError('queue timestamp follows issue')
    if request.completed_ms is None:
        return None
    if request.completed_ms < request.issued_ms:
        raise ValueError('completion precedes issue')
    queue = None if request.queued_ms is None else request.issued_ms - request.queued_ms
    return queue, request.completed_ms - request.issued_ms


@dataclass(frozen=True)
class Capture:
    attached: bool = True
    device_matches: bool = True
    window_matches: bool = True
    lost_events: int = 0
    outstanding_known: bool = True
    requests: tuple[Request, ...] = ()


def evidence(capture):
    """Description of this normalized sample, not causal or health diagnosis."""
    if capture.lost_events < 0:
        raise ValueError('invalid lost-event count')
    if not (capture.attached and capture.device_matches and capture.window_matches):
        return 'coverage-unknown'
    if capture.lost_events or not capture.outstanding_known:
        return 'coverage-incomplete'
    durations = [spans(r) for r in capture.requests]
    if any(s is None for s in durations):
        return 'outstanding-requests-excluded-from-completion-histogram'
    if not durations:
        return 'no-completed-requests-observed'
    if any(q is None for q, _ in durations):
        return 'issue-to-completion-only'
    # Aggregate boundary decomposition for the SAME synthetic completed cohort.
    # Not a percentile subtraction or a production bottleneck threshold.
    queue = sum(q for q, _ in durations)
    issued = sum(lat for _, lat in durations)
    if queue > issued:
        return 'observed-time-mostly-before-issue'
    if issued > queue:
        return 'observed-time-mostly-after-issue'
    return 'observed-boundaries-equal'


def queue_observation(reported_ms, metadata_present):
    """Model BCC biosnoop fallback: printed zero is not measured without metadata."""
    return reported_ms if metadata_present else None


def attribution(request):
    return request.comm if request.comm and request.origin_verified else 'origin-unverified'


def naive_verdict(requests):
    """Deliberately unsound baseline: no completions means healthy."""
    return 'healthy' if not [r for r in requests if r.completed_ms is not None] else 'disk-failure'


class Scenarios(unittest.TestCase):
    def test_01_queue_boundary(self):
        r = Request(0, 90, 100)
        self.assertEqual(spans(r), (90, 10))
        self.assertEqual(evidence(Capture(requests=(r,))), 'observed-time-mostly-before-issue')

    def test_02_issued_boundary(self):
        self.assertEqual(evidence(Capture(requests=(Request(0, 2, 100),))),
                         'observed-time-mostly-after-issue')

    def test_03_equal_boundaries(self):
        self.assertEqual(evidence(Capture(requests=(Request(0, 5, 10),))),
                         'observed-boundaries-equal')

    def test_04_missing_queue_not_zero(self):
        self.assertEqual(spans(Request(None, 2, 12)), (None, 10))
        self.assertEqual(evidence(Capture(requests=(Request(None, 2, 12),))),
                         'issue-to-completion-only')

    def test_05_inflight_not_healthy(self):
        c = Capture(requests=(Request(0, 2, None),))
        self.assertEqual(naive_verdict(c.requests), 'healthy')
        self.assertEqual(evidence(c), 'outstanding-requests-excluded-from-completion-histogram')

    def test_06_empty_is_observation_not_health(self):
        self.assertEqual(evidence(Capture()), 'no-completed-requests-observed')

    def test_07_attach_failure(self):
        self.assertEqual(evidence(Capture(attached=False)), 'coverage-unknown')

    def test_08_wrong_device(self):
        self.assertEqual(evidence(Capture(device_matches=False)), 'coverage-unknown')

    def test_09_wrong_window(self):
        self.assertEqual(evidence(Capture(window_matches=False)), 'coverage-unknown')

    def test_10_lost_events(self):
        self.assertEqual(evidence(Capture(lost_events=1)), 'coverage-incomplete')

    def test_11_unknown_inflight(self):
        self.assertEqual(evidence(Capture(outstanding_known=False)), 'coverage-incomplete')

    def test_12_writeback_attribution(self):
        self.assertEqual(attribution(Request(0, 1, 2, 'kworker/u8:1')), 'origin-unverified')

    def test_13_named_app_not_proof(self):
        self.assertEqual(attribution(Request(0, 1, 2, 'database')), 'origin-unverified')

    def test_14_verified_origin(self):
        self.assertEqual(attribution(Request(0, 1, 2, 'database', True)), 'database')

    def test_15_clock_order(self):
        for r in (Request(3, 2, 4), Request(0, 2, 1), Request(-1, 2, 3),
                  Request(0, float('nan'), 3), Request(0, 2, float('inf'))):
            with self.subTest(r=r), self.assertRaises(ValueError):
                spans(r)

    def test_16_tail_hidden_by_mean(self):
        # Same mean, different tail: not a throughput or hardware experiment.
        uniform = [10] * 100
        bursty = [1] * 99 + [901]
        self.assertEqual(sum(uniform) / len(uniform), sum(bursty) / len(bursty))
        self.assertNotEqual(max(uniform), max(bursty))

    def test_17_inflight_with_fast_completions(self):
        c = Capture(requests=(Request(0, 1, 2), Request(0, 1, None)))
        self.assertEqual(evidence(c), 'outstanding-requests-excluded-from-completion-histogram')

    def test_19_missing_metadata_zero(self):
        self.assertIsNone(queue_observation(0, False))
        self.assertEqual(queue_observation(0, True), 0)
        r = Request(None, 1, 2)
        self.assertEqual(evidence(Capture(requests=(r,))), "issue-to-completion-only")

    def test_18_never_media_failure(self):
        c = Capture(requests=(Request(0, 1, 10000),))
        self.assertEqual(naive_verdict(c.requests), 'disk-failure')
        self.assertEqual(evidence(c), 'observed-time-mostly-after-issue')


if __name__ == '__main__':
    unittest.main()
