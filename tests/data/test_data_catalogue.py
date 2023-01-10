import os

from glambie.data.data_catalogue import DataCatalogue
import pytest


@pytest.fixture()
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


@pytest.fixture()
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


def test_data_catalogue_can_be_initiated(example_catalogue):
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
