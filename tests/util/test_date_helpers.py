from glambie.util.date_helpers import datetime2year, year2datetime, get_year_length, decimal_dates_to_datetime_dates, datetime_dates_to_decimal_dates
import datetime


def test_year2datetime():
    assert year2datetime(2000) == datetime.datetime(2000, 1, 1)


def test_datetime2year():
    date = datetime.datetime(2000, 1, 1)
    assert datetime2year(date) == 2000.0


def test_year_conversion_loop():
    # test one way if values the same after converting from decimal to date and back
    decimal_date = 2000.18
    datetime_date = year2datetime(decimal_date)
    assert datetime2year(datetime_date) == decimal_date
    # test other way
    datetime_date = datetime.datetime(2005, 4, 2)
    decimal_date = datetime2year(datetime_date)
    assert year2datetime(decimal_date) == datetime_date    


def test_get_year_length():
    assert get_year_length(2000).days == 366
    assert get_year_length(2001).days == 365


def test_decimal_dates_to_datetime_dates():
    decimal_list = [2000, 2001]
    assert decimal_dates_to_datetime_dates(decimal_list) == [datetime.datetime(2000, 1, 1), datetime.datetime(2001, 1, 1)]
    

def test_datetime_dates_to_decimal_dates():
    date_list = [datetime.datetime(2000, 1, 1), datetime.datetime(2001, 1, 1)]
    assert datetime_dates_to_decimal_dates(date_list) == [2000.0, 2001.0]