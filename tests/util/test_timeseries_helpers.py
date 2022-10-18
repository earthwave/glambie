from glambie.util.timeseries_helpers import combine_timeseries_imbie
from glambie.util.timeseries_helpers import get_matched_indices
from glambie.util.timeseries_helpers import moving_average
from glambie.util.timeseries_helpers import resample_1d_array
from glambie.util.timeseries_helpers import timeseries_as_months
from glambie.util.timeseries_helpers import cumulative_to_derivative
from glambie.util.timeseries_helpers import derivative_to_cumulative
from glambie.util.timeseries_helpers import resample_derivative_timeseries_to_monthly_grid

import numpy as np
import pandas as pd
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
    # basic test
    dates = np.array([2010, 2011])
    ts_new = timeseries_as_months(dates, downsample_to_month=True)
    assert len(ts_new) == 13
    assert ts_new[0] == 2010.0
    assert ts_new[1] == 2010.0 + (1 / 12)
    # test input should equal output
    dates = np.array([2010., 2010 + (1 / 12), 2010 + (2 / 12)])
    ts_new = timeseries_as_months(dates, downsample_to_month=True)
    assert np.array_equal(dates, ts_new)
    # should pad last element
    dates = np.array([2010.02, 2010.12, 2010.22])
    ts_new = timeseries_as_months(dates, downsample_to_month=True)
    assert ts_new[-1] == 2010.25


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
    t, y, data = combine_timeseries_imbie(t, y, outlier_tolerance=None, calculate_as_errors=False,
                                    perform_moving_average=False, verbose=False)
    assert t.shape == y.shape
    assert np.array_equal(data[0], t)


def test_combine_timeseries_avg():  # this test is a bit lazy ;)
    t = [np.array([2010, 2011, 2012, 2014]), np.array([2011, 2012, 2014, 2015]),
         np.array([2011.1, 2012.2, 2014.3, 2015.4])]
    y = [np.array([10, 11, 12, 14]), np.array([16, 16, 29, 50]), np.array([17, 16, 22, 90])]
    t_avg, y_avg, data_avg = combine_timeseries_imbie(t, y, outlier_tolerance=None, calculate_as_errors=True,
                                                perform_moving_average=True, verbose=False)
    t, y, data = combine_timeseries_imbie(t, y, outlier_tolerance=None, calculate_as_errors=False,
                                    perform_moving_average=False, verbose=False)
    assert t_avg.shape == t.shape
    assert ~np.array_equal(y_avg, y)  # just checking that the result with moving avg is not the same as without


def test_combine_timeseries_simple_example():
    t = [np.array([2010, 2011]), np.array([2010, 2011])]
    y = [np.array([1, 2]), np.array([2, 1])]  # this should return 1.5 for each element
    t, y, data = combine_timeseries_imbie(t, y, outlier_tolerance=None, calculate_as_errors=False,
                                    perform_moving_average=False, verbose=False)
    assert np.all(y == 1.5)


def test_combine_timeseries_simple_example_errors():
    t = [np.array([2010, 2011]), np.array([2010, 2011])]
    y = [np.array([4, 2]), np.array([6, 1])]
    t, y, data = combine_timeseries_imbie(t, y, outlier_tolerance=None, calculate_as_errors=True,
                                    perform_moving_average=False, verbose=False)
    assert y[-1] == (np.sqrt(1**2 + 2**2) / 2)
    assert round(y[0], 10) == round((np.sqrt(4**2 + 6**2) / 2), 10)  # round due to floating point diffs


def test_combine_timeseries_simple_example_mov_avg():
    t = [np.array([2010, 2011, 2012]), np.array([2010, 2011, 2012])]
    y = [np.array([1, 2, 1]), np.array([2, 1, 2])]  # this should return 1.5 for each element
    t, y, data = combine_timeseries_imbie(t, y, outlier_tolerance=None, calculate_as_errors=False,
                                    perform_moving_average=True, verbose=False)
    assert np.all(y == 1.5)


def test_cumulative_to_derivative():
    dates = [2010, 2011, 2012, 2013]
    cumulative_changes = [0., 3., 4., 5.]
    start_dates, end_dates, changes = cumulative_to_derivative(dates, cumulative_changes, return_type="arrays")
    assert np.array_equal(start_dates, np.array([2010, 2011, 2012]))
    assert np.array_equal(end_dates, np.array([2011, 2012, 2013]))
    assert np.array_equal(changes, np.array([3., 1., 1.]))
    # also check returntype dataframe works
    df = cumulative_to_derivative(dates, cumulative_changes, return_type="dataframe")
    pd.testing.assert_series_equal(df["changes"], pd.Series([3., 1., 1.], name="changes"))


def test_derivative_to_cumulative():
    start_dates = [2010, 2011, 2012]
    end_dates = [2011, 2012, 2013]
    derivative_changes = [3., 1., 1.]
    dates, changes = derivative_to_cumulative(start_dates, end_dates, derivative_changes, return_type="arrays")
    assert np.array_equal(dates, np.array([2010, 2011, 2012, 2013]))
    assert np.array_equal(changes, np.array([0., 3., 4., 5.]))
    # also check returntype dataframe works
    df = derivative_to_cumulative(start_dates, end_dates, derivative_changes, return_type="dataframe")
    pd.testing.assert_series_equal(df["changes"], pd.Series([0., 3., 4., 5.], name="changes"))


def test_derivative_to_cumulative_and_back_gives_initial_input_again():
    start_dates = [2010, 2011, 2012]
    end_dates = [2011, 2012, 2013]
    derivative_changes = [3., 1., 1.]
    dates, cumulative_changes = derivative_to_cumulative(
        start_dates, end_dates, derivative_changes, return_type="arrays")
    start_dates2, end_dates2, derivative_changes2 = cumulative_to_derivative(
        dates, cumulative_changes, return_type="arrays")
    assert np.array_equal(start_dates2, np.array(start_dates))
    assert np.array_equal(end_dates2, np.array(end_dates))
    assert np.array_equal(derivative_changes2, np.array(derivative_changes))


def test_resample_to_monthly_grid_test_no_changes():
    start_dates = [2010., 2010 + (1 / 12), 2010 + (2 / 12)]
    end_dates = [2010 + (1 / 12), 2010 + (2 / 12), 2010 + (3 / 12)]
    changes = [3., 1., 1.]
    start_dates2, end_dates2, changes2 = resample_derivative_timeseries_to_monthly_grid(
        start_dates, end_dates, changes)
    assert np.array_equal(start_dates2, np.array(start_dates))
    assert np.array_equal(end_dates2, np.array(end_dates))
    assert np.array_equal(changes2, np.array(changes))


def test_resample_to_monthly_grid_test_changes():
    start_dates = [2010.02, 2010.12, 2010.22]
    end_dates = [2010.12, 2010.22, 2010.32]
    changes = [3., 1., 1.]
    start_dates2, end_dates2, changes2 = resample_derivative_timeseries_to_monthly_grid(
        start_dates, end_dates, changes)
    assert len(start_dates) == len(end_dates)
    assert np.allclose(start_dates2, timeseries_as_months(start_dates))  # np.allclose to avoid floating point issues
    assert np.allclose(end_dates2, timeseries_as_months(end_dates))
    # make sure the last value in cumulative timeseries is the same for input and output
    assert pd.Series(changes2).cumsum().iloc[-1] == pd.Series(changes).cumsum().iloc[-1]
