from glambie.processing.processing_helpers import filter_catalogue_with_config_settings
from glambie.const.data_groups import GLAMBIE_DATA_GROUPS
from glambie.data.data_catalogue import DataCatalogue
from glambie.config.config_classes import GlambieRunConfig
import pytest
import os


@pytest.fixture()
def example_catalogue_1():
    return DataCatalogue.from_dict({"base_path": ["tests", "test_data", "datastore"],
                                    "datasets": [
        {
            "filename": "xx.csv",
            "region": "svalbard",
            "user_group": "sharks",
            "data_group": "altimetry",
            "unit": "m"
        },
        {
            "filename": "xx.csv",
            "region": "svalbard",
            "user_group": "lions",
            "data_group": "altimetry",
            "unit": "m"
        }]})

@pytest.fixture()
def example_catalogue_2():
    return DataCatalogue.from_dict({"base_path": ["tests", "test_data", "datastore"],
                                    "datasets": [
        {
            "filename": "xx.csv",
            "region": "svalbard",
            "user_group": "sharks",
            "data_group": "demdiff",
            "unit": "m"
        },
        {
            "filename": "xx.csv",
            "region": "svalbard",
            "user_group": "sloths",
            "data_group": "demdiff",
            "unit": "m"
        },
        {
            "filename": "xx.csv",
            "region": "svalbard",
            "user_group": "lions",
            "data_group": "glaciological",
            "unit": "mwe"
        },
        {
            "filename": "xx.csv",
            "region": "svalbard",
            "user_group": "dolphins",
            "data_group": "glaciological",
            "unit": "mwe"
        }]})


@pytest.fixture()
def glambie_config():
    yaml_abspath = os.path.join('tests', 'test_data', 'configs', 'test_config.yaml')
    return GlambieRunConfig.from_yaml(yaml_abspath)


def test_filter_catalogue_with_config_settings(example_catalogue_1, glambie_config):
    data_group = GLAMBIE_DATA_GROUPS["altimetry"]
    data_catalogue = example_catalogue_1
    region_config = glambie_config.regions[1]

    datasets_annual, datasets_trend = filter_catalogue_with_config_settings(data_group=data_group,
                                                                            region_config=region_config,
                                                                            data_catalogue=data_catalogue)
    # we should have filtered out lions from this dataset
    assert len(datasets_annual.datasets) == 1
    assert all(d.user_group != "lions" for d in datasets_annual.datasets)

    # we should have filtered out sharks from this dataset
    assert len(datasets_annual.datasets) == 1
    assert all(d.user_group != "sharks" for d in datasets_trend.datasets)


def test_filter_catalogue_with_config_settings_demdiff_and_glaciological(example_catalogue_2, glambie_config):
    data_group = GLAMBIE_DATA_GROUPS["demdiff_and_glaciological"]
    data_catalogue = example_catalogue_2
    region_config = glambie_config.regions[1]

    datasets_annual, datasets_trend = filter_catalogue_with_config_settings(data_group=data_group,
                                                                            region_config=region_config,
                                                                            data_catalogue=data_catalogue)
    # we should have filtered out lions from this dataset
    assert len(datasets_annual.datasets) == 1
    assert all(d.user_group != "lions" for d in datasets_annual.datasets)
    assert all(d.data_group != GLAMBIE_DATA_GROUPS["demdiff"] for d in datasets_annual.datasets)
    assert any(d.user_group == "dolphins" for d in datasets_annual.datasets)

    # we should have filtered out sharks from this dataset
    assert len(datasets_annual.datasets) == 1
    assert all(d.user_group != "sharks" for d in datasets_trend.datasets)
    assert all(d.data_group != GLAMBIE_DATA_GROUPS["glaciological"] for d in datasets_trend.datasets)
    assert any(d.user_group == "sloths" for d in datasets_trend.datasets)
