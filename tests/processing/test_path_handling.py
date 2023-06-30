
import os
from glambie.processing.path_handling import OutputPathHandler
from glambie.const.regions import REGIONS
from glambie.const.data_groups import GLAMBIE_DATA_GROUPS
import pytest
import shutil

TESTING_DIR = os.path.join("tests", "test_output_path_handler")


@pytest.fixture(scope="session", autouse=True)
def path_helper():
    def remove_test_dir():
        shutil.rmtree(TESTING_DIR)
    yield OutputPathHandler(TESTING_DIR)
    # Cleanup a testing directory once we are finished.
    remove_test_dir()


def test_get_region_output_folder_path(path_helper):
    region = REGIONS["iceland"]
    region_path = path_helper.get_region_output_folder_path(region=region)
    assert path_helper.base_path == TESTING_DIR
    assert os.path.exists(region_path)
    assert os.path.join(TESTING_DIR, region.name) == region_path


def test_get_region_and_data_group_output_folder_path(path_helper):
    region = REGIONS["central_asia"]
    path = path_helper.get_region_and_data_group_output_folder_path(region=region,
                                                                    data_group=GLAMBIE_DATA_GROUPS["altimetry"])
    assert os.path.exists(path)
    # should be subpath of region
    region_path = path_helper.get_region_output_folder_path(region=region)
    assert os.path.realpath(path).startswith(os.path.abspath(region_path))


def test_get_plot_output_file_path(path_helper):
    region = REGIONS["svalbard"]
    plot_file_name = "test.png"
    plot_file_path = path_helper.get_plot_output_file_path(region=region,
                                                           data_group=GLAMBIE_DATA_GROUPS["altimetry"],
                                                           plot_file_name=plot_file_name)
    # directory should exist
    assert os.path.exists(os.path.dirname(plot_file_path))
    # should be subpath of region & data_group
    region_data_group_path = path_helper.get_region_and_data_group_output_folder_path(
        region=region, data_group=GLAMBIE_DATA_GROUPS["altimetry"])
    assert os.path.realpath(plot_file_path).startswith(os.path.abspath(region_data_group_path))
    assert os.path.split(plot_file_path)[1] == plot_file_name


def test_get_csv_output_file_path(path_helper):
    region = REGIONS["svalbard"]
    plot_file_name = "test.csv"
    plot_file_path = path_helper.get_plot_output_file_path(
        region=region, data_group=GLAMBIE_DATA_GROUPS["altimetry"], plot_file_name=plot_file_name)
    # directory should exist
    assert os.path.exists(os.path.dirname(plot_file_path))
    # should be subpath of region & data_group
    region_data_group_path = path_helper.get_region_and_data_group_output_folder_path(
        region=region, data_group=GLAMBIE_DATA_GROUPS["altimetry"])
    assert os.path.realpath(plot_file_path).startswith(os.path.abspath(region_data_group_path))
    assert os.path.split(plot_file_path)[1] == plot_file_name
