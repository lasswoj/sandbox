import unittest
from calculator import Calculator, BranchValues

SYMBOL = "test"


class TestCalculator(unittest.TestCase):
    def setUp(self):
        self.calculator = Calculator()

    def test_push_data(self):
        data = [1, 2, 3, 4, 5]

        self.calculator.recalculate(data, SYMBOL)
        self.assertEqual(len(self.calculator.arrays[SYMBOL]), 5)
        self.assertEqual(self.calculator.arrays[SYMBOL], data)

    def test_recalculate(self):
        data = [1, 2, 3, 4, 5]
        self.calculator.recalculate(data, SYMBOL)
        self.assertEqual(len(self.calculator.calculations[SYMBOL]), 1)
        self.assertEqual(self.calculator.calculations[SYMBOL][0].amount, 5)


class TestBranchValues(unittest.TestCase):
    def test_from_chunk(self):
        data = [1, 2, 3, 4, 5]
        slice_iter = iter(data)
        branch = BranchValues.from_chunk(slice_iter, 0, 5)
        self.assertIsNotNone(branch)
        self.assertEqual(branch.amount, 5)
        self.assertAlmostEqual(branch.avg, 3.0)
        self.assertEqual(branch.min, 1)
        self.assertEqual(branch.max, 5)

    def test_merger(self):
        branch1 = BranchValues(2.0, 1, 0, 3, 2, 3, 1.0)
        branch2 = BranchValues(5.0, 4, 3, 6, 5, 3, 1.0)
        merged = BranchValues.merger([branch1, branch2], 0)
        self.assertIsNotNone(merged)
        self.assertEqual(merged.amount, 6)
        self.assertAlmostEqual(merged.avg, 3.5)
        self.assertEqual(merged.min, 1)
        self.assertEqual(merged.max, 6)


if __name__ == "__main__":
    unittest.main()
