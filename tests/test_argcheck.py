import datetime
import unittest

from kiwi.argcheck import argcheck, number, percent
from kiwi.datatypes import Decimal

class ArgTest(unittest.TestCase):
    def testOneArg(self):
        f = argcheck(str)(lambda s: None)
        f('str')
        self.assertRaises(TypeError, f, None)
        self.assertRaises(TypeError, f, 1)

    def testTwoArgs(self):
        f = argcheck(str, int)(lambda s, i: None)
        f('str', 1)
        self.assertRaises(TypeError, f, 1, 1)         # first incorret
        self.assertRaises(TypeError, f, 'str', 'str') # second incorrect
        self.assertRaises(TypeError, f, 1, 'str')     # swapped
        self.assertRaises(TypeError, f, 1)            # too few
        self.assertRaises(TypeError, f, 'str', 1, 1)  # too many

    def testVarArgs(self):
        f = argcheck(int)(lambda *v: None)
        f(1)
        f(1, 'str')
        f(1, 2, 3)
        #self.assertRaises(TypeError, f, 'str')

    def testDefault(self):
        f1 = lambda a, b=1: None
        d1 = argcheck(int, int)(f1)
        self.assertRaises(TypeError, d1, 'f')

        f2 = lambda a, b='str': None
        self.assertRaises(TypeError, argcheck, f2)

    def testKwargs(self):
        self.assertRaises(TypeError, argcheck, lambda **kw: None)

    def testUserDefined(self):
        class Payment(object):
            pass

        def pay(payment, description):
            pass
        pay = argcheck(Payment, str)(pay)
        pay(Payment(), 'foo')
        self.assertRaises(TypeError, 'bar', 'bar')
        self.assertRaises(TypeError, Payment(), Payment())

    def testClass(self):
        class Custom(object):
            pass

        class Test:
            def method1(self, foo, bar):
                return foo + bar
            method1 = argcheck(int, int)(method1)

            def method2(self, a, b, c, d, e, f, g=0.0):
                return g
            method2 = argcheck(Custom, int, datetime.datetime,
                               int, int, float, float)(method2)

            def method3(self, s, date=None, date2=None):
                return
            method3 = argcheck(str, datetime.datetime,
                               datetime.datetime)(method3)

            def method4(self, n):
                return n
            method4 = argcheck(percent)(method4)

        t = Test()
        self.assertEqual(t.method1(1, 2), 3)
        self.assertRaises(TypeError, t.method1, None, None)
        self.assertEqual(t.method2(Custom(), 2, datetime.datetime.now(),
                                   4, 5, 6.0), 0.0)

        t.method3('foo')
        t.method3('bar', None)
        t.method3('baz', None, None)
        t.method3(s='foo')
        t.method3(s='bar', date=None)
        t.method3(s='baz', date=None, date2=None)
        t.method4(n=0)
        t.method4(n=50)
        t.method4(n=100)
        self.assertRaises(TypeError, t.method3, 'noggie', True)
        self.assertRaises(TypeError, t.method3, 'boogie', None, True)
        self.assertRaises(TypeError, t.method3, s='noggie', date2=True)
        self.assertRaises(TypeError, t.method3, s='boogie',
                          date=None, date2=True)
        self.assertRaises(ValueError, t.method4, -1)
        self.assertRaises(ValueError, t.method4, 101)

    def testNone(self):
        def func_none(date=None):
            return date
        func_none = argcheck(datetime.datetime)(func_none)
        func_none()
        func_none(None)
        self.assertRaises(TypeError, func_none, True)
        self.assertRaises(TypeError, func_none, date=True)

        def func_none2(s, date=None, date2=None):
            return date
        func_none2 = argcheck(str, datetime.datetime,
                              datetime.datetime)(func_none2)
        func_none2('foo')
        func_none2('bar', None)
        func_none2('baz', None, None)
        func_none2(s='foo')
        func_none2(s='bar', date=None)
        func_none2(s='baz', date=None, date2=None)
        self.assertRaises(TypeError, func_none2, 'noggie', True)
        self.assertRaises(TypeError, func_none2, 'boogie', None, True)
        self.assertRaises(TypeError, func_none2, s='noggie', date2=True)
        self.assertRaises(TypeError, func_none2, s='boogie',
                          date=None, date2=True)


    def testNumber(self):
        def func(n):
            return n
        func = argcheck(number)(func)
        self.assertEqual(func(0), 0)
        self.assertEqual(func(0L), 0L)
        self.assertEqual(func(0.0), 0.0)
        self.assertEqual(func(Decimal(0)), Decimal(0))

    def testPercent(self):
        def func(n):
            return n
        func = argcheck(percent)(func)
        self.assertEqual(func(50), 50)
        self.assertEqual(func(50L), 50L)
        self.assertEqual(func(50.0), 50.0)
        self.assertEqual(func(Decimal(50)), Decimal(50))
        self.assertRaises(ValueError, func, -1)
        self.assertRaises(ValueError, func, -1L)
        self.assertRaises(ValueError, func, -1.0)
        self.assertRaises(ValueError, func, Decimal(-1))
        self.assertRaises(ValueError, func, 101)
        self.assertRaises(ValueError, func, 101L)
        self.assertRaises(ValueError, func, 101.0)
        self.assertRaises(ValueError, func, Decimal(101))

    def testDisable(self):
        argcheck.disable()
        def func(s):
            pass
        func = argcheck(str)(func)
        func(10)
        argcheck.enable()

    def testErrorHandling(self):
        self.assertRaises(TypeError, argcheck(str), True)
        self.assertRaises(TypeError, argcheck(int), lambda **x: None)
        self.assertRaises(TypeError, argcheck(int), lambda : None)
        self.assertRaises(TypeError, argcheck(int), lambda x='str': None)

if __name__ == '__main__':
    unittest.main()
