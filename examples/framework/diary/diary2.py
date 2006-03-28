#!/usr/bin/env python
from kiwi.python import Settable
from kiwi.ui.delegates import ProxyDelegate
from kiwi.ui.objectlist import Column, ObjectList

class DiaryEntry(Settable):
    def __init__(self):
        Settable.__init__(self, title='', period='morning', text='')

    def get_words(self):
        return len(self.text.split())

    def get_chars(self):
        return len(self.text)

class Diary(ProxyDelegate):
    def __init__(self):
        self.entries = ObjectList([Column("title", width=120, sorted=True),
                                   Column("period", width=80),
                                   Column("text", expand=True, visible=False)])
        ProxyDelegate.__init__(self, DiaryEntry(),
                               ['title', 'period', 'text', 'chars', 'words'],
                               gladefile="diary2",
                               delete_handler=self.quit_if_last)
        self.hbox.pack_start(self.entries)
        self.entries.show()
        self.entries.grab_focus()
        self.set_editable(False)

    def set_editable(self, editable):
        self.leftbox.set_sensitive(editable)
        self.remove.set_sensitive(editable)

    def proxy_updated(self, *args):
        self.entries.update(self.model)

    def on_add__clicked(self, button):
        entry = DiaryEntry()
        entry.title = 'Untitled'
        self.entries.append(entry, select=True)
        self.set_editable(True)

    def on_remove__clicked(self, button):
        entry = self.entries.get_selected()
        if entry:
            self.entries.remove(entry, select=True)

        self.set_editable(len(self.entries) >= 1)
        if not len(self.entries):
            self.set_model(None)

    def on_text__content_changed(self, text):
        self.proxy.update_many(("chars", "words"))
        self.entries.update(self.model)

    def on_entries__selection_changed(self, entries, instance):
        if instance:
            self.set_model(instance)
            self.title.grab_focus()

proxy = Diary()
proxy.show_and_loop()
