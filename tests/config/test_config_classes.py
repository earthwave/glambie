import os
import shutil

from glambie.config.config_classes import GlambieRunConfig
from glambie.config.config_classes import RegionRunConfig
from glambie.const.constants import YearType
from glambie.const.data_groups import GlambieDataGroup
from glambie.processing.path_handling import OutputPathHandler
import pytest
import yaml

TESTING_DIR = os.path.join("tests", "test_config_outputs")


@pytest.fixture(scope="session", autouse=True)
def output_path_handler():
    def remove_test_dir():
        shutil.rmtree(TESTING_DIR)
    yield OutputPathHandler(TESTING_DIR)
    # Cleanup a testing directory once we are finished.
    remove_test_dir()


def test_glambie_run_config_from_dict_raises_key_error():
    config_dict = {}
    with pytest.raises(KeyError):
        GlambieRunConfig.from_params(**config_dict)  # empty config should raise key error


def test_glambie_run_config_from_file():
    yaml_abspath = os.path.join('tests', 'test_data', 'configs', 'test_config.yaml')
    config = GlambieRunConfig.from_yaml(yaml_abspath)
    with open(yaml_abspath, 'r') as fh:
        config_dict = yaml.safe_load(fh)
        assert config_dict["catalogue_path"] == config.catalogue_path
        assert all(isinstance(g, GlambieDataGroup) for g in config.datagroups_to_calculate)
        assert config_dict["datagroups_to_calculate"][0] == config.datagroups_to_calculate[0].name


def test_glambie_run_config_regions_from_file():
    yaml_abspath = os.path.join('tests', 'test_data', 'configs', 'test_config.yaml')
    config = GlambieRunConfig.from_yaml(yaml_abspath)
    assert isinstance(config.regions[0].year_type, YearType)
    assert config.regions[0].seasonal_correction_dataset["user_group"] == "wgms_sine"


def test_write_glambie_region_config_to_yaml(output_path_handler):
    yaml_inpath = os.path.join('tests', 'test_data', 'configs', 'test_config_svalbard.yaml')
    yaml_outpath = os.path.join(output_path_handler.get_config_output_folder_path(), "test-out-svalbard.yaml")
    config = RegionRunConfig.from_yaml(yaml_inpath)
    config.save_to_yaml(yaml_outpath)
    # check config file exists:
    assert os.path.exists(yaml_outpath)
    # check we can read file back in:
    config_written = RegionRunConfig.from_yaml(yaml_outpath)
    # assert same attributes
    assert config_written.region_run_settings == config.region_run_settings
