import logging
from typing import Tuple

from glambie.config.config_classes import RegionRunConfig
from glambie.data.data_catalogue import DataCatalogue
from glambie.const.data_groups import GLAMBIE_DATA_GROUPS, GlambieDataGroup
from glambie.data.timeseries import Timeseries
from glambie.const.constants import YearType
import numpy as np
import pandas as pd

log = logging.getLogger(__name__)


def filter_catalogue_with_config_settings(data_group: GlambieDataGroup,
                                          region_config: RegionRunConfig,
                                          data_catalogue: DataCatalogue) -> Tuple[DataCatalogue, DataCatalogue]:
    """
    Filters data catalogue by the "exclude_trend_datasets" and "exclude_annual_datasets" config settings

    Parameters
    ----------
    data_group : GlambieDataGroup
        data group for which we filter the datasets, catalogue will also be filtered by data group
    region_config : RegionRunConfig
        region config file which includes a list of data sets to exclude from the catalogue
    data_catalogue : DataCatalogue
        original data catalogue to be filtered

    Returns
    -------
    Tuple[DataCatalogue, DataCatalogue]
        Tuple[data_catalogue_annual, data_catalogue_trend]
        the filtered catalogue for annual datasets and for longterm trend datasets
    """
    # 1 filter by data group - just in case it hasn't already been done
    if data_group != GLAMBIE_DATA_GROUPS["demdiff_and_glaciological"]:
        data_catalogue = data_catalogue.get_filtered_catalogue(
            data_group=data_group.name)
    else:
        data_catalogue_demdiff = data_catalogue.get_filtered_catalogue(
            data_group=GLAMBIE_DATA_GROUPS["demdiff"].name)
        data_catalogue_glaciological = data_catalogue.get_filtered_catalogue(
            data_group=GLAMBIE_DATA_GROUPS["glaciological"].name)
        # concatenate demdiff and glaciological into one
        data_catalogue = DataCatalogue.from_list(data_catalogue_demdiff.datasets
                                                 + data_catalogue_glaciological.datasets,
                                                 base_path=data_catalogue.base_path)
    # 2 filter out what has been specified in config for annual datasets
    datasets_annual = data_catalogue.datasets.copy()
    exclude_annual_datasets = region_config.region_run_settings[data_group.name].get("exclude_annual_datasets", [])
    log.info('Excluding the following datasets from ANNUAL calculations: datasets=%s', exclude_annual_datasets)
    for ds in exclude_annual_datasets:
        datasets_annual = [d for d in datasets_annual if d.user_group.lower() != ds.lower()]
    if data_group == GLAMBIE_DATA_GROUPS["demdiff_and_glaciological"]:
        datasets_annual = [d for d in datasets_annual if d.data_group != GLAMBIE_DATA_GROUPS["demdiff"]]

    # 3 filter out what has been specified in config for longterm trend datasets
    datasets_trend = data_catalogue.datasets.copy()
    exclude_trend_datasets = region_config.region_run_settings[data_group.name].get("exclude_trend_datasets", [])
    log.info('Excluding the following datasets from TREND calculations: datasets=%s', exclude_trend_datasets)
    for ds in exclude_trend_datasets:
        datasets_trend = [d for d in datasets_trend if d.user_group.lower() != ds.lower()]
    if data_group == GLAMBIE_DATA_GROUPS["demdiff_and_glaciological"]:
        datasets_trend = [d for d in datasets_trend if d.data_group != GLAMBIE_DATA_GROUPS["glaciological"]]

    data_catalogue_annual = DataCatalogue.from_list(datasets_annual, base_path=data_catalogue.base_path)
    data_catalogue_trend = DataCatalogue.from_list(datasets_trend, base_path=data_catalogue.base_path)

    return data_catalogue_annual, data_catalogue_trend


def convert_datasets_to_monthly_grid(data_catalogue: DataCatalogue) -> DataCatalogue:
    """
    Convert all datasets in data catalogue to monthly grid

    Parameters
    ----------
    data_catalogue : DataCatalogue
        data catalogue to be converted

    Returns
    -------
    DataCatalogue
        New data catalogue with converted data
    """
    datasets = []
    for ds in data_catalogue.datasets:
        datasets.append(ds.convert_timeseries_to_monthly_grid())
    catalogue_monthly_grid = DataCatalogue.from_list(datasets, base_path=data_catalogue.base_path)
    return catalogue_monthly_grid


def convert_datasets_to_annual_trends(data_catalogue: DataCatalogue, year_type: YearType,
                                      season_calibration_dataset: Timeseries) -> DataCatalogue:
    """
    Convert all datasets in data catalogue to annual trends

    Parameters
    ----------
    data_catalogue : DataCatalogue
        data catalogue to be converted

    year_type : YearType
        type of annual year, e.g hydrological or calendar

    Returns
    -------
    DataCatalogue
        New data catalogue with converted data
    """
    data_catalogue = convert_datasets_to_monthly_grid(data_catalogue)
    datasets = []
    for ds in data_catalogue.datasets:
        if (ds.data.max_temporal_resolution == 1) and (ds.data.min_temporal_resolution == 1):
            ds = ds.convert_timeseries_to_unit_mwe()
            datasets.append(ds.convert_timeseries_using_seasonal_homogenization(
                seasonal_calibration_dataset=season_calibration_dataset, year_type=year_type, p_value=0))
        else:
            datasets.append(ds.convert_timeseries_to_annual_trends(year_type=year_type))

    catalogue_annual_grid = DataCatalogue.from_list(datasets, base_path=data_catalogue.base_path)
    return catalogue_annual_grid


def convert_datasets_to_longterm_trends(data_catalogue: DataCatalogue, year_type: YearType,
                                        season_calibration_dataset: Timeseries) -> DataCatalogue:
    """
    Convert all datasets in data catalogue to longterm trends

    Parameters
    ----------
    data_catalogue : DataCatalogue
        data catalogue to be converted

    year_type : YearType
        type of annual year when longterm timeseries should start and end, e.g hydrological or calendar

    Returns
    -------
    DataCatalogue
        New data catalogue with converted data
    """
    data_catalogue = convert_datasets_to_monthly_grid(data_catalogue)
    data_catalogue_original = data_catalogue.copy()
    datasets = []
    for idx, ds in enumerate(data_catalogue.datasets):
        if data_catalogue_original.datasets[idx].data.max_temporal_resolution > 1:
            ds = data_catalogue_original.datasets[idx].convert_timeseries_to_unit_mwe()
            datasets.append(ds.convert_timeseries_using_seasonal_homogenization(
                seasonal_calibration_dataset=season_calibration_dataset, year_type=year_type, p_value=0))
        else:
            ds = ds.convert_timeseries_to_annual_trends(year_type=year_type)
            datasets.append(ds.convert_timeseries_to_longterm_trend())
    catalogue_trends = DataCatalogue.from_list(datasets, base_path=data_catalogue.base_path)
    return catalogue_trends


def convert_datasets_to_unit_mwe(data_catalogue: DataCatalogue) -> DataCatalogue:
    """
    Convert all datasets in data catalogue to unit mwe (meter water equivalent)

    Parameters
    ----------
    data_catalogue : DataCatalogue
        data catalogue to be converted

    Returns
    -------
    DataCatalogue
        New data catalogue with converted data
    """
    datasets = []
    for ds in data_catalogue.datasets:
        datasets.append(ds.convert_timeseries_to_unit_mwe())
    catalogue_mwe = DataCatalogue.from_list(datasets, base_path=data_catalogue.base_path)
    return catalogue_mwe


def prepare_seasonal_calibration_dataset(region_config: RegionRunConfig,
                                         data_catalogue: DataCatalogue) -> Timeseries:
    # get seasonal calibration dataset and convert to monthly grid
    season_calibration_dataset = data_catalogue.get_filtered_catalogue(
        user_group=region_config.seasonal_correction_dataset["user_group"],
        data_group=region_config.seasonal_correction_dataset["data_group"]).datasets[0]
    season_calibration_dataset.load_data()
    season_calibration_dataset = season_calibration_dataset.convert_timeseries_to_monthly_grid()
    season_calibration_dataset = season_calibration_dataset.convert_timeseries_to_unit_mwe()
    return season_calibration_dataset


def extend_annual_timeseries_if_outside_trends_period(annual_timeseries: Timeseries,
                                                      data_catalogue_trends: DataCatalogue,
                                                      timeseries_for_extension: Timeseries) -> Timeseries:
    for ds in data_catalogue_trends.datasets:
        if (min(ds.data.start_dates) < min(annual_timeseries.data.start_dates)) \
                or (max(ds.data.end_dates) > max(annual_timeseries.data.end_dates)):
            log.info("Extension of annual is performed, as the trends are longer than the annual timeseries")
            # Combine with other  timeseries to cover the missing timespan
            object_copy = annual_timeseries.copy()
            df1 = annual_timeseries.data.as_dataframe()
            df2 = timeseries_for_extension.data.as_dataframe()
            df_merged = pd.merge(df1, df2, on=["start_dates", "end_dates"], how="outer")
            df_merged.changes_x.fillna(df_merged.changes_y, inplace=True)
            df_merged.errors_x.fillna(df_merged.errors_y, inplace=True)
            df_merged = df_merged.sort_values(by="start_dates").reset_index()
            object_copy.data.changes = np.array(df_merged["changes_x"])
            object_copy.data.errors = np.array(df_merged["errors_x"])
            object_copy.data.start_dates = np.array(df_merged["start_dates"])
            object_copy.data.end_dates = np.array(df_merged["end_dates"])
            annual_timeseries = object_copy
    return annual_timeseries
