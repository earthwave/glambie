import os
from unittest.mock import patch

from glambie.data.data_catalogue import DataCatalogue
from glambie.data.timeseries import TimeseriesData
import pytest
import copy
import numpy as np
import pandas as pd


@pytest.fixture
def example_catalogue():
    return DataCatalogue.from_dict({"base_path": ["tests", "test_data", "datastore"],
                                    "datasets": [
        {
            "filename": "iceland_altimetry_sharks.csv",
            "region": "iceland",
            "user_group": "sharks",
            "data_group": "altimetry",
            "unit": "m"
        },
        {
            "filename": "svalbard_altimetry_sharks.csv",
            "region": "svalbard",
            "user_group": "sharks",
            "data_group": "altimetry",
            "unit": "m"
        },
        {
            "filename": "svalbard_altimetry_lions.csv",
            "region": "svalbard",
            "user_group": "lions",
            "data_group": "gravimetry",
            "unit": "m"
        }]})


@pytest.fixture
def example_catalogue_small():
    return DataCatalogue.from_dict({"base_path": ["tests", "test_data", "datastore"],
                                    "datasets": [
        {
            "filename": "central_asia_demdiff_sharks.csv",
            "region": "central_asia",
            "user_group": "sharks",
            "data_group": "demdiff",
            "unit": "m"
        }]})


def test_data_catalogue_can_be_instantiated(example_catalogue):
    assert example_catalogue is not None


def test_data_catalogue_datasets_length(example_catalogue):
    assert len(example_catalogue) == 3


def test_data_catalogue_datasets_correctly_ingested(example_catalogue):
    assert example_catalogue.datasets[0].user_group == 'sharks'
    assert example_catalogue.datasets[2].user_group == 'lions'
    assert example_catalogue.datasets[2].region.name == 'svalbard'
    assert example_catalogue.datasets[1].data_group.name == 'altimetry'
    assert example_catalogue.datasets[2].data_group.name == 'gravimetry'
    assert example_catalogue.datasets[0].unit == 'm'


def test_get_filtered_catalogue_by_region(example_catalogue):
    assert len(example_catalogue.get_filtered_catalogue(region_name='svalbard')) == 2


def test_get_filtered_catalogue_by_data_group(example_catalogue):
    assert len(example_catalogue.get_filtered_catalogue(data_group='altimetry')) == 2
    assert len(example_catalogue.get_filtered_catalogue(data_group='gravimetry')) == 1
    assert example_catalogue.get_filtered_catalogue(data_group='gravimetry').datasets[0].data_group.name == 'gravimetry'


def test_get_filtered_catalogue_by_region_and_data_group(example_catalogue):
    assert len(example_catalogue.get_filtered_catalogue(region_name='svalbard',
               data_group='altimetry')) == 1
    assert len(example_catalogue.get_filtered_catalogue(region_name='svalbard',
               data_group='altimetry')) == 1
    assert example_catalogue.get_filtered_catalogue(data_group='gravimetry').datasets[0].data_group.name == 'gravimetry'


def test_get_filtered_catalogue_by_user_group(example_catalogue):
    assert len(example_catalogue.get_filtered_catalogue(user_group='sharks')) == 2
    assert len(example_catalogue.get_filtered_catalogue(user_group='lions')) == 1


def test_as_dataframe(example_catalogue):
    df = example_catalogue.as_dataframe()
    assert df.shape[0] == 3  # should be 3 columns long


def test_data_catalogue_from_file():
    catalogue = DataCatalogue.from_json_file(os.path.join('tests', 'test_data', 'datastore', 'meta.json'))
    assert len(catalogue.datasets) == 4


def test_data_catalogue_from_submission_system():
    with (patch('glambie.data.data_catalogue.fetch_all_submission_metadata') as mock_fetch_metadata,
          patch('glambie.data.data_catalogue.fetch_timeseries_dataframe') as mock_fetch_dataframe):
        # return two fake metadata dicts
        mock_fetch_metadata.return_value = [
            {'region': 'ISL',
             'observational_source': 'altimetry',
             'lead_author_name': 'Gunnar Gunnarsson',
             'user_group': 'authors-altimetry',
             'rgi_version_select': '6.0',
             'lead_author_date_of_birth': 'May 18th 1889'},
            {'region': 'ISL',
             'observational_source': 'gravimetry',
             'lead_author_name': 'Gunnar Gunnarsson',
             'user_group': 'authors-gravimetry',
             'rgi_version_select': '6.0',
             'lead_author_date_of_birth': 'May 18th 1889'}
        ]
        # and return some fake data
        mock_fetch_dataframe.return_value = pd.DataFrame({
            'unit': ['m'],
            'start_date_fractional': [1],
            'end_date_fractional': [2],
            'glacier_change_observed': [3],
            'glacier_change_uncertainty': [4],
            'glacier_area_reference': [5],
            'glacier_area_observed': [6],
            'remarks': ['are we the baddies']
        })
        catalogue = DataCatalogue.from_glambie_submission_system("glambie2-submissions")
    assert len(catalogue.datasets) == 2
    assert catalogue.datasets_are_same_unit()
    assert catalogue.datasets[1].additional_metadata['lead_author_date_of_birth'] == 'May 18th 1889'


def test_data_catalogue_regions(example_catalogue):
    assert len(example_catalogue.regions) == 2   # should contain 2 unique regions


def test_load_all_data(example_catalogue_small):
    # data not loaded yet
    assert not example_catalogue_small.datasets[0].is_data_loaded
    # load data of entire catalogue
    example_catalogue_small.load_all_data()
    # now data should be loaded
    assert example_catalogue_small.datasets[0].is_data_loaded


def test_datasets_are_same_unit(example_catalogue):
    # all test datasets are in m
    assert example_catalogue.datasets_are_same_unit()

    # change first datasets unit
    example_catalogue.datasets[0].unit = "gt"
    assert not example_catalogue.datasets_are_same_unit()


def test_data_catalogue_copy(example_catalogue_small):
    example_catalogue_small.load_all_data()
    example_catalogue_copy = example_catalogue_small.copy()
    example_catalogue_copy.datasets[0].data.changes = [-4]
    assert example_catalogue_copy.datasets[0].data.changes[0] == -4
    assert example_catalogue_small.datasets[0].data.changes[0] != -4


def test_average_timeseries_in_catalogue_both_same(example_catalogue_small):
    example_catalogue_small.load_all_data()
    example_catalogue_small.datasets.append(copy.deepcopy(example_catalogue_small.datasets[0]))

    # since both timeseries are the same average should give back same as inputtimeseries
    result_timeseries, _ = example_catalogue_small.average_timeseries_in_catalogue(remove_trend=False,
                                                                                   add_trend_after_averaging=False)
    assert np.array_equal(result_timeseries.data.changes, example_catalogue_small.datasets[0].data.changes)


def test_average_timeseries_in_catalogue_example_with_doubled(example_catalogue_small):
    example_catalogue_small.load_all_data()
    example_catalogue_small.datasets.append(copy.deepcopy(example_catalogue_small.datasets[0]))

    # double the values for the test
    example_catalogue_small.datasets[0].data.changes = list(np.array(
        example_catalogue_small.datasets[0].data.changes) * 2)
    result_timeseries, _ = example_catalogue_small.average_timeseries_in_catalogue(remove_trend=False,
                                                                                   add_trend_after_averaging=False)
    # the result should then be 1.5 times initial timeseries
    assert np.array_equal(result_timeseries.data.changes, np.array(
        example_catalogue_small.datasets[1].data.changes) * 1.5)


def test_average_timeseries_in_catalogue_example_with_trends_removed(example_catalogue_small):
    example_catalogue_small.load_all_data()
    example_catalogue_small.datasets.append(copy.deepcopy(example_catalogue_small.datasets[0]))

    # double the values for the test
    example_catalogue_small.datasets[0].data.changes = list(np.array(
        example_catalogue_small.datasets[0].data.changes) * 2)
    result_timeseries, _ = example_catalogue_small.average_timeseries_in_catalogue(remove_trend=False,
                                                                                   add_trend_after_averaging=False)
    # remove trends
    result_timeseries_trend_removed, _ = example_catalogue_small \
        .average_timeseries_in_catalogue(remove_trend=True, add_trend_after_averaging=False)
    result_timeseries_trend_removed_added_after_averaging, _ = example_catalogue_small \
        .average_timeseries_in_catalogue(remove_trend=True, add_trend_after_averaging=True)
    # now we expect different results
    assert not np.array_equal(result_timeseries.data.changes, result_timeseries_trend_removed.data.changes)
    assert not np.array_equal(list(result_timeseries_trend_removed_added_after_averaging.data.changes),
                              result_timeseries_trend_removed.data.changes)
    assert np.allclose(result_timeseries_trend_removed_added_after_averaging.data.changes,
                       result_timeseries.data.changes)


def test_get_time_span_of_datasets(example_catalogue_small):
    example_catalogue_small.load_all_data()
    time_span = example_catalogue_small.get_time_span_of_datasets()
    # make sure all datasets are within the span
    for ds in example_catalogue_small.datasets:
        assert ds.data.min_start_date >= time_span[0]
        assert ds.data.max_end_date <= time_span[1]


def test_get_common_period_of_datasets_one_dataset(example_catalogue_small):
    example_catalogue_small.load_all_data()
    common_start_dates, common_end_dates = example_catalogue_small.get_common_period_of_datasets()
    # we only have one dataset within the catalogue so this should equal start and end dates of the dataset
    dataset_data = example_catalogue_small.datasets[0].data
    assert np.array_equal(dataset_data.start_dates, common_start_dates)
    assert np.array_equal(dataset_data.end_dates, common_end_dates)


def test_get_common_period_of_datasets_with_gaps(example_catalogue_small):
    example_catalogue_small.load_all_data()
    # let's add a dataset with a time gap
    ds_with_gaps = example_catalogue_small.datasets[0].copy()
    data = ds_with_gaps.data
    ds_with_gaps.data = TimeseriesData(start_dates=[*data.start_dates[:2], data.start_dates[3]],
                                       end_dates=[*data.end_dates[:2], data.end_dates[3]],
                                       changes=[*data.changes[:2], data.changes[3]],
                                       errors=[*data.errors[:2], data.errors[3]],
                                       glacier_area_reference=None, glacier_area_observed=None,
                                       hydrological_correction_value=None, remarks=None)

    catalogue = DataCatalogue.from_list([example_catalogue_small.datasets[0], ds_with_gaps])

    # now check if we get back expected values when one dataset has a gap
    common_start_dates, common_end_dates = catalogue.get_common_period_of_datasets()
    expected_start_dates = example_catalogue_small.datasets[0].data.start_dates
    expected_start_dates = [*expected_start_dates[:2], expected_start_dates[3]]
    expected_end_dates = example_catalogue_small.datasets[0].data.end_dates
    expected_end_dates = [*expected_end_dates[:2], expected_end_dates[3]]
    assert np.array_equal(common_start_dates, expected_start_dates)
    assert np.array_equal(common_end_dates, expected_end_dates)
