"""
Configuration control dataclasses for GlaMBIE.
"""
from dataclasses import dataclass
import yaml
from abc import ABC


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
            raise KeyError(error_msg)

    @classmethod
    def from_yaml(cls, yaml_abspath):
        # validate we get expected values
        with open(yaml_abspath, 'r') as fh:
            config_dict = yaml.safe_load(fh)
            return cls.from_params(**config_dict)


@dataclass
class RegionRunConfig(Config):

    @classmethod
    def from_params(cls, **config):
        # validate we get expected values
        cls._validate_dict(config)
        return cls(**config)


@dataclass
class GlambieRunConfig(Config):
    result_base_path: str
    region_config_base_path: str
    catalogue_path: str

    regions: list[RegionRunConfig]
    # regions_configs: list[RegionRunConfig]

    @classmethod
    def from_params(cls: type[Config], **config):
        # validate we get expected values
        cls._validate_dict(config)
        return cls(**config)
