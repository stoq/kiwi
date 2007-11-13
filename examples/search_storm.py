#
# An example demonstrating the SearchContainer with Storm
#
import datetime

import gtk

from storm.locals import Int, Unicode, Float, Date, create_database, Store

from kiwi.datatypes import currency
from kiwi.db.stormintegration import StormQueryExecuter
from kiwi.ui.objectlist import Column
from kiwi.ui.search import SearchContainer, DateSearchFilter


class Sale(object):
    __storm_table__ = 'sale'
    id = Int(primary=True)
    description = Unicode()
    price = Float()
    date = Date()

database = create_database("sqlite:")
store = Store(database)

store.execute(
    "CREATE TABLE sale "
    "(id INTEGER PRIMARY KEY, description VARCHAR, price FLOAT, date DATE)"
)

today = datetime.date.today()

for description, price, date in [
    ('Cup of coffee', 2.04, today - datetime.timedelta(1)),
    ('Chocolate bar', 1.85, today - datetime.timedelta(40)),
    ('Candy',         0.99, today - datetime.timedelta(30)),
    ('Grape Juice',   3.38, today - datetime.timedelta(23)),
    ('Ice tea',       1.25, today - datetime.timedelta(10)),
    ('Cookies',       0.85, today - datetime.timedelta(5)),
    ('Noogies',       1.45, today - datetime.timedelta(2)),
    ('Chocolate bar', 1.85, today)]:

    s = Sale()
    s.description=unicode(description)
    s.price=price
    s.date=date
    store.add(s)
    store.flush()


class PurchaseViewer(gtk.Window):
    def __init__(self):
        gtk.Window.__init__(self)
        self.set_title('Purchases')
        self.search = SearchContainer(self.get_columns())
        self.search.set_summary_label('price')
        self.add(self.search)
        self._setup_searching()
        self._create_filters()

    def _setup_searching(self):
        self.query = StormQueryExecuter(store)
        self.search.set_query_executer(self.query)
        self.query.set_table(Sale)

    def _create_filters(self):
        self.search.set_text_field_columns(['description'])
        self.search.add_filter(DateSearchFilter('Date:'),
                               columns=['date'])

    def get_columns(self):
        return [Column('description', data_type=str, title='Description',
                       expand=True),
                Column('price', data_type=currency, title='Price'),
                Column('date', data_type=datetime.date, width=90)]

view = PurchaseViewer()
view.set_size_request(-1, 400)
view.connect('delete-event', gtk.main_quit)
view.show_all()
gtk.main()
