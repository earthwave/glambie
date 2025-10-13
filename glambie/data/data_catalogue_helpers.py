from glambie.data.data_catalogue import DataCatalogue
import pandas as pd
import numpy as np
from glambie.util.timeseries_combination_helpers import (
    calibrate_timeseries_with_trends,
    combine_calibrated_timeseries,
)
from glambie.data.timeseries import TimeseriesData, Timeseries
import copy


def calibrate_timeseries_with_trends_catalogue(
    catalogue_with_trends: DataCatalogue, calibration_timeseries: Timeseries
) -> DataCatalogue:
    """
    Calibrates a Timeseries of higher resolution varibility with a DataCatalogue of Timeseries of longer-term trends.

    Parameters
    ----------
    catalogue_with_trends : DataCatalogue
        DataCatalogue containing a set of long-term trends.
    calibration_timeseries : Timeseries
        Timeseries used for calibration. Should be higher resolution and homogenized.

    Returns
    -------
    DataCatalogue
        Containing all the calibrated Timeseries. Contains the same length of datasets as catalogue_with_trends.

    Raises
    ------
        AssertionError
            If trends are not all the same unit.
    """

    if not catalogue_with_trends.datasets_are_same_unit():
        raise AssertionError(
            "Trends within catalogue all need to be the same unit before performing this operation."
        )

    # calibrate annual trends with longterm trend
    calibrated_series = []
    for ds in catalogue_with_trends.datasets:
        # 1) calibrate timeseries
        calibrated_s, dist_mat = calibrate_timeseries_with_trends(
            ds.data.as_dataframe(), calibration_timeseries.data.as_dataframe()
        )
        # 2) calculate mean calibration timeseries from all the different curves
        mean_calibrated_ts = combine_calibrated_timeseries(
            calibrated_s,
            dist_mat,
            p_value=0,
            calculate_outside_calibrated_series_period=False,
        )
        df_mean_calibrated = pd.DataFrame(
            {
                "start_dates": calibration_timeseries.data.as_dataframe().start_dates,
                "end_dates": calibration_timeseries.data.as_dataframe().end_dates,
                "changes": mean_calibrated_ts,
            }
        )
        df_mean_calibrated_na_removed = df_mean_calibrated[
            ~df_mean_calibrated["changes"].isna()
        ]

        # CALCULATE UNCERTAINTIES
        # The uncertainty of a calibrated time series is calculated by combining
        # the uncertainties of the anomalies and of the long-term trend
        df_trends = ds.data.as_dataframe()
        trend_uncertainties = df_trends.errors  # remove na lines
        calibration_timeseries_uncertainties = calibration_timeseries.data.errors[
            ~df_mean_calibrated["changes"].isna()
        ]
        # now convert trend uncertainties to same temporal unit as calibration_timeseries, e.g. annual
        trend_timeperiod = np.mean(df_trends.end_dates - df_trends.start_dates)
        desired_timeperiod = calibration_timeseries.data.max_temporal_resolution
        trend_error_resampled = trend_uncertainties * (
            desired_timeperiod / trend_timeperiod
        )
        df_trends["error_resampled"] = trend_error_resampled
        trend_uncertainties_resampled = []
        # add the correct uncertainties to match the years from the calibrated timeseries
        for _, row in df_mean_calibrated_na_removed.iterrows():
            err = df_trends[
                (row.start_dates >= df_trends.start_dates)
                & (row.end_dates <= df_trends.end_dates)
            ].error_resampled.iloc[0]
            trend_uncertainties_resampled.append(err)
        # combine both uncertainties following the law of random error propagation
        uncertainties_calibrated_series = (
            np.array(trend_uncertainties_resampled) ** 2
            + np.array(calibration_timeseries_uncertainties) ** 2
        ) ** 0.5

        ds_copy = copy.deepcopy(ds)
        ds_copy.data = TimeseriesData(
            start_dates=np.array(df_mean_calibrated_na_removed["start_dates"]),
            end_dates=np.array(df_mean_calibrated_na_removed["end_dates"]),
            changes=np.array(df_mean_calibrated_na_removed["changes"]),
            errors=np.array(uncertainties_calibrated_series),
            glacier_area_observed=None,
            glacier_area_reference=None,
            hydrological_correction_value=None,
            remarks=None,
        )
        calibrated_series.append(ds_copy)

    catalogue_calibrated_series = DataCatalogue.from_list(calibrated_series)
    return catalogue_calibrated_series
