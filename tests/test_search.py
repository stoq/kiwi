import datetime
import unittest

from kiwi.ui.search import LastWeek, LastMonth


class TestDateOptions(unittest.TestCase):
    def testLastWeek(self):
        option = LastWeek()
        for i in range(1, 8):
            get_today_date = lambda: datetime.date(2008, 1, i)
            option.get_today_date = get_today_date
            interval = (get_today_date() - datetime.timedelta(days=7),
                        get_today_date())

            self.assertEqual(option.get_interval(), interval)

    def testLastMonth(self):
        option = LastMonth()
        for i in range(1, 8):
            get_today_date = lambda: datetime.date(2008, 1, i)
            option.get_today_date = get_today_date
            interval = (get_today_date() - datetime.timedelta(days=31),
                        get_today_date())

            self.assertEqual(option.get_interval(), interval)


if __name__ == '__main__':
    unittest.main()
