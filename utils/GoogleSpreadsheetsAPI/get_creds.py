import datetime
import json
import pprint
from typing import Union
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
# from database import MongoDB

SPREADSHEETS_SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']


async def get_creds(mongodb) -> Union[Credentials, None]:
    # mongodb = MongoDB()
    """
    	Get Credentials from Google API
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    # if os.path.exists('./utils/GoogleSpreadsheetsAPI/token.json'):
    print("<>/\<> TRYING TO AUTHORIZE BY USING token.json FILE <>/\<>")
    token_json = await mongodb.db["GoogleAPITokenJson"].find({}, projection={ "_id": False, "token_as_string": True}).to_list(length=1)
    token_json = token_json[0]
    token_as_string = token_json.get("token_as_string")
    creds=None
    if len(token_as_string) > 0:
        token_as_json = json.loads(token_as_string)
        pprint.pprint(token_as_json)
        creds = Credentials.from_authorized_user_info(token_as_json, SPREADSHEETS_SCOPES)
        # creds = Credentials.from_authorized_user_file('./utils/GoogleSpreadsheetsAPI/token.json', SPREADSHEETS_SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("<>/\<> TRYING TO REFRESH CREDENTIALS <>/\<>")
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                './utils/GoogleSpreadsheetsAPI/credentials.json', SPREADSHEETS_SCOPES)
            creds = flow.run_local_server(port=0, access_type='offline',include_granted_scopes='true')
        # Save the credentials for the next run
        token_in_mongodb = await mongodb.db["GoogleAPITokenJson"].find({}).to_list(length=1)
        token_in_mongodb = token_in_mongodb[0]
        mongodb.db["GoogleAPITokenJson"].update_one(
            {"_id": token_in_mongodb.get("_id")}, 
            {"$set": {
                "token_as_string": creds.to_json(),
                "update_at": datetime.datetime.utcnow()
            }}
        )
        # with open('./utils/GoogleSpreadsheetsAPI/token.json', 'w') as token:
        #     token.write(creds.to_json())
    return creds
