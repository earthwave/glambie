from glambie.config.config_classes import GlambieRunConfig
import pytest
import os
import yaml
from glambie.const.constants import YearType

from glambie.const.data_groups import GlambieDataGroup


def test_glambie_run_config_from_dict_raises_key_error():
    with pytest.raises(KeyError):
        config_dict = {}
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
