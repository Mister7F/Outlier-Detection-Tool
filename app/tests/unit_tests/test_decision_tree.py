import unittest
import numpy as np
import pandas as pd
from analyzers.algorithms.decision_tree import Tree


class TestDecisionTree(unittest.TestCase):
	def test_decision_tree(self):
		# Load test data
		data = pd.read_csv('/app/tests/unit_tests/files/titanic_for_decision_tree.csv')
		data = data[['Pclass', 'Name', 'Sex', 'Age', 'SibSp', 'Survived']]
		data['Age'] = data['Age'].fillna(0)
		data = data.values

		# Run tests
		tree = Tree(
			data,
			feature_type=['enum', 'enum', 'enum', 'float', 'enum', 'enum'],
			max_depth=3
		)

		self.assertAlmostEqual(tree.impurity(), 0.3333650003885904)		
		self.assertEqual(tree.rule_val, 'female')
		self.assertEqual(tree.rule_col, 2)
		self.assertEqual(len(tree.childs), 2)
		self.assertEqual(tree.predict([3, 22, 'male', 1]), 0)
		self.assertEqual(tree.predict([1, 22, 'male', 1]), 0)
		self.assertEqual(tree.predict([3, 22, 'female', 1]), 1)
