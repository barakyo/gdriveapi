# GDriveAPI #

## Simplify interacting with the Google Drive API ##

GDriveAPI is a Python library to simplify your life when it comes to interacting with the Google Drive API. The library provides easy to use set of functions to construct queries for searching and retrieving files from Google Drive. In addition, returned items from Google Drive are converted to GDriveFile objects allowing you natively interact with them as you would other Python objects.

## Getting Started ##
To get started, import the GDriveAPI:

    from gdriveapi import GDriveAPI

You can insantiate a GDriveAPI object through one of two way.

### Google Drive Credentials Storage File ##
If you've already gone through the OAuth process before and generated a credentials file, you can simply load that file to instantiate a GDriveAPI object.

    from gdriveapi import GDriveAPI
    gdrive = GDriveAPI("path/to/credentials")

### OAuth* ###

If you haven't generated a credentials file before, you must instantiate by providing your `client_id`, `client_secret`, a list of `scopes`, and your `redirect_url` to the object.

    from gdriveapi import GDriveAPI
    gdrive = GDriveAPI(client_id="MY_CLIENT_ID", 
        client_secret="MY_CLIENT_SECRET", scopes=[SCOPES], 
        redirect_url="REDIRECT_URL")

Before using the object, you'll need to authorize the request. GDriveAPI will print a URL to the console which you'll need to copy and paste into the console.

** \* OAuth integration is a little tricky since it requires that you navigate to an authorization URL and provide a request token. Using a generated credentials file is a much smoother process. **

## Querying Google Drive ##

The following functions have been made available to provide with easy access to query Google Drive.

 * `get_folder`
 * `get_file_info`
 * `get_folder_contents`
 * `download_file`

All functions accept keyword arguments optionally appended by a valid operator to construct queries. A list of query parameters and their operators can be found in the [Google Drive SDK Documentation](https://developers.google.com/drive/search-parameters). Queries are constructed through the convention of passing a field and a valid parameter with a value to the function. This is easier explained through examples.

### Querying for a file with the file name "My document" ###
    
    from gdriveapi import GDriveAPI
    
    gdrive = GDriveAPI("path/to/credentials")
    files = gdrive.get_file_info(title="My document")
    
### Querying for all files that contain the word document ###

    from gdriveapi import GDriveAPI
    
    gdrive = GDriveAPI("path/to/credentials")
    files = gdrive.get_file_info(title_contains="document")