from abc import ABCMeta, abstractmethod, ABC

from components import Component, DynamicComponent, ComponentsCollection
from render_context import enter_render_context, get_render_context


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
        self.__component = component
        self.__hooks = hooks

    def start(self):
        self.__iterator = iter(self.__hooks)

    def process_hook(self, hook_class, *args, **kwargs):
        try:
            hook = next(self.__iterator)
        except StopIteration:
            raise Exception(f'Wrong number of hooks rendered in {self.__component.class_id()}.\
                            At least one more {hook_class} is going to be rendered.')

        if hook.__class__ is not hook_class:
            raise Exception(f'Broken hook order. Hook {hook_class} rendered instead of {hook.__class__}.')

        return hook.next_call(*args, **kwargs)

    def finish(self) -> 'ComponentHookProcessor':
        try:
            h = next(self.__iterator)

            raise Exception(f'Wrong number of hooks rendered in {self.__component.class_id()}.\
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
        self.__component = component

    def start(self):
        self.__hooks = []

    def process_hook(self, hook_class, *args, **kwargs):
        hook = hook_class(self.__component)
        self.__hooks.append(hook)

        return hook.first_call(*args, **kwargs)

    def finish(self) -> 'ComponentHookProcessor':
        return _NextHookProcessor(self.__component, self.__hooks)

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
