
import os
from glambie.processing.path_handling import OutputPathHandler
from glambie.const.regions import REGIONS
from glambie.const.data_groups import GLAMBIE_DATA_GROUPS
import pytest


@pytest.fixture
def path_helper(tmp_path: os.PathLike):
    return OutputPathHandler(tmp_path)


def test_get_region_output_folder_path(path_helper: OutputPathHandler, tmp_path: os.PathLike):
    region = REGIONS["iceland"]
    region_path = path_helper.get_region_output_folder_path(region=region)
    assert path_helper.base_path == tmp_path
    assert os.path.exists(region_path)
    assert os.path.join(tmp_path, f"{region.rgi_id}_{region.name}") == region_path


def test_get_region_and_data_group_output_folder_path(path_helper: OutputPathHandler):
    region = REGIONS["central_asia"]
    path = path_helper.get_region_and_data_group_output_folder_path(region=region,
                                                                    data_group=GLAMBIE_DATA_GROUPS["altimetry"])
    assert os.path.exists(path)
    # should be subpath of region
    region_path = path_helper.get_region_output_folder_path(region=region)
    assert os.path.realpath(path).startswith(os.path.abspath(region_path))


def test_get_plot_output_file_path(path_helper: OutputPathHandler):
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


def test_get_csv_output_file_path(path_helper: OutputPathHandler):
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


def test_get_config_output_folder_path(path_helper: OutputPathHandler, tmp_path: os.PathLike):
    config_path = path_helper.get_config_output_folder_path()
    assert path_helper.base_path == tmp_path
    assert os.path.exists(config_path)
    assert os.path.join(tmp_path, "configs") == config_path
