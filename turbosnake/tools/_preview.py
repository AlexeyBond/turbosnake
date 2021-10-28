import json
import os
import os.path as path
import sys


def preview_component(component):
    component.enable_preview = True
    return component


def run_preview(
        manager_module_name,
        options,
        module_name: str = '__main__',
):
    module = sys.modules[module_name]
    worker_path = path.join(path.dirname(__file__), '_preview_worker.py')

    os.spawnve(
        os.P_WAIT,
        sys.executable,
        [
            sys.executable,
            worker_path,
        ],
        {
            'PYTHONPATH': path.pathsep.join(sys.path),
            'TURBOSNAKE_PREVIEW_ROOT': module.__file__,
            'TURBOSNAKE_PREVIEW_MANAGER': manager_module_name,
            'TURBOSNAKE_PREVIEW_OPTIONS': json.dumps(options),
        }
    )
