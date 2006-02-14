#!/usr/bin/env python
import gtk

from kiwi.ui.objectlist import ObjectList, Column

class NewsItem:
    """An instance that holds information about a news article."""
    def __init__(self, title, author, url):
        self.title, self.author, self.url = title, author, url

# Assemble friendly Pigdog.org news into NewsItem instances so they can
# be used in the ObjectList
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

# Specify the columns: one for each attribute of NewsItem, the URL
# column invisible by default
my_columns = [Column("title", sorted=True),
              Column("author", justify=gtk.JUSTIFY_RIGHT),
              Column("url", title="URL", visible=False)]

objectlist = ObjectList(my_columns)
objectlist.add_list(news)

w = gtk.Window()
w.connect('delete-event', gtk.main_quit)
w.set_size_request(600, 250)

w.add(objectlist)

w.show_all()
gtk.main()
