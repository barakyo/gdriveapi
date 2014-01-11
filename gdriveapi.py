import httplib2
import json
import logging

from pyparsing import (Word, alphas, ParseException, OneOrMore, 
    ParseResults, alphanums) 
from apiclient.discovery import build
from apiclient.http import MediaFileUpload
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.file import Storage
from apiclient import errors
from collections import namedtuple
from datetime import datetime
from pytz import utc

logging.basicConfig(filename='gdriveapi.log', level=logging.DEBUG)

class GDriveAPI(object):

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
            # Create a new credentials file
            self.credentials_file = Storage("credentials")
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
        self.parser = GDriveAPIParser()
        self.op_map = {
            'lte': '<=', 
            'lt':  '<',
            'gt':  '>',
            'gte': '>=',
        }
    
    def authenticate(self, client_id, client_secret, scopes, redirect_url):
        """ Authenticates the user for the application they've provided give
        the credentials.

        client_id: Your application's client_id
        client_secret: Your application's client secret
        scopes: A list of scopes that you want your application to use
        redirect_url: The redirect_url for your application

        """
        flow = OAuth2WebServerFlow(client_id, client_secret, scopes, redirect_url)
        # Follow the steps for authentication
        authorize_url = flow.step1_get_authorize_url()
        print("Please goto the following link in your browser: " + authorize_url)
        auth_code = raw_input("Enter verification code: ")
        self.credentials = flow.step2_exchange(auth_code)
        # Store the credentials in Storage file
        self.credentials_file.put(self.credentials)

    def create_gdrive_files(self, files):
        """ Accepts a list of dictionaries from the result of a successful 
        query and converts the items into objects using nametuples for
        convenience of the API user 

        Constructs namedtuples after the keys of the largest dict returned in 
        the items list
        
        Args:
            files - The items list of a successful response, that is
                    response['items']

        Returns:
            A list of GDriveFiles
        """
        file_list = []
        for f in files:
            GDriveFile = namedtuple('GDriveFile', f.keys())
            file_list.append(GDriveFile(**f))
        return file_list
 
    def get_folder(self, **kwargs):
        """ Retrieves one or more folder from Google Drive. This function
            will return folders and ONLY folders since it appends
                "and mimeType = 'application/vnd.google-aps.folder'
            to any query.

            If you wish to retrieve both folders and files, please use the
            get_file() method.
    
            Args:
            **kwargs: Accepts any query parameters that are valid Google Drive
                      SDK requests.
                      
                      Equal values can be requested by simply using the normal 
                      params
                      
                      Fields that require keyword operators such as contains,
                      in, or greater than/less than/equal to operators will 
                      use the following syntax:
   
                        field_operator=VALUE
                      
                      For example, if you wish to query for all files that have
                      the word "blue" in them you would use the folowing 
                      parameter:
                        
                        title_contains="blue"
 
       Returns:
            
            GDriveFile objects (namedtuples) so that the returned results can
            be accessed as typical objects.

        """
        # Parse kwargs to ensure they're valid
        logging.debug("Getting folder, options passed in: " 
        + str(kwargs)) 
        tokens = self.parser.parse(**kwargs)
        query = self.construct_query(tokens)
        query['q'] += (" and mimeType = "
        "'application/vnd.google-apps.folder'")
        logging.info("Final query is: " + str(query))
        folders = self.drive_service.files().list(**query).execute()
        return self.create_gdrive_files(folders['items'])

    def get_file_info(self, **kwargs):
        """ Retrieves one or more files from Google Drive

        Args:
            **kwargs: Accepts any query parameters that are valid Google Drive
                      SDK requests.
                      
                      Equal values can be requested by simply using the normal 
                      params
                      
                      Fields that require keyword operators such as contains,
                      in, or greater than/less than/equal to operators will 
                      use the following syntax:
   
                        field_operator=VALUE
                      
                      For example, if you wish to query for all files that have
                      the word "blue" in them you would use the folowing 
                      parameter:
                        
                        title_contains="blue"
        Returns:
            
            GDriveFile objects (namedtuples) so that the returned results can
            be accessed as typical objects.

        """
        logging.debug("Getting file, options passed in: "
        + str(kwargs))
        tokens = self.parser.parse(**kwargs)
        query = self.construct_query(tokens)
        logging.info("Final query is: " + str(query))
        files = self.drive_service.files().list(**query).execute()
        return self.create_gdrive_files(files['items'])

    
    def get_folder_contents(self, folder_id, **kwargs):
        """ Retrieves one or more files from Google Drive which reside in the 
            folder with the specified id.

            This method is a shorthand for the method 
                get_file(parents_in=[FOLDER_ID]

        Args:
            **kwargs: Accepts any query parameters that are valid Google Drive
                      SDK requests.
                      Equal values can be requested by simply using the normal 
                      params
                      
                      Fields that require keyword operators such as contains,
                      in, or greater than/less than/equal to operators will 
                      use the following syntax:

                        field_operator=VALUE
                      
                      For example, if you wish to query for all files that have
                      the word "blue" in them you would use the folowing 
                      parameter:
                        
                        title_contains="blue"
        Returns:
            
            GDriveFile objects (namedtuples) so that the returned results can
            be accessed as typical objects.

        """
        kwargs['parents_in'] = folder_id
        return self.get_file_info(**kwargs) 

    def upload_file(self, filepath, convert=None, 
            useContentAsIndexableText=None,
            visibility=None, ocrLanguage=None, 
            ocr=None, timedTextLanguage=None, 
            timedTextTrackName=None, pinned=None, **kwargs):
        """ Uploads a file

            Args:
                filepath: Path of file to upload, String
                
                The following has been copied from: 
                https://developers.google.com/drive/v2/reference/files/insert
                
                convert: boolean,  Whether to convert this file to the 
                    corresponding Google Docs format. (Default: false)
                
                ocr: boolean Whether to attempt OCR on .jpg, .png, .gif, 
                    or .pdf uploads. (Default: false)
                
                ocrLanguage:	string	 If ocr is true, hints at the 
                    language to use. Valid values are ISO 639-1 codes.
                
                pinned:	boolean	 Whether to pin the head revision of 
                    the uploaded file. (Default: false)
                
                timedTextLanguage:	string	 The language of the timed text.
                
                timedTextTrackName:	string	 The timed text track name.
                
                useContentAsIndexableText:	boolean	 Whether to use the 
                    content as indexable text. (Default: false)
                
                visibility:	string	 The visibility of the new file. 
                    This parameter is only relevant when convert=false.
            
            Keyword Args:
                kwargs are based on the request body parameters

                description: string	A short description of the file.		
                
                lastViewedByMeDate:	datetime	Last time this 
                    file was viewed by the user (formatted RFC 3339 timestamp).	
                
                mimeType: string	The MIME type of the file. This is only 
                    mutable on update when uploading new content. This field can 
                    be left blank, and the mimetype will be determined from the 
                    uploaded content's MIME type.	
                
                modifiedDate: datetime	Last time this file was modified by anyone 
                    (formatted RFC 3339 timestamp). This is only mutable on 
                    update when the setModifiedDate parameter is set.	
                
                parents[]: list	Collection of parent folders which contain this
                    file.
                
                title:	string	The title of the this file. Used to identify 
                    file or folder name.
        """
        pass
    def download_file(self, id=None, **kwargs):
        """ Retrieves the contents of the specified file
           
            Arguments:
                id: ID of the file to retrieve
            
            kwargs:
                Valid Google Drive queries

            Raises:
                ValueError: Multiple files were found, query was not specific
                            enough

                IOError: Google returned a 404 for the specified file ID,
                         the file could not be found.
        """
        if not id:
            # An ID was not specified, so retrieve the file using the query
            file = self.get_file_info(**kwargs)
            if len(file) > 1:
                raise ValueError("""Multiple files were found, please retry
                    with a more specific query""")
            id = file[0].id
        # Download the file
        gdrive_file = self.drive_service.files().get(fileId=id).execute()
        # Determine if there was a rreturn or if a downloadURL exists
        try:
            url = gdrive_file['downloadUrl']
        except KeyError:
            # Let the user know the file couldn't be found
            raise IOError("File with id " + str(id) + " could not be found")
        # Grab contents of the file
        resp, content = self.drive_service._http.request(url)
        if resp.status != 200:
            # If a 404 or something else was raised, let the user know
            raise IOError("File could not be found: %s" % resp)
        # Return the content of the file
        return content

    def construct_value(self, value):
        """ Constructs a valid value for a query, will join ParseResults
        together so that all words will be apart of the value

        Args:
            value: String, list, or ParseResults of words to be joined

        Returns:
            A value contained in single quotes
        """
        query = "'"
        if type(value) is ParseResults:
            query += " ".join(value)
        else:
            query += value
        query += "'"
        return query

    def construct_query(self, tokens):
        """ Constructs a valid Google Drive SDK query
        
        Some notes:
            If the operator is "in", the query is constructed using the syntax
            
                <value> in <field>

            If the operator is a contains, =, <, <=, >, >= the query is simply
            constructed using the syntax:

                <field> <operator> <value>

        Args:
            tokens: A list of tokens which have the fields:
                    field, value, and operator

        Returns:
            A dictionary with the key "q" containing a valid 
            Google Drive SDK query.

        """
        query = ""
        token_length = len(tokens)
        for token, x in zip(tokens, xrange(token_length)):
            logging.debug("Constructing query string for token: "
            + str(token))
            if token.operator == "in":
                """ When operator is 'in' query is composed as 
                    <value> in <field> """
                query += "%s in %s" % (
                    self.construct_value(token.value),
                    token.field)
            else:
                query += " ".join([token.field,  token.operator,
                    self.construct_value(token.value)])
            if(x+1 < token_length):
                query += " and "
        return {"q": query}

class GDriveAPIParser(object):

    def __init__(self):
        self.op_map = {
            'lte': '<=', 
            'lt':  '<',
            'gt':  '>',
            'gte': '>=',
            '=':   '=',
        }
        self.fields_ops = {
            'title': ['contains', '='],
            'fullText': ['contains'],
            'mimeType': ['='],
            'modifiedDate': self.op_map.keys(),
            'lastViewedByMeDate': self.op_map.keys(),
            'trashed': ['='],
            'starred': ['='],
            'hidden': ['='],
            'parents': ['in'],
            'owners': ['in'],
            'writers': ['in'],
            'readers': ['in'],
        }
        fields = Word(" ".join(self.fields_ops.keys()))
        operators = Word("contains in lte lt gt gte")
        values = Word(alphanums + " ").leaveWhitespace()
        self.grammars = {
            # Defines grammar for queries such as title__contais="[title]"
            fields("field") + "_" + operators("operator") + "=" + OneOrMore(values)("value"),
            # Defines grammars for simple equals like, starred=True
            fields("field") + "=" + values("value")
        }
    
    def parse(self, **kwargs):
        """ Determines if user's queries are valid

        Args:
            **kwargs: Dictionary where the keys follow the convention 
                field__operator

        Returns:
            A list of pyparsing.ParseResult: Each ParseResult object has the
                following fields available:
                tokens.field
                tokens.operator
                tokens.value
        """
        token_list = []
        for query,val in kwargs.items():
            full_query  = query + "="
            if type(val) is datetime:
                full_query += val.isoformat()
            else:
                full_query += val
            logging.debug("Parsing query: " + full_query)
            # Try each of the grammars
            for grammar in self.grammars:
                try:
                    # Use only correct parses
                    tokens = grammar.parseString(full_query)
                    # Determine if this is a valid operator for this field
                    if not tokens.operator:
                        # Operator is an equal sign =
                        tokens.operator = '='
                    # Determine if the operator is valid
                    if not tokens.operator in self.fields_ops[tokens.field]:
                        raise ValueError("Field " + tokens.field 
                            + " does not have operator " + tokens.operator)
                    # If the passed in field was a date field
                    if('modifiedDate' == tokens.field or 
                        'lastViewedByMeDate' == tokens.field):
                        logging.debug("Performing date localizations")
                        # Replace operator word with actual operator
                        tokens.operator = self.op_map[tokens.operator] 
                        # Perform some localization and string conversion
                        localized_date = utc.localize(val)
                        # Replace current value with the UTC string value
                        tokens.value = localized_date.isoformat()
                    token_list.append(tokens)
                except ParseException:
                    # Ignore incorrect parsers
                    logging.debug("query " + full_query + " did not pass "
                    + "grammar " + str(grammar))
                    pass
        return token_list 
