from scipy.io import loadmat
import pandas as pd
import numpy as np
from otbelectrodes import *

"""
Of this library, only few functions will be useful to the final user. Therefore, only some of them should imported as:

from openfiles import emg_from_otb, emg_from_demuse, refsig_from_otb
"""

# -------------------------- Define functions used in the DEMUSE openfile function -----------------------------
#
# As different Matlab file structures exist, a different processing is necessary to use them in Python.
# In most cases we will use pandas dataframe (df), the most used data structure (and library) for data management in Python.
# Here we convert Matlab arrays (1 dimensional structures) into a df. The output can be transposed to suit the user necessity.
def oned_mat_to_pd(variable_name, mat_file, transpose_=False):
    if variable_name in mat_file.keys():
        
        # Catch the case for the PNR of a single MU which is a float value that cannot be directly added to a dataframe
        if isinstance(mat_file[variable_name], float):
            res = {0:mat_file[variable_name]}
            if transpose_== True:
                mat = pd.DataFrame(res, index=[0]).transpose()
            else:
                mat = pd.DataFrame(res, index=[0])
        
        else:
            if transpose_== True:
                mat = pd.DataFrame(mat_file[variable_name]).transpose()
            else:
                mat = pd.DataFrame(mat_file[variable_name])
        
        return mat

    else:
        print("\nVariable {} was not found in the mat file, check the spelling against the dict_keys\n".format(variable_name))

        return np.nan

# Here we convert Matlab matrixes (2 dimensional structures) into a df.
# The code is exactly the same as above (ONED_mat_to_pd), however, the basic transpose state is different.
# For the basic user this will allow to make the script work properly even if he/she omits to pass transpose while calling the function
def twod_mat_to_pd(variable_name, mat_file, transpose_=True):
    if variable_name in mat_file.keys():
        # Catch the exception of a single MU that would create an alrerady transposed dataframe
        if len(mat_file["IPTs"].shape) == 1:
            transpose_= False

        if transpose_== True:
            mat = pd.DataFrame(mat_file[variable_name]).transpose()
        else:
            mat = pd.DataFrame(mat_file[variable_name])
        
        return mat

    else:
        print("\nVariable {} was not found in the mat file, check the spelling against the dict_keys\n".format(variable_name))

        return np.nan

# Here we convert Matlab Cell arrays (3 dimensional structures) into a Python list
# In this case, the list was preferred to a df beause it is easier to store nested data in lists than df
# The output can be transposed to suit the user necessity
def threed_mat_to_list(variable_name, mat_file, transpose_=False):
    if variable_name in mat_file.keys():
        if transpose_== True:
            mat = list(map(list, zip(*mat_file[variable_name])))
        else:
            mat = list(mat_file[variable_name])

        return mat

    else:
        print("\nVariable {} was not found in the mat file, check the spelling against the dict_keys\n".format(variable_name))

        return np.nan

# Here we create a df containing the binary representation of the MU firing over time
def create_binary_firings(EMG_LENGTH, NUMBER_OF_MUS, MUPULSES):
    if isinstance(MUPULSES, list): # skip the step if I don't have the MUPULSES (is nan)
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
    if variable_name in mat_file.keys():
        if transpose_== True:
            mat = mat_file[variable_name].ravel(order='F') # ‘F’ means to index the elements in column-major
            mat = pd.DataFrame(list(map(np.ravel, mat))).transpose()
        else:
            mat = mat_file[variable_name].ravel(order='F')
            mat = pd.DataFrame(list(map(np.ravel, mat)))
        
        return mat
    
    else:
        print("\nVariable {} was not found in the mat file, check the spelling against the dict_keys\n".format(variable_name))

        return np.nan
#-----------------------------------------------------------------------------------------------




def emg_from_demuse (file):
    """
    This function is used to import the .mat file used in DEMUSE as a dictionary of Python objects (mainly pandas dataframes).

    The only necessary input is the file path (including file extension .mat).

    It returns a dictionary containing the following: "SOURCE", "RAW_SIGNAL", "REF_SIGNAL", "PNR",
    "IPTS", "MUPULSES", "FSAMP", "IED", "EMG_LENGTH", "NUMBER_OF_MUS", "BINARY_MUS_FIRING".

    The returned file is called emgfile for convention.

    Note: the demuse file contains 65 raw EMG channels (1 empty) instead of 64 (as for OTB matrix standards).
    """
    mat_file = loadmat(file, simplify_cells=True)

    # Parse .mat obtained from DEMUSE to see the available variables
    # First: see the variables name
    print("\n--------------------------------\nAvailable dict keys are:\n\n{}\n".format(mat_file.keys()))

    # Second: collect the necessary variables in pandas dataframe (df) or list (for matlab cell arrays)   -variable_name must be a string (i.e., "name")
    REF_SIGNAL = oned_mat_to_pd(variable_name="ref_signal", mat_file=mat_file, transpose_=False)
    PNR = oned_mat_to_pd(variable_name="PNR", mat_file=mat_file, transpose_=False)
    IPTS = twod_mat_to_pd(variable_name="IPTs", mat_file=mat_file, transpose_=True)
    MUPULSES = threed_mat_to_list(variable_name="MUPulses", mat_file=mat_file, transpose_=False)
    
    # Third: collect the necessary values in variables
    FSAMP = int(mat_file["fsamp"])                                      # Sampling frequency
    IED = int(mat_file["IED"])                                          # Interelectrode distance
    EMG_LENGTH, NUMBER_OF_MUS = IPTS.shape                              # File length and number of MUs

    # Create a df with the binary representation of firing times, if necessary for other appliactions. Not used here
    BINARY_MUS_FIRING = create_binary_firings(EMG_LENGTH, NUMBER_OF_MUS, MUPULSES)

    # Fourth: obtain the raw EMG signal
    RAW_SIGNAL = raw_sig_from_demuse(variable_name="SIG", mat_file=mat_file, transpose_=True)

    # Use this to know what data you have or don't have
    SOURCE = "DEMUSE"

    resdict =   {
                "SOURCE" : SOURCE,
                "RAW_SIGNAL" : RAW_SIGNAL, 
                "REF_SIGNAL" : REF_SIGNAL, 
                "PNR" : PNR, 
                "IPTS" : IPTS, 
                "MUPULSES" : MUPULSES, 
                "FSAMP" : FSAMP, 
                "IED" : IED, 
                "EMG_LENGTH" : EMG_LENGTH, 
                "NUMBER_OF_MUS" : NUMBER_OF_MUS, 
                "BINARY_MUS_FIRING" : BINARY_MUS_FIRING,
                }

    return resdict

###########################################################################################################################################################
###########################################################################################################################################################
###########################################################################################################################################################



# -------------------------- Define functions used in the OTB openfile function -----------------------------
#
# Here we extract and convert variables as those extracted for the .mat file coming from the DEMUSE software.
# That would make it easier to use them later on

# The user can decide if he/she wants the filtered or unfiltered reference signal
def get_otb_refsignal(df, refsig):
    assert refsig[0] in [True, False], f"refsig[0] must be true or false. {refsig[0]} was passed instead."
    assert refsig[1] in ['filtered', 'unfiltered'], f"refsig[1] must be filtered or unfiltered. {refsig[1]} was passed instead."

    if refsig[0] == True:
        if refsig[1] == "filtered":
            # Extract the performed path (filtered data)
            REF_SIGNAL_FILTERED = df.filter(regex='performed path')
            if not REF_SIGNAL_FILTERED.empty: # Check if the ref signal is available, otherwise provide a warning
                REF_SIGNAL_FILTERED = REF_SIGNAL_FILTERED.rename(columns = {REF_SIGNAL_FILTERED.columns[0]:0}) 
                """ REF_SIGNAL_FILTERED.columns = np.arange(len(IPTS.columns)) does not work here """
                # Verify that there is no value above 100% since the REF_SIGNAL is expected to be expressed as % of the MViF
                if max(REF_SIGNAL_FILTERED[0]) > 100:
                    print("\nALERT! Ref signal grater than 100, did you use values normalised to the MViF?\n")
                
                return REF_SIGNAL_FILTERED
            
            else:
                print("\nReference signal not found, it might be necessary for some analysis\n")
            
                return np.nan
        
        elif refsig[1] == "unfiltered":
            # Extract the acquired path (raw data)
            REF_SIGNAL_UNFILTERED = df.filter(regex='acquired data')
            if not REF_SIGNAL_UNFILTERED.empty:
                REF_SIGNAL_UNFILTERED = REF_SIGNAL_UNFILTERED.rename(columns = {REF_SIGNAL_UNFILTERED.columns[0]:0})
                # Verify that there is no value above 100% since the REF_SIGNAL is expected to be expressed as % of the MViF
                if max(REF_SIGNAL_UNFILTERED[0]) > 100:
                    print("\nALERT! Ref signal grater than 100, did you use values normalised to the MViF?\n")

                return REF_SIGNAL_UNFILTERED
            
            else:
                print("\nReference signal not found, it might be necessary for some analysis\n")
            
                return np.nan

        else:
            raise Exception("Wrong input in the get_OTB_refsignal function, you can use ref=\"filtered\" or ref=\"unfiltered\"")
            
    else:
        print("\nReference signal not found, it might be necessary for some analysis\n")

        return np.nan

def get_otb_decomposition(df):
    # Extract the IPTS and rename columns progressively
    IPTS = df.filter(regex='Source for decomposition')
    IPTS.columns = np.arange(len(IPTS.columns)) #IPTS = IPTS.rename(columns={x:y for x,y in zip(IPTS.columns,range(0,len(IPTS.columns)))})
    # Verify to have the IPTS
    if IPTS.empty:
        IPTS = np.nan

    #MUPULSES
    BINARY_MUS_FIRING = df.filter(regex='Decomposition of')
    BINARY_MUS_FIRING.columns = np.arange(len(BINARY_MUS_FIRING.columns))
    # Verify to have the BINARY_MUS_FIRING
    if BINARY_MUS_FIRING.empty:
        BINARY_MUS_FIRING = np.nan

    return IPTS, BINARY_MUS_FIRING

def get_otb_mupulses(binarymusfiring, numberofMUs):
    # Create empty list of lists to fill with ndarrays containing the mupulses (point of firing)
    MUPULSES = [ [] for _ in range(numberofMUs) ]

    for i in binarymusfiring: # Loop all the MUs
        my_ndarray = []
        for idx, x in binarymusfiring[i].iteritems(): # Loop the MU firing times
            if x > 0:
                my_ndarray.append(idx)  # Take the firing time and add it to the ndarray

        my_ndarray = np.array(my_ndarray)
        MUPULSES[i] = my_ndarray
    
    return MUPULSES

def get_otb_ied(df):
    for matrix in OTBelectrodes_ied.keys():
        # Check the matrix used in the columns name (in the df obtained from OTBiolab+)
        if matrix in str(df.columns):
            IED = int(OTBelectrodes_ied[matrix])

            return IED # we don't need break since return ends the function

def get_otb_rawsignal(df):
    # Drop all the known columns different from the raw EMG signal.
    # This is a workaround since the OTBiolab+ software does not export a unique name for the raw EMG signal
    pattern = 'Source for decomposition|Decomposition of|acquired data|performed path'
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
        raise Exception("Failure in searching the raw signal, please check that it is present in the .mat file and that only the accepted parameters have been included")

#-----------------------------------------------------------------------------------------------




def emg_from_otb(file, refsig=[True, "filtered"]):
    """
    This function is used to import the .mat file exportable by the OTBiolab+ software as a dictionary of Python objects (mainly pandas dataframes).

    The first argument is the file path (including file extension .mat).

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
    print("\n--------------------------------\nAvailable dict keys are:\n\n{}\n".format(mat_file.keys()))

    # Second: Simplify (rename) columns description and extract all the parameters in a pandas dataframe
    df = pd.DataFrame(mat_file["Data"], columns=mat_file["Description"])
    #print(df.head())

    REF_SIGNAL = get_otb_refsignal(df=df, refsig=refsig)
    PNR = np.nan
    IPTS, BINARY_MUS_FIRING = get_otb_decomposition(df=df)
    EMG_LENGTH, NUMBER_OF_MUS = IPTS.shape
    MUPULSES = get_otb_mupulses(binarymusfiring=BINARY_MUS_FIRING, numberofMUs=NUMBER_OF_MUS)
    FSAMP = int(mat_file["SamplingFrequency"])
    IED = get_otb_ied(df=df)
    RAW_SIGNAL = get_otb_rawsignal(df)

    # Use this to know what data you have or don't have
    SOURCE = "OTB"

    resdict =   {
                "SOURCE" : SOURCE,
                "RAW_SIGNAL" : RAW_SIGNAL, 
                "REF_SIGNAL" : REF_SIGNAL, 
                "PNR" : PNR, 
                "IPTS" : IPTS, 
                "MUPULSES" : MUPULSES, 
                "FSAMP" : FSAMP, 
                "IED" : IED, 
                "EMG_LENGTH" : EMG_LENGTH, 
                "NUMBER_OF_MUS" : NUMBER_OF_MUS, 
                "BINARY_MUS_FIRING" : BINARY_MUS_FIRING,
                }

    return resdict

#-----------------------------------------------------------------------------------------------




def refsig_from_otb (file, refsig="filtered"):
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
    print("\n--------------------------------\nAvailable dict keys are:\n\n{}\n".format(mat_file.keys()))

    # Second: Simplify (rename) columns description and extract all the parameters in a pandas dataframe
    df = pd.DataFrame(mat_file["Data"], columns=mat_file["Description"])
    #print(df.head())

    # Convert the input passed to refsig in a list compatible with the function get_otb_refsignal
    refsig_=[True, refsig]
    REF_SIGNAL = get_otb_refsignal(df=df, refsig=refsig_)

    # Use this to know what data you have or don't have
    SOURCE = "OTB"
    FSAMP = int(mat_file["SamplingFrequency"])

    resdict =   {
                "SOURCE" : SOURCE,
                "FSAMP" : FSAMP,
                "REF_SIGNAL" : REF_SIGNAL,
                }

    return resdict


###########################################################################################################################################################
###########################################################################################################################################################
###########################################################################################################################################################
# Test part
if __name__ == "__main__":
    import os, sys
    
    # Test OTB file
    file_toOpen = os.path.join(sys.path[0], "Decomposed Test files/OTB_25MViF_TRAPEZOIDAL_testfile.mat") # Test it on a common trapezoidal contraction
    emgfile = emg_from_otb(file=file_toOpen, refsig=[True, "filtered"])
    print(emgfile["NUMBER_OF_MUS"])

    """ # Test DEMUSE file
    #file_toOpen = os.path.join(sys.path[0], "Decomposed Test files/DEMUSE_10MViF_TRAPEZOIDAL_testfile.mat") # Test it on a common trapezoidal contraction
    file_toOpen = os.path.join(sys.path[0], "Decomposed Test files/DEMUSE_10MViF_TRAPEZOIDAL_only1MU_testfile.mat") # Test it on a contraction with a single MU
    emgfile = emg_from_demuse(file=file_toOpen) """