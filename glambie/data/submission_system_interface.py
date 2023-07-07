"""
Interface to the GlaMBIE data submission system.

The submission system standardises the data recieved by GlaMBIE in
a number of different ways and presents the output within a Google Bucket.

This module provides access functions for that bucket.
"""

from io import BytesIO
import json
import os
import re
from typing import List, Optional, Union

from google.cloud import storage
import pandas as pd

from glambie.const.data_groups import GlambieDataGroup
from glambie.const.regions import RGIRegion

_storage_client = storage.Client(project='glambie')

_SUBMISSIONS_BUCKET_URI = 'gs://glambie-submissions'

# The design of the DataCatalogue and Timeseries classes implicitly assumes that data is always present on disk,
# which is not the case. This is a design flaw, but rather than redesigning those classes we're simply going to add a
# "fake basepath" to indicate that the data has actually come from the submission system instead,
# which is not a filesystem location.
SUBMISSION_SYSTEM_BASEPATH = 'glambie_submission_system'


def _download_blob(blob_uri: str) -> Union[pd.DataFrame, dict]:
    """
    Download a Binary Large Object (BLOB) from a google bucket and return it as an in-memory object.

    Parameters
    ----------
    blob_uri : str
        The URI for the blob to download
    """
    assert blob_uri.startswith('gs://')
    with BytesIO() as buffer:
        _storage_client.download_blob_to_file(blob_uri, buffer)
        buffer.seek(0)
        if blob_uri.endswith('.csv'):
            return pd.read_csv(buffer)
        elif blob_uri.endswith('.json'):
            return json.load(buffer)
        else:
            raise NotImplementedError(f'download logic for blob uri {blob_uri} not implemented.')


def fetch_timeseries_dataframe(user_group: str, region: RGIRegion, data_group: GlambieDataGroup) -> pd.DataFrame:
    """
    Download a particular timeseries from the submission system.

    Parameters
    ----------
    user_group : str
        The user group for the submission (called "group_name" within the submission system)
    region : RGIRegion
        The RGIRegion for the submission
    data_group : GlambieDataGroup
        The GlambieDataGroup for the submission.
        Note that 'demdiff_and_glaciological' and 'consensus' Data Groups never appear in the submission system.

    Returns
    -------
    pd.DataFrame
        A dataframe containing the loaded submission data. Will have a different format per data_group.
    """
    csv_name_in_bucket = "_".join(
        [region.short_name.lower(),
         data_group.name.lower().replace("demdiff", "dem_differencing"),
         user_group.replace(" ", "_").lower()]) + '.csv'

    return _download_blob(_SUBMISSIONS_BUCKET_URI + '/' + csv_name_in_bucket)


def fetch_all_submission_metadata() -> List[dict]:
    """
    Download the metadata for all submissions provided to GlaMBIE.

    This fuses the content of both the top-level meta.json and the individual submission metadata
    files within the submission system, but does not load the Dataset Information File PDF.

    Returns
    -------
    List[dict]
        A list of dictionaries containing the metadata for each GlaMBIE submission.
        The field values provided for each submission are repeated for each individual Timeseries.
    """
    # note that here, a "dataset" is a single csv file.
    datasets = _download_blob(_SUBMISSIONS_BUCKET_URI + '/meta.json')['datasets']

    # load the other submission metadata.
    # to save effort, download each submission metadata file only once,
    # even though we duplicate the information within the Timeseries objects.
    submission_metadata_buffer = {}
    for dataset in datasets:
        if dataset['submission_metadata_filename'] not in submission_metadata_buffer:
            submission_metadata_buffer[dataset['submission_metadata_filename']] = _download_blob(
                _SUBMISSIONS_BUCKET_URI + '/' + dataset['submission_metadata_filename'])
        dataset.update(submission_metadata_buffer[dataset['submission_metadata_filename']])
        # submission_metadata_filename no longer matters, so we can remove it.
        del dataset['submission_metadata_filename']
        # we now have two copies of the group name, so remove one.
        # We keep group_name because the submission system internals mean that group_name contains
        # case information that user_group does not. We need that case information to correctly
        # identify the files within the submission system bucket.
        dataset['user_group'] = dataset['group_name']
        del dataset['group_name']

    return datasets


def download_dataset_information_file_to_disk(
        user_group: str, data_group: GlambieDataGroup, target_directory: Optional[str] = '.') -> None:
    """
    Download a dataset information file from the submission system.

    The file will be downloaded to a specified target directory.

    Parameters
    ----------
    user_group : str
        The user group for the submission (called "group_name" within the submission system)
    data_group : GlambieDataGroup
        The GlambieDataGroup for the submission.
        Note that 'demdiff_and_glaciological' and 'consensus' Data Groups never appear in the submission system.
    target_directory : Optional[str]
        The directory into which to download the file, by default the current working directory.
    """
    dataset_information_filename = "_".join(
        [data_group.name.lower().replace("demdiff", "dem_differencing"),
         'dataset_information',
         re.sub(r'[^0-9a-zA-Z]+', '-', user_group)]) + '.pdf'

    assert os.path.exists(target_directory), \
        f"Cannot download dataset information file to directory {target_directory} because it does not exist."
    with open(os.path.join(target_directory, dataset_information_filename), 'wb') as fh:
        _storage_client.download_blob_to_file(
            _SUBMISSIONS_BUCKET_URI + '/' + dataset_information_filename, fh)
