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
from openhdemg.library.analysis import (
    compute_thresholds, compute_dr, basic_mus_properties, compute_covisi,
    compute_drvariability,
)
import numpy as np


class TestAnalysis(unittest.TestCase):
    """
    Test the functions/classes in the analysis module.
    """

    def test_compute_thresholds(self):
        """
        Test the compute_thresholds function with the samplefile.
        """

        # Load the decomposed samplefile
        emgfile = emg_from_samplefile()

        # Default parameters
        res = compute_thresholds(
            emgfile=emgfile,
            event_="rt_dert",
            type_="abs_rel",
            n_firings=1,
            mvc=1234,
        )

        self.assertAlmostEqual(
            res["abs_RT"][0], 86.824, places=2,
        )
        self.assertAlmostEqual(
            res["abs_DERT"][1], 220.965, places=2,
        )
        self.assertAlmostEqual(
            res["rel_RT"][2], 12.491, places=2,
        )
        self.assertAlmostEqual(
            res["rel_DERT"][3], 7.373, places=2,
        )

        # Change n_firings
        res = compute_thresholds(
            emgfile=emgfile,
            event_="rt_dert",
            type_="abs_rel",
            n_firings=5,
            mvc=1234,
        )

        self.assertAlmostEqual(
            res["abs_RT"][0], 170.833, places=2,
        )
        self.assertAlmostEqual(
            res["abs_DERT"][1], 244.561, places=2,
        )
        self.assertAlmostEqual(
            res["rel_RT"][2], 14.677, places=2,
        )
        self.assertAlmostEqual(
            res["rel_DERT"][3], 9.313, places=2,
        )

        # Change event_
        res = compute_thresholds(
            emgfile=emgfile,
            event_="rt",
            type_="rel",
            n_firings=5,
            mvc=1234,
        )

        self.assertAlmostEqual(
            res["rel_RT"][0], 13.843, places=2,
        )

    def test_compute_dr(self):
        """
        Test the compute_dr function with the samplefile.
        """

        # Load the decomposed samplefile
        emgfile = emg_from_samplefile()

        # Ramps duration
        t_ramps = 10 * emgfile["FSAMP"]

        # Default parameters
        res = compute_dr(
            emgfile=emgfile,
            n_firings_RecDerec=4,
            n_firings_steady=10,
            start_steady=0 + t_ramps,
            end_steady=emgfile["EMG_LENGTH"] - t_ramps,
            event_="rec_derec_steady",
        )

        self.assertAlmostEqual(
            res["DR_rec"][0], 3.341, places=2,
        )
        self.assertAlmostEqual(
            res["DR_derec"][1], 4.662, places=2,
        )
        self.assertAlmostEqual(
            res["DR_start_steady"][2], 8.793, places=2,
        )
        self.assertAlmostEqual(
            res["DR_end_steady"][3], 10.718, places=2,
        )
        self.assertAlmostEqual(
            res["DR_all_steady"][4], 10.693, places=2,
        )
        self.assertAlmostEqual(
            res["DR_all"][3], 10.693, places=2,
        )

        # Change n_firings_RecDerec
        res = compute_dr(
            emgfile=emgfile,
            n_firings_RecDerec=10,
            n_firings_steady=10,
            start_steady=0 + t_ramps,
            end_steady=emgfile["EMG_LENGTH"] - t_ramps,
            event_="rec_derec_steady",
        )

        self.assertAlmostEqual(
            res["DR_rec"][0], 7.031, places=2,
        )
        self.assertAlmostEqual(
            res["DR_derec"][1], 5.596, places=2,
        )

        res = compute_dr(
            emgfile=emgfile,
            n_firings_RecDerec=1,
            n_firings_steady=10,
            start_steady=0 + t_ramps,
            end_steady=emgfile["EMG_LENGTH"] - t_ramps,
            event_="rec_derec_steady",
        )

        self.assertTrue(np.isnan(res["DR_rec"][0]))
        self.assertTrue(np.isnan(res["DR_derec"][0]))

        # Change n_firings_steady
        res = compute_dr(
            emgfile=emgfile,
            n_firings_RecDerec=4,
            n_firings_steady=36,
            start_steady=0 + t_ramps,
            end_steady=emgfile["EMG_LENGTH"] - t_ramps,
            event_="rec_derec_steady",
        )

        self.assertAlmostEqual(
            res["DR_start_steady"][0], 9.971, places=2,
        )
        self.assertAlmostEqual(
            res["DR_end_steady"][1], 6.806, places=2,
        )

        res = compute_dr(
            emgfile=emgfile,
            n_firings_RecDerec=1,
            n_firings_steady=1,
            start_steady=0 + t_ramps,
            end_steady=emgfile["EMG_LENGTH"] - t_ramps,
            event_="rec_derec_steady",
        )

        self.assertAlmostEqual(
            res["DR_start_steady"][0], 7.474, places=2,
        )
        self.assertAlmostEqual(
            res["DR_end_steady"][1], 7.062, places=2,
        )

        # Change idr_range
        res = compute_dr(
            emgfile=emgfile,
            n_firings_RecDerec=4,
            n_firings_steady=10,
            start_steady=0 + t_ramps,
            end_steady=emgfile["EMG_LENGTH"] - t_ramps,
            event_="rec_derec_steady",
            idr_range=[7, 10],
        )

        self.assertTrue(np.isnan(res["DR_end_steady"][0]))
        self.assertAlmostEqual(
            res["DR_all"][1], 7.644, places=2,
        )

    def test_basic_mus_properties(self):
        """
        Test the basic_mus_properties function with the samplefile.
        """

        # Load the decomposed samplefile
        emgfile = emg_from_samplefile()

        # Ramps duration
        t_ramps = 10 * emgfile["FSAMP"]

        # Default parameters
        res = basic_mus_properties(
            emgfile=emgfile,
            n_firings_rt_dert=1,
            n_firings_RecDerec=4,
            n_firings_steady=10,
            start_steady=0 + t_ramps,
            end_steady=emgfile["EMG_LENGTH"] - t_ramps,
            accuracy="default",
            ignore_negative_ipts=False,
            constrain_pulses=[True, 3],
            mvc=1234,
        )

        self.assertAlmostEqual(
            res["MVC"][0], 1234.0, places=0,
        )
        self.assertAlmostEqual(
            res["Accuracy"][1], 0.955, places=2,
        )
        self.assertAlmostEqual(
            res["avg_Accuracy"][0], 0.914, places=2,
        )
        self.assertAlmostEqual(
            res["COV_steady"][0], 1.316, places=2,
        )

        # Change accuracy estimation
        res = basic_mus_properties(
            emgfile=emgfile,
            n_firings_rt_dert=1,
            n_firings_RecDerec=4,
            n_firings_steady=10,
            start_steady=0 + t_ramps,
            end_steady=emgfile["EMG_LENGTH"] - t_ramps,
            accuracy="SIL_PNR",
            ignore_negative_ipts=True,
            constrain_pulses=[True, 3],
            mvc=1234,
        )

        self.assertAlmostEqual(
            res["SIL"][1], 0.830, places=2,
        )
        self.assertAlmostEqual(
            res["avg_SIL"][0], 0.676, places=2,
        )
        self.assertAlmostEqual(
            res["PNR"][4], 28.469, places=2,
        )
        self.assertAlmostEqual(
            res["avg_PNR"][0], 29.113, places=2,
        )

        res = basic_mus_properties(
            emgfile=emgfile,
            n_firings_rt_dert=1,
            n_firings_RecDerec=4,
            n_firings_steady=10,
            start_steady=0 + t_ramps,
            end_steady=emgfile["EMG_LENGTH"] - t_ramps,
            accuracy="PNR",
            ignore_negative_ipts=True,
            constrain_pulses=[False, 3],
            mvc=1234,
        )

        self.assertAlmostEqual(
            res["PNR"][4], 28.079, places=2,
        )
        self.assertAlmostEqual(
            res["avg_PNR"][0], 29.895, places=2,
        )

        # Change idr_range
        res = basic_mus_properties(
            emgfile=emgfile,
            n_firings_rt_dert=1,
            n_firings_RecDerec=4,
            n_firings_steady=10,
            start_steady=0 + t_ramps,
            end_steady=emgfile["EMG_LENGTH"] - t_ramps,
            idr_range=[7, 10],
            accuracy="default",
            ignore_negative_ipts=False,
            constrain_pulses=[True, 3],
            mvc=1234,
        )

        self.assertTrue(np.isnan(res["DR_end_steady"][0]))
        self.assertAlmostEqual(
            res["DR_all"][1], 7.644, places=2,
        )
        self.assertAlmostEqual(
            res["COVisi_steady"][2], 7.677, places=2,
        )

    def test_compute_covisi(self):
        """
        Test the compute_dr function with the samplefile.
        """

        # Load the decomposed samplefile
        emgfile = emg_from_samplefile()

        # Ramps duration
        t_ramps = 10 * emgfile["FSAMP"]

        # Default parameters
        res = compute_covisi(
            emgfile=emgfile,
            n_firings_RecDerec=4,
            start_steady=0 + t_ramps,
            end_steady=emgfile["EMG_LENGTH"] - t_ramps,
            event_="rec_derec_steady",
            single_mu_number=-1,
        )

        self.assertAlmostEqual(
            res["COVisi_rec"][0], 67.000, places=2,
        )
        self.assertAlmostEqual(
            res["COVisi_derec"][1], 24.007, places=2,
        )
        self.assertAlmostEqual(
            res["COVisi_steady"][2], 8.700, places=2,
        )
        self.assertAlmostEqual(
            res["COVisi_all"][3], 19.104, places=2,
        )

        # Change n_firings_RecDerec and event_
        res = compute_covisi(
            emgfile=emgfile,
            n_firings_RecDerec=1,
            start_steady=0 + t_ramps,
            end_steady=emgfile["EMG_LENGTH"] - t_ramps,
            event_="rec_derec",
            single_mu_number=-1,
        )

        self.assertTrue(np.isnan(res["COVisi_rec"][0]))
        self.assertTrue(np.isnan(res["COVisi_derec"][0]))

        # Change single_mu_number
        res = compute_covisi(
            emgfile=emgfile,
            n_firings_RecDerec=4,
            start_steady=0 + t_ramps,
            end_steady=emgfile["EMG_LENGTH"] - t_ramps,
            event_="rec_derec_steady",
            single_mu_number=3,
        )

        self.assertAlmostEqual(
            res["COVisi_all"][0], 19.104, places=2,
        )

        # Change idr_range
        res = compute_covisi(
            emgfile=emgfile,
            n_firings_RecDerec=4,
            start_steady=0 + t_ramps,
            end_steady=emgfile["EMG_LENGTH"] - t_ramps,
            event_="rec_derec_steady",
            idr_range=[7, 10],
            single_mu_number=-1,
        )

        self.assertTrue(np.isnan(res["COVisi_rec"][0]))
        self.assertAlmostEqual(
            res["COVisi_steady"][2], 7.677, places=2,
        )

    def test_compute_drvariability(self):
        """
        Test the compute_drvariability function with the samplefile.
        """

        # Load the decomposed samplefile
        emgfile = emg_from_samplefile()

        # Ramps duration
        t_ramps = 10 * emgfile["FSAMP"]

        # Default parameters
        res = compute_drvariability(
            emgfile=emgfile,
            n_firings_RecDerec=4,
            start_steady=0 + t_ramps,
            end_steady=emgfile["EMG_LENGTH"] - t_ramps,
            event_="rec_derec_steady",
        )

        self.assertAlmostEqual(
            res["DRvar_rec"][0], 109.254, places=2,
        )
        self.assertAlmostEqual(
            res["DRvar_derec"][1], 21.662, places=2,
        )
        self.assertAlmostEqual(
            res["DRvar_steady"][2], 8.840, places=2,
        )
        self.assertAlmostEqual(
            res["DRvar_all"][3], 12.803, places=2,
        )

        # Change n_firings_RecDerec
        res = compute_drvariability(
            emgfile=emgfile,
            n_firings_RecDerec=1,
            start_steady=0 + t_ramps,
            end_steady=emgfile["EMG_LENGTH"] - t_ramps,
            event_="rec_derec_steady",
        )

        self.assertTrue(np.isnan(res["DRvar_rec"][0]))
        self.assertTrue(np.isnan(res["DRvar_derec"][1]))

        # Change idr_range
        res = compute_drvariability(
            emgfile=emgfile,
            n_firings_RecDerec=4,
            start_steady=0 + t_ramps,
            end_steady=emgfile["EMG_LENGTH"] - t_ramps,
            event_="rec_derec_steady",
            idr_range=[7, 10],
        )

        self.assertTrue(np.isnan(res["DRvar_rec"][0]))
        self.assertAlmostEqual(
            res["DRvar_all"][1], 6.466, places=2,
        )


if __name__ == '__main__':
    unittest.main()
