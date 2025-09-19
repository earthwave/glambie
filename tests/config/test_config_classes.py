import os

from glambie.config.config_classes import GlambieRunConfig
from glambie.config.config_classes import RegionRunConfig
from glambie.const.constants import (
    ExtractTrendsMethod,
    YearType,
    SeasonalCorrectionMethod,
)
from glambie.const.data_groups import GlambieDataGroup
import pytest
import yaml


def test_glambie_run_config_from_dict_raises_key_error():
    config_dict = {}
    with pytest.raises(KeyError):
        GlambieRunConfig.from_params(
            **config_dict
        )  # empty config should raise key error


def test_glambie_run_config_from_file():
    yaml_abspath = os.path.join("tests", "test_data", "configs", "test_config.yaml")
    config = GlambieRunConfig.from_yaml(yaml_abspath)
    assert isinstance(config.method_to_extract_trends, ExtractTrendsMethod)
    assert isinstance(config.seasonal_correction_method, SeasonalCorrectionMethod)
    with open(yaml_abspath, "r") as fh:
        config_dict = yaml.safe_load(fh)
        assert config_dict["catalogue_path"] == config.catalogue_path
        assert all(
            isinstance(g, GlambieDataGroup) for g in config.datagroups_to_calculate
        )
        assert (
            config_dict["datagroups_to_calculate"][0]
            == config.datagroups_to_calculate[0].name
        )
        assert config.method_to_extract_trends == ExtractTrendsMethod(
            config_dict["method_to_extract_trends"]
        )
        assert config.seasonal_correction_method == SeasonalCorrectionMethod(
            config_dict["seasonal_correction_method"]
        )


def test_glambie_run_config_regions_from_file():
    yaml_abspath = os.path.join("tests", "test_data", "configs", "test_config.yaml")
    config = GlambieRunConfig.from_yaml(yaml_abspath)
    assert isinstance(config.regions[0].year_type, YearType)
    assert config.regions[0].seasonal_correction_dataset["user_group"] == "wgms_sine"


def test_write_glambie_region_config_to_yaml(tmp_path):
    yaml_inpath = os.path.join(
        "tests", "test_data", "configs", "test_config_svalbard.yaml"
    )
    yaml_outpath = os.path.join(tmp_path, "test-out-svalbard.yaml")
    config = RegionRunConfig.from_yaml(yaml_inpath)
    config.save_to_yaml(yaml_outpath)
    # check config file exists:
    assert os.path.exists(yaml_outpath)
    # check we can read file back in:
    config_written = RegionRunConfig.from_yaml(yaml_outpath)
    # assert same attributes
    assert config_written.region_run_settings == config.region_run_settings
