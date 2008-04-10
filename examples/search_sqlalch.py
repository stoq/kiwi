
import datetime

import gtk
from sqlalchemy import Table, Column as SQLAColumn, DynamicMetaData, create_engine, \
    String, ForeignKey, Integer, relation, create_session, Date
from sqlalchemy.orm import mapper

from kiwi.enums import SearchFilterPosition
#from kiwi.db.sqlobj import SQLObjectQueryExecuter
from kiwi.ui.objectlist import Column
from kiwi.ui.search import (SearchContainer, DateSearchFilter,
                            ComboSearchFilter)

from kiwi.db.sqlalch import SQLAlchemyQueryExecuter


meta = DynamicMetaData()

category_table = Table('category', meta,
    SQLAColumn('id', Integer, primary_key=True, autoincrement=True),
    SQLAColumn('name', String),
)

class Category(object):
    """A Category"""

mapper(Category, category_table)

task_table = Table('task', meta,
    SQLAColumn('id', Integer, primary_key=True, autoincrement=True),
    SQLAColumn('title', String),
    SQLAColumn('category_id', Integer, ForeignKey('category.id')),
    SQLAColumn('date', Date),
)

class Task(object):
    """A task"""

mapper(Task, task_table, properties=dict(
    category = relation(Category, backref='tasks'),
))

engine = create_engine('sqlite:///')
meta.connect(engine)
meta.create_all()

session = create_session(bind_to=engine)



for category in ['Work',
                 'Home',
                 'School']:
    c = Category()
    c.name=category
    session.save(c)
session.flush()

work = session.query(Category).select_by(name='Work')[0]
home = session.query(Category).select_by(name='Home')[0]
school = session.query(Category).select_by(name='School')[0]

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

    t = Task()
    t.title=title
    t.category=category
    t.date=date
    session.save(t)
session.flush()

class TaskViewer(gtk.Window):
    def __init__(self):
        gtk.Window.__init__(self)
        self.set_title('Tasks')
        self.search = SearchContainer(self.get_columns())
        self.add(self.search)
        self._setup_searching()
        self._create_filters()

    def _setup_searching(self):
        self.query = SQLAlchemyQueryExecuter(session)
        self.search.set_query_executer(self.query)
        self.query.set_table(Task)

    def _create_filters(self):
        categories = [(c.name, c.id) for c in session.query(Category).select()]
        categories.insert(0, ('Any', None))
        self.category_filter = ComboSearchFilter(
            'Category:', categories)
        self.search.add_filter(
            self.category_filter,
            SearchFilterPosition.TOP, ['id'])

        self.search.set_text_field_columns(['title'])
        self.search.add_filter(DateSearchFilter('Date:'),
                               columns=['date'])

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
