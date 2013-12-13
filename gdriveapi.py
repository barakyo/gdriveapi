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
        self.parser = GDriveAPIParser()
    
    def authenticate(self, client_id, client_secret, scopes, redirect_url):
        """ Authenticates the user for the application they've provided give
        the credentials.

        client_id: Your application's client_id
        client_secret: Your application's client secret
        scopes: A list of scopes that you want your application to use
        redirect_url: The redirect_url for your application

        """
        flow = OAuth2WebServerFlow(client_id, client_secret, scopes, redirect_url)
        if not self.credentials:
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

        Constructs namedtuples after the keys of the first file in the list
        
        Args:
            files - The items list of a successful response, that is
                    response['items']

        Returns:
            A list of GDriveFiles
        """
        GDriveFile = namedtuple('GDriveFile', files[0].keys())
        return [GDriveFile(**f) for f in files]
 
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

    def get_file(self, **kwargs):
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
        return self.get_file(**kwargs) 

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
        self.fields_ops = {
            'title': ['contains', '='],
            'fullText': ['contains'],
            'mimeType': ['='],
            'modifiedDate': ['lte', 'lt', '=', 'gt', 'gte'],
            'lastViewedByMeDate': ['lte', 'lt', '=', 'gt', 'gte'],
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
            full_query  = query + "=" + val
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
                    if not tokens.operator in self.fields_ops[tokens.field]:
                        raise ValueError("Field " + tokens.field 
                            + " does not have operator " + tokens.operator)
                    token_list.append(tokens)
                except ParseException:
                    # Ignore incorrect parsers
                    logging.debug("query " + full_query + " did not pass "
                    + "grammar " + str(grammar))
                    pass
        return token_list 
