import numpy as np
import unittest
from analyzers.algorithms.univariate_outliers import UnivariateOutlier


class TestUnivariateOutlier(unittest.TestCase):
	def setUp(self):
		pass

	def test_univariate_outlier(self):
		self.assertEqual(
			UnivariateOutlier(trigger_sensitity=3)
			._mad(np.array([1, 2, 3, 1, 2, 1, 9, -18])).tolist(),
			[6, 7]
		)

		self.assertEqual(
			UnivariateOutlier(trigger_sensitity=15)
			._mad(np.array([1, 2, 3, 1, 2, 1, 9, -18])).tolist(),
			[7]
		)

		self.assertEqual(
			UnivariateOutlier(trigger_sensitity=3)
			._stdev(np.array([1, 2, 3, 1, 2, 1, 9, -18])).tolist(),
			[]
		)

		self.assertEqual(
			UnivariateOutlier(trigger_sensitity=1)
			._stdev(np.array([1, 2, 3, 1, 2, 1, 9, -18])).tolist(),
			[6, 7]
		)

		self.assertEqual(
			UnivariateOutlier(trigger_sensitity=2)
			._stdev(np.array([1, 2, 3, 1, 2, 1, 9, -18])).tolist(),
			[7]
		)

		self.assertEqual(
			UnivariateOutlier(trigger_sensitity=0)
			._stdev(np.array([1, 1, 1, 1])).tolist(),
			[]
		)

		self.assertEqual(
			UnivariateOutlier(trigger_sensitity=20, n_neighbors=3)
			._lof(np.array([1, 1, 1, 1, 9, 9, 9, 9, 5, 15])).tolist(),
			[8, 9]
		)

		self.assertEqual(
			UnivariateOutlier(trigger_sensitity=12, n_neighbors=3)
			._lof(np.array([1, 1, 1, 1, 9, 9, 9, 9, 5, 15])).tolist(),
			[9]
		)

		self.assertEqual(
			UnivariateOutlier(trigger_sensitity=9, n_neighbors=3)
			._lof(np.array([1, 1, 1, 1, 9, 9, 9, 9, 5, 15])).tolist(),
			[]
		)

		self.assertEqual(
			UnivariateOutlier(trigger_sensitity=1, n_neighbors=3)
			._lof_stdev(np.array([1, 1, 1, 1, 9, 9, 9, 9, 5, 15])).tolist(),
			[8, 9]
		)

		


	