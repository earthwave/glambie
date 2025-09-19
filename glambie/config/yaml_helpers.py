from glambie.const.constants import YearType
import yaml


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
