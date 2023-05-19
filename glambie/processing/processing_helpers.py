import logging
from typing import Tuple

from glambie.config.config_classes import RegionRunConfig
from glambie.data.data_catalogue import DataCatalogue
from glambie.const.data_groups import GLAMBIE_DATA_GROUPS, GlambieDataGroup

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
    log.info('Excluding the following datasets from annual calculations: datasets=%s', exclude_annual_datasets)
    for ds in exclude_annual_datasets:
        datasets_annual = [d for d in datasets_annual if d.user_group.lower() != ds.lower()]
    if data_group == GLAMBIE_DATA_GROUPS["demdiff_and_glaciological"]:
        datasets_annual = [d for d in datasets_annual if d.data_group != GLAMBIE_DATA_GROUPS["demdiff"]]

    # 3 filter out what has been specified in config for longterm trend datasets
    datasets_trend = data_catalogue.datasets.copy()
    exclude_trend_datasets = region_config.region_run_settings[data_group.name].get("exclude_trend_datasets", [])
    log.info('Excluding the following datasets from trend calculations: datasets=%s', exclude_trend_datasets)
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


def convert_datasets_to_annual_trends(data_catalogue: DataCatalogue) -> DataCatalogue:
    """
    Convert all datasets in data catalogue to annual trends

    Parameters
    ----------
    data_catalogue : DataCatalogue
        data catalogue to be converted

    Returns
    -------
    DataCatalogue
        New data catalogue with converted data
    """
    data_catalogue = convert_datasets_to_monthly_grid(data_catalogue)
    datasets = []
    for ds in data_catalogue.datasets:
        datasets.append(ds.convert_timeseries_to_annual_trends())
    catalogue_annual_grid = DataCatalogue.from_list(datasets, base_path=data_catalogue.base_path)
    return catalogue_annual_grid


def convert_datasets_to_longterm_trends(data_catalogue: DataCatalogue) -> DataCatalogue:
    """
    Convert all datasets in data catalogue to longterm trends

    Parameters
    ----------
    data_catalogue : DataCatalogue
        data catalogue to be converted

    Returns
    -------
    DataCatalogue
        New data catalogue with converted data
    """
    data_catalogue = convert_datasets_to_monthly_grid(data_catalogue)
    # first convert to annual so that longterm trend will fit into annual grid
    data_catalogue = convert_datasets_to_annual_trends(data_catalogue)
    datasets = []
    for ds in data_catalogue.datasets:
        # then convert to longterm trend
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
