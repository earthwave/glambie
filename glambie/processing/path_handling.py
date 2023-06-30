from glambie.const.regions import RGIRegion
from glambie.const.data_groups import GlambieDataGroup
import os
from pathlib import Path
import datetime


class OutputPathHandler():
    """
    Handles paths for Glambie processing intermediate results, plots and other outputs
    """

    def __init__(self, base_path: str):
        """
        Creates base_path folder recursively if it doesn't already exist.

        Parameters
        ----------
        base_path : str
            base path of the outputs
        """
        self.base_path = base_path
        Path(self.base_path).mkdir(parents=True, exist_ok=True)

    def get_region_output_folder_path(self, region: RGIRegion) -> str:
        """
        Returns requested folder path for saving outputs.
        If a folder dosen't exist it is iteratively created on the fly.

        Parameters
        ----------
        region : RGIRegion
            RGI Region of outputs

        Returns
        -------
        str
            output folder path
        """
        folder_path = os.path.join(self.base_path, region.name)
        Path(folder_path).mkdir(parents=True, exist_ok=True)
        return folder_path

    def get_region_and_data_group_output_folder_path(self, region: RGIRegion, data_group: GlambieDataGroup) -> str:
        """
        Returns requested folder path for saving outputs.
        If a folder dosen't exist it is iteratively created on the fly.

        Parameters
        ----------
        region : RGIRegion
            RGI Region of outputs
        data_group : GlambieDataGroup
            Glambie Data Group of outputs

        Returns
        -------
        str
            output folder path
        """
        folder_path = os.path.join(self.base_path, region.name, data_group.name)
        Path(folder_path).mkdir(parents=True, exist_ok=True)
        return folder_path

    def get_plot_output_file_path(self, region: RGIRegion, data_group: GlambieDataGroup, plot_file_name: str) -> str:
        """
        Returns requested file path for saving output plot.
        If a folder doesn't exist it is iteratively created on the fly.

        Parameters
        ----------
        region : RGIRegion
            RGI Region of outputs
        data_group : GlambieDataGroup
            Glambie Data Group of outputs
        plot_file_name : str
            filename of the plot

        Returns
        -------
        str
            output file path of plot
        """
        folder_path = os.path.join(self.base_path, region.name, data_group.name, "plots")
        Path(folder_path).mkdir(parents=True, exist_ok=True)
        filepath = os.path.join(folder_path, plot_file_name)
        return filepath

    def get_csv_output_file_path(self, region: RGIRegion, data_group: GlambieDataGroup, csv_file_name: str) -> str:
        """
        Returns requested file path for saving output csv.
        If a folder doesn't exist it is iteratively created on the fly.

        Parameters
        ----------
        region : RGIRegion
            RGI Region of outputs
        data_group : GlambieDataGroup
            Glambie Data Group of outputs
        csv_file_name : str
            filename of the plot

        Returns
        -------
        str
            output file path of csv
        """
        folder_path = os.path.join(self.base_path, region.name, data_group.name, "csvs")
        Path(folder_path).mkdir(parents=True, exist_ok=True)
        filepath = os.path.join(folder_path, csv_file_name)
        return filepath


def get_output_path_handler_with_timestamped_subfolder(base_output_dir: str) -> OutputPathHandler:
    """
    Creates a OutputPathHandler with a timestamped subfolder from the base_output_dir.

    E.g. for a base_output_dir of '/output/path'
    the OutputPathHandler objects base_path would be '/output/path/2023-05-11_12-54'
    using the timestamp when calling the function as in YYYY-mm-dd-HH-MM

    Parameters
    ----------
    base_output_dir : str
        base path of outputs

    Returns
    -------
    OutputPathHandler
        Output Path Handler object
    """
    output_path = os.path.join(base_output_dir, datetime.datetime.now().strftime('%Y-%m-%d_%H-%M'))
    return OutputPathHandler(output_path)
