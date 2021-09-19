import sys

from turbosnake import functional_component, use_state
from turbosnake.ttk import tk_app, TkWindow, TkMenu, TkWindowMenu, TkMenuCommand, TkMenuSeparator, TkMenuCheckbutton, \
    TkLabel, TkRadioGroup, TkMenuRadioButton


def on_exit(*_):
    sys.exit(0)


@functional_component
def root():
    foo, set_foo = use_state('Foo!')

    with TkWindowMenu():
        with TkMenu(label='Bar'):
            with TkMenu(label='Baz'):
                TkMenuCommand(label='Foo')
                TkMenuCommand(label='Exit', on_click=on_exit)

        with TkMenu(label='FfOoOo'):
            with TkRadioGroup(initial_value='foO'):
                TkMenuRadioButton(label='Foo', value='Foo')
                TkMenuRadioButton(label='foO', value='foO')
                TkMenuRadioButton(label='fOo', value='fOo')

    TkLabel(text=foo)

    with TkWindow(title='Window 2'):
        with TkWindowMenu():
            with TkMenu(label='File'):
                TkMenuCommand(label='Open')
                TkMenuCheckbutton(label='Foo?', on_value='Foo!', off_value='No FOO!', on_change=set_foo,
                                  initial_value=foo)
                TkMenuSeparator()
                TkMenuCommand(label='Exit', on_click=on_exit)

            if foo == 'Foo!':
                with TkMenu(label='Foo'):
                    TkMenuCommand(label='Bar')

            TkMenuCommand(label=foo, disabled=foo != 'Foo!')


if __name__ == '__main__':
    with tk_app(min_width=500, min_height=50, resizable_w=False, title='Menus'):
        root()
