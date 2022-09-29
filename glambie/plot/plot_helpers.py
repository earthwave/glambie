import numpy as np

"""
Handy functions to help making plots
"""


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
