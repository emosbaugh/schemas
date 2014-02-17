from functools import partial, wraps
import simplejson as json
from functions import first, is_seq, walk_keys


def required_key(k):
    return (k, True)


def optional_key(k):
    return (k, False)


def strip_metadata(k, v):
    if is_seq(k):
        return (first(k), v)
    return (k, v)


def sanitize(schema, k, v):
    if k in schema:
        if schema[k](v):
            return (k, v)
        else:
            print "Schema violation for key '{0}' and value '{1}'".format(k, v)
    else:
        print "Cannot validate '{0}', key not in schema".format(k)
    return None


def is_missing(data, k, v):
    if is_seq(k):
        key, required = k
    else:
        key, required = k, True
    if key not in data and required is True:
        return (key, None)
    return None


def validate(schema):
    """Validate function arguments and check for required fields."""
    def decorator(f):
        @wraps(f)
        def wrapper(data, *args, **kwargs):
            schema_ = walk_keys(strip_metadata, schema)
            sanitize_with_schema = partial(sanitize, schema_)
            sanitized_data = walk_keys(sanitize_with_schema, data)
            omitted = walk_keys(partial(is_missing, sanitized_data), schema)
            if omitted:
                raise ValueError("Required fields: " + json.dumps(omitted))
            return f(sanitized_data, *args, **kwargs)
        return wrapper
    return decorator
