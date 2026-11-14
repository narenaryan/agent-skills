"""Original synthetic evidence checks, not a Cloudflare client or schema validator."""
from copy import deepcopy
import unittest


def describe(snapshot):
    """Trusted, normalized fixtures only. Never returns permission or runtime proof."""
    state = snapshot.get('current_state')
    result = {'configuration': snapshot['version'], 'action': snapshot['action'],
              'runtime': 'unverified', 'usage_freshness': 'unknown',
              'period': None, 'evaluation': 'unavailable', 'delivery': 'unavailable',
              'desired_state': None, 'expires_at': None}
    if state is None:
        return result
    result['period'] = (state['billing_period_start'], state['billing_period_end'])
    result['evaluation'] = state['status']
    enforcement = state.get('enforcement')
    if enforcement:
        result['desired_state'] = enforcement['desired_state']
        result['expires_at'] = enforcement['expires_at']
        equal = enforcement['desired_generation'] == enforcement['applied_generation']
        result['delivery'] = ('completed' if enforcement['delivery_status'] == 'succeeded'
                              and equal else 'not_confirmed')
    return result


def snapshot():
    return {'version': 4, 'action': 'usage_block', 'current_state': {
        'billing_period_start': '2026-10-10T00:00:00Z',
        'billing_period_end': '2026-11-10T00:00:00Z',
        'status': 'limit_reached', 'balance_cents': 11000,
        'evaluated_at': '2026-11-09T23:00:00Z', 'enforcement': {
            'desired_state': 'active', 'desired_generation': 7, 'applied_generation': 7,
            'delivery_status': 'succeeded', 'expires_at': '2026-11-10T00:00:00Z'}}}


class EvidenceTests(unittest.TestCase):
    def test_rollover_is_not_a_configuration_change(self):
        before = snapshot(); after = deepcopy(before)
        after['current_state'].update(billing_period_start='2026-11-10T00:00:00Z',
            billing_period_end='2026-12-10T00:00:00Z', status='below_limit', balance_cents=0)
        self.assertEqual(before['version'], after['version'])
        self.assertNotEqual(describe(before), describe(after))
        faulty_cached = describe(before) if before['version'] == after['version'] else describe(after)
        self.assertNotEqual(faulty_cached, describe(after))

    def test_missing_is_not_zero_or_below_limit(self):
        p = snapshot(); del p['current_state']
        self.assertEqual(describe(p)['evaluation'], 'unavailable')
        self.assertNotEqual(describe(p)['evaluation'], 'below_limit')

    def test_unknown_statuses_are_retained(self):
        for status in ['unavailable', 'no_current_period', 'disabled', 'below_limit', 'limit_reached']:
            p = snapshot(); p['current_state']['status'] = status
            self.assertEqual(describe(p)['evaluation'], status)

    def test_delivery_does_not_prove_runtime(self):
        self.assertEqual(describe(snapshot())['delivery'], 'completed')
        self.assertEqual(describe(snapshot())['runtime'], 'unverified')

    def test_generation_and_status_both_needed(self):
        for status in ['pending', 'leased', 'retry', 'succeeded']:
            for applied in [6, 7]:
                p = snapshot(); e = p['current_state']['enforcement']
                e.update(delivery_status=status, applied_generation=applied)
                expected = 'completed' if status == 'succeeded' and applied == 7 else 'not_confirmed'
                self.assertEqual(describe(p)['delivery'], expected)

    def test_evaluation_clock_is_not_event_clock(self):
        p = snapshot(); p['current_state']['evaluated_at'] = '2026-11-10T00:00:00Z'
        self.assertEqual(describe(p)['usage_freshness'], 'unknown')

    def test_notification_is_not_block(self):
        p = snapshot(); p['action'] = 'notification'; p['current_state']['enforcement'] = None
        self.assertEqual(describe(p)['action'], 'notification')
        self.assertEqual(describe(p)['runtime'], 'unverified')

    def test_independent_completed_inactive_is_not_active_cap(self):
        p = snapshot()
        p['current_state']['enforcement']['desired_state'] = 'inactive'
        r = describe(p)
        self.assertEqual(r['delivery'], 'completed')
        self.assertEqual(r['desired_state'], 'inactive')
        self.assertEqual(r['runtime'], 'unverified')

    def test_independent_expiry_retained_not_runtime_proof(self):
        p = snapshot()
        p['current_state']['enforcement']['expires_at'] = '2026-11-01T00:00:00Z'
        r = describe(p)
        self.assertEqual(r['delivery'], 'completed')
        self.assertEqual(r['expires_at'], '2026-11-01T00:00:00Z')
        self.assertEqual(r['runtime'], 'unverified')

    def test_independent_null_state_and_no_owned_effect(self):
        p = snapshot(); p['current_state'] = None
        self.assertEqual(describe(p)['evaluation'], 'unavailable')
        p = snapshot(); p['current_state']['enforcement'] = None
        r = describe(p)
        self.assertEqual(r['evaluation'], 'limit_reached')
        self.assertEqual(r['delivery'], 'unavailable')
        self.assertIsNone(r['desired_state'])
        self.assertIsNone(r['expires_at'])

    def test_concurrency_one_is_not_total_spend_cap(self):
        # Original hypothetical: serial jobs settle after a stale observation.
        # Not actual Cloudflare timing, prices, or an overspend forecast.
        costs = [2] * 10
        self.assertGreater(sum(costs), 10)
        self.assertEqual(max([1 for _ in costs]), 1)


if __name__ == '__main__':
    unittest.main()
