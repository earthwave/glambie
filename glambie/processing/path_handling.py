from glambie.const.regions import RGIRegion
from glambie.const.data_groups import GlambieDataGroup
import os
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
        os.makedirs(self.base_path, exist_ok=True)

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
        os.makedirs(folder_path, exist_ok=True)
        return folder_path

    def get_config_output_folder_path(self) -> str:
        """
        Returns requested folder path for saving configs of a run.
        If a folder dosen't exist it is iteratively created on the fly.

        Returns
        -------
        str
            output folder path
        """
        folder_path = os.path.join(self.base_path, "configs")
        os.makedirs(folder_path, exist_ok=True)
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
        os.makedirs(folder_path, exist_ok=True)
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
        os.makedirs(folder_path, exist_ok=True)
        return os.path.join(folder_path, plot_file_name)

    def get_csv_output_file_path(self,
                                 region: RGIRegion,
                                 data_group: GlambieDataGroup,
                                 csv_file_name: str,
                                 subfolder: str = "") -> str:
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
        subfolder : str
            subfolder in which to save the plot, default ''
        Returns
        -------
        str
            output file path of csv
        """
        folder_path = os.path.join(self.base_path, region.name, data_group.name, "csvs", subfolder)
        os.makedirs(folder_path, exist_ok=True)
        return os.path.join(folder_path, csv_file_name)


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
    return OutputPathHandler(os.path.join(base_output_dir, datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')))
