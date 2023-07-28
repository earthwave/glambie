import os
import pytest
import numpy as np
import pandas as pd
from google.cloud.storage import Blob, Client
from unittest.mock import MagicMock, patch
from glambie.data.submission_cleaning_script import download_csv_files_from_bucket, check_glambie_submission_for_errors


@pytest.fixture()
def test_inputs_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_data')


@pytest.fixture()
def example_file_check_dataframe():
    return pd.DataFrame.from_dict({'local_filepath': 'dummy',
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
    blob_1.public_url = "https://a/acs.csv"

    blob_2 = MagicMock(spec=Blob)
    blob_2.name = "a/wna.csv"
    blob_2.public_url = "https://a/wna.csv"

    # We need to be able to iterate over the blobs and query them for prefixes
    mock_blobs = MagicMock()
    mock_blobs.__iter__.return_value = [blob_1, blob_2]
    mock_blobs.prefixes = ['acs/', 'wna/']  # ? not sure what this does

    # Give the client the blobs?
    mock_client = MagicMock(spec=Client)
    mock_client.list_blobs.return_value = mock_blobs

    return mock_client


@pytest.fixture()
def test_google_bucket() -> MagicMock(Client):
    return mock_client


def test_download_csv_files_from_bucket(tmp_path):

    mock_client = test_google_bucket()
    with patch.object(download_csv_files_from_bucket, 'storage_client') as mock_client:
        test_prefix = 'acs'
        local_data_directory_path = str(tmp_path)  # temp folder for test of download
        downloaded_files = download_csv_files_from_bucket(mock_client, local_data_directory_path,
                                                          region_prefix=test_prefix)

    # How will asserts change now?
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
