import unittest

import gobject
import gtk
from gazpacho.loader.loader import ObjectBuilder

import kiwi.ui.gazpacholoader
kiwi

def glade(s):
    return '<glade-interface>%s</glade-interface>' % s

class TestGazpachoLoader(unittest.TestCase):
    def testConstruct(self):
        objs = (("kiwi+ui+widgets+list+List", "w1"),
                ("ObjectList", "w2"),
                ("kiwi+ui+widgets+combobox+ComboBox", "w3"),
                ("ProxyComboBox", "w4"),
                ("kiwi+ui+widgets+combobox+ComboBoxEntry", "w5"),
                ("ProxyComboBoxEntry", "w6"))
        s = ''

        for obj, name in objs:
            s += '<widget class="%s" id="%s"/>\n' % (obj, name)
        ob = ObjectBuilder(buffer=glade(s))
        for obj, name in objs:
            widget = ob.get_widget(name)
            self.failUnless(isinstance(widget, gtk.Widget))
            gtype = gobject.type_from_name(obj)
            self.failUnless(gobject.type_is_a(gtype, gtk.Widget))
            self.failUnless(gobject.type_is_a(gtype, widget))

if __name__ == '__main__':
    unittest.main()
