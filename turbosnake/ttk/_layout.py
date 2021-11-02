from abc import abstractmethod, ABCMeta
from typing import Type, Union, Callable, Literal

from turbosnake._utils0 import have_differences_by_keys


class LayoutManagerABC(metaclass=ABCMeta):
    __slots__ = ('container', 'settings', 'active')
    SELF_LAYOUT_PROPS = ()
    CHILD_LAYOUT_PROPS = ()

    def __init__(self, container, settings):
        self.container = container
        self.settings = settings
        self.active = True

    @abstractmethod
    def on_child_added(self, child):
        ...

    def on_child_updated(self, child):
        if child.has_props_changed(self.CHILD_LAYOUT_PROPS):
            self.on_child_layout_props_changed(child)

    @abstractmethod
    def on_child_layout_props_changed(self, child):
        ...

    def on_child_removed(self, child):
        ...

    def on_update_settings(self, new_settings: dict):
        changed = have_differences_by_keys(self.settings, new_settings, self.SELF_LAYOUT_PROPS)
        self.settings = new_settings

        if changed:
            self.on_own_layout_props_changed()

    def on_own_layout_props_changed(self):
        ...

    def on_terminated(self):
        self.active = False


class PlaceLayoutManager(LayoutManagerABC):
    CHILD_LAYOUT_PROPS = ('x', 'y', 'relx', 'rely', 'width', 'relwidth', 'height', 'relheight', 'anchor')
    SELF_LAYOUT_PROPS = ('default_anchor',)

    def __init__(self, container, settings):
        super().__init__(container, settings)

    def on_child_added(self, child):
        child_props = child.props
        own_props = self.settings
        place_options = {}

        if 'anchor' in child_props:
            place_options['anchor'] = child_props['anchor']
        elif 'default_anchor' in own_props:
            place_options['anchor'] = own_props['default_anchor']

        def relative_or_absolute_option(abs_prop: str, rel_prop: str):
            if rel_prop in child_props:
                assert abs_prop not in child_props, f"At most one of '{abs_prop}' and '{rel_prop}' must be set on " \
                                                    f"this component but both are present"

                place_options[rel_prop] = child_props[rel_prop]
            elif abs_prop in child_props:
                abs_val = child_props[abs_prop]

                if isinstance(abs_val, str) and abs_val.endswith('%'):
                    place_options[rel_prop] = float(abs_val[:-1]) * 0.01
                elif isinstance(abs_val, float):
                    place_options[rel_prop] = abs_val
                else:
                    place_options[abs_prop] = abs_val

        relative_or_absolute_option('x', 'relx')
        relative_or_absolute_option('y', 'rely')
        relative_or_absolute_option('width', 'relwidth')
        relative_or_absolute_option('height', 'relheight')

        child.widget.place(cnf=place_options)

    def on_child_layout_props_changed(self, child):
        child.widget.place_forget()
        self.on_child_added(child)

    def on_own_layout_props_changed(self):
        for child in self.container.get_tk_children():
            self.on_child_layout_props_changed(child)


class PackLayoutManager(LayoutManagerABC):
    __slots__ = ('_repack_requested',)

    CHILD_LAYOUT_PROPS = ('side', 'px', 'py', 'expand', 'fill', 'anchor')
    SELF_LAYOUT_PROPS = ('default_side',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._repack_requested = False

    def _pack_child(self, child):
        p = self.settings
        cp = child.props
        child.widget.pack(
            side=cp.get('side', p.get('default_side', 'top')),
            padx=cp.get('px', 0),
            pady=cp.get('py', 0),
            expand=cp.get('expand', False),
            fill=cp.get('fill', None),
            anchor=cp.get('anchor', None)
        )

    def _repack_children(self):
        if not self._repack_requested:
            return

        for child in self.container.get_tk_children():
            child.widget.pack_forget()
            self._pack_child(child)

        self._repack_requested = False

    def _schedule_repack(self):
        if not self._repack_requested:
            self._repack_requested = True
            self.container.tree.enqueue_task('layout', self._repack_children)

    def on_child_added(self, child):
        self._schedule_repack()

    def on_child_layout_props_changed(self, child):
        self._schedule_repack()

    def on_terminated(self):
        self._repack_requested = False

    def on_own_layout_props_changed(self):
        self._schedule_repack()


class GridLayoutManager(LayoutManagerABC):
    __slots__ = ('_row_count', '_column_count')

    CHILD_LAYOUT_PROPS = ('row', 'column', 'row_span', 'column_span', 'sticky')
    SELF_LAYOUT_PROPS = (
        'row_weights', 'row_min_sizes', 'row_pads', 'column_weights', 'column_min_sizes', 'column_pads'
    )

    def __init__(self, container, settings):
        super().__init__(container, settings)

        self._row_count = 0
        self._column_count = 0
        self._configure_rows_and_columns()

    def _configure_rows_and_columns(self):
        widget = self.container.widget
        self._row_count = self._configure_rows_or_columns(
            widget.grid_rowconfigure,
            'row_weights',
            'row_min_sizes',
            'row_pads',
            self._row_count
        )
        self._column_count = self._configure_rows_or_columns(
            widget.grid_columnconfigure,
            'column_weights',
            'column_min_sizes',
            'column_pads',
            self._column_count
        )

    def _configure_rows_or_columns(
            self,
            method: Callable,
            weights_prop: str,
            min_sizes_prop: str,
            pads_prop: str,
            prev_count: int
    ):
        props = self.container.props
        weights = props.get(weights_prop, ())
        min_sizes = props.get(min_sizes_prop, ())
        pads = props.get(pads_prop, ())

        new_count = max(len(weights), len(min_sizes), len(pads))

        configure_count = max(prev_count, new_count)
        zeros = (0,) * configure_count
        weights += zeros
        min_sizes += zeros
        pads += zeros

        for (i, weight, min_size, pad) in zip(range(configure_count), weights, min_sizes, pads):
            method(i, weight=weight, minsize=min_size, pad=pad)

        return new_count

    def on_own_layout_props_changed(self):
        self._configure_rows_and_columns()

    def on_child_added(self, child):
        child_props = child.props
        grid_settings = {
            'column': child_props.get('column', 0),
            'row': child_props.get('row', 0),
            'rowspan': child_props.get('row_span', 1),
            'columnspan': child_props.get('column_span', 1)
        }

        if 'sticky' in child_props:
            grid_settings['sticky'] = child_props['sticky']

        child.widget.grid(grid_settings)

    def on_child_layout_props_changed(self, child):
        child.widget.grid_forget()
        self.on_child_added(child)


DEFAULT_LAYOUT_MANAGER = 'pack'

NAMED_LAYOUT_MANAGERS: dict[str, Type[LayoutManagerABC]] = {
    'place': PlaceLayoutManager,
    'pack': PackLayoutManager,
    'grid': GridLayoutManager,
}

LayoutManagerPropValue = Union[Literal['place', 'pack', 'grid'], Type[LayoutManagerABC]]


def get_layout_manager_class(layout_manager: LayoutManagerPropValue) -> Type[LayoutManagerABC]:
    if isinstance(layout_manager, str):
        return NAMED_LAYOUT_MANAGERS[layout_manager]
    else:
        assert issubclass(layout_manager, LayoutManagerABC)

        return layout_manager
