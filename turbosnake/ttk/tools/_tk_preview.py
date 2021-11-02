from typing import Callable

from turbosnake.tools import run_preview, preview_component as preview_component_
from turbosnake.ttk import TkTree

preview_component = preview_component_


def tk_run_preview(
        module_name='__main__',
        topmost=True,
        min_width=200,
        min_height=0,
):
    run_preview(
        module_name=module_name,
        manager_module_name=__name__,
        options={
            'topmost': topmost,
            'min_width': min_width,
            'min_height': min_height,
        }
    )


def create_tree(**options) -> TkTree:
    return TkTree(**options)


def run_main_loop(tree: TkTree, **options):
    tree.main_loop()


def render_preview_components(components: list[Callable], **options):
    for component in components:
        # TODO: Add named frames/tabs or something like that...
        component()
