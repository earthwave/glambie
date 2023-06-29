import os
import numpy as np
import pandas as pd
from google.cloud.storage import Client

DATA_TRANSFER_BUCKET_NAME = "glambie-submissions"
PROJECT_NAME = "glambie"
_storage_client = Client()


def download_csvs_from_bucket(file_prefix: str) -> list[str]:
    """
    Function to download glambie .csv files from the google bucket to a local folder, where they can be checked and
    edited. Specify which files using the file_prefix parameter

    TO DO: is there an alternative to 'prefix' that will let me select all .csv files in bucket? If yes, set this
    in function and leave file_prefix as None by default to return all csvs unless otherwise specified.
    TO DO: remove hardcoded home directory path, replace with temporary directory?

    Parameters
    ----------
    file_prefix : str
        String describing the pattern to look for in the filenames when deciding which to download.

    Returns
    -------
    list[str]
        List of files that have been downloaded to the local directory.
    """

    list_of_blobs_in_bucket = _storage_client.list_blobs(DATA_TRANSFER_BUCKET_NAME, prefix=file_prefix)
    downloaded_files = []

    for blob in list_of_blobs_in_bucket:
        downloaded_files.append(blob.name)
        destination_file_path = os.path.join('/home/dubbersophie/glambie_data', blob.name)
        with open(destination_file_path, "wb") as temp_file:
            blob.download_to_file(temp_file, raw_download=False)

    return downloaded_files


def generate_results_dataframe(downloaded_files: list[str]) -> pd.DataFrame:
    """
    Function to generate a dataframe sumamrising which of the files need editing, and what edits need to be made for
    these. Thought about doing the edits at the same time, but wanted to retain a record separate to the files
    themselves of what changes have been made.

    TO DO: Write the dataframe to a .csv - store in repo?

    Parameters
    ----------
    downloaded_files : list[str]
        List of files that have been downloaded to the local directory.

    Returns
    -------
    pd.DataFrame
        Dataframe containing results of checks for inconsistencies within the csv files compared to the expected glambie
        standard.
    """

    results_dict = {'files': [os.path.basename(file) for file in downloaded_files]}
    results_dataframe = pd.DataFrame.from_dict(results_dict)

    results_dataframe['date_check_satisfied'] = np.nan
    results_dataframe['nodata_check_satisfied'] = np.nan

    for file in downloaded_files:
        results_dataframe = check_glambie_submission_for_errors(file, results_dataframe)

    return results_dataframe


def check_glambie_submission_for_errors(csv_file_path: str, results_dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    Function to perform consistency checks on a submitted glambie csv file. Currently performs 2 checks:

    1. check for any non equal end_dates and subsequent start_dates: in some cases we see 1 day gaps between these
    instead of overlapping dates as expected.
    2. check for any instances of extreme values of change - we are aware of instances where people have used
    e.g change = 9999. for rows where they don't have a measured change.

    TO DO: implement no data check

    Parameters
    ----------
    csv_file_path : str
        Path to downloaded glambie csv file.
    results_dataframe : pd.DataFrame
        Dataframe containing results of checks for inconsistencies within the csv files compared to the expected glambie
        standard.

    Returns
    -------
    pd.DataFrame
        Dataframe containing input dataframe updated with the results of the checks for one file.
    """

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

    return results_dataframe
