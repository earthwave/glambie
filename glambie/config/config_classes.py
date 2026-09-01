"""
Configuration control dataclasses for GlaMBIE.
"""

from dataclasses import MISSING, dataclass
from typing import Literal
import yaml
import logging
from abc import ABC, abstractmethod
from glambie.const.constants import (
    ExtractTrendsMethod,
    YearType,
    SeasonalCorrectionMethod,
)
from glambie.config.yaml_helpers import (
    region_run_config_class_representer,
    year_type_class_representer,
    enum_class_representer,
    glambie_data_group_representer,
    glambie_run_config_representer,
)
from glambie.const.data_groups import GLAMBIE_DATA_GROUPS, GlambieDataGroup
import os
from enum import Enum


log = logging.getLogger(__name__)


class Config(ABC):
    """
    Abstract base class for configuration classes
    """

    @classmethod
    def _validate_dict(cls, config_dict):
        config_dict_key_set = set(config_dict.keys())
        # All dataclass fields that may appear in input dictionaries.
        reference_dict_key_set = {
            k for k, v in cls.__dataclass_fields__.items() if v.init
        }
        # Only fields without defaults are mandatory; fields with defaults are optional.
        required_dict_key_set = {
            k
            for k, v in cls.__dataclass_fields__.items()
            if v.init and v.default is MISSING and v.default_factory is MISSING
        }

        unexpected_keys = sorted(config_dict_key_set - reference_dict_key_set)
        # Missing optional fields are allowed; only enforce truly required keys.
        missing_keys = sorted(required_dict_key_set - config_dict_key_set)
        if unexpected_keys or missing_keys:
            error_msg = (
                f"The config dictionary is not in the correct format for {cls}. "
            )
            if unexpected_keys:
                error_msg += f"The config dictionary contains the following unexpected keys: {unexpected_keys}. "
            if missing_keys:
                error_msg += f"The config dictionary is missing the following keys: {missing_keys}. "
            log.error(error_msg)
            raise KeyError(error_msg)

    @classmethod
    def from_yaml(cls, yaml_abspath):
        # validate we get expected values
        with open(yaml_abspath, "r") as fh:
            config_dict = yaml.safe_load(fh)
            return cls.from_params(**config_dict)

    @classmethod
    @abstractmethod
    def from_params(cls, **_kwargs):
        pass


@dataclass
class RegionRunConfig(Config):
    region_name: str
    year_type: YearType
    seasonal_correction_dataset: list
    region_run_settings: list
    disable_data_groups: list[GlambieDataGroup] | None = None

    @classmethod
    def from_params(cls, **config):
        # validate we get expected values
        cls._validate_dict(config)
        config_obj = cls(**config)
        config_obj._init_year_type()
        config_obj._init_disable_data_groups()
        return config_obj

    def _init_year_type(self):
        if not isinstance(self.year_type, YearType):
            self.year_type = YearType(self.year_type)

    def _init_disable_data_groups(self):
        if self.disable_data_groups is None:
            return

        new_datagroup_list = []
        for group in self.disable_data_groups:
            if isinstance(group, GlambieDataGroup):
                new_datagroup_list.append(group)
            else:
                new_datagroup_list.append(GLAMBIE_DATA_GROUPS[group])
        self.disable_data_groups = new_datagroup_list

    def save_to_yaml(self, out_path):
        class _RegionConfigDumper(yaml.SafeDumper):
            pass

        _RegionConfigDumper.add_representer(RegionRunConfig, region_run_config_class_representer)
        _RegionConfigDumper.add_representer(GlambieDataGroup, glambie_data_group_representer)
        _RegionConfigDumper.add_representer(YearType, year_type_class_representer)
        _RegionConfigDumper.add_multi_representer(Enum, enum_class_representer)

        with open(out_path, "w") as outfile:
            yaml.dump(self, outfile, Dumper=_RegionConfigDumper, default_flow_style=False, sort_keys=False)


@dataclass
class GlambieRunConfig(Config):
    glambie_version: Literal[1, 2]
    config_folder: str
    result_base_path: str
    region_config_base_path: str
    datagroups_to_calculate: list[GlambieDataGroup]
    regions: list[RegionRunConfig]
    start_year: float
    end_year: float
    rgi_area_version: int
    method_to_extract_trends: str
    seasonal_correction_method: str

    @classmethod
    def from_params(cls: type[Config], **config_obj):
        # validate we get expected values
        cls._validate_dict(config_obj)
        config_obj = cls(**config_obj)
        config_obj._init_datagroups()
        config_obj._init_method_to_extract_trends()
        config_obj._init_seasonal_correction_method()
        config_obj._init_glambie_region_run_settings()
        return config_obj

    def _init_datagroups(self):
        new_datagroup_list = []
        for group in self.datagroups_to_calculate:  # in case already initiated
            if isinstance(group, GlambieDataGroup):
                new_datagroup_list.append(group)
            else:
                new_datagroup_list.append(GLAMBIE_DATA_GROUPS[group])
        self.datagroups_to_calculate = new_datagroup_list

    def _init_method_to_extract_trends(self):
        if not isinstance(self.method_to_extract_trends, ExtractTrendsMethod):
            self.method_to_extract_trends = ExtractTrendsMethod(
                self.method_to_extract_trends
            )

    def _init_seasonal_correction_method(self):
        if not isinstance(self.seasonal_correction_method, SeasonalCorrectionMethod):
            self.seasonal_correction_method = SeasonalCorrectionMethod(
                self.seasonal_correction_method
            )

    def _init_glambie_region_run_settings(self):
        new_regions = []
        for region in self.regions:
            if isinstance(region, RegionRunConfig):  # in case already initiated
                new_regions.append(region)
            else:
                if region[
                    "enable_this_region"
                ]:  # else we don't include it in the config
                    config_file_path = os.path.join(
                        self.region_config_base_path,
                        self.config_folder + str(self.glambie_version),
                        region["config_file_path"],
                    )
                    region_config = RegionRunConfig.from_yaml(config_file_path)
                    # check that region name is the same in both configs, throw error if not
                    if region_config.region_name != region["region_name"]:
                        error_msg = f"""The config region name from the GlambieRunConfig and the GlambieRegionConfig
                        do not match up: {region_config.region_name} != {region["region_name"]}."""
                        log.error(error_msg)
                        raise ValueError(error_msg)

                    # Parent config can optionally disable datagroups for this specific region.
                    if "disable_data_groups" in region:
                        region_config.disable_data_groups = region["disable_data_groups"]
                        region_config._init_disable_data_groups()
                    new_regions.append(region_config)
        self.regions = new_regions

    def save_to_yaml(self, output_folder_path: str):
        class _GlambieConfigDumper(yaml.SafeDumper):
            pass

        _GlambieConfigDumper.add_representer(GlambieRunConfig, glambie_run_config_representer)
        _GlambieConfigDumper.add_representer(GlambieDataGroup, glambie_data_group_representer)
        _GlambieConfigDumper.add_multi_representer(Enum, enum_class_representer)

        parent_outfile = os.path.join(output_folder_path, "0_parent.yaml")
        with open(parent_outfile, "w") as fh:
            yaml.dump(self, fh, Dumper=_GlambieConfigDumper, default_flow_style=False, sort_keys=False)
        # Save out the region configs as well
        for region in self.regions:
            outfile = os.path.join(output_folder_path, f"{region.region_name}.yaml")
            region.save_to_yaml(outfile)
