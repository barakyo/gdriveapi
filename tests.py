import unittest
from gdriveapi import GDriveAPI

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
            self.gdrive = GDriveAPI()

    def test_invalid_cred_file(self):
        """ Tests that the class fails correctly when an invalid file is 
        passed in """
        with self.assertRaises(ValueError):
            self.gdrive = GDriveAPI("fake_file")

    def test_get_folder(self):
        pass

if __name__ == '__main__':
    unittest.main()     
