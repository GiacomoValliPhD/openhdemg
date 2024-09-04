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
from openhdemg.library.mathtools import (
    min_max_scaling, norm_xcorr, norm_twod_xcorr, compute_sil, compute_pnr,
    derivatives_beamforming, mle_cv_est, find_mle_teta,
)
import numpy as np


class TestMathTools(unittest.TestCase):
    """
    Test the functions/classes in the mathtools module.
    """

    def test_min_max_scaling(self):
        """
        Test the min_max_scaling function.
        """

        # Load the decomposed samplefile
        emgfile = emg_from_samplefile()

        # Test with a pd.Series
        res = min_max_scaling(emgfile["RAW_SIGNAL"][0])
        self.assertAlmostEqual(res.min(), 0, places=0)
        self.assertAlmostEqual(res.max(), 1, places=0)

        # Test with a pd.DataFrame
        res = min_max_scaling(emgfile["RAW_SIGNAL"])
        self.assertAlmostEqual(res.min().min(), 0, places=0)
        self.assertAlmostEqual(res.max().max(), 1, places=0)

    def test_norm_xcorr(self):
        """
        Test the norm_xcorr function.
        """

        # Load the decomposed samplefile
        emgfile = emg_from_samplefile()

        # Change out
        res = norm_xcorr(
            emgfile["RAW_SIGNAL"][0],
            -1*emgfile["RAW_SIGNAL"][1],
            out="both",
        )
        self.assertAlmostEqual(res, -0.986, places=2)

        res = norm_xcorr(
            emgfile["RAW_SIGNAL"][0],
            emgfile["RAW_SIGNAL"][1],
            out="max",
        )
        self.assertAlmostEqual(res, 0.986, places=2)

    def test_norm_twod_xcorr(self):
        """
        Test the norm_twod_xcorr function.
        """

        # Load the decomposed samplefile
        emgfile = emg_from_samplefile()

        # Create a shifted version of the EMG signal
        df = emgfile["RAW_SIGNAL"].iloc[10000:10200, :]
        shifted_df = df.shift(15).fillna(0)

        # Change mode
        res = norm_twod_xcorr(df, shifted_df, mode="full")
        self.assertAlmostEqual(res[1], 0.975, places=2)
        self.assertEqual(res[0].shape, (399, 127))

        res = norm_twod_xcorr(df, shifted_df, mode="valid")
        self.assertAlmostEqual(res[1], -0.358, places=2)
        self.assertEqual(res[0].shape, (1, 1))

        res = norm_twod_xcorr(df, shifted_df, mode="same")
        self.assertAlmostEqual(res[1], 0.975, places=2)
        self.assertEqual(res[0].shape, df.shape)

    def test_compute_sil(self):
        """
        Test the compute_sil function.
        """

        # Load the decomposed samplefile
        emgfile = emg_from_samplefile()

        # Change ignore_negative_ipts
        res = compute_sil(
            ipts=emgfile["IPTS"][0],
            mupulses=emgfile["MUPULSES"][0],
            ignore_negative_ipts=False,
        )
        self.assertAlmostEqual(res, 0.879, places=2)

        res = compute_sil(
            ipts=emgfile["IPTS"][0],
            mupulses=emgfile["MUPULSES"][0],
            ignore_negative_ipts=True,
        )
        self.assertAlmostEqual(res, 0.525, places=2)

        # Thest failure with no or few firings
        res = compute_sil(
            ipts=emgfile["IPTS"][0],
            mupulses=np.empty(0),
            ignore_negative_ipts=False,
        )
        self.assertTrue(np.isnan(res))

        res = compute_sil(
            ipts=emgfile["IPTS"][0],
            mupulses=np.array([10500]),
            ignore_negative_ipts=False,
        )
        self.assertAlmostEqual(res, 1, places=0)

        res = compute_sil(
            ipts=emgfile["IPTS"][0],
            mupulses=np.array([10500, 50000]),
            ignore_negative_ipts=False,
        )
        self.assertAlmostEqual(res, 0.945, places=2)

    def test_compute_pnr(self):
        """
        Test the compute_pnr function.
        """

        # Load the decomposed samplefile
        emgfile = emg_from_samplefile()

        # Default values
        res = compute_pnr(
            ipts=emgfile["IPTS"][0],
            mupulses=emgfile["MUPULSES"][0],
            fsamp=emgfile["FSAMP"],
            constrain_pulses=[True, 3],
            separate_paired_firings=True,
        )
        self.assertAlmostEqual(res, 27.345, places=2)

        # Change constrain_pulses and separate_paired_firings
        res = compute_pnr(
            ipts=emgfile["IPTS"][0],
            mupulses=emgfile["MUPULSES"][0],
            fsamp=emgfile["FSAMP"],
            constrain_pulses=[True, 3],
            separate_paired_firings=False,
        )
        self.assertAlmostEqual(res, 27.345, places=2)

        res = compute_pnr(
            ipts=emgfile["IPTS"][0],
            mupulses=emgfile["MUPULSES"][0],
            fsamp=emgfile["FSAMP"],
            constrain_pulses=[False, 3],
            separate_paired_firings=True,
        )
        self.assertAlmostEqual(res, 31.167, places=2)

        # Thest failure with no or few firings
        res = compute_pnr(
            ipts=emgfile["IPTS"][0],
            mupulses=np.empty(0),
            fsamp=emgfile["FSAMP"],
            constrain_pulses=[True, 3],
            separate_paired_firings=True,
        )
        self.assertTrue(np.isnan(res))

        res = compute_pnr(
            ipts=emgfile["IPTS"][0],
            mupulses=np.array([10500]),
            fsamp=emgfile["FSAMP"],
            constrain_pulses=[True, 3],
            separate_paired_firings=True,
        )
        self.assertTrue(np.isnan(res))

        res = compute_pnr(
            ipts=emgfile["IPTS"][0],
            mupulses=np.array([10500, 50000]),
            fsamp=emgfile["FSAMP"],
            constrain_pulses=[True, 3],
            separate_paired_firings=True,
        )
        self.assertAlmostEqual(res, -7.475, places=2)

    def test_derivatives_beamforming(self):
        """
        Test the derivatives_beamforming function.
        """

        # Load the decomposed samplefile
        emgfile = emg_from_samplefile()

        sig = emgfile["RAW_SIGNAL"].iloc[10287:10317, 3:8].transpose()
        res = derivatives_beamforming(
            sig=sig.to_numpy(),
            row=0,
            teta=1,
        )
        self.assertAlmostEqual(res[0], 380.5292664746554, places=9)
        self.assertAlmostEqual(res[1], 38211.07196482990, places=9)

    def test_mle_cv_est(self):
        """
        Test the mle_cv_est function.
        """

        # Load the decomposed samplefile
        emgfile = emg_from_samplefile()

        sig = emgfile["RAW_SIGNAL"].iloc[10287:10317, 3:8].transpose()
        sig = sig.diff().diff().dropna().to_numpy()
        res = mle_cv_est(
            sig=sig,
            initial_teta=1,
            ied=emgfile["IED"],
            fsamp=emgfile["FSAMP"],
        )
        self.assertAlmostEqual(res[0], 7.279193825482191, places=9)
        self.assertAlmostEqual(res[1], 2.250798700076472, places=9)

    def test_find_mle_teta(self):
        """
        Test the find_mle_teta function.
        """

        # Load the decomposed samplefile
        emgfile = emg_from_samplefile()

        sig = emgfile["RAW_SIGNAL"].iloc[10287:10317, 3:8].transpose()
        sig = sig.diff().diff().dropna().to_numpy()
        res = find_mle_teta(
            sig1=sig[0, :],
            sig2=sig[1, :],
            ied=emgfile["IED"],
            fsamp=emgfile["FSAMP"],
        )
        self.assertAlmostEqual(res, 1, places=0)


if __name__ == '__main__':
    unittest.main()
