import asyncio
import sys
import tkinter as tk
import traceback
from abc import abstractmethod, ABCMeta, ABC
from collections import Generator
from functools import cache
from tkinter.ttk import Style
from typing import Optional

from turbosnake import Component, Tree
from turbosnake._utils0 import create_daemon_event_loop
from turbosnake.ttk._layout import get_layout_manager_class, DEFAULT_LAYOUT_MANAGER, LayoutManagerABC

"""
_core.py

Contains basic low-level parts of turbosnake-ttk adapter.
"""


class TkBase(metaclass=ABCMeta):
    @property
    @abstractmethod
    def widget(self) -> tk.BaseWidget:
        ...

    @property
    @abstractmethod
    def tree(self):
        ...

    @abstractmethod
    def get_window(self) -> 'TkBase':
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


class TkContainerBase(TkBase, ABC):
    def init_container(self, layout_manager=DEFAULT_LAYOUT_MANAGER, **kwargs):
        self._layout_manager: LayoutManagerABC = get_layout_manager_class(layout_manager)(
            container=self,
            settings=kwargs
        )

    def update_container_settings(self, layout_manager=DEFAULT_LAYOUT_MANAGER, **kwargs):
        lm_class = get_layout_manager_class(layout_manager)

        if self._layout_manager.__class__ is not lm_class:
            self._layout_manager.on_terminated()
            self._layout_manager = new_lm = lm_class(container=self, settings=kwargs)
            for child in self.get_tk_children():
                new_lm.on_child_added(child)
        else:
            self._layout_manager.on_update_settings(kwargs)

    def destroy_container(self):
        self._layout_manager.on_terminated()
        del self._layout_manager

    def on_tk_child_mounted(self, child):
        super().on_tk_child_mounted(child)
        self._layout_manager.on_child_added(child)

    def on_tk_child_updated(self, child):
        super().on_tk_child_updated(child)
        self._layout_manager.on_child_updated(child)

    def on_tk_child_unmounted(self, child):
        super().on_tk_child_unmounted(child)
        self._layout_manager.on_child_removed(child)


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
        topmost=False,
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

    widget.attributes('-topmost', topmost)


class TkTree(Tree, TkContainerBase, TkBase):
    def get_window(self):
        return self

    def __init__(self, widget=None, event_loop_factory=create_daemon_event_loop, **options):
        super().__init__(queues=(*super().TASK_QUEUES, 'layout', 'layout_effect'))

        self.__widget = widget or tk.Tk()
        configure_window(self.__widget, **options)
        self.init_container(**options)

        self.__style_db = Style(self.__widget)

        self.__event_loop_factory = event_loop_factory

    @property
    @cache
    def event_loop(self) -> asyncio.AbstractEventLoop:
        return self.__event_loop_factory()

    def schedule_task(self, callback):
        self.__widget.after_idle(callback)

    def schedule_delayed_task(self, delay, callback):
        cancel_id = self.__widget.after(ms=delay, func=callback)
        return lambda: self.__widget.after_cancel(cancel_id)

    @property
    def widget(self):
        return self.__widget

    @property
    def style_db(self) -> Style:
        return self.__style_db

    def handle_error(self, error, queue_name, task):
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

    @property
    def tree(self) -> TkTree:
        # noinspection PyTypeChecker
        return super().tree

    def mount(self, parent):
        assert isinstance(parent.tree, TkTree), "TkComponent's can be mounted under TkTree only"
        super().mount(parent)

        tk_parent: TkBase = self.get_tk_parent()

        self.tk_parent = tk_parent
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
        self.__widget = widget

        self.configure_widget(widget)

    def configure_widget(self, widget):
        widget.config(**self.get_widget_config(**self.props))

    def update(self):
        super().update()

        self.configure_widget(self.__widget)

        self.tk_parent.on_tk_child_updated(self)

    @abstractmethod
    def create_widget(self, tk_parent: tk.BaseWidget) -> tk.BaseWidget:
        ...

    def get_widget_config(self, **props):
        return {}

    def get_window(self):
        return self.tk_parent.get_window()
