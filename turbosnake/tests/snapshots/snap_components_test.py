# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import GenericRepr, Snapshot

snapshots = Snapshot()

snapshots['ComponentTest::test_nested_fragments_snapshot 1'] = {
    '__class__': GenericRepr("<class 'turbosnake._components.Fragment'>"),
    '__component__': True,
    'children': [
        {
            '__class__': GenericRepr("<class 'turbosnake._components.Fragment'>"),
            '__component__': True,
            'children': [
            ],
            'key': (
                GenericRepr("<class 'turbosnake._components.Fragment'>"),
                1
            ),
            'props': {
            }
        },
        {
            '__class__': GenericRepr("<class 'turbosnake._components.Fragment'>"),
            '__component__': True,
            'children': [
                {
                    '__class__': GenericRepr("<class 'turbosnake._components.Fragment'>"),
                    '__component__': True,
                    'children': [
                    ],
                    'key': (
                        GenericRepr("<class 'turbosnake._components.Fragment'>"),
                        1
                    ),
                    'props': {
                    }
                }
            ],
            'key': (
                GenericRepr("<class 'turbosnake._components.Fragment'>"),
                2
            ),
            'props': {
                'children': {
                    '__class__': GenericRepr("<class 'turbosnake._components.ComponentsCollection'>"),
                    'items': [
                        {
                            '__class__': GenericRepr("<class 'turbosnake._components.Fragment'>"),
                            '__component__': True,
                            'children': [
                            ],
                            'key': (
                                GenericRepr("<class 'turbosnake._components.Fragment'>"),
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
    'key': None,
    'props': {
        'children': {
            '__class__': GenericRepr("<class 'turbosnake._components.ComponentsCollection'>"),
            'items': [
                {
                    '__class__': GenericRepr("<class 'turbosnake._components.Fragment'>"),
                    '__component__': True,
                    'children': [
                    ],
                    'key': (
                        GenericRepr("<class 'turbosnake._components.Fragment'>"),
                        1
                    ),
                    'props': {
                    }
                },
                {
                    '__class__': GenericRepr("<class 'turbosnake._components.Fragment'>"),
                    '__component__': True,
                    'children': [
                        {
                            '__class__': GenericRepr("<class 'turbosnake._components.Fragment'>"),
                            '__component__': True,
                            'children': [
                            ],
                            'key': (
                                GenericRepr("<class 'turbosnake._components.Fragment'>"),
                                1
                            ),
                            'props': {
                            }
                        }
                    ],
                    'key': (
                        GenericRepr("<class 'turbosnake._components.Fragment'>"),
                        2
                    ),
                    'props': {
                        'children': {
                            '__class__': GenericRepr("<class 'turbosnake._components.ComponentsCollection'>"),
                            'items': [
                                {
                                    '__class__': GenericRepr("<class 'turbosnake._components.Fragment'>"),
                                    '__component__': True,
                                    'children': [
                                    ],
                                    'key': (
                                        GenericRepr("<class 'turbosnake._components.Fragment'>"),
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
