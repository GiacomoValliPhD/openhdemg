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
from openhdemg.tests.unit.functions_for_unit_test import (
    get_directories as getd,
)
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
                result = res["col0"]
            else:
                self.assertIsInstance(res, pd.DataFrame)
                result = res
            pd.testing.assert_frame_equal(result, emgfile["RAW_SIGNAL"])

        # Test no sorting
        emgfile = emg_from_demuse(
            filepath=getd("library", "demuse", "DEMUSE_D_R_mMU.mat"),
        )
        for code in [None, "None"]:
            for dividebycolumn in [True, False]:
                res = sort_rawemg(
                    emgfile,
                    code=code,
                    dividebycolumn=dividebycolumn,
                    n_rows=13,
                    n_cols=5,
                )
                if dividebycolumn:
                    self.assertIsInstance(res, dict)
                    self.assertIsInstance(res["col0"], pd.DataFrame)
                    result = pd.concat(res.values(), axis=1)
                else:
                    self.assertIsInstance(res, pd.DataFrame)
                    result = res
                pd.testing.assert_frame_equal(result, emgfile["RAW_SIGNAL"])

        # Load the decomposed samplefile
        emgfile = emg_from_samplefile()

        # Test built in OTB sorting orders
        codes = [
            "GR08MM1305",
            "GR04MM1305",
            "GR10MM0808",
            "HD04MM1305",
            "HD08MM1305",
            "HD05MM0804",
            "HD10MM0804",
            "HD10MM0808",
        ]
        for code in codes:
            test_emgfile = emgfile
            if code in ["HD05MM0804", "HD10MM0804"]:
                test_emgfile = emgfile.copy()
                test_emgfile["RAW_SIGNAL"] = emgfile["RAW_SIGNAL"].iloc[:, :32]

            if code in ["GR08MM1305", "GR04MM1305"]:
                expected_columns, first_channel = 65, 63
            elif code in ["HD04MM1305", "HD08MM1305"]:
                expected_columns, first_channel = 65, 11
            elif code in ["HD05MM0804", "HD10MM0804"]:
                expected_columns, first_channel = 32, 31
            else:
                expected_columns, first_channel = 64, 56

            for orientation in [0, 180]:
                for dividebycolumn in [True, False]:
                    res = sort_rawemg(
                        test_emgfile,
                        code=code,
                        orientation=orientation,
                        dividebycolumn=dividebycolumn,
                    )
                    if dividebycolumn:
                        self.assertIsInstance(res, dict)
                        self.assertIsInstance(res["col0"], pd.DataFrame)
                        result = pd.concat(res.values(), axis=1)
                    else:
                        self.assertIsInstance(res, pd.DataFrame)
                        result = res
                    self.assertEqual(result.shape[1], expected_columns)
                    result_column = 0 if orientation == 0 else -1
                    pd.testing.assert_series_equal(
                        result.iloc[:, result_column],
                        test_emgfile["RAW_SIGNAL"].iloc[:, first_channel],
                        check_names=False,
                    )

        # Test custom sorting orders
        custom_sorting_order = [
            [63, 62, 61,     60, 59, 58, np.nan, 56, 55, 54, 53, 52,     51,],
            [38, 39, 40,     41, 42, 43,     44, 45, 46, 47, 48, 49,     50,],
            [37, 36, 35, np.nan, 33, 32,     31, 30, 29, 28, 27, 26,     25,],
            [12, 13, 14,     15, 16, 17,     18, 19, 20, 21, 22, 23,     24,],
            [11, 10,  9,      8, 7,  6,       5,  4,  3,  2,  1,  0, np.nan,],
        ]
        flattened_order = [
            channel
            for matrix_column in custom_sorting_order
            for channel in matrix_column
        ]
        expected = emgfile["RAW_SIGNAL"].reindex(columns=flattened_order)
        expected.columns = range(expected.shape[1])

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
                result = pd.concat(res.values(), axis=1)
            else:
                self.assertIsInstance(res, pd.DataFrame)
                result = res
            pd.testing.assert_frame_equal(result, expected)

        # Test existing input validation
        with self.assertRaises(ValueError):
            sort_rawemg(emgfile, code="invalid")
        with self.assertRaises(ValueError):
            sort_rawemg(emgfile, code="Custom order")

        for n_rows, n_cols in [
            (None, 5),
            (13, None),
            (13.0, 5),
            (13, 5.0),
            (7, 9),
        ]:
            with self.assertRaises(ValueError):
                sort_rawemg(
                    emgfile,
                    code=None,
                    n_rows=n_rows,
                    n_cols=n_cols,
                )


if __name__ == '__main__':
    unittest.main()
