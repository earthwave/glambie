import logging
from typing import Tuple

from glambie.config.config_classes import RegionRunConfig
from glambie.const import constants
from glambie.data.data_catalogue import DataCatalogue
from glambie.const.data_groups import GLAMBIE_DATA_GROUPS, GlambieDataGroup
from glambie.data.timeseries import Timeseries
from glambie.const.constants import ExtractTrendsMethod, YearType, SeasonalCorrectionMethod
from glambie.util.date_helpers import get_years
import numpy as np
import pandas as pd
import warnings

log = logging.getLogger(__name__)


def filter_catalogue_with_config_settings(data_group: GlambieDataGroup,
                                          region_config: RegionRunConfig,
                                          data_catalogue: DataCatalogue) -> Tuple[DataCatalogue, DataCatalogue]:
    """
    Filters data catalogue by the 'exclude_trend_datasets' and 'exclude_annual_datasets' config settings

    Adds combined datasets to other data groups via the 'include_combined_trend_datasets' and
    'include_combined_trend_datasets' config settings
    An asterix is added to the user_group name of combined solutions so that they are recognized as combined solutions
    by their name

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
    data_catalogue_original = data_catalogue.copy()

    # 1 filter by data group and region
    if data_group != GLAMBIE_DATA_GROUPS["demdiff_and_glaciological"]:
        data_catalogue = data_catalogue.get_filtered_catalogue(
            data_group=data_group.name, region_name=region_config.region_name)
    else:
        data_catalogue_demdiff = data_catalogue.get_filtered_catalogue(
            data_group=GLAMBIE_DATA_GROUPS["demdiff"].name, region_name=region_config.region_name)
        data_catalogue_glaciological = data_catalogue.get_filtered_catalogue(
            data_group=GLAMBIE_DATA_GROUPS["glaciological"].name, region_name=region_config.region_name)
        # concatenate demdiff and glaciological into one
        data_catalogue = DataCatalogue.from_list(data_catalogue_demdiff.datasets
                                                 + data_catalogue_glaciological.datasets,
                                                 base_path=data_catalogue.base_path)
    # 2 filter out what has been specified in config for annual datasets
    datasets_annual = data_catalogue.datasets.copy()
    exclude_annual_datasets = region_config.region_run_settings[data_group.name].get("exclude_annual_datasets", [])
    log.info('Excluding the following datasets from ANNUAL calculations: datasets=%s', exclude_annual_datasets)
    for ds in exclude_annual_datasets:
        if ds is not None:
            datasets_annual = [d for d in datasets_annual if d.user_group.lower() != ds.lower()]
    if data_group == GLAMBIE_DATA_GROUPS["demdiff_and_glaciological"]:
        datasets_annual = [d for d in datasets_annual if d.data_group != GLAMBIE_DATA_GROUPS["demdiff"]]

    # 3 filter out what has been specified in config for longterm trend datasets
    datasets_trend = data_catalogue.datasets.copy()
    exclude_trend_datasets = region_config.region_run_settings[data_group.name].get("exclude_trend_datasets", [])
    log.info('Excluding the following datasets from TREND calculations: datasets=%s', exclude_trend_datasets)
    for ds in exclude_trend_datasets:
        if ds is not None:
            datasets_trend = [d for d in datasets_trend if d.user_group.lower() != ds.lower()]
    if data_group == GLAMBIE_DATA_GROUPS["demdiff_and_glaciological"]:
        datasets_trend = [d for d in datasets_trend if d.data_group != GLAMBIE_DATA_GROUPS["glaciological"]]

    # 4 add additional combined datasets stated in configs to data group
    additional_annual_datasets = get_additional_combined_datasets(
        data_catalogue=data_catalogue_original, data_group=data_group,
        region_config=region_config, type_of_information="annual")
    additional_trend_datasets = get_additional_combined_datasets(
        data_catalogue=data_catalogue_original, data_group=data_group,
        region_config=region_config, type_of_information="trend")
    # combined solution should have a symbol so that they are recognized in the plots
    for ds in additional_annual_datasets:
        ds.user_group = ds.user_group + "_#"
    for ds in additional_trend_datasets:
        if ds not in additional_annual_datasets:
            ds.user_group = ds.user_group + "_#"

    datasets_annual.extend(additional_annual_datasets)
    datasets_trend.extend(additional_trend_datasets)
    log.info('Including the following combined datasets to ANNUAL calculations: datasets=%s',
             additional_annual_datasets)
    log.info('Including the following combined datasets to TREND calculations: datasets=%s', additional_trend_datasets)

    data_catalogue_annual = DataCatalogue.from_list(datasets_annual, base_path=data_catalogue.base_path)
    data_catalogue_trend = DataCatalogue.from_list(datasets_trend, base_path=data_catalogue.base_path)

    return data_catalogue_annual, data_catalogue_trend


def get_additional_combined_datasets(data_catalogue: DataCatalogue, data_group: GlambieDataGroup,
                                     region_config: RegionRunConfig, type_of_information: str) -> list[Timeseries]:
    """
    Returns a list of combined datasets to be added to a data group using the run config

    Parameters
    ----------
    data_catalogue : DataCatalogue
        the catalogue containing the combined datasets
    data_group : GlambieDataGroup
        the data group for which we want to add the combined datasets
    region_config : RegionRunConfig
        region config which will contain the information on which combined datasets to add
    type_of_information : str
        which category of information, i.e. either 'annual' or 'trend'

    Returns
    -------
    list[Timeseries]
        a list of Timeseries of the data source 'combined' which have been identified
    """
    additional_datasets = []
    if "include_combined_{}_datasets".format(type_of_information) in region_config.region_run_settings[data_group.name]:
        include_combined_datasets = region_config.region_run_settings[data_group.name].get(
            "include_combined_{}_datasets".format(type_of_information), [])
        include_combined_datasets = [x for x in include_combined_datasets if x is not None]
        for ds in include_combined_datasets:
            catalogue_filtered = data_catalogue.get_filtered_catalogue(
                data_group="combined", region_name=region_config.region_name, user_group=ds)
            if len(catalogue_filtered.datasets) > 0:
                additional_datasets.append(catalogue_filtered.datasets[0])
            else:
                log.info("Cannot find and add the following combined dataset to %s datasets: %s",
                         type_of_information, ds)
    return additional_datasets


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
                                      method_to_correct_seasonally: SeasonalCorrectionMethod,
                                      seasonal_calibration_dataset: Timeseries = None) -> DataCatalogue:
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
    method_to_correct_seasonally: SeasonalCorrectionMethod
        method as to how annual trends are corrected when they don't start in the desired season, i.e. don't follow
        the desired annual grid defined with 'year_type'
    seasonal_calibration_dataset: Timeseries, by default None
        Timeseries dataset for seasonal calibration if trends are at annual resolution. Will be ignored if seasonal
        correction method is not set to SeasonalCorrectionMethod.SEASONAL_HOMOGENIZATION

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

            # apply seasonal correction depending on settings given
            ds = apply_seasonal_correction_to_dataset(dataset_to_correct=ds,
                                                      method_to_correct_seasonally=method_to_correct_seasonally,
                                                      year_type=year_type,
                                                      seasonal_calibration_dataset=seasonal_calibration_dataset)

            datasets.append(ds)
        else:
            datasets.append(ds.convert_timeseries_to_annual_trends(year_type=year_type))

    catalogue_annual_grid = DataCatalogue.from_list(datasets, base_path=data_catalogue.base_path)
    return catalogue_annual_grid


def convert_datasets_to_longterm_trends_in_unit_mwe(
        data_catalogue: DataCatalogue, year_type: YearType,
        method_to_extract_trends: ExtractTrendsMethod,
        method_to_correct_seasonally: SeasonalCorrectionMethod,
        seasonal_calibration_dataset: Timeseries = None,
        output_trend_date_range: Tuple[float, float] = None) -> DataCatalogue:
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
    method_to_extract_trends: ExtractTrendsMethod:
        method as to how the long-term trends are extracted from a high resolution (e.g. monthly) timeseries
    method_to_correct_seasonally: SeasonalCorrectionMethod
        method as to how long-term trends are correct when they don't start in the desired season, i.e. don't follow
        the desired annual grid defined with 'year_type'
    seasonal_calibration_dataset: Timeseries, by default None
        Timeseries dataset for seasonal calibration if trends are at lower resolution than 1 year.
        Will be ignore if seasonal correction method is not set to SeasonalCorrectionMethod.SEASONAL_HOMOGENIZATION
    output_trend_date_range : Tuple[float, float], optional
        If specified, the time series are filtered by the time window before the longterm trend is extracted,
        meaning that the resulting longterm trends are within the minimum and maximum of the time window.
        Note that existing longterm trends are removed if the are outside the time window.
        The dates are expected in decimal years format (float), e.g. 2012.75.

    Returns
    -------
    DataCatalogue
        New data catalogue with converted data
    """
    data_catalogue = convert_datasets_to_monthly_grid(data_catalogue)
    datasets = []
    for original_dataset in data_catalogue.datasets:
        temporal_resolution = original_dataset.data.max_temporal_resolution
        # remove any dates outside minimum and maximum
        if output_trend_date_range is not None:
            ds = original_dataset.reduce_to_date_window(start_date=output_trend_date_range[0],
                                                        end_date=output_trend_date_range[1])
        else:
            ds = original_dataset

        # if temporal resolution lower than a year read from higher resolution timeseries
        # note that this assumes we now have monthly resolution.
        # The case that we have datasets that are < 1 year but > monthly they will need to be handled here in the future
        if temporal_resolution < 1:
            if year_type == constants.YearType.CALENDAR:
                year_start = 0
            elif year_type == constants.YearType.GLACIOLOGICAL:
                year_start = ds.region.glaciological_year_start
            new_start_dates, new_end_dates = get_years(year_start, min_date=ds.data.min_start_date,
                                                       max_date=ds.data.max_end_date, return_type="arrays")
            ds = ds.reduce_to_date_window(new_start_dates[0], new_end_dates[-1])
            ds = ds.convert_timeseries_to_longterm_trend(
                method_to_extract_trends=method_to_extract_trends).convert_timeseries_to_unit_mwe()

        # if temporal resolution is a year or higher, seaonal correction should be applied
        else:
            # if resolution 1 year, read longterm trend and then apply seasonal correction after
            if temporal_resolution == 1:
                ds = ds.convert_timeseries_to_longterm_trend(
                    method_to_extract_trends=ExtractTrendsMethod.START_VS_END)

            # now convert to mwe unit. This needs to be done here and not earlier due to the density uncertainties
            # for different time periods
            ds = ds.convert_timeseries_to_unit_mwe()

            # apply seasonal correction depending on settings given
            ds = apply_seasonal_correction_to_dataset(dataset_to_correct=ds,
                                                      method_to_correct_seasonally=method_to_correct_seasonally,
                                                      year_type=year_type,
                                                      seasonal_calibration_dataset=seasonal_calibration_dataset)

        datasets.append(ds)
    catalogue_trends = DataCatalogue.from_list(datasets, base_path=data_catalogue.base_path)
    return catalogue_trends


def apply_seasonal_correction_to_dataset(dataset_to_correct: Timeseries,
                                         method_to_correct_seasonally: SeasonalCorrectionMethod,
                                         year_type: constants.YearType,
                                         seasonal_calibration_dataset: Timeseries = None) -> Timeseries:
    """
    Performs seasonal homogenization to a datasets. i.e. if the input dataset does not follow

    Parameters
    ----------
    dataset_to_correct : Timeseries
        dataset to be corrected seasonally
    method_to_correct_seasonally : SeasonalCorrectionMethod
        method as to how long-term trends are correct when they don't start in the desired season, i.e. don't follow
        the desired annual grid defined with 'year_type'
    year_type : constants.YearType
        type of annual year, e.g hydrological or calendar
    seasonal_calibration_dataset : Timeseries, optional
        Timeseries dataset for seasonal calibration if trends are at annual resolution. Will be ignore if seasonal
        correction method is not set to SeasonalCorrectionMethod.SEASONAL_HOMOGENIZATION

    Convert all datasets in data catalogue to annual trends.
    If an input dataset within the catalogue is at annual resolution, seasonal homogenization is performed.
    Otherwise the annual timeseries is directly extracted from timeseries.

    Returns
    -------
    Timeseries
        a seasonally corrected timeseries dataset
    """
    if method_to_correct_seasonally == SeasonalCorrectionMethod.SEASONAL_HOMOGENIZATION:
        if seasonal_calibration_dataset is None:
            raise AssertionError("Seasonal calibration dataset is None, cannot perform operation.")
        corrected_dataset = dataset_to_correct.shift_timeseries_to_annual_grid_with_seasonal_homogenization(
            seasonal_calibration_dataset=seasonal_calibration_dataset, year_type=year_type, p_value=0)
    elif method_to_correct_seasonally == SeasonalCorrectionMethod.PROPORTIONAL:
        corrected_dataset = dataset_to_correct.shift_timeseries_to_annual_grid_proportionally(year_type=year_type)
    else:
        raise NotImplementedError("Seasonal correction method '{}' is not implemented yet."
                                  .format(method_to_correct_seasonally))
    return corrected_dataset


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


def convert_datasets_to_unit_gt(data_catalogue: DataCatalogue) -> DataCatalogue:
    """
    Convert all datasets in data catalogue to unit gt (Gigatonnes)

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
        # first remove area change
        ds = ds.apply_or_remove_area_change(apply_area_change=False)
        # then convert to gt with constant area
        datasets.append(ds.convert_timeseries_to_unit_gt())
    catalogue_gt = DataCatalogue.from_list(datasets, base_path=data_catalogue.base_path)
    return catalogue_gt


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


def extend_annual_timeseries_if_shorter_than_time_window(
        annual_timeseries: Timeseries,
        timeseries_for_extension: Timeseries,
        desired_time_window: Tuple[float, float]) -> Timeseries:
    """
    Extends an annual timeseries with another annual timeseries in case the given desired time window spans longer
    than the annual dataset. Also fills data daps within 'annual_timeseries' with data from 'timeseries_for_extension'.
    Assumes that 'annual_timeseries' and 'timeseries_for_extension' both follow the same annual grid.

    Parameters
    ----------
    annual_timeseries : Timeseries
        annual timeseries to be extended
    timeseries_for_extension : Timeseries
        timeseries to be used to extend annual_timeseries
    desired_time_window : Tuple[float, float]
        A tuple with the length of the desired timeseries in the form of [min_start_date, max_end_date]

    Returns
    -------
    Timeseries
        Extended annual timeseries.
        If the desired time window is within 'annual_timeseries' and 'annual_timeseries' does not have any data gaps
        this will be the same as 'annual_timeseries'
    """
    annual_timeseries_copy = annual_timeseries.copy()
    if (desired_time_window[0] < min(annual_timeseries_copy.data.start_dates)) \
            or (desired_time_window[1] > max(annual_timeseries_copy.data.end_dates)) \
            or not annual_timeseries_copy.data.is_cumulative_valid():  # or the case where the timeseries has a gap
        log.info("The trends are longer than the annual timeseries. Extension of annual will be performed.")

        # Remove trend of timeseries for extension over the common time period
        catalogue_dfs = [annual_timeseries_copy.data.as_dataframe(), timeseries_for_extension.data.as_dataframe()]
        start_ref_period = np.max([df.start_dates.min() for df in catalogue_dfs])
        end_ref_period = np.min([df.end_dates.max() for df in catalogue_dfs])
        if not start_ref_period < end_ref_period:
            warnings.warn("No common period detected when removing trends.", stacklevel=2)
        for df in catalogue_dfs:
            df_sub = df[(df["start_dates"] >= start_ref_period) & (df["end_dates"] <= end_ref_period)]
            df["changes"] = df["changes"] - df_sub["changes"].mean()  # edit the dataframe

        # Combine with other timeseries to cover the missing timespan
        df_merged = pd.merge(catalogue_dfs[0], catalogue_dfs[1], on=["start_dates", "end_dates"], how="outer")
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


def check_and_handle_gaps_in_timeseries(data_catalogue: DataCatalogue) -> Tuple[DataCatalogue, list[list]]:
    """
    Checks all datasets in a timeseries if they have a temporal gap, and if so, splits them up into multiple datasets
    without gaps. If no gaps are found, the datasets stay the same.
    User group names of the split datasets will have an underscore and then the sequence number appended
    to the original name

    Parameters
    ----------
    data_catalogue : DataCatalogue
        data catalogue with input datasets

    Returns
    -------
    Tuple[DataCatalogue, list[list]]
        - data catalogue with new datasets containing no gaps.
          will contain more datasets than input data catalogue when gaps were found.
        - list of lists containing the user group names of the datasets that have been split up
          e.g. [["rabbit_1", "rabbit_2"], ["seal_1", "seal_2", "seal_3"]]
    """
    new_datasets = []
    list_of_split_series = []
    for timeseries in data_catalogue.datasets:
        if not timeseries.data.is_cumulative_valid():  # if invalid convert to handle the gaps
            # 1 split timeseries dataframe
            df_data = timeseries.data.as_dataframe()
            split_dataframes = slice_timeseries_at_gaps(df_data)
            # 2 add split timeseries to new_datasets
            grouped_timeseries = []
            for idx, split_timeseries in enumerate(split_dataframes):
                timeseries_copy = timeseries.copy()
                # rename user group name to be unique
                timeseries_copy.user_group = f"{timeseries_copy.user_group }_{str(idx+1)}"
                timeseries_copy.data.changes = np.array(split_timeseries["changes"])
                timeseries_copy.data.errors = np.array(split_timeseries["errors"])
                timeseries_copy.data.start_dates = np.array(split_timeseries["start_dates"])
                timeseries_copy.data.end_dates = np.array(split_timeseries["end_dates"])
                new_datasets.append(timeseries_copy)
                grouped_timeseries.append(timeseries_copy.user_group)
            list_of_split_series.append(grouped_timeseries)
        else:  # or else append original
            new_datasets.append(timeseries)

    new_data_catalogue = DataCatalogue.from_list(new_datasets, base_path=data_catalogue.base_path)
    return new_data_catalogue, list_of_split_series


def slice_timeseries_at_gaps(df_timeseries: pd.DataFrame) -> list[pd.DataFrame]:
    """
    Splits a dataframe into separate chunks/slices to remove temporal gaps in the timeseries.

    Parameters
    ----------
    df_timeseries : pd.DataFrame
        pandas dataframe containing a timeseries and the columns 'start_dates' and 'end_dates'.
        If 'end_date' != 'start_date' for any consecutive rows this is considered as a time gap.

    Returns
    -------
    list[pd.DataFrame]
        a list with slices of the original dataframe. All new dataframes within the list are gapless.
    """
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


def recombine_split_timeseries_in_catalogue(data_catalogue: DataCatalogue,
                                            names_of_split_datasets_in_catalogue: list[list]) -> DataCatalogue:
    """
    Combines a list of split timeseries back into full timeseries
    Can be used after gaps have been removed

    Parameters
    ----------
    data_catalogue : DataCatalogue
        input data catalogue which potentially have been split up due to gaps
    names_of_split_datasets_in_catalogue : list[list]
        list with user group names of datasets within the data catalogue that have been split
        e.g. [["rabbit_1", "rabbit_2"], ["seal_1", "seal_2", "seal_3"]]

    Returns
    -------
    DataCatalogue
        data catalogue with timeseries that are now recombined
    """
    new_datasets = []
    # split datasets
    for split_ds_list in names_of_split_datasets_in_catalogue:
        old_datasets = [data_catalogue.get_filtered_catalogue(user_group=s).datasets[0] for s in split_ds_list]
        start_dates = []
        end_dates = []
        changes = []
        errors = []
        for ds in old_datasets:
            start_dates.extend(ds.data.start_dates)
            end_dates.extend(ds.data.end_dates)
            changes.extend(ds.data.changes)
            errors.extend(ds.data.errors)
        df = pd.DataFrame({"start_dates": start_dates, "end_dates": end_dates,
                           "changes": changes, "errors": errors})
        df = df.sort_values(by="start_dates")
        if len(start_dates) != len(np.unique(start_dates)) or len(end_dates) != len(np.unique(end_dates)):
            error_msg = f'''Issue with combining split datasets, duplicate dates discovered when combining:
            {split_ds_list}'''
            log.error(error_msg)
            raise ValueError(error_msg)

        # copy the metadata to the new combined dataset. we just take the first dataset of old datasets assuming all
        # split datasets have the same metadata as they have been split from the same original dataset
        new_dataset = old_datasets[0].copy()
        # fill dataset with new values
        new_dataset.data.start_dates = np.array(df["start_dates"])
        new_dataset.data.end_dates = np.array(df["end_dates"])
        new_dataset.data.changes = np.array(df["changes"])
        new_dataset.data.errors = np.array(df["errors"])
        new_dataset.user_group = new_dataset.user_group[:-2]  # remove the underscore and numbering from the name
        new_datasets.append(new_dataset)

    # now add all datasets to list that weren't split
    for dataset in data_catalogue.datasets:
        # check if in flattened list
        if dataset.user_group not in [j for sub in names_of_split_datasets_in_catalogue for j in sub]:
            new_datasets.append(dataset)

    new_data_catalogue = DataCatalogue.from_list(new_datasets, base_path=data_catalogue.base_path)
    return new_data_catalogue


def set_unneeded_columns_to_nan(data_catalogue: DataCatalogue) -> DataCatalogue:
    """
    Sets data columns of TimeseriesData not needed in GlaMBIE processing algorithm to NaN within a DataCatalogue
    to simplify object manipulation

    Parameters
    ----------
    data_catalogue : DataCatalogue
        input data catalogue with Timeseries datasets to be manipulated

    Returns
    -------
    DataCatalogue
        manipulated data catalogue
    """
    result_catalogue = data_catalogue.copy()
    for timeseries in result_catalogue.datasets:
        timeseries.data.glacier_area_observed = None
        timeseries.data.glacier_area_reference = None
        timeseries.data.hydrological_correction_value = None
        timeseries.data.remarks = None
    return result_catalogue


def get_reduced_catalogue_to_date_window(data_catalogue: DataCatalogue,
                                         start_date: float,
                                         end_date: float,
                                         date_window_is_gap: bool = False) -> DataCatalogue:
    """
    Reduces all datasets within a data catalogue to desired minimum and maximum dates

    Parameters
    ----------
    data_catalogue : DataCatalogue
        input data catalogue with datasets
    start_date : float
        desired start date of output datasets
    end_date : float
        desired end date of output datasets
    date_window_is_gap : bool
        If set to False, all values smaller than start date and larger than end date are removed.
        If set to True the start and end date are taken as start and end of a gap that is removed from
        the timeseries. This means that all values between start and end date are removed.
        by default False

    Returns
    -------
    DataCatalogue
        Data catalogue with reduced datasets
    """
    reduced_datasets = []
    for dataset in data_catalogue.datasets:
        reduced_datasets.append(dataset.reduce_to_date_window(start_date=start_date, end_date=end_date,
                                                              date_window_is_gap=date_window_is_gap))
    return DataCatalogue.from_list(reduced_datasets, base_path=data_catalogue.base_path)
