import unittest
import numpy as np
from helpers.text_processing import *


class TestTextProcessing(unittest.TestCase):
	def test_onthot_encode(self):
		self.assertEqual(
			onthot_encode(np.array(['a', 'hello', 'Mister7F', 'd', 'a'])).tolist(),
			[[0, 1, 0, 0], [0, 0, 0, 1], [1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0]]
		)

		self.assertEqual(
			onthot_encode(np.array(['a', 'hello', 'Mister7F', 'd', 'a']), return_dic=True)[1],
			{'hello': 3, 'a': 1, 'Mister7F': 0, 'd': 2}
		)

	def test_class_to_ide(self):

		self.assertEqual(
			class_to_id(np.array(['a', 'hello', 'Mister7F', 'd', 'a'])).tolist(),
			[1, 3, 0, 2, 1]
		)

		self.assertEqual(
			class_to_id(np.array(['a', 'hello', 'Mister7F', 'd', 'a']), return_dic=True)[1],
			{'hello': 3, 'a': 1, 'Mister7F': 0, 'd': 2}
		)

	def test_tokenizer(self):
		tokenizer = Tokenizer('-')

		tokenizer.train_on_data(['a-b-c-d-e-f', 'f-a-d-e-a-c-b-k-a'])

		self.assertEqual(
			[i.tolist() for i in tokenizer.tokenize(['a-b', 'e-k-e'])],
			[[1, 6], [3, 7, 3]]
		)

		self.assertEqual(
			[i.tolist() for i in tokenizer.tokenize(['a-b', 'e-k-e'], onehot=True)],
			[
				[
					[0, 1, 0, 0, 0, 0, 0, 0],
					[0, 0, 0, 0, 0, 0, 1, 0]
				],
				[
					[0, 0, 0, 1, 0, 0, 0, 0],
					[0, 0, 0, 0, 0, 0, 0, 1],
					[0, 0, 0, 1, 0, 0, 0, 0]
				]
			]
		)
		

		
