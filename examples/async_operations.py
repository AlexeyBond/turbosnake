import asyncio

from turbosnake import functional_component, use_async_call, use_effect
from turbosnake.ttk import tk_app, tk_frame, tk_button, tk_label, tk_packed_frame

_counter = 0


@functional_component
def operation():
    @use_async_call
    async def fn():
        await asyncio.sleep(5)
        global _counter
        _counter = _counter + 1
        return _counter

    with tk_frame():
        with tk_packed_frame(default_side='left'):
            tk_button(text='start', on_click=fn)
            tk_button(text='cancel', on_click=fn.cancel)

        if not fn.was_called:
            msg = '---'
        elif fn.is_in_progress:
            msg = 'Loading...'
        elif fn.future.cancelled():
            msg = 'Cancelled'
        else:
            try:
                msg = f'Result: {fn.future.result()}'
            except Exception as e:
                msg = f'Error: {e}'

        tk_label(text=msg)


@functional_component
def stargazers_count():
    @use_async_call
    async def load_data():
        try:
            import aiohttp
        except:
            raise Exception('Install aiohttp to see this example')

        async with aiohttp.client.ClientSession() as session:
            async with session.get('https://api.github.com/repos/alexeybond/turbosnake') as response:
                data = await response.json()

        return data['stargazers_count']

    use_effect(load_data)

    if not load_data.was_called or load_data.is_in_progress:
        msg = 'Loading...'
    else:
        try:
            msg = f'Turbosnake has {load_data.future.result()} stargazer(s).'
        except Exception as e:
            msg = f'Error: {e}'

    with tk_packed_frame(default_side='left', fill='x'):
        tk_button(text='Reload', disabled=load_data.is_in_progress, on_click=load_data)
        tk_label(text=msg)


@functional_component
def root():
    operation()
    operation()
    stargazers_count()


if __name__ == '__main__':
    with tk_app(min_width=300, min_height=400):
        root()
