# encoding: iso-8859-1
from gi.repository import Gtk, Gio

from kiwi.datatypes import ValidationError
from kiwi.ui.widgets.combo import ProxyComboEntry
from kiwi.ui.delegates import GladeDelegate, SlaveDelegate


class Dialog(GladeDelegate):
    def __init__(self):
        GladeDelegate.__init__(self, gladefile='lang.ui',
                               delete_handler=self.quit_if_last)
        self.register_validate_function(self.validity)
        hb = Gtk.HeaderBar()
        hb.set_title('Foobar')
        hb.set_show_close_button(True)

        button = Gtk.Button()
        icon = Gio.ThemedIcon(name="mail-send-receive-symbolic")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        button.add(image)
        hb.pack_end(button)

        self.toplevel.set_titlebar(hb)

    def validity(self, data):
        self.ok_button.set_sensitive(data)

    def on_ok_button__clicked(self, button):
        raise SystemExit


class English(SlaveDelegate):
    def __init__(self):
        box = Gtk.HBox(spacing=6)
        box.set_border_width(6)
        box.show()

        label = Gtk.Label(label="Number:")
        label.show()
        box.pack_start(label, False, False, 0)

        combo = ProxyComboEntry()
        combo.set_property('model-attribute', 'number')
        combo.set_property('data-type', 'str')
        combo.prefill(['One', 'Two', 'Three'])
        combo.show()
        box.pack_start(combo, True, True, 0)
        self.combo = combo

        SlaveDelegate.__init__(self, toplevel=box, widgets=['combo'])

    def on_combo__validate(self, widget, data):
        if data != 'Two':
            return ValidationError("foo")


class Swedish(SlaveDelegate):
    def __init__(self):
        box = Gtk.HBox(spacing=6)
        box.set_border_width(6)
        box.show()

        label = Gtk.Label(label="Nummer:")
        label.show()
        box.pack_start(label, False, False, 0)

        combo = ProxyComboEntry()
        combo.set_property('model-attribute', 'nummer')
        combo.set_property('data-type', 'str')
        combo.prefill(['Ett', 'Två', 'Tre'])
        combo.show()
        box.pack_start(combo, True, True, 0)
        self.combo = combo

        SlaveDelegate.__init__(self, toplevel=box, widgets=['combo'])

    def on_combo__validate(self, widget, data):
        if data != 'Tre':
            return ValidationError("bar")


class EnglishModel:
    pass


class SwedishModel:
    # Sylvia Saint?
    pass

dialog = Dialog()

# English
babe = EnglishModel()
babe.number = 'One'

eng = English()
eng.show()
dialog.attach_slave("english", eng)
eng.add_proxy(babe, ['combo'])

# Swedish part
brud = SwedishModel()
brud.nummer = 'Ett'

swe = Swedish()
swe.show()
dialog.attach_slave("swedish", swe)
swe.add_proxy(brud, ['combo'])
dialog.show_all()

Gtk.main()
