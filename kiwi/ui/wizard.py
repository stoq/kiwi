#
# Kiwi: a Framework and Enhanced Widgets for Python
#
# Copyright (C) 2005-2006 Async Open Source
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307
# USA
#
# Author(s): Gustavo Rahal <gustavo@async.com.br>
#            Evandro Vale Miquelito <evandro@async.com.br>
#            Johan Dahlin <jdahlin@async.com.br>
#

import gettext

import gtk

from kiwi.ui.delegates import GladeDelegate

_ = lambda m: gettext.dgettext('kiwi', m)

class WizardStep:
    """ This class must be inherited by the steps """
    def __init__(self, previous=None, header=None):
        self.previous = previous
        self.header = header

    def next_step(self):
        # This is a virtual method, which must be redefined on children
        # classes. It should not be called by the last step (in this case,
        # has_next_step should return 0).
        raise NotImplementedError

    def post_init(self):
        """A virtual method that must be defined on child when it's
        necessary. This method will be called right after the change_step
        method on PluggableWizard is concluded for the current step.
        """

    def has_next_step(self):
        # This method should return False on last step classes
        return True

    def has_previous_step(self):
        # This method should return False on first step classes; since
        # self.previous is normally None for them, we can get away with
        # this simplified check. Redefine as necessary.
        return self.previous is not None

    def previous_step(self):
        return self.previous

    def validate_step(self):
        """A hook called always when changing steps. If it returns False
        we can not go forward.
        """
        return True

class PluggableWizard(GladeDelegate):
    """ Wizard controller and view class """
    gladefile = 'PluggableWizard'
    retval = None

    def __init__(self, title, first_step, size=None, edit_mode=False):
        """
        Create a new PluggableWizard object.
        @param title:
        @param first_step:
        @param size:
        @param edit_mode:
        """
        GladeDelegate.__init__(self, delete_handler=self.quit_if_last,
                               gladefile=self.gladefile)
        if not isinstance(first_step, WizardStep):
            raise TypeError("first_step must be a WizardStep instance")

        self.set_title(title)
        self._current = None
        self._first_step = first_step
        self.edit_mode = edit_mode
        if size:
            self.get_toplevel().set_default_size(size[0], size[1])

        self._change_step(first_step)
        if not self.edit_mode:
            self.ok_button.hide()

    # Callbacks

    def on_next_button__clicked(self, button):
        self.go_to_next()

    def on_ok_button__clicked(self, button):
        self._change_step()

    def on_previous_button__clicked(self, button):
        self._change_step(self._current.previous_step())

    def on_cancel_button__clicked(self, button):
        self.cancel()

    # Private API

    def _change_step(self, step=None):
        if step is None:
            # This is the last step and we can finish the job here
            self.finish()
            return
        # If the next step is the current one, stay on it.
        if step is self._current:
            return
        step.show()
        self._current = step
        self._refresh_slave()
        if step.header:
            self.header_lbl.show()
            self.header_lbl.set_text(step.header)
        else:
            self.header_lbl.hide()
        self.update_view()
        self._current.post_init()

    def _refresh_slave(self):
        holder_name = 'slave_area'
        if self.get_slave(holder_name):
            self.detach_slave(holder_name)
        self.attach_slave(holder_name, self._current)

    def _show_first_page(self):
        self.enable_next()
        self.disable_back()
        self.disable_finish()
        self.notification_lbl.hide()

    def _show_page(self):
        self.enable_back()
        self.enable_next()
        self.disable_finish()
        self.notification_lbl.hide()

    def _show_last_page(self):
        self.enable_back()
        self.notification_lbl.show()
        if self.edit_mode:
            self.disable_next()
        else:
            self.enable_next()
        self.enable_finish()

    # Public API
    def update_view(self):
        if self.edit_mode:
            self.ok_button.set_sensitive(True)

        if not self._current.has_previous_step():
            self._show_first_page()
        elif self._current.has_next_step():
            self._show_page()
        else:
            self._show_last_page()

    def enable_next(self):
        """
        Enables the next button in the wizard.
        """
        self.next_button.set_sensitive(True)

    def disable_next(self):
        """
        Disables the next button in the wizard.
        """
        self.next_button.set_sensitive(False)

    def enable_back(self):
        """
        Enables the back button in the wizard.
        """
        self.previous_button.set_sensitive(True)

    def disable_back(self):
        """
        Disables the back button in the wizard.
        """
        self.previous_button.set_sensitive(False)

    def enable_finish(self):
        """
        Enables the finish button in the wizard.
        """
        if self.edit_mode:
            button = self.ok_button
        else:
            button = self.next_button
        button.set_label(_('_Finish'))

    def disable_finish(self):
        """
        Disables the finish button in the wizard.
        """
        if self.edit_mode:
            self.ok_button.set_label(gtk.STOCK_OK)
        else:
            self.next_button.set_label(gtk.STOCK_GO_FORWARD)

    def set_message(self, message):
        """
        Set message for nofitication.
        @param message:
        """
        self.notification_lbl.set_text(message)

    def cancel(self, *args):
        # Redefine this method if you want something done when cancelling the
        # wizard.
        self.retval = None

    def finish(self):
        # Redefine this method if you want something done when finishing the
        # wizard.
        pass

    def go_to_next(self):
        if not self._current.validate_step():
            return

        if not self._current.has_next_step():
            # This is the last step
            self._change_step()
            return

        self._change_step(self._current.next_step())
