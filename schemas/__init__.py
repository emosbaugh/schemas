from functools import partial, wraps
import numbers
import operator as op
import re

from functions import first, identity, is_seq, last, merge, walk


class MarshallingError(Exception):
    pass


def eq(x):
    return partial(op.eq, x)


def is_identical(x):
    return partial(op.is_, x)


def not_(x):
    return partial(op.not_, x)


def is_number(x):
    return isinstance(x, numbers.Number)


def is_pos(x):
    return True if is_number(x) and x > 0 else False


def is_subset(x):
    return partial(op.contains, x)


def is_string(x):
    return isinstance(x, str)


def is_match(pattern):
    return lambda text: re.search(pattern, text)


def required_key():
    return None


def optional_key():
    return None


def strip_metadata(schema):
    def process_node(k, v):
        if is_seq(k):
            return (last(k), v)
        return (k, v)
    return walk(process_node, identity, schema)


def sanitize(data, schema):
    def process_node(schema, k, v):
        if k in schema:
            if schema[k](v) or schema[k] == identity:
                return (k, v)
            else:
                print "Schema violation for key '{0}' and value '{1}'".format(k, v)
        else:
            print "Cannot validate '{0}', key not in schema".format(k)
        return None
    return walk(partial(process_node, strip_metadata(schema)), identity, data)


def validate(data, schema):
    def is_missing(data, k, v):
        if is_seq(k):
            type_, key = k
        else:
            type_, key = optional_key, k
        if key not in data and type_ == required_key:
            return (key, None)
        return None
    sanitized_data = sanitize(data, schema)
    omitted = walk(partial(is_missing, sanitized_data), identity, schema)
    if omitted:
        raise MarshallingError("Fields missing: " + ", ".join(omitted.keys()))
    return sanitized_data


def validate_with(schema):
    """Validate function arguments and check for required fields."""
    def decorator(f):
        @wraps(f)
        def wrapper(data, *args, **kwargs):
            return f(validate(data, schema), *args, **kwargs)
        return wrapper
    return decorator


def marshal(data, schema, before=False):
    def process_node(schema, k, v, before=False):
        try:
            if not isinstance(schema[k], (list, tuple)):
                func = identity
            else:
                func = first if before else last
            try:
                return (k, func(schema[k])(v))
            except TypeError:
                raise MarshallingError(
                    "Cannot process node for key '{0}' and value '{1}'".format(k, v))
        except KeyError:
            return None
    return walk(partial(process_node, schema, before=before), identity, data)


def marshal_with(schema):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if args:
                data = marshal(first(args), schema, before=True)
                rmap = f(data, **kwargs)
                body = marshal(rmap['body'], schema)
                return merge(rmap, {'body': body})
            else:
                rmap = f(*args, **kwargs)
                body = marshal(rmap['body'], schema)
                return merge(rmap, {'body': body})
        return wrapper
    return decorator


def satisfies(data, schema):
    def process_node(schema, k, v):
        if schema[k].__class__ == partial and schema[k].func == op.eq:
            assert first(schema[k].args) == v
        else:
            assert schema[k](v)
    return walk(partial(process_node, schema), identity, data)
