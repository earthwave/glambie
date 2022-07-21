from glambie.util.date_helpers import datetime2year, year2datetime, get_year_timedelta, \
    fractional_years_to_datetime_dates, datetime_dates_to_fractional_years
import datetime


def test_year2datetime():
    assert year2datetime(2000) == datetime.datetime(2000, 1, 1)


def test_datetime2year():
    date = datetime.datetime(2000, 1, 1)
    assert datetime2year(date) == 2000.0


def test_year_conversion_loop():
    # test one way if values the same after converting from decimal to date and back
    fractional_year_date = 2000.18
    datetime_date = year2datetime(fractional_year_date)
    assert datetime2year(datetime_date) == fractional_year_date
    # test other way
    datetime_date = datetime.datetime(2005, 4, 2)
    fractional_year_date = datetime2year(datetime_date)
    assert year2datetime(fractional_year_date) == datetime_date


def test_get_year_timedelta():
    assert get_year_timedelta(2000).days == 366
    assert get_year_timedelta(2001).days == 365


def test_fractional_year_to_datetime_dates():
    fractional_year_list = [2000, 2001]
    assert fractional_years_to_datetime_dates(fractional_year_list) \
        == [datetime.datetime(2000, 1, 1), datetime.datetime(2001, 1, 1)]


def test_datetime_dates_to_fractional_years():
    date_list = [datetime.datetime(2000, 1, 1), datetime.datetime(2001, 1, 1)]
    assert datetime_dates_to_fractional_years(date_list) == [2000.0, 2001.0]
