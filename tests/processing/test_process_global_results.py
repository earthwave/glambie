
from glambie.processing.process_global_results import _combine_regional_results_into_global
import pytest
import numpy as np

from glambie.const.data_groups import GLAMBIE_DATA_GROUPS
from glambie.const.regions import REGIONS
from glambie.data.timeseries import Timeseries
from glambie.data.timeseries import TimeseriesData
from glambie.data.data_catalogue import DataCatalogue


@pytest.fixture()
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
                     region=REGIONS["iceland"])
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
                     region=REGIONS["svalbard"])
    return DataCatalogue.from_list([ts1, ts2])


def test_combine_regional_results_into_global(example_catalogue):
    combined_result = _combine_regional_results_into_global(regional_results_catalogue=example_catalogue)
    dataset1 = example_catalogue.datasets[0]
    dataset2 = example_catalogue.datasets[1]
    expected_result = (dataset1.data.changes * dataset1.region.rgi6_area
                       + dataset2.data.changes * dataset2.region.rgi6_area) / (
                           dataset1.region.rgi6_area + dataset2.region.rgi6_area)
    assert np.array_equal(expected_result, combined_result.data.changes)


def test_combine_regional_results_into_global_errors(example_catalogue):
    combined_result = _combine_regional_results_into_global(regional_results_catalogue=example_catalogue)
    dataset1 = example_catalogue.datasets[0]
    dataset2 = example_catalogue.datasets[1]
    total_area = dataset1.region.rgi6_area + dataset2.region.rgi6_area
    # rules of weighted mean error propagation
    expected_errors = np.sqrt((dataset1.data.errors**2 * dataset1.region.rgi6_area**2)
                              + (dataset2.data.errors**2 * dataset2.region.rgi6_area**2)) / total_area
    assert np.array_equal(expected_errors, combined_result.data.errors)
