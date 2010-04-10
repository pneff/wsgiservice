# -*- coding: utf-8 -*-
"""This tests only work in Python 2.6 and newer. They are in a separate file
so that the parse exceptions don't cause any problems with the other tests.
"""
import sys
import wsgiservice
import nose


def test_mount():
    """mount decorator adds the path as an attribute _path."""

    @wsgiservice.mount('/{id}')
    class Document(wsgiservice.Resource):
        pass

    assert Document.__name__ == 'Document'
    assert Document._path == '/{id}'


def test_validate_resource():
    """validate decorator adds rules to the _validations attribute list."""

    @wsgiservice.validate('id', re=r'[-0-9a-zA-Z]{36}',
        doc='Document ID, must be a valid UUID.')
    class User(wsgiservice.Resource):
        pass

    print User._validations
    assert User.__name__ == 'User'
    assert User._validations['id'] == {'re': r'[-0-9a-zA-Z]{36}',
        'convert': None, 'doc': 'Document ID, must be a valid UUID.'}
