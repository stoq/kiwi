"""
kiwi.tasklet demo program
"""

from gi.repository import Gtk

from kiwi import tasklet


class Counter(tasklet.Tasklet):
    def __init__(self, dialog):
        self.dialog = dialog
        super(Counter, self).__init__()

    def run(self):
        timeout = tasklet.WaitForTimeout(1000)
        msgwait = tasklet.WaitForMessages(accept='quit')

        for i in range(10, 0, -1):
            self.dialog.format_secondary_markup(
                "Time left: <b>%i</b> seconds" % i)

            yield timeout, msgwait
            ev = tasklet.get_event()

            if isinstance(ev, tasklet.Message) and ev.name == 'quit':
                return
            elif ev is timeout:
                pass
            else:
                raise AssertionError


def main():
    dialog = Gtk.MessageDialog(parent=None, flags=0, type=Gtk.MessageType.QUESTION,
                               buttons=Gtk.ButtonsType.YES_NO,
                               message_format="Please answer Yes or No")
    dialog.format_secondary_markup("Time left: <b>??</b> seconds")
    dialog.show()

    counter = Counter(dialog)

    yield (tasklet.WaitForTasklet(counter),
           tasklet.WaitForSignal(dialog, "response"),
           tasklet.WaitForSignal(dialog, "close"))

    event = tasklet.get_event()
    if isinstance(event, tasklet.WaitForSignal):
        print("signal '%s', stopping counter" % event.signal)
        yield tasklet.Message("quit", dest=counter)  # stop the counter

        if event.signal == 'close':
            Gtk.main_quit()
            return

        response = event.signal_args[0]
        msgbox = Gtk.MessageDialog(parent=dialog,
                                   flags=Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                   type=Gtk.MessageType.INFO,
                                   buttons=Gtk.ButtonsType.OK,
                                   message_format=("Thank you "
                                                   "for your kind answer!"))
        print("response was", response)
        if response == Gtk.ResponseType.YES:
            msgbox.format_secondary_markup(
                "Your response was <i><b>Yes</b></i>")
        elif response == Gtk.ResponseType.NO:
            msgbox.format_secondary_markup(
                "Your response was <i><b>No</b></i>")
        else:
            ## must have been a delete event
            print("response was delete event")
            Gtk.main_quit()
            return
        msgbox.show()

        print("showing dialog")
        yield (tasklet.WaitForSignal(msgbox, "response"),
               tasklet.WaitForSignal(msgbox, "close"))
        print("event", tasklet.get_event())

    else:
        ## timeout must have exausted..
        assert isinstance(event, tasklet.WaitForTasklet)
        msgbox = Gtk.MessageDialog(parent=dialog,
                                   flags=Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                   type=Gtk.MessageType.WARNING,
                                   buttons=Gtk.ButtonsType.OK,
                                   message_format="You're too slow!!")
        msgbox.show()

        yield (tasklet.WaitForSignal(msgbox, "response"),
               tasklet.WaitForSignal(msgbox, "close"))

    Gtk.main_quit()

if __name__ == '__main__':
    tasklet.run(main())
    Gtk.main()
