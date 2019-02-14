import numpy as np

import matplotlib
import matplotlib.pyplot as plt
from helpers.singletons import logging

class OutliersErrorBased:
	'''
	Used to detect outliers
	If we make a bad prediction, it might be an anomaly.
	'''
	def __init__(self, errors, labels_title=[], labels=[], is_anormal=None):
		'''
		Params
		======
		- errors (ndarray)     : List of errors at the end of the neural network, sorted by id
		- labels_title (list)  : Title describing the label
		- labels (ndarray)     : Labels to describe items, sorted by id
		- is_anormal (ndarray) : Used to measure the performance of our algorithm, sorted by id
		'''
		self.errors = errors
		self.labels_title = labels_title
		self.labels = labels
		self.is_anormal = is_anormal

	def _check_debugging(self):
		if self.is_anormal is None:
			raise 'I need to know which item is anormal to measure performance... :/'

	def measure_performance(self, threshold):
		self._check_debugging()

		precision = self.is_anormal[self.errors>threshold].mean()
		recall = (self.errors[self.is_anormal != 0] > threshold).astype(int).mean()

		f1_score = (2 * precision * recall) / (precision + recall) if (precision + recall) else 0

		return f1_score, precision, recall

	def plot_graph(self, n_points=1000):
		self._check_debugging()

		f1_score = []
		precision = []
		recall = []
		thresholds = []

		max_error = self.errors.max()
		min_error = self.errors.min()

		logging.logger.info('Error range [%f - %f]' % (min_error, max_error))

		for p in range(n_points):		    
		    threshold = (max_error - min_error) * (p/n_points) + min_error
		    
		    f1, pr, re = self.measure_performance(threshold)
		    
		    f1_score.append(f1)
		    precision.append(pr)
		    recall.append(re)
		    thresholds.append(threshold)

		# Plot gaph
		fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 6), dpi=80)

		ax1.plot(thresholds, f1_score)
		ax1.set(xlabel='Threshold [MSE]', ylabel='F1 Score', title='F1 Score')

		ax2.plot(thresholds, precision)
		ax2.set(xlabel='Threshold [MSE]', ylabel='Precision', title='Precision\nReal anomalies inside "considered as anomaly"')

		ax3.plot(thresholds, recall)
		ax3.set(xlabel='Threshold [MSE]', ylabel='Recall', title='Recall\nAnomaly which are detected as anomaly')

		plt.show()

	def show_most_anormal(self, count=10):
		# Index sorted by anomaly
		anomalies = np.argsort(self.errors)[::-1]

		logging.logger.info('=======================')
		logging.logger.info('== Show most anormal ==')
		logging.logger.info('=======================')
		logging.logger.info('Elements are sorted in order of abnormality')
		logging.logger.info('Error\t' + '\t'.join(self.labels_title))
		
		logging.logger.info('=====\t' + '\t'.join('=' * len(k) for k in self.labels_title))
		
		for e, label in zip(self.errors[anomalies[:count]], self.labels[anomalies[:count]]):
			logging.logger.info(str(e)[:5] + '\t' + '\t'.join([str(l) for l in label]))
		
		logging.logger.info('\n')