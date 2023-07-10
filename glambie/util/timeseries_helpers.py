import warnings
from matplotlib import pyplot as plt
import numpy as np
import math
from scipy import interpolate
from typing import Tuple
import pandas as pd
import datetime
from dateutil.relativedelta import relativedelta
from glambie.util.date_helpers import datetime_dates_to_fractional_years


def contains_duplicates(x: np.array) -> bool:
    """Checks if an array / list contains duplicate values
    """
    return len(np.unique(x)) != len(x)


def get_matched_indices(array1: np.array, array2: np.array, tolerance: float = 0.0) -> Tuple[np.array, np.array]:
    """
    Returns two arrays of indices at which 'array1' and 'array2' match.
    Can e.g. be used to find matching dates from two timeseries

    Example
    -------
    >>> a = np.array([3, 5, 7, 9, 11])
    >>> b = np.array([5, 6, 7, 8, 9, 10])
    >>> ai, bi = get_matched_indices(a, b)
    >>> print(ai)
    [1, 2, 3]
    >>> print(bi)
    [0, 2, 4]
    >>> print(a[ai])
    [5, 7, 9]
    >>> print(b[bi])
    [5, 7, 9]

    Parameters
    ----------
    array1 : np.array
        the first of the two series to match
    array2 : np.array
        the second of the two series to match
    tolerance : float, optional
        the tolerance within which to consider a pair of values to be a match, by default 0.0

    Returns
    -------
    Tuple[np.array, np.array]
        1. The indices at which values in 'array1' match a value in 'array2'
        2. The indices at which values in 'array2' match a value in 'array1'
    """
    if contains_duplicates(array1) or contains_duplicates(array2):
        raise ValueError('Input array <array1> or <array2> should not contain duplicates.')

    length_arr1 = len(array1)
    length_arr2 = len(array2)
    match_arr1 = np.zeros(array1.shape, dtype=bool)
    match_arr2 = np.zeros(array2.shape, dtype=bool)

    if length_arr1 == 1 or length_arr2 == 1:
        if length_arr2 > 1:
            match_arr2[:] = (array2 == array1[0])
            if match_arr2.any():
                match_arr1 = np.zeros((np.count_nonzero(match_arr2)), dtype=np.int32)
            else:
                match_arr1 = np.array([])
            match_arr2 = np.flatnonzero(match_arr2)
        else:
            match_arr1[:] = (array1 == array2[0])
            if match_arr1.any():
                match_arr2 = np.zeros((np.count_nonzero(match_arr1)), dtype=np.int32)
            else:
                match_arr2 = np.array([])
            match_arr1 = np.flatnonzero(match_arr1)
        return match_arr1, match_arr2
    concat_arr = np.concatenate((array1, array2))
    ind = np.concatenate(
        [np.arange(length_arr1), np.arange(length_arr2)]
    )
    vec = np.concatenate(
        [np.zeros([length_arr1], dtype=bool),
         np.ones([length_arr2], dtype=bool)]
    )

    sub = np.argsort(concat_arr)
    concat_arr = concat_arr[sub]
    ind = ind[sub]
    vec = vec[sub]

    if tolerance == 0:
        firstdup = np.logical_and(
            concat_arr == np.roll(concat_arr, -1),
            vec != np.roll(vec, -1)
        )
    else:
        firstdup = np.logical_and(
            np.abs(concat_arr - np.roll(concat_arr, -1)) < tolerance,
            vec != np.roll(vec, -1)
        )
    count = np.count_nonzero(firstdup)
    firstdup = np.flatnonzero(firstdup)
    if count == 0:
        match_arr1 = np.array([])
        match_arr2 = np.array([])
        return match_arr1, match_arr2
    dup = np.zeros((count * 2), dtype=int)
    even = np.arange(count) * 2

    dup[even] = firstdup
    dup[even + 1] = firstdup + 1

    ind = ind[dup]
    vec = vec[dup]
    match_arr2 = ind[vec]
    match_arr1 = ind[np.logical_not(vec)]
    return match_arr1, match_arr2


def resample_1d_array(x: np.array, y: np.array, x_new: np.array, mode: str = "linear") -> np.array:
    """Simple resampling of a an array: returns interpolated y-values based on a new x-array

    Parameters
    ----------
    x : np.array
        The x-values of the input sequence (e.g an array of fractional dates)
    y : np.array
        The y-values of the input sequence
    x_new : np.array
        The desired x-values of the output sequence (e.g. an array of the new desired time resolution)
    mode : str, optional
        the method of interpolation to use, either 'linear', 'nearest' or 'spline'
        by default "linear"

    Returns
    -------
    np.array
        And array of the y-values at each value in 'x_new'. Will have the same length as x_new

    Raises
    ------
    ValueError
        if mode not recognised
    """
    if mode == "spline":
        s = interpolate.InterpolatedUnivariateSpline(x, y)
        ynew = s(x_new)
    elif mode == "linear":
        ynew = np.interp(x_new, x, y)
    elif mode == "nearest":
        s = interpolate.interp1d(x, y, kind='nearest', fill_value="extrapolate")
        ynew = s(x_new)
    else:
        raise ValueError("Unrecognised interpolation mode")

    return ynew


def moving_average(dx: float, x: np.array, y: np.array = None, clip: bool = False) -> np.array:
    """Calculates the moving average of an array.

    If an argument for y is not provided, the function instead provides a moving average of the signal x,
    over a width of dx samples.

    Parameters
    ----------
    dx : float
        the x-distance over which to average, the window is calculated as 'x > x[i]- (dx/2)' and 'x < x[i] + (dx/2)'
    x : np.array
        the x-coordinates of the input data
    y : np.array, optional
        the y-coordinates of the input data, by default None
    clip : bool, optional
        limit the output data to values for which enough data exists to form a complete average,
        returned is a np.array of the same size as y with nan values inserted for the clip, by default False

    Returns
    -------
    np.array
        the averaged y-values, has same length as y
    """
    if y is not None:
        n = len(x)

        ry = np.empty(n,)
        ry.fill(np.NAN)

        for i in range(n):
            ok = np.logical_and(
                x > x[i] - dx / 2.,
                x < x[i] + dx / 2.)
            if ok.any():
                ry[i] = np.mean(y[ok])
        if clip:
            ok = np.logical_or(
                x < np.min(x) + dx / 2 - 1,
                x > np.max(x) - dx / 2 + 1)
            if ok.any():
                ry[ok] = np.NAN
        return ry
    else:
        result = np.cumsum(x, dtype=x.dtype)
        result[dx:] = result[dx:] - result[:-dx]
        return result[dx - 1:] / dx


def timeseries_as_months(fractional_year_array: np.array, downsample_to_month: bool = True) -> np.array(float):
    """Calculates an array (in units of fractional years) of evenly spaced monthly intervals over the timespan of
    a given date array (in units of fractional years)

    This function can be used as input for resampling to ensure that timesteps of different time series are consistent

    Note that the year is evenly split into 12 parts within this function, meaning that not each month starts at
    the first of the month.

    Parameters
    ----------
    fractional_year_array : np.array
        The input time-series
    downsample_to_month : bool, optional
        if True, extends the series to contain values each month
        if False, only existing dates are shifted to nearest month

    Returns
    -------
    np.array[float]
        the new monthly array of fractional years
    """
    if downsample_to_month:
        t0 = math.floor(np.min(fractional_year_array) * 12) / 12.
        t1 = math.ceil(np.max(fractional_year_array) * 12) / 12.
        # small hack to include last element in case it's on a full integer number
        monthly_array = np.arange(math.ceil((t1 - t0 + 0.00001) * 12)) / 12. + t0
    else:  # we add half a month (1/24) to fractional year so it's not always rounded down
        monthly_array = np.floor((np.array(fractional_year_array) + (1 / 24)) * 12) / 12.

    if contains_duplicates(monthly_array):
        warnings.warn("The rounded dates contain duplicates. "
                      "To avoid this, use the function with data at lower temporal resolution than monthly.")

    return monthly_array


def timeseries_is_monthly_grid(fractional_year_array: np.array) -> bool:
    """
    Returns True if all values in the input array are on the monthly grid defined by timeseries_as_months.
    Also works if the resolution of the input array is not monthly.

    Parameters
    ----------
    fractional_year_array : np.array
        The input time-series

    Returns
    -------
    Boolean
        True if input series is on monthly grid, False otherwise
    """
    with warnings.catch_warnings():  # ignore warning about duplicates
        warnings.simplefilter("ignore")
        monthly_grid = timeseries_as_months(fractional_year_array, downsample_to_month=False)
    try:
        np.testing.assert_almost_equal(monthly_grid, fractional_year_array)
    except AssertionError:
        return False
    return True


def combine_timeseries_imbie(t_array: list[np.ndarray],
                             y_array: list[np.ndarray],
                             outlier_tolerance: float = None,
                             calculate_as_errors: bool = False,
                             perform_moving_average: bool = False,
                             verbose=False) \
        -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Combines a number of input timeseries sequences using the logic from IMBIE

    Parameters
    ----------
    t_array : list[np.ndarray]
        a list/iterable of the time-series arrays to be combined
    y_array : list[np.ndarray]
        a list/iterable of the y-value arrays to be combined
    outlier_tolerance : float, optional
        tolerance within which to consider a value to be valid, by default None
    calculate_as_errors : bool, optional
        if True, the y_array series is combined using uncertainty propagation rules, by default False
    perform_moving_average : bool, optional
        if True, performs a moving average on the output (over one calendar year), by default False
    verbose : bool, optional
        if True, renders graphs for debugging purposes, by default False

    Returns
    -------
    Tuple[np.ndarray, np.ndarray, np.ndarray]
        1: numpy array of the fractional years array of the combined data
        2: The corresponding y-values of the combined data series
        3. data_out: 2d array of the full resampled data set of each solution
                     data_out[0] will be the the fractional years array of the combined data
                     data_out[1:] all following elements will be the resampled y_values for each solution
    """

    colors = ['r', 'g', 'b', 'c', 'y', 'm', 'o', 'k']  # n.b. this assumes we have no more than 8 solutions
    if verbose:
        for t_solution, y_solution, c in zip(t_array, y_array, colors[1:]):
            plt.plot(t_solution, y_solution, c + '-')
    # create solution_indices array, which indicates which input array each element originated from
    solution_indices = [np.ones(ti.shape, dtype=int) * (i + 1) for i, ti in enumerate(t_array)]
    solution_indices = np.concatenate(solution_indices)
    # chain together input sequences, solution_indices describes
    t_array = np.concatenate(t_array)
    y_array = np.concatenate(y_array)
    # sort the input time-values, and interpolate them to monthly values, this will be the output time domain
    t_array_combined = timeseries_as_months(np.sort(t_array))
    # remove duplicates from where inputs have overlapped
    t_array_combined = np.unique(t_array_combined)
    # create output array to be filled
    y_array_combined = np.zeros(t_array_combined.shape, dtype=t_array_combined.dtype)
    # solutions_per_timestep is used to count the number of input data points that have been used for each output point
    solutions_per_timestep = np.zeros(t_array_combined.shape, dtype=t_array_combined.dtype)

    # create data_out array for resampled data input
    full_resampled_data = np.empty(
        (len(t_array_combined), np.max(solution_indices) + 1),
        dtype=t_array_combined.dtype
    )
    full_resampled_data.fill(np.NAN)  # initially all values to NaN
    full_resampled_data[:, 0] = t_array_combined  # fill in time domain

    #  RESAMPLE ALL SOLUTIONS TO MONTHLY AND SUM UP SOLUTIONS in y_array_combined
    for index_of_solution in range(1, np.max(solution_indices) + 1):  # iterate through each solution
        # Find valid indices for solution in concatenated array
        valid_indices = np.logical_and(solution_indices == index_of_solution, np.isfinite(y_array))

        # if outlier_tolerance has been specified, eliminate values far from the mean
        if outlier_tolerance is not None:
            valid_indices[valid_indices] = np.abs(y_array[valid_indices] - np.nanmean(y_array)) \
                < max(outlier_tolerance, 1) * np.nanstd(y_array)
        # if we've eliminated all values in the current input, skip to the next solution.
        if not valid_indices.any():
            continue
        # Filter concatenated y_array and t_array by solution, so get values for current solution
        t_solution = t_array[valid_indices]
        y_solution = y_array[valid_indices]
        # sort by time
        sort = np.argsort(t_solution)
        t_solution = t_solution[sort]
        y_solution = y_solution[sort]
        # match time to monthly values
        t_solution_resampled = timeseries_as_months(t_solution)
        # use interpolation to find y-values at the new times
        y_solution_resampled = resample_1d_array(t_solution, y_solution, t_solution_resampled)
        # find locations where the times match the times of the combined series
        matched_indices_1, matched_indices_2 = get_matched_indices(np.floor(t_array_combined * 12),
                                                                   np.floor(t_solution_resampled * 12))
        if verbose:
            plt.plot(t_solution_resampled, y_solution_resampled, colors[index_of_solution] + '.',
                     label='solution: {}'.format(index_of_solution))
        # add the values from the current input seq. to the output seq.
        if calculate_as_errors:
            y_array_combined[matched_indices_1] += y_solution_resampled[matched_indices_2] ** 2.
        else:
            y_array_combined[matched_indices_1] += y_solution_resampled[matched_indices_2]
        full_resampled_data[matched_indices_1, index_of_solution] = y_solution_resampled[matched_indices_2]
        # increment the values in solutions_per_timestep for each current point
        solutions_per_timestep[matched_indices_1] += 1

    # DIVIDE SUMMED RESULT BY NUMBER OF SOLUTIONS TO GET AVERAGE
    # set any zeros in solutions_per_timestep to ones so we don't run into divide by 0 errors
    solutions_per_timestep_ = np.maximum(solutions_per_timestep, np.ones(solutions_per_timestep.shape))
    # use solutions_per_timestep_ to calculate the element-wise average of the data
    if calculate_as_errors:
        y_array_combined = np.sqrt(y_array_combined / solutions_per_timestep_) / np.sqrt(solutions_per_timestep_)
    else:
        y_array_combined /= solutions_per_timestep_
    # find any locations where no values were found
    valid_indices = (solutions_per_timestep == 0)
    # set those locations to NaNs
    if valid_indices.any():
        y_array_combined[valid_indices] = np.NAN

    # PERFORM ADDITIONAL OPTIONAL EDITS ON RESULT
    if verbose:  # optionally plot output
        plt.plot(t_array_combined, y_array_combined, '--k', label='combined')
    if perform_moving_average:  # optionally perform moving average
        y_array_combined = moving_average(13. / 12, t_array_combined, y_array_combined)
        if verbose:
            plt.plot(t_array_combined, y_array_combined, '--k', color='grey', label='comb. moving avg')
    full_resampled_data = full_resampled_data.T
    if verbose:
        plt.legend()
        plt.show()
    return t_array_combined, y_array_combined, full_resampled_data


def derivative_to_cumulative(start_dates: list[float],
                             end_dates: list[float],
                             changes: list[float],
                             return_type="arrays"):
    """
    Calculates a cumulative timeseries from a list of non cumulative changes between start and end date

    Parameters
    ----------
    start_dates : np.array or list of decimal dates
        start dates of each time period
    end_dates : np.array or list of decimal dates
        end dates of each time period
    changes : np.array or list
        changes between start and end date
    return_type : str, optional
        type in which the result is returned. Current options are: 'arrays' and 'dataframe', by default 'arrays'

    Returns
    -------
    Tuple[np.array, np.array] or pd.DataFrame, depending on specified return_type
        'arrays': (dates, cumulative_changes)
        'dataframe': pd.DataFrame({'dates': dates, 'changes': changes})
    """
    dates = np.array([start_dates[0], *end_dates])
    changes = np.array([0, *np.array(pd.Series(changes).cumsum())])
    if return_type == "arrays":
        return dates, changes
    elif return_type == "dataframe":
        df_cumulative = pd.DataFrame({'dates': dates,
                                      'changes': changes,
                                      })
        return df_cumulative


def cumulative_to_derivative(fractional_year_array, cumulative_changes, return_type="arrays"):
    """
    Calculates a a list of non cumulative changes between start and end dates from a list of cumulative changes.

    Parameters
    ----------
    dates : np.array or list of decimal dates
        dates of timeseries
    changes : np.array or list
        cumulative changes
    return_type : str, optional
        type in which the result is returned. Current options are: 'arrays' and 'dataframe', by default 'arrays'

    Returns
    -------
    Tuple[np.array, np.array, np.array] or pd.DataFrame, depending on specified return_type
        'arrays': (start_dates, end_dates, changes)
        'dataframe': pd.DataFrame({'start_dates': start_dates, 'end_dates': end_dates, 'changes': changes})
    """
    # remove first row
    derivative = np.array(pd.Series(cumulative_changes).diff().iloc[1:])
    # remove last row for start dates
    start_dates = np.array(pd.Series(fractional_year_array).iloc[:-1])
    # remove first row for end dates
    end_dates = np.array(pd.Series(fractional_year_array).iloc[1:])

    if return_type == "arrays":
        return start_dates, end_dates, derivative
    elif return_type == "dataframe":
        df = pd.DataFrame({"start_dates": start_dates, "end_dates": end_dates, "changes": derivative})
        return df


def resample_derivative_timeseries_to_monthly_grid(start_dates, end_dates, changes, return_type="arrays"):
    """
    Resample a timeseries of derivatives to a uniform monthly grid.
    The monthly grid is defined by timeseries_as_months(), containing 12 evenly spaced months.

    Parameters
    ----------
    start_dates : np.array or list of decimal dates
        start dates of each time period
    end_dates : np.array or list of decimal dates
        end dates of each time period
    changes : np.array or list
        changes between start and end date
    return_type : str, optional
        type in which the result is returned. Current options are: 'arrays' and 'dataframe', by default 'arrays'

    Returns
    -------
    Tuple[np.array, np.array, np.array] or pd.DataFrame, depending on specified return_type
        'arrays': (start_dates, end_dates, changes) resampled to the monthly grid
        'dataframe': pd.DataFrame({'start_dates': start_dates, 'end_dates': end_dates, 'changes': changes})
    """
    # 1 convert to cumulative (to make sure rate is not lost during the resample process)
    dates, changes = derivative_to_cumulative(start_dates, end_dates, changes)
    # 2 resample to the monthly grid defined by timeseries_as_months()
    monthly_grid = timeseries_as_months(dates)
    changes = resample_1d_array(dates, changes, monthly_grid)
    # 3 convert back to derivatives
    start_dates, end_dates, changes = cumulative_to_derivative(monthly_grid, changes, return_type="arrays")
    if return_type == "arrays":
        return start_dates, end_dates, changes
    elif return_type == "dataframe":
        return pd.DataFrame({"start_dates": start_dates, "end_dates": end_dates, "changes": changes})


def get_total_trend(start_dates, end_dates, changes, calculate_as_errors=False, return_type="dataframe"):
    """
    Calculates the full longterm trend of a derivatives timeseries

    Parameters
    ----------
    start_dates : np.array or list of decimal dates
        input start dates of each time period
    end_dates : np.array or list of decimal dates
        input end dates of each time period
    changes : np.array or list
        input changes between start and end date
    calculate_as_errors : bool
        if set to True, the error of the trend will be calculaterd instead, assuming 'changes' are uncertainties
        by default False
    return_type : str, optional
        type in which the result is returned. Current options are: 'value' and 'dataframe', by default 'dataframe'

    Returns
    -------
    pd.DataFrame or single value with overall trend
        'dataframe': pd.DataFrame({'start_dates': start_dates, 'end_dates': end_dates, 'changes': changes})
                     will contain a single row.
        'value': long-term trend in input unit

    """
    if calculate_as_errors:
        result = np.sqrt(np.nansum(changes**2)) / len(changes)
    else:
        result = np.nansum(changes)
    if return_type == "value":
        return result
    elif return_type == "dataframe":
        return pd.DataFrame({"start_dates": [float(np.nanmin(start_dates))],
                             "end_dates": [float(np.nanmax(end_dates))],
                             "changes": [result]})


def get_average_trends_over_new_time_periods(start_dates, end_dates, changes, new_start_dates, new_end_dates,
                                             calculate_as_errors=False):
    """
    Returns average trend over new time periods.
    Note that this can not be used for upsampling, only for downsampling (e.g. from months to annual averages)

    Parameters
    ----------
    start_dates : np.array
        Array with start dates of input timeseries (in fractional years)
    end_dates : np.array
        Array with end dates of input timeseries (in fractional years)
    changes : np.array
        Array with timeseries changes
    new_start_dates : np.array
        Array with dates of new timeseries start dates (in fractional years)
        All values within new_start_dates should exist within start_dates or the result may be invalid
    new_end_dates : np.array
        Array with dates of new timeseries end dates (in fractional years)
        All within new_end_dates values should exist within end_dates or the result may be invalid
    calculate_as_errors : bool
        if set to True, the error of the trend will be calculaterd instead, assuming 'changes' are uncertainties
        by default False

    Returns
    -------
    pd.DataFrame
        with the new start_dates, end_dates and changes calculated
        pd.DataFrame({'start_dates': start_dates, 'end_dates': end_dates, 'changes': changes})
    """
    # check if in monthly grid
    if not np.isin(np.array(new_start_dates), np.array(start_dates)).all():
        warnings.warn("New start dates should be values in timeseries start_dates."
                      "Result may be invalid.")

    if not np.isin(np.array(new_end_dates), np.array(end_dates)).all():
        warnings.warn("New end dates should be values in timeseries end_dates."
                      "Result may be invalid.")

    timeseries_df = pd.DataFrame({"start_dates": start_dates, "end_dates": end_dates, "changes": changes})
    annual_changes = []
    for start_date, end_date in zip(new_start_dates, new_end_dates):
        df_sub = timeseries_df[(timeseries_df["start_dates"] >= start_date) & (timeseries_df["end_dates"] <= end_date)]
        annual_changes.append(get_total_trend(df_sub["start_dates"],
                              df_sub["end_dates"], df_sub["changes"], return_type="value",
                              calculate_as_errors=calculate_as_errors))

    return pd.DataFrame({"start_dates": new_start_dates,
                         "end_dates": new_end_dates,
                         "changes": annual_changes})


def interpolate_change_per_day_to_fill_gaps(input_dataframe):
    """
    Use this function to fill gaps in an elevation change time series that have a non-uniform temporal resolution.
    Linear interpolation is performed on elevation_change_per_day values, to fill gaps in the input timeseries. An
    overall elevation change in the data gap is then added to the original dataframe.

    Parameters
    ----------
    timeseries_dataframe : _type_
        _description_
    """
    date_gaps = [datetime.datetime.strptime(input_dataframe.start_date[i + 1], '%d/%m/%Y') - datetime.datetime.strptime(
        input_dataframe.end_date[i], '%d/%m/%Y') for i in range(len(input_dataframe) - 1)]
    date_gaps_in_days = [a.days for a in date_gaps]
    input_dataframe['date_gap_days'] = np.append(date_gaps_in_days, [0])

    start_dates = [datetime.datetime.strptime(a, '%d/%m/%Y') for a in input_dataframe.start_date]
    end_dates = [datetime.datetime.strptime(a, '%d/%m/%Y') for a in input_dataframe.end_date]
    new_start_dates, new_end_dates, new_changes, new_errors = [], [], [], []

    for i in range(len(input_dataframe.start_date) - 1):
        current_start_date = start_dates[i]
        current_end_date = end_dates[i]
        new_start_dates.append(current_start_date)
        new_end_dates.append(current_end_date)
        new_changes.append(input_dataframe.glacier_change_observed[i])
        new_errors.append(input_dataframe.glacier_change_uncertainty[i])

        if date_gaps_in_days[i] > 1:
            gap_start_date = current_end_date + relativedelta(days=1)
            gap_end_date = start_dates[i + 1] - relativedelta(days=1)
            new_start_dates.append(gap_start_date)
            new_end_dates.append(gap_end_date)
            new_changes.append(np.nan)
            new_errors.append(np.nan)

    interpolated_dataframe = pd.DataFrame()
    interpolated_dataframe['start_date'] = [datetime.datetime.strftime(a, '%d/%m/%Y') for a in new_start_dates]
    interpolated_dataframe['end_date'] = [datetime.datetime.strftime(a, '%d/%m/%Y') for a in new_end_dates]
    interpolated_dataframe['glacier_change_observed'] = new_changes
    interpolated_dataframe['glacier_change_uncertainty'] = new_errors

    # calculate days covered by each row
    date_gaps = [
        datetime.datetime.strptime(interpolated_dataframe['end_date'][i], '%d/%m/%Y') - datetime.datetime.strptime(
            interpolated_dataframe['start_date'][i], '%d/%m/%Y') for i in range(len(interpolated_dataframe))]
    date_gaps_in_days = [a.days for a in date_gaps]
    interpolated_dataframe['days_covered'] = date_gaps_in_days

    # calculate change per day in each row
    interpolated_dataframe['glacier_change_per_day'] = [
        a / b for a, b in zip(interpolated_dataframe.glacier_change_observed, interpolated_dataframe.days_covered)]
    interpolated_dataframe['glacier_change_uncertainty_per_day'] = [
        a / b for a, b in zip(interpolated_dataframe.glacier_change_uncertainty, interpolated_dataframe.days_covered)]

    dates_list_fractional = datetime_dates_to_fractional_years(new_start_dates)
    interpolated_dataframe['date_fractional'] = dates_list_fractional

    # Linear interpolation of glacier_change_per_day to fill gaps
    df = pd.DataFrame({'time': interpolated_dataframe['date_fractional'],
                       'mass': interpolated_dataframe['glacier_change_per_day'],
                       'error': interpolated_dataframe['glacier_change_uncertainty_per_day']})
    df_int = df.interpolate(method='linear')

    interpolated_dataframe['glacier_change_per_day'] = df_int['mass'].values.tolist()
    interpolated_dataframe['glacier_change_uncertainty_per_day'] = df_int['error'].values.tolist()

    # Convert back to glacier_change_observed
    interpolated_dataframe['glacier_change_observed'] = [
        a * b for a, b in zip(interpolated_dataframe.glacier_change_per_day, interpolated_dataframe.days_covered)]
    interpolated_dataframe['glacier_change_uncertainty'] = [
        a * b for a, b in zip(interpolated_dataframe.glacier_change_uncertainty_per_day,
                              interpolated_dataframe.days_covered)]

    # removing all remaining small day gaps by setting end_date(i) = start_date(i+1)
    updated_end_dates = []
    for i in range(len(interpolated_dataframe.end_date) - 1):
        updated_end_dates.append(interpolated_dataframe.start_date[i + 1])
    updated_end_dates.append(interpolated_dataframe['end_date'].tolist()[-1])
    interpolated_dataframe['end_date'] = updated_end_dates

    # then remove row that has been interpolated for GRACE gap, as this value will be much bigger than the rest
    # (check for start date == 1/7/2017, not super robust)
    interpolated_dataframe.drop(
        interpolated_dataframe.loc[interpolated_dataframe.start_date.__eq__('01/07/2017')].index, inplace=True)

    return interpolated_dataframe
