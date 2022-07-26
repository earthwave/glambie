import pytest
from glambie.data.data_catalogue import DataCatalogue
import os


@pytest.fixture()
def example_catalogue():
    return DataCatalogue({"basepath": ["tests", "test_data", "datastore"],
                          "datasets": [
                              {
                                  "filename": "iceland_altimetry_sharks.csv",
                                  "region": "iceland",
                                  "user_group": "sharks",
                                  "data_group": "altimetry"
                              },
                              {
                                  "filename": "svalbard_altimetry_sharks.csv",
                                  "region": "svalbard",
                                  "user_group": "sharks",
                                  "data_group": "altimetry"
                              },
                              {
                                  "filename": "svalbard_altimetry_lions.csv",
                                  "region": "svalbard",
                                  "user_group": "lions",
                                  "data_group": "altimetry"
                              }]})


def test_data_catalogue_can_be_initiated(example_catalogue):
    assert example_catalogue is not None


def test_data_catalogue_datasets_length(example_catalogue):
    assert len(example_catalogue) == 3


def test_data_catalogue_datasets_correctly_ingested(example_catalogue):
    assert example_catalogue.datasets[0].user_group == 'sharks'
    assert example_catalogue.datasets[2].user_group == 'lions'
    assert example_catalogue.datasets[2].region.name == 'svalbard'
    assert example_catalogue.datasets[2].data_group.name == 'altimetry'


def test_get_datasets_by_region(example_catalogue):
    assert len(example_catalogue.get_datasets_by_region('svalbard')) == 2


def test_as_dataframe(example_catalogue):
    df = example_catalogue.as_dataframe()
    assert df.shape[0] == 3  # should be 3 columns long


def test_data_catalogue_from_file():
    catalogue = DataCatalogue.from_file(os.path.join('tests', 'test_data', 'datastore', 'meta.json'))
    assert len(catalogue.datasets) == 4
