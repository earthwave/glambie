import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from glambie.util.timeseries_helpers import resample_1d_array, timeseries_as_months
from glambie.data.timeseries import Timeseries

"""
Handy functions to help making plots
"""

COLOURS = ["red", "blue", "gold", "green", "orange", "teal", "pink", "purple"]


def get_colours(number_of_colours: int) -> list[str]:
    """
    Calculates and returns a list of colours for matplotlib using 'COLOURS'
    If more colours needed they are generated from the Spectral colour map.

    Parameters
    ----------
    number_of_colours : int
        number of colours needed

    Returns
    -------
    list[str]
        list with names and hex codes of colours
    """
    if number_of_colours > len(COLOURS):
        number_of_colours_needed = number_of_colours - len(COLOURS)
        cmap = mpl.pyplot.get_cmap('Spectral', number_of_colours_needed)
        colour_list_hex = [mpl.colors.rgb2hex(cmap(i)) for i in range(number_of_colours_needed)]
        return [*COLOURS, *colour_list_hex]
    else:
        return COLOURS[:number_of_colours]


def autoscale_y_axis(ax, margin=0.1):
    """
    This function rescales the y-axis based on the data that is visible given the current xlim of the axis.
    Can be used after changing x-axis to rescale y-axis

    Parameters
    ----------
    ax : matplitlib.axes.axes
        a matplotlib axes object
    margin : float, optional
        the fraction of the total height of the y-data to pad the upper and lower ylims, by default 0.1
    """

    def get_bottom_top(line):
        xd = line.get_xdata()
        yd = line.get_ydata()
        lo, hi = ax.get_xlim()
        y_displayed = yd[((xd > lo) & (xd < hi))]
        h = np.max(y_displayed) - np.min(y_displayed)
        bot = np.min(y_displayed) - margin * h
        top = np.max(y_displayed) + margin * h
        return bot, top

    lines = ax.get_lines()
    bot, top = np.inf, -np.inf

    for line in lines:
        new_bot, new_top = get_bottom_top(line)
        if new_bot < bot:
            bot = new_bot
        if new_top > top:
            top = new_top

    ax.set_ylim(bot, top)


def apply_vertical_adjustment_for_cumulative_plot(timeseries_to_adjust: pd.DataFrame,
                                                  reference_timeseries: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates vertical adjustment for plotting a cumulative series,
    basing the start of a timeseries on a reference dataset

    Parameters
    ----------
    timeseries_to_adjust : pd.DataFrame
        DataFrame of the timeseries that should be vertically adjusted
    reference_timeseries : pd.DataFrame
        DataFrame of a reference timeseries for calculating vertical adjustment with cumulative timeseries

    Returns
    -------
    pd.DataFrame
        vertical adjusted cumulative timeseries
    """
    adjustment = None
    # get adjustment date onto monthly grid
    adjustment_date = timeseries_as_months([timeseries_to_adjust.dates.iloc[0]])[0]

    if (adjustment_date >= min(reference_timeseries.dates)) and (adjustment_date <= max(reference_timeseries.dates)):
        # this means we adjust the first date of the adjustment series to the change of the reference series
        # at the corresponding date

        # read adjustment at specific date
        row = reference_timeseries[reference_timeseries.dates == adjustment_date]
        if len(row) == 1:
            adjustment = row.iloc[0].changes
        # else need to upsample reference timeseries to monthly changes
        else:
            monthly_grid = timeseries_as_months(np.array(reference_timeseries.dates))
            changes = resample_1d_array(np.array(reference_timeseries.dates),
                                        np.array(reference_timeseries.changes),
                                        monthly_grid)
            ts_new = pd.DataFrame({"dates": monthly_grid, "changes": changes})
            # handle Nan values, e.g. when there is a gap in the timeseries
            ts_new = ts_new.fillna(method="bfill")
            adjustment = ts_new[ts_new.dates == adjustment_date].iloc[0].changes
    else:
        # this means we adjust the adjustment series at the first date of the reference series
        adjustment_date = timeseries_as_months([reference_timeseries.dates.iloc[0]])[0]

        # read adjustment at specific date
        row = timeseries_to_adjust[timeseries_to_adjust.dates == adjustment_date]
        if len(row) >= 1:
            adjustment = - row.iloc[0].changes
        # else need to upsample reference timeseries to monthly changes
        else:
            monthly_grid = timeseries_as_months(np.array(timeseries_to_adjust.dates))
            changes = resample_1d_array(np.array(timeseries_to_adjust.dates),
                                        np.array(timeseries_to_adjust.changes),
                                        monthly_grid)
            ts_new = pd.DataFrame({"dates": monthly_grid, "changes": changes})
            adjustment = - ts_new[ts_new.dates == adjustment_date].iloc[0].changes

    adjusted_timeseries = timeseries_to_adjust.copy()
    adjusted_timeseries.changes = adjusted_timeseries.changes + adjustment

    return adjusted_timeseries


def plot_non_cumulative_timeseries_on_axis(result_dataframe: pd.DataFrame,
                                           ax: mpl.pyplot.axis,
                                           colour: str,
                                           label: str = "",
                                           linestyle: str = "-",
                                           plot_errors: bool = True):
    """
    Plots a non-cumulative dataframe on a given axis

    Parameters
    ----------
    result_dataframe : pd.DataFrame
        Dataframe to be plotted
    ax : mpl.pyplot.axis
        matplotlib axis to be plotted on
    colour : str
        hex colour for plot
    label : str, optional
        label of dataset, by default ""
    linestyle : str, optional
        plot linestyle, by default "-" (solid)
    plot_errors : bool, optional
        if true, uncertainty bounds are plotted, by default True
    """
    for _, row in result_dataframe.iterrows():  # iterate over each row of the timeseries
        time_period = row["end_dates"] - row["start_dates"]
        changes_per_year = np.array(row["changes"]) / time_period
        ax.plot([row["start_dates"], row["end_dates"]], [changes_per_year, changes_per_year],
                color=colour, linestyle=linestyle)
        if plot_errors:
            ax.fill_between([row["start_dates"], row["end_dates"]],
                            [changes_per_year, changes_per_year] + np.array(row["errors"]) / time_period,
                            [changes_per_year, changes_per_year] - np.array(row["errors"]) / time_period,
                            alpha=0.15, color=colour)
    # plot label
    ax.plot([], [], label=label, color=colour)


def plot_cumulative_timeseries_on_axis(timeseries: Timeseries,
                                       ax: mpl.pyplot.axis,
                                       colour: str,
                                       timeseries_for_vertical_adjustment: Timeseries = None,
                                       label: str = "",
                                       linestyle: str = "-",
                                       plot_errors: bool = True):
    """
    Plots a Timeseries as cumulative timeseries on a given axis

    Parameters
    ----------
    timeseries : Timeseries
        Timeseries object to be plotted
    ax : mpl.pyplot.axis
        matplotlib axis to be plotted on
    colour : str
        hex colour for plot
    timeseries_for_vertical_adjustment : Timeseries, optional
        timeseries to do a vertical adjustment with, by default None
    label : str, optional
        label of dataset, by default ""
    linestyle : str, optional
        plot linestyle, by default "-" (solid)
    plot_errors : bool, optional
        if true, uncertainty bounds are plotted, by default True
    """
    df_cum_trend = timeseries.data.as_cumulative_timeseries()
    if timeseries_for_vertical_adjustment is not None:
        df_combined_cum_trend = timeseries_for_vertical_adjustment.data.as_cumulative_timeseries()
        df_cum_trend["changes"] = apply_vertical_adjustment_for_cumulative_plot(df_cum_trend,
                                                                                df_combined_cum_trend).changes
    ax.plot(df_cum_trend["dates"], df_cum_trend["changes"], label=label, color=colour, linestyle=linestyle)
    if plot_errors:
        ax.fill_between(df_cum_trend["dates"], df_cum_trend["changes"] + df_cum_trend["errors"],
                        df_cum_trend["changes"] - df_cum_trend["errors"], alpha=0.15, color=colour)


def finalise_save_to_file_and_close_plot(output_filepath: str):
    """
    Applies tight_layout, saves figure and closes figure.

    Parameters
    ----------
    output_filepath : str
        absolute path for output plot
    """
    plt.tight_layout()
    plt.savefig(output_filepath)
    plt.close()


def add_labels_axlines_and_title(axes: mpl.pyplot.axes,
                                 unit: str,
                                 title: str,
                                 legend_fontsize: int = 9,
                                 legend_outside_plot: bool = True):
    """
    Extend plot with labels, legend etc.:
    - Adds labels to axes with units
    - Adds title
    - Adds legend
    - Adds a horizontal axhline at 0

    Parameters
    ----------
    axes : mpl.pyplot.axes
        axes object with two axis, axes[0] shows non-cumulative timeseries, axes[1] shows the cumulative timeseries
    unit : str
        unit for label description, e.g. 'Gt'
    title : str
        plot title
    legend_fontsize : int, optional
        legend font size, by default 9
    legend_outside_plot : bool, optional
        if True the legend is plotted outside the plot. good for when there are many datasets in on plot
        by default True
    """
    axes[0].set_title(title)
    axes[0].axhline(0, color="grey", linewidth=0.9, linestyle="--")
    axes[0].set_xlabel("Time")
    axes[0].set_ylabel("Change [{} per year]".format(unit))
    axes[1].axhline(0, color="grey", linewidth=0.9, linestyle="--")
    if legend_outside_plot:
        axes[1].legend(bbox_to_anchor=(1.04, 1), borderaxespad=0, fontsize=legend_fontsize)
    else:
        axes[1].legend(fontsize=legend_fontsize)
    axes[1].set_xlabel("Time")
    axes[1].set_ylabel("Cumulative change [{}]".format(unit))
