from ._components import TkTree


def tk_app(widget=None, **options):
    """Shortcut function that creates TkTree, renders it's content and starts main loop.

    Usage:

    if __name__ == '__main__':
        with tk_app():
            root(...)
    """
    tree = TkTree(widget, **options)

    class _App:
        def __enter__(self):
            return tree.__enter__()

        def __exit__(self, exc_type, exc_val, exc_tb):
            tree.__exit__(exc_type, exc_val, exc_tb)

            tree.main_loop()

    return _App()
