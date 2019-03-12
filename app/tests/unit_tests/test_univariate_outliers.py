import numpy as np
import unittest
from helpers.outliers_detection import outliers_detection


class TestUnivariateOutlier(unittest.TestCase):
    def setUp(self):
        pass

    def test_univariate_outlier(self):
        self.assertEqual(
            outliers_detection(
                np.array([1, 2, 3, 1, 2, 1, 9, -18]),
                'mad',
                trigger_sensitity=3
            ).tolist(),
            [6, 7]
        )

        self.assertEqual(
            outliers_detection(
                np.array([1, 2, 3, 1, 2, 1, 9, -18]),
                'mad',
                trigger_sensitity=3
            ).tolist(),
            [6, 7]
        )

        self.assertEqual(
            outliers_detection(
                np.array([1, 2, 3, 1, 2, 1, 9, -18]),
                'stdev',
                trigger_sensitity=3
            ).tolist(),
            []
        )

        self.assertEqual(
            outliers_detection(
                np.array([1, 2, 3, 1, 2, 1, 9, -18]),
                'stdev',
                trigger_sensitity=1
            ).tolist(),
            [6, 7]
        )

        self.assertEqual(
            outliers_detection(
                np.array([1, 2, 3, 1, 2, 1, 9, -18]),
                'stdev',
                trigger_sensitity=2
            ).tolist(),
            [7]
        )

        self.assertEqual(
            outliers_detection(
                np.array([1, 1, 1, 1]),
                'stdev',
                trigger_sensitity=0
            ).tolist(),
            []
        )

        self.assertEqual(
            outliers_detection(
                np.array([1, 1, 1, 1, 9, 9, 9, 9, 5, 15]),
                'lof',
                trigger_sensitity=20,
                n_neighbors=3
            ).tolist(),
            [8, 9]
        )

        self.assertEqual(
            outliers_detection(
                np.array([1, 1, 1, 1, 9, 9, 9, 9, 5, 15]),
                'lof',
                trigger_sensitity=12,
                n_neighbors=3
            ).tolist(),
            [9]
        )

        self.assertEqual(
            outliers_detection(
                np.array([1, 1, 1, 1, 9, 9, 9, 9, 5, 15]),
                'lof',
                trigger_sensitity=9,
                n_neighbors=3
            ).tolist(),
            []
        )

        self.assertEqual(
            outliers_detection(
                np.array([1, 1, 1, 1, 9, 9, 9, 9, 5, 15]),
                'lof_stdev',
                trigger_sensitity=1,
                n_neighbors=3
            ).tolist(),
            [8, 9]
        )
