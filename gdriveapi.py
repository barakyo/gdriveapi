import httplib2
import json
import dataset
import logging
import logging
import pprint

from pyparsing import (Word, alphas, ParseException, OneOrMore, 
    ParseResults, alphanums) 
from apiclient.discovery import build
from apiclient.http import MediaFileUpload
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.file import Storage
from apiclient import errors

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

    def get_folder(self, **kwargs):
        # Parse kwargs to ensure they're valid
        logging.debug("Getting folder, options passed in: " 
        + str(kwargs)) 
        tokens = self.parser.parse(**kwargs)
        query = self.construct_query(tokens)
        query['q'] += (" and mimeType = "
        "'application/vnd.google-apps.folder'")
        logging.info("Final query is: " + str(query))
        return self.drive_service.files().list(**query).execute()

    def get_file(self, **kwargs):
        logging.debug("Getting file, options passed in: "
        + str(kwargs))
        tokens = self.parser.parse(**kwargs)
        query = self.construct_query(tokens)
        logging.info("Final query is: " + str(query))
        return self.drive_service.files().list(**query).execute()

    
    def get_folder_contents(self, folder_id, **kwargs):
        kwargs['parents_in'] = folder_id
        logging.debug("Getting folder contents with options:"
        + str(kwargs))
        tokens = self.parser.parse(**kwargs)
        logging.debug("tokens returned: " + str(tokens))
        query = self.construct_query(tokens)
        logging.info("Final query is: " + str(query))
        return self.drive_service.files().list(**query).execute()

    def construct_value(self, value):
        query = "'"
        if type(value) is ParseResults:
            query += " ".join(value)
        else:
            query += value
        query += "'"
        return query

    def construct_query(self, tokens):
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
