import tkinter as tk
from abc import abstractmethod, ABCMeta, ABC
from typing import Optional, Callable, Any, Iterable

from ._adapters import TkRadioGroup
from ._core import TkComponent
from .. import Component, Wrapper, event_prop_invoker, component, noop_handler

"""
_menu.py

Contains turbosnake adapters for tkinter's menu functionality.

Unlike normal widgets, menu items cannot be created and managed as separate objects, instead they should be created
using corresponding methods of containing menu.
That causes a difference in lifecycles of tk components and menu components.
So as menu-related components are that different from normal widgets they are placed here, in a separate file.
"""


class _TkMenuComponent(metaclass=ABCMeta):
    """Base class for things that may be added to menus."""

    @abstractmethod
    def add_to_menu(self, menu: tk.Menu):
        ...

    def get_menu_item_config(self):
        props = self.props
        return {
            'label': props['label'],
            'state': 'disabled' if props.get('disabled', False) else 'normal'
        }


class TkMenu(_TkMenuComponent, Wrapper, TkComponent):
    tk_ignore_subtree = True

    def add_to_menu(self, menu: tk.Menu):
        menu.add_cascade(menu=self.widget, **self.get_menu_item_config())

    def create_widget(self, tk_parent: tk.BaseWidget) -> tk.BaseWidget:
        return tk.Menu(tk_parent)

    def get_widget_config(self, title=None, tearoff=0, **props):
        conf = super().get_widget_config(**props)

        conf['title'] = title
        conf['tearoff'] = tearoff

        return conf

    def mount(self, parent):
        super().mount(parent)

        self.__layout_enqueued = False

    def unmount(self):
        super().unmount()

        del self.__layout_enqueued

    def __enqueue_layout(self):
        if self.__layout_enqueued:
            return

        self.tree.enqueue_task('layout', self.__layout)
        self.__layout_enqueued = True

    def get_menu_children(self) -> Iterable[_TkMenuComponent]:
        return self.first_matching_descendants(_TkMenuComponent.__instancecheck__)

    def __layout(self):
        self.__layout_enqueued = False

        menu: tk.Menu = self.widget

        menu.delete(0, 'end')

        for item in self.get_menu_children():
            item.add_to_menu(menu)

    def on_tk_child_mounted(self, child):
        assert isinstance(child,
                          _TkMenuComponent), 'Attempt to mount non-menu tk-component as a descendant of menu component'

        self.__enqueue_layout()

    def on_tk_child_updated(self, child):
        self.__enqueue_layout()

    def on_tk_child_unmounted(self, child):
        self.__enqueue_layout()

    def on_menu_child_mounted(self, child):
        self.__enqueue_layout()

    def on_menu_child_updated(self, child):
        self.__enqueue_layout()

    def on_menu_child_unmounted(self, child):
        if self.is_mounted():
            self.__enqueue_layout()


@component(TkMenu)
def tk_menu(
        *,
        label: str,
        title: Optional[str],
        disabled: bool = False,
        tearoff: int = 0,
        **_):
    ...


class TkWindowMenu(TkMenu):
    """Menu that automatically attaches to containing window when mounted."""

    def mount(self, parent):
        super().mount(parent)

        self.get_window().widget.configure(
            menu=self.widget
        )


@component(TkWindowMenu)
def tk_window_menu(**_):
    ...


class _TkMenuItemComponent(_TkMenuComponent, Component, ABC):
    def get_menu_parent(self) -> TkMenu:
        return self.first_matching_ascendant(TkMenu.__instancecheck__)

    def mount(self, parent):
        super().mount(parent)

        menu_parent = self.get_menu_parent()
        self.menu_parent = menu_parent
        menu_parent.on_menu_child_mounted(self)

    def unmount(self):
        self.menu_parent.on_menu_child_unmounted(self)

        super().unmount()

    def update(self):
        super().update()

        self.menu_parent.on_menu_child_updated(self)


class TkMenuCommand(_TkMenuItemComponent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.__command = event_prop_invoker(self, 'on_click')

    def add_to_menu(self, menu: tk.Menu):
        menu.add_command(
            command=self.__command,
            **self.get_menu_item_config(),
        )


@component(TkMenuCommand)
def tk_menu_command(
        *,
        label: str,
        disabled: bool = False,
        on_click: Callable = noop_handler,
        **_):
    ...


class TkMenuSeparator(_TkMenuItemComponent):
    def add_to_menu(self, menu: tk.Menu):
        menu.add_separator()


@component(TkMenuSeparator)
def tk_menu_separator(**_):
    ...


class TkMenuCheckbutton(_TkMenuItemComponent):
    def mount(self, parent):
        super().mount(parent)

        self.__var = tk.Variable(
            value=self.props['initial_value']
        )

    def unmount(self):
        super().unmount()

        del self.__var

    def __command(self, *_):
        self.props['on_change'](self.__var.get())

    def add_to_menu(self, menu: tk.Menu):
        props = self.props
        menu.add_checkbutton(
            variable=self.__var,
            onvalue=props['on_value'],
            offvalue=props['off_value'],
            command=self.__command,
            **self.get_menu_item_config(),
        )


@component(TkMenuCheckbutton)
def tk_menu_checkbutton(
        *,
        on_change: Callable = noop_handler,
        label: str,
        disabled: bool = False,
        initial_value: Any = False,
        on_value: Any = True,
        off_value: Any = False,
        **_):
    ...


class TkMenuRadioButton(_TkMenuItemComponent):
    def mount(self, parent):
        super().mount(parent)

        self.__radio_group = TkRadioGroup.get_for(self, self.props.get('group_name', None))

    def unmount(self):
        super().unmount()

        del self.__radio_group

    def __command(self):
        self.__radio_group.on_selected(self.props['value'])
        self.props['on_selected']()

    def add_to_menu(self, menu: tk.Menu):
        menu.add_radiobutton(
            value=self.props['value'],
            variable=self.__radio_group.variable,
            command=self.__command,
            **self.get_menu_item_config(),
        )


@component(TkMenuRadioButton)
def tk_menu_radiobutton(
        *,
        value: Any,
        label: str,
        disabled: bool = False,
        on_selected: Callable = noop_handler,
        group_name: Optional[str] = None,
        **_):
    ...
