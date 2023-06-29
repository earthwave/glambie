import os
from google.cloud.storage import Client

DATA_TRANSFER_BUCKET_NAME = "glambie-submissions"
PROJECT_NAME = "glambie"
_storage_client = Client()


def download_csvs_from_bucket():

    list_of_blobs_in_bucket = _storage_client.list_blobs(DATA_TRANSFER_BUCKET_NAME, prefix='acs')
    downloaded_files = []

    for blob in list_of_blobs_in_bucket:
        downloaded_files.append(blob.name)
        destination_file_path = os.path.join('/home/dubbersophie/glambie_data', blob.name)
        with open(destination_file_path, "wb") as temp_file:
            blob.download_to_file(temp_file, raw_download=False)

    return downloaded_files
