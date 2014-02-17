from nose.tools import assert_equal
from schemas import is_string, required_key, optional_key, sanitize_map


TEST_SCHEMA = {required_key('host'): is_string,
               'port': lambda p: 0 <= p < 65536,
               optional_key('description'): is_string}


def test_sanitize_map():
    data = {'host': 'some_string',
            'port': 0,
            'description': 'some_description'}
    assert_equal(sanitize_map(data, TEST_SCHEMA), data)
