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
from openhdemg.tests.unit.functions_for_unit_test import get_directories as getd

from openhdemg.library.openfiles import emg_from_samplefile

from openhdemg.library.tools import (
    compute_svr,
)

from openhdemg.library.pic import (
    compute_deltaf,
)

import numpy as np


class TestPIC(unittest.TestCase):
    """
    Test the functions/classes in the pic module.
    """

    def test_compute_deltaf(self):
        """
        Test the compute_deltaf function with the samplefile.
        """

        # Load the decomposed samplefile
        emgfile = emg_from_samplefile()

        # Generate smooth discharge rate estimates
        svrfits = compute_svr(emgfile)

        # Default parameters, test_unit_average
        res = compute_deltaf(
            emgfile,
            smoothfits=svrfits["gensvr"],
            average_method="test_unit_average",
            normalisation="False",
            recruitment_difference_cutoff=1.0,
            corr_cutoff=0.7,
            controlunitmodulation_cutoff=0.5,
            clean=True,
        )

        expected_values = [np.nan, 2.709522, 1.838382, np.nan, np.nan]

        for ii in range(len(expected_values)):
            if np.isnan(expected_values[ii]):
                self.assertTrue(np.isnan(res["dF"][ii]))
            else:
                self.assertAlmostEqual(
                    res["dF"][ii], expected_values[ii], places=2,
                )

        # Compute for all MU pairs
        res = compute_deltaf(
            emgfile,
            smoothfits=svrfits["gensvr"],
            average_method="all",
            normalisation="False",
            recruitment_difference_cutoff=1.0,
            corr_cutoff=0.7,
            controlunitmodulation_cutoff=0.5,
            clean=True,
        )

        expected_values = [np.nan, np.nan, np.nan, np.nan, 2.709522, np.nan,
                           np.nan, 2.127461, 1.549303, np.nan]

        for ii in range(len(expected_values)):
            if np.isnan(expected_values[ii]):
                self.assertTrue(np.isnan(res["dF"][ii]))
            else:
                self.assertAlmostEqual(
                    res["dF"][ii], expected_values[ii], places=2,
                )


if __name__ == '__main__':
    unittest.main()
