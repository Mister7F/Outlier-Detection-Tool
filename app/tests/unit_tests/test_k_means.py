import unittest
import numpy as np
from analyzers.algorithms.k_means import *


class TestKMeans(unittest.TestCase):
	def test_distance(self):
		self.assertEqual(
			distance(np.array([[0, 1], [4, 8]]), np.array([-4, 7])).tolist(), 
			[52, 65]
		)

	def test_centroid(self):
		self.assertAlmostEqual(
			centroid([[0, 1], [1, 0], [2, 3], [-4, 7]]).tolist(), 
			[-0.25, 2.75]
		)

	def test_k_means(self):
		np.random.seed(1337)

		self.assertEqual(
			k_means(np.array([[0, 0], [0, 1], [10, 20], [2, 2], [9, 23], [11, 21], [5, 5]]), n=2),
			[[0, 1, 3, 6], [2, 4, 5]]
		)
