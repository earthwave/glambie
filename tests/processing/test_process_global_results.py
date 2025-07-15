
from glambie.config.config_classes import GlambieRunConfig
from glambie.processing.process_global_results import _combine_regional_results_into_global
from glambie.processing.process_global_results import run_global_results
import pytest
import numpy as np
import os
from unittest.mock import patch

from glambie.const.data_groups import GLAMBIE_DATA_GROUPS
from glambie.const.regions import REGIONS
from glambie.data.timeseries import Timeseries
from glambie.data.timeseries import TimeseriesData
from glambie.data.data_catalogue import DataCatalogue
from glambie.processing.output_helpers import OutputPathHandler


@pytest.fixture
def example_catalogue():
    data1 = TimeseriesData(start_dates=[2010, 2011],
                           end_dates=[2011, 2012],
                           changes=np.array([2., 5.]),
                           errors=np.array([1., 1.2]),
                           glacier_area_reference=np.array([None, None]),
                           glacier_area_observed=np.array([None, None]),
                           hydrological_correction_value=None,
                           remarks=None)
    ts1 = Timeseries(rgi_version=6,
                     unit='mwe',
                     data_group=GLAMBIE_DATA_GROUPS['consensus'],
                     data=data1,
                     region=REGIONS["iceland"],
                     area_change_applied=True)
    data2 = TimeseriesData(start_dates=[2010, 2011],
                           end_dates=[2011, 2012],
                           changes=np.array([3., 4.]),
                           errors=np.array([0.9, 1.1]),
                           glacier_area_reference=np.array([None, None]),
                           glacier_area_observed=np.array([None, None]),
                           hydrological_correction_value=None,
                           remarks=None)
    ts2 = Timeseries(rgi_version=6,
                     unit='mwe',
                     data_group=GLAMBIE_DATA_GROUPS['consensus'],
                     data=data2,
                     region=REGIONS["svalbard"],
                     area_change_applied=True)
    return DataCatalogue.from_list([ts1, ts2])


def test_combine_regional_results_into_global_in_mwe(example_catalogue):
    combined_result = _combine_regional_results_into_global(regional_results_catalogue=example_catalogue,
                                                            rgi_area_version=7)
    dataset1 = example_catalogue.datasets[0]
    dataset2 = example_catalogue.datasets[1]
    adjusted_areas_1 = [dataset1.region.get_adjusted_area(start_dates, end_dates, rgi_area_version=7)
                        for start_dates, end_dates
                        in zip(dataset1.data.start_dates, dataset1.data.end_dates)]
    adjusted_areas_2 = [dataset2.region.get_adjusted_area(start_dates, end_dates, rgi_area_version=7)
                        for start_dates, end_dates
                        in zip(dataset2.data.start_dates, dataset2.data.end_dates)]
    expected_result = (dataset1.data.changes * adjusted_areas_1
                       + dataset2.data.changes * adjusted_areas_2) / (
                           np.array(adjusted_areas_1) + np.array(adjusted_areas_2))
    assert np.array_equal(expected_result, combined_result.data.changes)


def test_combine_regional_results_into_global_in_mwe_errors(example_catalogue):
    combined_result = _combine_regional_results_into_global(regional_results_catalogue=example_catalogue,
                                                            rgi_area_version=7)
    dataset1 = example_catalogue.datasets[0]
    dataset2 = example_catalogue.datasets[1]
    adjusted_areas_1 = np.array([dataset1.region.get_adjusted_area(start_dates, end_dates, rgi_area_version=7)
                                 for start_dates, end_dates
                                 in zip(dataset1.data.start_dates, dataset1.data.end_dates)])
    adjusted_areas_2 = np.array([dataset2.region.get_adjusted_area(start_dates, end_dates, rgi_area_version=7)
                                 for start_dates, end_dates
                                 in zip(dataset2.data.start_dates, dataset2.data.end_dates)])
    # rules of weighted mean error propagation
    expected_errors = np.sqrt((dataset1.data.errors**2 * adjusted_areas_1**2)
                              + (dataset2.data.errors**2 * adjusted_areas_2**2)) / (adjusted_areas_1 + adjusted_areas_2)
    assert np.array_equal(expected_errors, combined_result.data.errors)


def test_combine_regional_results_into_global_in_gt(example_catalogue):
    example_catalogue.datasets[0].unit = "Gt"
    example_catalogue.datasets[1].unit = "Gt"
    combined_result = _combine_regional_results_into_global(regional_results_catalogue=example_catalogue,
                                                            rgi_area_version=7)
    dataset1 = example_catalogue.datasets[0]
    dataset2 = example_catalogue.datasets[1]

    expected_changes = dataset1.data.changes + dataset2.data.changes
    expected_errors = (dataset1.data.errors**2 + dataset2.data.errors**2)**0.5
    assert np.array_equal(expected_changes, combined_result.data.changes)
    assert np.array_equal(expected_errors, combined_result.data.errors)


def test_run_global_results_saves_csv2(tmp_path, example_catalogue):
    output_path_handler = OutputPathHandler(tmp_path)  # set output to a tmp_path
    yaml_abspath = os.path.join('tests', 'test_data', 'configs', 'test_config.yaml')
    glambie_run_config = GlambieRunConfig.from_yaml(yaml_abspath)

    # patch _homogenize_regional_results_to_calendar_year as we don't have a seasonal calibration datasets
    with (patch('glambie.processing.process_global_results._homogenize_regional_results_to_calendar_year')
          as patch_homogenize_regional_results_to_calendar_year):
        # simply return the input dataset instead of calibrating to calendar year
        patch_homogenize_regional_results_to_calendar_year.return_value = example_catalogue

        run_global_results(glambie_run_config=glambie_run_config,
                           regional_results_catalogue=example_catalogue,
                           original_data_catalogue=example_catalogue, output_path_handler=output_path_handler)

        # check csvs have been saved
        result = example_catalogue.datasets[0]
        expected_paths = []
        for result in example_catalogue.datasets:
            expected_paths.append(output_path_handler.get_csv_output_file_path(
                region=result.region, data_group=GLAMBIE_DATA_GROUPS["consensus"],
                csv_file_name=f"consensus_calendar_year_{result.unit.lower()}_{result.region.name}.csv"))
        for expected_path in expected_paths:
            assert os.path.exists(expected_path)
