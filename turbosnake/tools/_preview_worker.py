import importlib
import json
import os
import sys
import traceback
from os import path
from types import ModuleType

from turbosnake import Tree, functional_component, use_state


class ModuleTracker:
    # TODO: Track dependencies of root module too
    def __init__(self, root_module: ModuleType):
        self._root_module = root_module
        self._root_mtime = self._get_root_mtime()

    def _get_root_mtime(self):
        return os.stat(self._root_module.__file__).st_mtime

    def has_changes(self):
        return self._get_root_mtime() != self._root_mtime

    def reload(self):
        self._root_mtime = self._get_root_mtime()
        importlib.reload(self._root_module)


def list_preview_components(module):
    return [v for v in module.__dict__.values() if hasattr(v, 'enable_preview') and v.enable_preview]


def load_root_module(module_path: str):
    print('Loading preview root module', module_path)

    module_name = path.basename(module_path).replace('.py', '')

    # sys.path.append(path.dirname(module_path))
    return importlib.import_module(module_name)


def print_refresh_error(message):
    print(message)
    traceback.print_exc(file=sys.stdout)
    sys.stdout.flush()


def preview(
        manager_module: ModuleType,
        root_module: ModuleType,
        options: dict,
):
    tree: Tree = manager_module.create_tree(**options)
    tracker = ModuleTracker(root_module)
    initial_preview_components = list_preview_components(root_module)

    def schedule_check():
        tree.schedule_delayed_task(100, check_updates)

    def check_updates():
        schedule_check()

        if not tracker.has_changes():
            return

        print('Update detected')
        sys.stdout.flush()

        # noinspection PyBroadException
        try:
            tracker.reload()
        except Exception:
            return print_refresh_error('Exception reloading changed modules:')

        preview_components = list_preview_components(root_module)
        set_components(preview_components)

    schedule_check()

    set_components = None

    @functional_component
    def preview_root():
        nonlocal set_components
        components, set_components = use_state(initial_preview_components)

        # noinspection PyBroadException
        try:
            manager_module.render_preview_components(components)
        except Exception:
            return print_refresh_error('Error rendering preview components:')

    with tree:
        preview_root()

    manager_module.run_main_loop(tree=tree, **options)


def main():
    manager_module_name = os.getenv('TURBOSNAKE_PREVIEW_MANAGER')
    root_module_path = os.getenv('TURBOSNAKE_PREVIEW_ROOT')
    options_string = os.getenv('TURBOSNAKE_PREVIEW_OPTIONS')

    preview(
        root_module=load_root_module(root_module_path),
        manager_module=importlib.import_module(manager_module_name),
        options=json.loads(options_string)
    )


if __name__ == '__main__':
    main()
