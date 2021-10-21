from abc import ABCMeta
from typing import Callable, Optional

from ._components import Component, Wrapper, ComponentNotFoundError
from ._hooks import Hook, ComponentHookProcessor
from ._utils import component


class ContextProvider(Wrapper, Component, metaclass=ABCMeta):
    def __init__(self, /, **props):
        super().__init__(**props)

        self.context_id = props['context_id']

    def mount(self, parent):
        super().mount(parent)
        self.__observers = []

    def unmount(self):
        super().unmount()
        del self.__observers

    def register_observer(self, observer: Callable):
        self.__observers.append(observer)

    def unregister_observer(self, observer: Callable):
        self.__observers.remove(observer)

    def __notify_observers(self, value):
        for observer in self.__observers:
            observer(value)

    def update_props_from(self, other: 'Component') -> bool:
        old_props = self.props
        new_props = other.props

        assert 'context_id' in new_props
        assert new_props['context_id'] == self.context_id

        self.props = new_props

        new_value = new_props['value']

        if new_value != old_props['value']:
            self.__notify_observers(new_value)

        return old_props.get('children', None) != new_props.get('children', None)

    @property
    def value(self):
        return self.props.get('value', None)


@component(ContextProvider)
def context_provider(context_id, value, **_):
    ...


class ContextNotProvidedError(Exception):
    def __init__(self, context_id):
        super().__init__(f'Context {context_id} is not provided.')


def get_context_provider(component: Component, context_id) -> ContextProvider:
    try:
        return component.first_matching_ascendant(
            lambda it: isinstance(it, ContextProvider) and it.context_id == context_id
        )
    except ComponentNotFoundError:
        raise ContextNotProvidedError(context_id)


class _ContextHook(Hook):
    def __init__(self, component):
        super().__init__(component)
        self.component = component
        self.context_id = None
        self.provider: Optional[ContextProvider] = None

    def first_call(self, context_id):
        self.context_id = context_id
        provider = get_context_provider(self.component, context_id)
        self.provider = provider
        provider.register_observer(self)
        return provider.value

    def _unsubscribe(self):
        self.provider.unregister_observer(self)
        self.provider = None
        self.context_id = None

    def next_call(self, context_id):
        if self.context_id != context_id:
            self._unsubscribe()
            return self.first_call(context_id)

        return self.provider.value

    def on_unmount(self):
        if self.provider:
            self._unsubscribe()

    def __call__(self, value):
        self.component.enqueue_update()


def use_context(context_or_id):
    context_id = context_or_id

    if isinstance(context_or_id, Context):
        context_id = context_or_id.id

    return ComponentHookProcessor.current().process_hook(_ContextHook, context_id)


class Context:
    def __init__(self, context_id=None):
        self.id = context_id or self

    def provider(self, /, value, **props):
        return context_provider(context_id=self.id, value=value, **props)
