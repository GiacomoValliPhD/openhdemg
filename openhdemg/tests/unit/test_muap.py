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

WARNING!!! - UNTESTED FUNCTIONS: Tracking_gui, MUcv_gui
"""


import unittest
from openhdemg.tests.unit.functions_for_unit_test import (
    get_directories as getd,
)
from openhdemg.library.openfiles import emg_from_samplefile, emg_from_delsys
from openhdemg.library.electrodes import sort_rawemg
from openhdemg.library.tools import delete_mus
from openhdemg.library.muap import (
    diff, double_diff, extract_delsys_muaps, sta, st_muap, unpack_sta,
    pack_sta, align_by_xcorr, tracking, Tracking_gui,
    remove_duplicates_between, xcc_sta, estimate_cv_via_mle, MUcv_gui,
)
import numpy as np
import pandas as pd
from time import time
import copy


class TestMuap(unittest.TestCase):
    """
    Test the functions/classes in the muap module.
    """

    def setUp(self):
        """
        Initialize variables for each test.

        This method is called before each test function runs.
        """

        # Load the decomposed samplefile
        self.emgfile = emg_from_samplefile()

        self.custom_sorting_order = [
            [63, 62, 61,     60, 59, 58, np.nan, 56, 55, 54, 53, 52,     51,],
            [38, 39, 40,     41, 42, 43,     44, 45, 46, 47, 48, 49,     50,],
            [37, 36, 35, np.nan, 33, 32,     31, 30, 29, 28, 27, 26,     25,],
            [12, 13, 14,     15, 16, 17,     18, 19, 20, 21, 22, 23,     24,],
            [11, 10,  9,      8, 7,  6,       5,  4,  3,  2,  1,  0, np.nan,],
        ]

        self.sorted_rawemg = sort_rawemg(
            self.emgfile,
            code="Custom order",
            dividebycolumn=True,
            custom_sorting_order=self.custom_sorting_order,
        )

    def test_diff(self):
        """
        Test the diff function.
        """

        res = diff(self.sorted_rawemg)
        self.assertAlmostEqual(res["col0"][1][0], 7.120769, places=6)
        self.assertTrue(np.isnan(res["col2"][29][0]))

    def test_double_diff(self):
        """
        Test the double_diff function.
        """

        res = double_diff(self.sorted_rawemg)
        self.assertAlmostEqual(res["col0"][2][0], -17.293295, places=6)
        self.assertTrue(np.isnan(res["col2"][29][0]))

    def test_extract_delsys_muaps(self):
        """
        Test the extract_delsys_muaps function.
        """

        # Load decomposed file with multiple MUs, reference signal and MUAPs
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

        res = extract_delsys_muaps(emgfile)
        self.assertIsInstance(res, dict)
        self.assertIsInstance(res[0], dict)
        self.assertIsInstance(res[0]["col0"], pd.DataFrame)
        self.assertAlmostEqual(
            res[0]["col0"][0][75], 8.39528411233914e-07, places=6,
        )

    def test_sta(self):
        """
        Test the sta function.
        """

        res = sta(
            self.emgfile,
            sorted_rawemg=self.sorted_rawemg,
            firings=[0, 50],
            timewindow=50,
        )

        self.assertIsInstance(res, dict)
        self.assertIsInstance(res[0], dict)
        self.assertIsInstance(res[0]["col0"], pd.DataFrame)
        self.assertAlmostEqual(res[0]["col0"][0][0], -6.154379, places=6)
        self.assertTrue(np.isnan(res[0]["col2"][29][0]))

    def test_st_muap(self):
        """
        Test the st_muap function.
        """

        res = st_muap(
            self.emgfile,
            sorted_rawemg=self.sorted_rawemg,
            timewindow=50,
        )

        self.assertIsInstance(res, dict)
        self.assertIsInstance(res[0], dict)
        self.assertIsInstance(res[0]["col0"], dict)
        self.assertIsInstance(res[0]["col0"][0], pd.DataFrame)
        self.assertAlmostEqual(res[0]["col0"][0][0][0], 57.9834, places=4)
        self.assertTrue(np.isnan(res[0]["col2"][29][0][0]))

    def test_unpack_sta_and_pack_sta(self):
        """
        Test the unpack_sta and pack_sta functions.
        """

        sta_ = sta(
            self.emgfile,
            sorted_rawemg=self.sorted_rawemg,
            firings=[0, 50],
            timewindow=50,
        )

        unpacked_sta, sta_keys = unpack_sta(sta_mu=sta_[0])

        packed_sta = pack_sta(df_sta=unpacked_sta, keys=sta_keys)

        self.assertIsInstance(sta_[0], dict)
        self.assertIsInstance(packed_sta, dict)
        self.assertTrue(sta_[0]["col0"].equals(packed_sta["col0"]))

    def test_align_by_xcorr(self):
        """
        Test the align_by_xcorr function.
        """

        sta_ = sta(
            self.emgfile,
            sorted_rawemg=self.sorted_rawemg,
            firings=[0, 50],
            timewindow=50,
        )

        res1, res2 = align_by_xcorr(
            sta_mu1=sta_[0],
            sta_mu2=sta_[0], 
            finalduration=0.5,
        )

        self.assertAlmostEqual(res1["col0"][0][0], -36.387123, places=6)
        self.assertAlmostEqual(res2["col0"][0][0], -36.366776, places=6)

    def test_tracking(self):
        """
        Test the tracking funtion.
        """

        # Check parallel processing
        t0 = time()
        res = tracking(
            emgfile1=self.emgfile,
            emgfile2=self.emgfile,
            firings="all",
            derivation="sd",
            timewindow=50,
            threshold=0.8,
            matrixcode="GR08MM1305",
            orientation=180,
            n_rows=None,
            n_cols=None,
            custom_sorting_order=None,
            custom_muaps=None,
            exclude_belowthreshold=True,
            filter=True,
            multiprocessing=True,
            show=False,
            gui=False,
        )
        time_parallel = time() - t0

        t0 = time()
        res = tracking(
            emgfile1=self.emgfile,
            emgfile2=self.emgfile,
            firings="all",
            derivation="sd",
            timewindow=50,
            threshold=0.8,
            matrixcode="GR08MM1305",
            orientation=180,
            n_rows=None,
            n_cols=None,
            custom_sorting_order=None,
            custom_muaps=None,
            exclude_belowthreshold=True,
            filter=True,
            multiprocessing=False,
            show=False,
            gui=False,
        )
        time_serial = time() - t0

        self.assertTrue(time_serial > time_parallel)

        # Test derivations
        for der in ["mono", "sd", "dd"]:
            res = tracking(
                emgfile1=self.emgfile,
                emgfile2=self.emgfile,
                firings="all",
                derivation=der,
                timewindow=50,
                threshold=0.8,
                matrixcode="GR08MM1305",
                orientation=180,
                n_rows=None,
                n_cols=None,
                custom_sorting_order=None,
                custom_muaps=None,
                exclude_belowthreshold=True,
                filter=True,
                multiprocessing=True,
                show=False,
                gui=False,
            )

            self.assertTrue(len(res) == 5)
            self.assertTrue(res["XCC"].mean() > 0.99)

        # Test filter, firings and timewindow
        res = tracking(
            emgfile1=self.emgfile,
            emgfile2=self.emgfile,
            firings=[0, 100],
            derivation="sd",
            timewindow=80,
            threshold=0.6,
            matrixcode="GR08MM1305",
            orientation=180,
            n_rows=None,
            n_cols=None,
            custom_sorting_order=None,
            custom_muaps=None,
            exclude_belowthreshold=True,
            filter=False,
            multiprocessing=True,
            show=False,
            gui=False,
        )

        self.assertTrue(len(res) == 15)
        self.assertAlmostEqual(res["XCC"][1], 0.623405, places=6)

        # Test custom_muaps
        # Load decomposed file with multiple MUs, reference signal and MUAPs
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
        delsys_muaps = extract_delsys_muaps(emgfile)

        res = tracking(
            emgfile1=emgfile,
            emgfile2=emgfile,
            threshold=0.6,
            custom_muaps=delsys_muaps,
            exclude_belowthreshold=True,
            filter=True,
            multiprocessing=True,
            show=False,
            gui=False,
        )

        self.assertTrue(len(res) == 38)
        self.assertTrue(res["XCC"].mean() > 0.99)

    def test_remove_duplicates_between(self):
        """
        Test the remove_duplicates_between function.
        """

        # Prepare different emgfiles
        emgfile1_less_mus = delete_mus(self.emgfile, munumber=0)
        emgfile2_noisy = copy.deepcopy(self.emgfile)
        emgfile2_noisy["ACCURACY"].iloc[0, 0] = 0.6
        emgfile2_noisy["ACCURACY"].iloc[1, 0] = 0.6

        # Test which
        res1, res2, tracking_res = remove_duplicates_between(
            emgfile1=emgfile1_less_mus,
            emgfile2=self.emgfile,
            gui=False,
            which="munumber",
        )
        self.assertTrue(res1["NUMBER_OF_MUS"] == 4)
        self.assertTrue(res2["NUMBER_OF_MUS"] == 1)

        res1, res2, tracking_res = remove_duplicates_between(
            emgfile1=self.emgfile,
            emgfile2=emgfile2_noisy,
            gui=False,
            which="accuracy",
        )
        self.assertTrue(res1["NUMBER_OF_MUS"] == 2)
        self.assertTrue(res2["NUMBER_OF_MUS"] == 3)

    def test_xcc_sta(self):
        """
        Test the xcc_sta function.
        """

        sta_ = sta(
            self.emgfile,
            sorted_rawemg=self.sorted_rawemg,
            firings=[0, 50],
            timewindow=50,
        )

        res = xcc_sta(sta=sta_)

        self.assertIsInstance(res, dict)
        self.assertIsInstance(res[0], dict)
        self.assertIsInstance(res[0]["col0"], pd.DataFrame)
        self.assertTrue(np.isnan(res[0]["col0"][0][0]))
        self.assertAlmostEqual(res[0]["col0"][1][0], 0.982674, places=6)
        self.assertTrue(np.isnan(res[0]["col0"][6][0]))

    def test_estimate_cv_via_mle(self):
        """
        Test the estimate_cv_via_mle function.
        """

        dd = double_diff(sorted_rawemg=self.sorted_rawemg)
        sta_ = sta(
            emgfile=self.emgfile,
            sorted_rawemg=dd,
            firings=[0, 50],
            timewindow=50,
        )

        signal = sta_[0]["col2"].loc[:, 32:36]
        res = estimate_cv_via_mle(emgfile=self.emgfile, signal=signal)

        self.assertAlmostEqual(res, 4.3530717224189805, places=6)


if __name__ == '__main__':
    unittest.main()
