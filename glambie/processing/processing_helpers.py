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


def convert_datasets_to_annual_trends(data_catalogue: DataCatalogue,
                                      year_type: YearType,
                                      season_calibration_dataset: Timeseries) -> DataCatalogue:
    """
    Convert all datasets in data catalogue to annual trends.
    If an input dataset within the catalogue is at annual resolution, seasonal homogenization is performed.
    Otherwise the annual timeseries is directly extracted from timeseries.

    Parameters
    ----------
    data_catalogue : DataCatalogue
        data catalogue to be converted

    year_type : YearType
        type of annual year, e.g hydrological or calendar

    season_calibration_dataset: Timeseries
        Timeseries dataset for seasonal calibration if trends are at annual resolution.

    Returns
    -------
    DataCatalogue
        New data catalogue with converted data
    """
    data_catalogue = convert_datasets_to_monthly_grid(data_catalogue)
    datasets = []
    for ds in data_catalogue.datasets:
        if ds.data.max_temporal_resolution == ds.data.min_temporal_resolution == 1:
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
    Convert all datasets in data catalogue to longterm trends.
    If dataset in catalogue has a lower resolution than a year, seasonal homogenization is used.
    Otherwise the trend is directly extracted for the higher resolution timeseries.

    Parameters
    ----------
    data_catalogue : DataCatalogue
        data catalogue to be converted

    year_type : YearType
        type of annual year when longterm timeseries should start and end, e.g hydrological or calendar

    season_calibration_dataset: Timeseries
        Timeseries dataset for seasonal calibration if trends are at lower resolution than 1 year.

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
    """
    Retrieves and prepares the seasonal calibration dataset from a data catalogue.

    In this function the seasonal calibration dataset is loaded, standardised date axis to a monthly grid
    and then converted to unit mwe

    Parameters
    ----------
    region_config : RegionRunConfig
        region config object, containing information on seasonal calibration dataset
    data_catalogue : DataCatalogue
        data catalogue, should contain the seasonal calibration dataset

    Returns
    -------
    Timeseries
        the seasonal calibration dataset
    """
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
    """
    Extends an annual timeseries with another annual timeseries in case the given trends span longer
    than the annual dataset.
    Assumes that 'annual_timeseries' and 'timeseries_for_extension' both follow the same annual grid.

    Parameters
    ----------
    annual_timeseries : Timeseries
        annual timeseries to be extended
    data_catalogue_trends : DataCatalogue
        trends timeseries te be used as a measure of the span the annual timeseries should have
    timeseries_for_extension : Timeseries
        timeseries to be used to extend annual_timeseries

    Returns
    -------
    Timeseries
        Extended annual timeseries.
        If trends are within 'annual_timeseries' this will be the same as 'annual_timeseries'
    """
    annual_timeseries_copy = annual_timeseries.copy()
    for ds in data_catalogue_trends.datasets:
        if (min(ds.data.start_dates) < min(annual_timeseries_copy.data.start_dates)) \
                or (max(ds.data.end_dates) > max(annual_timeseries_copy.data.end_dates)):
            log.info("Extension of annual is performed, as the trends are longer than the annual timeseries")
            # Combine with other timeseries to cover the missing timespan
            df_merged = pd.merge(annual_timeseries_copy.data.as_dataframe(),
                                 timeseries_for_extension.data.as_dataframe(),
                                 on=["start_dates", "end_dates"], how="outer")
            # Fill Nans in 'annual_timeseries' with values from 'timeseries_for_extension'
            df_merged.changes_x.fillna(df_merged.changes_y, inplace=True)
            df_merged.errors_x.fillna(df_merged.errors_y, inplace=True)
            df_merged = df_merged.sort_values(by="start_dates").reset_index()
            # now update the annual timeseries object with the extended timeseries
            annual_timeseries_copy.data.changes = np.array(df_merged["changes_x"])
            annual_timeseries_copy.data.errors = np.array(df_merged["errors_x"])
            annual_timeseries_copy.data.start_dates = np.array(df_merged["start_dates"])
            annual_timeseries_copy.data.end_dates = np.array(df_merged["end_dates"])
            return annual_timeseries_copy
    return annual_timeseries_copy


def check_and_handle_gaps_in_timeseries(data_catalogue: DataCatalogue) -> DataCatalogue:
    new_datasets = []
    for timeseries in data_catalogue.datasets:
        if not timeseries.data.is_cumulative_valid():  # if invalid convert to handle the gaps
            # 1 split timeseries dataframe
            df_data = timeseries.data.as_dataframe()
            split_dataframes = split_timeseries_at_gaps(df_data)
            # 2 add split timeseries to new_datasets
            for split_timeseries in split_dataframes:
                timeseries_copy = timeseries.copy()
                timeseries_copy.data.changes = np.array(split_timeseries["changes"])
                timeseries_copy.data.errors = np.array(split_timeseries["errors"])
                timeseries_copy.data.start_dates = np.array(split_timeseries["start_dates"])
                timeseries_copy.data.end_dates = np.array(split_timeseries["end_dates"])
                timeseries_copy.data.glacier_area_observed = None
                timeseries_copy.data.glacier_area_reference = None
                new_datasets.append(timeseries_copy)
        else:  # or else append original
            new_datasets.append(timeseries)

    new_data_catalogue = DataCatalogue.from_list(new_datasets, base_path=data_catalogue.base_path)
    return new_data_catalogue


def split_timeseries_at_gaps(df_timeseries: pd.DataFrame) -> list[pd.DataFrame]:
    split_indices = []
    split_timeseries_dataframes = []
    for idx, end_date in enumerate(df_timeseries["end_dates"].iloc[:-1]):
        # If end_date != start_date for any of the consecutive rows, append to indices where df is split
        if end_date != df_timeseries["start_dates"].iloc[idx + 1]:
            split_indices.append(idx)
    previous_index = 0
    for split_index in split_indices:
        split_timeseries_dataframes.append(df_timeseries.iloc[previous_index:split_index + 1].reset_index(drop=True))
        previous_index = split_index + 1
    # plus append last / full split in the end
    split_timeseries_dataframes.append(df_timeseries.iloc[previous_index:].reset_index(drop=True))
    return split_timeseries_dataframes
