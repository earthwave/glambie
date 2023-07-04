import logging
from glambie.config.config_classes import GlambieRunConfig
from glambie.const.regions import REGIONS
from glambie.data.data_catalogue import DataCatalogue
from glambie.data.timeseries import Timeseries, TimeseriesData
from glambie.const.constants import YearType
from glambie.processing.path_handling import OutputPathHandler
from glambie.processing.processing_helpers import prepare_seasonal_calibration_dataset
from glambie.const.data_groups import GLAMBIE_DATA_GROUPS
from glambie.plot.processing_plots import plot_combination_of_regions_to_global
import numpy as np
from functools import reduce


log = logging.getLogger(__name__)


def run_global_results(glambie_run_config: GlambieRunConfig,
                       regional_results_catalogue: DataCatalogue,
                       original_data_catalogue: DataCatalogue,
                       output_path_handler: OutputPathHandler) -> Timeseries:
    """
    Combines all regional results into a global result

    Parameters
    ----------
    glambie_run_config : GlambieRunConfig
        config object for the run
    regional_results_catalogue : DataCatalogue
        Data Catalogue containing the result datasets per region
    original_data_catalogue : DataCatalogue
        Data Catalogue of original data used to extract the seasonal calibration dataset for each region
    output_path_handler : OutputPathHandler
        object to handle output path. If set to None, no plots / other data will be saved

    Returns
    -------
    Timeseries
        Global timeseries
    """
    log.info('Starting to combine regional results into global')
    regional_results_catalogue_homogenized = _homogenize_regional_results_to_calendar_year(glambie_run_config,
                                                                                           regional_results_catalogue,
                                                                                           original_data_catalogue)
    global_timeseries = _combine_regional_results_into_global(regional_results_catalogue_homogenized)

    # plot
    if output_path_handler is not None:
        output_path = output_path_handler.get_plot_output_file_path(region=REGIONS["global"],
                                                                    data_group=GLAMBIE_DATA_GROUPS["consensus"],
                                                                    plot_file_name="1_global_picture.png")
        plot_combination_of_regions_to_global(catalogue_region_results=regional_results_catalogue_homogenized,
                                              global_timeseries=global_timeseries, region=REGIONS["global"],
                                              output_filepath=output_path)
    return global_timeseries


def _homogenize_regional_results_to_calendar_year(glambie_run_config: GlambieRunConfig,
                                                  regional_results_catalogue: DataCatalogue,
                                                  original_data_catalogue: DataCatalogue) -> DataCatalogue:
    """
    Homogenizes the regional results to calendar year using a seasonal calibration dataset.

    A high resolution timeseries with seasonal information is used to 'shift' and correct the current
    timesteps to calendar years.

    For more information check the Glambie algorithm description document.

    Parameters
    ----------
    glambie_run_config : GlambieRunConfig
        config object for the run
    regional_results_catalogue : DataCatalogue
        Data Catalogue containing the result datasets per region
    original_data_catalogue : DataCatalogue
        Data Catalogue of original data used to extract the seasonal calibration dataset for each region

    Returns
    -------
    DataCatalogue
        Data Catalogue with homogenized dataset. Has the same number of datasets as the 'regional_results_catalogue'
    """
    homogenized_regional_results = []

    for region_config in glambie_run_config.regions:
        # step 1: get seasonal calibration dataset
        data_catalogue = original_data_catalogue.get_filtered_catalogue(
            region_name=region_config.region_name)
        seasonal_calibration_dataset = prepare_seasonal_calibration_dataset(region_config, data_catalogue)
        # step 2: homogenize to calendar year
        data_set = regional_results_catalogue.get_filtered_catalogue(region_name=region_config.region_name).datasets[0]
        homogenized_regional_results.append(data_set.convert_timeseries_using_seasonal_homogenization(
            seasonal_calibration_dataset=seasonal_calibration_dataset, year_type=YearType.CALENDAR, p_value=0))

    result_catalogue = DataCatalogue.from_list(homogenized_regional_results)
    return result_catalogue


def _combine_regional_results_into_global(regional_results_catalogue: DataCatalogue) -> Timeseries:
    """
    Combines all regional results into one global timeseries.
    Assumes that timeseries are all in same grid and resolution temporally (e.g. calendar year) and of unit mwe.

    Parameters
    ----------
    regional_results_catalogue : DataCatalogue
        regional results (homogenized to the same year)

    Returns
    -------
    Timeseries
        Globally aggregated timeseries
    """
    assert regional_results_catalogue.datasets_are_same_unit()
    assert regional_results_catalogue.datasets[0].unit == "mwe"

    # merge all dataframes
    catalogue_dfs = [ds.data.as_dataframe() for ds in regional_results_catalogue.datasets]
    # calculate global area for weighted mean
    total_area = np.sum([ds.region.rgi6_area for ds in regional_results_catalogue.datasets])

    # multiply changes and errors with area for each region
    for _, (df, ds) in enumerate(zip(catalogue_dfs, regional_results_catalogue.datasets)):
        df["changes"] = (df["changes"] * ds.region.rgi6_area)
        # apply weighted mean error propagation
        df["errors"] = (df["errors"] * ds.region.rgi6_area)**2
        # ds.data.errors = ds.data.changes * ds.region.rgi6_area
    # calculate weighted mean
    df = reduce(lambda left, right: left.merge(right, how="outer", on=["start_dates", "end_dates"]), catalogue_dfs)
    df = df.sort_values(by="start_dates")
    start_dates, end_dates = np.array(df["start_dates"]), np.array(df["end_dates"])
    mean_changes = np.array(df[df.columns.intersection(
        df.filter(regex=("changes*")).columns.to_list())].sum(axis=1)) / total_area

    # apply square root to errors and divide by total area
    mean_uncertainties = np.sqrt(np.array(df[df.columns.intersection(
        df.filter(regex=("errors*")).columns.to_list())].sum(axis=1))) / total_area

    # make timeseries object with combined solution
    ts_data = TimeseriesData(start_dates=np.array(start_dates),
                             end_dates=np.array(end_dates),
                             changes=np.array(mean_changes),
                             errors=np.array(mean_uncertainties),
                             glacier_area_reference=None,
                             glacier_area_observed=None)
    # use this as a reference for filling metadata
    reference_dataset_for_metadata = regional_results_catalogue.datasets[0]

    return Timeseries(region=REGIONS["global"], data_group=GLAMBIE_DATA_GROUPS["consensus"],
                      data=ts_data, unit=reference_dataset_for_metadata.unit)
