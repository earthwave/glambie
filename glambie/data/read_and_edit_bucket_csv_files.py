import os
import numpy as np
import pandas as pd
from datetime import datetime
from google.cloud.storage import Client
from glambie.util.timeseries_helpers import interpolate_change_per_day_to_fill_gaps
from glambie.util.date_helpers import datetime_dates_to_fractional_years

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


def upload_edited_files_to_bucket(file_dataframe: pd.DataFrame, local_path: str):
    """
    After editing local copies of the submitted csv files, replace the original versions in the bucket with the
    edited local versions. Also upload an archvie folder containing original copies of all edited files

    Parameters
    ----------
    file_dataframe : pd.DataFrame
        Dataframe containing results of checks for inconsistencies within the csv files compared to the expected glambie
        standard.
    local_path : str
        Path to local copies of bucket data.

    Raises
    ------
    AssertionError
        If archive folder has not yet been created
    """

    for _, file in file_dataframe.iterrows():
        file_to_upload = file.local_filepath

        bucket = _storage_client.get_bucket(DATA_TRANSFER_BUCKET_NAME)
        blob = bucket.blob(file.file_name)
        blob.upload_from_filename(file_to_upload)
        print('Edited version of {} uploaded to bucket'.format(file.file_name))

    # Finally upload archive of unedited files
    archive_name = os.path.join(local_path, 'original_files_pre_edits.tar.gz')
    blob = bucket.blob('original_files_pre_edits.tar.gz')
    if os.path.exists(archive_name):
        blob.upload_from_filename(archive_name)
    else:
        raise AssertionError('The archive of original data has not been made')


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


def edit_local_copies_of_glambie_csvs(file_check_dataframe: pd.DataFrame, local_path: str) -> pd.DataFrame:
    """
    Function to edit the local copies of glambie csvs that didn't pass the checks run by
    check_glambie_submission_for_errors. Save out updated copies to the same local filepath.

    Parameters
    ----------
    file_check_dataframe : pd.DataFrame
        Dataframe containing results of checks for inconsistencies within the csv files compared to the expected glambie
        standard.
    """
    archive_path = os.path.join(local_path, 'original_files_pre_edits')
    os.makedirs(archive_path, exist_ok=True)

    file_check_dataframe['reason_for_edit'] = ['-' for i in range(len(file_check_dataframe))]

    for _, file in file_check_dataframe.iterrows():
        if not file.date_check_satisfied:
            submission_data_frame = pd.read_csv(file.local_filepath)

            date_gaps = [datetime.strptime(submission_data_frame.start_date[i + 1], '%d/%m/%Y') - datetime.strptime(
                submission_data_frame.end_date[i], '%d/%m/%Y') for i in range(len(submission_data_frame) - 1)]
            date_gaps_in_days = [a.days for a in date_gaps]

            # 1) Are all gaps 1 or 2 days? We are  aware of some submissions where leap years haven't been taken into
            # account, resulting in mostly 1 day gaps and a small number of 2 day gaps.
            if all(i <= 2 for i in date_gaps_in_days):

                # Always save unedited copy to the archive folder first before any edits
                print('writing original to {}'.format(os.path.join(archive_path, file.file_name)))
                submission_data_frame.to_csv(os.path.join(archive_path, file.file_name))

                updated_end_dates = []
                for i in range(len(submission_data_frame.end_date) - 1):
                    updated_end_dates.append(submission_data_frame.start_date[i + 1])
                updated_end_dates.append(submission_data_frame['end_date'].tolist()[-1])
                submission_data_frame['end_date'] = updated_end_dates
                updated_end_dates_as_datetime = [
                    datetime.strptime(a, '%d/%m/%Y') for a in submission_data_frame.end_date]
                submission_data_frame['end_date_fractional'] = datetime_dates_to_fractional_years(
                    updated_end_dates_as_datetime)

                file_check_dataframe.loc[file_check_dataframe.local_filepath.__eq__(file.local_filepath),
                                         'reason_for_edit'] = '1 or 2 day gap between every row'

            # 2) Is it a gravimetry file with a GRACE gap?
            else:
                if any(i > 350 for i in date_gaps_in_days) & ('gravimetry' in file.local_filepath):
                    non_grace_gaps = [i for i in date_gaps_in_days if i < 300]
                    # If the GRACE gap is the only gap, we won't edit.
                    if all(i == 0 for i in non_grace_gaps):
                        file_check_dataframe.loc[
                            file_check_dataframe.local_filepath.__eq__(file.local_filepath),
                            'reason_for_edit'] = 'Only data gap is due to GRACE missions'

                # 3) Remaining possibility is that it is a gravimetry file with non-GRACE gaps that need interpolating
                elif ('gravimetry' in file.local_filepath):
                    # Always save unedited copy to the archive folder first before any edits
                    print('writing original to {}'.format(os.path.join(archive_path, file.file_name)))
                    submission_data_frame.to_csv(os.path.join(archive_path, file.file_name))

                    # If it is a Wouters submission, need to convert to non-cumulative first!
                    if 'wouters' in file.filename:
                        diff_list_change = submission_data_frame['glacier_change_observed'].diff()
                        diff_list_change[0] = 0.0
                        submission_data_frame['glacier_change_observed'] = diff_list_change

                    interpolated_data_frame = interpolate_change_per_day_to_fill_gaps(submission_data_frame)
                    file_check_dataframe.loc[
                        file_check_dataframe.local_filepath.__eq__(file.local_filepath),
                        'reason_for_edit'] = 'interpolated valid gaps in grav file'

                    # Need to add back in the missing columns here
                    end_date_fractional = datetime_dates_to_fractional_years([datetime.strptime(
                        a, '%d/%m/%Y') for a in interpolated_data_frame.end_date])
                    start_date_fractional = datetime_dates_to_fractional_years([datetime.strptime(
                        a, '%d/%m/%Y') for a in interpolated_data_frame.start_date])
                    interpolated_data_frame['unit'] = [submission_data_frame['unit'][0]
                                                       for i in range(len(interpolated_data_frame))]

                    if all(i == submission_data_frame['glacier_area_reference'][0] for i in submission_data_frame[
                            'glacier_area_reference']):
                        interpolated_data_frame[
                            'glacier_area_reference'] = [submission_data_frame[
                                'glacier_area_reference'][0] for i in range(len(interpolated_data_frame))]
                    else:
                        print('Some different reference areas')

                    if all(i == submission_data_frame['glacier_area_observed'][0] for i in submission_data_frame[
                            'glacier_area_observed']):
                        interpolated_data_frame[
                            'glacier_area_observed'] = [submission_data_frame[
                                'glacier_area_observed'][0] for i in range(len(interpolated_data_frame))]
                    else:
                        print('Some different observed areas')

                    if all(i == submission_data_frame.remarks[0] for i in submission_data_frame.remarks) or \
                            all(np.isnan(submission_data_frame.remarks)):
                        interpolated_data_frame['remarks'] = [submission_data_frame.remarks[0]
                                                              for i in range(len(interpolated_data_frame))]
                    else:
                        print('Some different remarks')

                    interpolated_data_frame['user_group'] = [submission_data_frame['user_group'][0]
                                                             for i in range(len(interpolated_data_frame))]
                    interpolated_data_frame['start_date_fractional'] = start_date_fractional
                    interpolated_data_frame['end_date_fractional'] = end_date_fractional
                    interpolated_data_frame['date'] = interpolated_data_frame['start_date']
                    interpolated_data_frame['date_fractional'] = start_date_fractional
                    interpolated_data_frame['region_id'] = [submission_data_frame['region_id'][0]
                                                            for i in range(len(interpolated_data_frame))]

                    submission_data_frame = interpolated_data_frame.copy()

                else:
                    # If it is not a gravimetry file, then the data it contains is invalid.
                    file_check_dataframe.loc[
                        file_check_dataframe.local_filepath.__eq__(file.local_filepath),
                        'reason_for_edit'] = 'Non-gravimetry file with gaps in data - inspect manually'

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
                                     'reason_for_edit'] = 'Random no data value was used'

    return file_check_dataframe


def main(upload: bool = False):

    local_path = '/path/to/local/folder'
    # If you want to download files for a specific region, set the region_prefix and supply here
    downloaded_files = download_csvs_from_bucket(local_path, region_prefix=None)
    file_check_results_dataframe = generate_results_dataframe(downloaded_files, local_path)
    record_of_edits_dataframe = edit_local_copies_of_glambie_csvs(file_check_results_dataframe, local_path)

    record_of_edits_dataframe.to_csv(os.path.join(local_path, 'record_of_edited_files.csv'))

    # Final step that needs to be implemented here is to upload the edited files into the bucket, after copying the
    # original version of the file into an archive folder
    if upload:
        upload_edited_files_to_bucket(record_of_edits_dataframe)


if __name__ == "__main__":
    upload_after_editing = False
    main(upload_after_editing)
