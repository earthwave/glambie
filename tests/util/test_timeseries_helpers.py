from glambie.util.timeseries_helpers import combine_timeseries
from glambie.util.timeseries_helpers import get_matched_indices
from glambie.util.timeseries_helpers import moving_average
from glambie.util.timeseries_helpers import resample_1d_array
from glambie.util.timeseries_helpers import timeseries_as_months
import numpy as np
import pytest


def test_moving_average_no_window():
    dx = 1.0
    x = np.array([1, 2, 3, 4, 5])
    y = np.array([2, 2, 4, 5, 6])
    result = moving_average(dx, x, y=y, clip=False)
    assert np.array_equal(result, y)  # with window = 1.0 we should still get back the same array as the input


def test_moving_average():
    dx = 3.0  # window should be 'x > x[i]- (dx/2)' and 'x < x[i] + (dx/2)'
    x = np.array([1, 2, 3, 4, 5])
    y = np.array([2, 2, 4, 5, 6])
    result = moving_average(dx, x, y=y, clip=False)
    assert np.array_equal(result, np.array([2, (2 + 2 + 4) / 3, (2 + 4 + 5) / 3, (4 + 5 + 6) / 3, (5 + 6) / 2]))


def test_moving_average_with_clip():
    dx = 3.0
    x = np.array([1, 2, 3, 4, 5])
    y = np.array([2, 2, 4, 5, 6])
    result = moving_average(dx, x, y=y, clip=True)
    result
    assert np.array_equal(result[~np.isnan(result)], np.array([(2 + 2 + 4) / 3, (2 + 4 + 5) / 3, (4 + 5 + 6) / 3]))


def test_timeseries_as_months():
    f = np.array([2010, 2011])
    ts_new = timeseries_as_months(f, downsample_to_month=True)
    assert len(ts_new) == 13
    assert ts_new[0] == 2010.0
    assert ts_new[1] == 2010.0 + (1 / 12)


def test_timeseries_as_months_padding():
    f = np.array([2010, 2011, 2011.1])
    ts_new = timeseries_as_months(f, downsample_to_month=False)
    assert len(ts_new) == 3
    assert ts_new[0] == 2010.0
    assert ts_new[1] == 2011.0
    assert ts_new[2] == 2011.0 + (1 / 12)


def test_resample_1d_array_nearest():
    y = np.array([2, 4, 5])
    x = np.array([2011, 2012, 2013])
    x_new = np.array([2011, 2011.2, 2011.8, 2012, 2013])
    result = resample_1d_array(x=x, y=y, x_new=x_new, mode='nearest')
    assert np.array_equal(result, np.array([2, 2, 4, 4, 5]))


def test_resample_1d_array_linear():
    y = np.array([2, 4, 5])
    x = np.array([2011, 2012, 2013])
    x_new = np.array([2011, 2011.5, 2012, 2012.1, 2013])
    result = resample_1d_array(x=x, y=y, x_new=x_new, mode='linear')
    print(result)
    assert result[1] == 3.0
    assert round(result[3], 5) == 4.1  # due to floating point


def test_get_matched_indices():
    a = np.array([3, 5, 7, 9, 11])
    b = np.array([5, 6, 7, 8, 9, 10])
    ai, bi = get_matched_indices(a, b)
    assert np.array_equal(ai, np.array([1, 2, 3]))
    assert np.array_equal(bi, np.array([0, 2, 4]))
    assert np.array_equal(a[ai], b[bi])


def test_get_matched_indices_with_duplicates():
    a = np.array([3, 5, 5, 9, 11])
    b = np.array([5, 6, 7, 8, 9, 10])
    with pytest.raises(ValueError, match='Input array <array1> or <array2> should not contain duplicates.'):
        get_matched_indices(a, b)


def test_combine_timeseries_returns():
    t = [np.array([2010, 2011, 2012, 2014]), np.array([2011, 2012, 2014, 2015]),
         np.array([2011.1, 2012.2, 2014.3, 2015.4])]
    y = [np.array([10, 11, 12, 14]), np.array([16, 16, 29, 50]), np.array([17, 16, 22, 90])]
    t, y, data = combine_timeseries(t, y, outlier_tolerance=None, calculate_as_errors=False,
                                    perform_moving_average=False, verbose=False)
    assert t.shape == y.shape
    assert np.array_equal(data[0], t)


def test_combine_timeseries_avg():  # this test is a bit lazy ;)
    t = [np.array([2010, 2011, 2012, 2014]), np.array([2011, 2012, 2014, 2015]),
         np.array([2011.1, 2012.2, 2014.3, 2015.4])]
    y = [np.array([10, 11, 12, 14]), np.array([16, 16, 29, 50]), np.array([17, 16, 22, 90])]
    t_avg, y_avg, data_avg = combine_timeseries(t, y, outlier_tolerance=None, calculate_as_errors=True,
                                                perform_moving_average=True, verbose=False)
    t, y, data = combine_timeseries(t, y, outlier_tolerance=None, calculate_as_errors=False,
                                    perform_moving_average=False, verbose=False)
    assert t_avg.shape == t.shape
    assert ~np.array_equal(y_avg, y)  # just checking that the result with moving avg is not the same as without


def test_combine_timeseries_simple_example():
    t = [np.array([2010, 2011]), np.array([2010, 2011])]
    y = [np.array([1, 2]), np.array([2, 1])]  # this should return 1.5 for each element
    t, y, data = combine_timeseries(t, y, outlier_tolerance=None, calculate_as_errors=False,
                                    perform_moving_average=False, verbose=False)
    assert np.all(y == 1.5)


def test_combine_timeseries_simple_example_errors():
    t = [np.array([2010, 2011]), np.array([2010, 2011])]
    y = [np.array([4, 2]), np.array([6, 1])]
    t, y, data = combine_timeseries(t, y, outlier_tolerance=None, calculate_as_errors=True,
                                    perform_moving_average=False, verbose=False)
    assert y[-1] == (np.sqrt(1**2 + 2**2) / 2)
    assert round(y[0], 10) == round((np.sqrt(4**2 + 6**2) / 2), 10)  # round due to floating point diffs


def test_combine_timeseries_simple_example_mov_avg():
    t = [np.array([2010, 2011, 2012]), np.array([2010, 2011, 2012])]
    y = [np.array([1, 2, 1]), np.array([2, 1, 2])]  # this should return 1.5 for each element
    t, y, data = combine_timeseries(t, y, outlier_tolerance=None, calculate_as_errors=False,
                                    perform_moving_average=True, verbose=False)
    assert np.all(y == 1.5)
