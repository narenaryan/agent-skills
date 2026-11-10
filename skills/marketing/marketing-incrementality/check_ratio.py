"""Original arithmetic checks; not confidence-interval coverage validation."""
from fractions import Fraction as F
import unittest

def stats(rows):
    rows=[(F(s),F(n)) for s,n in rows]
    k=len(rows)
    if k<2 or any(n<0 for _,n in rows) or sum(n for _,n in rows)<=0:
        raise ValueError('At least two units and a positive total denominator required')
    sm=sum(s for s,_ in rows)/k
    nm=sum(n for _,n in rows)/k
    r=sm/nm
    residual=[s-r*n for s,n in rows]
    # Mean residual is exactly zero by construction; sample divisor is k-1.
    v=sum(x*x for x in residual)/(k-1)/k/nm**2
    vs=sum((s-sm)**2 for s,_ in rows)/(k-1)
    vn=sum((n-nm)**2 for _,n in rows)/(k-1)
    cov=sum((s-sm)*(n-nm) for s,n in rows)/(k-1)
    return r,v,(vs+r*r*vn-2*r*cov)/k/nm**2

class RatioTests(unittest.TestCase):
    def test_estimand_counterexample(self):
        rows=[(1,1),(0,1),(0,9),(0,9)]
        self.assertEqual(stats(rows)[0],F(1,20))
        self.assertEqual(sum(F(s,n) for s,n in rows)/4,F(1,4))
    def test_covariance_identity(self):
        for rows in [[(1,1),(0,1),(0,9),(0,9)],[(3,2),(7,3),(1,4)],[(0,0),(2,3),(4,7)]]:
            self.assertEqual(stats(rows)[1],stats(rows)[2])
    def test_covariance_cancellation(self):
        rows=[(2,1),(4,2),(8,4)]
        self.assertEqual(stats(rows)[1],0)
        # Omitting covariance yields positive variance despite identical unit ratios.
        k=len(rows)
        sm=sum(F(s) for s,_ in rows)/k
        nm=sum(F(n) for _,n in rows)/k
        r=sm/nm
        vs=sum((s-sm)**2 for s,_ in rows)/(k-1)
        vn=sum((n-nm)**2 for _,n in rows)/(k-1)
        faulty=(vs+r*r*vn)/k/nm**2
        self.assertGreater(faulty,stats(rows)[1])
    def test_equal_denominators(self):
        rows=[(1,2),(2,2),(0,2)]
        self.assertEqual(stats(rows)[0],sum(F(s,n) for s,n in rows)/3)
    def test_duplicate_units_are_not_more_independent_units(self):
        rows=[(1,1),(0,1),(0,9),(0,9)]
        self.assertEqual(stats(rows)[0],stats(rows*2)[0])
        self.assertLess(stats(rows*2)[1],stats(rows)[1])
    def test_common_scale_and_order(self):
        rows=[(3,2),(7,3),(1,4)]
        self.assertEqual(stats(rows),stats(list(reversed(rows))))
        self.assertEqual(stats(rows),stats([(s*100,n*100) for s,n in rows]))
    def test_zero_activity_retained(self):
        rows=[(0,0),(1,2),(4,8)]
        self.assertEqual(stats(rows)[0],F(1,2))
        self.assertEqual(stats(rows)[1],0)
    def test_independent_known_nonzero_variance(self):
        # Hand-expanded residual squares: (19/20)^2 + (1/20)^2
        # + 2*(9/20)^2 = 131/100; divide by 3*4*5^2.
        rows=[(1,1),(0,1),(0,9),(0,9)]
        self.assertEqual(stats(rows), (F(1,20),F(131,30000),F(131,30000)))

    def test_independent_zero_activity_changes_uncertainty(self):
        # Genuine zero activity does not change the ratio, but excluding it
        # changes the independent-unit sample and finite-sample estimate.
        with_zero=stats([(0,0),(1,1),(0,3)])
        without_zero=stats([(1,1),(0,3)])
        self.assertEqual(with_zero[0],without_zero[0])
        self.assertEqual(with_zero[1],F(27,256))
        self.assertEqual(without_zero[1],F(9,64))

    def test_independent_pairwise_variance_identity(self):
        from itertools import product
        options=[(s,n) for n in range(4) for s in range(n+1)]
        for rows in product(options,repeat=3):
            if not sum(n for _,n in rows):
                continue
            k=len(rows)
            r=F(sum(s for s,_ in rows),sum(n for _,n in rows))
            nm=F(sum(n for _,n in rows),k)
            u=[s-r*n for s,n in rows]
            pairwise=sum((u[i]-u[j])**2 for i in range(k) for j in range(i))
            expected=pairwise/(k*k*(k-1)*nm*nm)
            self.assertEqual(stats(rows)[1],expected)

    def test_invalid_arithmetic(self):
        for rows in [[],[(1,2)],[(0,0),(0,0)],[(1,-1),(2,3)]]:
            with self.assertRaises(ValueError): stats(rows)

if __name__=='__main__':
    unittest.main()
