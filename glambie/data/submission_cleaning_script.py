"""
Script that can be used to make local copies of data in the glambie submissions google bucket, check these files for
any formatting inconsistencies (with respect to the glambie standard), and then edit the local copies to correct these
problems. After applying a set of edits, depending on which issues are present in each dataset, you can then upload the
edited versions of files back to the bucket, as well as a zip archive of the original versions of these files.

Possible reasons for edits:
    1) Small gaps between end dates and subsequent start dates (1 or 2 days consistently)
    2) A gravimetry file with non-GRACE gaps that need interpolating
    3) Data has been submitted as cumulative change

This script should be run after all submissions have been received for a single round of the GlaMBIE project, before the
algorithm is run.
"""

from datetime import datetime
import logging
import os

from google.cloud.storage import Client
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Literal, Tuple

from glambie.monitoring.logger import setup_logging
from glambie.util.date_helpers import datetime_dates_to_fractional_years
from glambie.util.timeseries_helpers import interpolate_change_per_day_to_fill_gaps
from glambie.util.version_helpers import get_glambie_bucket_name

MAX_ALLOWED_ELEVATION_CHANGE_M = 100
MAX_ALLOWED_ELEVATION_CHANGE_GT = 10000
log = logging.getLogger(__name__)


def download_csv_files_from_bucket(
    storage_client: Client,
    local_data_directory_path: str,
    glambie_bucket_name: str,
    region_prefix: str = None,
) -> list[str]:
    """
    Function to download glambie .csv files from the google bucket to a local folder, where they can be checked and
    edited. Specify files for a specific region using the region_prefix parameter - otherwise all .csv files in the
    bucket will be downloaded.

    Parameters
    ----------
    storage_client : Client
        Google Cloud storage Client instance that will be used to access bucket.
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
    list_of_blobs_in_bucket = storage_client.list_blobs(
        glambie_bucket_name, prefix=region_prefix
    )
    downloaded_files = []

    for blob in list_of_blobs_in_bucket:
        if ".csv" in blob.name:
            downloaded_files.append(blob.name)
            destination_file_path = os.path.join(local_data_directory_path, blob.name)
            # check that destination directory exists and create it if it doesn't
            Path(destination_file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(destination_file_path, "wb") as output_file:
                blob.download_to_file(output_file, raw_download=False)

    return downloaded_files


def upload_edited_csv_files_to_bucket(
    storage_client: Client,
    files_to_upload: list[str],
    local_path: str,
    glambie_bucket_name: str,
):
    """
    After editing local copies of the submitted csv files, replace the original versions in the bucket with the
    edited local versions. Also upload an archive folder containing original copies of all edited files

    Parameters
    ----------
    storage_client : Client
        Google Cloud storage Client instance that will be used to access bucket.
    files_to_upload : list[str]
        List containing the names of files that should be uploaded to the GlaMBIE bucket
    local_path : str
        Path to local copies of bucket data.
    glambie_bucket_name : str
        Glambie GCP bucket name.

    Raises
    ------
    AssertionError
        If archive folder has not yet been created
    """
    for file in files_to_upload:
        bucket = storage_client.get_bucket(glambie_bucket_name)
        blob = bucket.blob(os.path.basename(file))
        blob.upload_from_filename(file)
        log.info("Edited version of %s uploaded to bucket", os.path.basename(file))

    # Finally upload archive of unedited files
    archive_name = os.path.join(local_path, "original_files_pre_edits.tar.gz")
    blob = bucket.blob("original_files_pre_edits.tar.gz")
    if os.path.exists(archive_name):
        blob.upload_from_filename(archive_name)
    else:
        raise AssertionError(
            f"The archive of original data {archive_name} has not been made locally and has therefore"
            "not been uploaded."
        )


def generate_results_dataframe(file_paths: list[str]) -> pd.DataFrame:
    """
    Generate a summary which of the files need editing and what edits need to be made for each. These can be reviewed
    or actioned later with edit_local_copies_of_glambie_csvs.

    Parameters
    ----------
    file_paths : list[str]
        List of files that have been downloaded to the local directory.

    Returns
    -------
    pd.DataFrame
        Dataframe containing results of checks for inconsistencies within the csv files compared to the expected glambie
        standard. Columns include filepaths and filenames, as well as 'date_check_satisfied' and
        'nodata_check_satisfied', which will True or False for each row depending on the outcome of
        check_glambie_submission_for_errors for each file.
    """

    results_dict = {
        "local_filepath": file_paths,
        "file_name": [os.path.basename(a) for a in file_paths],
    }
    results_dataframe = pd.DataFrame.from_dict(results_dict)

    results_dataframe["date_check_satisfied"] = False
    results_dataframe["nodata_check_satisfied"] = False

    for file in file_paths:
        file_check_dataframe = check_glambie_submission_for_errors(
            file, results_dataframe
        )

    return file_check_dataframe


def check_glambie_submission_for_errors(
    csv_file_path: str, file_check_dataframe: pd.DataFrame
) -> pd.DataFrame:
    """
    Perform consistency checks on a submitted GlaMBIE csv file. Currently performs 2 checks:

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
    log.info(
        "Checking submitted file %s for errors with respect to the glambie standard data format",
        os.path.basename(csv_file_path),
    )
    submission_data_frame = pd.read_csv(csv_file_path)

    # First, check for any non equal end_dates and subsequent start_dates
    start_dates = submission_data_frame.start_date.values
    end_dates = submission_data_frame.end_date.values
    start_dates = np.append(
        start_dates, np.nan
    )  # Add an extra element to the end of this list for check below

    start_dates_and_end_dates_align = True
    no_random_nodata_values_used = True

    for ind, end_date in enumerate(end_dates):
        # If end_date != start_date for any of the consecutive rows, set date_check_bool to False for this file - i.e.
        # file does not pass test and will need to be edited
        end_date_matches_next_start_date = end_date.__eq__(start_dates[ind + 1])
        if not end_date_matches_next_start_date:
            start_dates_and_end_dates_align = False

    # Next, check for any instances of extreme values of change - we are aware of instances where people have used
    # e.g change = 9999. for rows where they don't have a measured change. They were unaware that they should just
    # remove these rows instead of setting an arbitrary nodata value. Extreme value threshold needs to be different
    # depending on the units used.
    change_values = submission_data_frame.glacier_change_observed.values

    if np.any(
        submission_data_frame.unit.values[0] == np.array(["m", "mwe"])
    ):  # check if units are m or mwe
        # check that all changes in list are < +/-100
        no_random_nodata_values_used = all(
            abs(i) < MAX_ALLOWED_ELEVATION_CHANGE_M for i in change_values
        )
    elif submission_data_frame.unit.values[0] == "Gt":  # check if units are Gt
        no_random_nodata_values_used = all(
            abs(i) < MAX_ALLOWED_ELEVATION_CHANGE_GT for i in change_values
        )

    # If all rows passed the date check above, we store date_check_satisfied = True for this file: don't need to edit it
    file_check_dataframe.loc[
        file_check_dataframe.local_filepath.__eq__(csv_file_path),
        "date_check_satisfied",
    ] = start_dates_and_end_dates_align

    # Likewise if all rows passed the nodata check above, we store nodata_check_satisfied for this file.
    file_check_dataframe.loc[
        file_check_dataframe.local_filepath.__eq__(csv_file_path),
        "nodata_check_satisfied",
    ] = no_random_nodata_values_used

    return file_check_dataframe


def fix_simple_date_gaps(
    file_check_info_row: Tuple, submission_data_frame: pd.DataFrame, archive_path: str
):
    """
    Fix a dataframe of time series data which has gaps of 1 or 2 days between end_date and subsequent start_date in
    any rows. Larger gaps are dealt with in 'fix_non_grace_gravimetry_gaps', as they need interpolating.

    Parameters
    ----------
    file_check_info_row : Tuple
        Tuple containing column values for a single row of the file_check_info dataframe created by
        generate_results_dataframe.
    submission_data_frame : pd.DataFrame
        DataFrame containing submitted time series data.
    archive_path : str
        Path to original data archive, where dataframe is saved out before any edits are made to retain an original
        copy.

    Returns
    -------
    pd.DataFrame
        DataFrame containing submitted time series data, edited to remove small date gaps.
    """

    # Always save unedited copy to the archive folder first before any edits
    log.info(
        "Writing original file to %s",
        os.path.join(archive_path, file_check_info_row.file_name),
    )
    submission_data_frame.to_csv(
        os.path.join(archive_path, file_check_info_row.file_name)
    )

    updated_end_dates, updated_fractional_end_dates = [], []
    for i in range(len(submission_data_frame.end_date) - 1):
        updated_end_dates.append(submission_data_frame.start_date[i + 1])
        updated_fractional_end_dates.append(
            submission_data_frame.start_date_fractional[i + 1]
        )

    updated_end_dates.append(submission_data_frame["end_date"].tolist()[-1])
    updated_fractional_end_dates.append(
        submission_data_frame["end_date_fractional"].tolist()[-1]
    )

    submission_data_frame["end_date"] = updated_end_dates
    submission_data_frame["end_date_fractional"] = updated_fractional_end_dates

    return submission_data_frame


def fix_non_grace_gravimetry_gaps(
    file_check_info_row: Tuple, submission_data_frame: pd.DataFrame, archive_path: str
):
    """
    Fix a dataframe of gravimetry time series data which had large gaps of missing temporal coverage, by interpolating
    between these dates.

    Parameters
    ----------
    file_check_info_row : Tuple
        Tuple containing column values for a single row of the file_check_info dataframe created by
        generate_results_dataframe.
    submission_data_frame : pd.DataFrame
        DataFrame containing submitted time series data.
    archive_path : str
        Path to original data archive, where dataframe is saved out before any edits are made to retain an original
        copy.

    Returns
    -------
    pd.DataFrame
        DataFrame containing submitted time series data, edited to interpolate between larger date gaps.

    Raises
    ------
    AssertionError
        If not all observed areas are equal and a new interpolated column cannot be created.
    AssertionError
        If not all reference areas are equal and a new interpolated column cannot be created.
    AssertionError
        If not all remarks equal and a new interpolated column cannot be created.
    """

    # Always save unedited copy to the archive folder first before any edits
    log.info(
        "Writing original file to %s",
        os.path.join(archive_path, file_check_info_row.file_name),
    )
    submission_data_frame.to_csv(
        os.path.join(archive_path, file_check_info_row.file_name)
    )

    # If it is a Wouters submission, need to convert to non-cumulative first!
    if "wouters" in file_check_info_row.filename:
        diff_list_change = submission_data_frame["glacier_change_observed"].diff()
        diff_list_change[0] = 0.0
        submission_data_frame["glacier_change_observed"] = diff_list_change

    interpolated_data_frame = interpolate_change_per_day_to_fill_gaps(
        submission_data_frame
    )

    # Need to add back in the missing columns here
    end_date_fractional = datetime_dates_to_fractional_years(
        [datetime.strptime(a, "%d/%m/%Y") for a in interpolated_data_frame.end_date]
    )
    start_date_fractional = datetime_dates_to_fractional_years(
        [datetime.strptime(a, "%d/%m/%Y") for a in interpolated_data_frame.start_date]
    )
    interpolated_data_frame["unit"] = [
        submission_data_frame["unit"][0] for i in range(len(interpolated_data_frame))
    ]

    if all(
        i == submission_data_frame["glacier_area_reference"][0]
        for i in submission_data_frame["glacier_area_reference"]
    ):
        interpolated_data_frame["glacier_area_reference"] = [
            submission_data_frame["glacier_area_reference"][0]
            for i in range(len(interpolated_data_frame))
        ]
    else:
        raise AssertionError(
            f"Not all reference areas are equal in {file_check_info_row.file_name} -"
            "interpolated dataframe can not be saved, this file needs further"
            "investigation"
        )

    if all(
        i == submission_data_frame["glacier_area_observed"][0]
        for i in submission_data_frame["glacier_area_observed"]
    ):
        interpolated_data_frame["glacier_area_observed"] = [
            submission_data_frame["glacier_area_observed"][0]
            for i in range(len(interpolated_data_frame))
        ]
    else:
        raise AssertionError(
            f"Not all observed areas are equal in {file_check_info_row.file_name} -"
            "interpolated dataframe can not be saved out, this file needs further"
            "investigation"
        )

    if all(
        i == submission_data_frame.remarks[0] for i in submission_data_frame.remarks
    ) or all(np.isnan(submission_data_frame.remarks)):
        interpolated_data_frame["remarks"] = [
            submission_data_frame.remarks[0]
            for i in range(len(interpolated_data_frame))
        ]
    else:
        raise AssertionError(
            f"Not all remarks are the same in {file_check_info_row.file_name} -"
            "interpolated dataframe can not be saved out, this file needs further"
            "investigation"
        )

    interpolated_data_frame["user_group"] = [
        submission_data_frame["user_group"][0]
        for i in range(len(interpolated_data_frame))
    ]
    interpolated_data_frame["start_date_fractional"] = start_date_fractional
    interpolated_data_frame["end_date_fractional"] = end_date_fractional
    interpolated_data_frame["date"] = interpolated_data_frame["start_date"]
    interpolated_data_frame["date_fractional"] = start_date_fractional
    interpolated_data_frame["region_id"] = [
        submission_data_frame["region_id"][0]
        for i in range(len(interpolated_data_frame))
    ]

    submission_data_frame = interpolated_data_frame.copy()

    return submission_data_frame


def fix_no_data_values(
    file_check_info_row: Tuple, submission_data_frame: pd.DataFrame, archive_path: str
):
    """
    Fix a dataframe of timeseries data which has invalid no data values, by removing these rows from the data.

    Parameters
    ----------
    file_check_info_row : Tuple
        Tuple containing column values for a single row of the file_check_info dataframe created by
        generate_results_dataframe.
    submission_data_frame : pd.DataFrame
        DataFrame containing submitted time series data.
    archive_path : str
        Path to original data archive, where dataframe is saved out before any edits are made to retain an original
        copy.

    Returns
    -------
    pd.DataFrame
        DataFrame containing submitted time series data, edited to remove small date gaps.
    """

    # Always save unedited copy to the archive folder first before any edits
    log.info(
        "Writing original file to %s",
        os.path.join(archive_path, file_check_info_row.file_name),
    )
    submission_data_frame.to_csv(
        os.path.join(archive_path, file_check_info_row.file_name)
    )

    if np.any(submission_data_frame.unit.values[0] == np.array(["m", "mwe"])):
        # delete rows with change values > +/-100 - these numbers need some thought
        submission_data_frame.drop(
            submission_data_frame[
                abs(submission_data_frame.glacier_change_observed)
                > MAX_ALLOWED_ELEVATION_CHANGE_M
            ].index,
            inplace=True,
        )
    elif submission_data_frame.unit.values[0] == "Gt":
        # delete rows with change values > +/-10000
        submission_data_frame.drop(
            submission_data_frame[
                abs(submission_data_frame.glacier_change_observed)
                > MAX_ALLOWED_ELEVATION_CHANGE_GT
            ].index,
            inplace=True,
        )

    return submission_data_frame


def apply_csv_file_corrections(
    file_check_info: pd.DataFrame, directory_path: str
) -> pd.DataFrame:
    """
    Edit local copies of GlaMBIE submissions that didn't pass the checks run by
    check_glambie_submission_for_errors. Save out updated copies to the same local filepath.

    Parameters
    ----------
    file_check_info : pd.DataFrame
        Dataframe containing results of checks for inconsistencies within the csv files compared to the expected glambie
        standard.
    directory_path : str
        Path to files to be edited.

    Returns
    -------
    pd.DataFrame
        file_check_info dataframe updated with a new column containing reason for edit for each file that has been
        changed in this function
    """
    archive_path = os.path.join(directory_path, "original_files_pre_edits")
    os.makedirs(archive_path, exist_ok=True)

    file_check_info["reason_for_edit"] = ["-" for i in range(len(file_check_info))]

    for file_check_info_row in file_check_info.itertuples():
        if not file_check_info_row.date_check_satisfied:
            log.info(
                "Performing edits for submitted file %s, as date check was not satisfied",
                file_check_info_row.file_name,
            )

            submission_data_frame = pd.read_csv(file_check_info_row.local_filepath)

            date_gaps = [
                datetime.strptime(submission_data_frame.start_date[i + 1], "%d/%m/%Y")
                - datetime.strptime(submission_data_frame.end_date[i], "%d/%m/%Y")
                for i in range(len(submission_data_frame) - 1)
            ]
            date_gaps_in_days = [a.days for a in date_gaps]

            # 1) Are all gaps 1 or 2 days? We are  aware of some submissions where leap years haven't been taken into
            # account, resulting in mostly 1 day gaps and a small number of 2 day gaps.
            if all(i <= 2 for i in date_gaps_in_days):
                fix_simple_date_gaps(
                    file_check_info_row, submission_data_frame, archive_path
                )
                file_check_info.loc[
                    file_check_info.local_filepath.__eq__(
                        file_check_info_row.local_filepath
                    ),
                    "reason_for_edit",
                ] = "1 or 2 day gap between every row"

            else:
                # 2) Is it a gravimetry file with a GRACE gap?
                if any(i > 350 for i in date_gaps_in_days) & (
                    "gravimetry" in file_check_info_row.local_filepath
                ):
                    non_grace_gaps = [i for i in date_gaps_in_days if i < 300]
                    # If the GRACE gap is the only gap, we won't edit.
                    if all(i == 0 for i in non_grace_gaps):
                        file_check_info.loc[
                            file_check_info.local_filepath.__eq__(
                                file_check_info_row.local_filepath
                            ),
                            "reason_for_edit",
                        ] = "Only data gap is due to GRACE missions"

                # 3) Remaining possibility is that it is a gravimetry file with non-GRACE gaps that need interpolating
                elif "gravimetry" in file_check_info_row.local_filepath:
                    fix_non_grace_gravimetry_gaps(
                        file_check_info_row, submission_data_frame
                    )
                    file_check_info.loc[
                        file_check_info.local_filepath.__eq__(
                            file_check_info_row.local_filepath
                        ),
                        "reason_for_edit",
                    ] = "interpolated valid gaps in grav file"

                else:
                    # If it is not a gravimetry file, then the data it contains is invalid.
                    file_check_info.loc[
                        file_check_info.local_filepath.__eq__(
                            file_check_info_row.local_filepath
                        ),
                        "reason_for_edit",
                    ] = "Non-gravimetry file with gaps in data - inspect manually"

            # Save out to same path as original file
            submission_data_frame.to_csv(file_check_info_row.local_filepath)

        if not file_check_info_row.nodata_check_satisfied:
            submission_data_frame = pd.read_csv(file_check_info_row.local_filepath)
            fix_no_data_values(submission_data_frame)
            submission_data_frame.to_csv(file_check_info_row.local_filepath)

            # Record that the file has been edited
            file_check_info.loc[
                file_check_info.local_filepath.__eq__(
                    file_check_info_row.local_filepath
                ),
                "reason_for_edit",
            ] = "Random no data value was used"

    return file_check_info


def main(upload: bool = False, glambie_version: Literal[1, 2] = 2):
    local_path = "/path/to/local/folder"
    storage_client = Client()
    glambie_bucket_name = get_glambie_bucket_name(glambie_version)
    # If you want to download files for a specific region, set the region_prefix and supply here
    downloaded_files = download_csv_files_from_bucket(
        storage_client, local_path, glambie_bucket_name, region_prefix=None
    )
    file_check_results_dataframe = generate_results_dataframe(
        downloaded_files, local_path
    )
    record_of_edits_dataframe = apply_csv_file_corrections(
        file_check_results_dataframe, local_path
    )

    record_of_edits_dataframe.to_csv(
        os.path.join(local_path, "record_of_edited_files.csv")
    )

    # Final step that needs to be implemented here is to upload the edited files into the bucket, after copying the
    # original version of the file into an archive folder
    if upload:
        upload_edited_csv_files_to_bucket(
            storage_client,
            record_of_edits_dataframe.local_filepath.to_list(),
            local_path,
            glambie_bucket_name,
        )


if __name__ == "__main__":
    # setup logging
    setup_logging(log_file_path="/data/yak1/working/glambie/submission_cleaning_log.log")

    main(upload=False, glambie_version=2)
