import sys

from turbosnake import functional_component, use_state
from turbosnake.ttk import tk_app, tk_menu, tk_window_menu, tk_menu_command, tk_menu_separator, tk_menu_checkbutton, \
    tk_label, tk_radio_group, tk_menu_radiobutton, tk_window


def on_exit(*_):
    sys.exit(0)


@functional_component
def root():
    foo, set_foo = use_state('Foo!')

    with tk_window_menu():
        with tk_menu(label='Bar'):
            with tk_menu(label='Baz'):
                tk_menu_command(label='Foo')
                tk_menu_command(label='Exit', on_click=on_exit)

        with tk_menu(label='FfOoOo'):
            with tk_radio_group(initial_value='foO'):
                tk_menu_radiobutton(label='Foo', value='Foo')
                tk_menu_radiobutton(label='foO', value='foO')
                tk_menu_radiobutton(label='fOo', value='fOo')

    tk_label(text=foo)

    with tk_window(title='Window 2'):
        with tk_window_menu():
            with tk_menu(label='File'):
                tk_menu_command(label='Open')
                tk_menu_checkbutton(label='Foo?', on_value='Foo!', off_value='No FOO!', on_change=set_foo,
                                    initial_value=foo)
                tk_menu_separator()
                tk_menu_command(label='Exit', on_click=on_exit)

            if foo == 'Foo!':
                with tk_menu(label='Foo'):
                    tk_menu_command(label='Bar')

            tk_menu_command(label=foo, disabled=foo != 'Foo!')


if __name__ == '__main__':
    with tk_app(min_width=500, min_height=50, resizable_w=False, title='Menus'):
        root()
