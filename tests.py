import unittest
from gdriveapi import GDriveAPI
from gdriveapi import GDriveAPIParser
from datetime import datetime, timedelta

class GDriveAPITests(unittest.TestCase):
    """ Tests GDriveAPI  for several cases including:

        * Retrieving a folder
        * Retrieving a file
        * Retrieving children of a folder

    """
    def setUp(self):
        # self.gdrive = GDriveAPI("credentials")
        pass

    def test_failed_config(self):
        """ Tests that the class fails correctly when no configuration
        files are provided """
        with self.assertRaises(ValueError):
            gdrive = GDriveAPI()

    def test_invalid_cred_file(self):
        """ Tests that the class fails correctly when an invalid file is 
        passed in """
        with self.assertRaises(ValueError):
            gdrive = GDriveAPI("fake_file")

    def test_get_folder(self):
       gdrive = GDriveAPI("gdrive_credentials")
       folder = gdrive.get_folder(title_contains="Grad School")
       self.assertIsNotNone(folder)

    def test_title_contains(self):
        parser = GDriveAPIParser()
        token_list = ['title', '_', 'contains', '=', 'blue']
        tokens = parser.parse(title_contains="blue")
        for expected, result in zip(token_list, tokens[0]):
            self.assertEqual(expected, result, expected + "!=" + result)

    def test_fulltext_equals(self):
        """ This test should fail since fullText cannot use the = operator """
        parser = GDriveAPIParser()
        with self.assertRaises(ValueError):
            tokens = parser.parse(fullText="blue")

    def test_get_file_contents(self):
        gdrive = GDriveAPI("gdrive_credentials")
        folder = gdrive.get_folder(title_contains="Grad School")
        folder_id = folder[0].id
        files = gdrive.get_folder_contents(folder_id, title="Fall 2013")
        self.assertEqual(files[0].title, "Fall 2013")

    def test_week_old_files(self):
        """ Runs a test to get a list of files that have been modified in
            the last week. 

        Essentially testing that modified date and gt/e and lt/e work
        """
        now = datetime.now()
        one_week_ago = now - timedelta(days=10)
        gdrive = GDriveAPI("gdrive_credentials")
        files = gdrive.get_file_info(title_contains="document", 
                modifiedDate_lt=datetime.now(),
                modifiedDate_gt=one_week_ago)
        self.assertIsNotNone(files)
    
    def test_download_file_by_search(self):
        gdrive = GDriveAPI("gdrive_credentials")
        files = gdrive.get_file_info(title_contains="document")
        # Ensure that files were returned
        self.assertIsNotNone(files)
        try:
            my_document = gdrive.download_file(id=files[0].id)
        except IOError:
            self.assertFalse(True, "File cannot be found")
        else:
            self.assertTrue(True)
     
    def test_upload_file(self):
        gdrive = GDriveAPI("gdrive_credentials")
        file = gdrive.upload_file("test.txt", "Test File", 
                "A test file", "text/Plain")


if __name__ == '__main__':
    unittest.main()     
