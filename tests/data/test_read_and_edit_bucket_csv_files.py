import os
from glambie.data.read_and_edit_bucket_csv_files import download_csvs_from_bucket


def test_download_csvs_from_bucket():

    test_prefix = 'acs'
    downloaded_files = download_csvs_from_bucket(test_prefix)
    assert os.path.exists(os.path.join('/data/ox1/working/glambie/temp_local_copies_of_submitted_data',
                                       'acs_altimetry_jakob_gourmelen.csv'))
    assert len(downloaded_files) == 17
