import os
from unittest.mock import MagicMock

from google.cloud.storage import Blob
from google.cloud.storage import Client
import numpy as np
import pandas as pd
import pytest

from glambie.data.submission_cleaning_script import check_glambie_submission_for_errors
from glambie.data.submission_cleaning_script import download_csv_files_from_bucket


@pytest.fixture()
def test_inputs_path():
    return os.path.dirname(os.path.abspath(__file__)).replace('/data', '/test_data')


@pytest.fixture()
def example_file_check_dataframe():
    return pd.DataFrame.from_dict({'local_filepath': ['dummy'],
                                   'date_check_satisfied': np.nan,
                                   'nodata_check_satisfied': np.nan})


@pytest.fixture()
def mock_client() -> MagicMock(Client):
    """
    Create a mock google.cloud.storage.Client instance, to be used for testing download_csv_files_from_bucket
    """
    # Set up mock blobs that we instruct the function to download
    blob_1 = MagicMock(spec=Blob)
    blob_1.name = "a/acs.csv"
    blob_2 = MagicMock(spec=Blob)
    blob_2.name = "a/wna.csv"

    # We need to be able to iterate over the blobs
    mock_blobs = MagicMock()
    mock_blobs.__iter__.return_value = [blob_1, blob_2]

    # Set up a mock Client object and tell it to return the mock_blobs when list_blobs is called
    mock_client = MagicMock(spec=Client)
    mock_client.list_blobs.return_value = mock_blobs
    return mock_client


def test_download_csv_files_from_bucket(tmp_path, mock_client):

    test_prefix = 'acs'
    local_data_directory_path = str(tmp_path)  # temp folder for test of download
    downloaded_files = download_csv_files_from_bucket(mock_client, local_data_directory_path,
                                                      region_prefix=test_prefix)
    # check that download_to_file was called for each blob
    for mock_blob in mock_client.list_blobs():
        assert mock_blob.download_to_file.call_count == 1
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
