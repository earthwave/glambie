from datetime import datetime, timedelta


def fractional_years_to_datetime_dates(fractional_year_list: list) -> list:
    """Function to convert a list of fractional years to datetime dates

    Parameters
    ----------
    fractional_year_list : list
        list of fractional years

    Returns
    ----------
    A list of datetime dates
    """
    converted_dates = [year2datetime(i) for i in fractional_year_list]
    return converted_dates


def datetime_dates_to_fractional_years(datetime_dates_list: list) -> list:
    """Function to convert a list of datetime dates to fractional years

    Parameters
    ----------
    datetime_dates_list : list
        list of datetime date objects

    Returns
    ----------
    A list of fractional years
    """
    converted_dates = [datetime2year(i) for i in datetime_dates_list]
    return converted_dates


def datetime2year(datetime_date: datetime.date) -> float:
    """Function to convert a datetime date to a fractional year

    Parameters
    ----------
    datetime_date:
        datetime date object

    Returns
    ----------
    Date as a fractional year (decimal number)
    """
    year_part = datetime_date - datetime(year=datetime_date.year, month=1, day=1)
    year_length = get_year_timedelta(datetime_date.year)
    return datetime_date.year + year_part / year_length


def year2datetime(fractional_year: float) -> datetime.date:
    """Function to convert a fractional year to a datetime date

    Parameters
    ----------
    fractional_year: float
        year as decimal

    Returns
    ----------
    Converted datetime object
    """
    year = int(fractional_year)
    year_length = (
        datetime(year=year + 1, month=1, day=1)
        - datetime(year=year, month=1, day=1)
    )
    days_within_year = timedelta(days=(fractional_year - year) * (year_length.days))
    day_one_of_year = datetime(year, 1, 1)
    date = day_one_of_year + days_within_year
    return date


def get_year_timedelta(year: int) -> timedelta:
    '''Returns the length of a year as time delta object
    i.e. leap years will have 366 days, other years have 365 days

    '''
    year_length = (
        datetime(year=year + 1, month=1, day=1)
        - datetime(year=year, month=1, day=1)
    )
    return year_length
