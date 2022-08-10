"""
This file contains all the functions that don't properly apply to the plot or analysis category.
However, these functions are necessary for the usability of the library.
"""
import copy
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal


def showselect(emgfile, title="", nclic=2):
    """
    This function is used to select a part of the recording (based on the reference signal).
    
    The first argument should be the emgfile.
    Additionally (and encouraged), a title of the plot can be passed in title="Do this".
    By default, this function collects and sorts 2 clics. 1 and 4 clics can also be specified with nclic.
    The area can be selected with any letter or number in the keyboard, wrong points can be removed
    by pressing the right mouse button. Once finished, press enter to continue.
    It returns the start and the end point of the selection.
    """
    # Extract the variables of interest from the EMG file
    REF_SIGNAL = emgfile["REF_SIGNAL"]

    # Show the signal for the selection
    plt.figure(num="Fig_ginput")
    plt.plot(REF_SIGNAL[0])
    plt.xlabel("Samples")
    plt.ylabel("MViF")
    plt.title(title, fontweight ="bold")
    ginput_res = plt.ginput(n=-1, timeout=0, mouse_add=None)

    # Check if the user entered the correct number of clics
    if nclic != len(ginput_res):
        raise Exception("Wrong number of inputs, read the title")
    
    # Act according to the number of clics
    if nclic == 2:
    # Sort the input range. Used to resize the signal, select the steady-state, calculate MViF 
        if ginput_res[0][0] < ginput_res[1][0]:
            start_point = round(ginput_res[0][0])
            end_point = round(ginput_res[1][0])
        else:
            start_point = round(ginput_res[1][0])
            end_point = round(ginput_res[0][0])
        
        plt.close()
        return start_point, end_point
    
    elif nclic == 1:
        start_point = round(ginput_res[0][0])

        plt.close()
        return start_point
    
    elif nclic ==4: # Used for activation capacity
        points = [ginput_res[0][0], ginput_res[1][0], ginput_res[2][0], ginput_res[3][0]]
        # Sort the input range
        points.sort()
        
        start_point_tw = round(points[0])
        end_point_tw = round(points[1])
        start_point_rest = round(points[2])
        end_point_rest = round(points[3])
        
        plt.close()
        return start_point_tw, end_point_tw, start_point_rest, end_point_rest


def resize_emgfile(emgfile, area=None):
    """
    This function resizes all the emgfile (temporarily) to compute the various parameters only in
    the area of interest.
    The first argument should be the emgfile.
    If the resizing area is already known, it can be passed (in samples, as a list (e.g., [120,2560])) as
    input to area. If area == None, then the user can select the area of interest manually.
    It returns the new (resized) emgfile and the start and end of the selection (can be used for code automation).
    Suggested names for the returned objects: rs_emgfile, start_, end_
    """
    # Identify the area of interest
    if isinstance(area, list) and len(area) == 2:
        start_ = area[0]
        end_ = area[1]
    
    else:
        # Visualise and select the steady-state
        start_, end_ = showselect(emgfile, title="Select the start/end area to consider then press enter")
    
    # Create the object to store the resized emgfile.
    # Create a deepcopy to avoid changing the original emgfile
    rs_emgfile = copy.deepcopy(emgfile)
    """
    Need to be resized: ==>
    emgfile =   {
                "SOURCE" : SOURCE,
                ==> "RAW_SIGNAL" : RAW_SIGNAL, 
                ==> "REF_SIGNAL" : REF_SIGNAL, 
                "PNR" : PNR, 
                ==> "IPTS" : IPTS, 
                ==> "MUPULSES" : MUPULSES, 
                "FSAMP" : FSAMP, 
                "IED" : IED, 
                ==> "EMG_LENGTH" : EMG_LENGTH, 
                "NUMBER_OF_MUS" : NUMBER_OF_MUS, 
                ==> "BINARY_MUS_FIRING" : BINARY_MUS_FIRING,
                }
    """
    rs_emgfile["RAW_SIGNAL"] = emgfile["RAW_SIGNAL"].iloc[start_ : end_]
    rs_emgfile["REF_SIGNAL"] = emgfile["REF_SIGNAL"].iloc[start_ : end_]
    rs_emgfile["IPTS"] = emgfile["IPTS"].iloc[start_ : end_]
    rs_emgfile["EMG_LENGTH"] = int(len(emgfile["IPTS"].index))
    rs_emgfile["BINARY_MUS_FIRING"] = emgfile["BINARY_MUS_FIRING"].iloc[start_ : end_]
    for i in range(emgfile["NUMBER_OF_MUS"]):
        # Here I need to mask the array based on a filter and return the values in an array with []
        rs_emgfile["MUPULSES"][i] = emgfile["MUPULSES"][i][(emgfile["MUPULSES"][i] >= start_) & (emgfile["MUPULSES"][i] < end_)]
   
    return rs_emgfile, start_, end_


def compute_idr(emgfile):
    """
    This function computes the instantaneous discharge rate (IDR) from the MUPULSES.
    The IDR is very useful for plotting and visualisation of the MUs behaviour.
    The only necessary argument is the emgfile.
    It returns a dict with a key for every MUs (keys are integers). Accessing the key, we have a dataframe containing
    the mupulses, the time of firing in seconds and the idr for that specific MU.
    """
    # Compute the instantaneous discharge rate (IDR) from the MUPULSES
    if isinstance(emgfile["MUPULSES"], list):
        # Empty dict to fill with dataframes containing the MUPULSES in [0] and idr in [1]
        idr = {x: np.nan ** 2 for x in range(emgfile["NUMBER_OF_MUS"])}

        for mu in range(emgfile["NUMBER_OF_MUS"]):
            # Manage the exception of a single MU
            # Put the mupulses of the MU in the loop in a df
            df = pd.DataFrame(emgfile["MUPULSES"][mu] if emgfile["NUMBER_OF_MUS"] > 1 else np.array(emgfile["MUPULSES"]))
            # Calculate time in seconds and add it in column 1
            df[1] = df[0] / emgfile["FSAMP"]
            # Calculate the istantaneous discharge rate (idr), add it in column 2
            df[2] = emgfile["FSAMP"] / df[0].diff()
            
            df.rename(columns = {0:"mupulses", 1:"timesec", 2:"idr"}, inplace = True)
            
            # Add the idr to the idr dict
            idr[mu] = (df)
            
            """ 
            idr is a dict with a key for every MU
            idr[mu] is a DataFrame
                 mupulses    timesec       idr
            0        3956   1.931641       NaN
            1        4398   2.147461  4.633484
            2        4738   2.313477  6.023529
            3        5030   2.456055  7.013699
            4        5366   2.620117  6.095238
            ..        ...        ...       ...
            184     59441  29.023926  6.340557
            185     59756  29.177734  6.501587
            186     60258  29.422852  4.079681
            187     60813  29.693848  3.690090
            188     61453  30.006348  3.200000
            """

        return idr
    
    else:
        raise Exception("MUPULSES is probably absent or it is not contained in a list")


def delete_mus(emgfile, munumber):
    """
    This function allows to delete unwanted MUs.
    The first argument should be the emgfile.
    The second argument is/are the MU/MUs to delete. An integer or a list of MUs to remove
    can be passed in input. The list can be passed as a manually-written list or with:
    munumber=[*range(0, 12)], 
    We need the "*" operator to unpack the results of range and build a list.
    The function returns the same emgfile but without the specified MUs.
    The function will not work if the emgfile only contains 1 motor unit, 
    since the entire file should be deleted instead. In this case, None will be returned.
    """
    
    # Check how many MUs we have, if we only have 1 MU, the entire file should be deleted instead.
    if emgfile["NUMBER_OF_MUS"] <= 1:
        return
    
    # Create the object to store the new emgfile without the specified MUs.
    # Create a deepcopy to avoid changing the original emgfile
    del_emgfile = copy.deepcopy(emgfile)
    """
    Need to be changed: ==>
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
                ==> "NUMBER_OF_MUS" : NUMBER_OF_MUS, 
                ==> "BINARY_MUS_FIRING" : BINARY_MUS_FIRING,
                }
    """

    # Common part working for all the possible inputs to munumber
    # Drop PNR values and rename the index
    if emgfile["SOURCE"] == "DEMUSE": # Modify once PNR calculation is implemented also for OTB files
        del_emgfile["PNR"] = emgfile["PNR"].drop(munumber) # Works with lists and integers
        del_emgfile["PNR"].reset_index(inplace = True, drop = True) # Drop the old index

    # Drop IPTS by columns and rename the columns
    del_emgfile["IPTS"] = emgfile["IPTS"].drop(munumber, axis = 1) # Works with lists and integers
    del_emgfile["IPTS"].columns = range(del_emgfile["IPTS"].shape[1])

    # Drop BINARY_MUS_FIRING by columns and rename the columns
    del_emgfile["BINARY_MUS_FIRING"] = emgfile["BINARY_MUS_FIRING"].drop(munumber, axis = 1) # Works with lists and integers
    del_emgfile["BINARY_MUS_FIRING"].columns = range(del_emgfile["BINARY_MUS_FIRING"].shape[1])
    
    if isinstance(munumber, int):
        # Delete MUPULSES by position in the list.
        del del_emgfile["MUPULSES"][munumber]

        # Subrtact one MU to the total number
        del_emgfile["NUMBER_OF_MUS"] = emgfile["NUMBER_OF_MUS"] - 1
    
    elif isinstance(munumber, list):
        # Delete all the content in the del_emgfile["MUPULSES"] and append only the MUs that we want to retain (exclude deleted MUs)
        # This is a workaround to directly deleting elements
        del_emgfile["MUPULSES"] = []
        for mu in range(emgfile["NUMBER_OF_MUS"]):
            if mu not in munumber:
                del_emgfile["MUPULSES"].append(emgfile["MUPULSES"][mu])
        
        # Subrtact the number of deleted MUs to the total number
        del_emgfile["NUMBER_OF_MUS"] = emgfile["NUMBER_OF_MUS"] - len(munumber)
    
    else:
        raise Exception("While calling the delete_mus function, you should pass an integer or a list in munumber= ")
    
    return del_emgfile


def filter_refsig(emgfile, order=4, cutoff=20):
    """
    This function is used to low-pass filter the reference signal and remove noise. The filter is a Zero-lag low-pass Butterworth.
    As first input, can be passed both the emgfile and the refsig (obtained from the function refsig_from_otb).
    Other inputs are: filter order (order, 4th if not specified), the cutoff frequency (cutoff, 20 Hz if not specified).
    It returns the filtered refsig.
    """
    # Create the object to store the filtered refsig.
    # Create a deepcopy to avoid changing the original refsig
    filtrefsig = copy.deepcopy(emgfile)

    # Calculate the components of the filter and apply them with filtfilt to obtain Zero-lag filtering
    b, a = signal.butter(N=order, Wn=cutoff, fs=filtrefsig["FSAMP"], btype="lowpass")
    filtrefsig["REF_SIGNAL"][0] = signal.filtfilt(b, a, filtrefsig["REF_SIGNAL"][0])

    return filtrefsig


def remove_offset(emgfile, offsetval=0, auto=0):
    """
    This function is used to remove the offset from the refsig. 
    
    As first input, can be passed both the emgfile and the refsig (obtained from the function refsig_from_otb).
    If offsetval is 0 (default), the user will be asked to manually select an aerea to compute the offset value.
    Otherwise, the value passed to offsetval will be used. Negative offsetval can be passed.
    If auto > 0, the script automatically removes the offset based on the number of samples passed in input.
    The function returns the same file but with the offset removed.
    """
    # Check that all the inputs are correct
    if not isinstance(offsetval, (float, int)):
        raise Exception(f"offsetval must be one of the following types: float, int. {type(offsetval)} was passed instead.")
    if not isinstance(auto, (float, int)):
        raise Exception(f"auto must be one of the following types: float, int. {type(auto)} was passed instead.")

    # Create the object to store the filtered refsig.
    # Create a deepcopy to avoid changing the original refsig
    offs_emgfile = copy.deepcopy(emgfile)
    
    # Act differently if the automatic removal of the offset is active (>0) or not
    if auto <= 0:
        if offsetval != 0:
            # Directly subtract the offset value.
            offs_emgfile["REF_SIGNAL"][0] = offs_emgfile["REF_SIGNAL"][0] - offsetval
        
        else:
            # Select the area to calculate the offset (average value of the selected area)
            start_, end_ = showselect(offs_emgfile, title="Select the start/end of a resting area to calculate the offset, then press enter")
            offsetval = offs_emgfile["REF_SIGNAL"].iloc[start_ : end_].mean()
            # We need to convert the series offsetval into float
            offs_emgfile["REF_SIGNAL"][0] = offs_emgfile["REF_SIGNAL"][0] - float(offsetval)
    
    else:
        # Compute and subtract the offset value.
        offsetval = offs_emgfile["REF_SIGNAL"].iloc[0 : auto].mean()
        # We need to convert the series offsetval into float
        offs_emgfile["REF_SIGNAL"][0] = offs_emgfile["REF_SIGNAL"][0] - float(offsetval)
    
    return offs_emgfile


def get_mvif(emgfile):
    """
    This function is used to measure the MViF. 
    
    As only input, can be passed both the emgfile and the refsig (obtained from the function refsig_from_otb).
    If multiple repetitions are selected, the maximum value will be returned.
    It returns a float.
    """
    # Select the area to measure the MViF (maximum value)
    start_, end_ = showselect(emgfile, title="Select the start/end area to measure the MViF, then press enter")
    mvif = emgfile["REF_SIGNAL"].iloc[start_ : end_].max()
    # We need to convert the series mvif into float
    mvif = round(float(mvif), 2)

    return mvif

def compute_rfd(emgfile, ms=[50, 100, 150, 200], startpoint=None):
    """
    This function is used to calculate the rate of force development (N/Sec). 
    
    As first input, can be passed both the emgfile and the refsig (obtained from the function refsig_from_otb).
    The time to calculate RFD is by default 50, 100, 150, 200 ms. A list with different values can be passed to ms.
    The user will be requested to manually select the starting point for the RFD by default. If an integer is passed
    to startpoint, this value will be used instead.
    It returns a dataframe containing the RFD.
    """
    
    # Check if the startpoint was passed
    if isinstance(startpoint, int):
        start_ = startpoint
    else:
        # Otherwise select the starting point for the RFD
        start_ = showselect(emgfile, title="Select the starting point for RFD, then press enter", nclic=1)

    # Create a dict to add the RFD
    rfd_dict = dict.fromkeys(ms, None)
    # Loop through the ms list and calculate the respective rfd.
    for thisms in ms:
        ms_insamples = round((int(thisms) * emgfile["FSAMP"]) / 1000)
    
        n_0 = emgfile["REF_SIGNAL"].iloc[start_]
        n_next = emgfile["REF_SIGNAL"].iloc[start_ + ms_insamples]
        
        rfdval = (n_next - n_0) / (thisms/1000) # (ms/1000 to convert mSec in Sec)
        
        rfd_dict[thisms] = rfdval
    
    rfd = pd.DataFrame(rfd_dict)
    
    return rfd



###########################################################################################################################################################
###########################################################################################################################################################
###########################################################################################################################################################
# Test part
if __name__ == "__main__":
    import os, sys
    from openfiles import emg_from_demuse, emg_from_otb
    import numpy as np

    """ # Test DEMUSE file
    file_toOpen = os.path.join(sys.path[0], "Decomposed Test files/DEMUSE_10MViF_TRAPEZOIDAL_testfile.mat") # Test it on a common trapezoidal contraction
    #file_toOpen = os.path.join(sys.path[0], "Decomposed Test files/DEMUSE_10MViF_TRAPEZOIDAL_only1MU_testfile.mat") # Test it on a contraction with a single MU
    emgfile = emg_from_demuse(file=file_toOpen) """

    # Test OTB file
    file_toOpen = os.path.join(sys.path[0], "Decomposed Test files/OTB_25MViF_TRAPEZOIDAL_testfile.mat") # Test it on a common trapezoidal contraction
    emgfile = emg_from_otb(file=file_toOpen, refsig=[True, "filtered"])

    res = delete_mus(emgfile, munumber=1)