from abc import ABCMeta, abstractmethod, ABC

from ._components import Component, DynamicComponent, ComponentsCollection, Ref
from ._render_context import enter_render_context, get_render_context


class Hook(metaclass=ABCMeta):
    def __init__(self, component):
        pass

    @abstractmethod
    def first_call(self, *args, **kwargs):
        ...

    @abstractmethod
    def next_call(self, *args, **kwargs):
        ...

    def on_unmount(self):
        pass


class ComponentHookProcessor(metaclass=ABCMeta):
    CONTEXT_ID = 'ComponentHookProcessor'

    def __init__(self, component):
        self.__component = component

    @property
    def component(self):
        return self.__component

    @classmethod
    def current(cls) -> 'ComponentHookProcessor':
        ctx = get_render_context(cls.CONTEXT_ID)

        assert ctx, 'Hook rendered outside appropriate context'

        return ctx

    @abstractmethod
    def process_hook(self, hook_class, *args, **kwargs):
        ...

    @abstractmethod
    def start(self):
        ...

    @abstractmethod
    def finish(self) -> 'ComponentHookProcessor':
        ...

    @abstractmethod
    def on_unmount(self):
        ...


class _NextHookProcessor(ComponentHookProcessor):
    def __init__(self, component: Component, hooks):
        super().__init__(component)
        self.__hooks = hooks

    def start(self):
        self.__iterator = iter(self.__hooks)

    def process_hook(self, hook_class, *args, **kwargs):
        try:
            hook = next(self.__iterator)
        except StopIteration:
            raise Exception(f'Wrong number of hooks rendered in {self.component.class_id()}.\
                            At least one more {hook_class} is going to be rendered.')

        if hook.__class__ is not hook_class:
            raise Exception(f'Broken hook order. Hook {hook_class} rendered instead of {hook.__class__}.')

        return hook.next_call(*args, **kwargs)

    def finish(self) -> 'ComponentHookProcessor':
        try:
            h = next(self.__iterator)

            raise Exception(f'Wrong number of hooks rendered in {self.component.class_id()}.\
                            At least one more {h.__class__} hook expected.')
        except StopIteration:
            pass  # ok!

        del self.__iterator

        return self

    def on_unmount(self):
        for hook in self.__hooks:
            hook.on_unmount()


class InitialHookProcessor(ComponentHookProcessor):
    def __init__(self, component):
        super().__init__(component)

    def start(self):
        self.__hooks = []

    def process_hook(self, hook_class, *args, **kwargs):
        hook = hook_class(self.component)
        self.__hooks.append(hook)

        return hook.first_call(*args, **kwargs)

    def finish(self) -> 'ComponentHookProcessor':
        return _NextHookProcessor(self.component, self.__hooks)

    def on_unmount(self):
        pass


class ComponentWithHooks(DynamicComponent, ABC):
    def mount(self, parent):
        super().mount(parent)

        self.__hook_processor: ComponentHookProcessor = InitialHookProcessor(self)

    def unmount(self):
        super().unmount()

        self.__hook_processor.on_unmount()

    def render_children(self) -> ComponentsCollection:
        hp = self.__hook_processor
        hp.start()
        revert = enter_render_context(ComponentHookProcessor.CONTEXT_ID, hp)
        try:
            result = super().render_children()
        finally:
            revert()

        self.__hook_processor = hp.finish()

        return result


class _StateHook(Hook):
    def __init__(self, component: Component):
        super().__init__(component)
        self.__component = component

    def set_state(self, value):
        self.__component.set_state(self, value)

    def first_call(self, default):
        self.__component.set_state(self, default)
        return default, self.set_state

    def next_call(self, *_):
        return self.__component.get_state(self), self.set_state


def use_state(default=None):
    return ComponentHookProcessor.current().process_hook(
        _StateHook,
        default
    )


class _ToggleHook(Hook):
    def __init__(self, component: Component):
        super().__init__(component)
        self.__component = component

    def toggle(self):
        self.__component.set_state(
            self,
            not self.__component.get_state(self)
        )

    def first_call(self, initial):
        self.__component.set_state(self, initial)
        return initial, self.toggle

    def next_call(self, *_):
        return self.__component.get_state(self), self.toggle


def use_toggle(initial: bool = False):
    return ComponentHookProcessor.current().process_hook(
        _ToggleHook,
        initial
    )


class _PreviousHook(Hook):
    def __init__(self, component):
        super().__init__(component)
        self.__component = component

    def first_call(self, value, initial):
        self.__value = value
        return initial

    def next_call(self, value, *_):
        prev = self.__value
        self.__value = value
        return prev


def use_previous(value, initial=None):
    return ComponentHookProcessor.current().process_hook(
        _PreviousHook,
        value,
        initial
    )


_sentinel = object()


def use_function_hook(hook_class, arg_1=_sentinel, *args, **kwargs):
    """Generic method for hooks that accept a function as one of arguments.

    Resulting hook can be used as a plain function or as a decorator:

    def use_my_hook(*args):
        return use_function_hook(HookCls, *args)

    ...
    # The following two are equivalent:

    use_my_hook(lambda x: ..., y, z)

    # WARNING: the first argument here MUST NOT be a callable!
    @use_my_hook(y, z)
    def fn(x):
        ...

    # For cases without arguments

    @use_my_hook
    def fn0(x):
        ...
    """
    ctx = ComponentHookProcessor.current()

    if callable(arg_1):
        return ctx.process_hook(hook_class, arg_1, *args, **kwargs)

    def use_function_hook_decorator(fn):
        assert callable(fn)

        return ctx.process_hook(hook_class, fn, *(() if arg_1 is _sentinel else (arg_1,)), *args, **kwargs)

    return use_function_hook_decorator


class _MemoHook(Hook):
    def first_call(self, fn, *dependencies):
        self.__dependencies = dependencies
        value = fn()
        self.__value = value
        return value

    def next_call(self, fn, *dependencies):
        if self.__dependencies == dependencies:
            return self.__value
        return self.first_call(fn, *dependencies)


def use_memo(*args):
    """Calls a function, memoizes last result and returns it on next calls as long as dependencies have not changed.

    val = use_memo(lambda: ..., x, y)

    # WARNING: first dependency MUST NOT be a callable
    @use_memo(x, y)
    def val():
        ...

    # Calls function once, always returns result of the first call
    @use_memo
    def val():
        ...

    :param args:
    :return:
    """
    return use_function_hook(_MemoHook, *args)


class _CallbackHook(Hook):
    def first_call(self, fn, *dependencies):
        self.__fn = fn
        self.__dependencies = dependencies
        return fn

    def next_call(self, fn, *dependencies):
        if self.__dependencies == dependencies:
            return self.__fn
        return self.first_call(fn, dependencies)


def use_callback(*args):
    """Hook that returns the same callable instance on consequent renders as long as it's dependencies do not change.

    This helps to avoid extra re-renders of nested components when a callback is passed to them as property.

    cb = use_callback(lambda x: ..., dep1, dep2)


    @use_callback
    def cb2(x):
        ...

    # WARNING: First dependency MUST NOT be a callable!
    @use_callback(dep,dep1)
    def cb3(x):
        ...
    """
    return use_function_hook(_CallbackHook, *args)


class _CallbackProxyHook(Hook):
    def first_call(self, callback):
        self.__callback = callback
        return self

    def next_call(self, callback):
        self.__callback = callback
        return self

    def __call__(self, *args, **kwargs):
        return self.__callback(*args, **kwargs)


def use_callback_proxy(callback):
    """Hook that returns the same callable redirecting calls to callback passed on last render.

    Unlike use_callback doesn't accept any dependencies 'cause doesn't need them.

    cb1 = use_callback_proxy(lambda ...: ...)

    @use_callback_proxy
    def cb2(...):
        ...
    """
    return ComponentHookProcessor.current().process_hook(_CallbackProxyHook, callback)


def use_self():
    """Pseudo-hook that returns reference to currently rendered component."""
    return ComponentHookProcessor.current().component


class _EffectHook(Hook):
    def __init__(self, component: Component):
        super().__init__(component)
        self.__component = component
        self.__next_effect = None
        self.__revert_previous = None

    def __do_revert_previous(self):
        revert = self.__revert_previous
        self.__revert_previous = None

        if callable(revert):
            revert()

    def __execute_effect(self):
        if not self.__next_effect:
            return
        self.__do_revert_previous()
        self.__revert_previous = self.__next_effect()
        self.__next_effect = None

    def __enqueue_effect(self, effect):
        if not self.__next_effect:
            self.__component.tree.schedule_task(self.__execute_effect)
        self.__next_effect = effect

    def first_call(self, effect, *dependencies):
        self.__dependencies = dependencies
        self.__enqueue_effect(effect)

    def next_call(self, effect, *dependencies):
        if self.__dependencies == dependencies:
            return

        self.__dependencies = dependencies
        self.__enqueue_effect(effect)

    def on_unmount(self):
        self.__component.tree.schedule_task(self.__revert_previous)


def use_effect(*args):
    """Executes a side-effect.

    # Executes a lambda when any of dependencies changes since last render:
    use_effect(lambda: ..., dep1, dep2)

    # Or function:
    # WARNING: First dependency MUST NOT be a callable!
    @use_effect(dep1, dep2)
    def do_something():
        ...

    # Executes a lambda once after first render
    use_effect(lambda: ...)

    # Or function:
    @use_effect
    def do_something():
        ...

    # Function may return another function that will be called before the effect is executed next time or after the
    # component gets unmounted:
    @use_effect
    def foo():
        def bar():
            ...  # will be called after the component is unmounted
        return bar

    Note: effect functions and effect revert functions are not called immediately but are scheduled on tree's event loop
    """
    return use_function_hook(_EffectHook, *args)


class _RefHook(Hook, Ref):
    def first_call(self):
        return self

    def next_call(self):
        return self


def use_ref() -> Ref:
    """Returns the same unique `Ref` instance on every render."""
    return ComponentHookProcessor.current().process_hook(_RefHook)
