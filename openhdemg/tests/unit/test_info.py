"""
To run the tests using unittest, execute from the openhdemg/tests directory:
    python -m unittest discover

First, you should dowload all the files necessary for the testing and store
them inside openhdemg/tests/fixtures. The files are available at:
https://drive.google.com/drive/folders/1suCZSils8rSCs2E3_K25vRCbN3AFDI7F?usp=sharing

IMPORTANT: Do not alter the content of the dowloaded folder!

WARNING!!! Since the library's functions perform complex tasks and return
complex data structures, these tests can verify that no critical errors occur,
but the accuracy of each function must be assessed independently upon creation,
or at each revision of the code.

WARNING!!! - UNTESTED FUNCTIONS: none
"""


import unittest
from openhdemg.library.openfiles import emg_from_samplefile
from openhdemg.library.info import info


class TestInfo(unittest.TestCase):
    """
    Test the functions/classes in the info module.
    """

    def test_info_methods(self):
        """
        Test the info methods.
        """

        # Load the decomposed samplefile
        emgfile = emg_from_samplefile()

        info().data(emgfile)

        res = info().abbreviations()
        self.assertIsInstance(res, dict)

        res = info().aboutus()
        self.assertIsInstance(res[0], str)
        self.assertIsInstance(res[1], str)

        res = info().contacts()
        self.assertIsInstance(res, dict)

        res = info().links()
        self.assertIsInstance(res, dict)

        res = info().citeus()
        self.assertIsInstance(res, str)


if __name__ == '__main__':
    unittest.main()
