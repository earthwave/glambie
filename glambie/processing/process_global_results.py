import logging
from glambie.config.config_classes import GlambieRunConfig
from glambie.const.regions import REGIONS
from glambie.data.data_catalogue import DataCatalogue
from glambie.data.timeseries import Timeseries, TimeseriesData
from glambie.const.constants import YearType
from glambie.processing.path_handling import OutputPathHandler
from glambie.processing.processing_helpers import (
    convert_datasets_to_unit_gt,
    prepare_seasonal_calibration_dataset,
)
from glambie.processing.processing_helpers import get_reduced_catalogue_to_date_window
from glambie.util.version_helpers import get_glambie_bucket_name
from glambie.const.data_groups import GLAMBIE_DATA_GROUPS
from glambie.plot.processing_plots import plot_combination_of_regions_to_global
import numpy as np
import pandas as pd

log = logging.getLogger(__name__)


def run_global_results(
    glambie_run_config: GlambieRunConfig,
    regional_results_catalogue: DataCatalogue,
    original_data_catalogue: DataCatalogue,
    output_path_handler: OutputPathHandler,
) -> Timeseries:
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
    log.info("Starting to combine regional results into a global results.")
    regional_results_catalogue_homogenized = (
        _homogenize_regional_results_to_calendar_year(
            glambie_run_config, regional_results_catalogue, original_data_catalogue
        )
    )
    # remove any dates outside config time period:
    regional_results_catalogue_homogenized = get_reduced_catalogue_to_date_window(
        data_catalogue=regional_results_catalogue_homogenized,
        start_date=glambie_run_config.start_year,
        end_date=glambie_run_config.end_year + 1,
    )  # plus one to include until the end of the year, and not start

    global_timeseries_mwe = _combine_regional_results_into_global(
        regional_results_catalogue_homogenized, glambie_run_config.rgi_area_version
    )

    # now convert to gigatonnes
    regional_results_catalogue_homogenized_gt = convert_datasets_to_unit_gt(
        regional_results_catalogue_homogenized, glambie_run_config.rgi_area_version
    )
    global_timeseries_gt = _combine_regional_results_into_global(
        regional_results_catalogue_homogenized_gt, glambie_run_config.rgi_area_version
    )

    # plot and save to csv
    if output_path_handler is not None:
        # 1 in mwe
        plot_output_file = output_path_handler.get_plot_output_file_path(
            region=REGIONS["global"],
            data_group=GLAMBIE_DATA_GROUPS["consensus"],
            plot_file_name="1_global_picture_mwe.png",
        )
        plot_combination_of_regions_to_global(
            catalogue_region_results=regional_results_catalogue_homogenized,
            global_timeseries=global_timeseries_mwe,
            region=REGIONS["global"],
            output_filepath=plot_output_file,
        )
        csv_output_file = output_path_handler.get_csv_output_file_path(
            region=REGIONS["global"],
            data_group=GLAMBIE_DATA_GROUPS["consensus"],
            csv_file_name="global_mwe.csv",
        )
        global_timeseries_mwe.save_data_as_csv(csv_output_file)
        # 2 in gigatonnes
        plot_output_file = output_path_handler.get_plot_output_file_path(
            region=REGIONS["global"],
            data_group=GLAMBIE_DATA_GROUPS["consensus"],
            plot_file_name="2_global_picture_gt.png",
        )
        plot_combination_of_regions_to_global(
            catalogue_region_results=regional_results_catalogue_homogenized_gt,
            global_timeseries=global_timeseries_gt,
            region=REGIONS["global"],
            output_filepath=plot_output_file,
        )
        # plot without global timeseries
        plot_output_file = output_path_handler.get_plot_output_file_path(
            region=REGIONS["global"],
            data_group=GLAMBIE_DATA_GROUPS["consensus"],
            plot_file_name="3_global_picture_gt_regional.png",
        )
        plot_combination_of_regions_to_global(
            catalogue_region_results=regional_results_catalogue_homogenized_gt,
            global_timeseries=None,
            region=REGIONS["global"],
            output_filepath=plot_output_file,
            plot_errors=False,
        )
        csv_output_file = output_path_handler.get_csv_output_file_path(
            region=REGIONS["global"],
            data_group=GLAMBIE_DATA_GROUPS["consensus"],
            csv_file_name="global_gt.csv",
        )
        global_timeseries_gt.save_data_as_csv(csv_output_file)

        # save out regional results homogenized to calendar year (in mwe and in gt)
        for results in zip(
            regional_results_catalogue_homogenized.datasets,
            regional_results_catalogue_homogenized_gt.datasets,
        ):
            for result in results:
                result.save_data_as_csv(
                    output_path_handler.get_csv_output_file_path(
                        region=result.region,
                        data_group=GLAMBIE_DATA_GROUPS["consensus"],
                        csv_file_name=f"consensus_calendar_year_{result.unit.lower()}_{result.region.name}.csv",
                    )
                )

    return global_timeseries_mwe


def _homogenize_regional_results_to_calendar_year(
    glambie_run_config: GlambieRunConfig,
    regional_results_catalogue: DataCatalogue,
    original_data_catalogue: DataCatalogue,
) -> DataCatalogue:
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
            region_name=region_config.region_name
        )
        seasonal_calibration_dataset = prepare_seasonal_calibration_dataset(
            region_config,
            data_catalogue,
            glambie_run_config.rgi_area_version,
            get_glambie_bucket_name(glambie_run_config.glambie_version),
        )
        # step 2: homogenize to calendar year
        data_set = regional_results_catalogue.get_filtered_catalogue(
            region_name=region_config.region_name
        ).datasets[0]
        homogenized_regional_results.append(
            data_set.shift_timeseries_to_annual_grid_with_seasonal_homogenization(
                seasonal_calibration_dataset=seasonal_calibration_dataset,
                year_type=YearType.CALENDAR,
                p_value=0,
            )
        )

    result_catalogue = DataCatalogue.from_list(homogenized_regional_results)
    return result_catalogue


def _combine_regional_results_into_global(
    regional_results_catalogue: DataCatalogue, rgi_area_version: int
) -> Timeseries:
    """
    Combines all regional results into one global timeseries.
    Assumes that timeseries are all in same grid and resolution temporally (e.g. calendar year) and of unit mwe or Gt.

    Parameters
    ----------
    regional_results_catalogue : DataCatalogue
        regional results (homogenized to the same year)
        rgi_area_version : int
            version of RGI area to use for area adjustment

    Returns
    -------
    Timeseries
        Globally aggregated timeseries in input unit
    """
    assert regional_results_catalogue.datasets_are_same_unit()
    assert (
        regional_results_catalogue.datasets[0].unit == "mwe"
        or regional_results_catalogue.datasets[0].unit.lower() == "gt"
    )

    if regional_results_catalogue.datasets[0].unit == "mwe":
        for ds in regional_results_catalogue.datasets:
            assert ds.area_change_applied

    # merge all dataframes
    catalogue_dfs = [
        ds.data.as_dataframe() for ds in regional_results_catalogue.datasets
    ]

    for df, ds in zip(catalogue_dfs, regional_results_catalogue.datasets):
        if regional_results_catalogue.datasets[0].unit.lower() == "mwe":
            # make list of adjusted areas
            adjusted_areas = [
                ds.region.get_adjusted_area(
                    start_date, end_date, rgi_area_version=rgi_area_version
                )
                for start_date, end_date in zip(df["start_dates"], df["end_dates"])
            ]
            # multiply changes and errors with area for each region
            df["changes"] = df["changes"] * adjusted_areas
            df["errors"] = (
                df["errors"] * adjusted_areas
            )  # apply weighted mean error propagation
            df["areas"] = adjusted_areas
        df["errors"] = df["errors"] ** 2  # square errors for error propagation

    # join all catalogues by start and end dates
    # the resulting dataframe has a set of columns with repeating prefixes
    df_merged_all = pd.concat(
        [x.set_index(["start_dates", "end_dates"]) for x in catalogue_dfs],
        axis=1,
        keys=range(len(catalogue_dfs)),
    )
    df_merged_all.columns = df_merged_all.columns.map("{0[1]}_{0[0]}".format)
    df_merged_all = df_merged_all.sort_values(by="start_dates")
    df_merged_all = df_merged_all.reset_index()
    start_dates, end_dates = (
        np.array(df_merged_all["start_dates"]),
        np.array(df_merged_all["end_dates"]),
    )

    # calculate sum of changes
    mean_changes = np.array(
        df_merged_all[
            df_merged_all.columns.intersection(
                df_merged_all.filter(regex=("changes*")).columns.to_list()
            )
        ].sum(axis=1)
    )
    # calculate sum of areas
    total_area = np.array(
        df_merged_all[
            df_merged_all.columns.intersection(
                df_merged_all.filter(regex=("areas*")).columns.to_list()
            )
        ].sum(axis=1)
    )
    # apply sum and square root to (squared) errors
    mean_uncertainties = np.sqrt(
        np.array(
            df_merged_all[
                df_merged_all.columns.intersection(
                    df_merged_all.filter(regex=("errors*")).columns.to_list()
                )
            ].sum(axis=1)
        ).astype(np.float64)
    )

    if regional_results_catalogue.datasets[0].unit.lower() == "mwe":
        # divide results in mwe my total_area
        # total_area = np.sum([ds.region.rgi6_area for ds in regional_results_catalogue.datasets])
        mean_changes = mean_changes / total_area
        mean_uncertainties = mean_uncertainties / total_area

    # make timeseries object with combined solution
    ts_data = TimeseriesData(
        start_dates=start_dates,
        end_dates=end_dates,
        changes=mean_changes,
        errors=mean_uncertainties,
        glacier_area_reference=None,
        glacier_area_observed=None,
        hydrological_correction_value=None,
        remarks=None,
    )
    # use this as a reference for filling metadata
    reference_dataset_for_metadata = regional_results_catalogue.datasets[0]

    return Timeseries(
        region=REGIONS["global"],
        data_group=GLAMBIE_DATA_GROUPS["consensus"],
        data=ts_data,
        unit=reference_dataset_for_metadata.unit,
    )
