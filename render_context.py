from contextlib import contextmanager
import threading

_tl = threading.local()


def get_render_context(name):
    return getattr(_tl, name, None)


def enter_render_context(name, value):
    """Sets and restores a render context variable.

    restore = enter_render_context('x', myCtx)

    ...
    get_render_context('x') is myCtx
    ...

    restore()

    :param name:
    :param value:
    :return:
    """
    prev = get_render_context(name)

    setattr(_tl, name, value)

    def exit_render_context():
        assert get_render_context(name) is value

        setattr(_tl, name, prev)

        return value

    return exit_render_context


@contextmanager
def render_context_manager(name, value):
    """Wrapper for `enter_render_context` to use it with `with`

    :param name: context name
    :param value: context value
    """
    recover = enter_render_context(name, value)

    try:
        yield value
    finally:
        recover()
