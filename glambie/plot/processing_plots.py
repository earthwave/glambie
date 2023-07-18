
import matplotlib.pyplot as plt
from glambie.data.data_catalogue import DataCatalogue
from glambie.data.timeseries import Timeseries
from glambie.const.data_groups import GlambieDataGroup
from glambie.const.regions import RGIRegion
from glambie.processing.path_handling import OutputPathHandler
from glambie.processing.processing_helpers import convert_datasets_to_monthly_grid
from glambie.processing.processing_helpers import convert_datasets_to_unit_mwe
from glambie.plot.plot_helpers import get_colours, add_labels_axlines_and_title, finalise_save_to_file_and_close_plot
from glambie.plot.plot_helpers import plot_non_cumulative_timeseries_on_axis, plot_cumulative_timeseries_on_axis


def plot_all_plots_for_region_data_group_processing(output_path_handler: OutputPathHandler,
                                                    region: RGIRegion,
                                                    data_group: GlambieDataGroup,
                                                    data_catalogue_annual_raw: DataCatalogue,
                                                    data_catalogue_trends_raw: DataCatalogue,
                                                    data_catalogue_annual_homogenized: DataCatalogue,
                                                    data_catalogue_annual_anomalies: DataCatalogue,
                                                    timeseries_annual_combined: Timeseries,
                                                    data_catalogue_trends_homogenized: DataCatalogue,
                                                    data_catalogue_calibrated_series: DataCatalogue,
                                                    timeseries_trend_combined: Timeseries
                                                    ):
    plot_fp = output_path_handler.get_plot_output_file_path(region=region, data_group=data_group,
                                                            plot_file_name="1_annual_input_data.png")
    plot_raw_input_data_of_data_group(catalogue_raw=data_catalogue_annual_raw,
                                      trend_combined=timeseries_trend_combined,
                                      data_group=data_group,
                                      region=region,
                                      category="annual",
                                      output_filepath=plot_fp,
                                      plot_errors=True)
    # Convert to same unit as annual datasets now
    data_catalogue_annual_raw = convert_datasets_to_monthly_grid(data_catalogue_annual_raw)
    data_catalogue_annual_raw = convert_datasets_to_unit_mwe(data_catalogue_annual_raw)
    plot_fp = output_path_handler.get_plot_output_file_path(region=region, data_group=data_group,
                                                            plot_file_name="2_annual_homogenize_data_2.png")
    plot_raw_and_homogenized_input_data_of_data_group(catalogue_raw=data_catalogue_annual_raw,
                                                      catalogue_homogenized=data_catalogue_annual_homogenized,
                                                      trend_combined=timeseries_trend_combined,
                                                      data_group=data_group,
                                                      region=region,
                                                      category="annual",
                                                      output_filepath=plot_fp,
                                                      plot_errors=False)
    plot_fp = output_path_handler.get_plot_output_file_path(region=region, data_group=data_group,
                                                            plot_file_name="3_annual_homogenize_data.png")
    plot_homogenized_input_data_of_data_group(catalogue_annual=data_catalogue_annual_homogenized,
                                              trend_combined=timeseries_trend_combined,
                                              data_group=data_group,
                                              region=region,
                                              output_filepath=plot_fp,
                                              plot_errors=False)
    plot_fp = output_path_handler.get_plot_output_file_path(region=region, data_group=data_group,
                                                            plot_file_name="4_annual_variability.png")
    plot_annual_variability_of_data_group(catalogue_annual_anomalies=data_catalogue_annual_anomalies,
                                          timeseries_combined_annual=timeseries_annual_combined,
                                          data_group=data_group,
                                          region=region,
                                          output_filepath=plot_fp,
                                          plot_errors=False)
    plot_fp = output_path_handler.get_plot_output_file_path(region=region, data_group=data_group,
                                                            plot_file_name="5_trends_input_data.png")
    plot_raw_input_data_of_data_group(catalogue_raw=data_catalogue_trends_raw,
                                      trend_combined=timeseries_trend_combined,
                                      data_group=data_group,
                                      region=region,
                                      category="trends",
                                      output_filepath=plot_fp,
                                      plot_errors=False)
    data_catalogue_trends_raw = convert_datasets_to_monthly_grid(data_catalogue_trends_raw)
    data_catalogue_trends_raw = convert_datasets_to_unit_mwe(data_catalogue_trends_raw)
    plot_fp = output_path_handler.get_plot_output_file_path(region=region, data_group=data_group,
                                                            plot_file_name="6_trends_homogenize_data.png")
    plot_raw_and_homogenized_input_data_of_data_group(catalogue_raw=data_catalogue_trends_raw,
                                                      catalogue_homogenized=data_catalogue_trends_homogenized,
                                                      trend_combined=timeseries_trend_combined,
                                                      data_group=data_group,
                                                      region=region,
                                                      category="trends",
                                                      output_filepath=plot_fp,
                                                      plot_errors=False)
    plot_fp = output_path_handler.get_plot_output_file_path(region=region, data_group=data_group,
                                                            plot_file_name="7_trends_recalibration.png")
    plot_recalibration_of_annual_variability_with_trends(catalogue_trends=data_catalogue_trends_homogenized,
                                                         catalogue_calibrated_series=data_catalogue_calibrated_series,
                                                         trend_combined=timeseries_trend_combined,
                                                         data_group=data_group,
                                                         region=region,
                                                         output_filepath=plot_fp,
                                                         plot_errors=False)
    plot_fp = output_path_handler.get_plot_output_file_path(region=region, data_group=data_group,
                                                            plot_file_name="8_combined_result.png")
    plot_recalibrated_result_of_data_group(catalogue_trends=data_catalogue_trends_homogenized,
                                           catalogue_calibrated_series=data_catalogue_calibrated_series,
                                           trend_combined=timeseries_trend_combined,
                                           data_group=data_group,
                                           region=region,
                                           output_filepath=plot_fp,
                                           plot_errors=False)


def plot_raw_input_data_of_data_group(catalogue_raw: DataCatalogue,
                                      trend_combined: DataCatalogue,
                                      data_group: GlambieDataGroup,
                                      region: RGIRegion,
                                      category: str,
                                      output_filepath: str,
                                      plot_errors: bool = True):
    _, axes = plt.subplots(2, 1, figsize=(11, 6))
    colours = get_colours(len(catalogue_raw.datasets))

    # plot non-cumulative timeseries
    for count, ds in enumerate(catalogue_raw.datasets):
        plot_non_cumulative_timeseries_on_axis(
            result_dataframe=ds.data.as_dataframe(), ax=axes[0], colour=colours[count], plot_errors=plot_errors,
            label="Dataset: " + ds.user_group)

    # plot cumulative timeseries
    for count, ds in enumerate(catalogue_raw.datasets):
        plot_cumulative_timeseries_on_axis(
            timeseries=ds, ax=axes[1], colour=colours[count], plot_errors=plot_errors, linestyle="-",
            timeseries_for_vertical_adjustment=trend_combined,
            label="Dataset: " + ds.user_group)

    if len(catalogue_raw.datasets) > 0:
        unit = catalogue_raw.datasets[0].unit
    else:
        unit = "unknown"

    add_labels_axlines_and_title(
        axes=axes, unit=unit, legend_fontsize=7,
        title="{} - {} - {}: raw input data".format(region.long_name, data_group.long_name, category))
    finalise_save_to_file_and_close_plot(output_filepath)


def plot_raw_and_homogenized_input_data_of_data_group(catalogue_raw: DataCatalogue,
                                                      catalogue_homogenized: DataCatalogue,
                                                      trend_combined: DataCatalogue,
                                                      data_group: GlambieDataGroup,
                                                      region: RGIRegion,
                                                      category: str,
                                                      output_filepath: str,
                                                      plot_errors: bool = True):
    _, axes = plt.subplots(2, 1, figsize=(10, 6))
    colours = get_colours(len(catalogue_homogenized.datasets))

    # plot non-cumulative timeseries
    for count, ds in enumerate(catalogue_raw.datasets):
        plot_non_cumulative_timeseries_on_axis(
            result_dataframe=ds.data.as_dataframe(), ax=axes[0], colour=colours[count], plot_errors=plot_errors,
            label="Raw: " + ds.user_group, linestyle=(0, (1, 1)))

    for count, ds in enumerate(catalogue_homogenized.datasets):
        plot_non_cumulative_timeseries_on_axis(
            result_dataframe=ds.data.as_dataframe(), ax=axes[0], colour=colours[count], linestyle="-",
            plot_errors=plot_errors, label="Homog.: " + ds.user_group)

    # plot cumulative timeseries
    for count, ds_raw in enumerate(catalogue_raw.datasets):
        plot_cumulative_timeseries_on_axis(
            timeseries=ds_raw, ax=axes[1], colour=colours[count], plot_errors=plot_errors, linestyle=(0, (1, 1)),
            timeseries_for_vertical_adjustment=trend_combined,
            label="Raw: " + ds_raw.user_group)
    for count, ds_homog in enumerate(catalogue_homogenized.datasets):
        plot_cumulative_timeseries_on_axis(
            timeseries=ds_homog, ax=axes[1], colour=colours[count], plot_errors=plot_errors, linestyle="-",
            timeseries_for_vertical_adjustment=trend_combined,
            label="Homog.: " + ds_homog.user_group)

    add_labels_axlines_and_title(
        axes=axes, unit=trend_combined.unit, legend_fontsize=7,
        title="{} - {} - {}: raw input data".format(region.long_name, data_group.long_name, category))
    finalise_save_to_file_and_close_plot(output_filepath)


def plot_homogenized_input_data_of_data_group(catalogue_annual: DataCatalogue,
                                              trend_combined: DataCatalogue,
                                              data_group: GlambieDataGroup,
                                              region: RGIRegion,
                                              output_filepath: str,
                                              plot_errors: bool = True):
    _, axes = plt.subplots(2, 1, figsize=(10, 6))
    colours = get_colours(len(catalogue_annual.datasets))

    # plot non-cumulative timeseries
    for count, ds in enumerate(catalogue_annual.datasets):
        plot_non_cumulative_timeseries_on_axis(
            result_dataframe=ds.data.as_dataframe(), ax=axes[0], colour=colours[count], plot_errors=plot_errors,
            label="Dataset: " + ds.user_group)

    # plot cumulative timeseries
    for count, ds in enumerate(catalogue_annual.datasets):
        plot_cumulative_timeseries_on_axis(
            timeseries=ds, ax=axes[1], colour=colours[count], plot_errors=plot_errors, linestyle="-",
            timeseries_for_vertical_adjustment=trend_combined,
            label="Dataset: " + ds.user_group)

    add_labels_axlines_and_title(
        axes=axes, unit=catalogue_annual.datasets[0].unit, legend_fontsize=7,
        title="{} - {}: homogenized input data".format(region.long_name, data_group.long_name))
    finalise_save_to_file_and_close_plot(output_filepath)


def plot_annual_variability_of_data_group(catalogue_annual_anomalies: DataCatalogue,
                                          timeseries_combined_annual: Timeseries,
                                          data_group: GlambieDataGroup,
                                          region: RGIRegion,
                                          output_filepath: str,
                                          plot_errors: bool = True):
    _, axes = plt.subplots(2, 1, figsize=(10, 6))
    colours = get_colours(len(catalogue_annual_anomalies.datasets))

    # plot non-cumulative timeseries
    for count, ds in enumerate(catalogue_annual_anomalies.datasets):
        plot_non_cumulative_timeseries_on_axis(
            result_dataframe=ds.data.as_dataframe(), ax=axes[0], colour=colours[count], plot_errors=False,
            label="Dataset: " + ds.user_group)

    # plot non-cumulative timeseries - combined solution
    plot_non_cumulative_timeseries_on_axis(result_dataframe=timeseries_combined_annual.data.as_dataframe(),
                                           ax=axes[0], colour="black", linestyle="--", plot_errors=False)
    axes[0].plot([], [], label="{} - combined solution".format(data_group.long_name), color="black", linestyle="--")

    # plot cumulative timeseries
    for count, ds in enumerate(catalogue_annual_anomalies.datasets):
        plot_cumulative_timeseries_on_axis(
            timeseries=ds, ax=axes[1], colour=colours[count], plot_errors=plot_errors, linestyle="-",
            timeseries_for_vertical_adjustment=timeseries_combined_annual,
            label="Dataset: " + ds.user_group)

    plot_cumulative_timeseries_on_axis(
        timeseries=timeseries_combined_annual, ax=axes[1], colour="black", plot_errors=plot_errors, linestyle="--",
        timeseries_for_vertical_adjustment=None, label="{} - combined solution".format(data_group.long_name))

    add_labels_axlines_and_title(
        axes=axes, unit=catalogue_annual_anomalies.datasets[0].unit, legend_fontsize=7,
        title="{} - {}: annual anomalies".format(region.long_name, data_group.long_name))
    finalise_save_to_file_and_close_plot(output_filepath)


def plot_recalibration_of_annual_variability_with_trends(catalogue_trends: DataCatalogue,
                                                         catalogue_calibrated_series: DataCatalogue,
                                                         trend_combined: DataCatalogue,
                                                         data_group: GlambieDataGroup,
                                                         region: RGIRegion,
                                                         output_filepath: str,
                                                         plot_errors: bool = True):
    _, axes = plt.subplots(2, 1, figsize=(10, 6))
    colours = get_colours(len(catalogue_trends.datasets))

    # plot non-cumulative timeseries
    for count, (ds_trend, ds_annual) in enumerate(zip(catalogue_trends.datasets, catalogue_calibrated_series.datasets)):
        plot_non_cumulative_timeseries_on_axis(
            result_dataframe=ds_trend.data.as_dataframe(), ax=axes[0], colour=colours[count],
            label="Trend: " + ds_trend.user_group)
        plot_non_cumulative_timeseries_on_axis(
            result_dataframe=ds_annual.data.as_dataframe(), ax=axes[0], colour=colours[count], linestyle="--",
            label="Calibrated annual: " + ds_annual.user_group)

    # plot cumulative
    for count, (trends, annual) in enumerate(zip(catalogue_trends.datasets, catalogue_calibrated_series.datasets)):
        plot_cumulative_timeseries_on_axis(
            timeseries=trends, ax=axes[1], colour=colours[count], plot_errors=plot_errors,
            timeseries_for_vertical_adjustment=trend_combined,
            label="Trend: " + trends.user_group)
        plot_cumulative_timeseries_on_axis(
            timeseries=annual, ax=axes[1], colour=colours[count], plot_errors=plot_errors, linestyle="--",
            timeseries_for_vertical_adjustment=trend_combined,
            label="Calibrated annual: " + annual.user_group)

    add_labels_axlines_and_title(
        axes=axes, unit=catalogue_trends.datasets[0].unit,
        title="{} - {}: recalibration with trends".format(region.long_name, data_group.long_name), legend_fontsize=7)

    add_labels_axlines_and_title(
        axes=axes, unit=catalogue_trends.datasets[0].unit, legend_fontsize=7,
        title="{} - {}: recalibration with trends".format(region.long_name, data_group.long_name))
    finalise_save_to_file_and_close_plot(output_filepath)


def plot_recalibrated_result_of_data_group(catalogue_trends: DataCatalogue,
                                           catalogue_calibrated_series: DataCatalogue,
                                           trend_combined: Timeseries,
                                           data_group: GlambieDataGroup,
                                           region: RGIRegion,
                                           output_filepath: str,
                                           plot_errors: bool = True):
    _, axes = plt.subplots(2, 1, figsize=(10, 6))
    colours = get_colours(len(catalogue_trends.datasets))

    # plot non-cumulative
    for count, ds in enumerate(catalogue_calibrated_series.datasets):
        plot_non_cumulative_timeseries_on_axis(
            result_dataframe=ds.data.as_dataframe(), ax=axes[0], colour=colours[count], linestyle="--",
            label="Calibrated annual series: " + ds.user_group + " (" + ds.data_group.name + ")")

    plot_non_cumulative_timeseries_on_axis(
        result_dataframe=trend_combined.data.as_dataframe(), ax=axes[0], colour="black", linestyle="--",
        label="{} - combined solution".format(data_group.long_name))

    # plot cumulative
    for count, timeseries in enumerate(catalogue_calibrated_series.datasets):
        plot_cumulative_timeseries_on_axis(
            timeseries=timeseries, ax=axes[1], colour=colours[count], plot_errors=plot_errors, linestyle="--",
            timeseries_for_vertical_adjustment=trend_combined,
            label="Calibrated annual series: {}".format(timeseries.user_group))

    plot_cumulative_timeseries_on_axis(
        timeseries=trend_combined, ax=axes[1], colour="black", plot_errors=plot_errors, linestyle="--",
        timeseries_for_vertical_adjustment=None,
        label="{} - combined solution".format(data_group.long_name))

    add_labels_axlines_and_title(axes=axes, unit=catalogue_trends.datasets[0].unit, legend_fontsize=7,
                                 title="{} - {}: combined solution".format(region.long_name, data_group.long_name))
    finalise_save_to_file_and_close_plot(output_filepath)


def plot_combination_of_sources_within_region(catalogue_results: DataCatalogue,
                                              combined_timeseries: Timeseries,
                                              region: RGIRegion,
                                              output_filepath: str,
                                              plot_errors: bool = True):

    _, axes = plt.subplots(2, 1, figsize=(10, 6))
    colours = get_colours(len(catalogue_results.datasets))

    # plot non-cumulative
    for count, df in enumerate(catalogue_results.datasets):
        plot_non_cumulative_timeseries_on_axis(
            result_dataframe=df.data.as_dataframe(), ax=axes[0], colour=colours[count],
            label="{}".format(df.data_group.long_name))

    # plot non-cumulative combined solution
    plot_non_cumulative_timeseries_on_axis(result_dataframe=combined_timeseries.data.as_dataframe(),
                                           ax=axes[0], colour="black", linestyle="--", label="Consensus estimate")

    # plot cumulative timeseries
    for count, timeseries in enumerate(catalogue_results.datasets):
        plot_cumulative_timeseries_on_axis(
            timeseries=timeseries, ax=axes[1], colour=colours[count], plot_errors=plot_errors, linestyle="-",
            timeseries_for_vertical_adjustment=combined_timeseries,
            label="{} - combined solution".format(timeseries.data_group.long_name))

    # plot combined solution
    plot_cumulative_timeseries_on_axis(
        timeseries=combined_timeseries, ax=axes[1], colour="black", plot_errors=plot_errors, linestyle="-",
        timeseries_for_vertical_adjustment=None,
        label="Consensus estimate")

    add_labels_axlines_and_title(axes=axes, unit=combined_timeseries.unit,
                                 title="{}: combined estimate".format(region.long_name), legend_fontsize=7)
    finalise_save_to_file_and_close_plot(output_filepath)


def plot_combination_of_regions_to_global(catalogue_region_results: DataCatalogue,
                                          global_timeseries: Timeseries,
                                          region: RGIRegion,
                                          output_filepath: str,
                                          plot_errors: bool = True):

    _, axes = plt.subplots(2, 1, figsize=(10, 6))
    colours = get_colours(len(catalogue_region_results.datasets))

    for count, timeseries in enumerate(catalogue_region_results.datasets):
        plot_non_cumulative_timeseries_on_axis(result_dataframe=timeseries.data.as_dataframe(),
                                               ax=axes[0], colour=colours[count],
                                               label=timeseries.region.long_name)

    # plot combined solution
    plot_non_cumulative_timeseries_on_axis(
        result_dataframe=global_timeseries.data.as_dataframe(), ax=axes[0], colour="black", linestyle="--",
        label="Global estimate")

    # plot cumulative timeseries
    for count, timeseries in enumerate(catalogue_region_results.datasets):
        plot_cumulative_timeseries_on_axis(
            timeseries=timeseries, ax=axes[1], colour=colours[count], plot_errors=plot_errors, linestyle="-",
            timeseries_for_vertical_adjustment=global_timeseries,
            label="{}".format(timeseries.region.long_name))

    # plot combined solution
    plot_cumulative_timeseries_on_axis(
        timeseries=global_timeseries, ax=axes[1], colour="black", plot_errors=plot_errors, linestyle="-",
        timeseries_for_vertical_adjustment=None, label="Global estimate")

    add_labels_axlines_and_title(axes=axes, unit=global_timeseries.unit,
                                 title="{}: combined estimate".format(region.long_name), legend_fontsize=7)
    finalise_save_to_file_and_close_plot(output_filepath)
