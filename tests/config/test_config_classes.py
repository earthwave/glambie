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


def test_write_glambie_run_config_to_yaml(tmp_path):
    yaml_abspath = os.path.join("tests", "test_data", "configs", "test_config.yaml")
    config = GlambieRunConfig.from_yaml(yaml_abspath)
    config.save_to_yaml(str(tmp_path))

    parent_outfile = os.path.join(tmp_path, "0_parent.yaml")
    assert os.path.exists(parent_outfile)

    # Check a region yaml was also written out
    for region in config.regions:
        assert os.path.exists(os.path.join(tmp_path, f"{region.region_name}.yaml"))

    # Verify the raw yaml content matches the original config values
    with open(parent_outfile, "r") as fh:
        raw = yaml.safe_load(fh)

    assert raw["glambie_version"] == config.glambie_version
    assert raw["start_year"] == config.start_year
    assert raw["end_year"] == config.end_year
    assert raw["rgi_area_version"] == config.rgi_area_version
    assert raw["method_to_extract_trends"] == config.method_to_extract_trends.value
    assert raw["seasonal_correction_method"] == config.seasonal_correction_method.value

    # datagroups_to_calculate must be plain strings, not full dicts
    assert all(isinstance(g, str) for g in raw["datagroups_to_calculate"])
    assert raw["datagroups_to_calculate"] == [g.name for g in config.datagroups_to_calculate]

    # regions must be minimal dicts with the expected keys
    assert [r["region_name"] for r in raw["regions"]] == [r.region_name for r in config.regions]
    assert all(r["enable_this_region"] is True for r in raw["regions"])
    assert all("config_file_path" in r for r in raw["regions"])


def test_write_glambie_region_config_to_yaml(tmp_path):
    yaml_inpath = os.path.join(
        "tests", "test_data", "configs", "glambie-2", "test_config_svalbard.yaml"
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
