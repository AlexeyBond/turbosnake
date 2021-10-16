import inspect
from collections import Iterable
from functools import update_wrapper
from typing import Optional, Union

from ._components import Component, ParentComponent, DynamicComponent, component_inserter
from ._hooks import ComponentWithHooks
from ._slotted_component import PropSlotsComponent


def functional_component(
        fn=None,
        /,
        # Should this component be able to have children (inheriting ParentComponent)?
        # When omitted or set to non-boolean value, is inferred from function signature (
        # ParentComponent is inherited iff there is an explicit `children` property).
        children: Optional[bool] = None,
        # True if hooks should be supported for this component
        hooks: bool = True,
        # Whenever the component should support slots.
        # When set to None (default) - slot support is inferred from function signature.
        # When set to False - slots are not supported even if function has slot_* parameters.
        # When set to True - slots are supported even if function does not have any slot_* parameters.
        # When is a list of strings - slots are supported but only listed slot names are allowed.
        # When is a dictionary - slots are supported. Keys of dictionary are names of slots and the values are custom
        # names of properties they are stored in.
        slots: Union[None, bool, Iterable[str], dict[str, str]] = None,
):
    # noinspection PyShadowingNames
    def _create_functional_component(fn: callable):
        bases = [DynamicComponent, Component]
        statics = {}

        fn_signature = inspect.signature(fn)

        if children is True or (children is not False and 'children' in fn_signature.parameters):
            bases.insert(0, ParentComponent)

        if hooks:
            bases.insert(0, ComponentWithHooks)

        slot_props = [it for it in fn_signature.parameters.keys() if it.startswith('slot_')]
        has_slot_props = len(slot_props) != 0

        if slots or (slots is not False and has_slot_props):
            bases.insert(0, PropSlotsComponent)

            if isinstance(slots, dict):
                statics['allowed_slots'] = set(slots.keys())
                statics['slot_to_prop_name'] = slots.__getitem__
            elif hasattr(slots, '__iter__'):  # TODO: Not the best way to check if object is iterable
                statics['allowed_slots'] = set(slots)
            elif has_slot_props and slots is None:
                statics['allowed_slots'] = set(map(PropSlotsComponent.default_prop_name_to_slot_name, slot_props))

        class FunctionComponent(*bases):
            def render(self):
                return fn(**self.props)

            # noinspection PyMethodMayBeStatic
            def class_id(self):
                return f'FunctionalComponent<{fn.__name__}>'

        for k, v in statics.items():
            setattr(FunctionComponent, k, v)

        return update_wrapper(component_inserter(FunctionComponent), fn)

    if fn:
        return _create_functional_component(fn)

    return _create_functional_component
