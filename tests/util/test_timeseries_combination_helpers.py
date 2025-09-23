import warnings
import pytest
import pandas as pd
import numpy as np
from glambie.util.timeseries_combination_helpers import get_distance_to_timeperiod
from glambie.util.timeseries_combination_helpers import calibrate_timeseries_with_trends
from glambie.util.timeseries_combination_helpers import combine_calibrated_timeseries


@pytest.fixture
def example_trends():
    return pd.DataFrame(
        {"start_dates": [2000, 2002], "end_dates": [2002, 2005], "changes": [3, 8]}
    )


@pytest.fixture
def example_calibration_timeseries():
    return pd.DataFrame(
        {
            "start_dates": [2000, 2001, 2002, 2003, 2004],
            "end_dates": [2001, 2002, 2003, 2004, 2005],
            "changes": [1.0, 2.0, 3.0, 2.0, 1.0],
        }
    )


@pytest.fixture
def example_calibrated_series():
    return np.array(
        [
            [1.0, 2.0, 3.0, 2.0, 1.0],
            [1.66666667, 2.66666667, 3.66666667, 2.66666667, 1.66666667],
        ]
    )


@pytest.fixture
def example_distance_matrix():
    return np.array([[1.0, 1.0, 2.0, 3.0, 4.0], [3.0, 2.0, 1.0, 1.0, 1.0]])


def test_get_distance_to_timeperiod():
    period_start_date = 2000.0
    period_end_date = 2005.0
    date = 2001.0
    assert (
        get_distance_to_timeperiod(
            date=date,
            period_start_date=period_start_date,
            period_end_date=period_end_date,
        )
        == 0.0
    )
    date = 2000.0
    assert (
        get_distance_to_timeperiod(
            date=date,
            period_start_date=period_start_date,
            period_end_date=period_end_date,
        )
        == 0.0
    )
    date = 1999.0
    assert (
        get_distance_to_timeperiod(
            date=date,
            period_start_date=period_start_date,
            period_end_date=period_end_date,
        )
        == 1.0
    )
    date = 2005.0
    assert (
        get_distance_to_timeperiod(
            date=date,
            period_start_date=period_start_date,
            period_end_date=period_end_date,
        )
        == 1 / 12
    )
    # in the case of yearly resolution, the date 2005 is already a year away
    date = 2005.0
    assert (
        get_distance_to_timeperiod(
            date=date,
            period_start_date=period_start_date,
            period_end_date=period_end_date,
            resolution=1,
        )
        == 1.0
    )


def test_calibrate_timeseries_with_trends(
    example_trends, example_calibration_timeseries
):
    calibrated_ts, distance_matrix = calibrate_timeseries_with_trends(
        example_trends, example_calibration_timeseries
    )
    # sum of overalapping period should correspond to the trend
    assert calibrated_ts[1][2:].sum() == 8
    assert calibrated_ts[0][:2].sum() == 3

    # for the first period we expect no correction, as the trend is the same as in the calibration series
    assert np.array_equal(
        calibrated_ts[0], np.array(example_calibration_timeseries["changes"])
    )

    # for the second period we expect a correction
    # difference between the two trends over the overlapping time period are 2, then divide by the 3 years of overlap
    expected_correction = 2 / 3
    assert np.array_equal(
        calibrated_ts[1],
        np.array(example_calibration_timeseries["changes"]) + expected_correction,
    )

    # check distance matrix
    assert np.array_equal(distance_matrix[0], np.array([1.0, 1.0, 2.0, 3.0, 4.0]))
    assert np.array_equal(distance_matrix[1], np.array([3.0, 2.0, 1.0, 1.0, 1.0]))


def test_combine_calibrated_timeseries(
    example_calibrated_series, example_distance_matrix
):
    p_value = 2

    calibrated_mean_series = combine_calibrated_timeseries(
        example_calibrated_series, example_distance_matrix, p_value=p_value
    )
    # first number should be closer to first series than second series
    assert abs(1.0 - calibrated_mean_series[0]) < abs(
        1.66666667 - calibrated_mean_series[0]
    )
    # second number should be closer to first series than second series
    assert abs(2.0 - calibrated_mean_series[1]) < abs(
        2.66666667 - calibrated_mean_series[1]
    )
    # third number should be closer to second series
    assert abs(3.0 - calibrated_mean_series[2]) > abs(
        3.66666667 - calibrated_mean_series[2]
    )
    # impact of second series should be smaller on first number than second number
    assert abs(1.0 - calibrated_mean_series[0]) < abs(2.0 - calibrated_mean_series[1])


def test_combine_calibrated_timeseries_p_value_0(
    example_calibrated_series, example_distance_matrix
):
    p_value = 0
    calibrated_series = combine_calibrated_timeseries(
        example_calibrated_series, example_distance_matrix, p_value=p_value
    )
    assert np.array_equal(
        np.array([1.0, 2.0, 3.66666667, 2.66666667, 1.66666667]), calibrated_series
    )
    #  essentially a really high p-value should give the same result as p=0, when floating points don't matter anymore
    p_value = 100000000000000
    calibrated_series2 = combine_calibrated_timeseries(
        example_calibrated_series, example_distance_matrix, p_value=p_value
    )
    assert np.array_equal(calibrated_series2, calibrated_series)


def test_combine_calibrated_timeseries_calculate_outside_calibrated_series_period(
    example_calibrated_series, example_distance_matrix
):
    example_distance_matrix[0][0] = (
        2  # edit example so that first value will be outside the calibration period
    )
    p_value = 0
    calibrated_series = combine_calibrated_timeseries(
        example_calibrated_series,
        example_distance_matrix,
        p_value=p_value,
        calculate_outside_calibrated_series_period=True,
    )  # set to True
    calibrated_series_nan_at_start = combine_calibrated_timeseries(
        example_calibrated_series,
        example_distance_matrix,
        p_value=p_value,
        calculate_outside_calibrated_series_period=False,
    )  # set to False
    assert np.isnan(
        calibrated_series_nan_at_start[0]
    )  # First value is outside calibration period
    assert not np.isnan(calibrated_series[0])


def test_combine_calibrated_timeseries_high_p_value(
    example_calibrated_series, example_distance_matrix
):
    # when setting a high p-value the weighting matrix will be 0 everywhere outside the covered time period
    p_value = 200000
    calibrated_series = combine_calibrated_timeseries(
        example_calibrated_series, example_distance_matrix, p_value=p_value
    )
    assert np.array_equal(
        np.array([1.0, 2.0, 3.66666667, 2.66666667, 1.66666667]), calibrated_series
    )


def test_combine_calibrated_timeseries_warning_message(
    example_trends, example_calibration_timeseries
):
    example_trends["end_dates"] = [
        2002,
        2006,
    ]  # going until 2006 should spark a warning

    with warnings.catch_warnings(record=True) as w:
        # Cause all warnings to always be triggered
        warnings.simplefilter("always")
        # Trigger a warning
        calibrated_ts, _distance_matrix = calibrate_timeseries_with_trends(
            example_trends, example_calibration_timeseries
        )
        # Verify warning has been triggered
        assert len(w) == 1
        assert "ignored" in str(w[-1].message)
        # Verify that the trend has been ignored and only one trend has been calibrated
        assert len(calibrated_ts) == 1
