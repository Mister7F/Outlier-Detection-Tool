from functools import wraps
import inspect
import collections


################
# check_params #
################
def _get_signature(function):
    annotations = function.__annotations__

    sig = inspect.signature(function)

    params = collections.OrderedDict()

    for i, p in enumerate(sig.parameters.values()):
        params[p.name] = ({'pos': i})

        if p.default is not inspect._empty:
            params[p.name]['default'] = p.default

        if p.name in annotations:
            params[p.name]['type'] = annotations[p.name]

    return params


def _function_params(sig, args, kwargs):
    params = {}

    for i, arg in enumerate(args):
        params[list(sig.keys())[i]] = arg

    for k in kwargs:
        params[k] = kwargs[k]

    return params


def check_params(*d_args, **d_kwargs):
    del d_args

    def decorator(function):
        sig = _get_signature(function)

        def wrapper(*args, **kwargs):
            params = _function_params(sig, args, kwargs)
            for rule in d_kwargs:
                if rule not in params:
                    if rule not in sig or 'default' not in sig[rule]:
                        raise Exception('A parameter is missing [%s]' % rule)
                    params[rule] = sig[rule]['default']

                elif d_kwargs[rule] and params[rule] not in d_kwargs[rule]:
                    raise Exception('Wrong value [%s] for [%s] accept: %s'
                                    % (str(params[rule]), rule,
                                       str(d_kwargs[rule])))

            for p in sig:
                if p not in params:
                    raise Exception('A parameter is missing [%s]' % p)

            return function(**params)
        return wrapper
    return decorator
