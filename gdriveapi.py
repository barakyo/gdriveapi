import httplib2
import json
import dataset
import logging

from apiclient.discovery import build
from apiclient.http import MediaFileUpload
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.file import Storage
from apiclient import errors

class GDriveAPI:
    def __init__(self, credentials_file=None):
        if not credentials_file:
            # Start the authentication process
            self.credentials_file = Storage("credentials")
            self.authenticate()
        else:
            # Load credentials from the provided file
            self.credentials_file = Storage(credentials_file) 
            self.credentials = self.credentials_file.get()
        # Create a drive service to be used by the class
        http = httplib2.Http()
        http = self.credentials.authorize(http)
        self.drive_service = build('drive', 'v2', http=http)
    
    def authenticate(self):
        flow = OAuth2WebServerFlow(self.CLIENT_ID,self.CLIENT_SECRET,self.SCOPES,self.REDIRECT_URL)
        if not self.credentials:
            # Follow the steps for authentication
            authorize_url = flow.step1_get_authorize_url()
            print("Please goto the following link in your browser: " + authorize_url)
            auth_code = raw_input("Enter verification code: ")
            self.credentials = flow.step2_exchange(auth_code)
            # Store the credentials in Storage file
            self.credentials_file.put(self.credentials)
    

