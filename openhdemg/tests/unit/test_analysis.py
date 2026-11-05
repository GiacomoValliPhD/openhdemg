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
from openhdemg.library.tools import delete_mus
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

        # Test a file with no MUs
        emgfile = delete_mus(
            emgfile,
            munumber=list(range(emgfile["NUMBER_OF_MUS"])),
        )
        res = compute_thresholds(emgfile=emgfile, mvc=1234)
        self.assertTrue(res.empty)
        self.assertEqual(
            res.columns.tolist(),
            ["abs_RT", "abs_DERT", "rel_RT", "rel_DERT"],
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
            res["DR_end_steady"][3], 10.828, places=2,
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
            res["DR_end_steady"][1], 6.799, places=2,
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
            res["DR_end_steady"][1], 6.502, places=2,
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

        # Test a file with no MUs
        emgfile = delete_mus(
            emgfile,
            munumber=list(range(emgfile["NUMBER_OF_MUS"])),
        )
        res = compute_dr(
            emgfile=emgfile,
            start_steady=0 + t_ramps,
            end_steady=emgfile["EMG_LENGTH"] - t_ramps,
        )
        self.assertTrue(res.empty)
        self.assertEqual(
            res.columns.tolist(),
            [
                "DR_rec", "DR_derec", "DR_start_steady",
                "DR_end_steady", "DR_all_steady", "DR_all",
            ],
        )

    def test_basic_mus_properties(self):
        """
        Test the basic_mus_properties function with the samplefile.
        """

        # Load the decomposed samplefile
        emgfile = emg_from_samplefile()

        # Ramps duration
        t_ramps = 10 * emgfile["FSAMP"]

        # Add optional accuracy results and preserve the original inputs
        emgfile["ROA_WITH_REFERENCE_MUPULSES"] = emgfile["ACCURACY"].copy()
        accuracy = emgfile["ACCURACY"].copy()
        roa = emgfile["ROA_WITH_REFERENCE_MUPULSES"].copy()

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
        self.assertTrue(emgfile["ACCURACY"].equals(accuracy))
        self.assertTrue(
            emgfile["ROA_WITH_REFERENCE_MUPULSES"].equals(roa)
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
            res["COVisi_steady"][2], 7.626, places=2,
        )

        # Test a file with no MUs
        zero_emgfile = emg_from_samplefile()
        zero_emgfile = delete_mus(
            zero_emgfile,
            munumber=list(range(zero_emgfile["NUMBER_OF_MUS"])),
        )
        res = basic_mus_properties(
            emgfile=zero_emgfile,
            start_steady=0 + t_ramps,
            end_steady=zero_emgfile["EMG_LENGTH"] - t_ramps,
            mvc=1234,
        )
        self.assertTrue(res.empty)
        self.assertEqual(
            res.columns.tolist(),
            [
                "MVC", "MU_number", "Accuracy", "avg_Accuracy",
                "abs_RT", "abs_DERT", "rel_RT", "rel_DERT",
                "DR_rec", "DR_derec", "DR_start_steady",
                "DR_end_steady", "DR_all_steady", "DR_all",
                "COVisi_steady", "COVisi_all", "COV_steady",
            ],
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
            res["COVisi_steady"][2], 8.655, places=2,
        )
        self.assertAlmostEqual(
            res["COVisi_all"][3], 19.104, places=2,
        )

        # Change n_firings_RecDerec and event_
        idr_range = [7, 10]
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
            idr_range=idr_range,
            single_mu_number=-1,
        )

        self.assertTrue(np.isnan(res["COVisi_rec"][0]))
        self.assertAlmostEqual(
            res["COVisi_steady"][2], 7.626, places=2,
        )
        self.assertEqual(idr_range, [7, 10])

        # Test a file with no MUs
        emgfile = delete_mus(
            emgfile,
            munumber=list(range(emgfile["NUMBER_OF_MUS"])),
        )
        res = compute_covisi(
            emgfile=emgfile,
            start_steady=0 + t_ramps,
            end_steady=emgfile["EMG_LENGTH"] - t_ramps,
        )
        self.assertTrue(res.empty)
        self.assertEqual(
            res.columns.tolist(),
            [
                "COVisi_rec", "COVisi_derec",
                "COVisi_steady", "COVisi_all",
            ],
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
            res["DRvar_steady"][2], 8.809, places=2,
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

        # Test invalid n_firings_RecDerec
        with self.assertRaises(TypeError):
            compute_drvariability(
                emgfile=emgfile,
                n_firings_RecDerec=1.5,
                event_="rec",
            )

        # Test a file with no MUs
        emgfile = delete_mus(
            emgfile,
            munumber=list(range(emgfile["NUMBER_OF_MUS"])),
        )
        res = compute_drvariability(
            emgfile=emgfile,
            start_steady=0 + t_ramps,
            end_steady=emgfile["EMG_LENGTH"] - t_ramps,
        )
        self.assertTrue(res.empty)
        self.assertEqual(
            res.columns.tolist(),
            [
                "DRvar_rec", "DRvar_derec",
                "DRvar_steady", "DRvar_all",
            ],
        )


if __name__ == '__main__':
    unittest.main()
