import logging

from glambie.data.data_catalogue import DataCatalogue
from glambie.const.data_groups import GlambieDataGroup
from glambie.data.timeseries import Timeseries
from glambie.processing.path_handling import OutputPathHandler
from glambie.const.regions import RGIRegion

log = logging.getLogger(__name__)


def save_all_csvs_for_region_data_group_processing(
    output_path_handler: OutputPathHandler,
    region: RGIRegion,
    data_group: GlambieDataGroup,
    data_catalogue_annual_raw: DataCatalogue,
    data_catalogue_trends_raw: DataCatalogue,
    data_catalogue_annual_homogenized: DataCatalogue,
    data_catalogue_annual_anomalies: DataCatalogue,
    data_catalogue_trends_homogenized: DataCatalogue,
    data_catalogue_calibrated_series: DataCatalogue,
    timeseries_annual_combined: Timeseries,
    timeseries_trend_combined: Timeseries,
):
    # save out all catalogues
    for ds in data_catalogue_annual_raw.datasets:
        ds.save_data_as_csv(
            output_path_handler.get_csv_output_file_path(
                region=region,
                data_group=data_group,
                subfolder="annual_raw",
                csv_file_name=f"{ds.user_group}.csv",
            )
        )
    for ds in data_catalogue_trends_raw.datasets:
        ds.save_data_as_csv(
            output_path_handler.get_csv_output_file_path(
                region=region,
                data_group=data_group,
                subfolder="trends_raw",
                csv_file_name=f"{ds.user_group}.csv",
            )
        )
    for ds in data_catalogue_annual_homogenized.datasets:
        ds.save_data_as_csv(
            output_path_handler.get_csv_output_file_path(
                region=region,
                data_group=data_group,
                subfolder="annual_homogenized",
                csv_file_name=f"{ds.user_group}.csv",
            )
        )
    for ds in data_catalogue_trends_homogenized.datasets:
        ds.save_data_as_csv(
            output_path_handler.get_csv_output_file_path(
                region=region,
                data_group=data_group,
                subfolder="trends_homogenized",
                csv_file_name=f"{ds.user_group}.csv",
            )
        )
    for ds in data_catalogue_annual_anomalies.datasets:
        ds.save_data_as_csv(
            output_path_handler.get_csv_output_file_path(
                region=region,
                data_group=data_group,
                subfolder="annual_anomalies",
                csv_file_name=f"{ds.user_group}.csv",
            )
        )
    for ds in data_catalogue_calibrated_series.datasets:
        ds.save_data_as_csv(
            output_path_handler.get_csv_output_file_path(
                region=region,
                data_group=data_group,
                subfolder="calibrated_series",
                csv_file_name=f"{ds.user_group}.csv",
            )
        )
    # save out combined timeseries
    timeseries_annual_combined.save_data_as_csv(
        output_path_handler.get_csv_output_file_path(
            region=region, data_group=data_group, csv_file_name="annual-combined.csv"
        )
    )
    timeseries_trend_combined.save_data_as_csv(
        output_path_handler.get_csv_output_file_path(
            region=region, data_group=data_group, csv_file_name="trends-combined.csv"
        )
    )
