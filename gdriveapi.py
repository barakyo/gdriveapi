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

    def __init__(self, credentials_file=None, **config_kwargs):
        """ Instantiates a GDriveAPI class. Will use the provided 
        credentials file or the config file, at LEAST one must be
        provided
        
        Args:
            credentials_file: A generated oauth2client.file.Storage file.

            client_id: Your application's client_id
            client_secret: Your application's client secret
            scopes: A list of scopes that you want your application to use
            redirect_url: The redirect_url for your application
        
        Returns:
            An instantiated and authenticated GDriveAPI
        """ 
        # Determine if a credentials file was providied
        if not credentials_file:
            # If no file was provided, authenticate the user given the kwargs
            try:
               self.authenticate(config_kwargs.pop("client_id"),
                       config_kwargs.pop("client_secret"),
                       config_kwargs.pop("scopes"),
                       config_kwargs.pop("redirect_url"))
            except KeyError:
                # Raise an error letting the user know they didn't provide the
                # necessary credentials
                raise ValueError("A client_id, client_secret, scope, and "
                    "redirect_url must be provided to authenticate")
            # Start the authentication process
            self.credentials_file = Storage("credentials")
            self.authenticate()
        else:
            # Load credentials from the provided file
            self.credentials_file = Storage(credentials_file) 
            self.credentials = self.credentials_file.get()
            if not self.credentials:
                # Missing or invalid file
                raise ValueError("Could not find file: " + credentials_file)
        # Create a drive service to be used by the class
        http = httplib2.Http()
        http = self.credentials.authorize(http)
        self.drive_service = build('drive', 'v2', http=http)
    
    def authenticate(self, client_id, client_secret, scopes, redirect_url):
        """ Authenticates the user for the application they've provided give
        the credentials.

        client_id: Your application's client_id
        client_secret: Your application's client secret
        scopes: A list of scopes that you want your application to use
        redirect_url: The redirect_url for your application

        """
        flow = OAuth2WebServerFlow(self.CLIENT_ID,self.CLIENT_SECRET,self.SCOPES,self.REDIRECT_URL)
        if not self.credentials:
            # Follow the steps for authentication
            authorize_url = flow.step1_get_authorize_url()
            print("Please goto the following link in your browser: " + authorize_url)
            auth_code = raw_input("Enter verification code: ")
            self.credentials = flow.step2_exchange(auth_code)
            # Store the credentials in Storage file
            self.credentials_file.put(self.credentials)
    

