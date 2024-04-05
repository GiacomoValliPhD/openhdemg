import os
import pandas as pd
import numpy as np


def get_directories(folder, subfolder, filename):
    """
    Get the directory of the specified file.

    Parameters:
    -----------
    folder : str
        The name of the folder containing the folder with the specified file
        (e.g., library).
        The folder should be inside "tests/fixtures/..."
    subfolder : str or list
        A sting or list of the subfolder/s containing the specified file
        (e.g., "demuse" or ["delsys", "4pin"]).
        The folder/s should be inside "tests/fixtures/...folder..."
    filename : str
        The name of the file to open including the file extension. The file to
        open should be inside "tests/fixtures/...folder.../...subfolder".

    Returns
    -------
    filepath : str
        The full path to the file.
    """

    # Get the absolute path of the current Python file
    current_file_path = os.path.abspath(__file__)

    # Get the directory containing the current Python file
    current_directory = os.path.dirname(os.path.dirname(current_file_path))

    if isinstance(subfolder, str):
        subfolder = [subfolder]

    filepath = os.path.join(
        current_directory, "fixtures", folder, *subfolder, filename,
    )

    return filepath


def validate_emgfile_content(tc, emgfile):
    """
    Verify the emgfile content (instances and shapes).

    Parameters:
    -----------
    tc : class
        The unittest.TestCase instance (this should be "self").
    emgfile : dict
        The loaded emgfile (with decomposition outcome).
    """

    # Verify instances
    tc.assertIsInstance(emgfile, dict)
    tc.assertIsInstance(emgfile["SOURCE"], str)
    tc.assertIsInstance(emgfile["FILENAME"], str)
    tc.assertIsInstance(emgfile["RAW_SIGNAL"], pd.DataFrame)
    tc.assertIsInstance(emgfile["REF_SIGNAL"], pd.DataFrame)
    tc.assertIsInstance(emgfile["ACCURACY"], pd.DataFrame)
    tc.assertIsInstance(emgfile["IPTS"], pd.DataFrame)
    tc.assertIsInstance(emgfile["MUPULSES"], list)
    tc.assertIsInstance(emgfile["MUPULSES"][0], np.ndarray)
    tc.assertIsInstance(emgfile["FSAMP"], float)
    tc.assertIsInstance(emgfile["IED"], float)
    tc.assertIsInstance(emgfile["EMG_LENGTH"], int)
    tc.assertIsInstance(emgfile["NUMBER_OF_MUS"], int)
    tc.assertIsInstance(emgfile["BINARY_MUS_FIRING"], pd.DataFrame)
    tc.assertIsInstance(emgfile["EXTRAS"], pd.DataFrame)

    # Verify shapes
    tc.assertEqual(len(emgfile.keys()), 13)
    tc.assertTrue(
        emgfile["RAW_SIGNAL"].shape[0] > emgfile["RAW_SIGNAL"].shape[1]
    )
    try:  # Manage excpetion of no reference signal
        tc.assertTrue(
            emgfile["REF_SIGNAL"].shape[0] > emgfile["REF_SIGNAL"].shape[1]
        )
    except AssertionError:
        tc.assertTrue(emgfile["REF_SIGNAL"].shape[0] == 0)
    tc.assertTrue(
        emgfile["ACCURACY"].shape[0] >= emgfile["ACCURACY"].shape[1]
    )  # >= to manage the exception of a single MU
    if emgfile["SOURCE"] != "DELSYS":
        tc.assertTrue(
            emgfile["IPTS"].shape[0] > emgfile["IPTS"].shape[1]
        )
    else:
        tc.assertTrue(
            emgfile["IPTS"].shape[0] == 0
        )
    tc.assertTrue(
        emgfile["BINARY_MUS_FIRING"].shape[0] > emgfile["BINARY_MUS_FIRING"].shape[1]
    )

    # Verify congruent sizes
    if emgfile["SOURCE"] != "DELSYS":
        tc.assertTrue(
            emgfile["RAW_SIGNAL"].shape[0] == emgfile["IPTS"].shape[0]
        )
        tc.assertTrue(
            emgfile["IPTS"].shape[0] == emgfile["BINARY_MUS_FIRING"].shape[0]
        )
        tc.assertTrue(emgfile["IPTS"].shape[1] == emgfile["NUMBER_OF_MUS"])
        tc.assertTrue(
            emgfile["BINARY_MUS_FIRING"].shape[1] == emgfile["NUMBER_OF_MUS"]
        )
        tc.assertTrue(len(emgfile["MUPULSES"]) == emgfile["NUMBER_OF_MUS"])
    else:
        tc.assertTrue(
            emgfile["RAW_SIGNAL"].shape[0] == emgfile["BINARY_MUS_FIRING"].shape[0]
        )
        tc.assertTrue(
            emgfile["BINARY_MUS_FIRING"].shape[1] == emgfile["NUMBER_OF_MUS"]
        )
        tc.assertTrue(len(emgfile["MUPULSES"]) == emgfile["NUMBER_OF_MUS"])
        tc.assertTrue(
            emgfile["EXTRAS"].shape[1] == emgfile["NUMBER_OF_MUS"] * 4
        )


def validate_emg_refsig_content(tc, emg_refsig):
    """
    Verify the emg_refsig file content (instances and shapes).

    Parameters:
    -----------
    tc : class
        The unittest.TestCase instance (this should be "self").
    emg_refsig : dict
        The loaded emg_refsig.
    """

    # Verify instances
    tc.assertIsInstance(emg_refsig, dict)
    tc.assertIsInstance(emg_refsig["SOURCE"], str)
    tc.assertIsInstance(emg_refsig["FILENAME"], str)
    tc.assertIsInstance(emg_refsig["REF_SIGNAL"], pd.DataFrame)
    tc.assertIsInstance(emg_refsig["FSAMP"], float)
    tc.assertIsInstance(emg_refsig["EXTRAS"], pd.DataFrame)

    # Verify shapes
    tc.assertEqual(len(emg_refsig.keys()), 5)
    tc.assertTrue(
        emg_refsig["REF_SIGNAL"].shape[0] > emg_refsig["REF_SIGNAL"].shape[1]
    )
