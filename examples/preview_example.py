from turbosnake import functional_component
from turbosnake.ttk import tk_button, tk_grid_frame
from turbosnake.ttk.tools import tk_run_preview, preview_component

"""
Run this file and then try to change it to see contents of the window changing
according to changes in this file.
"""


@preview_component
@functional_component
def test_component():
    with tk_grid_frame(
            fill='both',
            expand=1,
            column_weights=(2, 1, 1),
            row_weights=(1, 0, 0),
            column_min_sizes=(100, 100, 0),
    ):
        tk_button(text='Hell`o', column=0, row=1, column_span=2, sticky='we')
        tk_button(text='Hell`o', column=1, row=0, sticky='wesn')
        tk_button(text='Hell`o', column=2, row=2)


if __name__ == '__main__':
    tk_run_preview(min_height=100)
