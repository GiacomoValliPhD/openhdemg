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
emg_from_customcsv :
    Used to load custom file formats contained in .csv files.
refsig_from_otb and refsig_from_customcsv:
    Used to load files from the OTBiolab+ software or from a custom .csv file
    that contain only the REF_SIGNAL.
save_json_emgfile, emg_from_json :
    Used to save the working file to a .json file or to load the .json
    file.
askopenfile, asksavefile :
    A quick GUI implementation that allows users to select the file to
    open or save.

Notes
-----
Once opened, the file is returned as a dict with keys:
    "SOURCE" : source of the file (i.e., "CUSTOMCSV", "DEMUSE", "OTB")
    "FILENAME" : the name of the opened file
    "RAW_SIGNAL" : the raw EMG signal
    "REF_SIGNAL" : the reference signal
    "ACCURACY" : accuracy score (depending on source file type)
    "IPTS" : pulse train (decomposed source)
    "MUPULSES" : instants of firing
    "FSAMP" : sampling frequency
    "IED" : interelectrode distance
    "EMG_LENGTH" : length of the emg file (in samples)
    "NUMBER_OF_MUS" : total number of MUs
    "BINARY_MUS_FIRING" : binary representation of MUs firings
    "EXTRAS" : additional custom values

The only exception is when files are loaded with just the reference signal:
    "SOURCE": source of the file (i.e., "CUSTOMCSV_REFSIG", "OTB_REFSIG")
    "FILENAME" : the name of the opened file
    "FSAMP": sampling frequency
    "REF_SIGNAL": the reference signal
    "EXTRAS" : additional custom values

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
#         refsig_from_customcsv
#         save_json_emgfile,
#         emg_from_json,
#         askopenfile,
#         asksavefile,
#         emg_from_samplefile,
#     ) # TODO add emg_from_delsys here, in init, in upper description and in docs description


from scipy.io import loadmat
import pandas as pd
import numpy as np
from openhdemg.library.electrodes import *
from openhdemg.library.mathtools import compute_sil
from openhdemg.library.tools import create_binary_firings, mupulses_from_binary
from tkinter import *
from tkinter import filedialog
import json
import gzip
import warnings
import os


# --------------------------------------------------------------------- #
# Main function to open decomposed files coming from DEMUSE.

def emg_from_demuse(filepath):
    """
    Import the .mat file decomposed in DEMUSE.

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
    - emg_from_otb : import the decomposed .mat file exportable by OTBiolab+.
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
            "ACCURACY": SIL
            "IPTS": IPTS,
            "MUPULSES": MUPULSES,
            "FSAMP": FSAMP,
            "IED": IED,
            "EMG_LENGTH": EMG_LENGTH,
            "NUMBER_OF_MUS": NUMBER_OF_MUS,
            "BINARY_MUS_FIRING": BINARY_MUS_FIRING,
            "EXTRAS": EXTRAS,
        }

    For DEMUSE files, the accuracy is estimated with the silhouette (SIL)
    score.

    Examples
    --------
    For an extended explanation of the imported emgfile:

    >>> import openhdemg.library as emg
    >>> emgfile = emg.emg_from_demuse(filepath="path/filename.mat")
    >>> info = emg.info()
    >>> info.data(emgfile)
    """

    # Load the .mat file
    mat_file = loadmat(filepath, simplify_cells=True)

    # Parse .mat obtained from DEMUSE to see the available variables
    """
    print(
        "\n--------------------------------\nAvailable dict keys are:\n\n{}\n".format(
            mat_file.keys()
        )
    )
    """

    # First, get the basic information and compulsory variables (i.e.,
    # RAW_SIGNAL, IPTS, MUPULSES, BINARY_MUS_FIRING) in a pd.DataFrame (df) or
    # list (for matlab cell arrays).

    # Use this to know the data source and name of the file
    SOURCE = "DEMUSE"
    FILENAME = os.path.basename(filepath)
    FSAMP = float(mat_file["fsamp"])
    IED = float(mat_file["IED"])

    # Get RAW_SIGNAL
    if "SIG" in mat_file.keys():
        mat = mat_file["SIG"].ravel(order="F")
        # "F" means to index the elements in column-major
        RAW_SIGNAL = pd.DataFrame(list(map(np.ravel, mat))).transpose()

    else:
        raise ValueError(
            "\nVariable 'SIG' not found in the .mat file\n"
        )

    # Get IPTS
    if "IPTs" in mat_file.keys():
        # Catch the exception of a single MU that would create an alrerady
        # transposed pd.DataFrame
        if len(mat_file["IPTs"].shape) == 1:
            IPTS = pd.DataFrame(mat_file["IPTs"])

        else:
            IPTS = pd.DataFrame(mat_file["IPTs"]).transpose()

    else:
        raise ValueError(
            "\nVariable 'IPTS' not found in the .mat file\n"
        )

    # Get EMG_LENGTH and NUMBER_OF_MUS
    EMG_LENGTH, NUMBER_OF_MUS = IPTS.shape

    # Get MUPULSES/BINARY_MUS_FIRING
    # Subtract 1 to MUPULSES because these are values in base 1 (MATLAB) and
    # manage exception of single MU thah would create a list and not a list of
    # arrays.
    if "MUPulses" in mat_file.keys():
        MUPULSES = list(mat_file["MUPulses"])
        for pos, pulses in enumerate(MUPULSES):
            MUPULSES[pos] = pulses - 1

        if NUMBER_OF_MUS == 1:
            MUPULSES = [np.array(MUPULSES)]

    else:
        raise ValueError(
            "\nVariable 'MUPulses' not found in the .mat file\n"
        )

    # Calculate BINARY_MUS_FIRING
    BINARY_MUS_FIRING = create_binary_firings(
        emg_length=EMG_LENGTH,
        number_of_mus=NUMBER_OF_MUS,
        mupulses=MUPULSES,
    )

    # Second, get/generate the other variables
    # Get REF_SIGNAL
    if "ref_signal" in mat_file.keys():
        # Catch the case for float values that cannot be directly added to a
        # dataframe
        if isinstance(mat_file["ref_signal"], float):
            res = {0: mat_file["ref_signal"]}
            REF_SIGNAL = pd.DataFrame(res, index=[0])

        else:
            REF_SIGNAL = pd.DataFrame(mat_file["ref_signal"])

    else:
        REF_SIGNAL = pd.DataFrame(columns=[0])
        warnings.warn(
            "\nVariable ref_signal not found in the .mat file, it might be necessary for some analyses\n"
        )

    # Estimate ACCURACY (SIL)
    if NUMBER_OF_MUS > 0:
        to_append = []
        for mu in range(NUMBER_OF_MUS):
            sil = compute_sil(ipts=IPTS[mu], mupulses=MUPULSES[mu])
            to_append.append(sil)
        ACCURACY = pd.DataFrame(to_append)

    else:
        ACCURACY = pd.DataFrame(columns=[0])

    emgfile = {
        "SOURCE": SOURCE,
        "FILENAME": FILENAME,
        "RAW_SIGNAL": RAW_SIGNAL,
        "REF_SIGNAL": REF_SIGNAL,
        "ACCURACY": ACCURACY,
        "IPTS": IPTS,
        "MUPULSES": MUPULSES,
        "FSAMP": FSAMP,
        "IED": IED,
        "EMG_LENGTH": EMG_LENGTH,
        "NUMBER_OF_MUS": NUMBER_OF_MUS,
        "BINARY_MUS_FIRING": BINARY_MUS_FIRING,
        "EXTRAS": pd.DataFrame(columns=[0]),
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
    ], f"refsig[0] must be 'true' or 'false'. {refsig[0]} was passed instead."
    assert refsig[1] in [
        "fullsampled",
        "subsampled",
    ], f"refsig[1] must be 'fullsampled' or 'subsampled'. {refsig[1]} was passed instead."

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
                        "\nALERT! Ref signal greater than 100, did you use values normalised to the MVC?\n"
                    )

                return REF_SIGNAL_SUBSAMPLED

            else:
                warnings.warn(
                    "\nReference signal not found, it might be necessary for some analyses\n"
                )

                return pd.DataFrame(columns=[0])

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
                    "\nReference signal not found, it might be necessary for some analyses\n"
                )

                return pd.DataFrame(columns=[0])

    else:
        warnings.warn("\nNot searched for reference signal, it might be necessary for some analyses\n")

        return pd.DataFrame(columns=[0])


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
        raise ValueError(
            "\nSource for decomposition (IPTS) not found in the .mat file\n"
        )

    # Extract the BINARY_MUS_FIRING and rename columns progressively
    BINARY_MUS_FIRING = df.filter(regex="Decomposition of")
    BINARY_MUS_FIRING.columns = np.arange(len(BINARY_MUS_FIRING.columns))
    # Verify to have the BINARY_MUS_FIRING
    if BINARY_MUS_FIRING.empty:
        raise ValueError(
            "\nDecomposition of (BINARY_MUS_FIRING) not found in the .mat file\n"
        )

    return IPTS, BINARY_MUS_FIRING


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
    IED : float
        The interelectrode distance in millimeters.
    """

    for matrix in OTBelectrodes_ied.keys():
        # Check the matrix used in the columns name
        # (in the df obtained from OTBiolab+)
        if matrix in str(df.columns):
            IED = float(OTBelectrodes_ied[matrix])

            return IED

    # If no matrix is found and we exit the loop:
    warnings.warn(
        "OTB recording grid not found, IED could not be inferred"
    )

    return np.nan


def get_otb_rawsignal(df, extras_regex):
    """
    Extract the raw signal from the OTB .mat file.

    Parameters
    ----------
    df : pd.DataFrame
        A pd.DataFrame containing all the informations extracted
        from the OTB .mat file.
    extras_regex : str
        A regex pattern unequivocally identifying the EXTRAS.

    Returns
    -------
    RAW_SIGNAL : pd.DataFrame
        A pd.DataFrame containing the RAW_SIGNAL.
    """

    # Drop all the known columns different from the raw EMG signal.
    # This is a workaround since the OTBiolab+ software does not export a
    # unique name for the raw EMG signal.
    base_pattern = "Source for decomposition|Decomposition of|acquired data|performed path"
    pattern = base_pattern + "|" + extras_regex
    emg_df = df[df.columns.drop(list(df.filter(regex=pattern)))]

    # Check if the number of remaining columns matches the expected number of
    # matrix channels.
    expectedchannels = np.nan
    for matrix in OTBelectrodes_Nelectrodes.keys():
        # Check the matrix used in the columns name (in the emg_df) to know
        # the number of expected channels.
        if matrix in str(emg_df.columns):
            expectedchannels = int(OTBelectrodes_Nelectrodes[matrix])
            break

    if expectedchannels is np.nan:
        raise ValueError("Matrix not recognised")

    if len(emg_df.columns) == expectedchannels:
        emg_df.columns = np.arange(len(emg_df.columns))
        RAW_SIGNAL = emg_df

        return RAW_SIGNAL

    else:
        # This check here is usefull to control that only the appropriate
        # elements have been included in the .mat file exported from OTBiolab+.
        raise ValueError(
            "\nFailure in searching the raw signal, please check that it is present in the .mat file and that only the accepted parameters have been included\n"
        )


def get_otb_extras(df, extras):
    """
    Extract the EXTRAS from the OTB .mat file.

    Parameters
    ----------
    df : pd.DataFrame
        A pd.DataFrame containing all the informations extracted
        from the OTB .mat file.

    Returns
    -------
    EXTRAS : pd.DataFrame
        A pd.DataFrame containing the EXTRAS.
    """

    if extras is None:

        return pd.DataFrame(columns=[0])

    else:
        EXTRAS = df.filter(regex=extras)

        return EXTRAS


# ---------------------------------------------------------------------
# Main function to open decomposed files coming from OTBiolab+.
# This function calls the functions defined above

def emg_from_otb(
    filepath,
    ext_factor=8,
    refsig=[True, "fullsampled"],
    version="1.5.8.0",
    extras=None,
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
    extras : None or str, default None
        Extras is used to store additional custom values. These information
        will be stored in a pd.DataFrame with columns named as in the .mat
        file. If not None, pass a regex pattern unequivocally identifying the
        variable in the .mat file to load as extras.

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

    The input .mat file exported from the OTBiolab+ software must have a
    specific content:
    - refsig signal is optional but, if present, there should be the
        fullsampled or the subsampled version (in OTBioLab+ the "performed
        path" refers to the subsampled signal, the "acquired data" to the
        fullsampled signal), REF_SIGNAL is expected to be expressed as % of
        the MVC (but not compulsory).
    - Both the IPTS ('Source for decomposition...' in OTBioLab+) and the
        BINARY_MUS_FIRING ('Decomposition of...' in OTBioLab+) must be
        present.
    - The raw EMG signal must be present (it has no specific name in
        OTBioLab+) with all the channels. Don't exclude unwanted channels
        before exporting the .mat file.
    - NO OTHER ELEMENTS SHOULD BE PRESENT, unless an appropriate regex pattern
    is passed to 'extras='!

    Structure of the returned emgfile:
        emgfile = {
            "SOURCE": SOURCE,
            "FILENAME": FILENAME,
            "RAW_SIGNAL": RAW_SIGNAL,
            "REF_SIGNAL": REF_SIGNAL,
            "ACCURACY": SIL,
            "IPTS": IPTS,
            "MUPULSES": MUPULSES,
            "FSAMP": FSAMP,
            "IED": IED,
            "EMG_LENGTH": EMG_LENGTH,
            "NUMBER_OF_MUS": NUMBER_OF_MUS,
            "BINARY_MUS_FIRING": BINARY_MUS_FIRING,
            "EXTRAS": EXTRAS,
        }

    For OTBiolab+ files, the accuracy is estimated with the silhouette (SIL)
    score.

    Examples
    --------
    For an extended explanation of the imported emgfile use:

    >>> import openhdemg.library as emg
    >>> emgfile = emg.emg_from_otb(filepath="path/filename.mat")
    >>> info = emg.info()
    >>> info.data(emgfile)
    """

    mat_file = loadmat(filepath, simplify_cells=True)

    # Parse .mat obtained from OTBiolab+ to see the available variables
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
            f"\nSpecified version is not valid. Use one of:\n{valid_versions}\n"
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
        df = pd.DataFrame(mat_file["Data"], columns=mat_file["Description"])

        # First, get the basic information and compulsory variables (i.e.,
        # RAW_SIGNAL, IPTS, MUPULSES, BINARY_MUS_FIRING) in a pd.DataFrame (df) or
        # list (for matlab cell arrays).

        # Use this to know the data source and name of the file
        SOURCE = "OTB"
        FILENAME = os.path.basename(filepath)
        FSAMP = float(mat_file["SamplingFrequency"])
        IED = get_otb_ied(df=df)

        # Get RAW_SIGNAL
        RAW_SIGNAL = get_otb_rawsignal(df=df, extras_regex=extras)

        # Get IPTS and BINARY_MUS_FIRING
        IPTS, BINARY_MUS_FIRING = get_otb_decomposition(df=df)
        # Align BINARY_MUS_FIRING to IPTS
        BINARY_MUS_FIRING = BINARY_MUS_FIRING.shift(- int(ext_factor))
        BINARY_MUS_FIRING.fillna(value=0, inplace=True)

        # Get MUPULSES
        MUPULSES = mupulses_from_binary(binarymusfiring=BINARY_MUS_FIRING)

        # Get EMG_LENGTH and NUMBER_OF_MUS
        EMG_LENGTH, NUMBER_OF_MUS = IPTS.shape

        # Get REF_SIGNAL
        REF_SIGNAL = get_otb_refsignal(df=df, refsig=refsig)

        # Estimate ACCURACY (SIL)
        if NUMBER_OF_MUS > 0:
            to_append = []
            for mu in range(NUMBER_OF_MUS):
                sil = compute_sil(ipts=IPTS[mu], mupulses=MUPULSES[mu])
                to_append.append(sil)
            ACCURACY = pd.DataFrame(to_append)

        else:
            ACCURACY = pd.DataFrame(columns=[0])

        # Get EXTRAS
        EXTRAS = get_otb_extras(df=df, extras=extras)

    emgfile = {
        "SOURCE": SOURCE,
        "FILENAME": FILENAME,
        "RAW_SIGNAL": RAW_SIGNAL,
        "REF_SIGNAL": REF_SIGNAL,
        "ACCURACY": ACCURACY,
        "IPTS": IPTS,
        "MUPULSES": MUPULSES,
        "FSAMP": FSAMP,
        "IED": IED,
        "EMG_LENGTH": EMG_LENGTH,
        "NUMBER_OF_MUS": NUMBER_OF_MUS,
        "BINARY_MUS_FIRING": BINARY_MUS_FIRING,
        "EXTRAS": EXTRAS,
    }

    return emgfile


# ---------------------------------------------------------------------
# Function to load the reference signal from OBIolab+.

def refsig_from_otb(
    filepath,
    refsig="fullsampled",
    version="1.5.8.0",
    extras=None,
):
    """
    Import the reference signal in the .mat file exportable by OTBiolab+.

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
    extras : None or str, default None
        Extras is used to store additional custom values. These information
        will be stored in a pd.DataFrame with columns named as in the .mat
        file. If not None, pass a regex pattern unequivocally identifying the
        variable in the .mat file to load as extras.

    Returns
    -------
    emg_refsig : dict
        A dictionary containing all the useful variables.

    See also
    --------
    - emg_from_otb : import the .mat file exportable by OTBiolab+.
    - emg_from_demuse : import the .mat file used in DEMUSE.
    - emg_from_customcsv : Import custom data from a .csv file.
    - refsig_from_customcsv : Import the reference signal from a custom .csv.

    Notes
    ---------
    The returned file is called ``emg_refsig`` for convention.

    The input .mat file exported from the OTBiolab+ software must contain:
    - refsig signal: there must be the fullsampled or the subsampled
        version (in OTBioLab+ the "performed path" refers to the subsampled
        signal, the "acquired data" to the fullsampled signal), REF_SIGNAL is
        expected to be expressed as % of the MVC (but not compulsory).
    - NO OTHER ELEMENTS SHOULD BE PRESENT, unless an appropriate regex pattern
    is passed to 'extras='!

    Structure of the returned emg_refsig:
        emg_refsig = {
            "SOURCE": SOURCE,
            "FILENAME": FILENAME,
            "FSAMP": FSAMP,
            "REF_SIGNAL": REF_SIGNAL,
            "EXTRAS": EXTRAS,
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

    # Parse .mat obtained from OTBiolab+ to see the available variables
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
            f"\nSpecified version is not valid. Use one of:\n{valid_versions}\n"
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

        # Use this to know the data source and name of the file
        SOURCE = "OTB_REFSIG"
        FILENAME = os.path.basename(filepath)
        FSAMP = float(mat_file["SamplingFrequency"])

        # Convert the input passed to refsig in a list compatible with the
        # function get_otb_refsignal
        refsig_ = [True, refsig]
        REF_SIGNAL = get_otb_refsignal(df=df, refsig=refsig_)

        # Get EXTRAS
        EXTRAS = get_otb_extras(df=df, extras=extras)

    emg_refsig = {
        "SOURCE": SOURCE,
        "FILENAME": FILENAME,
        "FSAMP": FSAMP,
        "REF_SIGNAL": REF_SIGNAL,
        "EXTRAS": EXTRAS,
    }

    return emg_refsig


# ---------------------------------------------------------------------
# Function to load custom CSV documents.
def emg_from_customcsv(
    filepath,
    ref_signal="REF_SIGNAL",
    raw_signal="RAW_SIGNAL",
    ipts="IPTS",
    mupulses="MUPULSES",
    binary_mus_firing="BINARY_MUS_FIRING",
    accuracy="ACCURACY",
    extras="EXTRAS",
    fsamp=2048,
    ied=8,
):
    """
    Import the emgfile from a custom .csv file.

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
    should leave the original inputs.

    The .csv file must contain at least the raw_signal and one of 'mupulses' or
    'binary_mus_firing'. If 'mupulses' is absent, it will be calculated from
    'binary_mus_firing' and viceversa.

    Parameters
    ----------
    filepath : str or Path
        The directory and the name of the file to load
        (including file extension .mat).
        This can be a simple string, the use of Path is not necessary.
    ref_signal : str, default 'REF_SIGNAL'
        Label of the column containing the reference signal.
    raw_signal : str, default 'RAW_SIGNAL'
        Label of the column(s) containing the raw emg signal.
    ipts : str, default 'IPTS'
        Label of the column(s) containing the pulse train (decomposed source).
    mupulses : str, default 'MUPULSES'
        Label of the column(s) containing the times of firing.
    binary_mus_firing : str, default 'BINARY_MUS_FIRING'
        Label of the column(s) containing the binary representation
        of the MUs firings.
    accuracy : str, default 'ACCURACY'
        Label of the column(s) containing the accuracy score of the MUs
        firings.
    extras : str, default 'EXTRAS'
        Label of the column(s) containing custom values. This information will
        be stored in a pd.DataFrame with columns named as in the .csv file.
    fsamp : int or float, default 2048
        Tha sampling frequency.
    ied : int or float, default 8
        The inter-electrode distance in mm.

    Returns
    -------
    emgfile : dict
        A dictionary containing all the useful variables.

    See also
    --------
    - emg_from_demuse : import the .mat file used in DEMUSE.
    - emg_from_otb : import the .mat file exportable by OTBiolab+.
    - refsig_from_otb : import reference signal in the .mat file exportable by
        OTBiolab+.
    - refsig_from_customcsv : Import the reference signal from a custom .csv.

    Notes
    -----
    The returned file is called ``emgfile`` for convention.

    Structure of the emgfile:
        emgfile = {
            "SOURCE": SOURCE,
            "FILENAME": FILENAME,
            "RAW_SIGNAL": RAW_SIGNAL,
            "REF_SIGNAL": REF_SIGNAL,
            "ACCURACY": ACCURACY,
            "IPTS": IPTS,
            "MUPULSES": MUPULSES,
            "FSAMP": FSAMP,
            "IED": IED,
            "EMG_LENGTH": EMG_LENGTH,
            "NUMBER_OF_MUS": NUMBER_OF_MUS,
            "BINARY_MUS_FIRING": BINARY_MUS_FIRING,
            "EXTRAS": EXTRAS,
        }

    Examples
    --------
    An example of the .csv file to load:
    >>>
    REF_SIGNAL  RAW_SIGNAL (1)  RAW_SIGNAL (2)  RAW_SIGNAL (3)  RAW_SIGNAL (4)  ...  MUPULSES (2)  BINARY_MUS_FIRING (1)  BINARY_MUS_FIRING (2)  ACCURACY (1)  ACCURACY (2)
             1        0.100000        0.100000        0.100000        0.100000  ...           1.0                      0                      0          0.89          0.95
             2        2.000000        2.000000        2.000000        2.000000  ...           2.0                      0                      0                                  
             3        0.500000        0.500000        0.500000        0.500000  ...           9.0                      0                      0                                  
             4        0.150000        0.150000        0.150000        0.150000  ...          15.0                      0                      1                                  
             5        0.350000        0.350000        0.350000        0.350000  ...          18.0                      1                      1                                  
             6        0.215000        0.215000        0.215000        0.215000  ...          22.0                      1                      0                            

    For an extended explanation of the imported emgfile use:

    >>> import openhdemg.library as emg
    >>> emgfile = emg_from_customcsv(filepath = "mypath/file.csv")
    >>> info = emg.info()
    >>> info.data(emgfile)
    """

    # Load the csv
    csv = pd.read_csv(filepath)

    # First, get the basic information and compulsory variables (i.e.,
    # RAW_SIGNAL, MUPULSES, BINARY_MUS_FIRING).

    # Use this to know the data source and name of the file
    SOURCE = "CUSTOMCSV"
    FILENAME = os.path.basename(filepath)

    # Get RAW_SIGNAL
    RAW_SIGNAL = csv.filter(regex=raw_signal, axis=1).dropna()
    if not RAW_SIGNAL.empty:
        RAW_SIGNAL.columns = [i for i in range(len(RAW_SIGNAL.columns))]
    else:
        raise ValueError(
            "\nraw_signal not found\n"
        )

    # Get MUPULSES/BINARY_MUS_FIRING
    df_mupulses = csv.filter(regex=mupulses, axis=1)
    BINARY_MUS_FIRING = csv.filter(regex=binary_mus_firing, axis=1).dropna()

    if df_mupulses.empty and BINARY_MUS_FIRING.empty:
        raise ValueError(
            "\nmupulses and binary_mus_firing not found. At least one of the two must be present\n")
    elif not df_mupulses.empty and not BINARY_MUS_FIRING.empty:
        MUPULSES = []
        for col in df_mupulses.columns:
            toappend = df_mupulses[col].dropna().to_numpy(dtype=int)
            MUPULSES.append(toappend)

        BINARY_MUS_FIRING.columns = [
            i for i in range(len(BINARY_MUS_FIRING.columns))
        ]

    elif df_mupulses.empty and not BINARY_MUS_FIRING.empty:
        BINARY_MUS_FIRING.columns = [
            i for i in range(len(BINARY_MUS_FIRING.columns))
        ]

        MUPULSES = mupulses_from_binary(binarymusfiring=BINARY_MUS_FIRING)

    else:  # if not df_mupulses.empty and BINARY_MUS_FIRING.empty:
        MUPULSES = []
        for col in df_mupulses.columns:
            toappend = df_mupulses[col].dropna().to_numpy(dtype=int)
            MUPULSES.append(toappend)

        l, _ = RAW_SIGNAL.shape
        BINARY_MUS_FIRING = create_binary_firings(
            emg_length=l,
            number_of_mus=len(MUPULSES),
            mupulses=MUPULSES,
        )

    # Get EMG_LENGTH and NUMBER_OF_MUS
    EMG_LENGTH, NUMBER_OF_MUS = BINARY_MUS_FIRING.shape

    # Second, get/generate the other variables
    # Get REF_SIGNAL
    REF_SIGNAL = csv.filter(regex=ref_signal, axis=1).dropna()
    if not REF_SIGNAL.empty:
        REF_SIGNAL.columns = [i for i in range(len(REF_SIGNAL.columns))]
        if len(REF_SIGNAL.columns) > 1:
            warnings.warn(
                "\nMore than 1 reference signal detected. You should place other signals in 'EXTRAS'\n"
            )
    else:
        REF_SIGNAL = pd.DataFrame(columns=[0])
        warnings.warn(
            "\nref_signal not found, it might be necessary for some analyses\n"
        )  # returns empty pd.DataFrame with 1 column

    # Get IPTS
    IPTS = csv.filter(regex=ipts, axis=1).dropna()
    if not IPTS.empty:
        IPTS.columns = [i for i in range(len(IPTS.columns))]
    else:
        IPTS = pd.DataFrame(columns=[*range(NUMBER_OF_MUS)])
        warnings.warn(
            "\nipts not found, it might be necessary for some analyses\n"
        )  # returns empty pd.DataFrame with n columns

    # Get ACCURACY
    ACCURACY = csv.filter(regex=accuracy, axis=1).dropna()
    if not ACCURACY.empty:
        # Merge all the accuracies of each MU in a single column.
        ACCURACY = ACCURACY.melt(value_name=0).drop(labels="variable", axis=1)
    else:
        ACCURACY = pd.DataFrame(columns=[0])
        warnings.warn(
            "\naccuracy not found. It might be necessary for some analyses\n"
        )  # returns empty pd.DataFrame with 1 column

    # Get EXTRAS
    EXTRAS = csv.filter(regex=extras, axis=1)
    if EXTRAS.empty:
        EXTRAS = pd.DataFrame(columns=[0])
        # returns empty pd.DataFrame with 1 column

    emgfile = {
        "SOURCE": SOURCE,
        "FILENAME": FILENAME,
        "RAW_SIGNAL": RAW_SIGNAL,
        "REF_SIGNAL": REF_SIGNAL,
        "ACCURACY": ACCURACY,
        "IPTS": IPTS,
        "MUPULSES": MUPULSES,
        "FSAMP": float(fsamp),
        "IED": float(ied),
        "EMG_LENGTH": EMG_LENGTH,
        "NUMBER_OF_MUS": NUMBER_OF_MUS,
        "BINARY_MUS_FIRING": BINARY_MUS_FIRING,
        "EXTRAS": EXTRAS,
    }

    return emgfile


# ---------------------------------------------------------------------
# Function to load the reference signal from custom CSV documents.

def refsig_from_customcsv(
    filepath,
    ref_signal="REF_SIGNAL",
    extras="EXTRAS",
    fsamp=2048,
):
    """
    Import the reference signal from a custom .csv file.

    Compared to the function emg_from_customcsv, this function only imports the
    REF_SIGNAL and, therefore, it can be used for special cases where only the
    REF_SIGNAL is necessary. This will allow a faster execution of the script
    and to avoid exceptions for missing data.

    This function detects the content of the .csv by parsing the .csv columns.
    For parsing, column labels should be provided. A label is a term common
    to all the columns containing the same information.
    For example, if the ref signal is contained in the column 'REF_SIGNAL', the
    label of the columns should be 'REF_SIGNAL' or a part of it (e.g., 'REF').
    If the parameters in input are not present in the .csv file (e.g.,
    'EXTRAS'), the user should leave the original inputs.

    Parameters
    ----------
    filepath : str or Path
        The directory and the name of the file to load
        (including file extension .mat).
        This can be a simple string, the use of Path is not necessary.
    ref_signal : str, default 'REF_SIGNAL'
        Label of the column containing the reference signal.
    extras : str, default 'EXTRAS'
        Label of the column(s) containing custom values. These information
        will be stored in a pd.DataFrame with columns named as in the .csv
        file.
    fsamp : int or float, default 2048
        Tha sampling frequency.

    Returns
    -------
    emg_refsig : dict
        A dictionary containing all the useful variables.

    Notes
    ---------
    The returned file is called ``emg_refsig`` for convention.

    Structure of the returned emg_refsig:
        emg_refsig = {
            "SOURCE": SOURCE,
            "FILENAME": FILENAME,
            "FSAMP": FSAMP,
            "REF_SIGNAL": REF_SIGNAL,
        }

    Examples
    --------
    An example of the .csv file to load:
    >>>
    REF_SIGNAL  EXTRAS (1)  EXTRAS (2)
             1         0.1           0
             2         0.2           0
             3         0.3           0
             4         0.4           0
             5         0.5           1
             6         0.6           1

    For an extended explanation of the imported emgfile use:

    >>> import openhdemg.library as emg
    >>> emgfile = refsig_from_customcsv(filepath = "mypath/file.csv")
    >>> info = emg.info()
    >>> info.data(emgfile)
    """

    # Load the csv
    csv = pd.read_csv(filepath)

    # Use this to know the data source and name of the file
    SOURCE = "CUSTOMCSV_REFSIG"
    FILENAME = os.path.basename(filepath)

    # Get REF_SIGNAL
    REF_SIGNAL = csv.filter(regex=ref_signal, axis=1).dropna()
    if not REF_SIGNAL.empty:
        REF_SIGNAL.columns = [i for i in range(len(REF_SIGNAL.columns))]
        if len(REF_SIGNAL.columns) > 1:
            warnings.warn(
                "\nMore than 1 reference signal detected. You should place other signals in 'EXTRAS'\n"
            )
    else:
        REF_SIGNAL = pd.DataFrame(columns=[0])
        warnings.warn(
            "\nref_signal not found, it might be necessary for some analyses\n"
        )  # returns empty pd.DataFrame with 1 column

    # Get EXTRAS
    EXTRAS = csv.filter(regex=extras, axis=1)
    if EXTRAS.empty:
        EXTRAS = pd.DataFrame(columns=[0])
        # returns empty pd.DataFrame with 1 column

    emgfile = {
        "SOURCE": SOURCE,
        "FILENAME": FILENAME,
        "FSAMP": float(fsamp),
        "REF_SIGNAL": REF_SIGNAL,
        "EXTRAS": EXTRAS,
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

    if emgfile["SOURCE"] in ["DEMUSE", "OTB", "CUSTOMCSV"]:
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
            "ACCURACY": ACCURACY
            "IPTS": IPTS,
            "MUPULSES": MUPULSES,
            "FSAMP": FSAMP,
            "IED": IED,
            "EMG_LENGTH": EMG_LENGTH,
            "NUMBER_OF_MUS": NUMBER_OF_MUS,
            "BINARY_MUS_FIRING": BINARY_MUS_FIRING,
            "EXTRAS": EXTRAS,
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

        # df
        # Extract the df from the dict, convert the df to a json, put the
        # json in a dict, convert the dict to a json.
        # We use dict converted to json to locate better the objects while
        # re-importing them in python.
        raw_signal = emgfile["RAW_SIGNAL"]
        ref_signal = emgfile["REF_SIGNAL"]
        accuracy = emgfile["ACCURACY"]
        ipts = emgfile["IPTS"]
        binary_mus_firing = emgfile["BINARY_MUS_FIRING"]
        extras = emgfile["EXTRAS"]

        raw_signal = raw_signal.to_json()
        ref_signal = ref_signal.to_json()
        accuracy = accuracy.to_json()
        ipts = ipts.to_json()
        binary_mus_firing = binary_mus_firing.to_json()
        extras = extras.to_json()

        raw_signal = {"RAW_SIGNAL": raw_signal}
        ref_signal = {"REF_SIGNAL": ref_signal}
        accuracy = {"ACCURACY": accuracy}
        ipts = {"IPTS": ipts}
        binary_mus_firing = {"BINARY_MUS_FIRING": binary_mus_firing}
        extras = {"EXTRAS": extras}

        raw_signal = json.dumps(raw_signal)
        ref_signal = json.dumps(ref_signal)
        accuracy = json.dumps(accuracy)
        ipts = json.dumps(ipts)
        binary_mus_firing = json.dumps(binary_mus_firing)
        extras = json.dumps(extras)

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
            accuracy,
            ipts,
            mupulses,
            fsamp,
            ied,
            emg_length,
            number_of_mus,
            binary_mus_firing,
            extras,
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

    elif emgfile["SOURCE"] in ["OTB_REFSIG", "CUSTOMCSV_REFSIG"]:
        """
        refsig =   {
                "SOURCE" : SOURCE,
                "FILENAME": FILENAME,
                "FSAMP" : FSAMP,
                "REF_SIGNAL" : REF_SIGNAL,
                "EXTRAS": EXTRAS,
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
        extras = emgfile["EXTRAS"]
        extras = extras.to_json()
        extras = {"EXTRAS": extras}
        extras = json.dumps(extras)
        # Merge all the objects in one
        list_to_save = [source, filename, fsamp, ref_signal, extras]
        json_to_save = json.dumps(list_to_save)
        # Compress and save
        with gzip.open(filepath, "w") as f:
            json_bytes = json_to_save.encode("utf-8")
            f.write(json_bytes)

    else:
        raise ValueError("\nFile source not recognised\n")


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
    (or ``emg_refsig`` if SOURCE in ["OTB_REFSIG", "CUSTOMCSV_REFSIG"]).

    Examples
    --------
    For an extended explanation of the imported emgfile use:

    >>> import openhdemg.library as emg
    >>> emgfile = emg.emg_from_json(filepath="path/filename.json")
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
    13
    """
    # Access the dictionaries and extract the data
    # jsonemgfile[0] contains the SOURCE in a dictionary
    source_dict = json.loads(jsonemgfile[0])
    source = source_dict["SOURCE"]
    # jsonemgfile[1] contains the FILENAME in all the sources
    filename_dict = json.loads(jsonemgfile[1])
    filename = filename_dict["FILENAME"]

    if source in ["DEMUSE", "OTB", "CUSTOMCSV"]:
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
        # jsonemgfile[4] contains the ACCURACY to be treated as jsonemgfile[2]
        accuracy_dict = json.loads(jsonemgfile[4])
        accuracy_dict = json.loads(accuracy_dict["ACCURACY"])
        accuracy = pd.DataFrame(accuracy_dict)
        accuracy.columns = accuracy.columns.astype(int)
        accuracy.index = accuracy.index.astype(int)
        accuracy.sort_index(inplace=True)
        # jsonemgfile[5] contains the IPTS to be treated as jsonemgfile[2]
        ipts_dict = json.loads(jsonemgfile[5])
        ipts_dict = json.loads(ipts_dict["IPTS"])
        ipts = pd.DataFrame(ipts_dict)
        ipts.columns = ipts.columns.astype(int)
        ipts.index = ipts.index.astype(int)
        ipts.sort_index(inplace=True)
        # jsonemgfile[6] contains the MUPULSES which is a list of lists but
        # has to be converted in a list of ndarrays.
        mupulses = json.loads(jsonemgfile[6])
        for num, element in enumerate(mupulses):
            mupulses[num] = np.array(element)
        # jsonemgfile[7] contains the FSAMP to be treated as jsonemgfile[0]
        fsamp_dict = json.loads(jsonemgfile[7])
        fsamp = float(fsamp_dict["FSAMP"])
        # jsonemgfile[8] contains the IED to be treated as jsonemgfile[0]
        ied_dict = json.loads(jsonemgfile[8])
        ied = float(ied_dict["IED"])
        # jsonemgfile[9] contains the EMG_LENGTH to be treated as
        # jsonemgfile[0]
        emg_length_dict = json.loads(jsonemgfile[9])
        emg_length = int(emg_length_dict["EMG_LENGTH"])
        # jsonemgfile[10] contains the NUMBER_OF_MUS to be treated as
        # jsonemgfile[0]
        number_of_mus_dict = json.loads(jsonemgfile[10])
        number_of_mus = int(number_of_mus_dict["NUMBER_OF_MUS"])
        # jsonemgfile[11] contains the BINARY_MUS_FIRING to be treated as
        # jsonemgfile[2]
        binary_mus_firing_dict = json.loads(jsonemgfile[11])
        binary_mus_firing_dict = json.loads(
            binary_mus_firing_dict["BINARY_MUS_FIRING"]
        )
        binary_mus_firing = pd.DataFrame(binary_mus_firing_dict)
        binary_mus_firing.columns = binary_mus_firing.columns.astype(int)
        binary_mus_firing.index = binary_mus_firing.index.astype(int)
        # jsonemgfile[12] contains the EXTRAS to be treated as
        # jsonemgfile[2]
        extras_dict = json.loads(jsonemgfile[12])
        extras_dict = json.loads(extras_dict["EXTRAS"])
        extras = pd.DataFrame(extras_dict)
        # extras.columns = extras.columns.astype(int)
        # extras.index = extras.index.astype(int)
        # extras.sort_index(inplace=True)
        # Don't alter extras, leave that to the user for maximum control

        emgfile = {
            "SOURCE": source,
            "FILENAME": filename,
            "RAW_SIGNAL": raw_signal,
            "REF_SIGNAL": ref_signal,
            "ACCURACY": accuracy,
            "IPTS": ipts,
            "MUPULSES": mupulses,
            "FSAMP": fsamp,
            "IED": ied,
            "EMG_LENGTH": emg_length,
            "NUMBER_OF_MUS": number_of_mus,
            "BINARY_MUS_FIRING": binary_mus_firing,
            "EXTRAS": extras,
        }

    elif source in ["OTB_REFSIG", "CUSTOMCSV_REFSIG"]:
        # jsonemgfile[2] contains the fsamp
        fsamp_dict = json.loads(jsonemgfile[2])
        fsamp = float(fsamp_dict["FSAMP"])
        # jsonemgfile[3] contains the REF_SIGNAL
        ref_signal_dict = json.loads(jsonemgfile[3])
        ref_signal_dict = json.loads(ref_signal_dict["REF_SIGNAL"])
        ref_signal = pd.DataFrame(ref_signal_dict)
        ref_signal.columns = ref_signal.columns.astype(int)
        ref_signal.index = ref_signal.index.astype(int)
        ref_signal.sort_index(inplace=True)
        # jsonemgfile[4] contains the EXTRAS
        extras_dict = json.loads(jsonemgfile[4])
        extras_dict = json.loads(extras_dict["EXTRAS"])
        extras = pd.DataFrame(extras_dict)

        emgfile = {
            "SOURCE": source,
            "FILENAME": filename,
            "FSAMP": fsamp,
            "REF_SIGNAL": ref_signal,
            "EXTRAS": extras,
        }

    else:
        raise Exception("\nFile source not recognised\n")

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
    filesource : str {"OPENHDEMG", "DEMUSE", "OTB", "OTB_REFSIG", "CUSTOMCSV", CUSTOMCSV_REFSIG}, default "OPENHDEMG"
        See notes for how files should be exported from OTB.

        ``OPENHDEMG``
            File saved from openhdemg (.json).
        ``DEMUSE``
            File saved from DEMUSE (.mat).
        ``OTB``
            File exported from OTB with decomposition and reference signal
            (.mat).
        ``OTB_REFSIG``
            File exported from OTB with only the reference signal (.mat).
        ``CUSTOMCSV``
            Custom file format (.csv).
        ``CUSTOMCSV_REFSIG``
            Custom file format (.csv) containing only the reference signal.
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
    custom_accuracy : str, default 'ACCURACY'
        Label of the column(s) containing the accuracy score of the
        decomposed MUs in the custom file.
        Ignore if loading other files.
    custom_extras : str, default 'EXTRAS'
        Label of the column(s) containing custom values in the custom file.
        This information will be stored in a pd.DataFrame with columns named
        as in the .csv file.
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
    if SOURCE in ["OTB_REFSIG", CUSTOMCSV_REFSIG]).

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
    - NO OTHER ELEMENTS SHOULD BE PRESENT! unless an appropriate regex pattern
    is passed to 'extras='!

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
    The .csv file must contain all the variables. The only admitted exceptions
    are 'ref_signal' and 'ipts'.

    Structure of the returned emgfile:
        emgfile = {
            "SOURCE": SOURCE,
            "FILENAME": FILENAME,
            "RAW_SIGNAL": RAW_SIGNAL,
            "REF_SIGNAL": REF_SIGNAL,
            "ACCURACY": accuracy score (depending on source file type),
            "IPTS": IPTS,
            "MUPULSES": MUPULSES,
            "FSAMP": FSAMP,
            "IED": IED,
            "EMG_LENGTH": EMG_LENGTH,
            "NUMBER_OF_MUS": NUMBER_OF_MUS,
            "BINARY_MUS_FIRING": BINARY_MUS_FIRING,
            "EXTRAS": EXTRAS,
        }

    Structure of the returned emg_refsig:
        emg_refsig = {
            "SOURCE": SOURCE,
            "FILENAME": FILENAME,
            "FSAMP": FSAMP,
            "REF_SIGNAL": REF_SIGNAL,
            "EXTRAS": EXTRAS,
        }

    Examples
    --------
    For an extended explanation of the imported emgfile use:

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="OPENHDEMG")
    >>> info = emg.info()
    >>> info.data(emgfile)
    """

    # Set initialdir (actually not working on Windows, but it's not a problem
    # of the code implementation)
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
            filetypes=[("MATLAB files", "*.mat")],
        )
    elif filesource == "OPENHDEMG":
        file_toOpen = filedialog.askopenfilename(
            initialdir=initialdir,
            title="Select an OPENHDEMG file to load",
            filetypes=[("JSON files", "*.json")],
        )
    elif filesource in ["CUSTOMCSV", "CUSTOMCSV_REFSIG"]:
        file_toOpen = filedialog.askopenfilename(
            initialdir=initialdir,
            title="Select a custom file to load",
            filetypes=[("CSV files", "*.csv")],
        )
    else:
        raise Exception(
            "\nfilesource not valid, it must be one of 'DEMUSE', 'OTB', 'OTB_REFSIG', 'OPENHDEMG', 'CUSTOMCSV', 'CUSTOMCSV_REFSIG'\n"
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
    elif filesource == "CUSTOMCSV":
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
            accuracy=kwargs.get("custom_accuracy", "ACCURACY"),
            extras=kwargs.get("custom_extras", "EXTRAS"),
            fsamp=kwargs.get("custom_fsamp", 2048),
            ied=kwargs.get("custom_ied", 8),
        )
    else:  # CUSTOMCSV_REFSIG
        emgfile = refsig_from_customcsv(
            filepath=file_toOpen,
            ref_signal=kwargs.get("custom_ref_signal", "REF_SIGNAL"),
            extras=kwargs.get("custom_extras", "EXTRAS"),
            fsamp=kwargs.get("custom_fsamp", 2048),
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
        filetypes=[("JSON files", "*.json")],
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
