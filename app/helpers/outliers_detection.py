import numpy as np
from inspect import signature
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor


def outliers_detection(data, method='stdev', trigger_sensitity=3,
                       n_neighbors=None, trigger_on=None):
    '''
    n_neighbors and trigger_on depends on the methods
    '''
    methods = {
        'z_score': _z_score,
        'mad': _mad,
        'stdev': _stdev,
        'lof': _lof,
        'lof_stdev': _lof_stdev,
        'isolation_forest': _isolation_forest,
        'less_than_sensitivity': _less_than_sensitivity,
        'pct_of_avg_value': _pct_of_avg_value
    }

    if method not in methods:
        raise Exception('Wrong method')

    method = methods[method]

    all_options = {
        'data': data,
        'trigger_sensitity': trigger_sensitity,
        'trigger_on': trigger_on,
        'n_neighbors': n_neighbors
    }

    options = {
        k: all_options[k]
        for k in all_options
        if k in signature(method).parameters
    }

    return method(**options)


def _z_score(data, trigger_sensitity):
    mad = np.median(abs(data-np.median(data)))
    z_scores = abs(0.6745 * (data - np.median(data)) / mad)
    return np.where(z_scores > trigger_sensitity)[0]


def _mad(data, trigger_sensitity, trigger_on=None):
    mad = np.median(abs(data-np.median(data)))
    if not mad:
        return []

    dec = (data - np.median(data)) / mad

    if trigger_on == 'low':
        return np.where(dec < trigger_sensitity)[0]

    elif trigger_on == 'high':
        return np.where(dec > trigger_sensitity)[0]

    return np.where(abs(dec) > trigger_sensitity)[0]


def _stdev(data, trigger_sensitity, trigger_on=None):
    if not data.std():
        return np.array([])
    scores = abs(data-np.median(data)) / data.std()

    if trigger_on == 'low':
        return np.where(scores < trigger_sensitity)[0]

    elif trigger_on == 'high':
        return np.where(scores > trigger_sensitity)[0]

    return np.where(abs(scores) > trigger_sensitity)[0]


def _lof(data, trigger_sensitity, n_neighbors):

    if data.shape[0] <= n_neighbors:
        # Not enough data to find outliers...
        return []

    if data.ndim == 1:
        data = data.reshape(-1, 1)
    clf = LocalOutlierFactor(
        novelty=True, contamination=trigger_sensitity/100,
        n_neighbors=n_neighbors
    )
    clf.fit(data)

    predictions = clf.predict(data)

    return np.arange(data.shape[0])[predictions < 0]


def _lof_stdev(data, trigger_sensitity, n_neighbors):
    if data.shape[0] <= n_neighbors:
        # Not enough data to find outliers...
        return []

    if data.ndim == 1:
        data = data.reshape(-1, 1)

    clf = LocalOutlierFactor(
        novelty=True,
        contamination=0.1,
        n_neighbors=n_neighbors
    )
    clf.fit(data)
    lofs = clf.score_samples(data)

    return _stdev(lofs, trigger_sensitity)


def _isolation_forest(data, trigger_sensitity):
    clf = IsolationForest(
        behaviour='new',
        max_samples=data.size,
        contamination=trigger_sensitity/100
    )
    clf.fit(data.reshape(-1, 1))
    predictions = clf.predict(data.reshape(-1, 1))

    return np.arange(data.shape[0])[predictions < 0]


def _less_than_sensitivity(data, trigger_sensitity):
    return np.arange(data.shape[0])[data < trigger_sensitity]


def _pct_of_avg_value(data, trigger_sensitity, trigger_on=None):
    avg = data.mean()
    pct = trigger_sensitity / 100

    if trigger_on == 'low':
        return np.arange(data.shape[0])[data < avg * pct]

    elif trigger_on == 'high':
        return np.arange(data.shape[0])[data > avg * pct]

    raise Exception('pct_of_avg_value needs trigger_on=[low/high]')
