import asyncio

from snapshottest import TestCase as SnapshotTestCase
from snapshottest.formatter import Formatter
from snapshottest.formatters import BaseFormatter as BaseSnapshotFormatter

from turbosnake import Tree, Component, ComponentsCollection
from turbosnake._utils import get_component_class
from turbosnake.test_helpers._selectors import Selector


class TestTree(Tree):
    def __init__(self):
        super().__init__()
        self.__callbacks = []

    @property
    def event_loop(self) -> asyncio.AbstractEventLoop:
        # TODO: Implement this and test asynchronous operation hook(s)
        raise NotImplemented

    def schedule_task(self, callback):
        self.__callbacks.append(callback)

    def schedule_delayed_task(self, delay, callback):
        # TODO: Implement some way of testing delayed tasks
        raise NotImplemented

    def run_tasks(self):
        ran_tasks = 0

        while len(self.__callbacks):
            self.__callbacks.pop(0)()
            ran_tasks += 1

        return ran_tasks


class ComponentSnapshotFormatter(BaseSnapshotFormatter):
    def can_format(self, value):
        return isinstance(value, Component)

    def format(self, value, indent, formatter):
        return formatter.format(self.normalize(value, formatter), indent)

    def normalize(self, value, formatter):
        return formatter.normalize({
            '__class__': value.class_id(),
            '__component__': True,
            'children': list(value.mounted_children()),
            'key': value.key,
            'props': value.props,
        })


class ComponentsCollectionSnapshotFormatter(BaseSnapshotFormatter):
    def can_format(self, value):
        return isinstance(value, ComponentsCollection)

    def format(self, value, indent, formatter):
        return formatter.format(self.normalize(value, formatter), indent)

    def normalize(self, value, formatter):
        return formatter.normalize({
            '__class__': ComponentsCollection,
            'items': list(value)
        })


Formatter.formatters.insert(0, ComponentSnapshotFormatter())
Formatter.formatters.insert(0, ComponentsCollectionSnapshotFormatter())


class TreeTestCase(SnapshotTestCase):
    def setUp(self):
        SnapshotTestCase.setUp(self)
        self.tree = TestTree()

    def render(self, component, **props):
        with self.tree:
            component(**props)

        self.tree.run_tasks()

        return self.tree.root

    def assertTreeMatchesSnapshot(self, run_tasks=True, **kwargs):
        if run_tasks:
            self.tree.run_tasks()

        self.assertMatchSnapshot(self.tree.root, **kwargs)

    def assertIsComponentInstance(self, component, component_class_or_inserter, msg=None):
        self.assertIsInstance(component, get_component_class(component_class_or_inserter), msg)

    def root_selector(self) -> Selector:
        return Selector([self.tree.root])
