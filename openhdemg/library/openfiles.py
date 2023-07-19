"""
Description
-----------
This module contains all the functions that are necessary to open or save
MATLAB (.mat), JSON (.json) or custom (.csv) files.
MATLAB files are used to store data from the DEMUSE and the OTBiolab+
software while JSON files are used to save and load files from this
library.
The choice of saving files in the open standard JSON file format was
preferred over the MATLAB file format since it has a better integration
with Python and has a very high cross-platform compatibility.

Function's scope
----------------
emg_from_samplefile :
    Used to load the sample file provided with the library.
emg_from_otb and emg_from_demuse :
    Used to load .mat files coming from the DEMUSE or the OTBiolab+
    software. Demuse has a fixed file structure while the OTB file, in
    order to be compatible with this library should be exported with a
    strict structure as described in the function emg_from_otb.
    In both cases, the input file is a .mat file.
refsig_from_otb :
    Used to load files from the OTBiolab+ software that contain only
    the REF_SIGNAL.
emg_from_customcsv :
    Used to load custom file formats contained in .csv files.
save_json_emgfile, emg_from_json :
    Used to save the working file to a .json file or to load the .json
    file.
askopenfile, asksavefile :
    A quick GUI implementation that allows users to select the file to
    open or save.

Notes
-----
Once opened, the file is returned as a dict with keys:
    "SOURCE" : source of the file (i.e., "CUSTOM", "DEMUSE", "OTB")
    "RAW_SIGNAL" : the raw EMG signal
    "REF_SIGNAL" : the reference signal
    "PNR" : pulse to noise ratio
    "SIL" : silouette score
    "IPTS" : pulse train (decomposed source)
    "MUPULSES" : instants of firing
    "FSAMP" : sampling frequency
    "IED" : interelectrode distance
    "EMG_LENGTH" : length of the emg file (in samples)
    "NUMBER_OF_MUS" : total number of MUs
    "BINARY_MUS_FIRING" : binary representation of MUs firings

The only exception is when OTB files are loaded with just the reference signal:
    "SOURCE": source of the file (i.e., "OTB_REFSIG")
    "FSAMP": sampling frequency
    "REF_SIGNAL": the reference signal

Additional informations can be found in the info module (emg.info()) and in
the function's description.
"""

# Some functions contained in this file are called internally and should not
# be exposed to the final user.
# Functions should be exposed in the __init__ file as:
#     from openhdemg.openfiles import (
#         emg_from_otb,
#         emg_from_demuse,
#         refsig_from_otb,
#         emg_from_customcsv,
#         save_json_emgfile,
#         emg_from_json,
#         askopenfile,
#         asksavefile,
#         emg_from_samplefile,
#     )


from scipy.io import loadmat
import pandas as pd
import numpy as np
from openhdemg.library.electrodes import *
from openhdemg.library.mathtools import compute_pnr, compute_sil
from openhdemg.library.tools import create_binary_firings
from tkinter import *
from tkinter import filedialog
import json
import gzip
import warnings
import os


# ---------------------------------------------------------------------
# Main function to open decomposed files coming from DEMUSE.

def emg_from_demuse(filepath):
    """
    Import the .mat file used in DEMUSE.

    Parameters
    ----------
    filepath : str or Path
        The directory and the name of the file to load
        (including file extension .mat).
        This can be a simple string, the use of Path is not necessary.

    Returns
    -------
    emgfile : dict
        A dictionary containing all the useful variables.

    See also
    --------
    - emg_from_otb : import the .mat file exportable by OTBiolab+.
    - refsig_from_otb : import REF_SIGNAL in the .mat file exportable by
        OTBiolab+.
    - emg_from_customcsv : Import custom data from a .csv file.

    Notes
    -----
    The returned file is called ``emgfile`` for convention.

    The demuse file contains 65 raw EMG channels (1 empty) instead of 64
    (as for OTB matrix standards) in the case of a 64 electrodes matrix.

    Structure of the emgfile:
        emgfile = {
            "SOURCE": SOURCE,
            "FILENAME": FILENAME,
            "RAW_SIGNAL": RAW_SIGNAL,
            "REF_SIGNAL": REF_SIGNAL,
            "PNR": PNR,
            "SIL": SIL
            "IPTS": IPTS,
            "MUPULSES": MUPULSES,
            "FSAMP": FSAMP,
            "IED": IED,
            "EMG_LENGTH": EMG_LENGTH,
            "NUMBER_OF_MUS": NUMBER_OF_MUS,
            "BINARY_MUS_FIRING": BINARY_MUS_FIRING,
        }

    Examples
    --------
    For an extended explanation of the imported emgfile:

    >>> import openhdemg.library as emg
    >>> emgfile = emg.emg_from_demuse(filepath="path/filename.mat")
    >>> info = emg.info()
    >>> info.data(emgfile)
    """

    mat_file = loadmat(filepath, simplify_cells=True)

    # Parse .mat obtained from DEMUSE to see the available variables
    # First: see the variables name
    """
    print(
        "\n--------------------------------\nAvailable dict keys are:\n\n{}\n".format(
            mat_file.keys()
        )
    )
    """

    # Second: collect the necessary variables in a pd.DataFrame (df)
    # or list (for matlab cell arrays)

    # Collect the REF_SIGNAL
    if "ref_signal" in mat_file.keys():

        # Catch the case for float values that cannot be directly added to a
        # dataframe
        if isinstance(mat_file["ref_signal"], float):
            res = {0: mat_file["ref_signal"]}
            REF_SIGNAL = pd.DataFrame(res, index=[0])

        else:
            REF_SIGNAL = pd.DataFrame(mat_file["ref_signal"])

    else:
        warnings.warn(
            "\nVariable ref_signal was not found in the mat file, check the spelling against the dict_keys\n"
        )

        REF_SIGNAL = np.nan

    # Collect the IPTS
    if "IPTs" in mat_file.keys():
        # Catch the exception of a single MU that would create an alrerady
        # transposed pd.DataFrame
        if len(mat_file["IPTs"].shape) == 1:
            IPTS = pd.DataFrame(mat_file["IPTs"])

        else:
            IPTS = pd.DataFrame(mat_file["IPTs"]).transpose()

    else:
        warnings.warn(
            "\nVariable IPTs was not found in the mat file, check the spelling against the dict_keys\n"
        )

        IPTS = np.nan

    # Collect Sampling frequency, Interelectrode distance,
    # File length and number of MUs
    FSAMP = int(mat_file["fsamp"])
    IED = int(mat_file["IED"])
    EMG_LENGTH, NUMBER_OF_MUS = IPTS.shape

    # Collect the MUPULSES, subtract 1 to MUPULSES because these are values in
    # base 1 (MATLAB) and manage exception of single MU.
    if "MUPulses" in mat_file.keys():
        MUPULSES = list(mat_file["MUPulses"])

    else:
        warnings.warn(
            "\nVariable MUPulses was not found in the mat file, check the spelling against the dict_keys\n"
        )

        MUPULSES = np.nan

    for pos, pulses in enumerate(MUPULSES):
        MUPULSES[pos] = pulses - 1

    if NUMBER_OF_MUS == 1:
        MUPULSES = [np.array(MUPULSES)]

    # Collect firing times
    BINARY_MUS_FIRING = create_binary_firings(
        emg_length=EMG_LENGTH,
        number_of_mus=NUMBER_OF_MUS,
        mupulses=MUPULSES,
    )

    # Collect the raw EMG signal
    if "SIG" in mat_file.keys():
        mat = mat_file["SIG"].ravel(order="F")
        # "F" means to index the elements in column-major
        RAW_SIGNAL = pd.DataFrame(list(map(np.ravel, mat))).transpose()

    else:
        warnings.warn(
            "\nVariable SIG was not found in the mat file, check the spelling against the dict_keys\n"
        )

        RAW_SIGNAL = np.nan

    # Use this to know the data source and name of the file
    SOURCE = "DEMUSE"
    FILENAME = os.path.basename(filepath)

    if NUMBER_OF_MUS > 0:
        # Calculate the PNR
        to_append = []
        for mu in range(NUMBER_OF_MUS):
            pnr = compute_pnr(
                ipts=IPTS[mu],
                mupulses=MUPULSES[mu],
                fsamp=FSAMP,
            )
            to_append.append(pnr)
        PNR = pd.DataFrame(to_append)

        # Calculate the SIL
        to_append = []
        for mu in range(NUMBER_OF_MUS):
            sil = compute_sil(ipts=IPTS[mu], mupulses=MUPULSES[mu])
            to_append.append(sil)
        SIL = pd.DataFrame(to_append)

    else:
        PNR = np.nan
        SIL = np.nan

    emgfile = {
        "SOURCE": SOURCE,
        "FILENAME": FILENAME,
        "RAW_SIGNAL": RAW_SIGNAL,
        "REF_SIGNAL": REF_SIGNAL,
        "PNR": PNR,
        "SIL": SIL,
        "IPTS": IPTS,
        "MUPULSES": MUPULSES,
        "FSAMP": FSAMP,
        "IED": IED,
        "EMG_LENGTH": EMG_LENGTH,
        "NUMBER_OF_MUS": NUMBER_OF_MUS,
        "BINARY_MUS_FIRING": BINARY_MUS_FIRING,
    }

    return emgfile


# ---------------------------------------------------------------------
# Define functions used in the OTB openfile function.
# These functions are not exposed to the final user.

def get_otb_refsignal(df, refsig):
    """
    Extract the REF_SIGNAL from the OTB .mat file.

    Parameters
    ----------
    df : pd.DataFrame
        A pd.DataFrame containing all the informations extracted
        from the OTB .mat file.
    refsig : list
        Whether to seacrh also for the REF_SIGNAL and whether to load the full
        or sub-sampled one. The list is composed as [bool, str]. str can be
        "fullsampled" or "subsampled".
        Please read the documentation of emg_from_otb.

    Returns
    -------
    REF_SIGNAL : pd.DataFrame or np.nan
        A pd.DataFrame containing the requested variable
        or np.nan if the variable was not found.
    """

    assert refsig[0] in [
        True,
        False,
    ], f"refsig[0] must be true or false. {refsig[0]} was passed instead."
    assert refsig[1] in [
        "fullsampled",
        "subsampled",
    ], f"refsig[1] must be fullsampled or subsampled. {refsig[1]} was passed instead."

    if refsig[0] is True:
        if refsig[1] == "subsampled":
            # Extract the performed path (subsampled data)
            REF_SIGNAL_SUBSAMPLED = df.filter(regex="performed path")
            # Check if the REF_SIGNAL is available
            if not REF_SIGNAL_SUBSAMPLED.empty:
                REF_SIGNAL_SUBSAMPLED = REF_SIGNAL_SUBSAMPLED.rename(
                    columns={REF_SIGNAL_SUBSAMPLED.columns[0]: 0}
                )
                # Verify that there is no value above 100% since the
                # REF_SIGNAL is expected to be expressed as % of the MVC
                if max(REF_SIGNAL_SUBSAMPLED[0]) > 100:
                    warnings.warn(
                        "\nALERT! Ref signal grater than 100, did you use values normalised to the MVC?\n"
                    )

                return REF_SIGNAL_SUBSAMPLED

            else:
                warnings.warn(
                    "\nReference signal not found, it might be necessary for some analysis\n"
                )

                return np.nan

        elif refsig[1] == "fullsampled":
            # Extract the acquired path (raw data)
            REF_SIGNAL_FULLSAMPLED = df.filter(regex="acquired data")
            if not REF_SIGNAL_FULLSAMPLED.empty:
                REF_SIGNAL_FULLSAMPLED = REF_SIGNAL_FULLSAMPLED.rename(
                    columns={REF_SIGNAL_FULLSAMPLED.columns[0]: 0}
                )
                # Verify that there is no value above 100% since the
                # REF_SIGNAL is expected to be expressed as % of the MVC
                if max(REF_SIGNAL_FULLSAMPLED[0]) > 100:
                    warnings.warn(
                        "\nALERT! Ref signal grater than 100, did you use values normalised to the MVC?\n"
                    )

                return REF_SIGNAL_FULLSAMPLED

            else:
                warnings.warn(
                    "\nReference signal not found, it might be necessary for some analysis\n"
                )

                return np.nan

    else:
        warnings.warn("\nNot searched for reference signal, it might be necessary for some analysis\n")

        return np.nan


def get_otb_decomposition(df):
    """
    Extract the IPTS and BINARY_MUS_FIRING from the OTB .mat file.

    Parameters
    ----------
    df : pd.DataFrame
        A pd.DataFrame containing all the informations extracted
        from the OTB .mat file.

    Returns
    -------
    IPTS, BINARY_MUS_FIRING : pd.DataFrame or np.nan
        pd.DataFrames containing the requested variables
        or np.nan if the variables were not found.
    """

    # Extract the IPTS and rename columns progressively
    IPTS = df.filter(regex="Source for decomposition")
    IPTS.columns = np.arange(len(IPTS.columns))
    # Verify to have the IPTS
    if IPTS.empty:
        IPTS = np.nan

    # Extract the BINARY_MUS_FIRING and rename columns progressively
    BINARY_MUS_FIRING = df.filter(regex="Decomposition of")
    BINARY_MUS_FIRING.columns = np.arange(len(BINARY_MUS_FIRING.columns))
    # Verify to have the BINARY_MUS_FIRING
    if BINARY_MUS_FIRING.empty:
        BINARY_MUS_FIRING = np.nan

    return IPTS, BINARY_MUS_FIRING


def get_otb_mupulses(binarymusfiring):
    """
    Extract the MUPULSES from the OTB .mat file.

    Parameters
    ----------
    binarymusfiring : pd.DataFrame
        A pd.DataFrame containing the binary representation of MUs firings.

    Returns
    -------
    MUPULSES : list
        A list of ndarrays containing the firing time of each MU.
    """

    # Create empty list of lists to fill with ndarrays containing the MUPULSES
    # (point of firing)
    numberofMUs = len(binarymusfiring.columns)
    MUPULSES = [[] for _ in range(numberofMUs)]

    for i in binarymusfiring:  # Loop all the MUs
        my_ndarray = []
        for idx, x in binarymusfiring[i].items():  # Loop the MU firing times
            if x > 0:
                my_ndarray.append(idx)  # Take the firing time and add it to the ndarray

        my_ndarray = np.array(my_ndarray)
        MUPULSES[i] = my_ndarray

    return MUPULSES


def get_otb_ied(df):
    """
    Extract the IED from the OTB .mat file.

    Parameters
    ----------
    df : pd.DataFrame
        A pd.DataFrame containing all the informations extracted
        from the OTB .mat file.

    Returns
    -------
    IED : int
        The interelectrode distance in millimeters.
    """

    for matrix in OTBelectrodes_ied.keys():
        # Check the matrix used in the columns name
        # (in the df obtained from OTBiolab+)
        if matrix in str(df.columns):
            IED = int(OTBelectrodes_ied[matrix])

            return IED


def get_otb_rawsignal(df):
    """
    Extract the IED from the OTB .mat file.

    Parameters
    ----------
    df : pd.DataFrame
        A pd.DataFrame containing all the informations extracted
        from the OTB .mat file.

    Returns
    -------
    RAW_SIGNAL : pd.DataFrame
        A pd.DataFrame containing the RAW_SIGNAL.
    """

    # Drop all the known columns different from the raw EMG signal.
    # This is a workaround since the OTBiolab+ software does not export a
    # unique name for the raw EMG signal.
    pattern = "Source for decomposition|Decomposition of|acquired data|performed path"
    emg_df = df[df.columns.drop(list(df.filter(regex=pattern)))]

    # Check if the number of remaining columns matches the expected number of
    # matrix channels.
    for matrix in OTBelectrodes_Nelectrodes.keys():
        # Check the matrix used in the columns name (in the emg_df) to know
        # the number of expected channels.
        if matrix in str(emg_df.columns):
            expectedchannels = int(OTBelectrodes_Nelectrodes[matrix])
            break

    if len(emg_df.columns) == expectedchannels:
        emg_df.columns = np.arange(len(emg_df.columns))
        RAW_SIGNAL = emg_df

        return RAW_SIGNAL

    else:
        # This check here is usefull to control that only the appropriate
        # elements have been included in the .mat file exported from OTBiolab+.
        raise Exception(
            "Failure in searching the raw signal, please check that it is present in the .mat file and that only the accepted parameters have been included"
        )


# ---------------------------------------------------------------------
# Main function to open decomposed files coming from OTBiolab+.
# This function calls the functions defined above

def emg_from_otb(
    filepath, ext_factor=8, refsig=[True, "fullsampled"], version="1.5.8.0"
):
    """
    Import the .mat file exportable by OTBiolab+.

    This function is used to import the .mat file exportable by the OTBiolab+
    software as a dictionary of Python objects (mainly pandas dataframes).

    Parameters
    ----------
    filepath : str or Path
        The directory and the name of the file to load
        (including file extension .mat).
        This can be a simple string, the use of Path is not necessary.
    ext_factor : int, default 8
        The extension factor used for the decomposition in OTbiolab+.
    refsig : list, default [True, "fullsampled"]
        Whether to seacrh also for the REF_SIGNAL and whether to load the full
        or sub-sampled one. The list is composed as [bool, str]. str can be
        "fullsampled" or "subsampled". Please read notes section.
    version : str, default "1.5.8.0"
        Version of the OTBiolab+ software used (4 points).
        Tested versions are:
            "1.5.3.0",
            "1.5.4.0",
            "1.5.5.0",
            "1.5.6.0",
            "1.5.7.2",
            "1.5.7.3",
            "1.5.8.0",
        If your specific version is not available in the tested versions,
        trying with the closer one usually works, but please double check the
        results.

    Returns
    -------
    emgfile : dict
        A dictionary containing all the useful variables.

    See also
    --------
    - refsig_from_otb : import REF_SIGNAL in the .mat file exportable from
        OTBiolab+.
    - emg_from_demuse : import the .mat file used in DEMUSE.
    - emg_from_customcsv : Import custom data from a .csv file.

    Raises
    ------
    ValueError
        When a wrong value is passed to version=.

    Notes
    ---------
    The returned file is called ``emgfile`` for convention.

    The input .mat file exported from the OTBiolab+ software should have a
    specific content:
    - refsig signal is optional but, if present, there should be the
        fullsampled or the subsampled version (in OTBioLab+ the "performed
        path" refers to the subsampled signal, the "acquired data" to the
        fullsampled signal), REF_SIGNAL is expected to be expressed as % of
        the MVC (but not compulsory).
    - Both the IPTS ('Source for decomposition...' in OTBioLab+) and the
        BINARY_MUS_FIRING ('Decomposition of...' in OTBioLab+) should be
        present.
    - The raw EMG signal should be present (it has no specific name in
        OTBioLab+) with all the channels. Don't exclude unwanted channels
        before exporting the .mat file.
    - NO OTHER ELEMENTS SHOULD BE PRESENT!

    Structure of the returned emgfile:
        emgfile = {
            "SOURCE": SOURCE,
            "FILENAME": FILENAME,
            "RAW_SIGNAL": RAW_SIGNAL,
            "REF_SIGNAL": REF_SIGNAL,
            "PNR": PNR,
            "SIL": SIL,
            "IPTS": IPTS,
            "MUPULSES": MUPULSES,
            "FSAMP": FSAMP,
            "IED": IED,
            "EMG_LENGTH": EMG_LENGTH,
            "NUMBER_OF_MUS": NUMBER_OF_MUS,
            "BINARY_MUS_FIRING": BINARY_MUS_FIRING,
        }

    Examples
    --------
    For an extended explanation of the imported emgfile use:

    >>> import openhdemg.library as emg
    >>> emgfile = emg.emg_from_otb(filepath="path/filename.mat")
    >>> info = emg.info()
    >>> info.data(emgfile)
    """

    mat_file = loadmat(filepath, simplify_cells=True)

    # Parse .mat obtained from DEMUSE to see the available variables
    """ print(
        "\n--------------------------------\nAvailable dict keys are:\n\n{}\n".format(
            mat_file.keys()
        )
    ) """

    # Check if a valid version has been specified
    valid_versions = [
        "1.5.3.0",
        "1.5.4.0",
        "1.5.5.0",
        "1.5.6.0",
        "1.5.7.2",
        "1.5.7.3",
        "1.5.8.0",
    ]
    if version not in valid_versions:
        raise ValueError(f"Specified version is not valid. Use one of:\n{valid_versions}")

    if version in [
        "1.5.3.0",
        "1.5.4.0",
        "1.5.5.0",
        "1.5.6.0",
        "1.5.7.2",
        "1.5.7.3",
        "1.5.8.0",
    ]:
        # Simplify (rename) columns description and extract all the parameters
        # in a pd.DataFrame
        df = pd.DataFrame(mat_file["Data"], columns=mat_file["Description"])

        # Collect the REF_SIGNAL
        REF_SIGNAL = get_otb_refsignal(df=df, refsig=refsig)

        # Collect the IPTS and the firing times
        IPTS, BINARY_MUS_FIRING = get_otb_decomposition(df=df)
        # Align BINARY_MUS_FIRING to IPTS
        BINARY_MUS_FIRING = BINARY_MUS_FIRING.shift(- int(ext_factor))
        BINARY_MUS_FIRING.fillna(value=0, inplace=True)

        # Collect additional parameters
        EMG_LENGTH, NUMBER_OF_MUS = IPTS.shape
        MUPULSES = get_otb_mupulses(binarymusfiring=BINARY_MUS_FIRING)
        FSAMP = int(mat_file["SamplingFrequency"])
        IED = get_otb_ied(df=df)
        RAW_SIGNAL = get_otb_rawsignal(df)

        # Use this to know the data source and name of the file
        SOURCE = "OTB"
        FILENAME = os.path.basename(filepath)

        if NUMBER_OF_MUS > 0:
            # Calculate the PNR
            to_append = []
            for mu in range(NUMBER_OF_MUS):
                pnr = compute_pnr(ipts=IPTS[mu], mupulses=MUPULSES[mu], fsamp=FSAMP)
                to_append.append(pnr)
            PNR = pd.DataFrame(to_append)

            # Calculate the SIL
            to_append = []
            for mu in range(NUMBER_OF_MUS):
                sil = compute_sil(ipts=IPTS[mu], mupulses=MUPULSES[mu])
                to_append.append(sil)
            SIL = pd.DataFrame(to_append)

        else:
            PNR = np.nan
            SIL = np.nan

        emgfile = {
            "SOURCE": SOURCE,
            "FILENAME": FILENAME,
            "RAW_SIGNAL": RAW_SIGNAL,
            "REF_SIGNAL": REF_SIGNAL,
            "PNR": PNR,
            "SIL": SIL,
            "IPTS": IPTS,
            "MUPULSES": MUPULSES,
            "FSAMP": FSAMP,
            "IED": IED,
            "EMG_LENGTH": EMG_LENGTH,
            "NUMBER_OF_MUS": NUMBER_OF_MUS,
            "BINARY_MUS_FIRING": BINARY_MUS_FIRING,
        }

        return emgfile


def refsig_from_otb(filepath, refsig="fullsampled", version="1.5.8.0"):
    """
    Import REF_SIGNAL in the .mat file exportable by OTBiolab+.

    This function is used to import the .mat file exportable by the OTBiolab+
    software as a dictionary of Python objects (mainly pandas dataframes).
    Compared to the function emg_from_otb, this function only imports the
    REF_SIGNAL and, therefore, it can be used for special cases where only the
    REF_SIGNAL is necessary. This will allow a faster execution of the script
    and to avoid exceptions for missing data.

    Parameters
    ----------
    filepath : str or Path
        The directory and the name of the file to load (including file
        extension .mat). This can be a simple string, the use of Path is not
        necessary.
    refsig : str {"fullsampled", "subsampled"}, default "fullsampled"
        Whether to load the full or sub-sampled one.
        Please read notes section.
    version : str, default "1.5.8.0"
        Version of the OTBiolab+ software used (4 points).
        Tested versions are:
            "1.5.3.0",
            "1.5.4.0",
            "1.5.5.0",
            "1.5.6.0",
            "1.5.7.2",
            "1.5.7.3",
            "1.5.8.0",
        If your specific version is not available in the tested versions,
        trying with the closer one usually works, but please double check the
        results.

    Returns
    -------
    emg_refsig : dict
        A dictionary containing all the useful variables.

    See also
    --------
    - emg_from_otb : import the .mat file exportable by OTBiolab+.
    - emg_from_demuse : import the .mat file used in DEMUSE.
    - emg_from_customcsv : Import custom data from a .csv file.

    Notes
    ---------
    The returned file is called ``emg_refsig`` for convention.

    The input .mat file exported from the OTBiolab+ software should contain:
    - refsig signal: there should be the fullsampled or the subsampled
        version (in OTBioLab+ the "performed path" refers to the subsampled
        signal, the "acquired data" to the fullsampled signal), REF_SIGNAL is
        expected to be expressed as % of the MVC (but not compulsory).

    Structure of the returned emg_refsig:
        emg_refsig = {
            "SOURCE": SOURCE,
            "FILENAME": FILENAME,
            "FSAMP": FSAMP,
            "REF_SIGNAL": REF_SIGNAL,
        }

    Examples
    --------
    For an extended explanation of the imported emgfile use:

    >>> import openhdemg.library as emg
    >>> emgfile = emg.refsig_from_otb(filepath="path/filename.mat")
    >>> info = emg.info()
    >>> info.data(emgfile)
    """

    mat_file = loadmat(filepath, simplify_cells=True)

    # Parse .mat obtained from DEMUSE to see the available variables
    """ print(
        "\n--------------------------------\nAvailable dict keys are:\n\n{}\n".format(
            mat_file.keys()
        )
    ) """

    # Check if a valid version has been specified
    valid_versions = [
        "1.5.3.0",
        "1.5.4.0",
        "1.5.5.0",
        "1.5.6.0",
        "1.5.7.2",
        "1.5.7.3",
        "1.5.8.0",
    ]
    if version not in valid_versions:
        raise ValueError(
            f"Specified version is not valid. Use one of:\n{valid_versions}"
        )

    if version in [
        "1.5.3.0",
        "1.5.4.0",
        "1.5.5.0",
        "1.5.6.0",
        "1.5.7.2",
        "1.5.7.3",
        "1.5.8.0",
    ]:
        # Simplify (rename) columns description and extract all the parameters
        # in a pd.DataFrame
        if isinstance(mat_file["Description"], str):
            col = [mat_file["Description"]]
        else:
            col = mat_file["Description"]

        df = pd.DataFrame(mat_file["Data"], columns=col)

        # Convert the input passed to refsig in a list compatible with the
        # function get_otb_refsignal
        refsig_ = [True, refsig]
        REF_SIGNAL = get_otb_refsignal(df=df, refsig=refsig_)

        # Use this to know the data source and name of the file
        SOURCE = "OTB_REFSIG"
        FILENAME = os.path.basename(filepath)
        FSAMP = int(mat_file["SamplingFrequency"])

        emg_refsig = {
            "SOURCE": SOURCE,
            "FILENAME": FILENAME,
            "FSAMP": FSAMP,
            "REF_SIGNAL": REF_SIGNAL,
        }

        return emg_refsig


# ---------------------------------------------------------------------
# Functions to open custom CSV documents.
def emg_from_customcsv(
    filepath,
    ref_signal="REF_SIGNAL",
    raw_signal="RAW_SIGNAL",
    ipts="IPTS",
    mupulses="MUPULSES",
    binary_mus_firing="BINARY_MUS_FIRING",
    fsamp=2048,
    ied=8,
):
    """
    Import custom data from a .csv file.

    The variables of interest should be contained in columns. The name of the
    columns containing each variable can be specified by the user if different
    from the default values.

    This function detects the content of the .csv by parsing the .csv columns.
    For parsing, column labels should be provided. A label is a term common
    to all the columns containing the same information.
    For example, if the raw signal is contained in the columns 'RAW_SIGNAL_1',
    'RAW_SIGNAL_2', ... , 'RAW_SIGNAL_n', the label of the columns should be
    'RAW_SIGNAL'.
    If the parameters in input are not present in the .csv file, the user
    can simply leave the original inputs.

    Parameters
    ----------
    filepath : str or Path
        The directory and the name of the file to load
        (including file extension .mat).
        This can be a simple string, the use of Path is not necessary.
    ref_signal : str, default 'REF_SIGNAL'
        Label of the column(s) containing the reference signal.
    raw_signal : str, default 'RAW_SIGNAL'
        Label of the column(s) containing the raw emg signal.
    ipts : str, default 'IPTS'
        Label of the column(s) containing the pulse train.
    mupulses : str, default 'MUPULSES'
        Label of the column(s) containing the times of firing.
    binary_mus_firing : str, default 'BINARY_MUS_FIRING'
        Label of the column(s) containing the binary representation
        of the MUs firings.
    fsamp : int, default 2048
        Tha sampling frequency.
    ied : int, default 8
        The inter-electrode distance in mm.

    Returns
    -------
    emgfile : dict
        A dictionary containing all the useful variables.

    See also
    --------
    - emg_from_demuse : import the .mat file used in DEMUSE.
    - emg_from_otb : import the .mat file exportable by OTBiolab+.
    - refsig_from_otb : import REF_SIGNAL in the .mat file exportable by
        OTBiolab+.

    Notes
    -----
    The returned file is called ``emgfile`` for convention.

    Structure of the emgfile:
        emgfile = {
            "SOURCE": SOURCE,
            "FILENAME": FILENAME,
            "RAW_SIGNAL": RAW_SIGNAL,
            "REF_SIGNAL": REF_SIGNAL,
            "PNR": PNR,
            "SIL": SIL
            "IPTS": IPTS,
            "MUPULSES": MUPULSES,
            "FSAMP": FSAMP,
            "IED": IED,
            "EMG_LENGTH": EMG_LENGTH,
            "NUMBER_OF_MUS": NUMBER_OF_MUS,
            "BINARY_MUS_FIRING": BINARY_MUS_FIRING,
        }

    Examples
    --------
    An example of the .csv file to load:
    >>>
        REF_SIGNAL  RAW_SIGNAL (1)  RAW_SIGNAL (2)  RAW_SIGNAL (3) ...  IPTS (1)  IPTS (2)  MUPULSES (1)  MUPULSES (2)  BINARY_MUS_FIRING (1)  BINARY_MUS_FIRING (2)
    0            1        0.100000        0.100000        0.100000 ...  0.010000  0.010000           2.0           1.0                      0                      0
    1            2        2.000000        2.000000        2.000000 ...  0.001000  0.001000           5.0           2.0                      0                      0
    2            3        0.500000        0.500000        0.500000 ...  0.020000  0.020000           8.0           9.0                      0                      0
    3            4        0.150000        0.150000        0.150000 ...  0.002000  0.002000           9.0          15.0                      0                      1
    4            5        0.350000        0.350000        0.350000 ... -0.100000 -0.100000          15.0          18.0                      1                      1
    5            6        0.215000        0.215000        0.215000 ...  0.200000  0.200000          16.0           NaN                      1                      0

    For an extended explanation of the imported emgfile use:

    >>> import openhdemg.library as emg
    >>> emgfile = emg_from_customcsv(filepath = "mypath/file.csv")
    >>> info = emg.info()
    >>> info.data(emgfile)
    """

    # Load the csv
    csv = pd.read_csv(filepath)

    # Get REF_SIGNAL
    REF_SIGNAL = csv.filter(regex=ref_signal, axis=1)
    if not REF_SIGNAL.empty:
        REF_SIGNAL.columns = [i for i in range(len(REF_SIGNAL.columns))]
    else:
        warnings.warn(
            "\nref_signal not found, it might be necessary for some analysis\n"
        )
        REF_SIGNAL = np.nan

    # Get RAW_SIGNAL
    RAW_SIGNAL = csv.filter(regex=raw_signal, axis=1)
    if not RAW_SIGNAL.empty:
        RAW_SIGNAL.columns = [i for i in range(len(RAW_SIGNAL.columns))]
    else:
        warnings.warn(
            "\nraw_signal not found, it might be necessary for some analysis\n"
        )
        RAW_SIGNAL = np.nan

    # Get IPTS
    IPTS = csv.filter(regex=ipts, axis=1)
    if not IPTS.empty:
        IPTS.columns = [i for i in range(len(IPTS.columns))]
    else:
        warnings.warn(
            "\nipts not found, it might be necessary for some analysis\n"
        )
        IPTS = np.nan

    # Get MUPULSES
    df = csv.filter(regex=mupulses, axis=1)
    if not df.empty:
        MUPULSES = []
        for col in df.columns:
            toappend = df[col].dropna().to_numpy(dtype=int)
            MUPULSES.append(toappend)
    else:
        MUPULSES = np.nan

    # Get BINARY_MUS_FIRING
    BINARY_MUS_FIRING = csv.filter(regex=binary_mus_firing, axis=1)
    if not BINARY_MUS_FIRING.empty:
        BINARY_MUS_FIRING.columns = [
            i for i in range(len(BINARY_MUS_FIRING.columns))
        ]
    else:
        BINARY_MUS_FIRING = np.nan

    # Get EMG_LENGTH and NUMBER_OF_MUS
    EMG_LENGTH, NUMBER_OF_MUS = IPTS.shape

    # Use this to know the data source and name of the file
    SOURCE = "CUSTOM"
    FILENAME = os.path.basename(filepath)

    if NUMBER_OF_MUS > 0:
        # Calculate the PNR
        to_append = []
        for mu in range(NUMBER_OF_MUS):
            pnr = compute_pnr(
                ipts=IPTS[mu],
                mupulses=MUPULSES[mu],
                fsamp=fsamp,
            )
            to_append.append(pnr)
        PNR = pd.DataFrame(to_append)

        # Calculate the SIL
        to_append = []
        for mu in range(NUMBER_OF_MUS):
            sil = compute_sil(ipts=IPTS[mu], mupulses=MUPULSES[mu])
            to_append.append(sil)
        SIL = pd.DataFrame(to_append)

    else:
        PNR = np.nan
        SIL = np.nan

    emgfile = {
        "SOURCE": SOURCE,
        "FILENAME": FILENAME,
        "RAW_SIGNAL": RAW_SIGNAL,
        "REF_SIGNAL": REF_SIGNAL,
        "PNR": PNR,
        "SIL": SIL,
        "IPTS": IPTS,
        "MUPULSES": MUPULSES,
        "FSAMP": fsamp,
        "IED": ied,
        "EMG_LENGTH": EMG_LENGTH,
        "NUMBER_OF_MUS": NUMBER_OF_MUS,
        "BINARY_MUS_FIRING": BINARY_MUS_FIRING,
    }

    return emgfile


# ---------------------------------------------------------------------
# Functions to convert and save the emgfile to JSON.

def save_json_emgfile(emgfile, filepath):
    """
    Save the emgfile or emg_refsig as a JSON file.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    filepath : str or Path
        The directory and the name of the file to save (including file
        extension .json).
        This can be a simple string; The use of Path is not necessary.
    """

    if emgfile["SOURCE"] in ["DEMUSE", "OTB", "CUSTOM"]:
        """
        We need to convert all the components of emgfile to a dictionary and
        then to json object.
        pd.DataFrame cannot be converted with json.dumps.
        Once all the elements are converted to json objects, we create a list
        of json objects and dump/save it into a single json file.
        emgfile = {
            "SOURCE": SOURCE,
            "FILENAME": FILENAME,
            "RAW_SIGNAL": RAW_SIGNAL,
            "REF_SIGNAL": REF_SIGNAL,
            "PNR": PNR,
            "SIL": SIL
            "IPTS": IPTS,
            "MUPULSES": MUPULSES,
            "FSAMP": FSAMP,
            "IED": IED,
            "EMG_LENGTH": EMG_LENGTH,
            "NUMBER_OF_MUS": NUMBER_OF_MUS,
            "BINARY_MUS_FIRING": BINARY_MUS_FIRING,
        }
        """
        # str or int
        # Directly convert the ditionary to a json format
        source = {"SOURCE": emgfile["SOURCE"]}
        filename = {"FILENAME": emgfile["FILENAME"]}
        fsamp = {"FSAMP": emgfile["FSAMP"]}
        ied = {"IED": emgfile["IED"]}
        emg_length = {"EMG_LENGTH": emgfile["EMG_LENGTH"]}
        number_of_mus = {"NUMBER_OF_MUS": emgfile["NUMBER_OF_MUS"]}
        source = json.dumps(source)
        filename = json.dumps(filename)
        fsamp = json.dumps(fsamp)
        ied = json.dumps(ied)
        emg_length = json.dumps(emg_length)
        number_of_mus = json.dumps(number_of_mus)

        # Extract the df from the dict, convert the dict to a json, put the
        # json in a dict, convert the dict to a json.
        # We use dict converted to json to locate better the objects while
        # re-importing them in python.
        raw_signal = emgfile["RAW_SIGNAL"]
        ref_signal = emgfile["REF_SIGNAL"]
        pnr = emgfile["PNR"]
        sil = emgfile["SIL"]
        ipts = emgfile["IPTS"]
        binary_mus_firing = emgfile["BINARY_MUS_FIRING"]

        raw_signal = raw_signal.to_json()
        ref_signal = ref_signal.to_json()
        pnr = pnr.to_json()
        sil = sil.to_json()
        ipts = ipts.to_json()
        binary_mus_firing = binary_mus_firing.to_json()

        raw_signal = {"RAW_SIGNAL": raw_signal}
        ref_signal = {"REF_SIGNAL": ref_signal}
        pnr = {"PNR": pnr}
        sil = {"SIL": sil}
        ipts = {"IPTS": ipts}
        binary_mus_firing = {"BINARY_MUS_FIRING": binary_mus_firing}

        raw_signal = json.dumps(raw_signal)
        ref_signal = json.dumps(ref_signal)
        pnr = json.dumps(pnr)
        sil = json.dumps(sil)
        ipts = json.dumps(ipts)
        binary_mus_firing = json.dumps(binary_mus_firing)

        # list of ndarray.
        # Every array has to be converted in a list; then, the list of lists
        # can be converted to json.
        mupulses = []
        for ind, array in enumerate(emgfile["MUPULSES"]):
            mupulses.insert(ind, array.tolist())
        mupulses = json.dumps(mupulses)

        # Convert a list of json objects to json. The result of the conversion
        # will be saved as the final json file.
        # Don't alter this order unless you modify also the emg_from_json
        # function.
        list_to_save = [
            source,
            filename,
            raw_signal,
            ref_signal,
            pnr,
            sil,
            ipts,
            mupulses,
            fsamp,
            ied,
            emg_length,
            number_of_mus,
            binary_mus_firing,
        ]
        json_to_save = json.dumps(list_to_save)

        # Compress and write the json file
        # From: https://stackoverflow.com/questions/39450065/python-3-read-write-compressed-json-objects-from-to-gzip-file
        with gzip.open(filepath, "w") as f:
            # Encode json
            json_bytes = json_to_save.encode("utf-8")
            # Write to a file
            f.write(json_bytes)
            # To improve writing time, f.write is the bottleneck but it is
            # hard to improve.

    elif emgfile["SOURCE"] == "OTB_REFSIG":
        """
        refsig =   {
                "SOURCE" : SOURCE,
                "FILENAME": FILENAME,
                "FSAMP" : FSAMP,
                "REF_SIGNAL" : REF_SIGNAL,
                }
        """
        # str or int
        source = {"SOURCE": emgfile["SOURCE"]}
        filename = {"FILENAME": emgfile["FILENAME"]}
        fsamp = {"FSAMP": emgfile["FSAMP"]}
        source = json.dumps(source)
        filename = json.dumps(filename)
        fsamp = json.dumps(fsamp)
        # df
        ref_signal = emgfile["REF_SIGNAL"]
        ref_signal = ref_signal.to_json()
        ref_signal = {"REF_SIGNAL": ref_signal}
        ref_signal = json.dumps(ref_signal)
        # Merge all the objects in one
        list_to_save = [source, filename, fsamp, ref_signal]
        json_to_save = json.dumps(list_to_save)
        # Compress and save
        with gzip.open(filepath, "w") as f:
            json_bytes = json_to_save.encode("utf-8")
            f.write(json_bytes)

    else:
        raise Exception("File source not recognised")


def emg_from_json(filepath):
    """
    Load the emgfile or emg_refsig stored in json format.

    Parameters
    ----------
    filepath : str or Path
        The directory and the name of the file to load (including file
        extension .json).
        This can be a simple string, the use of Path is not necessary.

    Returns
    -------
    emgfile : dict
        The dictionary containing the emgfile.

    See also
    --------
    - emg_from_demuse : import the .mat file used in DEMUSE.
    - emg_from_otb : import the .mat file exportable by OTBiolab+.
    - refsig_from_otb : import REF_SIGNAL in the .mat file exportable by
        OTBiolab+.
    - emg_from_customcsv : import custom data from a .csv file.

    Notes
    -----
    The returned file is called ``emgfile`` for convention
    (or ``emg_refsig`` if SOURCE = "OTB_REFSIG").

    Examples
    --------
    For an extended explanation of the imported emgfile use:

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile()
    >>> info = emg.info()
    >>> info.data(emgfile)
    """

    # Read and decompress json file
    with gzip.open(filepath, "r") as fin:
        json_bytes = fin.read()
        # Decode json file
        json_str = json_bytes.decode("utf-8")
        jsonemgfile = json.loads(json_str)

    """
    print(type(jsonemgfile))
    <class 'list'>
    print(len(jsonemgfile))
    11
    """
    # Access the dictionaries and extract the data
    # jsonemgfile[0] contains the SOURCE in a dictionary
    source_dict = json.loads(jsonemgfile[0])
    source = source_dict["SOURCE"]
    # jsonemgfile[1] contains the FILENAME in all the sources
    filename_dict = json.loads(jsonemgfile[1])
    filename = filename_dict["FILENAME"]

    if source in ["DEMUSE", "OTB", "CUSTOM"]:
        # jsonemgfile[2] contains the RAW_SIGNAL in a dictionary, it can be
        # extracted in a new dictionary and converted into a pd.DataFrame.
        # index and columns are imported as str, we need to convert it to int.
        raw_signal_dict = json.loads(jsonemgfile[2])
        raw_signal_dict = json.loads(raw_signal_dict["RAW_SIGNAL"])
        raw_signal = pd.DataFrame(raw_signal_dict)
        raw_signal.columns = raw_signal.columns.astype(int)
        raw_signal.index = raw_signal.index.astype(int)
        raw_signal.sort_index(inplace=True)
        # jsonemgfile[3] contains the REF_SIGNAL to be treated as jsonemgfile[2]
        ref_signal_dict = json.loads(jsonemgfile[3])
        ref_signal_dict = json.loads(ref_signal_dict["REF_SIGNAL"])
        ref_signal = pd.DataFrame(ref_signal_dict)
        ref_signal.columns = ref_signal.columns.astype(int)
        ref_signal.index = ref_signal.index.astype(int)
        ref_signal.sort_index(inplace=True)
        # jsonemgfile[4] contains the PNR to be treated as jsonemgfile[2]
        pnr_dict = json.loads(jsonemgfile[4])
        pnr_dict = json.loads(pnr_dict["PNR"])
        pnr = pd.DataFrame(pnr_dict)
        pnr.columns = pnr.columns.astype(int)
        pnr.index = pnr.index.astype(int)
        pnr.sort_index(inplace=True)
        # jsonemgfile[5] contains the SIL to be treated as jsonemgfile[2]
        sil_dict = json.loads(jsonemgfile[5])
        sil_dict = json.loads(sil_dict["SIL"])
        sil = pd.DataFrame(sil_dict)
        sil.columns = sil.columns.astype(int)
        sil.index = sil.index.astype(int)
        sil.sort_index(inplace=True)
        # jsonemgfile[6] contains the IPTS to be treated as jsonemgfile[2]
        ipts_dict = json.loads(jsonemgfile[6])
        ipts_dict = json.loads(ipts_dict["IPTS"])
        ipts = pd.DataFrame(ipts_dict)
        ipts.columns = ipts.columns.astype(int)
        ipts.index = ipts.index.astype(int)
        ipts.sort_index(inplace=True)
        # jsonemgfile[7] contains the MUPULSES which is a list of lists but
        # has to be converted in a list of ndarrays.
        mupulses = json.loads(jsonemgfile[7])
        for num, element in enumerate(mupulses):
            mupulses[num] = np.array(element)
        # jsonemgfile[8] contains the FSAMP to be treated as jsonemgfile[0]
        fsamp_dict = json.loads(jsonemgfile[8])
        fsamp = int(fsamp_dict["FSAMP"])
        # jsonemgfile[9] contains the IED to be treated as jsonemgfile[0]
        ied_dict = json.loads(jsonemgfile[9])
        ied = int(ied_dict["IED"])
        # jsonemgfile[10] contains the EMG_LENGTH to be treated as jsonemgfile[0]
        emg_length_dict = json.loads(jsonemgfile[10])
        emg_length = int(emg_length_dict["EMG_LENGTH"])
        # jsonemgfile[11] contains the NUMBER_OF_MUS to be treated as
        # jsonemgfile[0]
        number_of_mus_dict = json.loads(jsonemgfile[11])
        number_of_mus = int(number_of_mus_dict["NUMBER_OF_MUS"])
        # jsonemgfile[12] contains the BINARY_MUS_FIRING to be treated as
        # jsonemgfile[2]
        binary_mus_firing_dict = json.loads(jsonemgfile[12])
        binary_mus_firing_dict = json.loads(binary_mus_firing_dict["BINARY_MUS_FIRING"])
        binary_mus_firing = pd.DataFrame(binary_mus_firing_dict)
        binary_mus_firing.columns = binary_mus_firing.columns.astype(int)
        binary_mus_firing.index = binary_mus_firing.index.astype(int)

        emgfile = {
            "SOURCE": source,
            "FILENAME": filename,
            "RAW_SIGNAL": raw_signal,
            "REF_SIGNAL": ref_signal,
            "PNR": pnr,
            "SIL": sil,
            "IPTS": ipts,
            "MUPULSES": mupulses,
            "FSAMP": fsamp,
            "IED": ied,
            "EMG_LENGTH": emg_length,
            "NUMBER_OF_MUS": number_of_mus,
            "BINARY_MUS_FIRING": binary_mus_firing,
        }

    elif source == "OTB_REFSIG":
        # jsonemgfile[2] contains the fsamp
        fsamp_dict = json.loads(jsonemgfile[2])
        fsamp = int(fsamp_dict["FSAMP"])
        # jsonemgfile[3] contains the REF_SIGNAL
        ref_signal_dict = json.loads(jsonemgfile[3])
        ref_signal_dict = json.loads(ref_signal_dict["REF_SIGNAL"])
        ref_signal = pd.DataFrame(ref_signal_dict)
        ref_signal.columns = ref_signal.columns.astype(int)
        ref_signal.index = ref_signal.index.astype(int)
        ref_signal.sort_index(inplace=True)

        emgfile = {
            "SOURCE": source,
            "FILENAME": filename,
            "FSAMP": fsamp,
            "REF_SIGNAL": ref_signal,
        }

    else:
        raise Exception("File source not recognised")

    return emgfile


# ---------------------------------------------------------------------
# Function to open files from a GUI in a single line of code.

def askopenfile(initialdir="/", filesource="OPENHDEMG", **kwargs):
    """
    Select and open files with a GUI.

    Parameters
    ----------
    initialdir : str or Path, default "/"
        The directory of the file to load (excluding file name).
        This can be a simple string, the use of Path is not necessary.
    filesource : str {"OPENHDEMG", "DEMUSE", "OTB", "OTB_REFSIG", "CUSTOM"}, default "OPENHDEMG"
        See notes for how files should be exported from OTB.

        ``DEMUSE``
            File saved from DEMUSE (.mat).
        ``OTB``
            File exported from OTB with decomposition and reference signal
            (.mat).
        ``OTB_REFSIG``
            File exported from OTB with only the reference signal (.mat).
        ``CUSTOM``
            Custom file format (.csv).
        ``OPENHDEMG``
            File saved from openhdemg (.json).
    otb_ext_factor : int, default 8
        The extension factor used for the decomposition in the OTbiolab+
        software.
        Ignore if loading other files.
    otb_refsig_type : list, default [True, "fullsampled"]
        Whether to seacrh also for the REF_SIGNAL and whether to load the full
        or sub-sampled one. The list is composed as [bool, str]. str can be
        "fullsampled" or "subsampled".
        Ignore if loading other files.
    otb_version : str, default "1.5.8.0"
        Version of the OTBiolab+ software used (4 points).
        Tested versions are:
            "1.5.3.0",
            "1.5.4.0",
            "1.5.5.0",
            "1.5.6.0",
            "1.5.7.2",
            "1.5.7.3",
            "1.5.8.0",
        If your specific version is not available in the tested versions,
        trying with the closer one usually works, but please double check the
        results. Ignore if loading other files.
    custom_ref_signal : str, default 'REF_SIGNAL'
        Label of the column(s) containing the reference signal of the custom
        file.
        This and the following arguments are needed only for custom files.
        Ignore if loading other files.
    custom_raw_signal : str, default 'RAW_SIGNAL'
        Label of the column(s) containing the raw emg signal of the custom
        file. Ignore if loading other files.
    custom_ipts : str, default 'IPTS'
        Label of the column(s) containing the pulse train of the custom file.
        Ignore if loading other files.
    custom_mupulses : str, default 'MUPULSES'
        Label of the column(s) containing the times of firing of the custom
        file. Ignore if loading other files.
    custom_binary_mus_firing : str, default 'BINARY_MUS_FIRING'
        Label of the column(s) containing the binary representation
        of the MUs firings of the custom file.
        Ignore if loading other files.
    custom_fsamp : int, default 2048
        Tha sampling frequency of the custom file.
        Ignore if loading other files.
    custom_ied : int, default 8
        The inter-electrode distance in mm of the custom file.
        Ignore if loading other files.

    Returns
    -------
    emgfile : dict
        The dictionary containing the emgfile.

    See also
    --------
    - asksavefile : select where to save files with a GUI.

    Notes
    -----
    The returned file is called ``emgfile`` for convention (or ``emg_refsig``
    if SOURCE = "OTB_REFSIG").

    The input .mat file exported from the OTBiolab+ software should have a
    specific content:
    - refsig signal is optional but, if present, there should be both the
        fullsampled and the subsampled version (in OTBioLab+ the "performed
        path" refers to the subsampled signal, the "acquired data" to the
        fullsampled signal), REF_SIGNAL is expected to be expressed as % of
        the MViF (but not compulsory).
    - Both the IPTS ('Source for decomposition...' in OTBioLab+) and the
        BINARY_MUS_FIRING ('Decomposition of...' in OTBioLab+) should be
        present.
    - The raw EMG signal should be present (it has no specific name in
        OTBioLab+) with all the channels. Don't exclude unwanted channels
        before exporting the .mat file.
    - NO OTHER ELEMENTS SHOULD BE PRESENT!

    For custom .csv files:
    The variables of interest should be contained in columns. The name of the
    columns containing each variable can be specified by the user if different
    from the default values.
    This function detects the content of the .csv by parsing the .csv columns.
    For parsing, column labels should be provided. A label is a term common
    to all the columns containing the same information.
    For example, if the raw signal is contained in the columns 'RAW_SIGNAL_1',
    'RAW_SIGNAL_2', ... , 'RAW_SIGNAL_n', the label of the columns should be
    'RAW_SIGNAL'.
    If the parameters in input are not present in the .csv file, the user
    can simply leave the original inputs.
    Please see the documentation of the function emg_from_customcsv for
    additional informations.

    Structure of the returned emgfile:
        emgfile = {
            "SOURCE": SOURCE,
            "FILENAME": FILENAME,
            "RAW_SIGNAL": RAW_SIGNAL,
            "REF_SIGNAL": REF_SIGNAL,
            "PNR": PNR,
            "SIL": SIL,
            "IPTS": IPTS,
            "MUPULSES": MUPULSES,
            "FSAMP": FSAMP,
            "IED": IED,
            "EMG_LENGTH": EMG_LENGTH,
            "NUMBER_OF_MUS": NUMBER_OF_MUS,
            "BINARY_MUS_FIRING": BINARY_MUS_FIRING,
        }

    Structure of the returned emg_refsig:
        emg_refsig = {
            "SOURCE": SOURCE,
            "FILENAME": FILENAME,
            "FSAMP": FSAMP,
            "REF_SIGNAL": REF_SIGNAL,
        }

    Examples
    --------
    For an extended explanation of the imported emgfile use:

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile()
    >>> info = emg.info()
    >>> info.data(emgfile)
    """

    # Set initialdir (actually not working on Windows)
    if isinstance(initialdir, str):
        if initialdir == "/":
            initialdir = "/Decomposed Test files/"

    # Create and hide the tkinter root window necessary for the GUI based
    # open-file function
    root = Tk()
    root.withdraw()

    if filesource in ["DEMUSE", "OTB", "OTB_REFSIG"]:
        file_toOpen = filedialog.askopenfilename(
            initialdir=initialdir,
            title=f"Select a {filesource} file to load",
            filetypes=[("MATLAB files", ".mat")],
        )
    elif filesource == "OPENHDEMG":
        file_toOpen = filedialog.askopenfilename(
            initialdir=initialdir,
            title="Select an OPENHDEMG file to load",
            filetypes=[("JSON files", ".json")],
        )
    elif filesource == "CUSTOM":  # TODO add custom_refignal
        file_toOpen = filedialog.askopenfilename(
            initialdir=initialdir,
            title="Select a custom file to load",
            filetypes=[("CSV files", ".csv")],
        )
    else:
        raise Exception(
            "filesource not valid, it must be one of 'DEMUSE', 'OTB', 'OTB_REFSIG', 'OPENHDEMG' or 'CUSTOM'"
        )

    # Destroy the root since it is no longer necessary
    root.destroy()

    # Open file depending on file origin
    if filesource == "DEMUSE":
        emgfile = emg_from_demuse(filepath=file_toOpen)
    elif filesource == "OTB":
        emgfile = emg_from_otb(
            filepath=file_toOpen,
            ext_factor=kwargs.get("otb_ext_factor", 8),
            refsig=kwargs.get("otb_refsig_type", [True, "fullsampled"]),
            version=kwargs.get("otb_version", "1.5.8.0")
        )
    elif filesource == "OTB_REFSIG":
        ref = kwargs.get("otb_refsig_type", [True, "fullsampled"])
        emgfile = refsig_from_otb(
            filepath=file_toOpen,
            refsig=ref[1],
            version=kwargs.get("otb_version", "1.5.8.0"),
        )
    elif filesource == "OPENHDEMG":
        emgfile = emg_from_json(filepath=file_toOpen)
    else:  # custom
        emgfile = emg_from_customcsv(
            filepath=file_toOpen,
            ref_signal=kwargs.get("custom_ref_signal", "REF_SIGNAL"),
            raw_signal=kwargs.get("custom_raw_signal", "RAW_SIGNAL"),
            ipts=kwargs.get("custom_ipts", "IPTS"),
            mupulses=kwargs.get("custom_mupulses", "MUPULSES"),
            binary_mus_firing=kwargs.get(
                "custom_binary_mus_firing",
                "BINARY_MUS_FIRING"
            ),
            fsamp=kwargs.get("custom_fsamp", 2048),
            ied=kwargs.get("custom_ied", 8),
        )

    print("\n-----------\nFile loaded\n-----------\n")

    return emgfile


def asksavefile(emgfile):
    """
    Select where to save files with a GUI.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile to save.

    See also
    --------
    - askopenfile : select and open files with a GUI.
    """

    # Create and hide the tkinter root window necessary for the GUI based
    # open-file function
    root = Tk()
    root.withdraw()

    filepath = filedialog.asksaveasfilename(
        defaultextension=".json",
        filetypes=[("json files", "*.json")],
        title="Save JSON file",
    )

    # Destroy the root since it is no longer necessary
    root.destroy()

    print("\n-----------\nSaving file\n")

    save_json_emgfile(emgfile, filepath)

    print("File saved\n-----------\n")


def emg_from_samplefile():
    """
    Load the sample file. This file has been decomposed with the OTBiolab+
    software and contains some reference MUs together with the force/reference
    signal.

    This file contains only few MUs for storage reasons.

    Returns
    -------
    emgfile : dict
        The dictionary containing the emgfile.
    """

    # Get the absolute path to the script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the absolute path to the file in the data subfolder
    file_path = os.path.join(
        script_dir,
        'decomposed_test_files',
        'otb_testfile.mat',
    )

    # Load the file
    emgfile = emg_from_otb(
        filepath=file_path,
        ext_factor=8,
        refsig=[True, "fullsampled"],
        version="1.5.8.0",
    )

    return emgfile
