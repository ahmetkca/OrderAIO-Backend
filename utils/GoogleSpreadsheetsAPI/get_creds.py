import os.path
from typing import Union
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SPREADSHEETS_SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']


def get_creds() -> Union[Credentials, None]:
    """
    	Get Credentials from Google API
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('./utils/GoogleSpreadsheetsAPI/token.json'):
        creds = Credentials.from_authorized_user_file('./utils/GoogleSpreadsheetsAPI/token.json', SPREADSHEETS_SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                './utils/GoogleSpreadsheetsAPI/credentials.json', SPREADSHEETS_SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('./utils/GoogleSpreadsheetsAPI/token.json', 'w') as token:
            token.write(creds.to_json())
    return creds


if __name__ == '__main__':
    get_creds()
