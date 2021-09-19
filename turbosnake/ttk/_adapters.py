import tkinter as tk
from tkinter import ttk

from turbosnake import Wrapper, Component, event_prop_invoker
from turbosnake.ttk._core import _PackContainerBase, TkComponent, configure_window

"""
_adapters.py

Contains turbosnake components that are adapters for tkinter/ttk widgets. 
"""


class TkWindow(_PackContainerBase, TkComponent, Wrapper):
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


class TkPackedFrame(_PackContainerBase, TkComponent, Wrapper):
    @property
    def layout_props(self):
        return self.props

    def create_widget(self, tk_parent: tk.BaseWidget) -> tk.BaseWidget:
        return ttk.Frame(tk_parent)

    def get_widget_config(self, **props):
        return super().get_widget_config(**props)

    def update(self):
        super().update()

        # TODO: Repack iff own layout props changed
        self.schedule_repack()


class TkButton(TkComponent):
    def create_widget(self, tk_parent):
        return ttk.Button(
            tk_parent,
            command=event_prop_invoker(self, 'on_click')
        )

    def get_widget_config(self, text='', disabled=False, **props):
        cfg = super().get_widget_config(**props)

        cfg['text'] = text
        cfg['state'] = 'disabled' if disabled else 'normal'

        return cfg


class TkLabel(TkComponent):
    def create_widget(self, tk_parent: tk.BaseWidget) -> tk.BaseWidget:
        return ttk.Label(tk_parent)

    def get_widget_config(self, text='', **props):
        cfg = super().get_widget_config(**props)

        cfg['text'] = text

        return cfg


class TkEntry(TkComponent):
    def create_widget(self, tk_parent: tk.BaseWidget) -> tk.BaseWidget:
        widget = ttk.Entry(tk_parent)
        widget.insert(0, self.props.get('initial_value', ''))
        return widget

    @property
    def text(self):
        return self.widget.get()

    @text.setter
    def text(self, value):
        w: ttk.Entry = self.widget
        w.delete(0, len(w.get()))
        w.insert(0, value)


class TkScrollbar(TkComponent):
    def create_widget(self, tk_parent: tk.BaseWidget) -> tk.BaseWidget:
        scrollbar = ttk.Scrollbar(tk_parent)

        scrollbar.configure(
            command=event_prop_invoker(self, 'on_scroll')
        )

        return scrollbar

    def get_widget_config(self, orientation='vertical', **props):
        conf = super().get_widget_config(**props)

        conf['orient'] = orientation

        return conf


class TkCanvas(_PackContainerBase, TkComponent, Wrapper):
    @property
    def layout_props(self):
        return self.props

    def create_widget(self, tk_parent: tk.BaseWidget) -> tk.BaseWidget:
        return tk.Canvas(tk_parent)

    def get_widget_config(self, border_width=0, highlight_thickness=0, **props):
        cfg = super().get_widget_config(**props)

        cfg['borderwidth'] = border_width
        cfg['highlightthickness'] = highlight_thickness

        return cfg


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
