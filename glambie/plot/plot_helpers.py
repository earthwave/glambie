import numpy as np
import pandas as pd
import matplotlib as mpl
from glambie.util.timeseries_helpers import resample_1d_array, timeseries_as_months

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
        cmap = mpl.cm.get_cmap('Spectral', number_of_colours_needed)
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
        if len(row) >= 1:
            adjustment = row.iloc[0].changes
        # else need to upsample reference timeseries to monthly changes
        else:
            monthly_grid = timeseries_as_months(np.array(reference_timeseries.dates))
            changes = resample_1d_array(np.array(reference_timeseries.dates),
                                        np.array(reference_timeseries.changes),
                                        monthly_grid)
            ts_new = pd.DataFrame({"dates": monthly_grid, "changes": changes})
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
