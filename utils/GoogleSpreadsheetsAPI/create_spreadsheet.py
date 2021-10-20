from typing import Union
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from . import get_creds


def callback(request_id, response, exception):
    if exception:
        # Handle error
        print(exception)
    else:
        print("Permission Id: {}".format(response.get('id')))


def resize_columns(service, spreadsheet_id):
    requests_body = [
        {
			"autoResizeDimensions": {
				"dimensions": {
					"sheetId": 0,
					"dimension": "COLUMNS",
					"startIndex": 0,
					"endIndex": 9
				}
			}
		},
		{
			"updateDimensionProperties": {
				"range": {
					"sheetId": 0,
					"dimension": "COLUMNS",
					"startIndex": 7,
					"endIndex": 8
				},
				"properties": {
					"pixelSize": 180
				},
				"fields": "pixelSize"
			},
		}
		
	]
    body_ = {
		'requests': requests_body
	}
    request = service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body_)
    response = request.execute()
    


async def create_spreadsheetand_and_share(name: str, data, mongodb, emailAddress = None):
	try:
		creds: Union[Credentials, None] = await get_creds.get_creds(mongodb)
	except Exception as e:
		print("UNABLE TO GET CREDENTIALS FOR GOOGLE APIS!!!!")
		print(e)
		return
	if creds is None:
		print("UNABLE TO GET CREDENTIALS FOR GOOGLE APIS!!!!")
		return
	spreadsheet_service = build('sheets', 'v4', credentials=creds)
	drive_service = build('drive', 'v3', credentials=creds)

	spreadsheet = {
		'properties': {
			'title': name
		}
	}
	spreadsheet = spreadsheet_service.spreadsheets().create(
		body=spreadsheet,
		fields='spreadsheetId'
	).execute()
	spreadsheet_id = spreadsheet.get('spreadsheetId')
	body_ = {
		'majorDimension': 'ROWS',
		'values': data
	}
	request = spreadsheet_service.spreadsheets().values().update(spreadsheetId=spreadsheet_id, range="Sheet1!A1", body=body_, valueInputOption="USER_ENTERED")
	resize_columns(spreadsheet_service, spreadsheet_id)
	response = request.execute()
	user_permission = {
		'type': 'user',
		'role': 'writer',
		'emailAddress': emailAddress,
	}
	send_spreadsheet_request = drive_service.permissions().create(
		fileId=spreadsheet_id,
		body=user_permission,
		fields='id',
  		# transferOwnership=True
	)
	# send_spreadsheet_response = send_spreadsheet_request.execute()
	return spreadsheet_id
