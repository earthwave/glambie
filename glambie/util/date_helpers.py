from datetime import datetime, timedelta


def decimal_dates_to_datetime_dates(decimal_dates_list: list) -> list:
    """Function to convert a list of decimal dates to datetime dates

    Parameters
    ----------
    decimal_dates_list : list
        list of decimal date objects

    Returns
    ----------
    A list of datetime dates
    """
    converted_dates = [year2datetime(i) for i in decimal_dates_list]
    return converted_dates


def datetime_dates_to_decimal_dates(datetime_dates_list: list) -> list:
    """Function to convert a list of datetime dates to decimal dates

    Parameters
    ----------
    datetime_dates_list : list
        list of datetime date objects

    Returns
    ----------
    A list of decimal dates
    """
    converted_dates = [datetime2year(i) for i in datetime_dates_list]
    return converted_dates


def datetime2year(datetime_date: datetime.date) -> float:
    """Function to convert a datetime date to a decimal date

    Parameters
    ----------
    datetime_date:
        datetime date object

    Returns
    ----------
    Date as a decimal number
    """
    year_part = datetime_date - datetime(year=datetime_date.year, month=1, day=1)
    year_length = get_year_length(datetime_date.year)
    print(year_length)
    return datetime_date.year + year_part / year_length


def year2datetime(decimal_date: float) -> datetime.date:
    """Function to convert a decimal date to a datetime date

    Parameters
    ----------
    decimal_date: float
        decimal year

    Returns
    ----------
    Converted datetime object
    """
    year = int(decimal_date)
    year_length = (
        datetime(year=year + 1, month=1, day=1)
        - datetime(year=year, month=1, day=1)
    )
    days_within_year = timedelta(days=(decimal_date - year) * (year_length.days))
    print(days_within_year)
    day_one_of_year = datetime(year, 1, 1)
    date = day_one_of_year + days_within_year
    return date


def get_year_length(year: int) -> timedelta:
    '''Returns the length of a year as time delta object
    i.e. leap years will have 366 days, other years have 365 days

    '''
    year_length = (
        datetime(year=year + 1, month=1, day=1)
        - datetime(year=year, month=1, day=1)
    )
    return year_length
