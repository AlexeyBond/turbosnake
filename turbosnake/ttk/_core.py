import sys
import tkinter as tk
import traceback
from abc import abstractmethod, ABCMeta, ABC
from collections import Generator
from typing import Optional

from turbosnake import Component, Tree

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
            self.tree.enqueue_task('layout', self.__repack_children)

    def on_tk_child_mounted(self, child):
        if child.tk_ignore_subtree:
            return
        super().on_tk_child_mounted(child)
        self.schedule_repack()

    def on_tk_child_updated(self, child):
        if child.tk_ignore_subtree:
            return
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
    def get_window(self):
        return self

    def __init__(self, widget=None, **options):
        super().__init__(queues=(*super().TASK_QUEUES, 'layout', 'layout_effect'))

        self.__widget = widget or tk.Tk()
        configure_window(self.__widget, **options)

    layout_props = {}

    def schedule_task(self, callback):
        self.__widget.after_idle(callback)

    @property
    def widget(self):
        return self.__widget

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
        self.configure_widget(widget)

        self.__widget = widget

    def configure_widget(self, widget):
        widget.config(**self.get_widget_config(**self.props))

    def update(self):
        super().update()

        self.configure_widget(self.__widget)

        # TODO:
        # self.tk_parent.on_tk_child_updated(self)

    @abstractmethod
    def create_widget(self, tk_parent: tk.BaseWidget) -> tk.BaseWidget:
        ...

    def get_widget_config(self, **props):
        return {}

    def get_window(self):
        return self.tk_parent.get_window()
