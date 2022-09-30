"""
DESCRIPTION:

    This module contains all the functions that are necessary to open or save MATLAB (.mat) and JSON (.json) files. 
    MATLAB files are used to store data from the DEMUSE and the OTBiolab+ software while JSON files are used to 
    save and load files from this library.
    The choice of saving files in the open standard JSON file format was preferred over the MATLAB file format since 
    it has a better integration with Python and has a very high cross-platform compatibility.

    Most of the functions contained in this file are called internally and should not be exposed to the final user.

    Functions should be exposed as:
        from openhdemg.openfiles import emg_from_otb, emg_from_demuse, refsig_from_otb, askopenfile, save_json_emgfile, emg_from_json

FUNCTIONS' SCOPE:

    emg_from_otb and emg_from_demuse:
        are used to load .mat files coming from the DEMUSE or the OTBiolab+ software. Demuse has a fixed file structure while
        the OTB file, in order to be compatible with this library should be exported with a strict structure as described in the
        function emg_from_otb. In both cases, the input file is a .mat file.
    refsig_from_otb:
        is used to load files from the OTBiolab+ software that contain only the reference signal.
    
    askopenfile:
        is a quick GUI implementation that allows users to select the file to open.

    save_json_emgfile, emg_from_json:
        are used to save the working file to a .json file or to load the .json file.

#TODO
Structure of emgfile and refsig file

Additional informations can be found in the official documentation and in the function's description.
"""

from scipy.io import loadmat
import pandas as pd
import numpy as np
from openhdemg.otbelectrodes import *
from tkinter import *
from tkinter import filedialog
from pathlib import Path
import json, gzip

# ---------------------------------------------------------------------
# Define functions used in the DEMUSE openfile function.
# These functions are not exposed to the final user.

def oned_mat_to_pd(variable_name, mat_file, transpose_=False):
    """
    This function is used to convert Matlab arrays (1 dimensional structures) into a df.

    Parameters
    ----------
    variable_name: str
        Name of the variable to extract from the .mat file.
    
    mat_file: dict
        The .mat file loaded with loadmat.

    transpose_: bool, default False
        Whether to transpose the pd.DataFrame containing the extracted variable.
    
    Returns
    -------
    mat: pd.DataFrame or np.nan
        A pd.DataFrame containing the requested variable
        or np.nan if the variable was not found.
    """

    if variable_name in mat_file.keys():

        # Catch the case for the PNR of a single MU which is a float value that cannot be directly added to a dataframe
        if isinstance(mat_file[variable_name], float):
            res = {0: mat_file[variable_name]}
            if transpose_ == True:
                mat = pd.DataFrame(res, index=[0]).transpose()
            else:
                mat = pd.DataFrame(res, index=[0])

        else:
            if transpose_ == True:
                mat = pd.DataFrame(mat_file[variable_name]).transpose()
            else:
                mat = pd.DataFrame(mat_file[variable_name])

        return mat

    else:
        print(
            "\nVariable {} was not found in the mat file, check the spelling against the dict_keys\n".format(
                variable_name
            )
        )

        return np.nan


def twod_mat_to_pd(variable_name, mat_file, transpose_=True):
    """
    This function is used to convert Matlab matrixes (2 dimensional structures) into a df.

    Parameters
    ----------
    variable_name: str
        Name of the variable to extract from the .mat file.
    
    mat_file: dict
        The .mat file loaded with loadmat.

    transpose_: bool, default True
        Whether to transpose the pd.DataFrame containing the extracted variable.
    
    Returns
    -------
    mat: pd.DataFrame or np.nan
        A pd.DataFrame containing the requested variable
        or np.nan if the variable was not found.
    """

    if variable_name in mat_file.keys():
        # Catch the exception of a single MU that would create an alrerady transposed dataframe
        if len(mat_file["IPTs"].shape) == 1:
            transpose_ = False

        if transpose_ == True:
            mat = pd.DataFrame(mat_file[variable_name]).transpose()
        else:
            mat = pd.DataFrame(mat_file[variable_name])

        return mat

    else:
        print(
            "\nVariable {} was not found in the mat file, check the spelling against the dict_keys\n".format(
                variable_name
            )
        )

        return np.nan


def threed_mat_to_list(variable_name, mat_file, transpose_=False):
    """
    This function is used to convert Matlab Cell arrays (3 dimensional structures)
    into a Python list of numpy.ndarrays.

    Parameters
    ----------
    variable_name: str
        Name of the variable to extract from the .mat file.
    
    mat_file: dict
        The .mat file loaded with loadmat.

    transpose_: bool, default True
        Whether to transpose the pd.DataFrame containing the extracted variable.
    
    Returns
    -------
    mat: list
        A list of numpy.ndarrays containing the requested variable
        or np.nan if the variable was not found.
    """
    
    if variable_name in mat_file.keys():
        if transpose_ == True:
            mat = list(map(list, zip(*mat_file[variable_name])))
        else:
            mat = list(mat_file[variable_name])
        
        return mat

    else:
        print(
            "\nVariable {} was not found in the mat file, check the spelling against the dict_keys\n".format(
                variable_name
            )
        )

        return np.nan


def create_binary_firings(EMG_LENGTH, NUMBER_OF_MUS, MUPULSES):
    """
    This function creates a binary representation of the MU firing over time.

    Parameters
    ----------
    EMG_LENGTH: int
        Number of samples (length) in the emg file.
    
    NUMBER_OF_MUS: int
        Number of MUs in the emg file.

    MUPULSES: list
        The times of firing of each MU.
    
    Returns
    -------
    mat: pd.DataFrame
        A pd.DataFrame containing the requested variable
        or np.nan if the variable was not found.
    """

    if isinstance(MUPULSES, list):  # skip the step if I don't have the MUPULSES (is nan)
        # create an empty df containing zeros
        binary_MUs_firing = pd.DataFrame(np.zeros((EMG_LENGTH, NUMBER_OF_MUS)))
        # Loop through the columns (MUs) and isolate the data of interest
        for i in range(NUMBER_OF_MUS):
            this_mu_binary_firing = binary_MUs_firing[i]

            # Catch the exception of a single MU
            if NUMBER_OF_MUS != 1:
                this_mu_pulses = pd.DataFrame(MUPULSES[i])
                # Loop through the rows (time) and assign 1 if the MU is firing
                for position in range(len(this_mu_pulses)):
                    firing_point = int(this_mu_pulses.iloc[position])
                    this_mu_binary_firing.iloc[firing_point] = 1
            else:
                this_mu_pulses = MUPULSES
                for position in range(len(this_mu_pulses)):
                    firing_point = int(this_mu_pulses[position])
                    this_mu_binary_firing.iloc[firing_point] = 1

            # Merge the work done with the original df of zeros
            binary_MUs_firing[i] = this_mu_binary_firing

        return binary_MUs_firing

    else:
        return np.nan


def raw_sig_from_demuse(variable_name, mat_file, transpose_=False):
    """
    This function creates a binary representation of the MU firing over time.

    Parameters
    ----------
    variable_name: str
        The name of the variable containing the reference signal (usually "SIG").
    
    mat_file: dict
        The file loaded with loadmat containing the reference signal.

    transpose_: bool, default False
        Whether to transpose the pd.DataFrame containing the extracted variable.
    
    Returns
    -------
    mat: pd.DataFrame
        A pd.DataFrame containing the requested variable
        or np.nan if the variable was not found.
    """

    if variable_name in mat_file.keys():
        if transpose_ == True:
            mat = mat_file[variable_name].ravel(
                order="F"
            )  # ‘F’ means to index the elements in column-major
            mat = pd.DataFrame(list(map(np.ravel, mat))).transpose()
        else:
            mat = mat_file[variable_name].ravel(order="F")
            mat = pd.DataFrame(list(map(np.ravel, mat)))

        return mat

    else:
        print(
            "\nVariable {} was not found in the mat file, check the spelling against the dict_keys\n".format(
                variable_name
            )
        )

        return np.nan


# ---------------------------------------------------------------------
# Main function to open decomposed files coming from DEMUSE.
# This function calls the functions defined above

def emg_from_demuse(file):
    """
    This function is used to import the .mat file used in DEMUSE.
    
    Parameters
    ----------
    file: str or Path
        The directory and the name of the file to load (including file extension .mat).
    
    Returns
    -------
    emgfile: dict
        A dictionary containing all the useful variables.
    
    Important
    ---------
    The returned file is called ``emgfile`` for convention.

    Notes
    -----
    The demuse file contains 65 raw EMG channels (1 empty) instead of 64 (as for OTB matrix standards).

    Structure of the emgfile:
        emgfile = {
            "SOURCE": SOURCE,
            "RAW_SIGNAL": RAW_SIGNAL,
            "REF_SIGNAL": REF_SIGNAL,
            "PNR": PNR,
            "IPTS": IPTS,
            "MUPULSES": MUPULSES,
            "FSAMP": FSAMP,
            "IED": IED,
            "EMG_LENGTH": EMG_LENGTH,
            "NUMBER_OF_MUS": NUMBER_OF_MUS,
            "BINARY_MUS_FIRING": BINARY_MUS_FIRING,
        }
    """

    mat_file = loadmat(file, simplify_cells=True)

    # Parse .mat obtained from DEMUSE to see the available variables
    # First: see the variables name
    print(
        "\n--------------------------------\nAvailable dict keys are:\n\n{}\n".format(
            mat_file.keys()
        )
    )

    # Second: collect the necessary variables in pandas dataframe (df) or list (for matlab cell arrays)   -variable_name must be a string (i.e., "name")
    REF_SIGNAL = oned_mat_to_pd(
        variable_name="ref_signal", mat_file=mat_file, transpose_=False
    )
    PNR = oned_mat_to_pd(variable_name="PNR", mat_file=mat_file, transpose_=False)
    IPTS = twod_mat_to_pd(variable_name="IPTs", mat_file=mat_file, transpose_=True)
    MUPULSES = threed_mat_to_list(
        variable_name="MUPulses", mat_file=mat_file, transpose_=False
    )

    # Third: collect the necessary values in variables
    FSAMP = int(mat_file["fsamp"])  # Sampling frequency
    IED = int(mat_file["IED"])  # Interelectrode distance
    EMG_LENGTH, NUMBER_OF_MUS = IPTS.shape  # File length and number of MUs

    # Create a df with the binary representation of firing times, if necessary for other appliactions. Not used here
    BINARY_MUS_FIRING = create_binary_firings(EMG_LENGTH, NUMBER_OF_MUS, MUPULSES)

    # Fourth: obtain the raw EMG signal
    RAW_SIGNAL = raw_sig_from_demuse(
        variable_name="SIG", mat_file=mat_file, transpose_=True
    )

    # Use this to know what data you have or don't have
    SOURCE = "DEMUSE"

    # Manage exception of single MU
    if NUMBER_OF_MUS == 1:
        MUPULSES = [np.array(MUPULSES)]

    emgfile = {
        "SOURCE": SOURCE,
        "RAW_SIGNAL": RAW_SIGNAL,
        "REF_SIGNAL": REF_SIGNAL,
        "PNR": PNR,
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

# The user can decide if he/she wants the filtered or unfiltered reference signal
def get_otb_refsignal(df, refsig):
    """
    This function extracts the reference signal from the OTB .mat file.

    Parameters
    ----------
    df: pd.DataFrame
        A pd.DataFrame containing all the informations extracted
        from the OTB .mat file.
    
    refsig: list
        Whether to seacrh also for the reference signal and
        whether to load the filtered on unfiltered one.
        The list is composed as [bool, str]. See examples below.
        
    Returns
    -------
    REF_SIGNAL: pd.DataFrame or np.nan
        A pd.DataFrame containing the requested variable
        or np.nan if the variable was not found.
    
    Examples
    --------
    REF_SIGNAL = get_otb_refsignal(df=DF, refsig=[True, "filtered"])
    REF_SIGNAL = get_otb_refsignal(df=DF, refsig=[True, "unfiltered"])
    REF_SIGNAL = get_otb_refsignal(df=DF, refsig=[False])
    """

    assert refsig[0] in [
        True,
        False,
    ], f"refsig[0] must be true or false. {refsig[0]} was passed instead."
    assert refsig[1] in [
        "filtered",
        "unfiltered",
    ], f"refsig[1] must be filtered or unfiltered. {refsig[1]} was passed instead."

    if refsig[0] == True:
        if refsig[1] == "filtered":
            # Extract the performed path (filtered data)
            REF_SIGNAL_FILTERED = df.filter(regex="performed path")
            if not REF_SIGNAL_FILTERED.empty:  # Check if the ref signal is available
                REF_SIGNAL_FILTERED = REF_SIGNAL_FILTERED.rename(
                    columns={REF_SIGNAL_FILTERED.columns[0]: 0}
                )
                # Verify that there is no value above 100% since the REF_SIGNAL is expected to be expressed as % of the MViF
                if max(REF_SIGNAL_FILTERED[0]) > 100:
                    print(
                        "\nALERT! Ref signal grater than 100, did you use values normalised to the MViF?\n"
                    )

                return REF_SIGNAL_FILTERED

            else:
                print(
                    "\nReference signal not found, it might be necessary for some analysis\n"
                )

                return np.nan

        elif refsig[1] == "unfiltered":
            # Extract the acquired path (raw data)
            REF_SIGNAL_UNFILTERED = df.filter(regex="acquired data")
            if not REF_SIGNAL_UNFILTERED.empty:
                REF_SIGNAL_UNFILTERED = REF_SIGNAL_UNFILTERED.rename(
                    columns={REF_SIGNAL_UNFILTERED.columns[0]: 0}
                )
                # Verify that there is no value above 100% since the REF_SIGNAL is expected to be expressed as % of the MViF
                if max(REF_SIGNAL_UNFILTERED[0]) > 100:
                    print(
                        "\nALERT! Ref signal grater than 100, did you use values normalised to the MViF?\n"
                    )

                return REF_SIGNAL_UNFILTERED

            else:
                print(
                    "\nReference signal not found, it might be necessary for some analysis\n"
                )

                return np.nan

        else:
            raise Exception(
                'Wrong input in the get_OTB_refsignal function, you can use ref="filtered" or ref="unfiltered"'
            )

    else:
        print("\nReference signal not found, it might be necessary for some analysis\n")

        return np.nan


def get_otb_decomposition(df):
    """
    This function extracts the IPTS and BINARY_MUS_FIRING from the OTB .mat file.

    Parameters
    ----------
    df: pd.DataFrame
        A pd.DataFrame containing all the informations extracted
        from the OTB .mat file.
        
    Returns
    -------
    IPTS, BINARY_MUS_FIRING: pd.DataFrame or np.nan
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


def get_otb_mupulses(binarymusfiring, numberofMUs):
    """
    This function extracts the MUPULSES from the OTB .mat file.

    Parameters
    ----------
    binarymusfiring: pd.DataFrame
        A pd.DataFrame containing the binary representation of MUs firings.
    
    numberofMUs: int
        The total number of available MUs.
        
    Returns
    -------
    MUPULSES: list
        A list of ndarrays containing the firing time of each MU.
    """

    # Create empty list of lists to fill with ndarrays containing the mupulses (point of firing)
    MUPULSES = [[] for _ in range(numberofMUs)]

    for i in binarymusfiring:  # Loop all the MUs
        my_ndarray = []
        for idx, x in binarymusfiring[i].iteritems():  # Loop the MU firing times
            if x > 0:
                my_ndarray.append(idx)  # Take the firing time and add it to the ndarray

        my_ndarray = np.array(my_ndarray)
        MUPULSES[i] = my_ndarray

    return MUPULSES

#TODO
# Check also all the names in capitals and describe them somewhere
def get_otb_ied(df):
    for matrix in OTBelectrodes_ied.keys():
        # Check the matrix used in the columns name (in the df obtained from OTBiolab+)
        if matrix in str(df.columns):
            IED = int(OTBelectrodes_ied[matrix])

            return IED  # we don't need break since return ends the function


def get_otb_rawsignal(df):
    # Drop all the known columns different from the raw EMG signal.
    # This is a workaround since the OTBiolab+ software does not export a unique name for the raw EMG signal
    pattern = "Source for decomposition|Decomposition of|acquired data|performed path"
    emg_df = df[df.columns.drop(list(df.filter(regex=pattern)))]

    # Check if the number of remaining columns matches the expected number of matrix channels
    for matrix in OTBelectrodes_Nelectrodes.keys():
        # Check the matrix used in the columns name (in the emg_df) to know the number of expected channels
        if matrix in str(emg_df.columns):
            expectedchannels = int(OTBelectrodes_Nelectrodes[matrix])
            break

    if len(emg_df.columns) == expectedchannels:
        emg_df.columns = np.arange(len(emg_df.columns))
        RAW_SIGNAL = emg_df

        return RAW_SIGNAL

    else:
        # This check here is usefull to control that only the appropriate elements have been included in the .mat file exported from OTBiolab+
        raise Exception(
            "Failure in searching the raw signal, please check that it is present in the .mat file and that only the accepted parameters have been included"
        )


# -----------------------------------------------------------------------------------------------


def emg_from_otb(file, refsig=[True, "filtered"]):
    """
    This function is used to import the .mat file exportable by the OTBiolab+ software as a dictionary of Python objects (mainly pandas dataframes).

    The first argument is the file path (including file extension .mat). The use of Path is not required.

    refsig can be used to specify if REF_SIGNAL is present and if you want to import the filtered or the unfiltered signal.
    In OTBioLab+ the "performed path" refers to the filtered signal, the "acquired data" to the unfiltered signal.
    A list should be passed to refsig. The first element can be True or False, if False, the REF_SIGNAL is not imported (returns nan).
    The second element can be one of "filtered" or "unfiltered" depending on what you want to import.

    It returns a dictionary containing the following: "SOURCE", "RAW_SIGNAL", "REF_SIGNAL", "PNR",
    "IPTS", "MUPULSES", "FSAMP", "IED", "EMG_LENGTH", "NUMBER_OF_MUS", "BINARY_MUS_FIRING".

    The returned file is called emgfile for convention.

    The input .mat file exported from the OTBiolab+ software should have a specific content:
    - Reference signal is optional but, if present, there should be both the filtered and the unfiltered version
        (in OTBioLab+ the "performed path" refers to the filtered signal, the "acquired data" to the unfiltered signal),
        REF_SIGNAL is expected to be expressed as % of the MViF.
    - Both the IPTS ('Source for decomposition...' in OTBioLab+) and the BINARY_MUS_FIRING ('Decomposition of...' in OTBioLab+) should be present.
    - The raw EMG signal should be present (it has no specific name in OTBioLab+) with all the channels.
        Don't exclude unwanted channels before exporting the .mat file.
    - NO OTHER ELEMENTS SHOULD BE PRESENT!
    """
    mat_file = loadmat(file, simplify_cells=True)

    # Parse .mat obtained from DEMUSE to see the available variables
    # First: see the variables name
    print(
        "\n--------------------------------\nAvailable dict keys are:\n\n{}\n".format(
            mat_file.keys()
        )
    )

    # Second: Simplify (rename) columns description and extract all the parameters in a pandas dataframe
    df = pd.DataFrame(mat_file["Data"], columns=mat_file["Description"])
    # print(df.head())

    REF_SIGNAL = get_otb_refsignal(df=df, refsig=refsig)
    PNR = pd.DataFrame({0: np.nan}, index=[0])
    IPTS, BINARY_MUS_FIRING = get_otb_decomposition(df=df)
    EMG_LENGTH, NUMBER_OF_MUS = IPTS.shape
    MUPULSES = get_otb_mupulses(
        binarymusfiring=BINARY_MUS_FIRING, numberofMUs=NUMBER_OF_MUS
    )
    FSAMP = int(mat_file["SamplingFrequency"])
    IED = get_otb_ied(df=df)
    RAW_SIGNAL = get_otb_rawsignal(df)

    # Use this to know what data you have or don't have
    SOURCE = "OTB"

    resdict = {
        "SOURCE": SOURCE,
        "RAW_SIGNAL": RAW_SIGNAL,
        "REF_SIGNAL": REF_SIGNAL,
        "PNR": PNR,
        "IPTS": IPTS,
        "MUPULSES": MUPULSES,
        "FSAMP": FSAMP,
        "IED": IED,
        "EMG_LENGTH": EMG_LENGTH,
        "NUMBER_OF_MUS": NUMBER_OF_MUS,
        "BINARY_MUS_FIRING": BINARY_MUS_FIRING,
    }

    return resdict


# -----------------------------------------------------------------------------------------------


def refsig_from_otb(file, refsig="filtered"):
    """
    This function is used to import the .mat file exportable by the OTBiolab+ software as a dictionary of Python objects (mainly pandas dataframes).

    The first argument is the file path (including file extension .mat).

    Compared to the function emg_from_otb, this function only imports the reference signal and, therefore, it can be used for special cases
    where only the ref signal is necessary. This will allow a faster execution of the script and to avoid exceptions for missing data.

    The argument refsig can be used to specify if the REF_SIGNAL to import is the filtered or the unfiltered signal (filtered at source).
    In OTBioLab+ the "performed path" refers to the filtered signal, the "acquired data" to the unfiltered signal.
    "filtered" or "unfiltered" can be passed.

    It returns a dictionary containing: "SOURCE", "FSAMP", "REF_SIGNAL". This will allow compatibility with the emgfile.

    The returned file is called refsig for convention.
    """
    mat_file = loadmat(file, simplify_cells=True)

    # Parse .mat obtained from DEMUSE to see the available variables
    # First: see the variables name
    print(
        "\n--------------------------------\nAvailable dict keys are:\n\n{}\n".format(
            mat_file.keys()
        )
    )

    # Second: Simplify (rename) columns description and extract all the parameters in a pandas dataframe
    df = pd.DataFrame(mat_file["Data"], columns=mat_file["Description"])
    # print(df.head())

    # Convert the input passed to refsig in a list compatible with the function get_otb_refsignal
    refsig_ = [True, refsig]
    REF_SIGNAL = get_otb_refsignal(df=df, refsig=refsig_)

    # Use this to know what data you have or don't have
    SOURCE = "OTB_refsig"
    FSAMP = int(mat_file["SamplingFrequency"])

    resdict = {
        "SOURCE": SOURCE,
        "FSAMP": FSAMP,
        "REF_SIGNAL": REF_SIGNAL,
    }

    return resdict


# -----------------------------------------------------------------------------------------------


def askopenfile(
    initialdir="/", filesource="DEMUSE", otb_refsig_type=[True, "filtered"]
):
    """
    This function is a shortcut to select and open files with a GUI in a single line of code.

    Input:
    initialdir = Path("/Decomposed Test files/") by default, any other path can be specified,
        both as string or as Path.

    filesource = "DEMUSE" by default, one of "OTB", "OTB_refsig", "Open_HD-EMG" (json file) can be specified.

    otb_refsig_type = [True, "filtered"] by default, refsig can be used to specify if REF_SIGNAL is present
        and if you want to import the filtered or the unfiltered signal. In OTBioLab+ the "performed path" refers
        to the filtered signal, the "acquired data" to the unfiltered signal. A list should be passed to refsig.
        The first element can be True or False, if False, the REF_SIGNAL is not imported (returns nan).
        The second element can be one of "filtered" or "unfiltered" depending on what you want to import.
        This input is necessery only if loading files from OTBiolab+.

    Return:
    The returned file is called emgfile for convention (or refsig if filesource = "OTB_refsig").

    """
    # If initialdir == str, check if a string path is passed. If not, use a path to sample files.
    # elif initialdir == Path, use that path
    if isinstance(initialdir, str):
        if initialdir == "/":
            initialdir = Path("/Decomposed Test files/")
        else:
            initialdir = Path(initialdir)
    elif isinstance(initialdir, Path):
        pass
    else:
        raise Exception("initialdir must be a string or a Path")

    # Create and hide the tkinter root window necessary for the GUI based open-file function
    root = Tk()
    root.withdraw()

    if filesource in ["DEMUSE", "OTB", "OTB_refsig"]:
        file_toOpen = filedialog.askopenfilename(
            initialdir=initialdir,
            title="Select a file",
            filetypes=[("MATLAB files", ".mat")],  # Change once the .pyemg is available
        )
    elif filesource == "Open_HD-EMG":
        file_toOpen = filedialog.askopenfilename(
            initialdir=initialdir,
            title="Select a file",
            filetypes=[("JSON files", ".json")],  # Change once the .pyemg is available
        )
    else:
        raise Exception(
            "filesource not valid, it must be one of DEMUSE, OTB, OTB_refsig or Open_HD-EMG (as string)"
        )

    # Destroy the root since it is no longer necessary
    root.destroy()

    # Open file depending on file origin
    if filesource == "DEMUSE":
        emgfile = emg_from_demuse(file=file_toOpen)
    elif filesource == "OTB":
        emgfile = emg_from_otb(file=file_toOpen, refsig=otb_refsig_type)
    elif filesource == "OTB_refsig":
        emgfile = refsig_from_otb(file=file_toOpen, refsig=otb_refsig_type[1])
    elif filesource == "Open_HD-EMG":
        emgfile = emg_from_json(path=file_toOpen)

    return emgfile


###########################################################################################################################################################
###########################################################################################################################################################
###########################################################################################################################################################
def save_json_emgfile(emgfile, path):  # To add save OTBrefsig
    """
    This function saves the file (with the changes made by the user, if any) as a json file.

    The first argument is the emgfile to save (a python dictionary).

    The second argument is the file path (including file extension .json). This can be a simple string; The use of Path is not necessary.
    """
    if emgfile["SOURCE"] in ["DEMUSE", "OTB"]:
        """
        We need to convert all the components of emgfile to a dictionary and then to json object.
        df cannot be converted with json.dumps.
        Once all the elements are converted to json objects, we create a list of json objects and dump/save it into a single json file.
        emgfile =   {
                    "SOURCE" : SOURCE,
                    "RAW_SIGNAL" : RAW_SIGNAL,
                    "REF_SIGNAL" : REF_SIGNAL,
                    ==> "PNR" : PNR,
                    ==> "IPTS" : IPTS,
                    ==> "MUPULSES" : MUPULSES,
                    "FSAMP" : FSAMP,
                    "IED" : IED,
                    "EMG_LENGTH" : EMG_LENGTH,
                    "NUMBER_OF_MUS" : NUMBER_OF_MUS,
                    ==> "BINARY_MUS_FIRING" : BINARY_MUS_FIRING,
                    }
        """
        # str or int
        # Directly convert the ditionary to a json format
        source = {"SOURCE": emgfile["SOURCE"]}
        fsamp = {"FSAMP": emgfile["FSAMP"]}
        ied = {"IED": emgfile["IED"]}
        emg_length = {"EMG_LENGTH": emgfile["EMG_LENGTH"]}
        number_of_mus = {"NUMBER_OF_MUS": emgfile["NUMBER_OF_MUS"]}
        source = json.dumps(source)
        fsamp = json.dumps(fsamp)
        ied = json.dumps(ied)
        emg_length = json.dumps(emg_length)
        number_of_mus = json.dumps(number_of_mus)

        # df
        # Extract the df from the dict, convert the dict to a json, put the json in a dict, convert the dict to a json
        # We use dict converted to json to locate better the objects while re-importing them in python
        raw_signal = emgfile["RAW_SIGNAL"]
        ref_signal = emgfile["REF_SIGNAL"]
        pnr = emgfile["PNR"]
        ipts = emgfile["IPTS"]
        binary_mus_firing = emgfile["BINARY_MUS_FIRING"]
        raw_signal = raw_signal.to_json()
        ref_signal = ref_signal.to_json()
        pnr = pnr.to_json()
        ipts = ipts.to_json()
        binary_mus_firing = binary_mus_firing.to_json()
        raw_signal = {"RAW_SIGNAL": raw_signal}
        ref_signal = {"REF_SIGNAL": ref_signal}
        pnr = {"PNR": pnr}
        ipts = {"IPTS": ipts}
        binary_mus_firing = {"BINARY_MUS_FIRING": binary_mus_firing}
        raw_signal = json.dumps(raw_signal)
        ref_signal = json.dumps(ref_signal)
        pnr = json.dumps(pnr)
        ipts = json.dumps(ipts)
        binary_mus_firing = json.dumps(binary_mus_firing)

        # list of ndarray
        # Every array has to be converted in a list; then, the list of lists can be converted to json
        mupulses = []
        for ind, array in enumerate(emgfile["MUPULSES"]):
            mupulses.insert(ind, array.tolist())
        mupulses = json.dumps(mupulses)

        # Convert a list of json objects to json. The result of the conversion will be saved as the final json file.
        ############ Don't alter this order unless you modify also the emg_from_json function ############
        list_to_save = [
            source,
            raw_signal,
            ref_signal,
            pnr,
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
        with gzip.open(path, "w") as f:
            # Encode json
            json_bytes = json_to_save.encode("utf-8")
            # Write to a file
            f.write(json_bytes)

    elif emgfile["SOURCE"] == "OTB_refsig":
        """
        refsig =   {
                "SOURCE" : SOURCE,
                "FSAMP" : FSAMP,
                "REF_SIGNAL" : REF_SIGNAL,
                }
        """
        # str or int
        source = {"SOURCE": emgfile["SOURCE"]}
        fsamp = {"FSAMP": emgfile["FSAMP"]}
        source = json.dumps(source)
        fsamp = json.dumps(fsamp)
        # df
        ref_signal = emgfile["REF_SIGNAL"]
        ref_signal = ref_signal.to_json()
        ref_signal = {"REF_SIGNAL": ref_signal}
        ref_signal = json.dumps(ref_signal)
        # Merge all the objects in one
        list_to_save = [source, fsamp, ref_signal]
        json_to_save = json.dumps(list_to_save)
        # Compress and save
        with gzip.open(path, "w") as f:
            json_bytes = json_to_save.encode("utf-8")
            f.write(json_bytes)

    else:
        raise Exception("File source not recognised")


def emg_from_json(path):
    """
    This function loads the emgfile stored in json format.

    The only argument is the path of the file to open (including file extension .json). This can be a simple string; The use of Path is not necessary.

    Return:
    The returned file is called emgfile for convention (or refsig if filesource = "OTB_refsig").
    """
    # Read and decompress json file
    with gzip.open(path, "r") as fin:
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
    # jsonemgfile[0] contains the source in a dictionary
    source_dict = json.loads(jsonemgfile[0])
    source = source_dict["SOURCE"]
    if source in ["DEMUSE", "OTB"]:
        # jsonemgfile[1] contains the raw signal in a dictionary, i can extract the raw signal in a new dictionary and convert it to a df
        # index and columns are imported as str, so we need to convert it to int
        raw_signal_dict = json.loads(jsonemgfile[1])
        raw_signal_dict = json.loads(raw_signal_dict["RAW_SIGNAL"])
        raw_signal = pd.DataFrame(raw_signal_dict)
        raw_signal.columns = raw_signal.columns.astype(int)
        raw_signal.index = raw_signal.index.astype(int)
        raw_signal.sort_index(inplace=True)
        # jsonemgfile[2] contains the reference signal to be treated as jsonemgfile[1]
        ref_signal_dict = json.loads(jsonemgfile[2])
        ref_signal_dict = json.loads(ref_signal_dict["REF_SIGNAL"])
        ref_signal = pd.DataFrame(ref_signal_dict)
        ref_signal.columns = ref_signal.columns.astype(int)
        ref_signal.index = ref_signal.index.astype(int)
        ref_signal.sort_index(inplace=True)
        # jsonemgfile[3] contains the pnr to be treated as jsonemgfile[1]
        pnr_dict = json.loads(jsonemgfile[3])
        pnr_dict = json.loads(pnr_dict["PNR"])
        pnr = pd.DataFrame(pnr_dict)
        pnr.columns = pnr.columns.astype(int)
        pnr.index = pnr.index.astype(int)
        pnr.sort_index(inplace=True)
        # jsonemgfile[4] contains the ipts to be treated as jsonemgfile[1]
        ipts_dict = json.loads(jsonemgfile[4])
        ipts_dict = json.loads(ipts_dict["IPTS"])
        ipts = pd.DataFrame(ipts_dict)
        ipts.columns = ipts.columns.astype(int)
        ipts.index = ipts.index.astype(int)
        ipts.sort_index(inplace=True)
        # jsonemgfile[5] contains the mupulses which is a list of lists but has to be converted in a list of ndarrays
        mupulses = json.loads(jsonemgfile[5])
        for num, element in enumerate(mupulses):
            mupulses[num] = np.array(element)
        # jsonemgfile[6] contains the fsamp to be treated as jsonemgfile[0]
        fsamp_dict = json.loads(jsonemgfile[6])
        fsamp = int(fsamp_dict["FSAMP"])
        # jsonemgfile[7] contains the ied to be treated as jsonemgfile[0]
        ied_dict = json.loads(jsonemgfile[7])
        ied = int(ied_dict["IED"])
        # jsonemgfile[8] contains the ied to be treated as jsonemgfile[0]
        emg_length_dict = json.loads(jsonemgfile[8])
        emg_length = int(emg_length_dict["EMG_LENGTH"])
        # jsonemgfile[9] contains the ied to be treated as jsonemgfile[0]
        number_of_mus_dict = json.loads(jsonemgfile[9])
        number_of_mus = int(number_of_mus_dict["NUMBER_OF_MUS"])
        # jsonemgfile[10] contains the binary_mus_firing to be treated as jsonemgfile[1]
        binary_mus_firing_dict = json.loads(jsonemgfile[10])
        binary_mus_firing_dict = json.loads(binary_mus_firing_dict["BINARY_MUS_FIRING"])
        binary_mus_firing = pd.DataFrame(binary_mus_firing_dict)
        binary_mus_firing.columns = binary_mus_firing.columns.astype(int)
        binary_mus_firing.index = binary_mus_firing.index.astype(int)

        resdict = {
            "SOURCE": source,
            "RAW_SIGNAL": raw_signal,
            "REF_SIGNAL": ref_signal,
            "PNR": pnr,
            "IPTS": ipts,
            "MUPULSES": mupulses,
            "FSAMP": fsamp,
            "IED": ied,
            "EMG_LENGTH": emg_length,
            "NUMBER_OF_MUS": number_of_mus,
            "BINARY_MUS_FIRING": binary_mus_firing,
        }

    elif source == "OTB_refsig":
        # jsonemgfile[1] contains the fsamp
        fsamp_dict = json.loads(jsonemgfile[1])
        fsamp = int(fsamp_dict["FSAMP"])
        # jsonemgfile[2] contains the reference signal to be treated as jsonemgfile[1]
        ref_signal_dict = json.loads(jsonemgfile[2])
        ref_signal_dict = json.loads(ref_signal_dict["REF_SIGNAL"])
        ref_signal = pd.DataFrame(ref_signal_dict)
        ref_signal.columns = ref_signal.columns.astype(int)
        ref_signal.index = ref_signal.index.astype(int)
        ref_signal.sort_index(inplace=True)

        resdict = {
            "SOURCE": source,
            "FSAMP": fsamp,
            "REF_SIGNAL": ref_signal,
        }

    else:
        raise Exception("File source not recognised")

    return resdict
