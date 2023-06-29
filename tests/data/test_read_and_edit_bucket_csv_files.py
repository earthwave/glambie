import os
from glambie.data.read_and_edit_bucket_csv_files import download_csvs_from_bucket


def test_download_csvs_from_bucket():

    downloaded_files = download_csvs_from_bucket()
    assert os.path.exists('/home/dubbersophie/glambie_data/acs_altimetry_jakob_gourmelen.csv')
    assert len(downloaded_files) == 17
