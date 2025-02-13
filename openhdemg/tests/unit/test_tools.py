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

WARNING!!! - UNTESTED FUNCTIONS: showselect
"""


import unittest
from openhdemg.tests.unit.functions_for_unit_test import (
    get_directories as getd, validate_emgfile_content,
    validate_emg_refsig_content,
)
from openhdemg.library.openfiles import (
    emg_from_samplefile, refsig_from_otb, emg_from_delsys,
)
from openhdemg.library.tools import (
    showselect, create_binary_firings, mupulses_from_binary, resize_emgfile,
    compute_idr, delete_mus, delete_empty_mus, sort_mus, compute_covsteady,
    filter_rawemg, filter_refsig, remove_offset, get_mvc, compute_rfd,
    compute_svr,
)
import pandas as pd
import numpy as np
import scipy
import copy


class TestTools(unittest.TestCase):
    """
    Test the functions/classes in the tools module.
    """

    def setUp(self):
        """
        Initialize variables for each test.

        This method is called before each test function runs.
        """

        # Load the decomposed samplefile
        self.emgfile = emg_from_samplefile()

    def test_create_binary_firings(self):
        """
        Test the create_binary_firings function.
        """

        res = create_binary_firings(
            emg_length=self.emgfile["EMG_LENGTH"],
            number_of_mus=self.emgfile["NUMBER_OF_MUS"],
            mupulses=self.emgfile["MUPULSES"],
        )

        self.assertIsInstance(res, pd.DataFrame)
        self.assertTrue(res.shape[0] == self.emgfile["EMG_LENGTH"])
        self.assertTrue(res.shape[1] == self.emgfile["NUMBER_OF_MUS"])
        for column in res.columns:
            self.assertTrue(pd.api.types.is_integer_dtype(res[column]))
        self.assertTrue(res.min().min() == 0)
        self.assertTrue(res.max().max() == 1)

    def test_mupulses_from_binary(self):
        """
        Test the mupulses_from_binary function.
        """

        res = mupulses_from_binary(
            binarymusfiring=self.emgfile["BINARY_MUS_FIRING"]
        )

        self.assertIsInstance(res, list)
        self.assertIsInstance(res[0], np.ndarray)
        self.assertTrue(len(res) == self.emgfile["NUMBER_OF_MUS"])
        for pulses in res:
            self.assertEqual(pulses.dtype, int)
            self.assertTrue(
                np.min(pulses) >= 0 and
                np.max(pulses) < self.emgfile["EMG_LENGTH"]
            )

    def test_resize_emgfile(self):
        """
        Test the resize_emgfile function.
        """

        # Test the emgfile
        # Test multiple resizing and resizing outside the real area
        areas = [
            [10000, 30000],
            [-10, self.emgfile["EMG_LENGTH"] + 10],
            [5000, 10000]
        ]

        for area in areas:
            for accuracy in ["recalculate", "maintain"]:
                rs_emgfile, start_, end_ = resize_emgfile(
                    self.emgfile,
                    area=area,
                    how="ref_signal",
                    accuracy=accuracy,
                    ignore_negative_ipts=False,
                )

                validate_emgfile_content(self, self.emgfile)

        # Test the refsig_emgfile
        refsig_emgfile = refsig_from_otb(
            filepath=getd("library", "otb", "OTB_R.mat"),
        )

        rs_emgfile, start_, end_ = resize_emgfile(
                    refsig_emgfile,
                    area=areas[0],
                )

        validate_emg_refsig_content(self, rs_emgfile)

    def test_compute_idr(self):
        """
        Test the compute_idr function.
        """

        res = compute_idr(self.emgfile)

        self.assertIsInstance(res, dict)
        self.assertTrue(len(res.keys()) == self.emgfile["NUMBER_OF_MUS"])
        self.assertTrue(np.isnan(res[0]["idr"][0]))
        self.assertAlmostEqual(res[0]["idr"][1], 1.227082, places=6)
        # Use np.isclose for floating point comparison, ignoring NaN values
        comparison = np.isclose(
            self.emgfile["FSAMP"] / res[0]["diff_mupulses"],
            res[0]["idr"],
            equal_nan=True,
        )
        # Assert that all values are close (or NaN in both)
        self.assertTrue(comparison.all())

    def test_delete_mus(self):
        """
        Test the delete_mus function.
        """

        # Progressively delete all the MUs except 1
        res = copy.deepcopy(self.emgfile)
        for _ in range(self.emgfile["NUMBER_OF_MUS"]):
            res = delete_mus(
                res,
                munumber=0,
                if_single_mu="ignore",
            )
            if res["NUMBER_OF_MUS"] > 1:
                validate_emgfile_content(self, res)
            elif res["NUMBER_OF_MUS"] == 1:
                self.assertTrue(res["NUMBER_OF_MUS"] == 1)
                self.assertTrue(res["ACCURACY"].shape == (1, 1))
                self.assertTrue(res["IPTS"].shape == (res["EMG_LENGTH"], 1))
                self.assertTrue(len(res["MUPULSES"]) == 1)
                self.assertTrue(
                    res["BINARY_MUS_FIRING"].shape == (res["EMG_LENGTH"], 1)
                )
            else:
                raise ValueError(
                    "With if_single_mu='ignore', all MUs have been removed."
                )

        # Progressively delete all the MUs
        res = copy.deepcopy(self.emgfile)
        for _ in range(self.emgfile["NUMBER_OF_MUS"]):
            res = delete_mus(
                res,
                munumber=0,
                if_single_mu="remove",
            )
            if res["NUMBER_OF_MUS"] > 1:
                validate_emgfile_content(self, res)
            elif res["NUMBER_OF_MUS"] == 1:
                self.assertTrue(res["NUMBER_OF_MUS"] == 1)
                self.assertTrue(res["ACCURACY"].shape == (1, 1))
                self.assertTrue(res["IPTS"].shape == (res["EMG_LENGTH"], 1))
                self.assertTrue(len(res["MUPULSES"]) == 1)
                self.assertTrue(
                    res["BINARY_MUS_FIRING"].shape == (res["EMG_LENGTH"], 1)
                )
            else:
                self.assertTrue(res["NUMBER_OF_MUS"] == 0)
                self.assertTrue(res["ACCURACY"].empty)
                self.assertTrue(res["IPTS"].empty)
                self.assertTrue(len(res["MUPULSES"][0]) == 0)
                self.assertTrue(res["BINARY_MUS_FIRING"].empty)

        # Test passing a list of MUs to munumber
        res = copy.deepcopy(self.emgfile)
        res = delete_mus(
            res,
            munumber=[*range(res["NUMBER_OF_MUS"])],
        )

        self.assertTrue(res["NUMBER_OF_MUS"] == 0)
        self.assertTrue(res["ACCURACY"].empty)
        self.assertTrue(res["IPTS"].empty)
        self.assertTrue(len(res["MUPULSES"][0]) == 0)
        self.assertTrue(res["BINARY_MUS_FIRING"].empty)

        res = copy.deepcopy(self.emgfile)
        res = delete_mus(
            res,
            munumber=[*range(res["NUMBER_OF_MUS"] - 1)],
            if_single_mu="ignore",
        )

        self.assertTrue(res["NUMBER_OF_MUS"] == 1)
        self.assertTrue(res["ACCURACY"].shape == (1, 1))
        self.assertTrue(res["IPTS"].shape == (res["EMG_LENGTH"], 1))
        self.assertTrue(len(res["MUPULSES"]) == 1)
        self.assertTrue(
            res["BINARY_MUS_FIRING"].shape == (res["EMG_LENGTH"], 1)
        )

        # Test delete_delsys_muaps
        res = emg_from_delsys(
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

        res = delete_mus(
            res,
            munumber=[*range(res["NUMBER_OF_MUS"])],#[0, 3, 5, 7],
            if_single_mu="ignore",
            delete_delsys_muaps=True,
        )

        self.assertTrue(len(res["EXTRAS"].columns) == res["NUMBER_OF_MUS"] * 4)

    def test_delete_empty_mus(self):
        """
        Test the delete_empty_mus function.
        """

        emgfile = copy.deepcopy(self.emgfile)

        emgfile["MUPULSES"][0] = np.empty(0)

        res = delete_empty_mus(emgfile)

        self.assertTrue(res["NUMBER_OF_MUS"] == 4)
        validate_emgfile_content(self, res)

    def test_sort_mus(self):
        """
        Test the sort_mus function.
        """

        res = sort_mus(self.emgfile)

        for mu in range(1, res["NUMBER_OF_MUS"]):
            self.assertTrue(
                res["MUPULSES"][mu][0] > res["MUPULSES"][mu-1][0]
            )
        validate_emgfile_content(self, res)

    def test_compute_covsteady(self):
        """
        Test the compute_covsteady function.
        """

        # Ramps duration
        t_ramps = 10 * self.emgfile["FSAMP"]

        res = compute_covsteady(
            self.emgfile,
            start_steady=0 + t_ramps,
            end_steady=self.emgfile["EMG_LENGTH"] - t_ramps,
        )

        self.assertAlmostEqual(res, 1.3167753, places=6)

    def test_filter_rawemg(self):
        """
        Test the filter_rawemg function.
        """

        lc, hc = 20, 500
        res = filter_rawemg(
            self.emgfile,
            order=2,
            lowcut=lc,
            highcut=hc,
        )

        f, S = scipy.signal.welch(
            self.emgfile["RAW_SIGNAL"][0].to_numpy(),
            self.emgfile["FSAMP"],
            nperseg=256,
        )
        rms_unfiltered = np.sqrt(np.mean(S[(f < lc) | (f > hc)]**2))

        f, S = scipy.signal.welch(
            res["RAW_SIGNAL"][0].to_numpy(),
            self.emgfile["FSAMP"],
            nperseg=256,
        )
        rms_filtered = np.sqrt(np.mean(S[(f < lc) | (f > hc)]**2))

        self.assertTrue(rms_filtered < rms_unfiltered)

    def test_filter_refsig(self):
        """
        Test the filter_refsig function.
        """

        f, S = scipy.signal.welch(
            self.emgfile["REF_SIGNAL"][0].to_numpy(),
            self.emgfile["FSAMP"],
            nperseg=256,
        )

        # Calculate RMS value
        rms_unfiltered = np.sqrt(np.mean(S[f > 15]**2))

        res = filter_refsig(self.emgfile, order=4, cutoff=15)

        f, S = scipy.signal.welch(
            res["REF_SIGNAL"][0].to_numpy(),
            self.emgfile["FSAMP"],
            nperseg=256,
        )

        rms_filtered = np.sqrt(np.mean(S[f > 15]**2))

        self.assertTrue(rms_filtered < rms_unfiltered)

    def test_remove_offset(self):
        """
        Test the remove_offset function.
        """

        # Test auto
        res = remove_offset(self.emgfile, auto=round(self.emgfile["FSAMP"] / 2))

        self.assertAlmostEqual(
            res["REF_SIGNAL"][0: round(self.emgfile["FSAMP"] / 2)].mean()[0],
            0,
            places=3,
        )

        # Test offsetval
        res = remove_offset(res, offsetval=1)

        self.assertAlmostEqual(
            res["REF_SIGNAL"][0: round(self.emgfile["FSAMP"] / 2)].mean()[0],
            -1,
            places=3,
        )

    def test_get_mvc(self):
        """
        Test the get_mvc function.
        """

        res = get_mvc(self.emgfile, how="all")

        self.assertAlmostEqual(res, 27.170013427734375, places=6)

        # Test conversion_val
        res = get_mvc(self.emgfile, how="all", conversion_val=9.81)

        self.assertAlmostEqual(res, 266.5378317260742, places=6)

    def test_compute_rfd(self):
        """
        Test the compute_rfd function.
        """

        res = compute_rfd(
            self.emgfile,
            ms=[50, 100, 150, 200],
            startpoint=1683,
            conversion_val=0,
        )

        expected_values = np.array([4.760742, 3.768921, 4.760742, 4.66156])

        self.assertTrue(np.allclose(expected_values, res.values[0], atol=1e-5))

    def test_compute_svr(self):
        """
        Test the compute_svr function.
        """

        # TODO these tests need to be expanded to assess all the parameters
        # and their values

        # Test initial discontonuity and output dimensionality
        emgfile = emg_from_samplefile()
        emgfile["MUPULSES"][1] = np.insert(
            arr=emgfile["MUPULSES"][1],
            obj=0,
            values=int(emgfile["MUPULSES"][1][0] - emgfile["FSAMP"] * 2),
        )  # 2 sec discontinuity at the beginning on MU 1

        res = compute_svr(self.emgfile, discontfiring_dur=1)

        self.assertSetEqual(set(res.keys()), {'svrfit', 'svrtime', 'gensvr'})
        for fits in res.values():
            self.assertIsInstance(fits, list)
            self.assertEqual(len(fits), self.emgfile["NUMBER_OF_MUS"])
            for mu_fit in fits:
                self.assertIsInstance(mu_fit, np.ndarray)
                self.assertEqual(mu_fit.ndim, 1)


if __name__ == '__main__':
    unittest.main()
