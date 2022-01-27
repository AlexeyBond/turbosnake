import tkinter as tk
from tkinter import ttk

from turbosnake import use_ref, functional_component, ComponentsCollection, use_effect, use_callback_proxy
from ._adapters import tk_packed_frame, tk_canvas, tk_scrollbar, tk_button
from ._style import style

"""
_composite.py

Contains turbosnake.ttk-specific composite components.
"""


@functional_component
def tk_scrollable_frame(
        children: ComponentsCollection,
        **props
):
    """Vertically-scrollable frame.

    Based on `idlelib.configdialog.VerticalScrolledFrame` and random posts from stackoverflow.
    Unlike `idlelib.configdialog.VerticalScrolledFrame` supports mouse scroll events (at least, some of them).
    """
    canvas_ref = use_ref()
    interior_ref = use_ref()
    scrollbar_ref = use_ref()

    @use_effect(queue='layout_effect')
    def setup():
        canvas: tk.Canvas = canvas_ref.current.widget
        scrollbar: ttk.Scrollbar = scrollbar_ref.current.widget
        interior: ttk.Frame = interior_ref.current.widget

        scrollbar.config(command=canvas.yview)
        canvas.config(yscrollcommand=scrollbar.set)

        canvas.xview_moveto(0)
        canvas.yview_moveto(0)

        interior_id = canvas.create_window(0, 0, window=interior, anchor='nw')

        def _configure_interior(event):
            size = (interior.winfo_reqwidth(), interior.winfo_reqheight())
            canvas.config(scrollregion="0 0 %s %s" % size)

        interior.bind('<Configure>', _configure_interior)

        def _configure_canvas(event):
            if interior.winfo_reqwidth() != canvas.winfo_width():
                canvas.itemconfigure(interior_id, width=canvas.winfo_width())

        canvas.bind('<Configure>', _configure_canvas)

        root_widget: tk.BaseWidget = canvas_ref.current.tree.widget

        def on_wheel_scroll(event):
            # TODO: Add support for X11 events
            delta = event.delta
            if abs(delta) >= 120:
                delta = delta / 120

            # Why `-delta`, not `delta`? I don't know.
            canvas.yview_scroll(int(-delta), 'units')

        bind_id = None

        def bind_mouse_wheel(*_):
            nonlocal bind_id
            bind_id = root_widget.bind('<MouseWheel>', on_wheel_scroll)

        canvas.master.bind('<Enter>', bind_mouse_wheel)

        def unbind_mouse_wheel(*_):
            root_widget.unbind('<MouseWheel>', bind_id)

        canvas.master.bind('<Leave>', unbind_mouse_wheel)

        canvas_ref.current.tree.widget.bind('<MouseWheel>', print)

    with tk_packed_frame(**props):
        with tk_canvas(side='left', fill='both', expand=1, ref=canvas_ref):
            with tk_packed_frame(ref=interior_ref):
                children()
        tk_scrollbar(orientation='vertical', fill='y', side='right', expand=0, ref=scrollbar_ref)


@style(name_prefix='Link')
def _link_style(s):
    s.base_class = 'TLabel'
    s['foreground', 'active'] = '#167eb1'
    s['foreground', 'disabled'] = 'gray'
    s['foreground'] = '#2e00fd'


@functional_component
def tk_link(
        *,
        text,
        href,
        cursor='hand2',
        disabled_cursor='pirate',  # because why not?
        disabled=False,
        **props
):
    """A link. Yes, just like in web.
    """

    @use_callback_proxy
    def on_click(*_):
        import webbrowser
        webbrowser.open(href)

    tk_button(
        on_click=on_click,
        text=text,
        cursor=disabled_cursor if disabled else cursor,
        style=_link_style,
        disabled=disabled,
        **props
    )
