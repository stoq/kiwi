#!/usr/bin/env python
from kiwi.ui.delegates import ProxyDelegate
from kiwi.ui.objectlist import Column, ObjectList

class DiaryEntry:
    title = ''
    text = ''
    period = ''

class Diary(ProxyDelegate):
    def __init__(self):
        self.entries = ObjectList([Column("title", width=120),
                                   Column("period", width=80),
                                   Column("text", expand=True)])

        ProxyDelegate.__init__(self, DiaryEntry(), ['title', 'period', 'text'],
                               gladefile="diary",
                               delete_handler=self.quit_if_last)
        self.hbox.pack_start(self.entries)
        self.entries.show()
        self.entries.grab_focus()

    def on_add__clicked(self, button):
        entry = DiaryEntry()
        entry.title = 'New title'

        self.set_model(entry)
        self.entries.append(entry)
        self.title.grab_focus()

    def on_remove__clicked(self, button):
        entry = self.entries.get_selected()
        if entry:
            self.entries.remove(entry)

    def on_entries__selection_changed(self, entries, instance):
        if instance:
            self.set_model(instance)

proxy = Diary()
proxy.show_and_loop()
