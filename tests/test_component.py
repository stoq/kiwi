import unittest

from kiwi.component import AlreadyImplementedError, Interface, \
     get_utility, provide_utility

class IBanana(Interface):
    pass

class Obj(object): pass
o = Obj()

class TestUtilities(unittest.TestCase):
    def _clear(self, iface):
        # Yey, yey
        from kiwi.component import _handler
        del _handler._utilities[iface]

    def testGet(self):
        provide_utility(IBanana, o)
        self.assertRaises(TypeError, get_utility, object)
        self.assertEqual(get_utility(IBanana), o)
        self._clear(IBanana)

    def testProvide(self):
        self.assertRaises(NotImplementedError, get_utility, IBanana)
        provide_utility(IBanana, o)
        self.assertRaises(TypeError, provide_utility, object, o)
        self._clear(IBanana)

    def testAlreadyImplemented(self):
        self.assertRaises(NotImplementedError, get_utility, IBanana)
        provide_utility(IBanana, o)
        self.assertRaises(AlreadyImplementedError,
                          provide_utility, IBanana, o)
        self._clear(IBanana)

    def testZopeInterface(self):
        try:
            from zope.interface import Interface
        except ImportError:
            return

        class IApple(Interface):
            pass

        self.assertRaises(NotImplementedError, get_utility, IApple)
        provide_utility(IApple, o)
        self.assertRaises(AlreadyImplementedError,
                          provide_utility, IApple, o)
        self._clear(IApple)

if __name__ == '__main__':
    unittest.main()
