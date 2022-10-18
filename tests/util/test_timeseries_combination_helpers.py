import pandas as pd
import numpy as np
from glambie.util.timeseries_combination_helpers import get_distance_to_timeperiod, calibrate_timeseries_with_trends


def test_get_distance_to_timeperiod():
    period_start_date = 2000.0
    period_end_date = 2005.0
    date = 2001.0
    assert get_distance_to_timeperiod(date=date, period_start_date=period_start_date,
                                      period_end_date=period_end_date) == 0.0
    date = 2000.0
    assert get_distance_to_timeperiod(date=date, period_start_date=period_start_date,
                                      period_end_date=period_end_date) == 0.0
    date = 1999.0
    assert get_distance_to_timeperiod(date=date, period_start_date=period_start_date,
                                      period_end_date=period_end_date) == 1.0
    date = 2005.0
    assert get_distance_to_timeperiod(date=date, period_start_date=period_start_date,
                                      period_end_date=period_end_date) == 1 / 12
    # in the case of yearly resolution, the date 2005 is already a year away
    date = 2005.0
    assert get_distance_to_timeperiod(date=date, period_start_date=period_start_date,
                                      period_end_date=period_end_date, resolution=1) == 1.0


def test_calibrate_timeseries_with_trends():
    trends = pd.DataFrame({"start_dates": [2000, 2002],
                          "end_dates": [2002, 2005],
                           "changes": [3, 8]})
    calibration_timeseries = pd.DataFrame({"start_dates": [2000, 2001, 2002, 2003, 2004],
                                          "end_dates": [2001, 2002, 2003, 2004, 2005],
                                           "changes": [1., 2., 3., 2., 1.]})
    calibrated_ts, distance_matrix = calibrate_timeseries_with_trends(trends, calibration_timeseries)
    # sum of overalapping period should correspond to the trend
    assert calibrated_ts[1][2:].sum() == 8
    assert calibrated_ts[0][:2].sum() == 3

    # for the first period we expect no correction, as the trend is the same as in the calibration series
    assert np.array_equal(calibrated_ts[0], np.array(calibration_timeseries["changes"]))

    # for the second period we expect a correction
    # difference between the two trends over the overlapping time period are 2, then divide by the 3 years of overlap
    expected_correction = 2 / 3
    assert np.array_equal(calibrated_ts[1], np.array(calibration_timeseries["changes"]) + expected_correction)

    # check distance matrix
    assert np.array_equal(distance_matrix[0], np.array([3., 2., 1., 1., 1.]))
