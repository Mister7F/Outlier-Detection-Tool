import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor

from helpers.utils import check_params
from functools import wraps


def is_univariate(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        data = args[0]

        if data.ndim > 2 or (data.ndim == 2 and data.shape[1] > 1):
            raise Exception('This method accept only 1D vector')

        if data.ndim == 2:
            data = data.reshape(-1)

        return f(*args, **kwargs)

    return decorated


#####################
# OUTLIER DETECTION #
#####################
def outlier_detection(data, options):
    if '_' + options['method'] not in globals():
        raise Exception('Wrong method')
    method = globals()['_' + options['method']]

    options = dict(options)
    del options['method']

    return method(data, **options)


@is_univariate
@check_params(trigger_on=['all', 'low', 'high'])
def _stdev(data, sensitivity, trigger_on='all'):
    if not data.std():
        return np.array([])

    scores = (data - np.median(data)) / data.std()

    if trigger_on == 'low':
        return np.where(- scores > sensitivity)[0]

    elif trigger_on == 'high':
        return np.where(scores > sensitivity)[0]

    return np.where(abs(scores) > sensitivity)[0]


@is_univariate
@check_params(trigger_on=['all', 'low', 'high'])
def _z_score(data, sensitivity, trigger_on='all'):
    mad = np.median(abs(data - np.median(data)))
    z_scores = (0.6745 * (data - np.median(data)) / mad)

    if trigger_on == 'low':
        return np.where(z_scores < sensitivity)[0]

    elif trigger_on == 'high':
        return np.where(z_scores > sensitivity)[0]

    return np.where(abs(z_scores) > sensitivity)[0]


@is_univariate
@check_params(trigger_on=['all', 'low', 'high'])
def _mad(data, sensitivity, trigger_on='all'):
    mad = np.median(abs(data - np.median(data)))
    if not mad:
        return []
    score = (data - np.median(data) / mad)

    if trigger_on == 'low':
        return np.where(- score > sensitivity)[0]

    elif trigger_on == 'high':
        return np.where(score > sensitivity)[0]

    return np.where(abs(score) > sensitivity)[0]


@check_params(trigger_on=['low', 'high'])
def _lof(data, sensitivity, n_neighbors, trigger_on='low'):

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

    sensitivity /= 100

    index = np.argsort(lofs)

    if trigger_on == 'low':
        return index[:int(len(index) * sensitivity)]

    return index[- int(len(index) * sensitivity):]


@check_params(trigger_on=['low', 'high'])
def _lof_stdev(data, sensitivity, n_neighbors, trigger_on='low'):
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

    return _stdev(lofs, sensitivity=sensitivity, trigger_on=trigger_on)


@is_univariate
@check_params(trigger_on=['low', 'high'])
def _isolation_forest(data, sensitivity, trigger_on='low'):
    clf = IsolationForest(
        behaviour='new',
        max_samples=data.size,
        contamination=0
    )
    clf.fit(data.reshape(-1, 1))
    predictions = clf.predict(data.reshape(-1, 1))

    # 1: high density -1: low density
    predictions = clf.score_samples(data.reshape(-1, 1))
    predictions += 1

    if trigger_on == 'low':
        return np.arange(data.shape[0])[predictions < sensitivity/100]

    return np.arange(data.shape[0])[predictions > sensitivity/100]


@is_univariate
@check_params(trigger_on=['low', 'high'])
def _floats(data, sensitivity, trigger_on):
    if trigger_on == 'low':
        return np.arange(data.shape[0])[data < sensitivity]

    return np.arange(data.shape[0])[data > sensitivity]


@is_univariate
@check_params(trigger_on=['low', 'high'])
def _pct_of_avg_value(data, sensitivity, trigger_on):
    avg = data.mean()
    pct = sensitivity / 100

    if trigger_on == 'low':
        return np.arange(data.shape[0])[data < avg * pct]

    return np.arange(data.shape[0])[data > avg * pct]


@is_univariate
@check_params(trigger_on=['low', 'high'])
def _pct_of_max_value(data, sensitivity, trigger_on):
    avg = data.max()
    pct = sensitivity / 100

    if trigger_on == 'low':
        return np.arange(data.shape[0])[data < avg * pct]

    return np.arange(data.shape[0])[data > avg * pct]


@is_univariate
@check_params(trigger_on=['low', 'high'])
def _pct_of_min_value(data, sensitivity, trigger_on):
    avg = data.min()
    pct = sensitivity / 100

    if trigger_on == 'low':
        return np.arange(data.shape[0])[data < avg * pct]

    return np.arange(data.shape[0])[data > avg * pct]


@is_univariate
@check_params(trigger_on=['low', 'high'])
def _pct_of_median_value(data, sensitivity, trigger_on):
    avg = data.max()
    pct = sensitivity / 100

    if trigger_on == 'low':
        return np.arange(data.shape[0])[data < avg * pct]

    return np.arange(data.shape[0])[data > avg * pct]


@is_univariate
@check_params(trigger_on=['low', 'high'])
def _percentile(data, sensitivity, trigger_on):
    percentile = np.percentile(data, sensitivity)

    if trigger_on == 'low':
        return np.arange(data.shape[0])[data <= percentile]

    return np.arange(data.shape[0])[data >= percentile]


@check_params()
def _trigger_all(data):
    return np.arange(data.shape[0])
