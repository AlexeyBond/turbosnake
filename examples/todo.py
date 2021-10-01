from collections import OrderedDict

from turbosnake import functional_component, use_ref, use_toggle, use_state, use_callback_proxy
from turbosnake.ttk import tk_app
from turbosnake.ttk import tk_entry, tk_button, tk_window, tk_label, tk_packed_frame, tk_scrollable_frame


@functional_component
def create_form(on_create, on_dismiss):
    input_ref = use_ref()

    @use_callback_proxy
    def create():
        on_create(input_ref.current.text)
        on_dismiss()

    @use_callback_proxy
    def create_and_continue():
        on_create(input_ref.current.text)
        input_ref.current.text = ''

    with tk_window(on_close=on_dismiss, resizable=False, min_width=300, title='Create a TODO'):
        tk_entry(ref=input_ref, initial_value='Procrastinate', fill='x', px=8, py=8)

        with tk_packed_frame(default_side='left'):
            tk_button(text='Create', on_click=create)
            tk_button(text='Create+', on_click=create_and_continue)


@functional_component
def todo_item(name, text, on_done):
    @use_callback_proxy
    def done():
        on_done(name)

    with tk_packed_frame(default_side='left', fill='x', anchor='n'):
        tk_button(text='Done!', on_click=done, fill='y')
        with tk_packed_frame(expand=True, fill='x'):
            tk_label(text=name, anchor='w')
            tk_label(text=text, anchor='w')


INITIAL_LIST = OrderedDict({
    'TODO-0': 'Make this example look better',
})


@functional_component
def root():
    create_open, toggle_create_open = use_toggle()
    items, set_items = use_state(INITIAL_LIST)
    counter, set_counter = use_state(1)

    @use_callback_proxy
    def create(new_text):
        new_items = items.copy()
        new_items[f'TODO-{counter}'] = new_text
        set_counter(counter + 1)
        set_items(new_items)

    @use_callback_proxy
    def done(item_name):
        new_items = items.copy()
        del new_items[item_name]
        set_items(new_items)

    if create_open:
        create_form(
            on_dismiss=toggle_create_open,
            on_create=create
        )

    tk_button(text='Add', on_click=toggle_create_open, disabled=create_open)

    with tk_scrollable_frame(fill='both', expand=1):
        for name, text in items.items():
            todo_item(key=name, text=text, name=name, on_done=done)


if __name__ == '__main__':
    with tk_app(min_width=300, min_height=400, resizable_w=False, title='TODO list'):
        root()
