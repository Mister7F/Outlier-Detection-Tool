import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor


class UnivariateOutlier():
    def __init__(self, method='stdev', trigger_sensitity=3, n_neighbors=20):
        self.method = method
        self.trigger_sensitity = trigger_sensitity
        self.n_neighbors = n_neighbors

    def detect_outliers(self, data):
        '''
        Params
        ======
        - data (np.array) : 1D vector which contains values of items

        Return
        ======
        Return an index list of detected outliers
        '''
        if self.method == 'mad':
            return self._mad(data)

        elif self.method == 'mad_low':
            return self._mad_low(data)

        elif self.method == 'mad_high':
            return self._mad_high(data)

        elif self.method == 'z_score':
            return self._z_score(data)

        elif self.method == 'stdev':
            return self._stdev(data)

        elif self.method == 'stdev_low':
            return self._stdev_low(data)

        elif self.method == 'stdev_high':
            return self._stdev_high(data)

        elif self.method == 'lof':
            return self._lof(data)

        elif self.method == 'lof_stdev':
            return self._lof_stdev(data)

        elif self.method == 'isolation_forest':
            return self._isolation_forest(data)

        elif self.method == 'less_than_sensitivity':
            return self._less_than_sensitivity(data)

        elif self.method == 'pct_of_avg_value_low':
            return self._pct_of_avg_value_low(data)

        elif self.method == 'pct_of_avg_value_high':
            return self._pct_of_avg_value_high(data)

        raise ValueError('Wrong method', 'mad', 'mad_low', 'mad_high',
                         'z_score', 'stdev',
                         'lof', 'lof_stdev', 'isolation_forest')# todo : add here

    def _z_score(self, data):
        mad = np.median(abs(data-np.median(data)))
        z_scores = abs(0.6745 * (data - np.median(data)) / mad)
        return np.where(z_scores > self.trigger_sensitity)[0]

    def _mad(self, data):
        mad = np.median(abs(data-np.median(data)))
        if not mad:
            return []
        dec = abs((data - np.median(data)) / mad)
        return np.where(dec > self.trigger_sensitity)[0]

    def _mad_low(self, data):
        mad = np.median(abs(data-np.median(data)))
        if not mad:
            return []
        dec = (data - np.median(data)) / mad
        return np.where(dec < self.trigger_sensitity)[0]

    def _mad_high(self, data):
        mad = np.median(abs(data-np.median(data)))
        if not mad:
            return []
        dec = (data - np.median(data)) / mad
        return np.where(dec > self.trigger_sensitity)[0]

    def _stdev(self, data):
        if not data.std():
            return np.array([])
        scores = abs(data-np.median(data)) / data.std()
        return np.where(scores > self.trigger_sensitity)[0]

    def _stdev_low(self, data):
        if not data.std():
            return np.array([])
        scores = (data-np.median(data)) / data.std()
        return np.where(scores < self.trigger_sensitity)[0]

    def _stdev_high(self, data):
        if not data.std():
            return np.array([])
        scores = (data-np.median(data)) / data.std()
        return np.where(scores > self.trigger_sensitity)[0]

    def _lof(self, data):

        if data.shape[0] <= self.n_neighbors:
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
        if data.shape[0] <= self.n_neighbors:
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

    def _less_than_sensitivity(self, data):
        return np.arange(data.shape[0])[data < self.trigger_sensitity]

    def _pct_of_avg_value_low(self, data):
        avg = data.mean()
        pct = self.trigger_sensitity / 100

        return np.arange(data.shape[0])[data < avg * pct]

    def _pct_of_avg_value_high(self, data):
        avg = data.mean()
        pct = self.trigger_sensitity / 100

        return np.arange(data.shape[0])[data > avg * pct]
