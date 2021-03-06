import httplib2
import json
import dataset
import logging

from apiclient.discovery import build
from apiclient.http import MediaFileUpload
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.file import Storage
from apiclient import errors

logging.basicConfig(filename='gdrive_backup.log', level=logging.DEBUG)

class GDriveBackup:
    
    def __init__(self, config_path="config.json"):
        # Determine if credentials exist
        self.credentials_file  = Storage("gdrive_credentials")
        self.credentials = self.credentials_file.get()
        # Init connection to SQLite database
        self.db = dataset.connect('sqlite:///gdrive_backup.db')
        # Assume the config path is in the current dir
        self.config_path = config_path
        # Parse the config file for client secret and id
        self.parse_config()
        if not self.credentials:
            logging.debug("Parsing config and authenticating..")
            # No credentials exist, user must authenticate and get creds 
            # Instantiate the scopes to be used
            self.SCOPES = [
                    "https://www.googleapis.com/auth/drive",
            ]
            # Set the redirect url, don't know what this does exactly
            self.REDIRECT_URL = "urn:ietf:wg:oauth:2.0:oob"
            self.authenticate()
        else:
            # Use previously stored credentials
            self.credentials = self.credentials_file.get()
                # Build the drive service
        http = httplib2.Http()
        http = self.credentials.authorize(http)
        self.drive_service = build('drive', 'v2', http=http)

    def parse_config(self):
        # Parsing config occurs only on the first occurence
        with open(self.config_path) as config_file:
            json_config = json.load(config_file)
            self.CLIENT_SECRET = json_config['client_secret']
            self.CLIENT_ID     = json_config['client_id']
            self.paths         = json_config['paths']
            # Persist path data so we dont have to continually parse config
            for path in self.paths:
                # Add paths to path_table
                path_table = self.db['path_table']
                # Determine if this path has already been inserted
                existing_path = path_table.find_one(
                        gdrive_path=path['gdrive_path'])
                # If the path doesn't exist insert it into the db
                if not existing_path:
                    path_table.insert(path)
             
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
    
    def get_folder_id(self, folder):
        # Construct the correct dictionary to find the folder
        query_dict = self.construct_query_dict(folder)
        # make a request for this folder
        gdrive_folder = self.drive_service.files().list(
                **query_dict).execute()
        logging.debug(gdrive_folder)
        if len(gdrive_folder['items']) > 0:
            # Return id of the first item
            return gdrive_folder['items'][0]['id']
        else:
            raise KeyError("Response returned empty")

    def get_list(self):
        path_table = self.db['path_table']
        paths = path_table.all()
        for folder in paths:
            # If no ID was set for the folder, get a folder id
            if not folder.get('folder_id'):
                try:
                    # Get the folder id
                    folder_id = self.get_folder_id(folder)
                    # update the current row with the new folder id
                    # logging.debug("Updating row with id: " + str(folder['id']))
                    # path_table.update({
                    #     "id": folder['id'], 
                    #     "folder_id": folder_id
                    # }, ['id'])
                except KeyError:
                    # Response came back empty, so pass
                    logging.warning("File Not Found: " + folder['gdrive_path'])
                    pass
                except errors.HttpError, error:
                    # Most likely an invalid request
                    logging.warning("HTTP Error: " + error)
                    pass
            else:
                folder_id = folder['folder_id']
            # Get all children with this folder id
            try:
                children = get_folder_children(folder_id)
            except errors.HttpError, error:
                logging.warning("HTTP Error: " + error)
                pass

    def get_folder_children(self, folder_id):
        return self.drive_service.children().list(folderId=folder_id).execute()

    def construct_query_dict(self, folder):
        logging.debug("Creaing query string for: " + folder['gdrive_path'])
        q_string = "title = '" + folder['gdrive_path'] + "' and " \
        + " mimeType = 'application/vnd.google-apps.folder'"
        logging.debug("Query string: " + q_string) 
        return {
                "q": q_string 
        }
        

if __name__ == '__main__':
    gd_backup = GDriveBackup()
    # gd_backup.authenticate()
    gd_backup.get_list()
