import os
import numpy as np
import pandas as pd
from google.cloud.storage import Client

DATA_TRANSFER_BUCKET_NAME = "glambie-submissions"
PROJECT_NAME = "glambie"
_storage_client = Client()


def download_csvs_from_bucket(file_prefix: str) -> list[str]:

    list_of_blobs_in_bucket = _storage_client.list_blobs(DATA_TRANSFER_BUCKET_NAME, prefix=file_prefix)
    downloaded_files = []

    for blob in list_of_blobs_in_bucket:
        downloaded_files.append(blob.name)
        destination_file_path = os.path.join('/home/dubbersophie/glambie_data', blob.name)
        with open(destination_file_path, "wb") as temp_file:
            blob.download_to_file(temp_file, raw_download=False)

    return downloaded_files


def build_results_dataframe(downloaded_files: list[str]) -> pd.DataFrame:

    results_dict = {'files': [os.path.basename(file) for file in downloaded_files]}
    results_dataframe = pd.DataFrame.from_dict(results_dict)

    results_dataframe['date_check_satisfied'] = np.nan
    results_dataframe['nodata_check_satisfied'] = np.nan

    return results_dataframe


def check_glambie_submission_for_errors(csv_file_path: str, results_dataframe: pd.DataFrame):

    submission_data_frame = pd.read_csv(csv_file_path)

    # First, check for any non equal end_dates and subsequent start_dates
    start_dates = submission_data_frame.start_date.values
    end_dates = submission_data_frame.end_date.values
    start_dates.append(np.nan)  # Add an extra element to the end of this list for check below

    date_check_bool = True
    nodata_check_bool = True

    for ind, end_date in enumerate(end_dates):
        # If end_date != start_date for any of the consecutive rows, set date_check_bool to False for this file - i.e.
        # file does not pass test and will need to be edited
        row_bool = end_date.__eq__(start_dates[ind + 1])
        if not row_bool:
            date_check_bool = False

        # Next, check for any instances of extreme values of change - we are aware of instances where people have used
        # e.g change = 9999. for rows where they don't have a measured change. They were unaware that they should just
        # remove these rows instead of setting an arbitrary nodata value.

    # If all rows passed the date check above, we store date_check_satisfied = True for this file: don't need to edit it
    results_dataframe.loc[results_dataframe.files.__eq__(os.path.basename(csv_file_path)),
                          'date_check_satisfied'] = date_check_bool

    # Likewise if all rows passed the nodata check above, we store nodata_check_satisfied for this file.
    results_dataframe.loc[results_dataframe.files.__eq__(os.path.basename(csv_file_path)),
                          'nodata_check_satisfied'] = nodata_check_bool
