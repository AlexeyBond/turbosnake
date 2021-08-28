import queue
from collections import OrderedDict, Counter, Iterable

from render_context import get_render_context, render_context_manager, enter_render_context


class Tree:
    def __init__(self):
        self.__update_queue = queue.SimpleQueue()
        self.__update_processing_scheduled = False

    def enqueue_update(self, component):
        self.__update_queue.put(component)
        if not self.__update_processing_scheduled:
            self.schedule_task(self.__process_updates)
            self.__update_processing_scheduled = True

    def __process_updates(self):
        self.__update_processing_scheduled = False

        try:
            while True:
                self.__update_queue.get_nowait().update()
        except queue.Empty:
            pass

    def schedule_task(self, callback):
        raise NotImplemented


class Component:
    def __init__(self, key=None, **props):
        self.props = props

        collection_builder: ComponentCollectionBuilder = get_render_context(ComponentCollectionBuilder)

        assert collection_builder, 'Components must be created inside a proper rendering context'

        if key is None:
            key = collection_builder.get_default_key(prefix=self.__class__)

        self.key = key

        self.insert(collection_builder)

    def insert(self, builder: 'ComponentCollectionBuilder' = None):
        assert not getattr(self, 'tree', None), 'Attempt to render a mounted component'

        (builder or get_render_context(ComponentCollectionBuilder)).append(self)

    def mount(self, parent):
        assert not getattr(self, 'tree', None), 'Attempt to mount a mounted component'

        self.parent: Component = parent
        self.tree: Tree = parent.tree
        self.__state = {}
        self.__update_enqueued = False
        self.prev_props = self.props

        self.enqueue_update()

    def unmount(self):
        del self.parent
        del self.tree

    def enqueue_update(self):
        if not self.__update_enqueued:
            self.tree.enqueue_update(self)
            self.__update_enqueued = True

    def update_props_from(self, other: 'Component') -> bool:
        if other.props == self.props:
            return False

        self.props = other.props
        return True

    def props_equal_to(self, other: 'Component') -> bool:
        return other.props == self.props

    def update(self):
        self.__update_enqueued = False
        self.prev_props = self.props

    def get_state(self, key):
        return self.__state[key]

    def get_state_or_init(self, key, default):
        try:
            return self.__state[key]
        except KeyError:
            self.__state[key] = default
            return default

    def set_state(self, key, value):
        cur = self.get_state(key)
        if cur == value:
            return
        self.__state[key] = value
        self.enqueue_update()

    def del_state(self, key):
        if key in self.__state:
            del self.__state[key]
            self.enqueue_update()

    def mounted_children(self):
        """Iterator over all mounted children of this component"""
        yield from ()


class ComponentsCollection(list):
    def __eq__(self, other):
        if not other or not isinstance(other, ComponentsCollection):
            return False

        if len(self) != len(other):
            return False

        i2 = iter(other)

        for component in self:
            if not component.props_equal_to(next(i2)):
                return False

        return True


class ComponentCollectionBuilder:
    def __init__(self):
        self.__collection = ComponentsCollection()
        self.__incremental_key = Counter()

    def append(self, component):
        # assert isinstance(component, Component)
        self.__collection.append(component)

    def extend(self, components):
        self.__collection.extend(components)

    def get_default_key(self, prefix=None):
        self.__incremental_key[prefix] += 1
        return prefix, self.__incremental_key[prefix]

    def build(self):
        return self.__collection


class MountedComponentsCollection:
    """
    Manages a collection of components mounted to tree as children of a specified parent.
    """

    def __init__(self, parent):
        self.parent = parent
        self.components = OrderedDict()

    @staticmethod
    def is_updatable(component, new_component):
        return component.__class__ is new_component.__class__

    def __iter__(self) -> Iterable[Component]:
        return self.components.values()

    def update(self, components: list['Component']):
        old_components = self.components
        new_components = OrderedDict()

        for new_component in components:
            key = new_component.key
            old_component: Component = old_components.get(key, None)

            if old_component:
                if self.is_updatable(old_component, new_component):
                    if old_component.update_props_from(new_component):
                        old_component.enqueue_update()
                    new_components[key] = old_component
                    continue
                else:
                    old_component.unmount()
                    del old_components[key]

            new_component.mount(self.parent)

            new_components[key] = new_component

        for old_component in old_components.values():
            old_component.unmount()

        self.components = new_components

    def unmount(self):
        for component in self.components.values():
            component.unmount()
        self.components = OrderedDict()


class DynamicComponent(Component):
    """
    A Component that is built as a composition of other components rendered in #redner() function
    """

    def mount(self, parent):
        super().mount(parent)
        self.__mounted_children = MountedComponentsCollection(self)

    def unmount(self):
        super().unmount()
        self.__mounted_children.unmount()
        del self.__mounted_children

    def mounted_children(self):
        yield from self.__mounted_children

    def render(self):
        raise NotImplemented

    def update(self):
        builder = ComponentCollectionBuilder()

        with render_context_manager(ComponentCollectionBuilder, builder):
            self.render()

        self.__mounted_children.update(builder.build())

        super().update()


class ParentComponent(Component):
    """
    A component that can be rendered with a single set of "children" components which are stored as "children" prop
    of type ComponentsCollection.
    """

    def __enter__(self):
        assert not hasattr(self, '__restore_context')

        self.__restore_context = enter_render_context(ComponentCollectionBuilder, ComponentCollectionBuilder())

    def __exit__(self, exc_type, exc_val, exc_tb):
        builder = self.__restore_context()
        del self.__restore_context
        self.props['children'] = builder.build()
