from collections import Iterable
from typing import Type, Optional, Any, Union, Callable

from turbosnake import Component
from turbosnake._utils import get_component_class


class Selector:
    def __init__(self, components: Iterable[Component]):
        self._components = components

    def __iter__(self):
        return iter(self._components)

    def only(self) -> Component:
        it = iter(self._components)
        try:
            value = next(it)
        except StopIteration:
            raise Exception('No components match the selector')

        try:
            next(it)
        except StopIteration:
            pass
        else:
            raise Exception(f'More than one ({len(self.all())}) components match the selector')

        return value

    def one(self) -> Component:
        try:
            return next(iter(self._components))
        except StopIteration:
            raise Exception('No components selected while at least one expected')

    def all(self) -> list[Component]:
        return list(self._components)

    def count(self) -> int:
        return len(self.all())

    @staticmethod
    def _construct_predicate(component: Union[None, Type[Component], Callable] = None,
                             props: Optional[dict[str, Any]] = None,
                             ):
        component_class = None
        if component:
            component_class = get_component_class(component)

        def predicate(c):
            if component_class:
                if not isinstance(c, component_class):
                    return False

            if props:
                component_props = c.props

                for k in props.keys():
                    if k not in component_props or component_props[k] != props[k]:
                        return False

            return True

        return predicate

    def descendants_matching(self, predicate) -> 'Selector':
        result: set[Component] = set()

        def traverse(component):
            for child in component.mounted_children():
                if predicate(child):
                    result.add(child)
                traverse(child)

        for c in self._components:
            traverse(c)

        return Selector(result)

    def descendants(self,
                    component: Union[None, Type[Component], Callable] = None,
                    props: Optional[dict[str, Any]] = None,
                    ) -> 'Selector':
        return self.descendants_matching(self._construct_predicate(component, props))

    def children_matching(self, predicate) -> 'Selector':
        return Selector([child for component in self for child in component.mounted_children() if predicate(child)])

    def children(self,
                 component: Union[None, Type[Component], Callable] = None,
                 props: Optional[dict[str, Any]] = None,
                 ) -> 'Selector':
        return self.children_matching(self._construct_predicate(component, props))

    def parents_matching(self, predicate) -> 'Selector':
        return Selector([
            component.parent for component in self if
            component.parent is not component.tree and predicate(component.parent)
        ])

    def parents(self,
                component: Union[None, Type[Component], Callable] = None,
                props: Optional[dict[str, Any]] = None,
                ) -> 'Selector':
        return self.parents_matching(self._construct_predicate(component, props))
