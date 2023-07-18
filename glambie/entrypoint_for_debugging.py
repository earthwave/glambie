"""
Just a file for debudding the entrypoint"""
from glambie.processing.main import run_glambie_assessment
from glambie.config.config_classes import GlambieRunConfig
from glambie.monitoring.logging import setup_logging
from glambie.processing.path_handling import get_output_path_handler_with_timestamped_subfolder

if __name__ == '__main__':
    # get config object
    # config_path = "tests/test_data/configs/config_pilot_study.yaml"
    config_path = "main_study_config_files/0_parent_config.yaml"
    config_object = GlambieRunConfig.from_yaml(config_path)
    log_level = "DEBUG"
    # set up logging
    setup_logging(log_level=log_level)
    glambie_run_config = GlambieRunConfig.from_yaml(config_path)

    # get config object
    output_path_handler = get_output_path_handler_with_timestamped_subfolder(glambie_run_config.result_base_path)

    # run assessment
    run_glambie_assessment(glambie_run_config=glambie_run_config, output_path_handler=output_path_handler)
