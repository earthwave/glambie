"""
Just a file for debudding the entrypoint"""
# from glambie.const.constants import YearType
# from glambie.processing.main import run_glambie_assessment
from glambie.config.config_classes import GlambieRunConfig, RegionRunConfig
from glambie.const.constants import YearType
import yaml


def main():
    # create a list of custom classes, some of which contain nested classes
    # config_path = "tests/test_data/configs/config_pilot_study.yaml"
    config_path = "tests/test_data/configs/test_config.yaml"
    stuff = [GlambieRunConfig.from_yaml(config_path).regions[0]]
    # use a custom representer to forcibly convert the object to its own dictionary

    def region_run_config_class_representer(
            yaml_dumper: yaml.dumper.Dumper,
            object_to_represent: RegionRunConfig) -> yaml.nodes.MappingNode:
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

    def year_type_class_representer(
            yaml_dumper: yaml.dumper.Dumper,
            object_to_represent: YearType) -> yaml.nodes.MappingNode:
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

    yaml.add_representer(RegionRunConfig, region_run_config_class_representer)
    yaml.add_representer(YearType, year_type_class_representer)

    print(yaml.dump(stuff))
    # YearType.GLACIOLOGICAL
    # dumper = yaml.dumper.Dumper().
    # print(dumper.represent_dict(YearType.GLACIOLOGICAL.__dict__))


if __name__ == '__main__':
    main()


# if __name__ == '__main__':
#     # get config object
#     config_path = "tests/test_data/configs/config_pilot_study.yaml"
#     config_object = GlambieRunConfig.from_yaml(config_path)

#     #config_object.save_to_yaml("output_plots/test")

#     #print(yaml.dump(config_object))
#     yaml.encoding = None
#     yaml.representer.represent_mapping = strip_python_tags
#     #yaml.dump(config_object, sys.stdout)
#     y = yaml.dump(config_object.regions[0])
#     y = strip_python_tags(y)
#     # with open('tests/test_data/configs/iceland-out.yaml', 'w') as outfile:
#     #     yaml.dump(config_object.regions[0], outfile, default_flow_style=False)

#     with open('tests/test_data/configs/iceland-out.yaml', 'w') as outfile:
#         outfile.write(y)

#     rrc = RegionRunConfig.from_yaml('tests/test_data/configs/iceland-out.yaml')

#     #print(config_object.region_config_base_path)

#     # log_level = "DEBUG"
#     # # set up logging
#     # setup_logging(log_level=log_level)
#     # glambie_run_config = GlambieRunConfig.from_yaml(config_path)

#     # # get config object
#     # output_path_handler = get_output_path_handler_with_timestamped_subfolder(glambie_run_config.result_base_path)

#     # # run assessment
#     # run_glambie_assessment(glambie_run_config=glambie_run_config, output_path_handler=output_path_handler)
