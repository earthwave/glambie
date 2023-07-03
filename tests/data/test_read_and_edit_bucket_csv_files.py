import os
import pytest
import numpy as np
import pandas as pd
from glambie.data.read_and_edit_bucket_csv_files import download_csvs_from_bucket, check_glambie_submission_for_errors


@pytest.fixture()
def example_file_check_dataframe():
    return pd.DataFrame.from_dict({'file_name': ['dummy', 'dummy'],
                                   'date_check_satisfied': np.nan,
                                   'nodata_check_satisfied': np.nan})


def test_download_csvs_from_bucket(tmp_path):

    test_prefix = 'acs_altimetry'
    local_data_directory_path = str(tmp_path)  # temp folder for test of download
    downloaded_files = download_csvs_from_bucket(test_prefix, local_data_directory_path)
    assert os.path.exists(tmp_path / 'acs_altimetry_jakob_gourmelen.csv')
    assert len(downloaded_files) == 2


def test_check_glambie_submission_for_errors(test_inputs_path, example_file_check_dataframe):

    test_csv_date_error = os.path.join(test_inputs_path, 'submissions', 'test_glambie_submission_date_error.csv')
    test_csv_nodata_error = os.path.join(test_inputs_path, 'submissions', 'test_glambie_submission_nodata_error.csv')
    example_file_check_dataframe['file_name'] = [test_csv_date_error, test_csv_nodata_error]

    example_file_check_dataframe = check_glambie_submission_for_errors(test_csv_date_error,
                                                                       example_file_check_dataframe)

    assert not example_file_check_dataframe.loc[example_file_check_dataframe.file_name.__eq__(
        test_csv_date_error), 'date_check_satisfied'].values[0]
    assert example_file_check_dataframe.loc[example_file_check_dataframe.file_name.__eq__(
        test_csv_date_error), 'nodata_check_satisfied'].values[0]

    example_file_check_dataframe = check_glambie_submission_for_errors(test_csv_nodata_error,
                                                                       example_file_check_dataframe)

    assert example_file_check_dataframe.loc[example_file_check_dataframe.file_name.__eq__(
        test_csv_nodata_error), 'date_check_satisfied'].values[0]
    assert not example_file_check_dataframe.loc[example_file_check_dataframe.file_name.__eq__(
        test_csv_nodata_error), 'nodata_check_satisfied'].values[0]
