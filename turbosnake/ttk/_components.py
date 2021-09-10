import sys
import tkinter as tk
import tkinter.ttk as ttk
import traceback
from abc import abstractmethod, ABCMeta, ABC
from collections import Generator, Iterable
from typing import Optional

from turbosnake import Component, Tree, ParentComponent, DynamicComponent, ComponentsCollection


class TkBase(metaclass=ABCMeta):
    @property
    @abstractmethod
    def widget(self) -> tk.BaseWidget:
        ...

    @property
    @abstractmethod
    def tree(self):
        ...

    def on_tk_child_mounted(self, child):
        ...

    def on_tk_child_updated(self, child):
        ...

    def on_tk_child_unmounted(self, child):
        ...

    @abstractmethod
    def get_tk_children(self) -> Generator['TkComponent']:
        ...


class _PackContainerBase(TkBase, ABC):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__repack_enqueued = False

    @property
    @abstractmethod
    def layout_props(self):
        ...

    def pack_child(self, child: 'TkComponent'):
        p = self.layout_props
        cp = child.props
        child.widget.pack(
            side=cp.get('side', p.get('default_side', 'top')),
            padx=cp.get('px', 0),
            pady=cp.get('py', 0),
            expand=cp.get('expand', False),
            fill=cp.get('fill', None),
            anchor=cp.get('anchor', None)
        )

    def __repack_children(self):
        for child in self.get_tk_children():
            child.widget.pack_forget()
            self.pack_child(child)
        self.__repack_enqueued = False

    def schedule_repack(self):
        if not self.__repack_enqueued:
            self.__repack_enqueued = True
            self.tree.schedule_task(self.__repack_children)

    def on_tk_child_mounted(self, child):
        super().on_tk_child_mounted(child)
        self.schedule_repack()

    def on_tk_child_updated(self, child):
        super().on_tk_child_updated(child)
        self.schedule_repack()


def _get_tk_children(component: Component):
    for child in component.first_matching_descendants(TkComponent.__instancecheck__):
        if not child.tk_ignore_subtree:
            yield child


def configure_window(
        widget,
        title='turbosnake.ttk window',
        resizable=True,
        resizable_w=None,
        resizable_h=None,
        min_height=1,
        min_width=1,
        **_):
    widget.wm_title(title)

    resizable_tpl = (
        1 if (resizable if resizable_w is None else resizable_w) else 0,
        1 if (resizable if resizable_h is None else resizable_h) else 0
    )
    # Call of wm_resizable with arguments makes window blink, so don't do it when not necessary
    if resizable_tpl != widget.wm_resizable():
        widget.wm_resizable(*resizable_tpl)

    widget.wm_minsize(min_width, min_height)


class TkTree(Tree, _PackContainerBase, TkBase):
    def __init__(self, widget=None, **options):
        super().__init__()

        self.__widget = widget or tk.Tk()
        configure_window(self.__widget, **options)

    layout_props = {}

    def schedule_task(self, callback):
        self.__widget.after_idle(callback)

    @property
    def widget(self):
        return self.__widget

    def handle_update_error(self, error: Exception, component: Component):
        traceback.print_exc()
        # TODO: Do something smarter with exceptions...
        sys.exit(1)

    def get_tk_children(self):
        if isinstance(self.root, TkComponent):
            yield self.root
        else:
            yield from _get_tk_children(self.root)

    def main_loop(self):
        self.__widget.mainloop()


class TkComponent(Component, TkBase):
    tk_ignore_subtree: bool = False

    @property
    def widget(self) -> tk.Widget:
        return self.__widget

    def mount(self, parent):
        assert isinstance(parent.tree, TkTree), "TkComponent's can be mounted under TkTree only"
        super().mount(parent)

        tk_parent: TkBase = self.get_tk_parent()

        self.tk_parent = tk_parent
        # self.__layout_required = True
        self.__widget: Optional[tk.Widget] = None
        self._create_and_configure_widget()
        tk_parent.on_tk_child_mounted(self)

    def unmount(self):
        self.tk_parent.on_tk_child_unmounted(self)

        super().unmount()

        if self.__widget:
            self.__widget.destroy()

        del self.tk_parent
        del self.__widget

    def get_tk_parent(self) -> TkBase:
        return self.first_matching_ascendant(TkBase.__instancecheck__)

    def get_tk_children(self) -> Generator['TkComponent']:
        return _get_tk_children(self)

    def _create_and_configure_widget(self):
        if self.__widget:
            self.__widget.destroy()

        widget = self.create_widget(self.tk_parent.widget)
        self.configure_widget(widget)

        self.__widget = widget

    def configure_widget(self, widget):
        widget.config(**self.get_widget_config(**self.props))

    def update(self):
        super().update()

        self.configure_widget(self.__widget)

    @abstractmethod
    def create_widget(self, tk_parent: tk.BaseWidget) -> tk.BaseWidget:
        ...

    def get_widget_config(self, **props):
        return {}


def event_prop_invoker(self, prop_name):
    # TODO: Move to _components.py (?)
    """Creates a function that invokes event handler stored in given property of given component.

    Resulting function reads property on every invocation, so it remains valid after the property is changed.

    When property is missing or falsy, nothing happens on invocation of resulting function.

    :param self: component instance
    :param prop_name: name of a property containing event handler
    :return: the function, as described above
    """

    def _event_prop_invoker(*args, **kwargs):
        cb = self.props.get(prop_name, False)

        if not cb:
            return

        return cb(*args, **kwargs)

    return _event_prop_invoker


def tk_with_events(event_map: Iterable[str, str]):
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


class TkFlatContainer(TkComponent, ParentComponent, DynamicComponent, ABC):
    def render(self):
        pass  # not called

    def render_children(self) -> ComponentsCollection:
        return self.props.get('children', ComponentsCollection.EMPTY)


class TkPackedFrame(_PackContainerBase, TkFlatContainer):
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


class TkWindow(_PackContainerBase, TkFlatContainer, TkComponent):
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
