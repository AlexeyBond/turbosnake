# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import GenericRepr, Snapshot

snapshots = Snapshot()

snapshots['SlotsRenderTest::test_render_slots_with_custom_prop_names 1'] = {
    '__class__': 'FunctionalComponent<tc>',
    '__component__': True,
    'children': [
        {
            '__class__': GenericRepr("<class 'turbosnake._components.Fragment'>"),
            '__component__': True,
            'children': [
                {
                    '__class__': 'FunctionalComponent<stub>',
                    '__component__': True,
                    'children': [
                    ],
                    'key': (
                        'FunctionalComponent<stub>',
                        1
                    ),
                    'props': {
                        'label': 'а'
                    }
                }
            ],
            'key': 'slotA',
            'props': {
                'children': {
                    '__class__': GenericRepr("<class 'turbosnake._components.ComponentsCollection'>"),
                    'items': [
                        {
                            '__class__': 'FunctionalComponent<stub>',
                            '__component__': True,
                            'children': [
                            ],
                            'key': (
                                'FunctionalComponent<stub>',
                                1
                            ),
                            'props': {
                                'label': 'а'
                            }
                        }
                    ]
                }
            }
        },
        {
            '__class__': GenericRepr("<class 'turbosnake._components.Fragment'>"),
            '__component__': True,
            'children': [
                {
                    '__class__': 'FunctionalComponent<stub>',
                    '__component__': True,
                    'children': [
                    ],
                    'key': (
                        'FunctionalComponent<stub>',
                        1
                    ),
                    'props': {
                        'label': 'ь'
                    }
                }
            ],
            'key': 'slotB',
            'props': {
                'children': {
                    '__class__': GenericRepr("<class 'turbosnake._components.ComponentsCollection'>"),
                    'items': [
                        {
                            '__class__': 'FunctionalComponent<stub>',
                            '__component__': True,
                            'children': [
                            ],
                            'key': (
                                'FunctionalComponent<stub>',
                                1
                            ),
                            'props': {
                                'label': 'ь'
                            }
                        }
                    ]
                }
            }
        }
    ],
    'key': None,
    'props': {
        'another_slot': {
            '__class__': GenericRepr("<class 'turbosnake._components.ComponentsCollection'>"),
            'items': [
                {
                    '__class__': 'FunctionalComponent<stub>',
                    '__component__': True,
                    'children': [
                    ],
                    'key': (
                        'FunctionalComponent<stub>',
                        1
                    ),
                    'props': {
                        'label': 'ь'
                    }
                }
            ]
        },
        'the_slot_named_a': {
            '__class__': GenericRepr("<class 'turbosnake._components.ComponentsCollection'>"),
            'items': [
                {
                    '__class__': 'FunctionalComponent<stub>',
                    '__component__': True,
                    'children': [
                    ],
                    'key': (
                        'FunctionalComponent<stub>',
                        1
                    ),
                    'props': {
                        'label': 'а'
                    }
                }
            ]
        }
    }
}

snapshots['SlotsRenderTest::test_render_slotted_component 1'] = {
    '__class__': 'FunctionalComponent<tc>',
    '__component__': True,
    'children': [
        {
            '__class__': GenericRepr("<class 'turbosnake._components.Fragment'>"),
            '__component__': True,
            'children': [
                {
                    '__class__': 'FunctionalComponent<stub>',
                    '__component__': True,
                    'children': [
                    ],
                    'key': (
                        'FunctionalComponent<stub>',
                        1
                    ),
                    'props': {
                        'label': 'stub-1-1'
                    }
                },
                {
                    '__class__': 'FunctionalComponent<stub>',
                    '__component__': True,
                    'children': [
                    ],
                    'key': (
                        'FunctionalComponent<stub>',
                        2
                    ),
                    'props': {
                        'label': 'stub-1-2'
                    }
                }
            ],
            'key': 'slot1',
            'props': {
                'children': {
                    '__class__': GenericRepr("<class 'turbosnake._components.ComponentsCollection'>"),
                    'items': [
                        {
                            '__class__': 'FunctionalComponent<stub>',
                            '__component__': True,
                            'children': [
                            ],
                            'key': (
                                'FunctionalComponent<stub>',
                                1
                            ),
                            'props': {
                                'label': 'stub-1-1'
                            }
                        },
                        {
                            '__class__': 'FunctionalComponent<stub>',
                            '__component__': True,
                            'children': [
                            ],
                            'key': (
                                'FunctionalComponent<stub>',
                                2
                            ),
                            'props': {
                                'label': 'stub-1-2'
                            }
                        }
                    ]
                }
            }
        },
        {
            '__class__': GenericRepr("<class 'turbosnake._components.Fragment'>"),
            '__component__': True,
            'children': [
                {
                    '__class__': 'FunctionalComponent<stub>',
                    '__component__': True,
                    'children': [
                    ],
                    'key': (
                        'FunctionalComponent<stub>',
                        1
                    ),
                    'props': {
                        'label': 'stub-2-1'
                    }
                },
                {
                    '__class__': 'FunctionalComponent<stub>',
                    '__component__': True,
                    'children': [
                    ],
                    'key': (
                        'FunctionalComponent<stub>',
                        2
                    ),
                    'props': {
                        'label': 'stub-2-2'
                    }
                }
            ],
            'key': 'slot2',
            'props': {
                'children': {
                    '__class__': GenericRepr("<class 'turbosnake._components.ComponentsCollection'>"),
                    'items': [
                        {
                            '__class__': 'FunctionalComponent<stub>',
                            '__component__': True,
                            'children': [
                            ],
                            'key': (
                                'FunctionalComponent<stub>',
                                1
                            ),
                            'props': {
                                'label': 'stub-2-1'
                            }
                        },
                        {
                            '__class__': 'FunctionalComponent<stub>',
                            '__component__': True,
                            'children': [
                            ],
                            'key': (
                                'FunctionalComponent<stub>',
                                2
                            ),
                            'props': {
                                'label': 'stub-2-2'
                            }
                        }
                    ]
                }
            }
        }
    ],
    'key': None,
    'props': {
        'slot_1': {
            '__class__': GenericRepr("<class 'turbosnake._components.ComponentsCollection'>"),
            'items': [
                {
                    '__class__': 'FunctionalComponent<stub>',
                    '__component__': True,
                    'children': [
                    ],
                    'key': (
                        'FunctionalComponent<stub>',
                        1
                    ),
                    'props': {
                        'label': 'stub-1-1'
                    }
                },
                {
                    '__class__': 'FunctionalComponent<stub>',
                    '__component__': True,
                    'children': [
                    ],
                    'key': (
                        'FunctionalComponent<stub>',
                        2
                    ),
                    'props': {
                        'label': 'stub-1-2'
                    }
                }
            ]
        },
        'slot_2': {
            '__class__': GenericRepr("<class 'turbosnake._components.ComponentsCollection'>"),
            'items': [
                {
                    '__class__': 'FunctionalComponent<stub>',
                    '__component__': True,
                    'children': [
                    ],
                    'key': (
                        'FunctionalComponent<stub>',
                        1
                    ),
                    'props': {
                        'label': 'stub-2-1'
                    }
                },
                {
                    '__class__': 'FunctionalComponent<stub>',
                    '__component__': True,
                    'children': [
                    ],
                    'key': (
                        'FunctionalComponent<stub>',
                        2
                    ),
                    'props': {
                        'label': 'stub-2-2'
                    }
                }
            ]
        }
    }
}
