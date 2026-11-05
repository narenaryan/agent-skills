"""Original illustrative payoff checks, not a pricing or contract-approval engine.

Amounts are thousands of USD. Probabilities are assumptions, not estimates.
Both outcome states remain possible; fees, taxes, finance and legal terms omitted.
"""
from fractions import Fraction as F
import unittest


def payment(outcome):
    """An unresolved measurement is neither failure nor success."""
    if outcome == 'success':
        return F(40)
    if outcome == 'failure':
        return F(20)
    if outcome in ('missing', 'disputed'):
        return None
    raise ValueError('unknown outcome label')


def expected_payment(success_probability):
    p = F(success_probability)
    if not 0 <= p <= 1:
        raise ValueError('probability outside [0, 1]')
    return p * payment('success') + (1 - p) * payment('failure')


def seller_contribution(p, delivery_cost=F(24), administration=F(2)):
    return expected_payment(p) - delivery_cost - administration


def buyer_cost(p, administration=F(2)):
    return expected_payment(p) + administration


class Scenarios(unittest.TestCase):
    def test_differing_beliefs_make_proposal_apparently_attractive(self):
        self.assertEqual(seller_contribution(F(4, 5)), F(10))
        self.assertEqual(buyer_cost(F(1, 5)), F(26))
        self.assertGreater(seller_contribution(F(4, 5)), F(30 - 24))
        self.assertLess(buyer_cost(F(1, 5)), F(30))

    def test_common_belief_is_not_joint_value_creation(self):
        # Buyer savings + seller contribution improvement = -4 admin cost.
        for p in (F(0), F(1, 5), F(1, 2), F(4, 5), F(1)):
            seller_gain = seller_contribution(p) - F(6)
            buyer_gain = F(30) - buyer_cost(p)
            self.assertEqual(seller_gain + buyer_gain, F(-4))

    def test_neutral_beliefs_make_both_worse(self):
        self.assertEqual(seller_contribution(F(1, 2)), F(4))
        self.assertEqual(buyer_cost(F(1, 2)), F(32))

    def test_high_expected_margin_does_not_remove_downside(self):
        self.assertEqual(payment('failure') - 24 - 2, F(-6))
        self.assertLess(payment('failure') - 24 - 2, F(0))

    def test_low_expected_cost_does_not_satisfy_hard_budget(self):
        self.assertLess(buyer_cost(F(1, 5)), F(35))
        self.assertGreater(payment('success') + 2, F(35))

    def test_missing_evidence_is_not_low_payment(self):
        self.assertIsNone(payment('missing'))
        self.assertIsNone(payment('disputed'))
        self.assertEqual(payment('failure'), F(20))

    def test_seller_break_even_belief_with_admin(self):
        self.assertEqual(seller_contribution(F(3, 5)), F(6))
        self.assertLess(seller_contribution(F(59, 100)), F(6))

    def test_buyer_break_even_belief_with_admin(self):
        self.assertEqual(buyer_cost(F(2, 5)), F(30))
        self.assertGreater(buyer_cost(F(41, 100)), F(30))

    def test_asymmetric_information_changes_comparison(self):
        # A shared downside audit changes assumptions, not historical outcomes.
        self.assertLess(seller_contribution(F(3, 10)), F(6))
        self.assertEqual(seller_contribution(F(3, 10)), F(0))

    def test_quality_cut_can_make_timing_reward_misleading(self):
        # Original counterexample: same on-time label, different delivered value.
        rushed_value, careful_value = F(35), F(50)
        raw_reward = payment('success')
        self.assertLess(rushed_value - raw_reward, F(0))
        self.assertGreater(careful_value - raw_reward, F(0))

    def test_probability_endpoints_and_rejection(self):
        self.assertEqual(expected_payment(0), F(20))
        self.assertEqual(expected_payment(1), F(40))
        for p in (F(-1, 100), F(101, 100)):
            with self.assertRaises(ValueError):
                expected_payment(p)

    def test_unrecognized_measurement_does_not_settle(self):
        for state in ('pending', '', 'TRUE'):
            with self.assertRaises(ValueError):
                payment(state)


if __name__ == '__main__':
    unittest.main(verbosity=2)
