"""
To run the tests using unittest, execute from the openhdemg/tests directory:
    python -m unittest discover

First, you should dowload all the files necessary for the testing and store them inside
openhdemg/tests/fixtures. The files are available at:
https://drive.google.com/drive/folders/1suCZSils8rSCs2E3_K25vRCbN3AFDI7F?usp=sharing

IMPORTANT: Do not alter the content of the dowloaded folder!

WARNING!!! Since the library's functions perform complex tasks and return
complex data structures, these tests can verify that no critical errors occur,
but the accuracy of each function must be assessed independently upon creation,
or at each revision of the code.
"""


import pandas as pd
import numpy as np
import unittest
from openhdemg.tests.unit.functions_for_unit_test import get_directories as getd
from openhdemg.tests.unit.functions_for_unit_test import (
    validate_emgfile_content, validate_emg_refsig_content,
)
from openhdemg.library.openfiles import (
    emg_from_demuse, emg_from_otb, refsig_from_otb, emg_from_delsys,
    refsig_from_delsys, emg_from_customcsv, refsig_from_customcsv,
    save_json_emgfile, emg_from_json, askopenfile, asksavefile,
    emg_from_samplefile,
)


class TestOpenfiles(unittest.TestCase):
    """
    Test the functions/classes in the openfiles module.
    """

    def test_from_demuse(self):
        """
        Test loading various decomposed files saved from the DEMUSE software.
        """

        # Load decomposed file with multiple MUs and reference signal
        demuse_D_R_mMU = emg_from_demuse(
            filepath=getd("library", "demuse", "DEMUSE_D_R_mMU.mat"),
            )
        validate_emgfile_content(self, demuse_D_R_mMU)

        # Load decomposed file with only 1 MU and reference signal
        demuse_D_R_1MU = emg_from_demuse(
            filepath=getd("library", "demuse", "DEMUSE_D_R_1MU.mat"),
            )
        validate_emgfile_content(self, demuse_D_R_1MU)

        # Load decomposed file with multiple MUs (some empty) and reference
        # signal
        demuse_D_R_E_mMU = emg_from_demuse(
            filepath=getd("library", "demuse", "demuse_D_R_E_mMU.mat"),
            )
        validate_emgfile_content(self, demuse_D_R_E_mMU)

    def test_from_otb(self):
        """
        Test loading various files saved from the OTBiolab+ software.
        """

        # Load decomposed file with multiple MUs and reference signal
        otb_D_R_mMU = emg_from_otb(
            filepath=getd("library", "otb", "OTB_D_R_mMU.mat"),
            )
        validate_emgfile_content(self, otb_D_R_mMU)

        # Load decomposed file with multiple MUs, reference signal and EXTRAS
        otb_D_R_EX_mMU = emg_from_otb(
            filepath=getd("library", "otb", "OTB_D_R_EX_mMU.mat"),
            extras="requested|AUX  Force"
            )
        validate_emgfile_content(self, otb_D_R_EX_mMU)

        # Load decomposed file with only 1 MU and reference signal
        otb_D_R_1_MU = emg_from_otb(
            filepath=getd("library", "otb", "OTB_D_R_1MU.mat"),
            )
        validate_emgfile_content(self, otb_D_R_1_MU)

        # Load file with only the reference signal
        otb_R = refsig_from_otb(
            filepath=getd("library", "otb", "OTB_R.mat"),
            )
        validate_emg_refsig_content(self, otb_R)

        # Load file with only the reference signal and EXTRAS
        otb_R_EX = refsig_from_otb(
            filepath=getd("library", "otb", "OTB_R_EX.mat"),
            extras="requested path",
            )
        validate_emg_refsig_content(self, otb_R_EX)

    def test_from_delsys(self):
        """
        Test loading various files saved from the Delsys software.
        """

        # Load decomposed file with multiple MUs and reference signal
        otb_D_R_mMU = emg_from_otb(
            filepath=getd("library", "otb", "OTB_D_R_mMU.mat"),
            )
        validate_emgfile_content(self, otb_D_R_mMU)


if __name__ == '__main__':
    unittest.main()
