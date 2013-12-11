import unittest
from gdriveapi import GDriveAPI
from gdriveapi import GDriveAPIParser

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
       self.assertEqual(folder, folder)

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

if __name__ == '__main__':
    unittest.main()     
