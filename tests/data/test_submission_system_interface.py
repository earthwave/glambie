from io import BytesIO
import json
import os
from unittest.mock import ANY, call, patch

from glambie.data import submission_system_interface
from glambie.const.data_groups import GLAMBIE_DATA_GROUPS
from glambie.const.regions import REGIONS_BY_ID


def create_file_download_func(content: str) -> callable:
    # create and return a mock function  that can be used to replace google.cloud.storage.client.download_blob_to_file
    def mock_download_to_file(_, buffer: BytesIO):
        # ignore the provided filename (the first argument) and just write the content to the buffer
        buffer.write(content.encode())
    return mock_download_to_file


def test_fetch_timeseries_dataframe():
    with patch('glambie.data.submission_system_interface._storage_client') as mock_storage_client:
        mock_storage_client.download_blob_to_file.side_effect = create_file_download_func(
            """a,b,c,d,e
            1,2,3,4,5
            6,7,8,9,10
            """)

        result = submission_system_interface.fetch_timeseries_dataframe(
            user_group='wibble',
            region=REGIONS_BY_ID[0],
            data_group=GLAMBIE_DATA_GROUPS['altimetry'],
            glambie_bucket_name="glambie2-submissions"
        )

        mock_storage_client.download_blob_to_file.assert_called_with(
            'gs://glambie2-submissions/n/a_altimetry_wibble.csv', ANY)
        assert len(result.columns) == 5
        assert result['b'].iloc[1] == 7


def test_fetch_all_submission_metadata():
    with patch('glambie.data.submission_system_interface._storage_client') as mock_storage_client:
        # note this mock covers *both* download calls!
        mock_storage_client.download_blob_to_file.side_effect = create_file_download_func(
            json.dumps({
                'datasets': [{
                    'submission_metadata_filename': 'dummy_filename.json',
                    'user_group': 'alpha',
                    'group_name': 'Alpha'}],
                'additional_metadata_field_1': 'apples',
                'additional_metadata_field_2': 'pears',
                'additional_metadata_field_3': 'stairs'}))

        results = submission_system_interface.fetch_all_submission_metadata("glambie2-submissions")

        mock_storage_client.download_blob_to_file.assert_has_calls([
            call('gs://glambie2-submissions/meta.json', ANY),
            call('gs://glambie2-submissions/dummy_filename.json', ANY)])

        assert len(results) == 1
        assert results[0]['user_group'] == 'Alpha'
        assert results[0]['additional_metadata_field_2'] == 'pears'


def test_download_dataset_information_file(tmp_path: os.PathLike):
    with patch('glambie.data.submission_system_interface._storage_client') as mock_storage_client:
        # note this mock covers *both* download calls!
        mock_storage_client.download_blob_to_file.side_effect = create_file_download_func("I'm a PDF, honest!")

        submission_system_interface.download_dataset_information_file_to_disk(
            user_group='tourists',
            data_group=GLAMBIE_DATA_GROUPS['altimetry'],
            glambie_bucket_name="glambie2-submissions",
            target_directory=tmp_path
        )

        expected_output_path = os.path.join(tmp_path, "altimetry_dataset_information_tourists.pdf")
        assert os.path.exists(expected_output_path)
        with open(expected_output_path) as fh:
            assert fh.read() == "I'm a PDF, honest!"
