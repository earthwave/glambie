import numpy as np
from glambie.util.timeseries_helpers import moving_average, timeseries_as_months, resample_1d_array


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
