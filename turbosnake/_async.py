import asyncio
from abc import ABC, ABCMeta, abstractmethod
from asyncio import InvalidStateError, Future
from functools import cache
from threading import Thread
from typing import Optional

from ._components import Component
from ._hooks import Hook, use_function_hook


@cache
def get_default_event_loop():
    loop = asyncio.new_event_loop()

    Thread(target=loop.run_forever, daemon=True).start()

    return loop


# Timeout-based solutions for integration of asyncio with UI libraries like this one
# https://www.reddit.com/r/Python/comments/33ecpl/neat_discovery_how_to_combine_asyncio_and_tkinter/
# seem too dirty for me, so asyncio has to run on different thread.
# So I can't use Task directly since event loop may run on different thread and
# I can't use Future since it (seems to) cancel a coroutine only if it wasn't started.
# So I have created an adapter that calls Task methods on event loop.
class _AsyncCall:
    def __init__(self, fn, loop: asyncio.AbstractEventLoop, args, kwargs, on_update):
        self._loop = loop
        self.task: Optional[asyncio.Task] = None
        self._on_update = on_update

        loop.call_soon_threadsafe(self._create_task, fn, args, kwargs)

    def cancel(self, msg):
        self._loop.call_soon_threadsafe(self._cancel_task, msg)

    def _create_task(self, fn, args, kwargs):
        self.task = task = self._loop.create_task(
            fn(*args, **kwargs)
        )
        task.add_done_callback(self._on_update)

        self._on_update(task)

    def _cancel_task(self, msg):
        if self.task:
            self.task.cancel(msg)


class AsyncCallHookAPI(ABC, metaclass=ABCMeta):
    @abstractmethod
    def __call__(self, *args, **kwargs):
        """Starts new asynchronous operation with given arguments.

        Previous operation will be cancelled.
        """
        pass

    @property
    @abstractmethod
    def future(self) -> Future:
        """A future to last started operation.

        :raises InvalidStateError when no operation was started
        """
        pass

    @property
    @abstractmethod
    def is_in_progress(self) -> bool:
        """True iff an operation is currently in progress."""
        pass

    @property
    @abstractmethod
    def was_called(self) -> bool:
        """True iff an operation was started at least once."""
        pass

    @property
    @abstractmethod
    def is_done(self) -> bool:
        """True iff an operation was started and completed (successfully or not)."""
        pass

    @abstractmethod
    def cancel(self, msg='Cancelled by component'):
        """Cancels a currently running operation.

        Returns without exception if an operation wasn't started or is already completed.
        """
        pass


class _AsyncCallHook(Hook, AsyncCallHookAPI):
    def __init__(self, component):
        super().__init__(component)

        self.__component: Component = component
        self.__latest_call: Optional[_AsyncCall] = None

    def first_call(self, cb, *, loop):
        self.__callback = cb

        if not loop:
            loop = get_default_event_loop()

        self.__loop: asyncio.AbstractEventLoop = loop
        return self

    def next_call(self, *args, **kwargs):
        return self.first_call(*args, **kwargs)

    def on_unmount(self):
        if self.__latest_call:
            self.__latest_call.cancel('Component unmounted')

    def __on_update(self, task):
        def local_handler():
            if self.__latest_call.task is not task:
                return

            self.__component.enqueue_update()

        self.__component.tree.schedule_task(local_handler)

    def __call__(self, *args, **kwargs):
        if self.__latest_call:
            self.__latest_call.cancel('Next call requested')

        self.__latest_call = _AsyncCall(
            fn=self.__callback,
            loop=self.__loop,
            args=args,
            kwargs=kwargs,
            on_update=self.__on_update
        )

        return self

    @property
    def future(self) -> Future:
        lc = self.__latest_call
        if not lc:
            raise InvalidStateError('No calls were ever performed using this hook.')

        return lc.task

    @property
    def is_in_progress(self):
        lc = self.__latest_call
        if not lc:
            return False

        return not lc.task.done()

    @property
    def is_done(self):
        lc = self.__latest_call
        if not lc:
            return False

        return lc.task.done()

    @property
    def was_called(self):
        return self.__latest_call is not None

    def cancel(self, msg='Cancelled by component'):
        lc = self.__latest_call
        if not lc:
            return

        lc.cancel(msg)


def use_async_call(*args, loop: Optional[asyncio.AbstractEventLoop] = None) -> AsyncCallHookAPI:
    """Provides a way to start/cancel/access result of an asynchronous operation.

    A typical use-case is a component asynchronously loading/reloading displayed data:

    @use_async_call
    async def load_data():
        # Do something asynchronous...
        await asyncio.sleep(10)
        ...
        # Return a result
        return 'result'

    button(on_click=load_data, disabled=load_data.is_in_progress, text='Reload')
    button(on_click=load_data.cancel, disabled=not load_data.is_in_progress, text='Cancel')

    if load_data.is_done:
        try:
            label(text=load_data.future.result())
        except Exception as e:
            label(text=f'Error: {e}')

    :param loop: event loop to run the operation on.
    :return:
    """
    return use_function_hook(_AsyncCallHook, *args, loop=loop)
