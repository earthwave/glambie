import warnings
import numpy as np
import pandas as pd


def calibrate_timeseries_with_trends(trends: pd.DataFrame, calibration_timeseries: pd.DataFrame):
    """
    This function calibrates a higher resolution calibration timeseries with the trends from a trend DataFrame.
    The 'calibration_timeseries' is adjusted over the common time period, to represent the new trend.
    Each trend within 'trends' (i.e. each row) will produce a separate calibrated solution from the
    'calibration_timeseries'.

    The function further computes a distance matrix which can be used for inversed distance weighting
    when combining the different calibrated solutions

    Note that all dates should be prior resampled to the monthly date grid
    (see glambie.util.timeseries_helper.timeseries_as_months)

    If a trend (row within trends dataframe) is not within the time frame of calibration series it will be ignored
    and a warning will be raised.

    Parameters
    ----------
    trends : pd.DataFrame
        A dataframe containing longterm trends (derivative time series).
        Should contain columns "start_dates", "end_dates", "changes"
    calibration_timeseries : pd.DataFrame
        A dataframe containing a higher resolution timeseries (derivative time series).
        Should contain columns "start_dates", "end_dates", "changes"

    Returns
    -------
    Tuple(np.array[[]], np.array[[]])
        Returns a tuple of two 2D lists
        1.) 2D array with calibrated series
            will contain the dimensions of: (a) the trends dataframe length and (b) length of calibarion_timeseries
        2.) 2D array with a distance matrix for inverse distance calculations
            will contain the same dimensions as (1)
    """
    calibrated_timeseries_list = []  # will be populated with each longterm trend calibrated series
    distance_matrix_list = []
    for _, longterm_trend in trends.iterrows():
        # make sure that the longterm trend is within the calibration series
        if (min(calibration_timeseries["start_dates"]) <= longterm_trend["start_dates"]) \
                and (max(calibration_timeseries["end_dates"]) >= longterm_trend["end_dates"]):
            # get slice of the high resolution calibration dataset corresponding to the trend timeperiod
            calibration_slice = calibration_timeseries[((calibration_timeseries["start_dates"]
                                                        >= longterm_trend["start_dates"])
                                                        & (calibration_timeseries["end_dates"]
                                                           <= longterm_trend["end_dates"]))]
            # average of the high resolution calibratio timeseries over shared period
            avg_calibration_slice = calibration_slice["changes"].mean()
            # resample to same resolution as the calibration timeseries
            avg_trend = longterm_trend['changes'] / calibration_slice["changes"].shape[0]
            # calculate correction and apply to the calibration timeseries
            correction = avg_trend - avg_calibration_slice
            calibrated_timeseries_list.append(calibration_timeseries["changes"] + correction)

            # Create distance to observation period of the trend within the time grid of the calibration timeseries
            # note that 1 year is added for the inverse distance calculation,
            # so that it has a value of 1 when it is within the time period
            temporal_resolution = calibration_timeseries["start_dates"].iloc[1] - \
                calibration_timeseries["start_dates"].iloc[0]
            distance_matrix_list.append([get_distance_to_timeperiod(float(year), longterm_trend['start_dates'],
                                                                    longterm_trend['end_dates'],
                                                                    resolution=temporal_resolution) + 1.0
                                        for year in calibration_timeseries["start_dates"]])
        else:
            warnings.warn("Trend is outside calibration timeseries (fully or partly) and will be ignored. "
                          "trend_start={} , trend_end={}, calibration_series_start={}, calibration_series_end={}"
                          .format(longterm_trend["start_dates"], longterm_trend["end_dates"],
                                  min(calibration_timeseries["start_dates"]), max(calibration_timeseries["end_dates"])))

    return np.array(calibrated_timeseries_list), np.array(distance_matrix_list)


def combine_calibrated_timeseries(calibrated_series: np.array, distance_matrix: np.array, p_value: int = 2):
    """
    Combines a set of calibrated time series with inverse distance weights

    Parameters
    ----------
    calibrated_series : np.array
        2D array with calibrated series, e.g. return from calibrate_timeseries_with_trends()
    distance_matrix : np.array
        2D array with distance matrix to the timeperiod of the trend dataset,
        e.g. return from calibrate_timeseries_with_trends()
    p_value : int, optional
        p value to calculate distance weight, higher values equal higher slope from the time period/
        by default 2

    Returns
    -------
    np.array
        Mean calibrated series
    """
    # calculate inverse distance weight
    distance_weight = [(1 / np.array(x))**p_value for x in distance_matrix]
    # convert to percentages
    distance_weight_perc = np.array(distance_weight) / [sum(x) for x in zip(*distance_weight)]
    # apply distance weight
    weighted_calibrated_series = np.array(calibrated_series) * np.array(distance_weight_perc)
    # return sum of all distance weighted series (= mean timeseries)
    return np.array([sum(x) for x in zip(*weighted_calibrated_series)])


def get_distance_to_timeperiod(date: float,
                               period_start_date: float,
                               period_end_date: float,
                               resolution: float = 1 / 12) -> float:
    """
    Calculates the distance to a time period in years for distance weighting.

    Parameters
    ----------
    date : float
        date to calculate the distance in fractional years
        date is assumed to be at the start within a time series (and not the middle of a timestep)
        i.e. date is a start_date
    period_start_date : float
        start of timeperiod in fractional years
    period_end_date : float
        end of timeperiod in fractional years
    resolution : float, optional
        resolution of date, this is added to all values later than the time period,
        to account for the case where date is assumed a start_date within a timeseries (and not the middle)
        by default 1/12 (one month)

    Returns
    -------
    float
        Distance to time period in fractional years
    """
    if date >= period_end_date:
        return date - period_end_date + resolution  # add an extra data point since we are assuming it is a start_date
    if date < period_start_date:
        return period_start_date - date
    else:
        return 0.0
