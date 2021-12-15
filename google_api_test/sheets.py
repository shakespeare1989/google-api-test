"""
BEFORE RUNNING:
---------------
1. If not already done, enable the Google Sheets API
   and check the quota for your project at
   https://console.developers.google.com/apis/api/sheets
2. Install the Python client library for Google APIs by running
   `pip install --upgrade google-api-python-client`
"""
from pprint import pprint

from googleapiclient import discovery

# TODO: Change placeholder below to generate authentication credentials. See
# https://developers.google.com/sheets/quickstart/python#step_3_set_up_the_sample
#
# Authorize using one of the following scopes:
#     'https://www.googleapis.com/auth/drive'
#     'https://www.googleapis.com/auth/drive.file'
#     'https://www.googleapis.com/auth/spreadsheets'

def sheets():
    credentials = None

    service = discovery.build('sheets', 'v4', credentials=credentials)

    # The ID of the spreadsheet to retrieve metadata from.
    spreadsheet_id = 'G Suite User Usage Report'  # TODO: Update placeholder value.

    # The ID of the developer metadata to retrieve.
    metadata_id = 0  # TODO: Update placeholder value.

    request = service.spreadsheets().developerMetadata().get(spreadsheetId=spreadsheet_id, metadataId=metadata_id)
    response = request.execute()

    # TODO: Change code below to process the `response` dict:
    pprint(response)