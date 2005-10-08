import datetime
import unittest

from kiwi.argcheck import argcheck, number, percent

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
    
        @argcheck(Payment, str)
        def pay(payment, description):
            pass
        pay(Payment(), 'foo')
        self.assertRaises(TypeError, 'bar', 'bar')
        self.assertRaises(TypeError, Payment(), Payment())
        
    def testClass(self):
        class Custom(object):
            pass
        
        class Test:
            @argcheck(int, int)
            def method1(self, foo, bar):
                return foo + bar
            
            @argcheck(Custom, int, datetime.datetime, int, int,
                      float, float)
            def method2(self, a, b, c, d, e, f, g=0.0):
                return g

        t = Test()
        self.assertEqual(t.method1(1, 2), 3)
        self.assertRaises(TypeError, t.method1, None, None)
        self.assertEqual(t.method2(Custom(), 2, datetime.datetime.now(),
                                   4, 5, 6.0), 0.0)
        
if __name__ == '__main__':
    unittest.main()
