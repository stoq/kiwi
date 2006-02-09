import unittest

from kiwi.component import AlreadyImplementedError, Interface, \
     get_utility, provide_utility

class IBanana(Interface):
    pass

class Obj(object): pass
o = Obj()

class TestUtilities(unittest.TestCase):
    def tearDown(self):
        # Yey, yey
        from kiwi.component import _handler
        del _handler._utilities[IBanana]

    def testGet(self):
        provide_utility(IBanana, o)
        self.assertRaises(TypeError, get_utility, object)
        self.assertEqual(get_utility(IBanana), o)

    def testProvide(self):
        self.assertRaises(NotImplementedError, get_utility, IBanana)
        provide_utility(IBanana, o)
        self.assertRaises(TypeError, provide_utility, object, o)

    def testAlreadyImplemented(self):
        self.assertRaises(NotImplementedError, get_utility, IBanana)
        provide_utility(IBanana, o)
        self.assertRaises(AlreadyImplementedError,
                          provide_utility, IBanana, o)

if __name__ == '__main__':
    unittest.main()
