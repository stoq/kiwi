#
# Kiwi: a Framework and Enhanced Widgets for Python
#
# Copyright (C) 2005 Async Open Source
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# Author(s): Johan Dahlin <jdahlin@async.com.br>
#

import gettext

import atk
import gtk

__all__ = ['error', 'info', 'messagedialog', 'warning', 'yesno']

_ = gettext.gettext

_IMAGE_TYPES = {
    gtk.MESSAGE_INFO: gtk.STOCK_DIALOG_INFO,
    gtk.MESSAGE_WARNING : gtk.STOCK_DIALOG_WARNING,
    gtk.MESSAGE_QUESTION : gtk.STOCK_DIALOG_QUESTION,
    gtk.MESSAGE_ERROR : gtk.STOCK_DIALOG_ERROR,
}

_BUTTON_TYPES = {
    gtk.BUTTONS_NONE: (),
    gtk.BUTTONS_OK: (gtk.STOCK_OK, gtk.RESPONSE_OK,),
    gtk.BUTTONS_CLOSE: (gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE,),
    gtk.BUTTONS_CANCEL: (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,),
    gtk.BUTTONS_YES_NO: (gtk.STOCK_NO, gtk.RESPONSE_NO,
                         gtk.STOCK_YES, gtk.RESPONSE_YES),
    gtk.BUTTONS_OK_CANCEL: (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                            gtk.STOCK_OK, gtk.RESPONSE_OK)
    }

class HIGDialog(gtk.Dialog):
    def __init__(self, parent, flags,
                 type=gtk.MESSAGE_INFO, buttons=gtk.BUTTONS_NONE):
        if not type in _IMAGE_TYPES:
            raise TypeError(
                "type must be one of: %s", ', '.join(_IMAGE_TYPES.keys()))
        if not buttons in _BUTTON_TYPES:
            raise TypeError(
                "buttons be one of: %s", ', '.join(_BUTTON_TYPES.keys()))

        gtk.Dialog.__init__(self, '', parent, flags)
	self.set_border_width(5)
	self.set_resizable(False)
	self.set_has_separator(False)
	self.set_title("")
	self.set_skip_taskbar_hint(True)
	self.vbox.set_spacing(14)
	self.get_accessible().set_role(atk.ROLE_ALERT)

	self._primary_label = gtk.Label()
	self._secondary_label = gtk.Label()
	self._details_label = gtk.Label()
	self._image = gtk.image_new_from_stock(_IMAGE_TYPES[type],
                                               gtk.ICON_SIZE_DIALOG)
	self._image.set_alignment(0.5, 0.0)

	self._primary_label.set_use_markup(True)
        for label in (self._primary_label, self._secondary_label,
                      self._details_label):
            label.set_line_wrap(True)
            label.set_selectable(True)
            label.set_alignment(0.0, 0.5)

        hbox = gtk.HBox(False, 12)
        hbox.set_border_width(5)
        hbox.pack_start(self._image, False, False)

	vbox = gtk.VBox(False, 0)
        hbox.pack_start(vbox, False, False)
        vbox.pack_start(self._primary_label, False, False)
        vbox.pack_start(self._secondary_label, False, False)

	self._expander = gtk.expander_new_with_mnemonic(_("Show more _details"))
        self._expander.set_spacing(6)
        self._expander.add(self._details_label)
        vbox.pack_start(self._expander, False, False)
        self.vbox.pack_start(hbox, False, False)
        hbox.show_all()
        self._expander.hide()
        self.add_buttons(*_BUTTON_TYPES[buttons])

    def set_primary(self, text):
        self._primary_label.set_markup("<span weight=\"bold\" size=\"larger\">%s</span>" % text)

    def set_details(self, text):
        self._details_label.set_text(text)
        self._expander.show()

    def set_details_widget(self, widget):
        self._expander.remove(self._details_label)
        self._expander.add(widget)
        widget.show()
        self._expander.show()

def messagedialog(dialog_type, short, long=None, parent=None,
                  buttons=gtk.BUTTONS_OK, default=-1):
    """Create and show a MessageDialog.

    @param dialog_type: one of constants
      - gtk.MESSAGE_INFO
      - gtk.MESSAGE_WARNING
      - gtk.MESSAGE_QUESTION
      - gtk.MESSAGE_ERROR
    @param short:       A header text to be inserted in the dialog.
    @param long:        A long description of message.
    @param parent:      The parent widget of this dialog
    @type parent:       a gtk.Window subclass
    @param buttons:     The button type that the dialog will be display,
      one of the constants:
       - gtk.BUTTONS_NONE
       - gtk.BUTTONS_OK
       - gtk.BUTTONS_CLOSE
       - gtk.BUTTONS_CANCEL
       - gtk.BUTTONS_YES_NO
       - gtk.BUTTONS_OK_CANCEL
      or a tuple or 2-sized tuples representing label and response. If label
      is a stock-id a stock icon will be displayed.
    @param default: optional default response id
    """
    if buttons in (gtk.BUTTONS_NONE, gtk.BUTTONS_OK, gtk.BUTTONS_CLOSE,
                   gtk.BUTTONS_CANCEL, gtk.BUTTONS_YES_NO,
                   gtk.BUTTONS_OK_CANCEL):
        dialog_buttons = buttons
        buttons = []
    else:
        if type(buttons) != tuple:
            raise TypeError(
                "buttons must be a GtkButtonsTypes constant or a tuple")
        dialog_buttons = gtk.BUTTONS_NONE

    if parent and not isinstance(parent, gtk.Window):
        raise TypeError("parent must be a gtk.Window subclass")

    d = HIGDialog(parent=parent, flags=gtk.DIALOG_MODAL,
                  type=dialog_type, buttons=dialog_buttons)
    for text, response in buttons:
        d.add_buttons(text, response)

    d.set_primary(short)

    if long:
        if isinstance(long, gtk.Widget):
            d.set_details_widget(long)
        elif isinstance(long, basestring):
            d.set_details(long)
        else:
            raise TypeError("long must be a gtk.Widget or a string")

    if default != -1:
        d.set_default_response(default)

    if parent:
        d.set_transient_for(parent)
        d.set_modal(True)

    response = d.run()
    d.destroy()
    return response

def _simple(type, short, long=None, parent=None, buttons=gtk.BUTTONS_OK,
          default=-1):
    if buttons == gtk.BUTTONS_OK:
        default = gtk.RESPONSE_OK
    return messagedialog(type, short, long,
                         parent=parent, buttons=buttons,
                         default=default)

def error(short, long=None, parent=None, buttons=gtk.BUTTONS_OK, default=-1):
    return _simple(gtk.MESSAGE_ERROR, short, long, parent=parent,
                   buttons=buttons, default=default)

def info(short, long=None, parent=None, buttons=gtk.BUTTONS_OK, default=-1):
    return _simple(gtk.MESSAGE_INFO, short, long, parent=parent,
                   buttons=buttons, default=default)

def warning(short, long=None, parent=None, buttons=gtk.BUTTONS_OK, default=-1):
    return _simple(gtk.MESSAGE_WARNING, short, long, parent=parent,
                   buttons=buttons, default=default)

def yesno(text, parent=None, default=gtk.RESPONSE_YES):
    return messagedialog(gtk.MESSAGE_WARNING, text, None, parent,
                         buttons=gtk.BUTTONS_YES_NO,
                         default=default)

def _test():
     yesno('Kill?', default=gtk.RESPONSE_NO)

     info('Some information displayed not too long\nbut not too short',
          long=('foobar ba asdjaiosjd oiadjoisjaoi aksjdasdasd kajsdhakjsdh\n'
                'askdjhaskjdha skjdhasdasdjkasldj alksdjalksjda lksdjalksdj\n'
                'asdjaslkdj alksdj lkasjdlkjasldkj alksjdlkasjdlkasjdlka jklsdjakls\n'
                'ask;ldjaklsjdlkasjd alksdj laksjdlkasjd lkajs lkjdl kjaslk jkl\n'),
          default=gtk.RESPONSE_OK,
          )

     error('An error occurred', gtk.Button('Woho'))
     error('Unable to mount the selected volume.',
           'mount: can\'t find /media/cdrom0 in /etc/fstab or /etc/mtab')

if __name__ == '__main__':
    _test()
