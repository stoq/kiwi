#!/usr/bin/env python

import os

import gtk

from kiwi.ui.delegates import GladeDelegate, SlaveDelegate
from kiwi.ui.gadgets import quit_if_last, set_background, set_foreground
from kiwi.ui.objectlist import Column, ObjectList

class NewsItem:
    def __init__(self, title, author, url):
        self.title, self.author, self.url = title, author, url

# Friendly Pigdog.org news
news = [
 NewsItem("Smallpox Vaccinations for EVERYONE", "JRoyale",
          "http://www.pigdog.org/auto/Power_Corrupts/link/2700.html"),
 NewsItem("Is that uranium in your pocket or are you just happy to see me?",
          "Baron Earl",
          "http://www.pigdog.org/auto/bad_people/link/2699.html"),
 NewsItem("Cut 'n Paste", "Baron Earl",
          "http://www.pigdog.org/auto/ArtFux/link/2690.html"),
 NewsItem("A Slippery Exit", "Reverend CyberSatan",
          "http://www.pigdog.org/auto/TheCorporateFuck/link/2683.html"),
 NewsItem("Those Crazy Dutch Have Resurrected Elvis", "Miss Conduct",
          "http://www.pigdog.org/auto/viva_la_musica/link/2678.html")
]

class ListSlave(SlaveDelegate):
    def __init__(self, parent):
        self.parent = parent
        self.news_list = ObjectList([
                   Column('title', 'Title of article', str),
                   Column('author', 'Author of article', str),
                   Column('url', 'Address of article', str),
                   ])
        SlaveDelegate.__init__(self, toplevel=self.news_list)
        self.news_list.add_list(news)
        self.news_list.select(self.news_list[0])

    def on_news_list__selection_changed(self, list, item):
        print "%s %s %s\n" % (item.title, item.author, item.url)

    def on_news_list__double_click(self, the_list, selected_object):
        self.parent.ok.clicked()

class Shell(GladeDelegate):
    def __init__(self):
        keyactions = {
            gtk.keysyms.a: self.on_ok__clicked,
            gtk.keysyms.b: self.on_cancel__clicked,
            }

        GladeDelegate.__init__(self, gladefile="news_shell",
                          delete_handler=quit_if_last, keyactions=keyactions)

        # paint header and footer; they are eventboxes that hold a
        # label and buttonbox respectively
        set_background(self.header, "white")
        set_background(self.footer, "#A0A0A0")
        set_foreground(self.title,  "blue")

        self.slave = ListSlave(self)
        self.attach_slave("placeholder", self.slave)
        self.slave.show()
        self.slave.focus_toplevel() # Must be done after attach

    def on_ok__clicked(self, button):
        item = self.slave.news_list.get_selected()
        self.emit('result', item.url)
        self.hide_and_quit()

    def on_cancel__clicked(self, button):
        self.hide_and_quit()

url = None

shell = Shell()
shell.show()

def get_url(view, result):
    global url
    url = result

shell.connect('result', get_url)

gtk.main()

if url is not None:
    # Try to run BROWSER (or lynx) on the URL returned
    browser = os.environ.get("BROWSER", "lynx")
    os.system("%s %s" % (browser, url))
