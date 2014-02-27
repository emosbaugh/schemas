from functools import partial, wraps
import numbers
import operator as op

from functions import (MarshallingError, first, identity, is_seq, last, merge,
                       walk_keys)


def required_key():
    return None


def optional_key():
    return None


def strip_metadata(k, v):
    if is_seq(k):
        return (last(k), v)
    return (k, v)


def sanitize(schema, k, v):
    if k in schema:
        if schema[k](v) or schema[k] == identity:
            return (k, v)
        else:
            print "Schema violation for key '{0}' and value '{1}'".format(k, v)
    else:
        print "Cannot validate '{0}', key not in schema".format(k)
    return None


def is_missing(data, k, v):
    if is_seq(k):
        func, key = k
    else:
        func, key = optional_key, k
    if key not in data and func == required_key:
        return (key, None)
    return None


def validate(schema):
    """Validate function arguments and check for required fields."""
    def decorator(f):
        @wraps(f)
        def wrapper(data, *args, **kwargs):
            schema_ = walk_keys(strip_metadata, identity, schema)
            sanitized = walk_keys(partial(sanitize, schema_), identity, data)
            omitted = walk_keys(partial(is_missing, sanitized), identity, schema)
            if omitted:
                raise MarshallingError("Fields missing: " + ", ".join(omitted.keys()))
            return f(sanitized, *args, **kwargs)
        return wrapper
    return decorator


def marshal(schema, k, v, before=False):
    try:
        if not isinstance(schema[k], (list, tuple)):
            func = identity
        else:
            func = first if before else last
        return (k, func(schema[k])(v))
    except KeyError:
        return None


def marshal_with(schema):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if args:
                data = walk_keys(partial(marshal, schema, before=True), identity, *args)
                rmap = f(data, **kwargs)
                body = walk_keys(partial(marshal, schema), identity, rmap['body'])
                return merge(rmap, {'body': body})
            else:
                rmap = f(*args, **kwargs)
                body = walk_keys(partial(marshal, schema), identity, rmap['body'])
                return merge(rmap, {'body': body})
        return wrapper
    return decorator


def is_string(x):
    return isinstance(x, str)


def is_number(x):
    return isinstance(x, numbers.Number)


def is_subset(x):
    return partial(op.contains, x)


def is_positive(x):
    return True if x > 0 else False
