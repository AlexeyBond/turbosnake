from functools import partial
from inspect import signature, Parameter, isclass
from typing import Type, Callable, Union

from ._components import Component, component_inserter


def event_prop_invoker(self: Component, prop_name):
    """Creates a function that invokes event handler stored in given property of given component.

    Resulting function reads property on every invocation, so it remains valid after the property is changed.

    :param self: component instance
    :param prop_name: name of a property containing event handler
    :return: the function, as described above
    """

    def _event_prop_invoker(*args, **kwargs):
        return self.props[prop_name](*args, **kwargs)

    return _event_prop_invoker


def noop_handler(*_, **__):
    pass


def _component_inserter_declaration(component_class, fn: Callable):
    insert = component_inserter(component_class)
    sign = signature(fn)

    default_props = None

    for prop_name, prop_parameter in sign.parameters.items():
        if prop_parameter.default is not Parameter.empty:
            default_props = default_props or {}
            default_props[prop_name] = prop_parameter.default
        elif str(prop_parameter.annotation).startswith('typing.Optional'):
            default_props = default_props or {}
            default_props[prop_name] = None

    def _insert(**props):
        if default_props:
            props = default_props | props

        # Call fn to ensure that all required properties are present
        fn(**props)

        return insert(**props)

    return _insert


def component(component_class: Type[Component]):
    """Decorator that uses signature of decorated function to create a component inserter for given component type.

    Usage:

    @component(MyComponent)
    def my_component(*, prop1: int, prop2: Optional[str], prop3 = 'foo', **_):
        ...

    Purpose of this decorator is to (unlike plain call of component_inserter)

    - provide property name/type hints for IDE

    - provide default values for properties
    """
    return partial(_component_inserter_declaration, component_class)


def get_component_class(class_or_inserter: Union[Callable, Type[Component]]):
    """Returns component class for provided component inserter function.

    When component class is provided as first argument - returns it.
    """
    if isclass(class_or_inserter) and issubclass(class_or_inserter, Component):
        return class_or_inserter
    elif hasattr(class_or_inserter, '__wrapped__') and isclass(
            class_or_inserter.__wrapped__) and issubclass(class_or_inserter.__wrapped__,
                                                          Component):
        return class_or_inserter.__wrapped__
    else:
        raise Exception('Provided argument is not a component class or inserter')
