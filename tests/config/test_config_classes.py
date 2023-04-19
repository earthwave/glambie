from glambie.config.config_classes import GlambieRunConfig
import pytest
import os
import yaml


def test_glambie_run_config_from_dict_raises_key_error():
    with pytest.raises(KeyError):
        config_dict = {}
        GlambieRunConfig.from_params(**config_dict)


def test_glambie_run_config_from_file():
    yaml_abspath = os.path.join('tests', 'test_data', 'configs', 'test_config.yaml')
    config = GlambieRunConfig.from_yaml(yaml_abspath)
    with open(yaml_abspath, 'r') as fh:
        config_dict = yaml.safe_load(fh)
        assert config_dict["catalogue_path"] == config.catalogue_path
