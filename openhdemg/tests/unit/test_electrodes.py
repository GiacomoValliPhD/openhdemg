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
from openhdemg.library.openfiles import emg_from_delsys, emg_from_demuse
from openhdemg.library.openfiles import emg_from_samplefile
from openhdemg.library.electrodes import sort_rawemg
import pandas as pd
import numpy as np


class TestElectrodes(unittest.TestCase):
    """
    Test the functions/classes in the electrodes module.
    """

    def test_sort_rawemg(self):
        """
        Test the sort_rawemg function.
        """

        # Test built in Delsys sorting orders
        emgfile = emg_from_delsys(
            rawemg_filepath=getd(
                "library",
                ["delsys", "4pin", "DELSYS_D_R_MUAPs_mMU"],
                "Raw_EMG_signal_withFakeRef.mat"
            ),
            mus_directory=getd(
                "library",
                ["delsys", "4pin", "DELSYS_D_R_MUAPs_mMU"],
                "Bicep_Brachii_Motor_Units (Sensor 1)"
            ),
        )
        for dividebycolumn in [True, False]:
            res = sort_rawemg(
                emgfile,
                code="Trigno Galileo Sensor",
                dividebycolumn=dividebycolumn,
            )
            if dividebycolumn:
                self.assertIsInstance(res, dict)
                self.assertIsInstance(res["col0"], pd.DataFrame)
            else:
                self.assertIsInstance(res, pd.DataFrame)

        # Test no sorting
        emgfile = emg_from_demuse(
            filepath=getd("library", "demuse", "DEMUSE_D_R_mMU.mat"),
        )
        for dividebycolumn in [True, False]:
            res = sort_rawemg(
                emgfile,
                code="None",
                dividebycolumn=dividebycolumn,
                n_rows=13,
                n_cols=5,
            )
        if dividebycolumn:
            self.assertIsInstance(res, dict)
            self.assertIsInstance(res["col0"], pd.DataFrame)
        else:
            self.assertIsInstance(res, pd.DataFrame)

        # Load the decomposed samplefile
        emgfile = emg_from_samplefile()

        # Test built in OTB sorting orders
        for code in ["GR08MM1305", "GR04MM1305", "GR10MM0808"]:
            for orientation in [0, 180]:
                for dividebycolumn in [True, False]:
                    res = sort_rawemg(
                        emgfile,
                        code=code,
                        orientation=orientation,
                        dividebycolumn=dividebycolumn,
                    )
                    if dividebycolumn:
                        self.assertIsInstance(res, dict)
                        self.assertIsInstance(res["col0"], pd.DataFrame)
                    else:
                        self.assertIsInstance(res, pd.DataFrame)

        # Test custom sorting orders
        custom_sorting_order = [
            [63, 62, 61,     60, 59, 58, np.nan, 56, 55, 54, 53, 52,     51,],
            [38, 39, 40,     41, 42, 43,     44, 45, 46, 47, 48, 49,     50,],
            [37, 36, 35, np.nan, 33, 32,     31, 30, 29, 28, 27, 26,     25,],
            [12, 13, 14,     15, 16, 17,     18, 19, 20, 21, 22, 23,     24,],
            [11, 10,  9,      8, 7,  6,       5,  4,  3,  2,  1,  0, np.nan,],
        ]
        for dividebycolumn in [True, False]:
            res = sort_rawemg(
                emgfile,
                code="Custom order",
                dividebycolumn=dividebycolumn,
                custom_sorting_order=custom_sorting_order,
            )
            if dividebycolumn:
                self.assertIsInstance(res, dict)
                self.assertIsInstance(res["col0"], pd.DataFrame)
            else:
                self.assertIsInstance(res, pd.DataFrame)


if __name__ == '__main__':
    unittest.main()
