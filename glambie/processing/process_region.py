import logging

from glambie.config.config_classes import GlambieRunConfig, RegionRunConfig
from glambie.data.data_catalogue import DataCatalogue, Timeseries
from glambie.const.data_groups import GLAMBIE_DATA_GROUPS, GlambieDataGroup
from glambie.const.regions import REGIONS, RGIRegion
from glambie.processing.processing_helpers import convert_datasets_to_longterm_trends, convert_datasets_to_monthly_grid
from glambie.processing.processing_helpers import convert_datasets_to_annual_trends
from glambie.processing.processing_helpers import convert_datasets_to_unit_mwe
from glambie.processing.processing_helpers import filter_catalogue_with_config_settings
from glambie.data.data_catalogue_helpers import calibrate_timeseries_with_trends_catalogue
from glambie.plot.processing_plots import plot_all_plots_for_region_data_group_processing
from glambie.processing.path_handling import OutputPathHandler


log = logging.getLogger(__name__)


def run_one_region(glambie_run_config: GlambieRunConfig,
                   region_config: RegionRunConfig,
                   data_catalogue: DataCatalogue,
                   output_path_handler: OutputPathHandler) -> DataCatalogue:

    # filter data catalogue by region
    data_catalogue = data_catalogue.get_filtered_catalogue(
        region_name=region_config.region_name)

    # get seasonal calibration dataset and convert to monthly grid
    seasonal_calibration_dataset = data_catalogue.get_filtered_catalogue(
        user_group=region_config.seasonal_correction_dataset["user_group"],
        data_group=region_config.seasonal_correction_dataset["data_group"]).datasets[0]
    seasonal_calibration_dataset.load_data()
    seasonal_calibration_dataset = seasonal_calibration_dataset.convert_timeseries_to_monthly_grid()

    # TODO: also filter all data to 2000? (i.e.remove any data ending pre 2000)
    # TODO: convert to RGIv6 if not already done
    result_datasets = []
    for data_group in glambie_run_config.datagroups_to_calculate:
        log.info('Starting to process region=%s datagroup=%s', region_config.region_name, data_group.name)
        data_catalogue_annual, data_catalogue_trends = filter_catalogue_with_config_settings(
            data_group=data_group,
            region_config=region_config,
            data_catalogue=data_catalogue)

        # read data in catalogue
        data_catalogue_annual.load_all_data()
        data_catalogue_trends.load_all_data()
        data_catalogue_annual = convert_datasets_to_monthly_grid(data_catalogue_annual)
        data_catalogue_trends = convert_datasets_to_monthly_grid(data_catalogue_trends)

        if data_group == GLAMBIE_DATA_GROUPS["altimetry"] or data_group == GLAMBIE_DATA_GROUPS["gravimetry"]:
            trend_combined, _ = run_altimetry_or_gravimetry(data_catalogue_annual=data_catalogue_annual,
                                                            data_catalogue_trends=data_catalogue_trends,
                                                            seasonal_calibration_dataset=seasonal_calibration_dataset,
                                                            region=REGIONS[region_config.region_name],
                                                            data_group=data_group,
                                                            output_path_handler=output_path_handler)
            result_datasets.append(trend_combined)
        elif data_group == GLAMBIE_DATA_GROUPS["demdiff_and_glaciological"]:
            trend_combined, _ = run_demdiff_and_glaciological(data_catalogue_annual=data_catalogue_annual,
                                                              data_catalogue_trends=data_catalogue_trends,
                                                              seasonal_calibration_dataset=seasonal_calibration_dataset,
                                                              region=REGIONS[region_config.region_name],
                                                              data_group=data_group,
                                                              output_path_handler=output_path_handler)
            result_datasets.append(trend_combined)
        else:
            error_msg = f'Processing for the data_group {data_group.name} has not been implemented yet'
            log.error(error_msg)
            raise NotImplementedError(error_msg)

    result_catalogue = DataCatalogue.from_list(result_datasets, base_path=data_catalogue.base_path)
    return result_catalogue


def combine_within_one_region(catalogue_data_group_results: DataCatalogue):
    # TODO: implement
    catalogue_data_group_results
    pass


def run_altimetry_or_gravimetry(data_catalogue_annual: DataCatalogue,
                                data_catalogue_trends: DataCatalogue,
                                seasonal_calibration_dataset: Timeseries,
                                region: RGIRegion,
                                data_group: GlambieDataGroup,
                                output_path_handler: OutputPathHandler) -> DataCatalogue:

    data_catalogue_annual_raw = data_catalogue_annual
    data_catalogue_trends_raw = data_catalogue_trends

    # in case seasonal calibration dataset hasn't been converted yet
    seasonal_calibration_dataset = seasonal_calibration_dataset.convert_timeseries_to_monthly_grid()
    seasonal_calibration_dataset = seasonal_calibration_dataset.convert_timeseries_to_unit_mwe()

    # TODO: implement reading annual year for seasonal correction (calendar or hydrological) from config

    # 1) ANNUAL TRENDS
    log.info("Calculating combined annual trends within data group and region...")
    # convert to annual trends
    # TODO: need to enable here to detect between seasonal correction and reading dataset
    data_catalogue_annual = convert_datasets_to_annual_trends(data_catalogue_annual)
    # convert to mwe
    data_catalogue_annual = convert_datasets_to_unit_mwe(data_catalogue_annual)

    # calculate combined annual timeseries
    annual_combined, catalogue_annual_anomalies = data_catalogue_annual.average_timeseries_in_catalogue(
        remove_trend=True, out_data_group=data_group)

    # 2) LONGTERM TRENDS
    log.info("Recalibrating with longterm trends within data group and region...")
    # get catalogue with longerm datasets for altimetry
    data_catalogue_trends = convert_datasets_to_longterm_trends(data_catalogue_trends)
    # convert to mwe
    data_catalogue_trends = convert_datasets_to_unit_mwe(data_catalogue_trends)
    # recalibrate
    catalogue_calibrated_series = calibrate_timeseries_with_trends_catalogue(data_catalogue_trends, annual_combined)
    # we dont remove trends as these are calibrated series with trends
    trend_combined, _ = catalogue_calibrated_series.average_timeseries_in_catalogue(remove_trend=False,
                                                                                    out_data_group=data_group)

    if output_path_handler is not None:
        log.info("Saving plots for region=%s datagroup=%s under path=%s", region.name, data_group.name,
                 output_path_handler.get_plot_output_file_path(region=region, data_group=data_group,
                                                               plot_file_name=""))
        plot_all_plots_for_region_data_group_processing(output_path_handler=output_path_handler,
                                                        region=region,
                                                        data_group=data_group,
                                                        data_catalogue_annual_raw=data_catalogue_annual_raw,
                                                        data_catalogue_trends_raw=data_catalogue_trends_raw,
                                                        data_catalogue_annual_homogenized=data_catalogue_annual,
                                                        data_catalogue_annual_anomalies=catalogue_annual_anomalies,
                                                        timeseries_annual_combined=annual_combined,
                                                        data_catalogue_trends_homogenized=data_catalogue_trends,
                                                        data_catalogue_calibrated_series=catalogue_calibrated_series,
                                                        timeseries_trend_combined=trend_combined)

    return trend_combined, annual_combined


def run_demdiff_and_glaciological(data_catalogue_annual: DataCatalogue,
                                  data_catalogue_trends: DataCatalogue,
                                  seasonal_calibration_dataset: Timeseries,
                                  region: RGIRegion,
                                  data_group: GlambieDataGroup,
                                  output_path_handler: OutputPathHandler) -> DataCatalogue:
    data_catalogue_annual_raw = data_catalogue_annual
    data_catalogue_trends_raw = data_catalogue_trends

    # in case seasonal calibration dataset hasn't been converted yet
    seasonal_calibration_dataset = seasonal_calibration_dataset.convert_timeseries_to_monthly_grid()
    seasonal_calibration_dataset = seasonal_calibration_dataset.convert_timeseries_to_unit_mwe()

    # TODO: implement reading annual year for seasonal correction (calendar or hydrological) from config

    # 1) ANNUAL TRENDS
    log.info("Calculating combined annual trends within data group and region...")
    # convert to annual trends
    # TODO: need to enable here to detect between seasonal correction and reading dataset
    # data_catalogue_annual = convert_datasets_to_annual_trends(data_catalogue_annual)
    # convert to mwe
    data_catalogue_annual = convert_datasets_to_unit_mwe(data_catalogue_annual)
    datasets = [d.convert_timeseries_using_seasonal_homogenization(
        seasonal_calibration_dataset=seasonal_calibration_dataset, p_value=0) for d in data_catalogue_annual.datasets]
    data_catalogue_annual = DataCatalogue.from_list(datasets, base_path=data_catalogue_annual.base_path)

    # calculate combined annual timeseries
    annual_combined, catalogue_annual_anomalies = data_catalogue_annual.average_timeseries_in_catalogue(
        remove_trend=True, out_data_group=data_group)

    # 2) LONGTERM TRENDS
    log.info("Recalibrating with longterm trends within data group and region...")
    # TODO: need to enable here to detect between seasonal correction and reading dataset
    # get catalogue with longerm datasets for altimetry
    # data_catalogue_trends = convert_datasets_to_longterm_trends(data_catalogue_trends)
    # convert to mwe
    data_catalogue_trends = convert_datasets_to_unit_mwe(data_catalogue_trends)

    # DEMDIFF + GLACIOLOGICAL COMBINED ESTIMATE
    # get catalogue with longerm datasets for demdiff
    datasets = [d.convert_timeseries_using_seasonal_homogenization(
        seasonal_calibration_dataset=seasonal_calibration_dataset, p_value=0) for d in data_catalogue_trends.datasets]
    data_catalogue_trends = DataCatalogue.from_list(datasets, base_path=data_catalogue_trends.base_path)

    # recalibrate
    catalogue_calibrated_series = calibrate_timeseries_with_trends_catalogue(data_catalogue_trends, annual_combined)
    # we dont remove trends as these are calibrated series with trends
    trend_combined, _ = catalogue_calibrated_series.average_timeseries_in_catalogue(remove_trend=False,
                                                                                    out_data_group=data_group)

    if output_path_handler is not None:
        log.info("Saving plots for region=%s datagroup=%s under path=%s", region.name, data_group.name,
                 output_path_handler.get_plot_output_file_path(region=region, data_group=data_group,
                                                               plot_file_name=""))
        plot_all_plots_for_region_data_group_processing(output_path_handler=output_path_handler,
                                                        region=region,
                                                        data_group=data_group,
                                                        data_catalogue_annual_raw=data_catalogue_annual_raw,
                                                        data_catalogue_trends_raw=data_catalogue_trends_raw,
                                                        data_catalogue_annual_homogenized=data_catalogue_annual,
                                                        data_catalogue_annual_anomalies=catalogue_annual_anomalies,
                                                        timeseries_annual_combined=annual_combined,
                                                        data_catalogue_trends_homogenized=data_catalogue_trends,
                                                        data_catalogue_calibrated_series=catalogue_calibrated_series,
                                                        timeseries_trend_combined=trend_combined)

    return trend_combined, annual_combined
