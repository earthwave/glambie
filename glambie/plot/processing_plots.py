
import matplotlib.pyplot as plt
import numpy as np
from glambie.data.data_catalogue import DataCatalogue
from glambie.data.timeseries import Timeseries
from glambie.const.data_groups import GlambieDataGroup
from glambie.const.regions import RGIRegion
from glambie.processing.path_handling import OutputPathHandler
from glambie.processing.processing_helpers import convert_datasets_to_monthly_grid
from glambie.processing.processing_helpers import convert_datasets_to_unit_mwe
from glambie.plot.plot_helpers import apply_vertical_adjustment_for_cumulative_plot


COLOURS = ["red", "blue", "gold", "green", "orange", "teal", "pink", "purple"]


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
                                      output_filepath=plot_fp)
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
                                                      output_filepath=plot_fp)
    plot_fp = output_path_handler.get_plot_output_file_path(region=region, data_group=data_group,
                                                            plot_file_name="3_annual_homogenize_data.png")
    plot_homogenized_input_data_of_data_group(catalogue_annual=data_catalogue_annual_homogenized,
                                              trend_combined=timeseries_trend_combined,
                                              data_group=data_group,
                                              region=region,
                                              output_filepath=plot_fp)
    plot_fp = output_path_handler.get_plot_output_file_path(region=region, data_group=data_group,
                                                            plot_file_name="4_annual_variability.png")
    plot_annual_variability_of_data_group(catalogue_annual_anomalies=data_catalogue_annual_anomalies,
                                          timeseries_combined_annual=timeseries_annual_combined,
                                          data_group=data_group,
                                          region=region,
                                          output_filepath=plot_fp)
    plot_fp = output_path_handler.get_plot_output_file_path(region=region, data_group=data_group,
                                                            plot_file_name="5_trends_input_data.png")
    plot_raw_input_data_of_data_group(catalogue_raw=data_catalogue_trends_raw,
                                      trend_combined=timeseries_trend_combined,
                                      data_group=data_group,
                                      region=region,
                                      category="trends",
                                      output_filepath=plot_fp)
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
                                                      output_filepath=plot_fp)
    plot_fp = output_path_handler.get_plot_output_file_path(region=region, data_group=data_group,
                                                            plot_file_name="7_trends_recalibration.png")
    plot_recalibration_of_annual_variability_with_trends(catalogue_trends=data_catalogue_trends_homogenized,
                                                         catalogue_calibrated_series=data_catalogue_calibrated_series,
                                                         trend_combined=timeseries_trend_combined,
                                                         data_group=data_group,
                                                         region=region,
                                                         output_filepath=plot_fp)
    plot_fp = output_path_handler.get_plot_output_file_path(region=region, data_group=data_group,
                                                            plot_file_name="8_combined_result.png")
    plot_recalibrated_result_of_data_group(catalogue_trends=data_catalogue_trends_homogenized,
                                           catalogue_calibrated_series=data_catalogue_calibrated_series,
                                           trend_combined=timeseries_trend_combined,
                                           data_group=data_group,
                                           region=region,
                                           output_filepath=plot_fp)


def plot_raw_input_data_of_data_group(catalogue_raw: DataCatalogue,
                                      trend_combined: DataCatalogue,
                                      data_group: GlambieDataGroup,
                                      region: RGIRegion,
                                      category: str,
                                      output_filepath: str):
    _, ax = plt.subplots(2, 1, figsize=(7, 6))

    count = 0
    for _, ds in enumerate(catalogue_raw.datasets):
        for _, row in ds.data.as_dataframe().iterrows():
            time_period = row["end_dates"] - row["start_dates"]
            ax[0].plot([row["start_dates"], row["end_dates"]], [np.array(row["changes"]) / time_period,
                                                                np.array(row["changes"]) / time_period],
                       color=COLOURS[count])
        ax[0].plot([], [], label="Dataset: " + ds.user_group, color=COLOURS[count])
        count = count + 1
    ax[0].axhline(0, color='grey', linewidth=0.9, linestyle="--")
    ax[0].set_ylabel("Change [{} per year]".format(catalogue_raw.datasets[0].unit))

    count = 0
    for _, ds in enumerate(catalogue_raw.datasets):
        df_trend_cum = ds.data.as_cumulative_timeseries()
        vertical_shift_ref_timeseries = trend_combined.data.as_cumulative_timeseries()
        df_trend_cum["changes"] = apply_vertical_adjustment_for_cumulative_plot(df_trend_cum,
                                                                                vertical_shift_ref_timeseries).changes
        ax[1].plot(df_trend_cum["dates"], df_trend_cum["changes"],
                   label="Dataset: " + ds.user_group, color=COLOURS[count])
        count = count + 1
    ax[1].axhline(0, color='grey', linewidth=0.9, linestyle="--")
    ax[1].legend(prop={'size': 7})
    ax[1].set_xlabel("Time")
    ax[1].set_ylabel("Cumulative change [{}]".format(catalogue_raw.datasets[0].unit))
    ax[0].set_title("{} - {} - {}: raw input data".format(region.long_name, data_group.long_name, category))
    plt.tight_layout()
    plt.savefig(output_filepath)
    plt.close()


def plot_raw_and_homogenized_input_data_of_data_group(catalogue_raw: DataCatalogue,
                                                      catalogue_homogenized: DataCatalogue,
                                                      trend_combined: DataCatalogue,
                                                      data_group: GlambieDataGroup,
                                                      region: RGIRegion,
                                                      category: str,
                                                      output_filepath: str):
    _, ax = plt.subplots(2, 1, figsize=(7, 6))

    count = 0
    for _, ds in enumerate(catalogue_raw.datasets):
        for _, row in ds.data.as_dataframe().iterrows():
            time_period = row["end_dates"] - row["start_dates"]
            ax[0].plot([row["start_dates"], row["end_dates"]], [np.array(row["changes"]) / time_period,
                                                                np.array(row["changes"]) / time_period],
                       color=COLOURS[count])
        ax[0].plot([], [], label="Dataset (raw): " + ds.user_group, color=COLOURS[count])
        count = count + 1
    count = 0
    for _, ds in enumerate(catalogue_homogenized.datasets):
        for _, row in ds.data.as_dataframe().iterrows():
            time_period = row["end_dates"] - row["start_dates"]
            ax[0].plot([row["start_dates"], row["end_dates"]], [np.array(row["changes"]) / time_period,
                                                                np.array(row["changes"]) / time_period],
                       color=COLOURS[count], linestyle="--")
        ax[0].plot([], [], label="Dataset: " + ds.user_group, color=COLOURS[count], linestyle="--")
        count = count + 1
    ax[0].axhline(0, color='grey', linewidth=0.9, linestyle="--")
    ax[0].set_ylabel("Change [{} per year]".format(catalogue_raw.datasets[0].unit))
    count = 0
    for _, ds in enumerate(catalogue_raw.datasets):
        df_trend_cum = ds.data.as_cumulative_timeseries()
        vertical_shift_ref_timeseries = trend_combined.data.as_cumulative_timeseries()
        df_trend_cum["changes"] = apply_vertical_adjustment_for_cumulative_plot(df_trend_cum,
                                                                                vertical_shift_ref_timeseries).changes
        ax[1].plot(df_trend_cum["dates"], df_trend_cum["changes"],
                   label="Dataset (raw): " + ds.user_group, color=COLOURS[count])
        count = count + 1
    count = 0
    for _, ds in enumerate(catalogue_homogenized.datasets):
        df_trend_cum = ds.data.as_cumulative_timeseries()
        vertical_shift_ref_timeseries = trend_combined.data.as_cumulative_timeseries()
        df_trend_cum["changes"] = apply_vertical_adjustment_for_cumulative_plot(df_trend_cum,
                                                                                vertical_shift_ref_timeseries).changes
        ax[1].plot(df_trend_cum["dates"], df_trend_cum["changes"],
                   label="Dataset: " + ds.user_group, color=COLOURS[count], linestyle="--")
        count = count + 1
    ax[1].axhline(0, color='grey', linewidth=0.9, linestyle="--")
    ax[1].legend(prop={'size': 7})
    ax[1].set_xlabel("Time")
    ax[1].set_ylabel("Cumulative change [{}]".format(catalogue_raw.datasets[0].unit))
    ax[0].set_title("{} - {} - {}: raw input data".format(region.long_name, data_group.long_name, category))
    plt.tight_layout()
    plt.savefig(output_filepath)
    plt.close()


def plot_homogenized_input_data_of_data_group(catalogue_annual: DataCatalogue,
                                              trend_combined: DataCatalogue,
                                              data_group: GlambieDataGroup,
                                              region: RGIRegion,
                                              output_filepath: str):
    _, ax = plt.subplots(2, 1, figsize=(7, 6))

    count = 0
    for _, ds in enumerate(catalogue_annual.datasets):
        for _, row in ds.data.as_dataframe().iterrows():
            time_period = row["end_dates"] - row["start_dates"]
            ax[0].plot([row["start_dates"], row["end_dates"]], [np.array(row["changes"]) / time_period,
                                                                np.array(row["changes"]) / time_period],
                       color=COLOURS[count])
        ax[0].plot([], [], label="Dataset: " + ds.user_group, color=COLOURS[count])
        count = count + 1
    ax[0].axhline(0, color='grey', linewidth=0.9, linestyle="--")
    ax[0].set_ylabel("Change [{} per year]".format(catalogue_annual.datasets[0].unit))
    count = 0
    for _, ds in enumerate(catalogue_annual.datasets):
        df_trend_cum = ds.data.as_cumulative_timeseries()
        vertical_shift_ref_timeseries = trend_combined.data.as_cumulative_timeseries()
        df_trend_cum["changes"] = apply_vertical_adjustment_for_cumulative_plot(df_trend_cum,
                                                                                vertical_shift_ref_timeseries).changes
        ax[1].plot(df_trend_cum["dates"], df_trend_cum["changes"],
                   label="Dataset: " + ds.user_group, color=COLOURS[count])
        count = count + 1
    ax[1].axhline(0, color='grey', linewidth=0.9, linestyle="--")
    ax[1].legend(prop={'size': 7})
    ax[1].set_xlabel("Time")
    ax[1].set_ylabel("Cumulative change [{}]".format(catalogue_annual.datasets[0].unit))
    ax[0].set_title("{} - {}: homogenized input data".format(region.long_name, data_group.long_name))
    plt.tight_layout()
    plt.savefig(output_filepath)


def plot_annual_variability_of_data_group(catalogue_annual_anomalies: DataCatalogue,
                                          timeseries_combined_annual: Timeseries,
                                          data_group: GlambieDataGroup,
                                          region: RGIRegion,
                                          output_filepath: str):
    _, ax = plt.subplots(2, 1, figsize=(7, 6))
    count = 0
    for _, ds in enumerate(catalogue_annual_anomalies.datasets):
        for _, row in ds.data.as_dataframe().iterrows():
            time_period = row["end_dates"] - row["start_dates"]
            ax[0].plot([row["start_dates"], row["end_dates"]], [np.array(row["changes"]) / time_period,
                                                                np.array(row["changes"]) / time_period],
                       color=COLOURS[count])
        ax[0].plot([], [], label="Dataset: " + ds.user_group, color=COLOURS[count])
        count = count + 1

    for _, row in timeseries_combined_annual.data.as_dataframe().iterrows():
        time_period = row["end_dates"] - row["start_dates"]
        ax[0].plot([row["start_dates"], row["end_dates"]], [np.array(row["changes"]) / time_period,
                   np.array(row["changes"]) / time_period], color="black", linestyle="--")
    ax[0].plot([], [], label="{} - combined solution".format(data_group.long_name), color="black", linestyle="--")
    ax[0].axhline(0, color='grey', linewidth=0.9, linestyle="--")
    ax[0].legend(prop={'size': 7})
    ax[0].set_xlabel("Time")
    ax[0].set_ylabel("Change [{} per year]".format(catalogue_annual_anomalies.datasets[0].unit))
    count = 0
    df_combined_cum = timeseries_combined_annual.data.as_cumulative_timeseries()
    for _, ds in enumerate(catalogue_annual_anomalies.datasets):
        df_trend_cum = ds.data.as_cumulative_timeseries()
        vertical_shift_ref_timeseries = timeseries_combined_annual.data.as_cumulative_timeseries()
        df_trend_cum["changes"] = apply_vertical_adjustment_for_cumulative_plot(df_trend_cum,
                                                                                vertical_shift_ref_timeseries).changes
        ax[1].plot(df_trend_cum["dates"], df_trend_cum["changes"],
                   label="Dataset: " + ds.user_group, color=COLOURS[count])
        count = count + 1
    ax[1].plot(df_combined_cum["dates"], df_combined_cum["changes"],
               label="{} - combined solution".format(data_group.long_name), color="black", linestyle="--")
    ax[1].axhline(0, color='grey', linewidth=0.9, linestyle="--")
    ax[1].set_xlabel("Time")
    ax[1].set_ylabel("Cumulative change [{}]".format(catalogue_annual_anomalies.datasets[0].unit))
    ax[0].set_title("{} - {}: annual variability".format(region.long_name, data_group.long_name))
    plt.tight_layout()
    plt.savefig(output_filepath)
    plt.close()


def plot_recalibration_of_annual_variability_with_trends(catalogue_trends: DataCatalogue,
                                                         catalogue_calibrated_series: DataCatalogue,
                                                         trend_combined: DataCatalogue,
                                                         data_group: GlambieDataGroup,
                                                         region: RGIRegion,
                                                         output_filepath: str):
    _, ax = plt.subplots(2, 1, figsize=(7, 6))
    count = 0
    for idx, ds in enumerate(catalogue_trends.datasets):
        for _, row in ds.data.as_dataframe().iterrows():
            time_period = row["end_dates"] - row["start_dates"]
            ax[0].plot([row["start_dates"], row["end_dates"]], [np.array(row["changes"]) / time_period,
                                                                np.array(row["changes"]) / time_period],
                       color=COLOURS[count])
        ax[0].plot([], [], label="Trend: " + ds.user_group, color=COLOURS[count])

        ds = catalogue_calibrated_series.datasets[idx]
        for _, row in ds.data.as_dataframe().iterrows():
            time_period = row["end_dates"] - row["start_dates"]
            ax[0].plot([row["start_dates"], row["end_dates"]], [np.array(row["changes"]) / time_period,
                       np.array(row["changes"]) / time_period], color=COLOURS[count], linestyle="--")
        ax[0].plot([], [], label="Calibrated annual: " + ds.user_group, color=COLOURS[count], linestyle="--")
        count = count + 1

    ax[0].axhline(0, color='grey', linewidth=0.9, linestyle="--")
    ax[0].set_ylabel("Change [{} per year]".format(catalogue_trends.datasets[0].unit))

    count = 0
    for idx, ds in enumerate(catalogue_trends.datasets):
        df_trend_cum_cali = catalogue_calibrated_series.datasets[idx].data.as_cumulative_timeseries()

        df_trend_cum = ds.data.as_cumulative_timeseries()
        vertical_shift_ref_timeseries = trend_combined.data.as_cumulative_timeseries()
        df_trend_cum["changes"] = apply_vertical_adjustment_for_cumulative_plot(df_trend_cum,
                                                                                vertical_shift_ref_timeseries).changes
        ax[1].plot(df_trend_cum["dates"], df_trend_cum["changes"],
                   label="Trend: " + ds.user_group, color=COLOURS[count])
        # plot calibrated series
        df_trend_cum = df_trend_cum_cali
        vertical_shift_ref_timeseries = trend_combined.data.as_cumulative_timeseries()
        df_trend_cum["changes"] = apply_vertical_adjustment_for_cumulative_plot(df_trend_cum,
                                                                                vertical_shift_ref_timeseries).changes
        ax[1].plot(df_trend_cum["dates"], df_trend_cum["changes"], label="Calibrated annual: "
                   + ds.user_group, color=COLOURS[count], linestyle="--")
        count = count + 1

    ax[1].axhline(0, color='grey', linewidth=0.9, linestyle="--")
    ax[1].legend(prop={'size': 7})
    ax[1].set_xlabel("Time")
    ax[1].set_ylabel("Cumulative change [{}]".format(catalogue_trends.datasets[0].unit))
    ax[0].set_title("{} - {}: recalibration with trends".format(region.long_name,
                                                                data_group.long_name))
    plt.tight_layout()
    plt.savefig(output_filepath)
    plt.close()


def plot_recalibrated_result_of_data_group(catalogue_trends: DataCatalogue,
                                           catalogue_calibrated_series: DataCatalogue,
                                           trend_combined: Timeseries,
                                           data_group: GlambieDataGroup,
                                           region: RGIRegion,
                                           output_filepath: str):
    _, ax = plt.subplots(2, 1, figsize=(7, 6))
    count = 0
    for idx, ds in enumerate(catalogue_trends.datasets):
        ds = catalogue_calibrated_series.datasets[idx]
        for _, row in ds.data.as_dataframe().iterrows():
            time_period = row["end_dates"] - row["start_dates"]
            ax[0].plot([row["start_dates"], row["end_dates"]], [np.array(row["changes"]) / time_period,
                       np.array(row["changes"]) / time_period], color=COLOURS[count], linestyle="--")
        ax[0].plot([], [], label="Calibrated annual series: " + ds.user_group
                   + " (" + ds.data_group.name + ")", color=COLOURS[count], linestyle="--")
        count = count + 1
    for _, row in trend_combined.data.as_dataframe().iterrows():
        time_period = row["end_dates"] - row["start_dates"]
        ax[0].plot([row["start_dates"], row["end_dates"]], [np.array(row["changes"]) / time_period,
                   np.array(row["changes"]) / time_period], color="black", linestyle="--")
    ax[0].plot([], [], label="{} - combined solution".format(data_group.long_name), color="black", linestyle="--")

    ax[0].axhline(0, color='grey', linewidth=0.9, linestyle="--")
    ax[0].set_xlabel("Time")
    ax[0].set_ylabel("Change [m w.e. per year]")

    count = 0
    df_combined_cum_trend = trend_combined.data.as_cumulative_timeseries()
    for idx, ds in enumerate(catalogue_trends.datasets):
        ds = catalogue_calibrated_series.datasets[idx]
        df_trend_cum = ds.data.as_cumulative_timeseries()
        vertical_shift_ref_timeseries = trend_combined.data.as_cumulative_timeseries()
        df_trend_cum["changes"] = apply_vertical_adjustment_for_cumulative_plot(df_trend_cum,
                                                                                vertical_shift_ref_timeseries).changes
        ax[1].plot(df_trend_cum["dates"], df_trend_cum["changes"],
                   label="Calibrated annual series: {}".format(ds.user_group), color=COLOURS[count], linestyle="--")
        count = count + 1
    ax[1].plot(df_combined_cum_trend["dates"], df_combined_cum_trend["changes"],
               label="{} - combined solution".format(data_group.long_name), color="black", linestyle="--")

    ax[1].axhline(0, color='grey', linewidth=0.9, linestyle="--")
    ax[1].legend(prop={'size': 7})
    ax[1].set_xlabel("Time")
    ax[1].set_ylabel("Cumulative change [{}]".format(catalogue_trends.datasets[0].unit))
    ax[0].set_title("{} - {}: combined solution".format(region.long_name,
                                                        data_group.long_name))
    plt.tight_layout()
    plt.savefig(output_filepath)
    plt.close()
