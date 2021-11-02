import tkinter as tk
from abc import ABC
from tkinter import ttk
from typing import Callable, Optional, Literal

from turbosnake import Wrapper, Component, event_prop_invoker, component, noop_handler
from turbosnake.ttk._core import TkContainerBase, TkComponent, configure_window
from turbosnake.ttk._layout import LayoutManagerPropValue

"""
_adapters.py

Contains turbosnake components that are adapters for tkinter/ttk widgets. 
"""


class TkContainerComponent(TkContainerBase, TkComponent, ABC):
    def update(self):
        super().update()
        self.update_container_settings(**self.props)

    def mount(self, parent):
        super().mount(parent)
        self.init_container(**self.props)

    def unmount(self):
        super().unmount()
        self.destroy_container()


class TkWindow(TkContainerComponent, TkComponent, Wrapper):
    @property
    def layout_props(self):
        return self.props

    tk_ignore_subtree = True

    def _on_close(self):
        try:
            event_handler = self.props['on_close']
        except KeyError:
            self.widget.destroy()
            return

        event_handler()

    def create_widget(self, tk_parent: tk.BaseWidget) -> tk.BaseWidget:
        widget = tk.Toplevel(master=tk_parent)

        widget.protocol("WM_DELETE_WINDOW", self._on_close)

        return widget

    def configure_widget(self, widget: tk.Toplevel):
        super().configure_widget(widget)
        configure_window(widget, **self.props)

    def get_window(self):
        return self


@component(TkWindow)
def tk_window(
        *,
        title: str,
        resizable: bool = True,
        on_close: Callable = noop_handler,
        resizable_w: Optional[int] = None,
        resizable_h: Optional[int] = None,
        min_height: int = 1,
        min_width: int = 1,
        layout_manager: LayoutManagerPropValue = 'pack',
        **_):
    ...


class TkFrame(TkContainerComponent, TkComponent, Wrapper):
    def create_widget(self, tk_parent: tk.BaseWidget) -> tk.BaseWidget:
        return ttk.Frame(tk_parent)

    def get_widget_config(self, **props):
        return super().get_widget_config(**props)


@component(TkFrame)
def tk_frame(
        *,
        layout_manager: LayoutManagerPropValue = 'pack',
        **_):
    ...


@component(TkFrame)
def tk_packed_frame(
        *,
        layout_manager: Literal['pack'] = 'pack',
        default_side: Literal['top', 'bottom', 'left', 'right'] = 'top',
        **_):
    ...


@component(TkFrame)
def tk_place_frame(
        *,
        layout_manager: Literal['place'] = 'place',
        default_anchor='NW',
        **_):
    ...


@component(TkFrame)
def tk_grid_frame(
        *,
        layout_manager: Literal['grid'] = 'grid',
        row_weights: tuple[int, ...] = (),
        row_min_sizes: tuple[int, ...] = (),
        row_pads: tuple[int, ...] = (),
        column_weights: tuple[int, ...] = (),
        column_min_sizes: tuple[int, ...] = (),
        column_pads: tuple[int, ...] = (),
        **_):
    ...


class TkButton(TkComponent):
    def create_widget(self, tk_parent):
        return ttk.Button(
            tk_parent,
            command=event_prop_invoker(self, 'on_click')
        )

    def get_widget_config(self, text, disabled, **props):
        cfg = super().get_widget_config(**props)

        cfg['text'] = text
        cfg['state'] = 'disabled' if disabled else 'normal'

        return cfg


@component(TkButton)
def tk_button(
        *,
        on_click: Callable = noop_handler,
        text: str = '',
        disabled: bool = False,
        **_):
    ...


class TkLabel(TkComponent):
    def create_widget(self, tk_parent: tk.BaseWidget) -> tk.BaseWidget:
        return ttk.Label(tk_parent)

    def get_widget_config(self, text, **props):
        cfg = super().get_widget_config(**props)

        cfg['text'] = text

        return cfg


@component(TkLabel)
def tk_label(
        *,
        text: str = '',
        **_):
    ...


class TkEntry(TkComponent):
    def create_widget(self, tk_parent: tk.BaseWidget) -> tk.BaseWidget:
        widget = ttk.Entry(tk_parent)
        widget.insert(0, self.props['initial_value'])
        return widget

    @property
    def text(self):
        return self.widget.get()

    @text.setter
    def text(self, value):
        w: ttk.Entry = self.widget
        w.delete(0, len(w.get()))
        w.insert(0, value)


@component(TkEntry)
def tk_entry(
        *,
        initial_value: str = '',
        **_):
    ...


class TkScrollbar(TkComponent):
    def create_widget(self, tk_parent: tk.BaseWidget) -> tk.BaseWidget:
        scrollbar = ttk.Scrollbar(tk_parent)

        scrollbar.configure(
            command=event_prop_invoker(self, 'on_scroll')
        )

        return scrollbar

    def get_widget_config(self, orientation, **props):
        conf = super().get_widget_config(**props)

        conf['orient'] = orientation

        return conf


@component(TkScrollbar)
def tk_scrollbar(
        *,
        on_scroll: Callable = noop_handler,
        orientation: Literal['vertical', 'horizontal'] = 'vertical',
        **_):
    ...


class TkCanvas(TkContainerComponent, TkComponent, Wrapper):
    @property
    def layout_props(self):
        return self.props

    def create_widget(self, tk_parent: tk.BaseWidget) -> tk.BaseWidget:
        return tk.Canvas(tk_parent)

    def get_widget_config(self, border_width, highlight_thickness, **props):
        cfg = super().get_widget_config(**props)

        cfg['borderwidth'] = border_width
        cfg['highlightthickness'] = highlight_thickness

        return cfg


@component(TkCanvas)
def tk_canvas(
        *,
        border_width: int = 0,
        highlight_thickness: int = 0,
        **_):
    ...


class TkRadioGroup(Wrapper, Component):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.on_selected = event_prop_invoker(self, 'on_selected')

    @staticmethod
    def get_for(component: Component, name) -> 'TkRadioGroup':
        def predicate(c):
            return isinstance(c, TkRadioGroup) and c.name == name

        return component.first_matching_ascendant(predicate)

    @property
    def name(self):
        return self.props.get('name', None)

    def mount(self, parent):
        super().mount(parent)

        self.variable = tk.Variable(
            value=self.props.get('initial_value', None)
        )

    def unmount(self):
        super().unmount()

        del self.variable

    def update_props_from(self, other: 'Component') -> bool:
        assert self.props.get('name', None) == other.props.get('name', None), \
            f"""Radio group name must not be changed but was changed from {
            self.props.get('name', None)} to {other.props.get('name', None)}"""

        return super().update_props_from(other)


@component(TkRadioGroup)
def tk_radio_group(
        *,
        on_selected: Callable = noop_handler,
        name: Optional[str] = None,
        initial_value=None,
        **_):
    ...
