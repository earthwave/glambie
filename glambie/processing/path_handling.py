from glambie.const.regions import RGIRegion
from glambie.const.data_groups import GlambieDataGroup
import os
from pathlib import Path


class OuputPathHandler():
    """
    Handles paths for Glambie processing intermediate results, plots and other outputs
    """

    def __init__(self, base_path: str):
        """
        Constructor

        Parameters
        ----------
        base_path : str
            base path of the outputs
        """
        self.base_path = base_path

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
        If a folder dosen't exist it is iteratively created on the fly.

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
