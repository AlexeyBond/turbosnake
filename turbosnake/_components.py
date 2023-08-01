import asyncio
import queue
from abc import abstractmethod, ABCMeta
from collections import OrderedDict, Counter
from functools import wraps
from typing import Optional, Type, Union, Callable, Iterable

from ._render_context import get_render_context, render_context_manager, enter_render_context
from ._utils0 import have_differences_by_keys


class Ref:
    def __init__(self):
        self.current = None


class Tree(metaclass=ABCMeta):
    """Root node of a turbosnake tree.

    See ../doc/Tree.md for more details.
    """
    TASK_QUEUES = ('update', 'effect')

    def __init__(self, queues=TASK_QUEUES):
        super().__init__()
        self.__queue_names = queues
        self.__queues = {}
        for queue_name in queues:
            self.__queues[queue_name] = queue.SimpleQueue()

        self.__task_processing_scheduled = False
        self.__root: Optional[Component] = None

    def enqueue_task(self, queue_name, task):
        """Enqueue task for execution on given queue."""
        assert queue_name in self.__queue_names, 'Wrong queue name'

        self.__queues[queue_name].put(task)

        if not self.__task_processing_scheduled:
            self.schedule_task(self.__run_tasks)
            self.__task_processing_scheduled = True

    def __run_from_queue(self, queue_name):
        q = self.__queues[queue_name]

        try:
            task = q.get_nowait()
        except queue.Empty:
            return False

        while True:
            try:
                task()
            except Exception as e:
                self.handle_error(e, queue_name, task)

            try:
                task = q.get_nowait()
            except queue.Empty:
                return True

    def __run_tasks(self):
        self.__task_processing_scheduled = False

        for queue_name in self.__queue_names:
            if self.__run_from_queue(queue_name):
                self.schedule_task(self.__run_tasks)
                self.__task_processing_scheduled = True
                return

    @abstractmethod
    def schedule_task(self, callback: Callable):
        """Schedule task for immediate execution on event loop.

        This method must be implemented by Tree subclasses as it is used by task management system.

        However, it usually shouldn't be used directly by anything else than base Tree implementation.
        If you're using it, consider using `enqueue_task` instead.
        """
        ...

    @abstractmethod
    def schedule_delayed_task(self, delay: Union[int, float], callback: Callable) -> Callable:
        """Schedule task for delayed execution.

        :param delay: delay in milliseconds from now
        :param callback: the callback to execute
        :returns: callable that cancels task execution when called
        """
        ...

    @property
    @abstractmethod
    def event_loop(self) -> asyncio.AbstractEventLoop:
        """The default event loop used to execute asynchronous operations in components of this tree.

        Component updates may use the same event loop or run on different thread - in a different event loop or
        even without using a standard event loop (so does tkinter tree work - tkinter event loop cannot be integrated
        with asyncio event loop).
        Whenever event loop returned here runs on the same thread as component updates or does it use a different thread
        depends on tree implementation.
        So users should not rely on any assumptions on this matter, unless they are sure that application code is going
        to use a very specific tree implementation.

        Note: It is not guaranteed that event loop returned here will keep running after the tree is terminated.
        """
        ...

    def handle_error(self, error, queue_name, task):
        """Called when an error is raised in any of tasks executed as result of `enqueue_task` call."""
        raise error

    @property
    def tree(self) -> 'Tree':
        return self

    @property
    def root(self) -> 'Component':
        """Root component of this tree.

        May be `None` if a tree root is not initialized or error happen during root replacement.
        """
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
        new_root.assign_ref()
        self.__root = new_root


class ComponentNotFoundError(Exception):
    pass


class Component:
    def __init__(self, /, key=None, ref: Optional[Ref] = None, **props):
        self.props = props
        self.key = key
        self.ref = ref

    def insert(self, context: 'ComponentRenderingContext' = None):
        """Inserts this component into current rendering context."""
        assert not self.is_mounted(), 'Attempt to render a mounted component'

        if not context:
            context = get_render_context(ComponentRenderingContext.CONTEXT_ID)

            assert context, 'Attempt to render component outside of a rendering context'

        context.append(self)

    def mount(self, parent):
        """Called when this component is being mounted to a tree.

        :param parent: parent of this component
        """
        assert not self.is_mounted(), 'Attempt to mount a mounted component'

        self.parent: Component = parent
        self.__tree: Tree = parent.tree
        self.__state = {}
        self.__update_enqueued = False
        self.prev_props = self.props

        self.enqueue_update()

    def unmount(self):
        """Called when this component is being unmounted from tree."""
        del self.parent
        del self.__tree

    def enqueue_update(self):
        if not self.__update_enqueued:
            self.__tree.enqueue_task('update', self.update)
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
        """Returns `True` iff props of this component are equal to props of another one.

        This method may ignore some properties that are not used by this component.
        """
        return other.props == self.props

    def update(self):
        self.__update_enqueued = False
        self.prev_props = self.props

    def get_state(self, key):
        """Get state element.

        :raises KeyError: if such element is not present in component's state
        """
        return self.__state[key]

    def get_state_or_init(self, key, default):
        """Get state element or set to given default value if not present

        Doesn't request update when sets state to default value.
        """
        try:
            return self.__state[key]
        except KeyError:
            self.__state[key] = default
            return default

    def set_state(self, key, value):
        """Set state element and request update if new value is different from previous one."""
        try:
            cur = self.get_state(key)
        except KeyError:
            pass  # ok, state isn't even initialized
        else:
            if cur == value:
                return
        self.__state[key] = value
        self.enqueue_update()

    def del_state(self, key):
        if key in self.__state:
            del self.__state[key]
            self.enqueue_update()

    def mounted_children(self) -> Iterable['Component']:
        """Iterator over all mounted children of this component"""
        yield from ()

    def first_matching_descendants(self, predicate) -> Iterable['Component']:
        """Iterator over all descendants of this component that match given predicate but don't have any other such
        components between them and this component.
        """
        for child in self.mounted_children():
            if predicate(child):
                yield child
            else:
                yield from child.first_matching_descendants(predicate)

    def ascendants(self) -> Iterable['Component']:
        """Iterator over all ascendants of this component"""
        asc = self.parent
        tree = self.__tree

        while asc is not tree:
            yield asc
            asc = asc.parent

        yield asc

    def first_matching_ascendant(self, predicate) -> 'Component':
        """Returns closest ascendant of this component that matches given predicate.

        :raises ComponentNotFoundError: when there is no such ascendant
        """
        for asc in self.ascendants():
            if predicate(asc):
                return asc

        raise ComponentNotFoundError()

    @property
    def tree(self) -> Tree:
        """The Tree this component is mounted to"""
        return self.__tree

    def class_id(self):
        return self.__class__

    def is_mounted(self):
        """Returns `True` iff this component is mounted to a tree"""
        # TODO: Not the most reliable (?) way to check if a protected attribute exists.
        return hasattr(self, '_Component__tree')

    def assign_ref(self):
        ref = self.ref
        if ref:
            ref.current = self

    def has_props_changed(self, prop_names: Iterable[str]) -> bool:
        """Returns True iff value of any of properties listed in `prop_names` was changed during the most recent update.
        """
        return have_differences_by_keys(self.prev_props, self.props, prop_names)


class ComponentsCollection(metaclass=ABCMeta):
    """Base class for collection of components.

    Instances of this class are usually passed as `children` or slot properties to components.

    The main difference between plain list/tuple and ComponentsCollection is specialized equality operator that compares
    component properties properly.
    But also it provides a `()` operator that inserts all components from collection into current rendering context.
    """

    # noinspection PyTypeChecker
    def __eq__(self, other):
        if not other or not isinstance(other, ComponentsCollection):
            return False

        if len(self) != len(other):
            return False

        i2 = iter(other)

        for component in self:
            other_component = next(i2)
            if component.key != other_component.key:
                return False
            if component.ref is not other_component.ref:
                return False
            if not component.props_equal_to(other_component):
                return False

        return True

    def __call__(self, /, key=None):
        """Creates and inserts a `Fragment` containing all components from this collection."""
        return fragment(children=self, key=key)

    EMPTY: 'ComponentsCollection' = None


class MutableComponentsCollection(ComponentsCollection, list[Component]):
    ...


class ImmutableComponentsCollection(ComponentsCollection, tuple[Component, ...]):
    ...


ComponentsCollection.EMPTY = ImmutableComponentsCollection()


class ComponentRenderingContext:
    CONTEXT_ID = 'ComponentRenderingContext'

    def append(self, component: Component):
        raise NotImplementedError()

    def extend(self, components: Iterable[Component]):
        raise NotImplementedError()


class ComponentCollectionBuilder(ComponentRenderingContext):
    def __init__(self):
        self.__collection = MutableComponentsCollection()
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
        ...

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


class Wrapper(DynamicComponent, ParentComponent):
    """A component that can be rendered with a single set of children and mounts those children as it's children.
    """

    def render(self):
        pass

    def render_children(self) -> ComponentsCollection:
        return self.props.get('children', ComponentsCollection.EMPTY)


def component_inserter(component_class: Type[Component]):
    @wraps(component_class)
    def _component_inserter(**props):
        component: Component = component_class(**props)
        component.insert()
        return component

    return _component_inserter


class Fragment(Wrapper):
    def update_props_from(self, other: 'Component') -> bool:
        need_update = other.props.get('children', None) != self.props.get('children', None)
        self.props = other.props

        return need_update

    def props_equal_to(self, other: 'Component') -> bool:
        return self.props.get('children', None) == other.props.get('children', None)


fragment = component_inserter(Fragment)
