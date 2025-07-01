import logging
from typing import Tuple
import numpy as np

from glambie.config.config_classes import GlambieRunConfig, RegionRunConfig
from glambie.const.constants import ExtractTrendsMethod, GraceGap, YearType, SeasonalCorrectionMethod
from glambie.const.data_groups import GLAMBIE_DATA_GROUPS, GlambieDataGroup
from glambie.const.regions import REGIONS, RGIRegion
from glambie.data.data_catalogue import DataCatalogue, Timeseries
from glambie.data.data_catalogue_helpers import calibrate_timeseries_with_trends_catalogue
from glambie.plot.processing_plots import (
    plot_all_plots_for_region_data_group_processing, plot_combination_of_sources_within_region)
from glambie.processing.output_helpers import save_all_csvs_for_region_data_group_processing
from glambie.processing.path_handling import OutputPathHandler
from glambie.processing.processing_helpers import (
    check_and_handle_gaps_in_timeseries, convert_datasets_to_annual_trends,
    convert_datasets_to_longterm_trends_in_unit_mwe, convert_datasets_to_monthly_grid)
from glambie.processing.processing_helpers import convert_datasets_to_unit_gt
from glambie.processing.processing_helpers import convert_datasets_to_unit_mwe
from glambie.processing.processing_helpers import extend_annual_timeseries_if_shorter_than_time_window
from glambie.processing.processing_helpers import filter_catalogue_with_config_settings
from glambie.processing.processing_helpers import get_reduced_catalogue_to_date_window
from glambie.processing.processing_helpers import prepare_seasonal_calibration_dataset
from glambie.processing.processing_helpers import recombine_split_timeseries_in_catalogue
from glambie.processing.processing_helpers import set_unneeded_columns_to_nan

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
    seasonal_calibration_dataset = prepare_seasonal_calibration_dataset(region_config, data_catalogue)

    annual_backup_dataset = _prepare_consensus_variability_for_one_region(
        glambie_run_config=glambie_run_config, region_config=region_config, data_catalogue=data_catalogue,
        seasonal_calibration_dataset=seasonal_calibration_dataset, year_type=region_config.year_type,
        method_to_correct_seasonally=glambie_run_config.seasonal_correction_method,
        backup_dataset=seasonal_calibration_dataset,
        desired_time_span=[glambie_run_config.start_year, glambie_run_config.end_year])

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

            # remove GRACE gap from annual catalogue so that the variability isn't impacted by the lower resolution gap
            if data_group == GLAMBIE_DATA_GROUPS["gravimetry"]:
                data_catalogue_annual = get_reduced_catalogue_to_date_window(data_catalogue=data_catalogue_annual,
                                                                             start_date=GraceGap.START_DATE.value,
                                                                             end_date=GraceGap.END_DATE.value,
                                                                             date_window_is_gap=True)

            # run annual and trends calibration timeseries for region
            trend_combined = _run_region_timeseries_for_one_source(
                data_catalogue_annual=data_catalogue_annual,
                data_catalogue_trends=data_catalogue_trends,
                seasonal_calibration_dataset=seasonal_calibration_dataset,
                annual_backup_dataset=annual_backup_dataset,
                year_type=region_config.year_type,
                method_to_extract_trends=glambie_run_config.method_to_extract_trends,
                method_to_correct_seasonally=glambie_run_config.seasonal_correction_method,
                region=REGIONS[region_config.region_name],
                data_group=data_group,
                output_path_handler=output_path_handler,
                min_max_time_window_for_longterm_trends=[glambie_run_config.start_year, glambie_run_config.end_year])
            # apply area change
            trend_combined = trend_combined.apply_or_remove_area_change(rgi_area_version=7, apply_area_change=True)
            # save out with area change applied
            if output_path_handler is not None:
                trend_combined.save_data_as_csv(output_path_handler.get_csv_output_file_path(
                    region=trend_combined.region, data_group=data_group,
                    csv_file_name=f"{data_group.name}_final_with_area_change.csv"))
            result_datasets.append(trend_combined)
        else:
            log.info('Skipping to process region=%s datagroup=%s as no data found.',
                     region_config.region_name, data_group.name)

    result_catalogue = DataCatalogue.from_list(result_datasets, base_path=data_catalogue.base_path)
    return result_catalogue


def _prepare_consensus_variability_for_one_region(
        glambie_run_config: GlambieRunConfig,
        region_config: RegionRunConfig,
        data_catalogue: DataCatalogue,
        seasonal_calibration_dataset: Timeseries,
        year_type: YearType,
        method_to_correct_seasonally: SeasonalCorrectionMethod,
        backup_dataset: Timeseries,
        desired_time_span: Tuple[float, float]) -> Timeseries:
    """
    Prepares a consensus varibility dataset for a region, which can be used as an annual backup dataset
    in case there is no annual data within a data group

    Parameters
    ----------
    glambie_run_config : GlambieRunConfig
        config object for the run
    region_config : RegionRunConfig
        run config for a particular region
    data_catalogue : DataCatalogue
        data catalogue with input datasets
    seasonal_calibration_dataset : Timeseries
        Seasonal calibration dataset at ~ monthly resolution to be used to homogenize data
    year_type : YearType
        type of year to be used, e.g calendar or glaciological
    method_to_correct_seasonally: SeasonalCorrectionMethod
        method as to how long-term trends are correct when they don't start in the desired season, i.e. don't follow
        the desired annual grid defined with 'year_type'
    backup_dataset : Timeseries
        the backup timeseries to be used to fill missing data for achieving the desired time span
    desired_time_span : Tuple[float, float]
        the desired span of the output dataset in the format [min_start_date, max_end_date]
        the dates are expected in decimal years format (float), e.g. 2012.75.

    Returns
    -------
    Timeseries
        a combined annual timeseries spanning the 'desired_time_span'
    """

    log.info('Starting to process consensus variability for region=%s', region_config.region_name)

    result_datasets = []
    for data_group in glambie_run_config.datagroups_to_calculate:
        data_catalogue_annual, _ = filter_catalogue_with_config_settings(
            data_group=data_group, region_config=region_config, data_catalogue=data_catalogue)
        if len(data_catalogue_annual.datasets) != 0:
            # read data in catalogue
            data_catalogue_annual.load_all_data()
            data_catalogue_annual = set_unneeded_columns_to_nan(data_catalogue_annual)
            # remove GRACE gap from annual catalogue so that the variability isn't impacted by the lower resolution gap
            if data_group == GLAMBIE_DATA_GROUPS["gravimetry"]:
                data_catalogue_annual = get_reduced_catalogue_to_date_window(
                    data_catalogue=data_catalogue_annual, start_date=GraceGap.START_DATE.value,
                    end_date=GraceGap.END_DATE.value, date_window_is_gap=True)
            data_catalogue_annual, split_dataset_names_annual = check_and_handle_gaps_in_timeseries(
                data_catalogue_annual)
            data_catalogue_annual = convert_datasets_to_monthly_grid(data_catalogue_annual)

            annual_combined, _, _ = _run_region_variability_for_one_source(
                data_catalogue_annual=data_catalogue_annual, seasonal_calibration_dataset=seasonal_calibration_dataset,
                year_type=year_type, method_to_correct_seasonally=method_to_correct_seasonally,
                data_group=data_group, dataset_names_where_split_at_gap=split_dataset_names_annual)

            result_datasets.append(annual_combined)

    # get combined regional results combining the individual data group results
    result_catalogue = DataCatalogue.from_list(result_datasets, base_path=data_catalogue.base_path)
    consensus_annual = combine_within_one_region(result_catalogue, output_path_handler=None)

    # now deal with cases where the consensus does not cover all of the desired period
    # we will fall back on a backup dataset
    backup_dataset = backup_dataset.convert_timeseries_to_annual_trends(year_type=year_type)
    consensus_annual_full_ext = extend_annual_timeseries_if_shorter_than_time_window(
        annual_timeseries=consensus_annual,
        timeseries_for_extension=backup_dataset,
        desired_time_window=desired_time_span)

    # now we set all uncertainties to 0 so that they are not doublecounted when combined with the consensus
    consensus_annual_full_ext.data.errors = np.zeros(len(consensus_annual_full_ext.data.errors))

    return consensus_annual_full_ext


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
        output_path_unc = output_path.replace("mwe", "mwe_unc")

        for output_filepath, plot_errors in ((output_path, False), (output_path_unc, True)):
            plot_combination_of_sources_within_region(
                catalogue_results=catalogue_data_group_results, combined_timeseries=combined_ts,
                region=combined_ts.region, output_filepath=output_filepath, plot_errors=plot_errors)

        # save csv
        combined_ts.save_data_as_csv(output_path_handler.get_csv_output_file_path(
            region=combined_ts.region, data_group=GLAMBIE_DATA_GROUPS["consensus"],
            csv_file_name=f"consensus_hydrological_year_mwe_{combined_ts.region.name}.csv"))
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
        output_path = output_path_handler.get_plot_output_file_path(
            region=combined_region_timeseries_gt.region, data_group=GLAMBIE_DATA_GROUPS["consensus"],
            plot_file_name="2_consensus_sources_gt.png")
        output_path_unc = output_path.replace("gt", "gt_unc")

        for output_filepath, plot_errors in ((output_path, False), (output_path_unc, True)):
            plot_combination_of_sources_within_region(
                catalogue_results=catalogue_data_group_results_gt, combined_timeseries=combined_region_timeseries_gt,
                region=combined_region_timeseries_gt.region, output_filepath=output_filepath, plot_errors=plot_errors)

        # save csv
        combined_region_timeseries_gt.save_data_as_csv(output_path_handler.get_csv_output_file_path(
            region=combined_region_timeseries_gt.region, data_group=GLAMBIE_DATA_GROUPS["consensus"],
            csv_file_name=f"consensus_hydrological_year_gt_{combined_region_timeseries_gt.region.name}.csv"))

    return catalogue_data_group_results_gt, combined_region_timeseries_gt


def _run_region_timeseries_for_one_source(
        data_catalogue_annual: DataCatalogue,
        data_catalogue_trends: DataCatalogue,
        seasonal_calibration_dataset: Timeseries,
        annual_backup_dataset: Timeseries,
        year_type: YearType,
        method_to_extract_trends: ExtractTrendsMethod,
        method_to_correct_seasonally: SeasonalCorrectionMethod,
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
    method_to_extract_trends: ExtractTrendsMethod:
        method as to how the long-term trends are extracted from a high resolution (e.g. monthly) timeseries
    method_to_correct_seasonally: SeasonalCorrectionMethod
        method as to how long-term trends are correct when they don't start in the desired season, i.e. don't follow
        the desired annual grid defined with 'year_type'
    region : RGIRegion
        RGI region
    data_group : GlambieDataGroup
        Glambie Data Group which is calculated
    output_path_handler : OutputPathHandler
        object to handle output path. If set to None, no plots / other data will be saved
    min_max_time_window_for_longterm_trends : Tuple[float, float], optional
        if specified, the time series are filtered by the time window before the longterm trend is extracted,
        meaning that the resulting longterm trends are within the minimum and maximum of the time window.
        Note that existing longterm trends are removed if they are outside the time window.
        The dates are expected in decimal years format (float), e.g. 2012.75.

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

    annual_combined, data_catalogue_annual_homogenized, catalogue_annual_anomalies = \
        _run_region_variability_for_one_source(
            data_catalogue_annual=data_catalogue_annual, seasonal_calibration_dataset=seasonal_calibration_dataset,
            year_type=year_type, method_to_correct_seasonally=method_to_correct_seasonally,
            data_group=data_group, dataset_names_where_split_at_gap=split_dataset_names_annual)

    # 2) LONGTERM TRENDS
    log.info("Using the following trend datasets for %s, %s : %s",
             data_group.long_name, region.long_name, str([d.user_group for d in data_catalogue_trends.datasets]))

    trend_combined, data_catalogue_trends_homogenized, catalogue_calibrated_series = _run_region_trends_for_one_source(
        data_catalogue_trends=data_catalogue_trends, seasonal_calibration_dataset=seasonal_calibration_dataset,
        annual_backup_dataset=annual_backup_dataset, annual_combined_dataset=annual_combined, year_type=year_type,
        method_to_extract_trends=method_to_extract_trends, method_to_correct_seasonally=method_to_correct_seasonally,
        data_group=data_group, min_max_time_window_for_longterm_trends=min_max_time_window_for_longterm_trends)

    # 3) Save and plot
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
        save_all_csvs_for_region_data_group_processing(
            output_path_handler=output_path_handler,
            region=region,
            data_group=data_group,
            data_catalogue_annual_raw=data_catalogue_annual_raw,
            data_catalogue_trends_raw=data_catalogue_trends_raw,
            data_catalogue_annual_homogenized=data_catalogue_annual_homogenized,
            data_catalogue_annual_anomalies=catalogue_annual_anomalies,
            timeseries_annual_combined=annual_combined,
            data_catalogue_trends_homogenized=data_catalogue_trends_homogenized,
            data_catalogue_calibrated_series=catalogue_calibrated_series,
            timeseries_trend_combined=trend_combined)
        # plot
        plot_all_plots_for_region_data_group_processing(
            output_path_handler=output_path_handler,
            region=region,
            data_group=data_group,
            data_catalogue_annual_raw=data_catalogue_annual_raw,
            data_catalogue_trends_raw=data_catalogue_trends_raw,
            data_catalogue_annual_homogenized=data_catalogue_annual_homogenized,
            data_catalogue_annual_anomalies=catalogue_annual_anomalies,
            timeseries_annual_combined=annual_combined,
            data_catalogue_trends_homogenized=data_catalogue_trends_homogenized,
            data_catalogue_calibrated_series=catalogue_calibrated_series,
            timeseries_trend_combined=trend_combined,
            min_date=min_max_time_window_for_longterm_trends[0] - 1,
            max_date=min_max_time_window_for_longterm_trends[1] + 1)
    return trend_combined


def _run_region_variability_for_one_source(
        data_catalogue_annual: DataCatalogue,
        seasonal_calibration_dataset: Timeseries,
        year_type: YearType,
        method_to_correct_seasonally: SeasonalCorrectionMethod,
        data_group: GlambieDataGroup,
        dataset_names_where_split_at_gap: list) -> Tuple[Timeseries, DataCatalogue]:
    """
    Runs the combination of annual variability datasets for one Glambie Data Group within a region

    Parameters
    ----------
    data_catalogue_annual : DataCatalogue
        Data Catalogue with annual datasets to be used within algorithm
    seasonal_calibration_dataset : Timeseries
        Seasonal calibration dataset at ~ monthly resolution to be used to homogenize data
        Only used if method_to_correct_seasonally is defined as seasonal homogenization
    year_type : YearType
        type of year to be used, e.g calendar or glaciological
    method_to_correct_seasonally : SeasonalCorrectionMethod
        method as to how annual trends are corrected when they don't start in the desired season, i.e. don't follow
        the desired annual grid defined with 'year_type'
    data_group : GlambieDataGroup
        Glambie Data Group which is calculated
    dataset_names_where_split_at_gap : list
        list of dataset names where the annual trends were split out at a data gap
        this is so that the annual trends that were split at a data gap can be recombined

    Returns
    -------
    Tuple[Timeseries, DataCatalogue]
        1) a single timeseries of all the annual datasets combined
        2) a data catalogue of homogenized annual datasets
        3) a data catalogue of all the annual anomalies/variability that went into the combination
    """

    # convert to annual trends
    data_catalogue_annual_homogenized = convert_datasets_to_annual_trends(
        data_catalogue_annual, year_type=year_type, method_to_correct_seasonally=method_to_correct_seasonally,
        seasonal_calibration_dataset=seasonal_calibration_dataset)
    # convert to mwe
    data_catalogue_annual_homogenized = convert_datasets_to_unit_mwe(data_catalogue_annual_homogenized)

    # calculate combined annual timeseries
    # first need to recombine timeseries in cases where we split them due to gaps
    # reason for this is that we want to remove trends over a common period
    if len(dataset_names_where_split_at_gap) > 0:
        data_catalogue_annual_homogenized = recombine_split_timeseries_in_catalogue(
            data_catalogue_annual_homogenized, dataset_names_where_split_at_gap)
    # then average timeseries from annual catalogue, removing the trends
    annual_combined, catalogue_annual_anomalies = data_catalogue_annual_homogenized.average_timeseries_in_catalogue(
        remove_trend=True, out_data_group=data_group)
    return annual_combined, data_catalogue_annual_homogenized, catalogue_annual_anomalies


def _run_region_trends_for_one_source(
        data_catalogue_trends: DataCatalogue,
        seasonal_calibration_dataset: Timeseries,
        annual_combined_dataset: Timeseries,
        annual_backup_dataset: Timeseries,
        year_type: YearType,
        method_to_extract_trends: ExtractTrendsMethod,
        method_to_correct_seasonally: SeasonalCorrectionMethod,
        data_group: GlambieDataGroup,
        min_max_time_window_for_longterm_trends: Tuple[float, float] = None) -> Tuple[
            Timeseries, DataCatalogue, DataCatalogue]:
    """
    Runs the combination algorithm for all trend datasets for one Glambie Data Group within a region

    Parameters
    ----------
    data_catalogue_trends : DataCatalogue
        Data Catalogue with trend datasets to be used within algorithm
    seasonal_calibration_dataset : Timeseries
        Seasonal calibration dataset at ~ monthly resolution to be used to homogenize data
        Only used if method_to_correct_seasonally is defined as seasonal homogenization
    annual_combined_dataset : Timeseries
        a single timeseries of all the annual datasets combined
        output from '_run_region_variability_for_one_source()'
    annual_backup_dataset : Timeseries
        Dataset to be used as a backup when to extend combined annual series when it doesn't cover the whole period
    year_type : YearType
        type of year to be used, e.g calendar or glaciological
    method_to_extract_trends : ExtractTrendsMethod
        method as to how the long-term trends are extracted from a high resolution (e.g. monthly) timeseries
    method_to_correct_seasonally : SeasonalCorrectionMethod
        method as to how long-term trends are correct when they don't start in the desired season, i.e. don't follow
        the desired annual grid defined with 'year_type'    data_group : GlambieDataGroup
        _description_
    min_max_time_window_for_longterm_trends : Tuple[float, float], optional
        if specified, the time series are filtered by the time window before the longterm trend is extracted,
        meaning that the resulting longterm trends are within the minimum and maximum of the time window.
        Note that existing longterm trends are removed if they are outside the time window.
        The dates are expected in decimal years format (float), e.g. 2012.75.
        by default None

    Returns
    -------
    Tuple[Timeseries, DataCatalogue, DataCatalogue]
        1) a single timeseries of all the trend datasets combined
        2) a catalogue of the homogenized trends
        3) a data catalogue of all the calibrated trends that were averaged
    """

    log.info("Recalibrating with longterm trends within data group and region...")
    # get catalogue with longterm datasets in same unit as calibration dataset (mwe)
    data_catalogue_trends_homogenized = convert_datasets_to_longterm_trends_in_unit_mwe(
        data_catalogue_trends, year_type=year_type,
        seasonal_calibration_dataset=seasonal_calibration_dataset,
        method_to_extract_trends=method_to_extract_trends,
        method_to_correct_seasonally=method_to_correct_seasonally,
        output_trend_date_range=min_max_time_window_for_longterm_trends)

    # now treat case where trends are outside annual combined timeseries
    annual_combined_full_ext = extend_annual_timeseries_if_shorter_than_time_window(
        annual_timeseries=annual_combined_dataset,
        timeseries_for_extension=annual_backup_dataset.convert_timeseries_to_annual_trends(year_type=year_type),
        desired_time_window=data_catalogue_trends_homogenized.get_time_span_of_datasets())

    # recalibrate
    catalogue_calibrated_series = calibrate_timeseries_with_trends_catalogue(
        data_catalogue_trends_homogenized, annual_combined_full_ext)
    # now combine the calibrated timeseries
    # the trends are not removed when combining, because the dfferences in periods are already reflected
    # with the annual variability dataset
    trend_combined, _ = catalogue_calibrated_series.average_timeseries_in_catalogue(remove_trend=False,
                                                                                    out_data_group=data_group)
    return trend_combined, data_catalogue_trends_homogenized, catalogue_calibrated_series
