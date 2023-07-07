import os
import numpy as np
import pandas as pd
from datetime import datetime
from google.cloud.storage import Client
from dateutil.relativedelta import relativedelta
from glambie.util.timeseries_helpers import interpolate_change_per_day_to_fill_gaps

DATA_TRANSFER_BUCKET_NAME = "glambie-submissions"
PROJECT_NAME = "glambie"
_storage_client = Client()


def download_csvs_from_bucket(local_data_directory_path: str, region_prefix: str = None) -> list[str]:
    """
    Function to download glambie .csv files from the google bucket to a local folder, where they can be checked and
    edited. Specify files for a specific region using the region_prefix parameter

    Parameters
    ----------
    local_data_directory_path : str
        Path to save local copies of bucket data to.
    region_prefix : str, Optional
        String describing the region name pattern to look for in the filenames when deciding which to download,
        by default None.

    Returns
    -------
    list[str]
        List of files that have been downloaded to the local directory.
    """

    list_of_blobs_in_bucket = _storage_client.list_blobs(DATA_TRANSFER_BUCKET_NAME, prefix=region_prefix)
    downloaded_files = []

    for blob in list_of_blobs_in_bucket:
        if '.csv' in blob.name:
            downloaded_files.append(blob.name)
            destination_file_path = os.path.join(local_data_directory_path, blob.name)
            with open(destination_file_path, "wb") as temp_file:
                blob.download_to_file(temp_file, raw_download=False)

    return downloaded_files


def generate_results_dataframe(downloaded_files: list[str], local_path: str) -> pd.DataFrame:
    """
    Function to generate a dataframe sumamrising which of the files need editing, and what edits need to be made for
    these. Thought about doing the edits at the same time, but wanted to retain a record separate to the files
    themselves of what changes have been made.

    Parameters
    ----------
    downloaded_files : list[str]
        List of files that have been downloaded to the local directory.
    local_data_directory_path : str
        Path where local copies of bucket are saved.

    Returns
    -------
    pd.DataFrame
        Dataframe containing results of checks for inconsistencies within the csv files compared to the expected glambie
        standard.
    """

    results_dict = {'local_filepath': downloaded_files, 'file_name': [os.path.basename(a) for a in downloaded_files]}
    results_dataframe = pd.DataFrame.from_dict(results_dict)

    results_dataframe['date_check_satisfied'] = np.nan
    results_dataframe['nodata_check_satisfied'] = np.nan

    for file in downloaded_files:
        file_check_dataframe = check_glambie_submission_for_errors(file, results_dataframe)

    file_check_dataframe.to_csv(os.path.join(local_path, 'record_of_edited_files.csv'))

    return file_check_dataframe


def check_glambie_submission_for_errors(csv_file_path: str, file_check_dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    Function to perform consistency checks on a submitted glambie csv file. Currently performs 2 checks:

    1. check for any non equal end_dates and subsequent start_dates: in some cases we see 1 day gaps between these
    instead of overlapping dates as expected.
    2. check for any instances of extreme values of change - we are aware of instances where people have used
    e.g change = 9999. for rows where they don't have a measured change.

    This function doesn't actually edit any files - instead it returns a record of which files should be edited and
    why - which we want to save to retain full transparency for glambie participants.

    Parameters
    ----------
    csv_file_path : str
        Path to downloaded glambie csv file.
    file_check_dataframe : pd.DataFrame
        Dataframe containing results of checks for inconsistencies within the csv files compared to the expected glambie
        standard.

    Returns
    -------
    pd.DataFrame
        Dataframe containing input dataframe updated with the results of the checks for one file.
    """
    print(os.path.basename(csv_file_path))
    submission_data_frame = pd.read_csv(csv_file_path)

    # First, check for any non equal end_dates and subsequent start_dates
    start_dates = submission_data_frame.start_date.values
    end_dates = submission_data_frame.end_date.values
    start_dates = np.append(start_dates, np.nan)  # Add an extra element to the end of this list for check below

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
    # remove these rows instead of setting an arbitrary nodata value. Extreme value threshold needs to be different
    # depending on the units used.
    change_values = submission_data_frame.glacier_change_observed.values

    if 'm' in submission_data_frame.unit.values[0]:  # check if units are m or mwe
        nodata_check_bool = all(abs(i) < 100 for i in change_values)  # check that all changes in list are < +/-100
    elif 'Gt' in submission_data_frame.unit.values[0]:  # check if units are Gt
        nodata_check_bool = all(abs(i) < 10000 for i in change_values)

    # If all rows passed the date check above, we store date_check_satisfied = True for this file: don't need to edit it
    file_check_dataframe.loc[file_check_dataframe.local_filepath.__eq__(csv_file_path),
                             'date_check_satisfied'] = date_check_bool

    # Likewise if all rows passed the nodata check above, we store nodata_check_satisfied for this file.
    file_check_dataframe.loc[file_check_dataframe.local_filepath.__eq__(csv_file_path),
                             'nodata_check_satisfied'] = nodata_check_bool

    return file_check_dataframe


def edit_local_copies_of_glambie_csvs(file_check_dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    Function to edit the local copies of glambie csvs that didn't pass the checks run by
    check_glambie_submission_for_errors. Save out updated copies to the same local filepath.

    TO DO: there are some cases where date_gaps will contain lots of 1s, and then some e.g. 31, 62 where whole months
    are missing. This is allowed, and we would want to edit these files in the if statement below. Currently they won't
    be edited as not all of the gaps are the same size.

    Parameters
    ----------
    file_check_dataframe : pd.DataFrame
        Dataframe containing results of checks for inconsistencies within the csv files compared to the expected glambie
        standard.
    """
    file_check_dataframe['reason_for_edit'] = ['-' for i in range(len(file_check_dataframe))]

    for _, file in file_check_dataframe.iterrows():
        if not file.date_check_satisfied:
            submission_data_frame = pd.read_csv(file.local_filepath)
            # Check what the gap is between first end and second start date - if it is a uniform gap then we will fix it
            # here. If it varies, we will need to edit file manually
            date_gaps = [datetime.strptime(submission_data_frame.start_date[i + 1], '%d/%m/%Y') - datetime.strptime(
                submission_data_frame.end_date[i], '%d/%m/%Y') for i in range(len(submission_data_frame) - 1)]
            date_gaps_in_days = [a.days for a in date_gaps]

            # 1) Are all gaps 1 day
            if all(i == 1 for i in date_gaps_in_days):
                new_end_dates = [datetime.strptime(a, '%d/%m/%Y') + relativedelta(days=1)
                                 for a in submission_data_frame.end_date]
                submission_data_frame.end_date = [datetime.strftime(a, '%d/%m/%Y') for a in new_end_dates]
                file_check_dataframe.loc[file_check_dataframe.local_filepath.__eq__(file.local_filepath),
                                         'reason_for_edit'] = 'Day gap between end dates and subsequent start dates'

            # 2) Is it a gravimetry file with a GRACE gap?
            else:
                if any(i > 350 for i in date_gaps_in_days) & ('gravimetry' in file.local_filepath):
                    non_grace_gaps = [i for i in date_gaps_in_days if i < 300]
                    # If the GRACE gap is the only gap, we won't edit.
                    if all(i == 0 for i in non_grace_gaps):
                        file_check_dataframe.loc[
                            file_check_dataframe.local_filepath.__eq__(file.local_filepath),
                            'reason_for_edit'] = 'No edits needed for this file, only data gap is due to GRACE missions'

                # 3) Remaining possibility is that it is a gravimetry file with non-GRACE gaps that need interpolating
                elif ('gravimetry' in file.local_filepath):
                    submission_data_frame = interpolate_change_per_day_to_fill_gaps(submission_data_frame)
                    file_check_dataframe.loc[
                        file_check_dataframe.local_filepath.__eq__(file.local_filepath),
                        'reason_for_edit'] = 'Gravimetry file with valid gaps - these have been interpolated'
                else:
                    # If it is not a gravimetry file, then the data it contains is invalid.
                    file_check_dataframe.loc[
                        file_check_dataframe.local_filepath.__eq__(file.local_filepath),
                        'reason_for_edit'] = 'Non-gravimetry file with gaps in data - inspect manually'

                # removing all remaining small day gaps by setting end_date(i) = start_date(i+1)
                updated_end_dates = []
                for i in range(len(submission_data_frame.end_date) - 1):
                    updated_end_dates.append(submission_data_frame.start_date[i + 1])
                updated_end_dates.append(submission_data_frame['end_date'].tolist()[-1])
                submission_data_frame['end_date'] = updated_end_dates

            # Save out to same path as original file
            submission_data_frame.to_csv(file.local_filepath)

        if not file.nodata_check_satisfied:
            submission_data_frame = pd.read_csv(file.local_filepath)

            if 'm' in submission_data_frame.unit.values[0]:
                # delete rows with change values > +/-100 - these numbers need some thought
                submission_data_frame.drop(submission_data_frame[abs(
                    submission_data_frame.glacier_change_observed) > 100].index, inplace=True)
            elif 'Gt' in submission_data_frame.unit.values[0]:
                # delete rows with change values > +/-10000
                submission_data_frame.drop(submission_data_frame[abs(
                    submission_data_frame.glacier_change_observed) > 10000].index, inplace=True)

            submission_data_frame.to_csv(file.local_filepath)
            # Record that the file has been edited
            file_check_dataframe.loc[file_check_dataframe.local_filepath.__eq__(file.local_filepath),
                                     'reason_for_edit'] = 'Random nodata value was used - these rows have been removed'

    return file_check_dataframe


def main():

    local_path = '/path/to/local/folder'
    # If you want to download files for a specific region, set the region_prefix and supply here
    downloaded_files = download_csvs_from_bucket(local_path, region_prefix=None)
    gdf = generate_results_dataframe(downloaded_files, local_path)
    edit_local_copies_of_glambie_csvs(gdf)

    # Final step that needs to be implemented here is to upload the edited files into the bucket, after copying the
    # original version of the file into an archive folder


if __name__ == "__main__":
    main()
