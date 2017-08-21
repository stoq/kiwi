#
# Kiwi: a Framework and Enhanced Widgets for Python
#
# Copyright (C) 2005-2012 Async Open Source
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


import contextlib
import os
import gettext

from gi.repository import Atk, Gtk, GLib

__all__ = ['error', 'info', 'messagedialog', 'warning', 'yesno', 'save',
           'selectfile', 'selectfolder', 'HIGAlertDialog', 'BaseDialog',
           'ask_overwrite']

_ = lambda m: gettext.dgettext('kiwi', m)

_IMAGE_TYPES = {
    Gtk.MessageType.INFO: Gtk.STOCK_DIALOG_INFO,
    Gtk.MessageType.WARNING: Gtk.STOCK_DIALOG_WARNING,
    Gtk.MessageType.QUESTION: Gtk.STOCK_DIALOG_QUESTION,
    Gtk.MessageType.ERROR: Gtk.STOCK_DIALOG_ERROR,
}

_BUTTON_TYPES = {
    Gtk.ButtonsType.NONE: (),
    Gtk.ButtonsType.OK: (Gtk.STOCK_OK, Gtk.ResponseType.OK,),
    Gtk.ButtonsType.CLOSE: (Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE,),
    Gtk.ButtonsType.CANCEL: (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,),
    Gtk.ButtonsType.YES_NO: (Gtk.STOCK_NO, Gtk.ResponseType.NO,
                             Gtk.STOCK_YES, Gtk.ResponseType.YES),
    Gtk.ButtonsType.OK_CANCEL: (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                Gtk.STOCK_OK, Gtk.ResponseType.OK)
}


class HIGAlertDialog(Gtk.Dialog):
    def __init__(self, parent, flags,
                 type=Gtk.MessageType.INFO, buttons=Gtk.ButtonsType.NONE):
        if not type in _IMAGE_TYPES:
            raise TypeError(
                "type must be one of: %s", ', '.join(_IMAGE_TYPES.keys()))
        if not buttons in _BUTTON_TYPES:
            raise TypeError(
                "buttons be one of: %s", ', '.join(_BUTTON_TYPES.keys()))

        super(HIGAlertDialog, self).__init__('', parent, flags)

        self.set_deletable(False)
        self.set_border_width(5)
        self.set_resizable(False)
        # Some window managers (ION) displays a default title (???) if
        # the specified one is empty, workaround this by setting it
        # to a single space instead
        self.set_title(" ")
        self.set_skip_taskbar_hint(True)

        # It seems like get_accessible is not available on windows, go figure
        if hasattr(self, 'get_accessible'):
            self.get_accessible().set_role(Atk.Role.ALERT)

        self._primary_label = Gtk.Label()
        self._secondary_label = Gtk.Label()
        self._details_label = Gtk.Label()
        self._image = Gtk.Image.new_from_stock(_IMAGE_TYPES[type],
                                               Gtk.IconSize.DIALOG)
        self._image.set_alignment(0.5, 0.0)

        self._primary_label.set_use_markup(True)
        for label in (self._primary_label, self._secondary_label,
                      self._details_label):
            label.set_line_wrap(True)
            label.set_selectable(True)
            label.set_alignment(0.0, 0.5)
            label.set_max_width_chars(80)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        hbox.set_border_width(5)
        hbox.pack_start(self._image, False, False, 0)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        hbox.pack_start(vbox, True, True, 0)
        vbox.pack_start(self._primary_label, False, False, 0)
        vbox.pack_start(self._secondary_label, False, False, 0)
        self.main_vbox = vbox

        self._expander = Gtk.Expander.new_with_mnemonic(
            _("Show more _details"))
        self._expander.set_spacing(6)
        self._expander.add(self._details_label)
        vbox.pack_start(self._expander, False, False, 0)
        self.get_content_area().pack_start(hbox, True, True, 0)
        hbox.show_all()
        self._expander.hide()
        self.add_buttons(*_BUTTON_TYPES[buttons])
        self.label_vbox = vbox

    def set_primary(self, text, bold=True):
        if bold:
            text = "<span weight=\"bold\" size=\"larger\">%s</span>" % (
                GLib.markup_escape_text(text))
        self._primary_label.set_markup(text)

    def set_secondary(self, text):
        self._secondary_label.set_markup(text)

    def set_details_label(self, label):
        self._expander.set_label(label)

    def set_details(self, text, use_markup=False):
        if use_markup:
            self._details_label.set_markup(GLib.markup_escape_text(text))
        else:
            self._details_label.set_text(text)
        self._expander.show()

    def set_details_widget(self, widget):
        self._expander.remove(self._details_label)
        self._expander.add(widget)
        widget.show()
        self._expander.show()


class BaseDialog(Gtk.Dialog):
    def __init__(self, parent=None, title='', flags=0, buttons=()):
        if parent and not isinstance(parent, (Gtk.Window, Gtk.Dialog)):
            raise TypeError("parent needs to be None or a Gtk.Window subclass")

        if not flags and parent:
            flags &= (Gtk.DialogFlags.MODAL |
                      Gtk.DialogFlags.DESTROY_WITH_PARENT)

        super(BaseDialog, self).__init__(
            title=title, parent=parent, flags=flags, buttons=buttons)

        self.set_border_width(6)
        self.set_has_separator(False)
        self.vbox.set_spacing(6)


def messagedialog(dialog_type, short, description=None, parent=None,
                  buttons=Gtk.ButtonsType.OK, default=-1, bold=True):
    """Create and show a MessageDialog.

    :param dialog_type: one of constants
      - Gtk.MessageType.INFO
      - Gtk.MessageType.WARNING
      - Gtk.MessageType.QUESTION
      - Gtk.MessageType.ERROR
    :param short:       A header text to be inserted in the dialog.
    :param description: A long description of message.
    :param parent:      The parent widget of this dialog
    :type parent:       a Gtk.Window subclass
    :param buttons:     The button type that the dialog will be display,
      one of the constants:
       - Gtk.ButtonsType.NONE
       - Gtk.ButtonsType.OK
       - Gtk.ButtonsType.CLOSE
       - Gtk.ButtonsType.CANCEL
       - Gtk.ButtonsType.YES_NO
       - Gtk.ButtonsType.OK_CANCEL
      or a tuple or 2-sized tuples representing label and response. If label
      is a stock-id a stock icon will be displayed.
    :param default: optional default response id
    :param bold: If the short message should be formatted to bold
    """
    if buttons in (Gtk.ButtonsType.NONE, Gtk.ButtonsType.OK, Gtk.ButtonsType.CLOSE,
                   Gtk.ButtonsType.CANCEL, Gtk.ButtonsType.YES_NO,
                   Gtk.ButtonsType.OK_CANCEL):
        dialog_buttons = buttons
        buttons = []
    else:
        if buttons is not None and not isinstance(buttons, tuple):
            raise TypeError(
                "buttons must be a GtkButtonsTypes constant or a tuple")
        dialog_buttons = Gtk.ButtonsType.NONE

    if parent and not isinstance(parent, (Gtk.Window, Gtk.Dialog)):
        raise TypeError("parent must be a Gtk.Window subclass")

    d = HIGAlertDialog(parent=parent, flags=Gtk.DialogFlags.MODAL,
                       type=dialog_type, buttons=dialog_buttons)
    if buttons:
        for text, response in buttons:
            d.add_buttons(text, response)

    d.set_primary(short, bold=bold)

    if description:
        if isinstance(description, Gtk.Widget):
            d.set_details_widget(description)
        elif isinstance(description, str):
            d.set_details(description)
        else:
            raise TypeError(
                "description must be a Gtk.Widget or a string, not %r" % description)

    if default != -1:
        d.set_default_response(default)

    if parent:
        d.set_transient_for(parent)
        d.set_modal(True)

    response = d.run()
    d.destroy()
    return response


def _simple(type, short, description=None, parent=None, buttons=Gtk.ButtonsType.OK,
            default=-1):
    if buttons == Gtk.ButtonsType.OK:
        default = Gtk.ResponseType.OK
    return messagedialog(type, short, description,
                         parent=parent, buttons=buttons,
                         default=default)


def error(short, description=None, parent=None, buttons=Gtk.ButtonsType.OK, default=-1):
    return _simple(Gtk.MessageType.ERROR, short, description, parent=parent,
                   buttons=buttons, default=default)


def info(short, description=None, parent=None, buttons=Gtk.ButtonsType.OK, default=-1):
    return _simple(Gtk.MessageType.INFO, short, description, parent=parent,
                   buttons=buttons, default=default)


def warning(short, description=None, parent=None, buttons=Gtk.ButtonsType.OK, default=-1):
    return _simple(Gtk.MessageType.WARNING, short, description, parent=parent,
                   buttons=buttons, default=default)


def yesno(text, parent=None, default=Gtk.ResponseType.YES,
          buttons=Gtk.ButtonsType.YES_NO):
    return messagedialog(Gtk.MessageType.WARNING, text, None, parent,
                         buttons=buttons, default=default)


@contextlib.contextmanager
def selectfile(title='', parent=None, folder=None, filters=None):
    """Creates and returns a Gtk.FileChooserDialog.

    To run the dialog, the user apps should do:

        >>> with selectfile() as sf:
        ...     response = sf.run()
        ...     if response != Gtk.ResponseType.OK:
        ...         return
        ...     filename = sf.get_filename()

    :param title: the title of the folder, defaults to 'Select file'
    :param parent: parent Gtk.Window (defaults to ``None``)
    :param folder: initial folder (defaults to ``None``, which open current
      folder)
    :param filters: a list of filters to use, is incompatible with patterns"""

    filechooser = Gtk.FileChooserDialog(title or _('Select file'),
                                        parent,
                                        Gtk.FileChooserAction.OPEN,
                                        (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                         Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

    if filters is None:
        filters = []
    for f in filters:
        filechooser.add_filter(f)

    if folder:
        filechooser.set_current_folder(folder)

    filechooser.set_default_response(Gtk.ResponseType.OK)

    try:
        yield filechooser
    finally:
        filechooser.destroy()


def selectfolder(title='', parent=None, folder=None):
    """Displays a select folder dialog.
    :param title: the title of the folder, defaults to 'Select folder'
    :param parent: parent Gtk.Window or None
    :param folder: initial folder or None
    """

    filechooser = Gtk.FileChooserDialog(
        title or _('Select folder'),
        parent,
        Gtk.FileChooserAction.SELECT_FOLDER,
        (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
         Gtk.STOCK_OK, Gtk.ResponseType.OK))

    if folder:
        filechooser.set_current_folder(folder)

    filechooser.set_default_response(Gtk.ResponseType.OK)

    response = filechooser.run()
    if response != Gtk.ResponseType.OK:
        filechooser.destroy()
        return

    path = filechooser.get_filename()
    if path and os.access(path, os.R_OK | os.X_OK):
        filechooser.destroy()
        return path

    abspath = os.path.abspath(path)

    error(_('Could not select folder "%s"') % abspath,
          _('The folder "%s" could not be selected. '
            'Permission denied.') % abspath)

    filechooser.destroy()
    return


def ask_overwrite(filename, parent=None):
    submsg1 = _('A file named "%s" already exists') % os.path.abspath(filename)
    submsg2 = _('Do you wish to replace it with the current one?')
    text = ('<span weight="bold" size="larger">%s</span>\n\n%s\n'
            % (submsg1, submsg2))
    result = messagedialog(Gtk.MessageType.ERROR, text, parent=parent,
                           bold=False,
                           buttons=((Gtk.STOCK_CANCEL,
                                     Gtk.ResponseType.CANCEL),
                                    (_("Replace"),
                                     Gtk.ResponseType.YES)))
    return result == Gtk.ResponseType.YES


def save(title='', parent=None, current_name='', folder=None):
    """Displays a save dialog."""
    filechooser = Gtk.FileChooserDialog(title or _('Save'),
                                        parent,
                                        Gtk.FileChooserAction.SAVE,
                                        (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                         Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
    if current_name:
        filechooser.set_current_name(current_name)
    filechooser.set_default_response(Gtk.ResponseType.OK)

    if folder:
        filechooser.set_current_folder(folder)

    path = None
    while True:
        response = filechooser.run()
        if response != Gtk.ResponseType.OK:
            path = None
            break

        path = filechooser.get_filename()
        if not os.path.exists(path):
            break

        if ask_overwrite(path, parent):
            break
    filechooser.destroy()
    return path


def password(primary='', secondary='', parent=None):
    """
    Shows a password dialog and returns the password entered in the dialog
    :param primary: primary text
    :param secondary: secondary text
    :param parent: a Gtk.Window subclass or None
    :returns: the password or None if none specified
    :rtype: string or None
    """
    if not primary:
        raise ValueError("primary cannot be empty")

    d = HIGAlertDialog(parent=parent, flags=Gtk.DialogFlags.MODAL,
                       type=Gtk.MessageType.QUESTION,
                       buttons=Gtk.ButtonsType.OK_CANCEL)
    d.set_default_response(Gtk.ResponseType.OK)

    d.set_primary(primary + '\n')
    if secondary:
        secondary += '\n'
        d.set_secondary(secondary)

    hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    hbox.set_border_width(6)
    hbox.show()
    d.label_vbox.pack_start(hbox, True, True, 0)

    label = Gtk.Label(label=_('Password:'))
    label.show()
    hbox.pack_start(label, False, False, 0)

    entry = Gtk.Entry()
    entry.set_invisible_char('\u2022')
    entry.set_visibility(False)
    entry.show()

    d.add_action_widget(entry, Gtk.ResponseType.OK)
    # FIXME: Is there another way of connecting widget::activate to a response?
    d.action_area.remove(entry)
    hbox.pack_start(entry, True, True, 12)

    response = d.run()

    if response == Gtk.ResponseType.OK:
        password = entry.get_text()
    else:
        password = None
    d.destroy()
    return password


def _test():
    yesno('Kill?', default=Gtk.ResponseType.NO)

    info('Some information displayed not too long\nbut not too short',
         description=('foobar ba asdjaiosjd oiadjoisjaoi aksjdasdasd kajsdhakjsdh\n'
                      'askdjhaskjdha skjdhasdasdjkasldj alksdjalksjda lksdjalksdj\n'
                      'asdjaslkdj alksdj lkasjdlkjasldkj alksjdlkasjd jklsdjakls\n'
                      'ask;ldjaklsjdlkasjd alksdj laksjdlkasjd lkajs kjaslk jkl\n'),
         default=Gtk.ResponseType.OK,
         )

    error('An error occurred', Gtk.Button('Woho'))
    error('Unable to mount the selected volume.',
          'mount: can\'t find /media/cdrom0 in /etc/fstab or /etc/mtab')
    print(open(title='Open a file', patterns=['*.py']))
    print(save(title='Save a file', current_name='foobar.py'))

    print(password('Administrator password',
                   'To be able to continue the wizard you need to enter the '
                   'administrator password for the database on host anthem'))
    print(selectfolder())


if __name__ == '__main__':
    _test()
