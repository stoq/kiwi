import datetime

import gtk
from sqlobject import connectionForURI, SQLObject, StringCol, DateCol, ForeignKey, AND

from kiwi.enums import SearchFilterPosition
from kiwi.db.sqlobj import SQLObjectQueryExecuter
from kiwi.ui.objectlist import Column
from kiwi.ui.search import (SearchContainer, DateSearchFilter,
                            ComboSearchFilter)

__connection__ = connectionForURI('sqlite:///:memory:')

class Category(SQLObject):
    name = StringCol()
Category.createTable()

class Task(SQLObject):
    title = StringCol()
    category = ForeignKey('Category')
    date = DateCol()
Task.createTable()

for category in ['Work',
                 'Home',
                 'School']:
    Category(name=category)

work = Category.selectBy(name='Work')[0]
home = Category.selectBy(name='Home')[0]
school = Category.selectBy(name='School')[0]

today = datetime.date.today()
for title, category, date in [
    ('Upgrade web server',  work, today - datetime.timedelta(1)),
    ('Buy new light bulbs', home, today - datetime.timedelta(40)),
    ('Set stock options',   home, today - datetime.timedelta(30)),
    ('Pass geology test',   school, today - datetime.timedelta(23)),
    ('Extend student loan', school, today - datetime.timedelta(10)),
    ('Hire new secretary',  work, today - datetime.timedelta(5)),
    ('Complete GTA',        home, today),
    ('Train interns',       work, today)]:

    Task(title=title,
         category=category,
         date=date)

class TaskViewer(gtk.Window):
    def __init__(self):
        gtk.Window.__init__(self)
        self.set_title('Tasks')
        self.search = SearchContainer(self.get_columns())
        self.add(self.search)
        self._setup_searching()
        self._create_filters()

    def _setup_searching(self):
        self.query = SQLObjectQueryExecuter()
        self.query.set_query(self._executer_query)
        self.search.set_query_executer(self.query)
        self.query.set_table(Task)

    def _create_filters(self):
        categories = [(c.name, c.id) for c in Category.select()]
        categories.insert(0, ('Any', None))
        self.category_filter = ComboSearchFilter(
            'Category:', categories)
        self.search.add_filter(
            self.category_filter,
            SearchFilterPosition.TOP, ['categoryID'])

        self.search.set_text_field_columns(['title'])
        self.search.add_filter(DateSearchFilter('Date:'),
                               columns=['date'])

    def _executer_query(self, query, conn):
        category_id = self.category_filter.get_state().value
        if category_id is not None:
            query = AND(Category.q.id == category_id, query)
        return Task.select(query)

    def get_columns(self):
        return [
            Column('title', data_type=str, title='Title',
                   expand=True),
            Column('category.name', title='Category'),
            Column('date', data_type=datetime.date, width=90)
            ]

view = TaskViewer()
view.set_size_request(-1, 400)
view.connect('delete-event', gtk.main_quit)
view.show_all()
gtk.main()
