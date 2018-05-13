import asyncio
import unittest
import logging
import time

__all__ = ["Aut"]

log = logging.getLogger(__name__)

_times = {
    'setup': [],
    'teardown': [],
    'tests': {}
}

class Aut(unittest.TestCase):

    """Asynchronous Unit Test.

    Quick and dirty, but works pretty well.
    Based on https://stackoverflow.com/a/37888085/6164984

    !! use set_up and tear_down instead of setUp and tearDown !!
    """

    # timeout for every tests in seconds
    TIMEOUT = 1

    def __init__(self, *args, **kwargs):
        self._func_cache = {}
        super().__init__(*args, **kwargs)

    @staticmethod
    def get_times():
        return _times

    def setUp(self):
        self._start_time = time.time()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        if hasattr(self, 'before'):
            if not asyncio.iscoroutinefunction(self.before):
                self.loop.run_until_complete(asyncio.coroutine(self.before)())
            else:
                self.loop.run_until_complete(self.before())
        _times['setup'].append(time.time() - self._start_time)
        self._start_time = time.time()

    def tearDown(self):
        _times['tests'][self.id()] = time.time() - self._start_time
        self._start_time = time.time()
        if hasattr(self, 'after'):
            if not asyncio.iscoroutinefunction(self.after):
                self.loop.run_until_complete(asyncio.coroutine(self.after)())
            else:
                self.loop.run_until_complete(self.after())
        self.loop.stop()
        self.loop.close()
        _times['teardown'].append(time.time() - self._start_time)

    def decorate(self, fn):
        def wrapper(*args, **kwargs):
            try:
                return self.loop.run_until_complete(asyncio.wait_for(
                    fn(*args, **kwargs), self.TIMEOUT
                ))
            except asyncio.TimeoutError as e:
                pass
            # hack to not get "during handling of exception, an other..."
            self.fail(f'Timeout ({self.TIMEOUT}s): {fn}')
        return wrapper

    async def eventually(self, fn, value, x=10, wait=0.01):
        """Tests x times if the attribute is equal to value, awaiting a certain
        amount of time.
        """
        for _ in range(x):
            if await asyncio.coroutine(fn)() == value:
                return True
            await asyncio.sleep(wait)
        self.fail(f"Function {fn} did not return {value!r} after {x * wait}s")

    def __getattribute__(self, name):
        attr = object.__getattribute__(self, name)
        if asyncio.iscoroutinefunction(attr):
            if name.startswith('test_'):
                # return self.decorate(attr)
                if name not in self._func_cache:
                    self._func_cache[name] = self.decorate(attr)
                return self._func_cache[name]
        return attr

