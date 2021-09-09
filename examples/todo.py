from collections import OrderedDict

from turbosnake import functional_component, use_ref, use_callback, use_toggle, use_state
from turbosnake.ttk import tk_app, TkEntry, TkButton, TkWindow, TkLabel


@functional_component
def create_form(on_create, on_dismiss):
    input_ref = use_ref()

    @use_callback(input_ref)
    def create():
        on_create(input_ref.current.text)
        on_dismiss()

    with TkWindow(on_close=on_dismiss):
        TkEntry(ref=input_ref, initial_value='Procrastinate')

        TkButton(text='Create', on_click=create)


@functional_component
def todo_item(name, text, on_done):
    @use_callback([on_done])
    def done():
        on_done(name)

    TkLabel(text=name)
    TkLabel(text=text)
    TkButton(text='Done!', on_click=done)


@functional_component
def root():
    create_open, toggle_create_open = use_toggle()
    items, set_items = use_state(OrderedDict({'TODO-0': 'Make this example look better'}))
    counter, set_counter = use_state(1)

    @use_callback(counter, items)
    def create(new_text):
        new_items = items.copy()
        new_items[f'TODO-{counter}'] = new_text
        set_counter(counter + 1)
        set_items(new_items)

    @use_callback(items)
    def done(item_name):
        new_items = items.copy()
        del new_items[item_name]
        set_items(new_items)

    if create_open:
        create_form(
            on_dismiss=toggle_create_open,
            on_create=create
        )

    TkButton(text='Add', on_click=toggle_create_open)

    for name, text in items.items():
        todo_item(key=name, text=text, name=name, on_done=done)


if __name__ == '__main__':
    with tk_app():
        root()
