import tkinter as tk
from typing import Mapping

from turbosnake import event_prop_invoker
from ._core import TkComponent, TkTree


def tk_app(widget=None, **options):
    """Shortcut function that creates TkTree, renders it's content and starts main loop.

    Usage:

    if __name__ == '__main__':
        with tk_app():
            root(...)
    """
    tree = TkTree(widget, **options)

    class _App:
        def __enter__(self):
            return tree.__enter__()

        def __exit__(self, exc_type, exc_val, exc_tb):
            tree.__exit__(exc_type, exc_val, exc_tb)

            tree.main_loop()

    return _App()


def tk_with_events(event_map: Mapping[str, str]):
    """Decorator for tk-component that invokes event handlers from it's props when tk's events happen.

    @tk_with_events({
        '<<Button-1>>': 'on_mouse_down',
    })
    class MyComponent(TkComponent):
        ...

    :param event_map iterable of pairs (event sequence - handler property name)
    """

    def _tk_component_with_events(component):
        original_create_widget = component.create_widget

        assert issubclass(component, TkComponent)

        def create_widget(self, *args, **kwargs):
            widget: tk.Widget = original_create_widget(self, *args, **kwargs)

            for (event_sequence, prop_name) in event_map:
                widget.bind(event_sequence, event_prop_invoker(self, prop_name))

            return widget

        component.create_widget = create_widget

        return component

    return _tk_component_with_events
