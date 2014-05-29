import collections
from functools import partial, wraps
import numbers
import operator as op
import re

from functions import first, identity, is_seq, last, merge, walk


eq = lambda val: partial(op.eq, val)
identical = lambda val: partial(op.is_, val)
boolean = lambda x: isinstance(x, bool)
number = lambda x: isinstance(x, numbers.Number)
pos = lambda x: True if number(x) and x > 0 else False
string = lambda x: isinstance(x, basestring)
match = lambda pattern: lambda text: re.search(pattern, text)
subset = lambda set_: partial(op.contains, set_)
any = lambda x: x
optional_key = lambda x: x
required_key = lambda x: x


class MarshallingError(Exception):
    pass


def walk_pair(inner, outer, data, schema, handler):
    """ Traverse a pair of data structures and apply a function to each node. """
    def process_node(inner, k, v1, v2):
        if (not isinstance(v1, collections.Iterable)
            or isinstance(v1, basestring)
            or ((isinstance(v1, collections.Sequence)
                 and not isinstance(v1, basestring)
                 and hasattr(v2, '__call__')))):
            return inner(k, v1, v2)
        if isinstance(v1, collections.Sequence):
            rows = tuple(walk_pair(inner, identity, row, v2, handler) for row in v1)
            rv = tuple(filter(lambda row: row, rows))
        else:
            rv = walk_pair(inner, identity, v1, v2, handler)
        return (k, rv) if rv else None
    if isinstance(data, collections.Sequence):
        if isinstance(schema, collections.Sequence):
            schema_row = first(schema)
        else:
            schema_row = schema
        return outer(tuple(walk_pair(inner, identity, row, schema_row, handler)
                           for row in data))
    nodes = ()
    for (k, v) in data.iteritems():
        if k not in schema:
            if isinstance(k, collections.Sequence) and not isinstance(k, basestring):
                if not set(k).intersection(set(schema)):
                    handler(k)
                    nodes += ()
                else:
                    nodes += (process_node(inner, k, v, schema[last(k)]),)
            else:
                handler(k)
                nodes += ()
        else:
            nodes += (process_node(inner, k, v, schema[k]),)
    return outer(dict(filter(lambda node: node is not None, nodes)))


def sanitize_keys(schema):
    def sanitize_key(k, v):
        if is_seq(k):
            return (last(k), v)
        return (k, v)
    return walk(sanitize_key, identity, schema)


def sanitize(data, schema):
    def sanitize_node(k, v, validator):
        if validator(v) or validator == any:
            return (k, v)
        else:
            print "Schema violation for key '{0}' and value '{1}'".format(k, v)
            return None

    def handler(k):
        print "Cannot validate '{0}', key not in schema".format(k)
        return None
    return walk_pair(sanitize_node, identity, data, sanitize_keys(schema), handler)


def validate(data, schema):
    def identity3(k, v, validator):
        return (k, v)

    def handler(k):
        if is_seq(k):
            type_, key = k
        else:
            type_, key = optional_key, k
        if type_ == required_key:
            raise MarshallingError("Field missing: {0}".format(key))
        return None
    sanitized_data = sanitize(data, schema)
    walk_pair(identity3, identity, schema, sanitized_data, handler)
    return sanitized_data


def validate_with(schema):
    """Validate function arguments and check required fields."""
    def decorator(f):
        @wraps(f)
        def wrapper(data, *args, **kwargs):
            return f(validate(data, schema), *args, **kwargs)
        return wrapper
    return decorator


def marshal(data, schema, before=False):
    def marshal_node(k, v1, v2, before=False):
        if isinstance(v2, dict) and v1 is None:
            return (k, None)
        if not is_seq(v2):
            func = identity
        else:
            func = first if before else last
        try:
            return (k, func(v2)(v1))
        except (TypeError, ZeroDivisionError):
            raise MarshallingError(
                "Cannot process node for key '{0}' and value '{1}'".format(k, v1))

    def handler(k):
        print "Cannot process '{0}', key not in schema".format(k)
        return None
    return walk_pair(partial(marshal_node, before=before), identity, data, schema,
                     handler)


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


# this doesn't work'
# def satisfies(schema, data):
#     def assert_at_node(k, validator, v):
#         if validator.__class__ == partial and validator.func == op.eq:
#             assert v == first(validator.args)
#         else:
#             assert validator(v)
#         return None

#     def handler(k):
#         raise AssertionError("Cannot validate '{0}', key not in data".format(k))
#     return walk_pair(assert_at_node, identity, data, sanitize_keys(schema), handler)
