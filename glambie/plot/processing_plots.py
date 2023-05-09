
import matplotlib.pyplot as plt
import numpy as np
from glambie.data.data_catalogue import DataCatalogue
from glambie.const.data_groups import GlambieDataGroup
from glambie.const.regions import RGIRegion


COLOURS = ["red", "blue", "gold", "green", "orange", "teal", "pink", "purple"]


def plot_homogenized_input_data(catalogue_annual: DataCatalogue,
                                data_group: GlambieDataGroup,
                                region: RGIRegion,
                                output_filepath: str):
    _, ax = plt.subplots(2, 1, figsize=(6, 5), sharex=True)

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
    ax[0].set_ylabel("Change change [{}]".format(catalogue_annual.datasets[0].unit))
    count = 0
    for _, ds in enumerate(catalogue_annual.datasets):
        df_trend_cum = ds.data.as_cumulative_timeseries()
        df_trend_cum["changes"] = df_trend_cum["changes"] - \
            df_trend_cum[df_trend_cum["dates"] == 2012]["changes"].iloc[0]
        ax[1].plot(df_trend_cum["dates"], df_trend_cum["changes"],
                   label="Dataset: " + ds.user_group, color=COLOURS[count])
        count = count + 1
    ax[1].axhline(0, color='grey', linewidth=0.9, linestyle="--")
    ax[1].legend()
    ax[1].set_xlabel("Time")
    ax[1].set_ylabel("Cumulative change [{}]".format(catalogue_annual.datasets[0].unit))
    ax[0].set_title("{} - {}: homogenized input data".format(region.name, data_group.long_name))
    plt.tight_layout()
    plt.savefig(output_filepath)
