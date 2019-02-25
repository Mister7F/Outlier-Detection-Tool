import numpy as np
from sklearn.neighbors import LocalOutlierFactor

class UnivariateOutlier():
	def __init__(self, method='stdev', trigger_sensitity=3):
		self.method = method
		self.trigger_sensitity = trigger_sensitity

	def detect_outliers(self, data):
		'''
		Params
		======
		- data (np.array) : 1 Dimensionnal vector which contains values of items

		Return
		======
		Return an index list of detected outliers
		'''
		if self.method == 'mad':
			return self._mad(data)
		
		elif self.method == 'stdev':
			return self._stdev(data)

		elif self.method == 'lof':
			return self._lof(data)

		raise 'Wrong method'

	def _mad(self, data):
		mad = np.median(abs(data-np.median(data)))
		z_scores = abs(0.6745 * (data - np.median(data)) / mad)
		return np.where(z_scores > self.trigger_sensitity)[0]

	def _stdev(self, data):
		if not data.std():
			return np.array([])
		scores = abs(data-np.median(data)) / data.std()
		return np.where(scores > self.trigger_sensitity)[0]

	def _lof(self, data):
		if data.ndim == 1:
			data = data.reshape(-1, 1)
		clf = LocalOutlierFactor(novelty=True, contamination=self.trigger_sensitity/100, n_neighbors=max(data.shape[0]//100, 5))
		clf.fit(data)
		predictions = clf.predict(data)

		return np.arange(data.shape[0])[predictions < 0]