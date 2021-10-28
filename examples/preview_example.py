from turbosnake import functional_component
from turbosnake.ttk import tk_button
from turbosnake.ttk.tools import tk_run_preview, preview_component

"""
Run this file and then try to change it to see contents of the window changing
according to changes in this file.
"""


@preview_component
@functional_component
def test_component():
    tk_button(text='Hell`o')


if __name__ == '__main__':
    tk_run_preview()
