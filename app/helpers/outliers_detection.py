import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor

from functools import wraps


#############
# DECORATOR #
#############
def need_neighbors(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        options = args[0]
        if 'n_neighbors' not in options or options['n_neighbors'] <= 0:
            raise Exception('This method needs [n_neighbors]')

        return f(*args, **kwargs)

    return decorated


def is_univariate(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        options = args[0]
        data = args[1]

        if data.ndim > 2 or (data.ndim == 2 and data.shape[1] > 1):
            raise Exception('This method accept only 1D vector')

        if data.ndim == 2:
            data = data.reshape(-1)

        return f(options, data)

    return decorated


#####################
# OUTLIER DETECTION #
#####################
def outlier_detection(options, data):
    if '_' + options['method'] not in globals():
        raise Exception('Wrong method')
    method = globals()['_' + options['method']]

    return method(options, data)


@is_univariate
def _stdev(options, data):
    if not data.std():
        return np.array([])
    scores = abs(data-np.median(data)) / data.std()
    return np.where(scores > options['sensitivity'])[0]


@is_univariate
def _z_score(options, data):
    mad = np.median(abs(data-np.median(data)))
    z_scores = abs(0.6745 * (data - np.median(data)) / mad)
    return np.where(z_scores > options['sensitivity'])[0]


@is_univariate
def _mad(options, data):
    mad = np.median(abs(data-np.median(data)))
    if not mad:
        return []
    dec = abs((data - np.median(data)) / mad)
    return np.where(dec > options['sensitivity'])[0]


@is_univariate
def _mad_low(options, data):
    mad = np.median(abs(data-np.median(data)))
    if not mad:
        return []
    dec = (data - np.median(data)) / mad
    return np.where(dec < options['sensitivity'])[0]


@is_univariate
def _mad_high(options, data):
    mad = np.median(abs(data-np.median(data)))
    if not mad:
        return []
    dec = (data - np.median(data)) / mad
    return np.where(dec > options['sensitivity'])[0]


@is_univariate
def _stdev(options, data):
    if not data.std():
        return np.array([])
    scores = abs(data-np.median(data)) / data.std()
    return np.where(scores > options['sensitivity'])[0]


@is_univariate
def _stdev_low(options, data):
    if not data.std():
        return np.array([])
    scores = (data-np.median(data)) / data.std()
    return np.where(scores < options['sensitivity'])[0]


@is_univariate
def _stdev_high(options, data):
    if not data.std():
        return np.array([])
    scores = (data-np.median(data)) / data.std()
    return np.where(scores > options['sensitivity'])[0]


@need_neighbors
def _lof(options, data):

    if data.shape[0] <= options['n_neighbors']:
        # Not enough data to find outliers...
        return []

    if data.ndim == 1:
        data = data.reshape(-1, 1)
    clf = LocalOutlierFactor(
        novelty=True, contamination=options['sensitivity']/100,
        n_neighbors=options['n_neighbors']
    )
    clf.fit(data)

    predictions = clf.predict(data)

    return np.arange(data.shape[0])[predictions < 0]


@need_neighbors
def _lof_stdev(options, data):
    if data.shape[0] <= options['n_neighbors']:
        # Not enough data to find outliers...
        return []

    if data.ndim == 1:
        data = data.reshape(-1, 1)

    clf = LocalOutlierFactor(
        novelty=True,
        contamination=0.1,
        n_neighbors=options['n_neighbors']
    )
    clf.fit(data)
    lofs = clf.score_samples(data)

    return _stdev(lofs)


@is_univariate
def _isolation_forest(options, data):
    clf = IsolationForest(
        behaviour='new',
        max_samples=data.size,
        contamination=options['sensitivity']/100
    )
    clf.fit(data.reshape(-1, 1))
    predictions = clf.predict(data.reshape(-1, 1))

    return np.arange(data.shape[0])[predictions < 0]


@is_univariate
def _less_than_sensitivity(options, data):
    return np.arange(data.shape[0])[data < options['sensitivity']]


@is_univariate
def _pct_of_avg_value_low(options, data):
    avg = data.mean()
    pct = options['sensitivity'] / 100

    return np.arange(data.shape[0])[data < avg * pct]


@is_univariate
def _pct_of_avg_value_high(options, data):
    avg = data.mean()
    pct = options['sensitivity'] / 100

    return np.arange(data.shape[0])[data > avg * pct]
