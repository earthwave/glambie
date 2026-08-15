from enum import Enum
from glambie.const.constants import YearType
from glambie.const.data_groups import GlambieDataGroup
import yaml


def enum_class_representer(
    yaml_dumper: yaml.dumper.Dumper, object_to_represent: Enum
) -> yaml.nodes.ScalarNode:
    """Represent any Enum as its value."""
    return yaml_dumper.represent_data(object_to_represent.value)


def glambie_data_group_representer(
    yaml_dumper: yaml.dumper.Dumper, object_to_represent: GlambieDataGroup
) -> yaml.nodes.ScalarNode:
    """Represent a GlambieDataGroup as its name string."""
    return yaml_dumper.represent_data(object_to_represent.name)


def glambie_run_config_representer(
    yaml_dumper: yaml.dumper.Dumper, object_to_represent
) -> yaml.nodes.MappingNode:
    """Represent a GlambieRunConfig as a plain dict, converting regions to
    minimal dicts (region_name + enable_this_region + config_file_path).

    Uses __dict__ (not dataclasses.asdict) so that registered representers
    for nested objects (GlambieDataGroup, Enum subclasses) are invoked.
    """
    d = dict(object_to_represent.__dict__)
    # Replace full RegionRunConfig objects with minimal reference dicts
    d["regions"] = [
        {
            "region_name": r.region_name,
            "enable_this_region": True,
            "config_file_path": f"{r.region_name}.yaml",
        }
        for r in object_to_represent.regions
    ]
    return yaml_dumper.represent_dict(d)


def year_type_class_representer(
    yaml_dumper: yaml.dumper.Dumper, object_to_represent: YearType
) -> yaml.nodes.MappingNode:
    """
    Class representer for YearType

    Parameters
    ----------
    yaml_dumper : yaml.dumper.Dumper
        yaml dumper
    object_to_represent : YearType
        YearType object to represent

    Returns
    -------
    yaml.nodes.MappingNode
        yaml map
    """
    return yaml_dumper.represent_data(object_to_represent.value)


def region_run_config_class_representer(
    yaml_dumper: yaml.dumper.Dumper, object_to_represent
) -> yaml.nodes.MappingNode:
    """
    Class representer for RegionRunConfig

    Parameters
    ----------
    yaml_dumper : yaml.dumper.Dumper
        yaml dumper
    object_to_represent : RegionRunConfig
        RegionRunConfig object to represent

    Returns
    -------
    yaml.nodes.MappingNode
        yaml map
    """
    return yaml_dumper.represent_dict(object_to_represent.__dict__)
