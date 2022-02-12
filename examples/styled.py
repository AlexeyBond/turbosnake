from turbosnake import functional_component, use_toggle
from turbosnake.ttk import tk_app, style, tk_button


@style
def red(s):
    s['foreground'] = 'red'
    s['background'] = 'red'


@style
def dynamic(s, *, state, **_):
    c = 'red' if state else 'blue'
    s['foreground'] = c
    s['background'] = c


@functional_component
def root():
    state, toggle = use_toggle()
    state1, toggle1 = use_toggle()

    tk_button(style=red, text='Red button')

    tk_button(style=dynamic, state=state, text='Dynamic button', on_click=toggle)
    tk_button(style=dynamic, state=state1, text='Dynamic button', on_click=toggle1)


if __name__ == '__main__':
    with tk_app(min_width=300, min_height=400):
        root()
