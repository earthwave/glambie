from datetime import datetime
from datetime import timedelta
import numpy as np
import pandas as pd
import math


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


def get_years(desired_year_start: float, min_date: float, max_date: float, return_type="arrays"):
    """
    Returns start and end dates of years within a timespan (min_date to max_date).
    Only full years within the min_date - max_date time period are included.

    Parameters
    ----------
    desired_year_start : float
        a floating point number of when the glaciological year should start (between 0 and 1), e.g. 0.75 for October
    min_date : float
        minimum date to be calculated for, in fractional years
    max_date : float
        maximum date to be calculated for, in fractional years
    return_type : str, optional
        type in which the result is returned. Current options are: 'arrays' and 'dataframe', by default 'arrays'

    Returns
    -------
    Tuple[np.array, np.array] or pd.DataFrame, depending on specified return_type
        'arrays': (start_dates, end_dates)
        'dataframe': pd.DataFrame({'start_dates': start_dates, 'end_dates': end_dates})
    """
    years = list(range(math.floor(min_date), math.ceil(max_date)))

    start_dates = []
    end_dates = []
    for year in years:
        # if glaciological year is closer to the end of the year
        # the glaciological year is starting around the end of the previous year
        if round(desired_year_start) == 1:
            start_date = year - 1 + desired_year_start
            end_date = year + desired_year_start
            if (start_date >= min_date) & (end_date <= max_date):
                start_dates.append(start_date)
                end_dates.append(end_date)
        # if glaciological year is closer to the start of the year
        # the glaciological year is starting around start of the current year
        elif round(desired_year_start) == 0:
            start_date = year + desired_year_start
            end_date = year + 1 + desired_year_start
            if (start_date >= min_date) & (end_date <= max_date):
                start_dates.append(start_date)
                end_dates.append(end_date)
    if return_type == "dataframe":
        return pd.DataFrame({"start_dates": start_dates, "end_dates": end_dates})
    elif return_type == "arrays":
        return np.array(start_dates), np.array(end_dates)
