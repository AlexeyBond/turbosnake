import inspect
from abc import abstractmethod, ABC, ABCMeta
from tkinter.ttk import Style as TtkStyle
from typing import Union, Iterable, Optional, Callable

from turbosnake._utils0 import RandomIdSet
from turbosnake.ttk._core import TkComponent


class StyledTkComponent(TkComponent, ABC):
    # noinspection PyShadowingNames
    def get_widget_config(self, style=None, **props):
        config = super().get_widget_config(**props)

        if style:
            if isinstance(style, str):
                config['style'] = style
            elif isinstance(style, Style):
                try:
                    style_instance: StyleInstance = self.__style_instance
                except AttributeError:
                    self.__style_instance = style_instance = style.instantiate(self)
                else:
                    if style_instance.style is style:
                        style_instance.update(self)
                    else:
                        self.__style_instance = style_instance = style.instantiate(self)

                config['style'] = style_instance.name
            else:
                assert False, \
                    f'Got unexpected value for style attribute on {self.__class__.__name__} component: {repr(style)}'
        else:
            try:
                style_instance: StyleInstance = self.__style_instance
            except AttributeError:
                pass
            else:
                style_instance.release()
                del self.__style_instance
                config['style'] = None

        return config

    def unmount(self):
        super().unmount()

        try:
            style_instance = self.__style_instance
        except AttributeError:
            return

        style_instance.release()
        del self.__style_instance


class StyleInstance(ABC, metaclass=ABCMeta):
    @property
    @abstractmethod
    def name(self) -> str:
        """ Name of ttk style associated with this instance.
        """
        ...

    @property
    @abstractmethod
    def style(self) -> 'Style':
        """ Style this instance belongs to.
        """
        ...

    @abstractmethod
    def update(self, component: TkComponent):
        """ Called when a component that uses this style instance has updated.
        """
        ...

    @abstractmethod
    def release(self):
        """ Called when component stops using a style.
        """
        ...


class Style(ABC, metaclass=ABCMeta):
    @abstractmethod
    def instantiate(self, component: TkComponent) -> StyleInstance:
        ...

    @abstractmethod
    def apply(self, builder: 'StyleBuilder', component: TkComponent):
        ...

    @abstractmethod
    def __call__(self, callback: Callable) -> 'Style':
        """ Like #extend but extended style inherits name prefix of original style and the original style is not
        guaranteed to be functional any longer.

        Meant for use-cases where additional options are specified on style creation:

        @style(a_parent_style, another_parent_style, name_prefix='AReadableStyleName')
        def my_style(s):
            ...
        """
        ...

    def extend(self, *args, **kwargs):
        """ Creates new style extending this one.

        @style
        def style1(s):
            ...

        @style1.extend
        def style2(s):
            ...
        """
        return style(self, *args, **kwargs)


class StyleBuilder:
    def __init__(self, base_class: Optional[str] = None):
        self.__map = {}
        self.__config = {}
        self.base_class = base_class

    def __setitem__(self, key: Union[str, Iterable[str]], value: str):
        if isinstance(key, str):
            self.__config[key] = value
        elif hasattr(key, '__iter__'):
            key_len = len(key)
            if key_len == 1:
                self.__config[key[0]] = value
            elif key_len == 0:
                raise Exception('Style key sequence must not be empty')
            else:
                real_key = key[0]
                state_spec = key[1:]
                _map = self.__map
                _map[real_key] = ((state_spec, value), *_map.get(real_key, ()))
        else:
            raise Exception(f'Style key must be a string or sequence of strings, got {repr(key)}')

    def apply(self, style_db: TtkStyle, name: str):
        style_db.configure(name, **self.__config)
        style_db.map(name, **self.__map)


_global_style_id_set = RandomIdSet()


class _StaticStyleInstance(StyleInstance):
    def __init__(self, _style: '_StaticStyle', component: TkComponent):
        self.__style = _style
        self.__class = component.widget.winfo_class()
        self.__name = _style.configure_for_component(component)

    @property
    def style(self) -> Style:
        return self.__style

    @property
    def name(self) -> str:
        return self.__name

    def update(self, component: TkComponent):
        clz = component.widget.winfo_class()
        if clz == self.__class:
            return

        self.__name = self.__style.configure_for_component(component)
        self.__class = clz

    def release(self):
        pass


class _StaticStyle(Style):
    """A Style that does not depend on component properties.
    """
    _used_style_ids = set()

    def __init__(self,
                 configuration_callbacks: list[Callable],
                 name_prefix: str,
                 ):
        if not name_prefix:
            name_prefix = _global_style_id_set.generate()

        if len(configuration_callbacks) == 1:
            self.apply = configuration_callbacks[0]
        else:
            self.__callbacks = configuration_callbacks

        self.__name_prefix = name_prefix

        # Map from widget class to name of this style
        # e.g. for _StaticStyle with __name_prefix='Foo' and class 'TButton' there will be entry
        # 'TButton': 'Foo.TButton'
        self.__style_names: dict[str, str] = {}

    def __call__(self, callback):
        return style(*self.__callbacks, callback, name_prefix=self.__name_prefix)

    def configure_for_component(self, component: TkComponent) -> str:
        widget_class = component.widget.winfo_class()

        try:
            return self.__style_names[widget_class]
        except KeyError:
            pass

        builder = StyleBuilder(base_class=widget_class)
        self.apply(builder, component)
        resulting_base_class = builder.base_class

        try:
            style_name = self.__style_names[resulting_base_class]
        except KeyError:
            pass
        else:
            self.__style_names[widget_class] = style_name
            return style_name

        style_name = f'{self.__name_prefix}.{resulting_base_class}'

        builder.apply(
            component.tree.style_db,
            style_name
        )

        self.__style_names[resulting_base_class] = style_name
        return style_name

    def instantiate(self, component: TkComponent):
        return _StaticStyleInstance(self, component)

    def apply(self, builder: 'StyleBuilder', component: TkComponent):
        for cb in self.__callbacks:
            cb(builder, component)


class _DynamicStyleInstance(StyleInstance):
    def __init__(
            self,
            _style: '_DynamicStyle',
            component: TkComponent,
    ):
        self.__style = _style
        self.__component = component
        self.__base_class = None
        self.__name = None

        self.update(component)

    @property
    def name(self) -> str:
        return self.__name

    @property
    def style(self) -> 'Style':
        return self.__style

    def update(self, component: TkComponent):
        builder = StyleBuilder(base_class=component.widget.winfo_class())
        self.__style.apply(builder, component)
        base_class = builder.base_class

        if not self.__name:
            self.__name = self.__style.acquire_name(base_class)
            self.__base_class = base_class
        elif self.__base_class != base_class:
            self.__style.release_name(self.__base_class, self.__name)
            self.__name = self.__style.acquire_name(base_class)
            self.__base_class = base_class

        builder.apply(
            component.tree.style_db,
            self.__name
        )

    def release(self):
        self.__style.release_name(self.__base_class, self.__name)


class _DynamicStyle(Style):
    def __init__(
            self,
            configuration_callbacks,
            name_prefix,
    ):
        self.__callbacks = configuration_callbacks
        self.__name_prefix = name_prefix
        self.__style_id_set = RandomIdSet() if name_prefix else _global_style_id_set
        self.__name_pool: dict[str, list[str]] = {}

    def __generate_name(self, base_class):
        if self.__name_prefix:
            base_class = f'{self.__name_prefix}.{base_class}'

        return f'{self.__style_id_set.generate()}.{base_class}'

    def acquire_name(self, base_class):
        try:
            names: list[str] = self.__name_pool[base_class]
        except KeyError:
            return self.__generate_name(base_class)

        try:
            return names.pop()
        except IndexError:
            return self.__generate_name(base_class)

    def release_name(self, base_class, name):
        try:
            names: list[str] = self.__name_pool[base_class]
        except KeyError:
            names = []
            self.__name_pool[base_class] = names

        names.append(name)

    def instantiate(self, component: TkComponent) -> StyleInstance:
        return _DynamicStyleInstance(self, component)

    def apply(self, builder: 'StyleBuilder', component: TkComponent):
        for cb in self.__callbacks:
            cb(builder, component)

    def __call__(self, callback):
        return style(*self.__callbacks, callback, name_prefix=self.__name_prefix)


_POSITIONAL_PARAM_KINDS = (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
_KEYWORD_PARAM_KINDS = (
    inspect.Parameter.KEYWORD_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.VAR_KEYWORD)


def _normalize_style_callback(cb: Callable):
    try:
        if cb.__is_normalized_style_callback:
            return cb, cb.__dynamic_component_access_required
    except AttributeError:
        pass

    is_dynamic = False
    signature = inspect.signature(cb)
    parameters = (*signature.parameters.values(),)

    if parameters[0].kind not in _POSITIONAL_PARAM_KINDS:
        raise Exception('Illegal style function signature. At least one positional parameter is expected.')

    if len(parameters) == 1:
        def normalized_callback(builder: StyleBuilder, component: TkComponent):
            cb(builder)
    elif all(par.kind in _KEYWORD_PARAM_KINDS for par in parameters[1:]):
        is_dynamic = True

        def normalized_callback(builder: StyleBuilder, component: TkComponent):
            cb(builder, **component.props)
    else:
        raise Exception('Illegal style function signature')

    normalized_callback.__is_normalized_style_callback = True
    normalized_callback.__dynamic_component_access_required = is_dynamic

    return normalized_callback, is_dynamic


def style(
        *args,
        name_prefix=None
) -> Style:
    style_constructor = _StaticStyle
    callbacks = []

    for arg in args:
        if isinstance(arg, _StaticStyle):
            callbacks.append(arg.apply)
        elif isinstance(arg, Style):
            style_constructor = _DynamicStyle
            callbacks.append(arg.apply)
        elif callable(arg):
            normalized, is_dynamic = _normalize_style_callback(arg)
            callbacks.append(normalized)

            if is_dynamic:
                style_constructor = _DynamicStyle
        else:
            raise Exception(f'Unexpected style() argument: {repr(arg)}')

    return style_constructor(
        configuration_callbacks=callbacks,
        name_prefix=name_prefix,
    )
