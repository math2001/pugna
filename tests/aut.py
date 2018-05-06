import asyncio
import unittest

__all__ = ["Aut"]

class Aut(unittest.TestCase):

    """Asynchrone Unit Test.

    Quick and dirty, but works pretty well.
    Based on https://stackoverflow.com/a/37888085/6164984

    !! use set_up and tear_down instead of setUp and tearDown !!
    """

    # timeout for every tests in seconds
    TIMEOUT = 1

    def __init__(self, *args, **kwargs):
        self._func_cache = {}
        super().__init__(*args, **kwargs)

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(asyncio.coroutine(getattr(self, 'before',
                                                               lambda: None))())

    def tearDown(self):
        self.loop.run_until_complete(asyncio.coroutine(getattr(self, 'after',
                                                               lambda: None))())
        self.loop.stop()
        self.loop.close()

    def decorate(self, fn):
        def wrapper(*args, **kwargs):
            return self.loop.run_until_complete(asyncio.wait_for(
                fn(*args, **kwargs), self.TIMEOUT))
        return wrapper

    async def eventually(self, fn, value, x=10, wait=0.1):
        """Tests x times if the attribute is equal to value, awaiting a certain
        amount of time.
        """
        for _ in range(x):
            if await asyncio.coroutine(fn)() == value:
                return True
            await asyncio.sleep(wait)
        self.fail(f"{obj.__class__.__name__!r} attribute {attr!r} hasn't been "
                  f"set to {value!r} after {x * wait}s. Got "
                  f"{getattr(obj, attr, None)!r}")

    def __getattribute__(self, name):
        attr = object.__getattribute__(self, name)
        if asyncio.iscoroutinefunction(attr):
            if name.startswith('test_'):
                if name not in self._func_cache:
                    self._func_cache[name] = self.decorate(attr)
                return self._func_cache[name]
        return attr

async def hello():
    return 'hello'

async def bonjour():
    return 'bonjour'

class TestSomething(Aut):

    async def set_up(self):
        self.computed = await hello()

    async def tear_down(self):
        del self.computed

    async def test_hello(self):
        self.assertEqual(await hello(), 'hello')
        self.assertEqual(self.computed, 'hello')

    async def test_bonjour(self):
        self.assertEqual(await bonjour(), 'bonjour')

if __name__ == "__main__":
    unittest.main()