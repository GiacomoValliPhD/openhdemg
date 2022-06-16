"""
This file contains all the functions that don't properly apply to the plot or analysis category.
However, these functions are necessary for the usability of the library.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def showselect(emgfile, title=""):
    """
    This function is used to select a part of the recording (based on the reference signal).
    
    The first argument should be the emgfile.

    Additionally, a title of the plot can be passed in title="Do this".

    The area can be selected with any letter or number in the keyboard, wrong points can be removed
    by pressing the right mouse button. Once finished, press enter to continue.

    It returns the start and the end point of the selection.

    Suggested names for the returned objects: start_, end_
    """
    # Extract the variables of interest from the EMG file
    REF_SIGNAL = emgfile["REF_SIGNAL"]

    # Show the signal for the selection
    plt.figure(num="Fig_ginput")
    plt.plot(REF_SIGNAL[0])
    plt.xlabel("Samples")
    plt.ylabel("%MViF")
    plt.title(title, fontweight ="bold")
    ginput_res = plt.ginput(n=-1, timeout=0, mouse_add=None)
    # Sort the input range of the steady-state
    if ginput_res[0][0] < ginput_res[1][0]:
        start_ = round(ginput_res[0][0])
        end_ = round(ginput_res[1][0])
    else:
        start_ = round(ginput_res[1][0])
        end_ = round(ginput_res[0][0])
    
    return start_, end_


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
    
    # Create the object to store the resized emgfile
    rs_emgfile = emgfile
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
            df = pd.DataFrame(emgfile["MUPULSES"][mu] if emgfile["NUMBER_OF_MUS"] > 1 else emgfile["MUPULSES"])
            # Calculate time in seconds and add it in column 1
            df[1] = df[0] / emgfile["FSAMP"]
            # Calculate the delta (difference) between the firings and istantaneous discharge rate (idr), add it in column 2
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
        print("MUPULSES is probably absent or it is not contained in a list")