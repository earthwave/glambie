import os
import pytest
import numpy as np
import pandas as pd
from glambie.data.submission_cleaning_script import download_csvs_from_bucket, check_glambie_submission_for_errors


@pytest.fixture()
def test_inputs_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_data')


@pytest.fixture()
def example_file_check_dataframe():
    return pd.DataFrame.from_dict({'local_filepath': 'dummy',
                                   'date_check_satisfied': np.nan,
                                   'nodata_check_satisfied': np.nan})


def test_download_csvs_from_bucket(tmp_path):

    test_prefix = 'acs_altimetry'
    local_data_directory_path = str(tmp_path)  # temp folder for test of download
    downloaded_files = download_csvs_from_bucket(local_data_directory_path, region_prefix=test_prefix)
    assert os.path.exists(tmp_path / 'acs_altimetry_jakob_gourmelen.csv')
    assert len(downloaded_files) == 2


def test_check_glambie_submission_for_errors_date_error(test_inputs_path, example_file_check_dataframe):

    test_csv_with_date_error = os.path.join(test_inputs_path, 'submissions', 'test_glambie_submission_date_error.csv')
    example_file_check_dataframe['local_filepath'] = test_csv_with_date_error

    example_file_check_dataframe = check_glambie_submission_for_errors(test_csv_with_date_error,
                                                                       example_file_check_dataframe)

    assert not example_file_check_dataframe.loc[example_file_check_dataframe.local_filepath.__eq__(
        test_csv_with_date_error), 'date_check_satisfied'].values[0]
    assert example_file_check_dataframe.loc[example_file_check_dataframe.local_filepath.__eq__(
        test_csv_with_date_error), 'nodata_check_satisfied'].values[0]


def test_check_glambie_submission_for_errors_nodata_error(test_inputs_path, example_file_check_dataframe):

    test_csv_with_nodata_error = os.path.join(
        test_inputs_path, 'submissions', 'test_glambie_submission_nodata_error.csv')
    example_file_check_dataframe['local_filepath'] = test_csv_with_nodata_error

    example_file_check_dataframe = check_glambie_submission_for_errors(test_csv_with_nodata_error,
                                                                       example_file_check_dataframe)

    assert example_file_check_dataframe.loc[example_file_check_dataframe.local_filepath.__eq__(
        test_csv_with_nodata_error), 'date_check_satisfied'].values[0]
    assert not example_file_check_dataframe.loc[example_file_check_dataframe.local_filepath.__eq__(
        test_csv_with_nodata_error), 'nodata_check_satisfied'].values[0]
