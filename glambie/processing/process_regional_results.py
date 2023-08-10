import logging
from typing import Tuple

from glambie.config.config_classes import GlambieRunConfig, RegionRunConfig
from glambie.data.data_catalogue import DataCatalogue, Timeseries
from glambie.const.data_groups import GlambieDataGroup, GLAMBIE_DATA_GROUPS
from glambie.const.regions import REGIONS, RGIRegion
from glambie.const.constants import YearType
from glambie.processing.processing_helpers import convert_datasets_to_longterm_trends_in_unit_mwe
from glambie.processing.processing_helpers import convert_datasets_to_monthly_grid
from glambie.processing.processing_helpers import recombine_split_timeseries_in_catalogue
from glambie.processing.processing_helpers import convert_datasets_to_annual_trends, convert_datasets_to_unit_mwe
from glambie.processing.processing_helpers import convert_datasets_to_unit_gt
from glambie.processing.processing_helpers import filter_catalogue_with_config_settings
from glambie.processing.processing_helpers import prepare_seasonal_calibration_dataset
from glambie.processing.processing_helpers import extend_annual_timeseries_if_outside_trends_period
from glambie.processing.processing_helpers import check_and_handle_gaps_in_timeseries
from glambie.processing.processing_helpers import set_unneeded_columns_to_nan
from glambie.processing.output_helpers import save_all_csvs_for_region_data_group_processing
from glambie.data.data_catalogue_helpers import calibrate_timeseries_with_trends_catalogue
from glambie.plot.processing_plots import plot_all_plots_for_region_data_group_processing
from glambie.plot.processing_plots import plot_combination_of_sources_within_region
from glambie.processing.path_handling import OutputPathHandler


log = logging.getLogger(__name__)


def run_one_region(glambie_run_config: GlambieRunConfig,
                   region_config: RegionRunConfig,
                   data_catalogue: DataCatalogue,
                   output_path_handler: OutputPathHandler) -> DataCatalogue:
    """
    Runs the glambie algorithm for an individual region within the different sources (as specified in the config)
    and returns a DataCatalogue with one solution per source

    Parameters
    ----------
    glambie_run_config : GlambieRunConfig
        config object for the run
    region_config : RegionRunConfig
        run config for a particular region
    data_catalogue : DataCatalogue
        data catalogue with input datasets
    output_path_handler : OutputPathHandler
        object to handle output path. If set to None, no plots / other data will be saved

    Returns
    -------
    DataCatalogue
        DataCatalogue with one combined solution per glambie data source
    """
    # filter data catalogue by region
    data_catalogue = data_catalogue.get_filtered_catalogue(
        region_name=region_config.region_name)

    # get seasonal calibration dataset and convert to monthly grid
    season_calibration_dataset = prepare_seasonal_calibration_dataset(region_config, data_catalogue)
    # TODO: add annual backup dataset to config?
    annual_backup_dataset = season_calibration_dataset.copy()

    # TODO: convert to RGIv6 if not already done
    result_datasets = []
    for data_group in glambie_run_config.datagroups_to_calculate:
        log.info('Starting to process region=%s datagroup=%s', region_config.region_name, data_group.name)
        data_catalogue_annual, data_catalogue_trends = filter_catalogue_with_config_settings(
            data_group=data_group,
            region_config=region_config,
            data_catalogue=data_catalogue)
        if not len(data_catalogue_annual.datasets) == len(data_catalogue_trends.datasets) == 0:
            # read data in catalogue
            data_catalogue_annual.load_all_data()
            data_catalogue_trends.load_all_data()
            data_catalogue_annual = set_unneeded_columns_to_nan(data_catalogue_annual)
            data_catalogue_trends = set_unneeded_columns_to_nan(data_catalogue_trends)

            # run annual and trends calibration timeseries for region
            trend_combined = _run_region_timeseries_one_source(
                data_catalogue_annual=data_catalogue_annual,
                data_catalogue_trends=data_catalogue_trends,
                seasonal_calibration_dataset=season_calibration_dataset,
                annual_backup_dataset=annual_backup_dataset,
                year_type=region_config.year_type,
                region=REGIONS[region_config.region_name],
                data_group=data_group,
                output_path_handler=output_path_handler,
                min_max_time_window_for_longterm_trends=[glambie_run_config.start_year, glambie_run_config.end_year])
            # apply area change
            trend_combined = trend_combined.apply_or_remove_area_change(rgi_area_version=6, apply_area_change=True)
            # save out with area change applied
            trend_combined.save_data_as_csv(output_path_handler.get_csv_output_file_path(
                region=trend_combined.region, data_group=data_group,
                csv_file_name=f"{data_group.name}_final_with_area_change.csv"))
            result_datasets.append(trend_combined)
        else:
            log.info('Skipping to process region=%s datagroup=%s as no data found.',
                     region_config.region_name, data_group.name)

    result_catalogue = DataCatalogue.from_list(result_datasets, base_path=data_catalogue.base_path)
    return result_catalogue


def combine_within_one_region(catalogue_data_group_results: DataCatalogue,
                              output_path_handler: OutputPathHandler) -> Timeseries:
    """
    Combines the combined estimates from each Glambie Data Group within a region

    Parameters
    ----------
    catalogue_data_group_results : DataCatalogue
        Data Catalogue with data group results, one dataset per data group
    output_path_handler : OutputPathHandler
        object to handle output path. If set to None, no plots / other data will be saved

    Returns
    -------
    Timeseries
        Combined/consensus timeseries
    """
    # combine
    combined_ts, _ = catalogue_data_group_results.average_timeseries_in_catalogue(remove_trend=True,
                                                                                  add_trend_after_averaging=True,
                                                                                  out_data_group=GLAMBIE_DATA_GROUPS[
                                                                                      "consensus"])
    if output_path_handler is not None:
        output_path = output_path_handler.get_plot_output_file_path(region=combined_ts.region,
                                                                    data_group=GLAMBIE_DATA_GROUPS["consensus"],
                                                                    plot_file_name="1_consensus_sources_mwe.png")
        # plot
        plot_combination_of_sources_within_region(catalogue_results=catalogue_data_group_results,
                                                  combined_timeseries=combined_ts, region=combined_ts.region,
                                                  output_filepath=output_path)
        # save csv
        combined_ts.save_data_as_csv(output_path_handler.get_csv_output_file_path(
            region=combined_ts.region, data_group=GLAMBIE_DATA_GROUPS["consensus"],
            csv_file_name=f"consensus_mwe_{combined_ts.region.name}.csv"))
    return combined_ts


def convert_and_save_one_region_to_gigatonnes(
        catalogue_data_group_results: DataCatalogue,
        combined_region_timeseries: Timeseries,
        output_path_handler: OutputPathHandler) -> Tuple[DataCatalogue, Timeseries]:
    """
    Converts regional results to gigatonnes and saves out plots and csvs (depending on the output path handler settings)

    Parameters
    ----------
    catalogue_data_group_results : DataCatalogue
        input catalogue of results per data group, to be converted to Gigatonnes
    combined_region_timeseries : Timeseries
        input time series of regional consensus from different sources, to be converted to Gigatonnes
    output_path_handler : OutputPathHandler
        object to handle output path. If set to None, no plots / other data will be saved

    Returns
    -------
    Tuple[DataCatalogue, Timeseries]
        Unit converted data catalogue and region timeseries (in Gigatonnes)
    """
    # convert to gigatonnes
    combined_region_timeseries_gt = combined_region_timeseries.apply_or_remove_area_change(apply_area_change=False)
    combined_region_timeseries_gt = combined_region_timeseries_gt.convert_timeseries_to_unit_gt()
    catalogue_data_group_results_gt = convert_datasets_to_unit_gt(catalogue_data_group_results)

    if output_path_handler is not None:
        output_path = output_path_handler.get_plot_output_file_path(region=combined_region_timeseries_gt.region,
                                                                    data_group=GLAMBIE_DATA_GROUPS["consensus"],
                                                                    plot_file_name="2_consensus_sources_gt.png")
        # plot
        plot_combination_of_sources_within_region(catalogue_results=catalogue_data_group_results_gt,
                                                  combined_timeseries=combined_region_timeseries_gt,
                                                  region=combined_region_timeseries_gt.region,
                                                  output_filepath=output_path)
        # save csv
        combined_region_timeseries_gt.save_data_as_csv(output_path_handler.get_csv_output_file_path(
            region=combined_region_timeseries_gt.region, data_group=GLAMBIE_DATA_GROUPS["consensus"],
            csv_file_name=f"consensus_gt_{combined_region_timeseries_gt.region.name}.csv"))

    return catalogue_data_group_results_gt, combined_region_timeseries_gt


def _run_region_timeseries_one_source(
        data_catalogue_annual: DataCatalogue,
        data_catalogue_trends: DataCatalogue,
        seasonal_calibration_dataset: Timeseries,
        annual_backup_dataset: Timeseries,
        year_type: YearType,
        region: RGIRegion,
        data_group: GlambieDataGroup,
        output_path_handler: OutputPathHandler,
        min_max_time_window_for_longterm_trends: Tuple[float, float] = None) -> Timeseries:
    """
    Runs the glambie algorithm for all datasets for one Glambie Data Group within a region

    Parameters
    ----------
    data_catalogue_annual : DataCatalogue
        Data Catalogue with annual datasets to be used within algorithm
    data_catalogue_trends : DataCatalogue
        Data Catalogue with trend datasets to be used within algorithm
    seasonal_calibration_dataset : Timeseries
        Seasonal calibration dataset at ~ monthly resolution to be used to homogenize data
    annual_backup_data_set : Timeseries
        Dataset to be used as a backup when data_catalogue_annual is empty
        or to extend combined annual series when they don't cover the whole period
    year_type : YearType
        type of year to be used, e.g calendar or glaciological
    region : RGIRegion
        RGI region
    data_group : GlambieDataGroup
        Glambie Data Group which is calculated
    output_path_handler : OutputPathHandler
        object to handle output path. If set to None, no plots / other data will be saved
    min_max_time_window_for_longterm_trends : Tuple[float, float], optional
        if specified, the time series are filtered by the time window before the longterm trend is axtracted,
        meaning that the resulting longterm trends are within the minimum and maximum of the time window
        Note that existing longterm trends are removed if the are outside the time window
        the dates are expected in decimal years format (float), e.g. 2012.75

    Returns
    -------
    Timeseries
        timeseries of combined dataset
    """
    # prepare annual and trend datasets
    data_catalogue_annual, split_dataset_names_annual = check_and_handle_gaps_in_timeseries(data_catalogue_annual)
    data_catalogue_trends, split_dataset_names_trends = check_and_handle_gaps_in_timeseries(data_catalogue_trends)
    data_catalogue_annual = convert_datasets_to_monthly_grid(data_catalogue_annual)
    data_catalogue_trends = convert_datasets_to_monthly_grid(data_catalogue_trends)

    # keep raw datasets for plotting later
    data_catalogue_annual_raw = data_catalogue_annual
    data_catalogue_trends_raw = data_catalogue_trends

    # 1) ANNUAL TRENDS
    log.info("Calculating combined annual trends within data group %s "
             "and region %s", data_group.long_name, region.long_name)

    # add annual dataset if none in catalogue
    if len(data_catalogue_annual.datasets) == 0:
        log.info('No annual dataset found for %s in region %s, using backup dataset %s',
                 data_group.long_name, region.long_name, annual_backup_dataset.user_group)
        data_catalogue_annual = DataCatalogue.from_list([annual_backup_dataset])

    log.info("Using the following annual datasets for %s, %s : %s",
             data_group.long_name, region.long_name, str([d.user_group for d in data_catalogue_annual.datasets]))

    # convert to annual trends
    data_catalogue_annual = convert_datasets_to_annual_trends(data_catalogue_annual, year_type=year_type,
                                                              season_calibration_dataset=seasonal_calibration_dataset)
    # convert to mwe
    data_catalogue_annual = convert_datasets_to_unit_mwe(data_catalogue_annual)

    # calculate combined annual timeseries
    # first need to recombine timeseries in cases where we split them due to gaps
    # reason for this is that we want to remove trends over a common period
    if len(split_dataset_names_annual) > 0:
        data_catalogue_annual = recombine_split_timeseries_in_catalogue(
            data_catalogue_annual, split_dataset_names_annual)
    # then average timeseries from annual catalogue, removing the trends
    annual_combined, catalogue_annual_anomalies = data_catalogue_annual.average_timeseries_in_catalogue(
        remove_trend=True, out_data_group=data_group)

    # 2) LONGTERM TRENDS
    log.info("Using the following trend datasets for %s, %s : %s",
             data_group.long_name, region.long_name, str([d.user_group for d in data_catalogue_trends.datasets]))
    log.info("Recalibrating with longterm trends within data group and region...")
    # get catalogue with longerm datasets in same unit as calibration dataset (mwe)
    data_catalogue_trends = convert_datasets_to_longterm_trends_in_unit_mwe(
        data_catalogue_trends, year_type=year_type,
        season_calibration_dataset=seasonal_calibration_dataset,
        output_trend_date_range=min_max_time_window_for_longterm_trends)

    # now treat case where trends are outside annual combined timeseries
    annual_combined_full_ext = extend_annual_timeseries_if_outside_trends_period(
        annual_timeseries=annual_combined,
        data_catalogue_trends=data_catalogue_trends,
        timeseries_for_extension=annual_backup_dataset.convert_timeseries_to_annual_trends(year_type=year_type))

    # recalibrate
    catalogue_calibrated_series = calibrate_timeseries_with_trends_catalogue(
        data_catalogue_trends, annual_combined_full_ext)
    # we dont remove trends as these are calibrated series with trends
    trend_combined, _ = catalogue_calibrated_series.average_timeseries_in_catalogue(remove_trend=False,
                                                                                    out_data_group=data_group)

    if output_path_handler is not None:
        log.info("Saving plots for region=%s datagroup=%s under path=%s", region.name, data_group.name,
                 output_path_handler.get_plot_output_file_path(region=region, data_group=data_group,
                                                               plot_file_name=""))
        # prepare data catalogues for plotting if they have been split due to gaps
        if len(split_dataset_names_annual) > 0:
            data_catalogue_trends = recombine_split_timeseries_in_catalogue(
                data_catalogue_trends, split_dataset_names_trends)
            catalogue_calibrated_series = recombine_split_timeseries_in_catalogue(
                catalogue_calibrated_series, split_dataset_names_trends)
            data_catalogue_annual_raw = recombine_split_timeseries_in_catalogue(
                data_catalogue_annual_raw, split_dataset_names_annual)
            data_catalogue_trends_raw = recombine_split_timeseries_in_catalogue(
                data_catalogue_trends_raw, split_dataset_names_trends)

        # save CSVs
        save_all_csvs_for_region_data_group_processing(output_path_handler=output_path_handler,
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
        # plot
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
    return trend_combined
