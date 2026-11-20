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
import warnings
from openhdemg.library.openfiles import emg_from_samplefile
from openhdemg.library.mathtools import (
    min_max_scaling, norm_xcorr, norm_twod_xcorr, discrete_spike_xcorr,
    compute_sil, compute_pnr, compute_pulses_agreement_rate,
    derivatives_beamforming, mle_cv_est, find_mle_teta,
)
import numpy as np
import pandas as pd


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

        res = min_max_scaling(emgfile["RAW_SIGNAL"], col_by_col=True)
        for col in res.columns:
            self.assertAlmostEqual(res[col].min(), 0, places=0)
            self.assertAlmostEqual(res[col].max(), 1, places=0)

        # Test with a 1D array
        array = np.random.uniform(low=-2, high=5, size=(100))
        res = min_max_scaling(array, col_by_col=True)
        self.assertAlmostEqual(res.min(), 0, places=0)
        self.assertAlmostEqual(res.max(), 1, places=0)

        array = np.random.uniform(low=-2, high=5, size=(100, 1))
        res = min_max_scaling(array, col_by_col=True)
        self.assertAlmostEqual(res.min(), 0, places=0)
        self.assertAlmostEqual(res.max(), 1, places=0)

        # Test with a 2D array
        array = np.random.uniform(low=-2, high=5, size=(100, 10))
        res = min_max_scaling(array, col_by_col=True)
        for col in range(res.shape[1]):
            self.assertAlmostEqual(res[:, col].min(), 0, places=0)
            self.assertAlmostEqual(res[:, col].max(), 1, places=0)

        # Test with a 2D integer array
        array = np.array([[0, 10], [5, 20], [10, 30]])
        original_array = array.copy()
        res = min_max_scaling(array, col_by_col=True)
        for col in range(res.shape[1]):
            self.assertAlmostEqual(res[0, col], 0, places=6)
            self.assertAlmostEqual(res[1, col], 0.5, places=6)
            self.assertAlmostEqual(res[2, col], 1, places=6)
        self.assertTrue(np.issubdtype(res.dtype, np.floating))
        self.assertTrue(np.array_equal(array, original_array))

        # Test with a 3D array
        array = np.random.uniform(low=-2, high=5, size=(100, 10, 25))
        res = min_max_scaling(array)
        self.assertAlmostEqual(res.min(), 0, places=0)
        self.assertAlmostEqual(res.max(), 1, places=0)

    def test_min_max_scaling_dataframe(self):
        index = pd.Index([10, 20, 30], name="sample")
        frame = pd.DataFrame({"A": [0, 2, 4], "B": [4, 6, 8]}, index=index)
        original = frame.copy()
        for col_by_col, expected in (
            (False, {"A": [0.0, 0.25, 0.5], "B": [0.5, 0.75, 1.0]}),
            (True, {"A": [0.0, 0.5, 1.0], "B": [0.0, 0.5, 1.0]}),
        ):
            with self.subTest(col_by_col=col_by_col):
                scaled = min_max_scaling(frame, col_by_col=col_by_col)
                pd.testing.assert_frame_equal(
                    scaled, pd.DataFrame(expected, index=index),
                    check_exact=True,
                )
                pd.testing.assert_frame_equal(frame, original)

    def test_min_max_scaling_missing_values_and_constant_column(self):
        frame = pd.DataFrame({"A": [0.0, np.nan, 4.0], "B": [2, 2, 2]})
        for col_by_col, expected_b in (
            (False, [0.5, 0.5, 0.5]), (True, [np.nan, np.nan, np.nan]),
        ):
            with self.subTest(col_by_col=col_by_col):
                expected = pd.DataFrame(
                    {"A": [0.0, np.nan, 1.0], "B": expected_b}
                )
                scaled = min_max_scaling(frame, col_by_col=col_by_col)
                pd.testing.assert_frame_equal(scaled, expected)

    def test_min_max_scaling_deprecated_series_or_df(self):
        series = pd.Series([1, 3, 5], index=[10, 20, 30], name="signal")
        expected = min_max_scaling(data=series)
        with self.assertWarnsRegex(DeprecationWarning, "series_or_df"):
            scaled = min_max_scaling(series_or_df=series)
        pd.testing.assert_series_equal(scaled, expected)

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

    def test_norm_xcorr_signed_peak_and_zero_energy(self):
        impulse = np.array([0.0, 2.0, 0.0])
        for signal in (impulse, pd.Series(impulse)):
            with self.subTest(input_type=type(signal).__name__):
                self.assertEqual(norm_xcorr(signal, -signal, out="both"), -1.0)
                self.assertEqual(norm_xcorr(signal, -signal, out="max"), 0.0)
                self.assertEqual(norm_xcorr(signal * 0, signal), 0.0)
                self.assertEqual(norm_xcorr(signal, signal * 0), 0.0)

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
        self.assertIsInstance(res[0], pd.DataFrame)
        self.assertAlmostEqual(res[1], 0.975, places=2)
        self.assertEqual(res[0].shape, (399, 127))

        res = norm_twod_xcorr(df, shifted_df, mode="valid")
        self.assertIsInstance(res[0], pd.DataFrame)
        self.assertAlmostEqual(res[1], -0.358, places=2)
        self.assertEqual(res[0].shape, (1, 1))

        res = norm_twod_xcorr(df, shifted_df, mode="same")
        self.assertIsInstance(res[0], pd.DataFrame)
        self.assertAlmostEqual(res[1], 0.975, places=2)
        self.assertEqual(res[0].shape, df.shape)

        # Test numpy array and modes
        arr = df.to_numpy()
        shifted_arr = shifted_df.to_numpy()
        res = norm_twod_xcorr(arr, shifted_arr, mode="full")
        self.assertIsInstance(res[0], np.ndarray)
        self.assertAlmostEqual(res[1], 0.975, places=2)
        self.assertEqual(res[0].shape, (399, 127))

        res = norm_twod_xcorr(arr, shifted_arr, mode="same")
        self.assertIsInstance(res[0], np.ndarray)
        self.assertAlmostEqual(res[1], 0.975, places=2)
        self.assertEqual(res[0].shape, arr.shape)

    def test_norm_twod_xcorr_shifted_impulse(self):
        first = np.zeros((3, 3))
        second = np.zeros((3, 3))
        first[1, 1] = 2.0
        second[0, 2] = 3.0

        # Zero lag is at (2, 2) in the full result. The offset is (+1, -1).
        full = np.zeros((5, 5))
        full[3, 1] = 1.0
        for sig1, sig2 in (
            (first, second), (pd.DataFrame(first), pd.DataFrame(second)),
        ):
            for mode, expected in (
                ("full", full),
                ("same", full[1:4, 1:4]),
                ("valid", full[2:3, 2:3]),
            ):
                with self.subTest(input_type=type(sig1).__name__, mode=mode):
                    corr, peak = norm_twod_xcorr(sig1, sig2, mode=mode)
                    self.assertIsInstance(corr, type(sig1))
                    np.testing.assert_array_equal(corr, expected)
                    self.assertEqual(peak, expected.max())

    def test_norm_twod_xcorr_zero_energy(self):
        for signal in (np.ones((2, 2)), pd.DataFrame(np.ones((2, 2)))):
            with self.subTest(input_type=type(signal).__name__):
                corr, peak = norm_twod_xcorr(signal, signal * 0)
                np.testing.assert_array_equal(corr, np.zeros((3, 3)))
                self.assertEqual(peak, 0.0)

    def test_norm_twod_xcorr_deprecated_dataframe_arguments(self):
        first = pd.DataFrame([[1.0, 0.0], [0.0, 0.0]])
        second = pd.DataFrame([[0.0, 1.0], [0.0, 0.0]])
        expected, expected_peak = norm_twod_xcorr(sig1=first, sig2=second)
        for alias, arguments in (
            ("df1", {"df1": first, "sig2": second}),
            ("df2", {"sig1": first, "df2": second}),
        ):
            with self.subTest(alias=alias):
                with self.assertWarnsRegex(DeprecationWarning, alias):
                    corr, peak = norm_twod_xcorr(**arguments)
                pd.testing.assert_frame_equal(corr, expected)
                self.assertEqual(peak, expected_peak)

    def test_discrete_spike_xcorr(self):
        # Shifting the second train back one sample aligns both pulses.
        for first, second, max_lag, expected in (
            ([10, 20], [11, 21], 1, [2, 0, 0]),
            ([10, 20], [11, 20], 0, [1]),
            ([], [10], 1, [0, 0, 0]),
            ([10], [], 1, [0, 0, 0]),
        ):
            with self.subTest(first=first, second=second, max_lag=max_lag):
                counts = discrete_spike_xcorr(first, second, max_lag)
                np.testing.assert_array_equal(counts, expected)

    def test_compute_sil(self):
        """
        Test the compute_sil function.
        """

        # Load the decomposed samplefile
        emgfile = emg_from_samplefile()

        ipts = emgfile["IPTS"][0]
        mupulses = emgfile["MUPULSES"][0]
        with warnings.catch_warnings():
            warnings.simplefilter("error", DeprecationWarning)
            res = compute_sil(ipts=ipts, mupulses=mupulses)
        self.assertAlmostEqual(res, 0.879, places=2)

        res = compute_sil(ipts=ipts * np.abs(ipts), mupulses=mupulses)
        self.assertAlmostEqual(res, 0.525, places=2)

        # Test with no or few firings
        res = compute_sil(ipts=ipts, mupulses=np.empty(0))
        self.assertAlmostEqual(res, 0, places=6)

        res = compute_sil(ipts=ipts, mupulses=np.array([10500]))
        self.assertAlmostEqual(res, 1, places=0)

        res = compute_sil(
            ipts=ipts,
            mupulses=np.array([10500, 50000]),
            compute_on_peaks_only=False,
        )
        self.assertAlmostEqual(res, 0.945, places=2)

    def test_compute_sil_deprecated_ignore_negative_ipts(self):
        ipts = pd.Series([-4.0, -1.0, -4.0, 2.0, -3.0, 1.0, -3.0, 4.0, -2.0])
        mupulses = np.array([1, 3, 7])
        for ignore_negative, source in (
            (False, ipts), (True, ipts * np.abs(ipts)),
        ):
            with self.subTest(ignore_negative_ipts=ignore_negative):
                expected = compute_sil(ipts=source, mupulses=mupulses)
                with self.assertWarnsRegex(
                    DeprecationWarning, "ignore_negative_ipts",
                ):
                    score = compute_sil(
                        ipts=ipts, mupulses=mupulses,
                        ignore_negative_ipts=ignore_negative,
                    )
                self.assertAlmostEqual(score, expected)

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

    def test_compute_pulses_agreement_rate(self):
        for estimated, reference, tolerance, expected in (
            ([10, 20], [10, 30], 0, 50.0),
            ([9, 11], [10], 0, 0.0),
            ([9, 11], [10], 1, 200 / 3),  # Only one can match the reference.
            ([21, 9], [10, 20], 1, 100.0),  # Both ends of the tolerance window.
            ([40, 19, 19, 3], [20, 8, 20], 1, 40.0),
            ([], [], 1, 0.0),
            ([10], [], 1, 0.0),
            ([], [10], 1, 0.0),
        ):
            with self.subTest(
                estimated=estimated, reference=reference, tolerance=tolerance,
            ):
                rate = compute_pulses_agreement_rate(
                    estimated_pulses=np.array(estimated, dtype=np.int64),
                    reference_pulses=np.array(reference, dtype=np.int64),
                    tolerance=tolerance,
                )
                self.assertAlmostEqual(rate, expected)

    def test_compute_pulses_agreement_rate_invalid_options(self):
        pulses = np.array([10, 20])
        with self.assertRaisesRegex(ValueError, "tolerance"):
            compute_pulses_agreement_rate(pulses, pulses, tolerance=-1)
        with self.assertRaisesRegex(NotImplementedError, "unsupported"):
            compute_pulses_agreement_rate(pulses, pulses, method="unsupported")

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
        self.assertAlmostEqual(res[0], 380.52906669115697, places=3)
        self.assertAlmostEqual(res[1], 38211.06997829802, places=3)

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
        self.assertAlmostEqual(res[0], 7.279193825482191, places=3)
        self.assertAlmostEqual(res[1], 2.250798700076472, places=3)

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
        self.assertAlmostEqual(res, 12.026160794414398, places=6)

        # Test when the minimum delay is different from 1
        sig1 = np.zeros(64)
        sig2 = np.zeros(64)
        sig1[20] = 1
        sig2[24] = 1
        res = find_mle_teta(
            sig1=sig1,
            sig2=sig2,
            ied=10,
            fsamp=2048,
        )
        self.assertAlmostEqual(res, 4, places=6)

    def test_find_mle_teta_at_delay_limits(self):
        # At 10 mm and 2000 Hz the search covers lags from 2 to 20 samples.
        sig1 = np.zeros(64)
        sig1[20] = 1.0
        for delay in (2, 20):
            with self.subTest(delay=delay):
                sig2 = np.zeros(64)
                sig2[20 + delay] = 1.0
                result = find_mle_teta(sig1, sig2, ied=10, fsamp=2000)
                self.assertEqual(result, delay)

    def test_find_mle_teta_rejects_non_1d_signals(self):
        signal = np.zeros(64)
        row = signal.reshape(1, -1)
        for name, first, second in (
            ("sig1", row, signal), ("sig2", signal, row),
        ):
            with self.subTest(name=name):
                with self.assertRaisesRegex(ValueError, name):
                    find_mle_teta(first, second, ied=10, fsamp=2000)


if __name__ == '__main__':
    unittest.main()
