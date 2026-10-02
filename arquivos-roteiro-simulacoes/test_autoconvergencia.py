"""Testes sintéticos; não são resultados da Equação do Telegrafista."""
import math
import unittest

from autoconvergencia import (check_grid_pair, normalized_l2, observed_order,
                             parse_steps, restrict, synthetic_checks)


class SyntheticTests(unittest.TestCase):
    def test_unit_difference(self):
        self.assertEqual(normalized_l2([2.] * 8, [3.] * 8), 1.)

    def test_constant_restriction(self):
        self.assertEqual(restrict([7.] * 8), [7.] * 4)

    def test_average_not_subsampling(self):
        self.assertEqual(restrict([1., 3., 5., 7.]), [2., 6.])

    def test_second_order_example(self):
        order, reason = observed_order(.016, .004)
        self.assertAlmostEqual(order, 2.)
        self.assertEqual(reason, '')

    def test_unavailable_orders(self):
        for errors in ((0., 1.), (math.nan, 1.), (1e-18, 1e-19)):
            order, reason = observed_order(*errors)
            self.assertTrue(math.isnan(order))
            self.assertTrue(reason)

    def test_misaligned_domain_is_rejected(self):
        coarse = dict(n=2, lower=-2., upper=2., dx=2., time=.8)
        fine = dict(n=4, lower=-2., upper=2., dx=1., time=.8)
        check_grid_pair(coarse, fine)
        fine['lower'] += .1
        with self.assertRaises(ValueError):
            check_grid_pair(coarse, fine)

    def test_step_rejection_is_not_counted_as_accepted(self):
        text = ('CLAW1... Step   1   Courant number = 1.600  dt =  0.1250D-01  t =  0.1250D-01\n'
                'CLAW1 rejecting step... Courant number too large\n'
                'CLAW1... Step   1   Courant number = 0.900  dt =  0.7031D-02  t =  0.7031D-02\n')
        rows = parse_steps(text)
        self.assertEqual([r['aceito'] for r in rows], [False, True])
        self.assertAlmostEqual(rows[1]['dt_log'], .007031)

    def test_required_checks_are_separate(self):
        checks = synthetic_checks()
        self.assertEqual(len(checks), 3)
        self.assertTrue(all(r['status'] == 'passou' for r in checks))


if __name__ == '__main__':
    unittest.main()
