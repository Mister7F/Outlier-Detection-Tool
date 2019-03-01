import numpy as np
from sklearn.neighbors import LocalOutlierFactor
from sklearn.ensemble import IsolationForest

class UnivariateOutlier():
	def __init__(self, method='stdev', trigger_sensitity=3, n_neighbors=20):
		self.method = method
		self.trigger_sensitity = trigger_sensitity
		self.n_neighbors = n_neighbors

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

		elif self.method == 'lof_stdev':
			return self._lof_stdev(data)

		elif self.method == 'isolation_forest':
			return self._isolation_forest(data)

		raise ValueError('Wrong method', 'mad', 'stdev', 'lof', 'lof_stdev')

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

		if data.shape[0] < 10:
			# Not enough data to find outliers...
			return []

		if data.ndim == 1:
			data = data.reshape(-1, 1)
		clf = LocalOutlierFactor(
			novelty=True, contamination=self.trigger_sensitity/100,
			n_neighbors=self.n_neighbors
		)
		clf.fit(data)

		predictions = clf.predict(data)

		return np.arange(data.shape[0])[predictions < 0]

	def _lof_stdev(self, data):
		if data.shape[0] < 10:
			# Not enough data to find outliers...
			return []

		if data.ndim == 1:
			data = data.reshape(-1, 1)

		clf = LocalOutlierFactor(
			novelty=True,
			contamination=0.1,
			n_neighbors=self.n_neighbors
		)
		clf.fit(data)
		lofs = clf.score_samples(data)
		
		return self._stdev(lofs)

	def _isolation_forest(self, data):
		clf = IsolationForest(
			behaviour='new',
			max_samples=data.size,
			contamination=self.trigger_sensitity/100
		)
		clf.fit(data.reshape(-1, 1))
		predictions = clf.predict(data.reshape(-1, 1))

		return np.arange(data.shape[0])[predictions < 0]