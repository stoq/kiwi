#!/usr/bin/env python
import os

import gtk

from kiwi import utils
from kiwi.ui.delegates import Delegate, SlaveDelegate
from kiwi.ui.widgets.list import List, Column

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

my_columns = [Column("title", sorted=True, tooltip="Title of article", width=50), 
              Column("author", tooltip="Author of article"), 
              Column("url", title="Address", visible=False, 
                     tooltip="Address of article")]

class Shell(Delegate):
    widgets = ["ok", "cancel", "header", "footer", "title"]
    def __init__(self):
        Delegate.__init__(self, gladefile="news_shell", 
                          delete_handler=self.quit_if_last)

        # paint header and footer; they are eventboxes that hold a
        # label and buttonbox respectively
        gadgets.set_background(self.header, "white") 
        gadgets.set_background(self.footer, "#A0A0A0")
        gadgets.set_foreground(self.title, "blue")

        # Create the delegate and set it up
        kiwilist = List(my_columns, news)
        kiwilist.connect('selection-change', self.news_selected)
        kiwilist.connect('double-click', self.double_click)
        slave = SlaveDelegate(toplevel=kiwilist)
        
        self.attach_slave("placeholder", slave)
        slave.focus_toplevel() # Must be done after attach
        
        self.slave = slave
    
    def news_selected(self, the_list):
        # only one item can be selected in mode SELECTION_BROWSE
        kiwilist = self.slave.get_toplevel()
        item = kiwilist.get_selected()[0]
        print "%s %s %s\n" % (item.title, item.author, item.url)

    def double_click(self, the_list, selected_object):
        self.emit('result', selected_object.url)
        self.hide_and_quit()
        
    def on_ok__clicked(self, *args):
        kiwilist = self.slave.get_toplevel()
        selected = kiwilist.get_selected()
        if selected is not None:
            item = selected[0]
            self.emit('result', item.url)
        self.hide_and_quit()

    def on_cancel__clicked(self, *args):
        self.hide_and_quit()

url = None
shell = Shell()
shell.show_all()
def get_url(view, result):
    global url
    url = result
    
shell.connect('result', get_url)

gtk.main()

if url is not None:
    # Try to run BROWSER (or lynx) on the URL returned
    browser = os.environ.get("BROWSER", "lynx")
    os.system("%s %s" % (browser, url))
    
