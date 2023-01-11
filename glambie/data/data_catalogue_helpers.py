from glambie.data.data_catalogue import DataCatalogue
import pandas as pd
import numpy as np
from glambie.util.timeseries_combination_helpers import calibrate_timeseries_with_trends, combine_calibrated_timeseries
from glambie.data.timeseries import TimeseriesData, Timeseries
import copy


def calibrate_timeseries_with_trends_catalogue(catalogue_with_trends: DataCatalogue,
                                               calibration_timeseries: Timeseries) -> DataCatalogue:
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
    """

    # calibrate annual trends with longterm trend
    calibrated_series = []
    for ds in catalogue_with_trends.datasets:
        # 1) calibrate timeseries
        calibrated_s, dist_mat = calibrate_timeseries_with_trends(ds.data.as_dataframe(),
                                                                  calibration_timeseries.data.as_dataframe())
        # 2) caliculate mean calibration timeseries from all the different curves
        mean_calibrated_ts = combine_calibrated_timeseries(calibrated_s, dist_mat, p_value=0)
        df_mean_calibrated = pd.DataFrame({"start_dates": calibration_timeseries.data
                                           .as_dataframe().start_dates,
                                           "end_dates": calibration_timeseries.data
                                           .as_dataframe().end_dates, "changes": mean_calibrated_ts})
        df_mean_calibrated = df_mean_calibrated[~df_mean_calibrated["changes"].isna()]
        ds_copy = copy.deepcopy(ds)
        ds_copy.data = TimeseriesData(start_dates=np.array(df_mean_calibrated["start_dates"]),
                                      end_dates=np.array(df_mean_calibrated["end_dates"]),
                                      changes=np.array(df_mean_calibrated["changes"]),
                                      errors=None, glacier_area_observed=None,
                                      glacier_area_reference=None)
        calibrated_series.append(ds_copy)

    catalogue_calibrated_series = DataCatalogue.from_list(calibrated_series)
    return catalogue_calibrated_series
