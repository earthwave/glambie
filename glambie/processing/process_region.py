import logging

from glambie.config.config_classes import GlambieRunConfig, RegionRunConfig
from glambie.data.data_catalogue import DataCatalogue, Timeseries
from glambie.const.data_groups import GLAMBIE_DATA_GROUPS, GlambieDataGroup

log = logging.getLogger(__name__)


def run_one_region(glambie_run_config: GlambieRunConfig,
                   region_config: RegionRunConfig,
                   data_catalogue: DataCatalogue) -> DataCatalogue:

    # filter data catalogue by region?
    data_catalogue = data_catalogue.get_filtered_catalogue(
        region_name=region_config.region_name)

    # get seasonal calibration dataset and convert to monthly grid
    seasonal_calibration_dataset = data_catalogue.get_filtered_catalogue(
        user_group=region_config.seasonal_correction_dataset["user_group"],
        data_group=region_config.seasonal_correction_dataset["data_group"]).datasets[0]
    seasonal_calibration_dataset.load_data()
    seasonal_calibration_dataset = seasonal_calibration_dataset.convert_timeseries_to_monthly_grid()

    # TODO: don't forget to convert seasonal calibration dataset to mwe
    # TODO: also filter all data to 2000? (i.e.remove any data ending pre 2000)

    for data_group in glambie_run_config.datagroups_to_calculate:
        log.info('Starting to process region=%s datagroup=%s', region_config.region_name, data_group.name)

        # data_catalogue = data_catalogue.get_filtered_catalogue(
        #     data_group=data_group.name)

        data_catalogue_annual, data_catalogue_trends = filter_catalogue_with_config_settings(
            data_group=data_group,
            region_config=region_config,
            data_catalogue=data_catalogue)

        # read data in catalogue
        data_catalogue_annual.load_all_data()
        data_catalogue_trends.load_all_data()

        if data_group == GLAMBIE_DATA_GROUPS["altimetry"]:
            result_catalogue = run_altimetry(data_catalogue_annual=data_catalogue_annual,
                                             data_catalogue_trends=data_catalogue_trends,
                                             seasonal_calibration_dataset=seasonal_calibration_dataset)
        elif data_group == GLAMBIE_DATA_GROUPS["gravimetry"]:
            result_catalogue = run_gravimetry(data_catalogue_annual=data_catalogue_annual,
                                              data_catalogue_trends=data_catalogue_trends,
                                              seasonal_calibration_dataset=seasonal_calibration_dataset)
        elif data_group == GLAMBIE_DATA_GROUPS["demdiff_and_glaciological"]:
            result_catalogue = run_demdiff_and_glaciological(data_catalogue_annual=data_catalogue_annual,
                                                             data_catalogue_trends=data_catalogue_trends,
                                                             seasonal_calibration_dataset=seasonal_calibration_dataset)
        else:
            error_msg = f'Processing for the data_group {data_group.name} has not been implemented yet'
            log.error(error_msg)
            raise NotImplementedError(error_msg)

    # todo: aggregate different results catalogue into one catalogue

    return result_catalogue


def filter_catalogue_with_config_settings(data_group: GlambieDataGroup,
                                          region_config: RegionRunConfig,
                                          data_catalogue: DataCatalogue) -> list[DataCatalogue, DataCatalogue]:
    # 1 filter by data group - just in case it hasn't already been done
    data_catalogue = data_catalogue.get_filtered_catalogue(
        data_group=data_group.name)
    # 2 filter out what has been specified in config for annual datasets
    datasets_annual = data_catalogue.datasets.copy()
    exclude_annual_datasets = region_config.region_run_settings[data_group.name].get("exclude_annual_datasets", [])
    log.info('Excluding the following datasets from annual calculations: datasets=%s', exclude_annual_datasets)
    for ds in exclude_annual_datasets:
        datasets_annual = [d for d in datasets_annual if d.user_group.lower() != ds.lower()]
    # 3 filter out what has been specified in config for longterm trend datasets
    datasets_trend = data_catalogue.datasets.copy()
    exclude_trend_datasets = region_config.region_run_settings[data_group.name].get("exclude_trend_datasets", [])
    log.info('Excluding the following datasets from trend calculations: datasets=%s', exclude_trend_datasets)
    for ds in exclude_trend_datasets:
        datasets_trend = [d for d in datasets_trend if d.user_group.lower() != ds.lower()]

    data_catalogue_annual = DataCatalogue.from_list(datasets_annual, base_path=data_catalogue.base_path)
    data_catalogue_trend = DataCatalogue.from_list(datasets_trend, base_path=data_catalogue.base_path)

    return data_catalogue_annual, data_catalogue_trend


def combine_within_one_region():
    pass


def run_demdiff_and_glaciological(data_catalogue_annual: DataCatalogue,
                                  data_catalogue_trends: DataCatalogue,
                                  seasonal_calibration_dataset: Timeseries) -> DataCatalogue:
    data_catalogue_annual
    data_catalogue_trends
    seasonal_calibration_dataset
    pass


def run_altimetry(data_catalogue_annual: DataCatalogue,
                  data_catalogue_trends: DataCatalogue,
                  seasonal_calibration_dataset: Timeseries) -> DataCatalogue:
    data_catalogue_annual
    data_catalogue_trends
    seasonal_calibration_dataset
    pass


def run_gravimetry(data_catalogue_annual: DataCatalogue,
                   data_catalogue_trends: DataCatalogue,
                   seasonal_calibration_dataset: Timeseries) -> DataCatalogue:
    data_catalogue_annual
    data_catalogue_trends
    seasonal_calibration_dataset
    pass
