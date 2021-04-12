import asyncio
import functools


def wrap_sync_writer(writer):
    class AsyncWriter:
        def __init__(self, writer):
            self.write = wrap_sync_func(writer.write)

    return AsyncWriter(writer)


def wrap_sync_reader(reader):
    class AsyncReader:
        def __init__(self, reader):
            self.read = wrap_sync_func(reader.read)

    return AsyncReader(reader)


def wrap_sync_func(func):
    if asyncio.iscoroutinefunction(func):
        return func

    @functools.wraps(func)
    async def coro(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            functools.partial(func, *args, **kwargs)
        )
    return coro


def run_async(coro):
    asyncio.set_event_loop(asyncio.new_event_loop())
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(coro)
    loop.close()
    return result
