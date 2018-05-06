import asyncio
import unittest

__all__ = ["Aut"]

class Aut(unittest.TestCase):

    """Asynchrone Unit Test.

    Quick and dirty, but works pretty well.
    Based on https://stackoverflow.com/a/37888085/6164984

    !! use set_up and tear_down instead of setUp and tearDown !!
    """

    def __init__(self, *args, **kwargs):
        self._func_cache = {}
        super().__init__(*args, **kwargs)

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(asyncio.coroutine(getattr(self, 'set_up', lambda: None))())

    def tearDown(self):
        self.loop.run_until_complete(asyncio.coroutine(getattr(self, 'tear_down', lambda: None))())
        self.loop.stop()
        self.loop.close()

    def decorate(self, fn):
        def wrapper(*args, **kwargs):
            return self.loop.run_until_complete(fn(*args, **kwargs))
        return wrapper


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
