#!/usr/bin/env python
import gtk

from kiwi.ui.gadgets import quit_if_last
from kiwi.ui.views import BaseView


class NewsItem:
    """An instance representing an item of news.
       Attributes: title, author, url, size"""
    title = ''
    url = ''
    author = ''
    size = 0

item = NewsItem()
my_widgets = ["title", "author", "url", "size"]
view = BaseView(gladefile="newsform.ui",
                widgets=my_widgets, delete_handler=quit_if_last)
view.add_proxy(item, my_widgets)
view.focus_topmost()
view.show()
gtk.main()  # runs till window is closed as per delete_handler

print 'Item: "%s" (%s) %s %d' % (item.title, item.author, item.url, item.size)
