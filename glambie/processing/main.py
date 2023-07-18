import logging
from glambie.config.config_classes import GlambieRunConfig
from glambie.data.data_catalogue import DataCatalogue
from glambie.data.submission_system_interface import SUBMISSION_SYSTEM_BASEPATH_PLACEHOLDER
from glambie.processing.process_regional_results import run_one_region, combine_within_one_region
from glambie.processing.path_handling import OutputPathHandler
from glambie.processing.process_global_results import run_global_results
from typing import Tuple

log = logging.getLogger(__name__)


def run_glambie_assessment(glambie_run_config: GlambieRunConfig,
                           output_path_handler: OutputPathHandler):
    """
    Runs the glambie assessment algorithm

    Parameters
    ----------
    glambie_run_config : GlambieRunConfig
        Glambie run config object, which specifies the run parameters
    output_path_handler : OutputPathHandler
        Run output handler. If None, no plots/csvs etc. will be saved out.
    """
    # save out configs
    if output_path_handler is not None:
        glambie_run_config.save_to_yaml(output_path_handler.get_config_output_folder_path())

    # load catalogue
    data_catalogue_original = _load_catalogue_and_data(glambie_run_config.catalogue_path)

    # run regional results
    results_catalogue_combined_per_region, _ = _run_regional_results(
        glambie_run_config, data_catalogue_original, output_path_handler=output_path_handler)

    # run global results
    if len(results_catalogue_combined_per_region.datasets) > 0:
        run_global_results(glambie_run_config=glambie_run_config,
                           regional_results_catalogue=results_catalogue_combined_per_region,
                           original_data_catalogue=data_catalogue_original,
                           output_path_handler=output_path_handler)


def _run_regional_results(glambie_run_config: GlambieRunConfig,
                          data_catalogue: DataCatalogue,
                          output_path_handler: OutputPathHandler) -> Tuple[DataCatalogue, DataCatalogue]:
    """
    Runs the algorithm within each individual region

    Parameters
    ----------
    glambie_run_config : GlambieRunConfig
        Glambie run config object, which specifies the run parameters
    data_catalogue : DataCatalogue
        Data Catalogue with all input datasets
    output_path_handler : OutputPathHandler
        Run output handler. If None, no plots/csvs etc. will be saved out.

    Returns
    -------
    Tuple[DataCatalogue, DataCatalogue]
        - Data Catalogue with regional results. Contains one timeseries per region specified to run within the config.
    """
    data_group_results_per_region = []
    combined_regional_results = []
    for region_config in glambie_run_config.regions:
        log.info('Starting to process region=%s', region_config.region_name)
        results_one_region = run_one_region(glambie_run_config=glambie_run_config,
                                            region_config=region_config,
                                            data_catalogue=data_catalogue,
                                            output_path_handler=output_path_handler)
        data_group_results_per_region.extend(results_one_region.datasets)

        # get combined regional results combining the individual data group results
        if len(data_group_results_per_region) > 0:
            combined_results = combine_within_one_region(results_one_region, output_path_handler)
            combined_regional_results.append(combined_results)

    catalogue_data_group_results_per_region = DataCatalogue.from_list(
        data_group_results_per_region)
    catalogue_combined_regional_results = DataCatalogue.from_list(
        combined_regional_results)

    return catalogue_combined_regional_results, catalogue_data_group_results_per_region


def _load_catalogue_and_data(data_catalogue_path: str) -> DataCatalogue:
    """
    Loads data catalogue and reads all data from a file path, or the submission system.

    Parameters
    ----------
    data_catalogue_path : str
        absolute file path to database metadata file

    Returns
    -------
    DataCatalogue
        Data Catalogue with all data loaded
    """
    # read catalogue
    if data_catalogue_path == SUBMISSION_SYSTEM_BASEPATH_PLACEHOLDER:
        catalogue = DataCatalogue.from_glambie_submission_system()
    else:
        catalogue = DataCatalogue.from_json_file(data_catalogue_path)
    catalogue.load_all_data()
    return catalogue
