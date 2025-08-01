"""
Configuration control dataclasses for GlaMBIE.
"""
from dataclasses import dataclass
import yaml
import logging
from abc import ABC, abstractclassmethod
from glambie.const.constants import ExtractTrendsMethod, YearType, SeasonalCorrectionMethod
from glambie.config.yaml_helpers import region_run_config_class_representer, year_type_class_representer
from glambie.const.data_groups import GLAMBIE_DATA_GROUPS, GlambieDataGroup
import os

log = logging.getLogger(__name__)


class Config(ABC):
    """
    Abstract base class for configuration classes
    """

    @classmethod
    def _validate_dict(cls, config_dict):
        config_dict_key_set = set(config_dict.keys())
        reference_dict_key_set = {k for k, v in cls.__dataclass_fields__.items() if v.init}

        if config_dict_key_set != reference_dict_key_set:
            error_msg = f'The config dictionary is not in the correct format for {cls}. '
            unexpected_keys = sorted(config_dict_key_set - reference_dict_key_set)
            if len(unexpected_keys) > 0:
                error_msg += f'The config dictionary contains the following unexpected keys: {unexpected_keys}. '
            missing_keys = sorted(reference_dict_key_set - config_dict_key_set)
            if len(missing_keys) > 0:
                error_msg += f'The config dictionary is missing the following keys: {missing_keys}. '
            log.error(error_msg)
            raise KeyError(error_msg)

    @classmethod
    def from_yaml(cls, yaml_abspath):
        # validate we get expected values
        with open(yaml_abspath, 'r') as fh:
            config_dict = yaml.safe_load(fh)
            return cls.from_params(**config_dict)

    @abstractclassmethod
    def from_params(self):
        pass


@dataclass
class RegionRunConfig(Config):
    region_name: str
    year_type: YearType
    seasonal_correction_dataset: list
    region_run_settings: list

    @classmethod
    def from_params(cls, **config):
        # validate we get expected values
        cls._validate_dict(config)
        config_obj = cls(**config)
        config_obj._init_year_type()
        return config_obj

    def _init_year_type(self):
        if not isinstance(self.year_type, YearType):
            self.year_type = YearType(self.year_type)

    def save_to_yaml(self, out_path):
        yaml.add_representer(RegionRunConfig, region_run_config_class_representer)
        yaml.add_representer(YearType, year_type_class_representer)
        with open(out_path, 'w') as outfile:
            outfile.write(yaml.dump(self))


@dataclass
class GlambieRunConfig(Config):
    result_base_path: str
    region_config_base_path: str
    catalogue_path: str
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
            self.method_to_extract_trends = ExtractTrendsMethod(self.method_to_extract_trends)

    def _init_seasonal_correction_method(self):
        if not isinstance(self.seasonal_correction_method, SeasonalCorrectionMethod):
            self.seasonal_correction_method = SeasonalCorrectionMethod(self.seasonal_correction_method)

    def _init_glambie_region_run_settings(self):
        new_regions = []
        for region in self.regions:
            if isinstance(region, RegionRunConfig):  # in case already initiated
                new_regions.append(region)
            else:
                if region["enable_this_region"]:  # else we don't include it in the config
                    config_file_path = os.path.join(self.region_config_base_path, region["config_file_path"])
                    region_config = RegionRunConfig.from_yaml(config_file_path)
                    # check that region name is the same in both configs, throw error if not
                    if region_config.region_name != region["region_name"]:
                        error_msg = f'''The config region name from the GlambieRunConfig and the GlambieRegionConfig
                        do not match up: {region_config.region_name} != {region["region_name"]}.'''
                        log.error(error_msg)
                        raise ValueError(error_msg)
                    new_regions.append(region_config)
        self.regions = new_regions

    def save_to_yaml(self, output_folder_path: str):
        for region in self.regions:
            outfile = os.path.join(output_folder_path, f"{region.region_name}.yaml")
            region.save_to_yaml(outfile)
