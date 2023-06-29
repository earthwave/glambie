import pandas as pd
from io import BytesIO
from google.cloud.storage import Client

DATA_TRANSFER_BUCKET_NAME = "glambie-submissions"
PROJECT_NAME = "glambie"
_storage_client = Client(project=PROJECT_NAME)

def download_csv_files_from_bucket():

    query_result_chunks = []
    for blob in _storage_client.list_blobs(DATA_TRANSFER_BUCKET_NAME, suffix='csv'):
        chunk_buffer = BytesIO()
        blob.download_to_file(chunk_buffer)
        chunk_buffer.seek(0)
        query_result_chunks.append(pd.read_parquet(chunk_buffer))