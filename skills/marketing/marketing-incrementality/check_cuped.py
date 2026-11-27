"""Original finite-population teaching fixture; not a production estimator.

No packages, services, campaign data or coefficient fitting. All assignment sets
are enumerated; theta is fixed before assignment, not estimated from outcomes.
"""
from fractions import Fraction as F
from itertools import combinations
from statistics import mean, pvariance, variance
import json
import unittest


def estimate(y, x, treatment, theta=F(0)):
    """Complete randomization, one scalar per unit, fixed common coefficient."""
    if len(y) != len(x) or len(y) != len(treatment):
        raise ValueError('mismatched units')
    if any(v not in (0, 1) for v in treatment):
        raise ValueError('binary assignment required')
    if any(v is None for v in y + x):
        raise ValueError('missing values need an explicit analysis plan')
    z = [F(a) - theta * F(b) for a, b in zip(y, x)]
    arms = [[z[i] for i, t in enumerate(treatment) if t == g] for g in (0, 1)]
    if min(map(len, arms)) < 2:
        raise ValueError('at least two units per arm required for variance')
    c, t = arms
    return mean(t) - mean(c), variance(t) / len(t) + variance(c) / len(c)


def enumerate_design(x, y0, y1, n_t, theta=F(0), contamination=F(0)):
    estimates, estimated_variances = [], []
    for selected in combinations(range(len(x)), n_t):
        selected = set(selected)
        arm = [int(i in selected) for i in range(len(x))]
        y = [y1[i] if a else y0[i] for i, a in enumerate(arm)]
        # Deliberately invalid scenario: treatment changes a purported covariate.
        observed_x = [v + contamination * a for v, a in zip(x, arm)]
        delta, vhat = estimate(y, observed_x, arm, theta)
        estimates.append(delta)
        estimated_variances.append(vhat)
    return {
        'assignments': len(estimates),
        'mean_effect': mean(estimates),
        'variance': pvariance(estimates),
        'mean_estimated_variance': mean(estimated_variances),
    }


# Orthogonal centered components, repeated at two residual values per x.
X = [F(x) for x in (-5, -3, -1, 1, 3, 5) for _ in (0, 1)]
E = [F(e) for _ in range(6) for e in (-1, 1)]
Y0 = [20 + 2*x + e for x, e in zip(X, E)]
Y1 = [v + 3 for v in Y0]


class Contracts(unittest.TestCase):
    def test_all_balanced_assignments_and_variance(self):
        raw = enumerate_design(X, Y0, Y1, 6)
        adj = enumerate_design(X, Y0, Y1, 6, F(2))
        self.assertEqual(raw['assignments'], 924)
        self.assertEqual(raw['mean_effect'], 3)
        self.assertEqual(adj['mean_effect'], 3)
        self.assertLess(adj['variance'], raw['variance'])
        # Constant treatment effect: Neyman variance estimator is unbiased.
        self.assertEqual(adj['mean_estimated_variance'], adj['variance'])
        self.assertEqual(raw['mean_estimated_variance'], raw['variance'])

    def test_unequal_allocation_preserves_target(self):
        r = enumerate_design(X, Y0, Y1, 4, F(2))
        self.assertEqual(r['assignments'], 495)
        self.assertEqual(r['mean_effect'], 3)
        self.assertEqual(r['variance'], r['mean_estimated_variance'])

    def test_heterogeneous_effect_conservative_variance(self):
        y1 = [v + 3 + x/2 for v, x in zip(Y0, X)]
        r = enumerate_design(X, Y0, y1, 6, F(2))
        tau = [a-b for a,b in zip(y1,Y0)]
        self.assertEqual(r['mean_effect'], mean(tau))
        self.assertEqual(r['mean_estimated_variance'] - r['variance'], variance(tau)/len(tau))

    def test_post_treatment_covariate_removes_real_effect(self):
        r = enumerate_design(X, Y0, Y1, 6, F(2), F(1))
        self.assertEqual(r['mean_effect'], 1)  # truth 3 minus theta * 1
        self.assertEqual(r['variance'], enumerate_design(X,Y0,Y1,6,F(2))['variance'])

    def test_unhelpful_covariate_can_worsen_precision(self):
        y0 = [20+e for e in E]
        y1 = [v+3 for v in y0]
        raw = enumerate_design(X,y0,y1,6)
        bad = enumerate_design(X,y0,y1,6,F(2))
        self.assertEqual(bad['mean_effect'], 3)
        self.assertGreater(bad['variance'], raw['variance'])

    def test_wrong_sign_adjustment_is_detected(self):
        raw = enumerate_design(X,Y0,Y1,6)
        wrong = enumerate_design(X,Y0,Y1,6,F(-2))
        self.assertGreater(wrong['variance'],raw['variance'])

    def test_common_center_cancels(self):
        t = [0]*6+[1]*6
        y = [Y1[i] if a else Y0[i] for i,a in enumerate(t)]
        self.assertEqual(estimate(y,X,t,F(2)),estimate(y,[v+100 for v in X],t,F(2)))

    def test_arm_centering_erases_adjustment(self):
        t = [0]*6+[1]*6
        y = [Y1[i] if a else Y0[i] for i,a in enumerate(t)]
        centered = [x-mean([X[j] for j in range(12) if t[j]==t[i]]) for i,x in enumerate(X)]
        bad_delta, _ = estimate(y,centered,t,F(2))
        raw_delta, _ = estimate(y,X,t)
        good_delta, _ = estimate(y,X,t,F(2))
        self.assertEqual(bad_delta,raw_delta)
        self.assertNotEqual(bad_delta,good_delta)

    def test_null_effect_and_wrong_standard_error(self):
        raw = enumerate_design(X,Y0,Y0,6)
        adj = enumerate_design(X,Y0,Y0,6,F(2))
        self.assertEqual(adj['mean_effect'],0)
        self.assertNotEqual(raw['mean_estimated_variance'],adj['variance'])
        # Copying raw SE is not the SE of the adjusted estimator.
        self.assertGreater(raw['mean_estimated_variance'],adj['mean_estimated_variance'])

    def test_input_contract(self):
        for args in [([1,2],[1],[0,1]),([1,None,3,4],[1,2,3,4],[0,0,1,1]),([1,2,3,4],[1,2,3,4],[0,0,0,1]),([1,2,3,4],[1,2,3,4],[0,2,1,1])]:
            with self.assertRaises(ValueError):
                estimate(*args)


def report():
    rows = {
        'balanced_raw': enumerate_design(X,Y0,Y1,6),
        'balanced_adjusted': enumerate_design(X,Y0,Y1,6,F(2)),
        'treatment_contaminated': enumerate_design(X,Y0,Y1,6,F(2),F(1)),
        'unequal_adjusted': enumerate_design(X,Y0,Y1,4,F(2)),
    }
    return {name:{k:(float(v) if isinstance(v,F) else v) for k,v in row.items()} for name,row in rows.items()}


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Contracts)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print(json.dumps(report(),indent=2))
