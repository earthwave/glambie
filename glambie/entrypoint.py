"""
The single command line entry point for the package.

use as:

python -m glambie path/to/config.yaml
python -m glambie path/to/config.yaml -d -q

"""

import argparse
from glambie.processing.main import run_glambie_assessment
from glambie.config.config_classes import GlambieRunConfig
from glambie.monitoring.logger import setup_logging
from glambie.processing.path_handling import (
    get_output_path_handler_with_timestamped_subfolder,
)
import logging

log = logging.getLogger(__name__)


def main():
    # Build the argument parser
    parser = argparse.ArgumentParser(prog="glambie", description="GlaMBIE entry point.")
    parser.add_argument(
        "config", type=str, help="The config path to a yaml config file"
    )
    parser.add_argument(
        "-q",
        dest="quiet",
        action="store_true",
        help="run in quiet mode. No intermediate plots and results are saved out.",
    )
    parser.add_argument(
        "-d", dest="debug_mode", action="store_true", help="run in debug mode"
    )

    # parse the input arguments
    args = parser.parse_args()

    # get config object
    config_path = args.config
    glambie_run_config = GlambieRunConfig.from_yaml(config_path)

    # get logging level
    if args.debug_mode:
        log_level = "DEBUG"
    else:
        log_level = "INFO"

    # set up logging
    setup_logging(log_level=log_level)
    log.info(
        "Initiating GlaMBIE algorithm with config file = %s log_level = %s",
        config_path,
        log_level,
    )

    if not args.quiet:
        output_path_handler = get_output_path_handler_with_timestamped_subfolder(
            glambie_run_config.result_base_path
        )
        log.info("Output directory set to %s", output_path_handler.base_path)
    else:
        output_path_handler = None

    # run assessment
    run_glambie_assessment(
        glambie_run_config=glambie_run_config, output_path_handler=output_path_handler
    )

    print("Finished running GlaMBIE algorithm.")
