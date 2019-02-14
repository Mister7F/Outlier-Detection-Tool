import numpy as np
from functools import reduce

from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences

from helpers.singletons import logging

def onthot_encode(vector, return_dic=False):
	'''
	Take an list of string, and onehot encode each string

	Params
	======
	- vector     ([str]) : List of string
	- return_dic (bool)  : If true, return the dic used to one-hoot encode vector
	'''
	values, counts = np.unique(vector, return_counts=True)

	dic = {v: i for i, v in enumerate(values)}

	oh_vector = np.zeros((vector.size, values.size))

	for i, v in enumerate(vector):
		oh_vector[i][dic[v]] = 1

	if return_dic:
		return oh_vector, dic

	return oh_vector

def class_to_id(vector, return_dic=False):
	'''
	Replace each element by an id
	'''
	values, counts = np.unique(vector, return_counts=True)

	dic = {v: i for i, v in enumerate(values)}

	ret = np.array([dic[v] for v in vector])

	if return_dic:
		return ret, dic

	return ret


class Tokenizer:
	def __init__(self, split, vocab_size=4000, tolower=True):
		'''
		Params
		======
		- split_characters ([str]) : Delimit words
		- vocab_size       (int)   : Keep only most frequent words, avoid to waste memory
		'''
		self.split = split
		self.vocab_size = vocab_size

		self.dic = None
		self.tolower = tolower

	def train_on_data(self, sentences):
		'''
		Create the dictionnary using sentences

		Params
		======
		- sentences (list) : List of strings (sentence)
		'''

		dic = []
		for sentence in sentences:
			if self.tolower:
				sentence = sentence.lower()
			sentence = reduce(lambda x, y: x.replace(y, self.split[0]), [sentence, *self.split])

			for s in sentence.split(self.split[0]):
				if s:
					dic.append(s)
		
		dic = np.array(dic)

		dic, count = np.unique(dic, return_counts=True)

		dic = dic[np.argsort(count)[::-1]]

		if self.vocab_size < dic.size:
			dic = dic[:self.vocab_size]

		self.dic = {v:i+1 for i, v in enumerate(dic)}

	def tokenize(self, sentences, onehot=False):
		'''
		Return a list of word id
		Params
		======
		- sentences (list): List of strings (sentences)
		- onehot    (bool): If False, return a list of word id
							'This is a tokenizer' -> [2, 3, 1, 0]
							If True, return a list of word vector (onehot)
							'This is a tokenizer' -> [[0, 0, 1, 0], [0, 0, 0, 1], [0, 1, 0, 0], [1, 0, 0, 0]]
		'''
		data = []

		if onehot:
			matr = np.eye(len(self.dic)+1)

			for sentence in sentences:
				if self.tolower:
					sentence = sentence.lower()
				for s in self.split:
					sentence = sentence.replace(s, self.split[0])
				sentence = sentence.split(self.split[0])

				vect = np.array([matr[self.dic[s]] for s in sentence if s in self.dic])

				data.append(vect)
		else:
			for sentence in sentences:
				if self.tolower:
					sentence = sentence.lower()
				for s in self.split:
					sentence = sentence.replace(s, self.split[0])
				sentence = sentence.split(self.split[0])

				vect = np.array([self.dic[s] for s in sentence if s in self.dic])

				data.append(vect)

		return data