from functools import partial
import operator as op

from functions import identity
import pytest
import simplejson as json

import schemas as s


def gen_obj(*args):
    def s0(args):
        return {}

    def s1(args):
        return {'a': args[0]}

    def s2(args):
        return {'a': {'b': args[0],
                      'c': args[1]}}

    def s4(args):
        return {'a': {'b': args[0],
                      'c': args[1]},
                'd': ({'e': args[2],
                       'f': args[3]})}

    def s6(args):
        return {'a': {'b': args[0],
                      'c': args[1]},
                'd': ({'e': args[2],
                       'f': args[3]},
                      {'e': args[4],
                       'f': args[5]})}
    def s12(args):
        return ({'a': {'b': args[0],
                       'c': args[1]},
                 'd': ({'e': args[2],
                        'f': args[3]},
                       {'e': args[4],
                        'f': args[5]})},
                {'a': {'b': args[6],
                       'c': args[7]},
                 'd': ({'e': args[8],
                        'f': args[9]},
                       {'e': args[10],
                        'f': args[11]})})
    objects = {0: s0, 1: s1, 2: s2, 4: s4, 6: s6, 12: s12}
    return objects[len(args)](args)


def hexlify(k, v):
    return (k, hex(v))


def is_between_three_and_nine(k, v):
    if 3 < v < 9:
        return (k, hex(v))
    return None


def join(k, v1, v2):
    return (k, v1 + v2)


def log_it(k):
    print "Cannot find '{0}', key not in schema".format(k)
    return None


def letters(n):
    return [chr(ord('a') + i) for i in range(n)]


def test_walk_data_is_object():
    expects = gen_obj(*map(hex, range(6)))
    assert s.walk(hexlify, identity, gen_obj(*range(6))) == expects


def test_walk_data_is_array():
    data = gen_obj(*range(12))
    assert s.walk(hexlify, identity, data) == gen_obj(*map(hex, range(12)))


def test_walk_with_outer_func_data_is_object():
    data = gen_obj(*range(6))
    assert s.walk(hexlify, json.dumps, data) == json.dumps(gen_obj(*map(hex, range(6))))


def test_walk_with_outer_func_data_is_array():
    data = gen_obj(*range(12))
    assert s.walk(hexlify, json.dumps, data) == json.dumps(gen_obj(*map(hex, range(12))))


def test_walk_filter_range_data_is_object():
    assert s.walk(is_between_three_and_nine, identity, gen_obj(*range(4))) == {}


def test_walk_filter_range_data_is_array():
    expects = ({'d': ({'e': '0x4',
                       'f': '0x5'},)},
               {'a': {'b': '0x6',
                      'c': '0x7'},
                'd': ({'e': '0x8'},)})
    assert s.walk(is_between_three_and_nine, identity, gen_obj(*range(12))) == expects


def test_walk_pair_data_is_object():
    s1 = gen_obj(*letters(6))
    s2 = gen_obj('A', 'B', 'C', 'D')
    expects = gen_obj('aA', 'bB', 'cC', 'dD', 'eC', 'fD')
    assert s.walk_pair(join, identity, s1, s2, log_it) == expects


def test_walk_pair_data_is_array():
    s1 = gen_obj(*letters(12))
    s2 = (gen_obj('A', 'B', 'C', 'D'),)
    expects = gen_obj(
        'aA', 'bB', 'cC', 'dD', 'eC', 'fD', 'gA', 'hB', 'iC', 'jD', 'kC', 'lD')
    assert s.walk_pair(join, identity, s1, s2, log_it) == expects


def test_walk_pair_data_is_array_schema_is_object():
    s1 = gen_obj(*letters(12))
    s2 = gen_obj('A', 'B', 'C', 'D')
    expects = gen_obj(
        'aA', 'bB', 'cC', 'dD', 'eC', 'fD', 'gA', 'hB', 'iC', 'jD', 'kC', 'lD')
    assert s.walk_pair(join, identity, s1, s2, log_it) == expects


def test_sanitize_keys():
    schema = {'a': {(s.required_key, 'b'): s.number,
                    'c': s.any},
              'd': ({(s.required_key, 'e'): s.string,
                     (s.optional_key, 'f'): s.pos})}
    expects = gen_obj(s.number, s.any, s.string, s.pos)
    assert s.sanitize_keys(schema) == expects


def test_sanitize():
    schema = gen_obj(s.number, s.eq('test'), s.string, s.pos)
    data = gen_obj(4, 'bad_value', 'abc', -1, 7, 4)
    expects = {'a': {'b': 4},
               'd': ({'e': 'abc'},
                     {'f': 4})}
    assert s.sanitize(data, schema) == expects


def test_any():
    schema = gen_obj(s.any, s.any, s.any, s.any)
    data = gen_obj(4, 'bad_value', 'abc', -1, 7, 4)
    assert s.sanitize(data, schema) == data


def test_validate():
    schema = gen_obj(s.number, s.eq('test'), s.string, s.pos)
    data = gen_obj(4, 'bad_value', 'abc', -1, 7, 4)
    expects = {'a': {'b': 4},
               'd': ({'e': 'abc'},
                     {'f': 4})}
    assert s.validate(data, schema) == expects


def test_validate_key_required():
    schema = {'a': {'b': s.number,
                    (s.required_key, 'c'): s.eq('test')},
              'd': ({'e': s.string,
                     'f': s.pos})}
    data = gen_obj(4, 'bad_value', 'abc', -1, 7, 4)
    with pytest.raises(s.MarshallingError) as excinfo:
        s.validate(data, schema)
    assert excinfo.value.message == 'Field missing: c'


def test_validate_partial_schema():
    schema = {'a': {'b': s.number}}
    data = gen_obj(4, 'bad_value', 'abc', -1, 7, 4)
    assert s.validate(data, schema) == {'a': {'b': 4}}


def test_marshal_before():
    schema = gen_obj([partial(op.mul, 1000), partial(op.mul, 1)],
                     [partial(op.mul, 100), partial(op.mul, 10)],
                     [partial(op.mul, 10), partial(op.mul, 100)],
                     [partial(op.mul, 1), partial(op.mul, 1000)])
    data = gen_obj(*range(6))
    expects = gen_obj(0, 100, 20, 3, 40, 5)
    assert s.marshal(data, schema, before=True) == expects


def test_marshal_after():
    schema = gen_obj([partial(op.mul, 1000), partial(op.mul, 1)],
                     [partial(op.mul, 100), partial(op.mul, 10)],
                     [partial(op.mul, 10), partial(op.mul, 100)],
                     [partial(op.mul, 1), partial(op.mul, 1000)])
    data = gen_obj(*range(6))
    expects = gen_obj(0, 10, 200, 3000, 400, 5000)
    assert s.marshal(data, schema) == expects


def test_marshal_default():
    schema = gen_obj(partial(op.mul, 1000),
                     partial(op.mul, 100),
                     partial(op.mul, 10),
                     partial(op.mul, 1))
    data = gen_obj(*range(6))
    expects = gen_obj(0, 100, 20, 3, 40, 5)
    assert s.marshal(data, schema) == expects


def test_marshalling_error():
    schema = gen_obj(partial(op.div, 1))
    data = gen_obj(0)
    with pytest.raises(s.MarshallingError) as excinfo:
        s.marshal(data, schema)
    assert excinfo.value.message == "Cannot process node for key 'a' and value '0'"
