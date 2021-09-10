import queue
from abc import abstractmethod
from collections import OrderedDict, Counter, Iterable
from typing import Optional

from ._render_context import get_render_context, render_context_manager, enter_render_context


class Ref:
    def __init__(self):
        self.current = None


class Tree:
    def __init__(self):
        super().__init__()
        self.__update_queue = queue.SimpleQueue()
        self.__update_processing_scheduled = False
        self.__root: Optional[Component] = None

    def enqueue_update_component(self, component):
        self.__update_queue.put(component)
        if not self.__update_processing_scheduled:
            self.schedule_task(self.process_updates)
            self.__update_processing_scheduled = True

    def process_updates(self):
        self.__update_processing_scheduled = False

        try:
            while True:
                component = self.__update_queue.get_nowait()
                try:
                    component.update()
                except Exception as e:
                    self.handle_update_error(e, component=component)
        except queue.Empty:
            pass

    def schedule_task(self, callback):
        raise NotImplementedError()

    def handle_update_error(self, error: Exception, component: 'Component'):
        raise error

    @property
    def tree(self):
        return self

    @property
    def root(self):
        return self.__root

    def __enter__(self):
        assert not hasattr(self, '_Tree__restore_context')

        self.__restore_context = enter_render_context(ComponentRenderingContext.CONTEXT_ID,
                                                      SingletonComponentRenderContext())

    def __exit__(self, exc_type, exc_val, exc_tb):
        ctx: SingletonComponentRenderContext = self.__restore_context()
        del self.__restore_context

        if exc_type:
            return

        if self.__root:
            old_root = self.__root
            self.__root = None
            old_root.unmount()

        new_root = ctx.get_component()
        new_root.mount(self)
        self.__root = new_root


class Component:
    def __init__(self, /, key=None, ref: Optional[Ref] = None, **props):
        self.props = props
        self.key = key
        self.ref = ref

        self.insert()

    def insert(self, context: 'ComponentRenderingContext' = None):
        assert not self.is_mounted(), 'Attempt to render a mounted component'

        if not context:
            context = get_render_context(ComponentRenderingContext.CONTEXT_ID)

            assert context, 'Attempt to render component outside of a rendering context'

        context.append(self)

    def mount(self, parent):
        assert not self.is_mounted(), 'Attempt to mount a mounted component'

        self.parent: Component = parent
        self.__tree: Tree = parent.tree
        self.__state = {}
        self.__update_enqueued = False
        self.prev_props = self.props

        self.enqueue_update()

    def unmount(self):
        del self.parent
        del self.__tree

    def enqueue_update(self):
        if not self.__update_enqueued:
            self.__tree.enqueue_update_component(self)
            self.__update_enqueued = True

    def update_props_from(self, other: 'Component') -> bool:
        """Updates `props` of this component with props of another component.

        :param other:   the component to take props from
        :return:        `True` iff properties of this component have changed and it should be updated
        """
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
        try:
            cur = self.get_state(key)
            if cur == value:
                return
        except KeyError:
            pass  # ok, state isn't even initialized
        self.__state[key] = value
        self.enqueue_update()

    def del_state(self, key):
        if key in self.__state:
            del self.__state[key]
            self.enqueue_update()

    def mounted_children(self) -> Iterable['Component']:
        """Iterator over all mounted children of this component"""
        yield from ()

    def first_matching_descendants(self, predicate):
        """Iterator over all descendants of this component that match given predicate but don't have any other such
        components between them and this component.
        """
        for child in self.mounted_children():
            if predicate(child):
                yield child
            else:
                yield from child.first_matching_descendants(predicate)

    def ascendants(self):
        asc = self.parent
        tree = self.__tree

        while asc is not tree:
            yield asc
            asc = asc.parent

        yield asc

    def first_matching_ascendant(self, predicate):
        for asc in self.ascendants():
            if predicate(asc):
                return asc

        # TODO: Add custom exception
        raise Exception('No such ascendant')

    @property
    def tree(self):
        return self.__tree

    def class_id(self):
        return self.__class__

    def is_mounted(self):
        # TODO: Not the most reliable (?) way to check if a protected attribute exists.
        return hasattr(self, '_Component__tree')

    def assign_ref(self):
        ref = self.ref
        if ref:
            ref.current = self


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

    def __call__(self):
        """Creates a `Fragment` containing all components from this collection."""
        return Fragment(children=self)

    EMPTY: 'ComponentsCollection' = None


# TODO: Make immutable
ComponentsCollection.EMPTY = ComponentsCollection()


class ComponentRenderingContext:
    CONTEXT_ID = 'ComponentRenderingContext'

    def append(self, component: Component):
        raise NotImplementedError()

    def extend(self, components: Iterable[Component]):
        raise NotImplementedError()


class ComponentCollectionBuilder(ComponentRenderingContext):
    def __init__(self):
        self.__collection = ComponentsCollection()
        self.__incremental_key = Counter()

    def append(self, component):
        # assert isinstance(component, Component)
        self.__collection.append(self._assign_default_key(component))

    def extend(self, components):
        self.__collection.extend(map(self._assign_default_key, components))

    def _assign_default_key(self, component):
        if not component.key:
            prefix = component.class_id()
            self.__incremental_key[prefix] += 1
            component.key = (prefix, self.__incremental_key[prefix])

        return component

    def build(self):
        return self.__collection


class SingletonComponentRenderContext(ComponentRenderingContext):
    def __init__(self):
        self.__component = None

    def append(self, component: Component):
        if self.__component:
            raise Exception('Only one component is allowed in this context')

        self.__component = component

    def extend(self, components: Iterable[Component]):
        for component in components:
            self.append(component)

    def get_component(self) -> Component:
        if not self.__component:
            raise Exception('No components rendered')

        return self.__component


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
        return iter(self.components.values())

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
                    old_component.ref = new_component.ref
                    old_component.assign_ref()
                    new_components[key] = old_component
                    del old_components[key]
                    continue
                else:
                    old_component.unmount()
                    del old_components[key]

            new_component.mount(self.parent)
            new_component.assign_ref()

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
        if self.is_mounted():
            yield from self.__mounted_children

    @abstractmethod
    def render(self):
        raise NotImplementedError()

    def render_children(self) -> ComponentsCollection:
        # TODO: Not the best name?
        builder = ComponentCollectionBuilder()

        with render_context_manager(ComponentRenderingContext.CONTEXT_ID, builder):
            self.render()

        return builder.build()

    def update(self):
        self.__mounted_children.update(self.render_children())

        super().update()


class ParentComponent(Component):
    """
    A component that can be rendered with a single set of "children" components which are stored as "children" prop
    of type ComponentsCollection.
    """

    def __enter__(self):
        assert not hasattr(self, '_ParentComponent__restore_context')

        self.__restore_context = enter_render_context(ComponentRenderingContext.CONTEXT_ID,
                                                      ComponentCollectionBuilder())

    def __exit__(self, exc_type, exc_val, exc_tb):
        builder = self.__restore_context()
        del self.__restore_context
        self.props['children'] = builder.build()


class Fragment(DynamicComponent, ParentComponent):
    def render(self):
        pass

    def render_children(self) -> ComponentsCollection:
        return self.props.get('children', ComponentsCollection.EMPTY)

    def update_props_from(self, other: 'Component') -> bool:
        if other.props.get('children', None) != self.props.get('children', None):
            self.props = other.props
            return True

        return False

    def props_equal_to(self, other: 'Component') -> bool:
        return self.props.get('children', None) == other.props.get('children', None)
