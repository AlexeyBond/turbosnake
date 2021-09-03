import inspect
from typing import Optional

from components import Component, ParentComponent, DynamicComponent
from hooks import ComponentWithHooks


def functional_component(
        fn=None,
        /,
        # Should this component be able to have children (inheriting ParentComponent)?
        # When omitted or set to non-boolean value, is inferred from function signature (
        # ParentComponent is inherited iff there is an explicit `children` property).
        children: Optional[bool] = None,
        # True if hooks should be supported for this component
        hooks: bool = True,
):
    # noinspection PyShadowingNames
    def _create_functional_component(fn: callable):
        bases = [DynamicComponent, Component]

        fn_signature = inspect.signature(fn)

        if children is True or (children is not False and 'children' in fn_signature.parameters):
            bases.insert(0, ParentComponent)

        if hooks:
            bases.insert(0, ComponentWithHooks)

        class FunctionComponent(*bases):
            def render(self):
                return fn(**self.props)

            # noinspection PyMethodMayBeStatic
            def class_id(self):
                return f'FunctionalComponent<{fn.__name__}>'

        return FunctionComponent

    if fn:
        return _create_functional_component(fn)

    return _create_functional_component
