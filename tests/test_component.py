import unittest

from kiwi.component import AlreadyImplementedError, Interface, \
     get_utility, provide_utility, remove_utility, implements, utilities

class IBanana(Interface):
    pass

class Obj(object): pass
o = Obj()

class TestUtilities(unittest.TestCase):
    def tearDown(self):
        utilities.clean()

    def testGet(self):
        self.assertEqual(None, get_utility(IBanana, None))
        provide_utility(IBanana, o)
        self.assertRaises(TypeError, get_utility, object)
        self.assertEqual(get_utility(IBanana), o)

    def testProvide(self):
        self.assertRaises(NotImplementedError, get_utility, IBanana)
        provide_utility(IBanana, o)
        self.assertRaises(TypeError, provide_utility, object, o)

    def testRemove(self):
        self.assertRaises(NotImplementedError, remove_utility, IBanana)
        provide_utility(IBanana, o)
        self.assertEqual(remove_utility(IBanana), o)
        self.assertRaises(NotImplementedError, remove_utility, IBanana)

    def testAlreadyImplemented(self):
        self.assertRaises(NotImplementedError, get_utility, IBanana)
        provide_utility(IBanana, o)
        self.assertRaises(AlreadyImplementedError,
                          provide_utility, IBanana, o)

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

    def testImplements(self):
        class I1(Interface):
            pass
        class C(object):
            implements(I1)
        c = C()
        class X(object):
            pass
        x = X()
        self.assertEqual(I1.providedBy(x), False)
        #self.assertEqual(I1.providedBy(C), False)
        self.assertEqual(I1.providedBy(c), True)

    def testInterfaceSub(self):
        class I1(Interface):
            pass
        class I2(I1):
            pass
        class C(object):
            implements(I2)
        class D(object):
            implements(I1)
        c = C()
        self.assertEqual(I1.providedBy(c), True)
        self.assertEqual(I2.providedBy(c), True)
        d = D()
        self.assertEqual(I1.providedBy(d), True)
        self.assertEqual(I2.providedBy(d), False)

    def testZImplements(self):
        try:
            from zope.interface import Interface, implements
        except ImportError:
            return

        class I1(Interface):
            pass
        class C(object):
            implements(I1)
        c = C()
        class X(object):
            pass
        x = X()
        self.assertEqual(I1.providedBy(x), False)
        self.assertEqual(I1.providedBy(C), False)
        self.assertEqual(I1.providedBy(c), True)

    def testZInterfaceSub(self):
        try:
            from zope.interface import Interface, implements
        except ImportError:
            return

        class I1(Interface):
            pass
        class I2(I1):
            pass
        class C(object):
            implements(I2)
        class D(object):
            implements(I1)
        c = C()
        self.assertEqual(I1.providedBy(c), True)
        self.assertEqual(I2.providedBy(c), True)
        d = D()
        self.assertEqual(I1.providedBy(d), True)
        self.assertEqual(I2.providedBy(d), False)

if __name__ == '__main__':
    unittest.main()
