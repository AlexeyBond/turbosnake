# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import GenericRepr, Snapshot


snapshots = Snapshot()

snapshots['FunctionalComponentTest::test_render_children 1'] = {
    '__class__': 'FunctionalComponent<parent>',
    '__component__': True,
    'children': [
        {
            '__class__': GenericRepr("<class 'components.Fragment'>"),
            '__component__': True,
            'children': [
                {
                    '__class__': GenericRepr("<class 'components.Fragment'>"),
                    '__component__': True,
                    'children': [
                        {
                            '__class__': 'FunctionalComponent<child>',
                            '__component__': True,
                            'children': [
                            ],
                            'key': (
                                'FunctionalComponent<child>',
                                1
                            ),
                            'props': {
                            }
                        }
                    ],
                    'key': (
                        GenericRepr("<class 'components.Fragment'>"),
                        1
                    ),
                    'props': {
                        'children': {
                            '__class__': GenericRepr("<class 'components.ComponentsCollection'>"),
                            'items': [
                                {
                                    '__class__': 'FunctionalComponent<child>',
                                    '__component__': True,
                                    'children': [
                                    ],
                                    'key': (
                                        'FunctionalComponent<child>',
                                        1
                                    ),
                                    'props': {
                                    }
                                }
                            ]
                        }
                    }
                }
            ],
            'key': (
                GenericRepr("<class 'components.Fragment'>"),
                1
            ),
            'props': {
                'children': {
                    '__class__': GenericRepr("<class 'components.ComponentsCollection'>"),
                    'items': [
                        {
                            '__class__': GenericRepr("<class 'components.Fragment'>"),
                            '__component__': True,
                            'children': [
                                {
                                    '__class__': 'FunctionalComponent<child>',
                                    '__component__': True,
                                    'children': [
                                    ],
                                    'key': (
                                        'FunctionalComponent<child>',
                                        1
                                    ),
                                    'props': {
                                    }
                                }
                            ],
                            'key': (
                                GenericRepr("<class 'components.Fragment'>"),
                                1
                            ),
                            'props': {
                                'children': {
                                    '__class__': GenericRepr("<class 'components.ComponentsCollection'>"),
                                    'items': [
                                        {
                                            '__class__': 'FunctionalComponent<child>',
                                            '__component__': True,
                                            'children': [
                                            ],
                                            'key': (
                                                'FunctionalComponent<child>',
                                                1
                                            ),
                                            'props': {
                                            }
                                        }
                                    ]
                                }
                            }
                        }
                    ]
                }
            }
        }
    ],
    'key': None,
    'props': {
        'children': {
            '__class__': GenericRepr("<class 'components.ComponentsCollection'>"),
            'items': [
                {
                    '__class__': 'FunctionalComponent<child>',
                    '__component__': True,
                    'children': [
                    ],
                    'key': (
                        'FunctionalComponent<child>',
                        1
                    ),
                    'props': {
                    }
                }
            ]
        }
    }
}

snapshots['FunctionalComponentTest::test_render_nested 1'] = {
    '__class__': 'FunctionalComponent<parent>',
    '__component__': True,
    'children': [
        {
            '__class__': 'FunctionalComponent<child>',
            '__component__': True,
            'children': [
            ],
            'key': (
                'FunctionalComponent<child>',
                1
            ),
            'props': {
                'cprop1': 'bar'
            }
        }
    ],
    'key': None,
    'props': {
        'prop1': 'bar'
    }
}
