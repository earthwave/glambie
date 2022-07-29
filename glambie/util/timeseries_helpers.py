from matplotlib import pyplot as plt
import numpy as np
import math
from scipy import interpolate
from typing import Union


def contains_duplicates(x):
    return len(np.unique(x)) != len(x)

def get_matched_indices(array1: np.array, array2: np.array, epsilon: float = 0.0) -> Union[np.array, np.array]:
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
    epsilon : float, optional
        the tolerance within which to consider a pair of values to be a match, by default 0.0

    Returns
    -------
    Union[np.array, np.array]
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

    if epsilon == 0:
        firstdup = np.logical_and(
            concat_arr == np.roll(concat_arr, -1),
            vec != np.roll(vec, -1)
        )
    else:
        firstdup = np.logical_and(
            np.abs(concat_arr - np.roll(concat_arr, -1)) < epsilon,
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
        ret = np.cumsum(x, dtype=x.dtype)
        ret[dx:] = ret[dx:] - ret[:-dx]
        return ret[dx - 1:] / dx


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
        t1 = math.ceil(np.max(fractional_year_array) * 12 + 1) / 12.
        monthly_array = np.arange((t1 - t0) * 12) / 12. + t0
    else:
        monthly_array = np.floor(fractional_year_array * 12) / 12.
    return monthly_array


def ts_combine(t: list[np.array], y: list[np.array], nsigma=0, error=False, average=False,
               verbose=False, ret_data_out=False) -> Union[np.array, np.array]:
    """
    Combines a number of input sequences

    INPUTS:
        t: an iterable of the time-series arrays to be combined
        y: an iterable of the y-value arrays to be combined
        nsigma: (optional) tolerance within which to consider a value to be valid
        average: (optional) if True, performs a moving average on the output
        verbose: (optional) if True, renders graphs for debugging purposes
        ret_data_out (optional): if True, returns the data_out array.
    OUTPUTS:
        t1: The abissca series of the combined data
        y1: The y-values of the combined data
        data_out (optional): returns the full data set
    """
    colors = ['r', 'g', 'b', 'c', 'y', 'm', 'o', 'k']
    if verbose:
        for ti, yi, c in zip(t, y, colors[1:]):
            plt.plot(ti, yi, c + '-')
    # create _id array, which indicates which input array each element originated from
    _id = [np.ones(ti.shape, dtype=int) * (i + 1) for i, ti in enumerate(t)]
    _id = np.concatenate(_id)
    # chain together input sequences
    t = np.concatenate(t)
    y = np.concatenate(y)

    # sort the input time-values, and interpolate them to monthly values
    t1 = timeseries_as_months(np.sort(t))
    # remove duplicates from where inputs have overlapped
    t1 = np.unique(t1)

    # create output array
    y1 = np.zeros(t1.shape, dtype=t1.dtype)
    # c1 is used to count the number of input data points that have been used for each output point
    c1 = np.zeros(t1.shape, dtype=t1.dtype)

    # create data_out array
    data_out = np.empty(
        (len(t1), np.max(_id) + 1),
        dtype=t1.dtype
    )
    # init. all values to NaN
    data_out.fill(np.NAN)

    data_out[:, 0] = t1
    for i in range(1, np.max(_id) + 1):
        # find valid data-points where the id matches the current input seq. being worked on
        ok = np.logical_and(
            _id == i, np.isfinite(y)
        )
        if nsigma:
            # if nsigma has been specified, eliminate values far from the mean
            ok[ok] = np.abs(y[ok] - np.nanmean(y)) < max(nsigma, 1) * np.nanstd(y)
        # if we've eliminated all values in the current input, skip to the next one.
        if not ok.any():
            continue
        # get the valid items
        ti = t[ok]
        yi = y[ok]
        # sort by time
        o = np.argsort(ti)
        ti = ti[o]
        yi = yi[o]

        # match time to monthly values
        t2 = timeseries_as_months(ti)
        # use interpolation to find y-values at the new times
        y2 = resample_1d_array(ti, yi, t2)
        # find locations where the times match other items in the input
        m1, m2 = get_matched_indices(np.floor(t1 * 12), np.floor(t2 * 12))
        # match,fix(t1*12),fix(t2*12),m1,m2
        # print repr(y1), repr(y2), repr(m1), repr(m2)
        if verbose:
            plt.plot(t2, y2, colors[i] + '.')
        # add the values from the current input seq. to the output seq.
        if error:
            y1[m1] += y2[m2] ** 2.
        else:
            y1[m1] += y2[m2]
        data_out[m1, i] = y2[m2]
        # increment the values in c1 for each current point
        c1[m1] += 1
    # set any zeros in c1 to ones
    c11 = np.maximum(c1, np.ones(c1.shape))
    # use c1 to calculate the element-wise average of the data
    if error:
        y1 = np.sqrt(y1 / c11) / np.sqrt(c11)
    else:
        y1 /= c11

    # find any locations where no values were found
    ok = (c1 == 0)
    # set those locations to NaNs
    if ok.any():
        y1[ok] = np.NAN
    # optionally plot output
    if verbose:
        plt.plot(t1, y1, '--k')
    # optionally perform moving average
    if average:
        y1 = moving_average(13. / 12, t1, y1)
        if verbose:
            plt.plot(t1, y1, '--k', color='grey', label='moving avg')
    data_out = data_out.T
    # render the plot
    if verbose:
        plt.legend()
        plt.show()
    # return the outputs
    if ret_data_out:
        return t1, y1, data_out
    return t1, y1
