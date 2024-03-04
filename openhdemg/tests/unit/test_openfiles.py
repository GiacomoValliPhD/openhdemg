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
"""


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


class TestOpenFiles(unittest.TestCase):
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

        # Load decomposed file with multiple MUs, reference signal and MUAPs
        delsys_D_R_MUAPs_mMU = emg_from_delsys(
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
        validate_emgfile_content(self, delsys_D_R_MUAPs_mMU)

        # Load decomposed file with multiple MUs and MUAPs
        delsys_D_MUAPs_mMU = emg_from_delsys(
            rawemg_filepath=getd(
                "library",
                ["delsys", "4pin", "DELSYS_D_MUAPs_mMU"],
                "Raw_EMG_signal.mat"
            ),
            mus_directory=getd(
                "library",
                ["delsys", "4pin", "DELSYS_D_MUAPs_mMU"],
                "Bicep_Brachii_Motor_Units (Sensor 1)"
            ),
        )
        validate_emgfile_content(self, delsys_D_MUAPs_mMU)

        # Load file with only the reference signal
        delsys_R = refsig_from_delsys(
            filepath=getd(
                "library",
                ["delsys", "4pin", "DELSYS_D_R_MUAPs_mMU"],
                "Raw_EMG_signal_withFakeRef.mat",
            )
        )
        validate_emg_refsig_content(self, delsys_R)

    def test_from_customcsv(self):
        """
        Test loading various files saved in a custom .csv file.
        """

        # Load decomposed file with multiple MUs, reference signal and EXTRAS
        custom_csv_D_R_EX_mMU = emg_from_customcsv(
            filepath=getd("library", "custom_csv", "C_CSV_D_R_EX_mMU.csv"),
            )
        validate_emgfile_content(self, custom_csv_D_R_EX_mMU)

        # Load decomposed file with multiple MUs, reference signal and EXTRAS
        custom_csv_D_R_EX_1MU = emg_from_customcsv(
            filepath=getd("library", "custom_csv", "C_CSV_D_R_EX_1MU.csv"),
            )
        validate_emgfile_content(self, custom_csv_D_R_EX_1MU)

        # Load file with only the reference signal EXTRAS
        custom_csv_R_EX = refsig_from_customcsv(
            filepath=getd("library", "custom_csv", "C_CSV_R_EX.csv"),
            )
        validate_emg_refsig_content(self, custom_csv_R_EX)

    def test_from_samplefile(self):
        """
        Test loading the decomposed sample file.
        """

        # Load decomposed file with multiple MUs and reference signal
        emgfile = emg_from_samplefile()
        validate_emgfile_content(self, emgfile)

    def test_from_json(self):
        """
        Test loading various files saved in .json.
        """

        # Load decomposed file with multiple MUs and reference signal
        openhdemg_D_R_mMU = emg_from_json(
            filepath=getd("library", "openhdemg", "OPENHD_D_R_mMU.json"),
            )
        validate_emgfile_content(self, openhdemg_D_R_mMU)

        # Load decomposed file with multiple MUs, reference signal and EXTRAS
        openhdemg_D_R_EX_mMU = emg_from_json(
            filepath=getd("library", "openhdemg", "OPENHD_D_R_EX_mMU.json"),
            )
        validate_emgfile_content(self, openhdemg_D_R_EX_mMU)

        # Load file with only reference signal
        openhdemg_R = emg_from_json(
            filepath=getd("library", "openhdemg", "OPENHD_R.json"),
            )
        validate_emg_refsig_content(self, openhdemg_R)

        # Load file with only reference signal and EXTRAS
        openhdemg_R_EX = emg_from_json(
            filepath=getd("library", "openhdemg", "OPENHD_R_EX.json"),
            )
        validate_emg_refsig_content(self, openhdemg_R_EX)

    def test_saving_and_reloading(self):
        """
        Test saving (various) and reloading (.json) files.
        """

        # Test with sample file
        emgfile = emg_from_samplefile()
        save_json_emgfile(
            emgfile, filepath=getd("library", "saved", "temp.json")
        )




if __name__ == '__main__':
    unittest.main()
