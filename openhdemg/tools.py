"""
This module contains all the functions that don't properly apply to the plot
or analysis (of the MUs properties) category.
However, these functions are necessary for the usability of the library and
can be considered as "tools" necessary to operate with the HD-EMG recordings.
"""

import copy
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
import warnings
from openhdemg.mathtools import compute_pnr, compute_sil


def showselect(emgfile, title="", nclic=2):
    """
    Select a part of the recording.

    The area can be selected (based on the REF_SIGNAL) with any letter or
    number in the keyboard, wrong points can be removed by pressing the
    right mouse button. Once finished, press enter to continue.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile and in particular the REF_SIGNAL
        (which is used for the selection).
    title : str
        The title of the plot. It is optional but strongly recommended.
        It should describe the task to do.
    nclic: int {1, 2, 4}, default 2
        The number of clics to be collected.

    Returns
    -------
    points : int
        The selected points (sorted in ascending order) based on nclic.

    Raises
    ------
    ValueError
        When the user clicked a wrong number of inputs in the GUI.

    Examples
    --------
    Load the EMG file and select the points.

    >>> import openhdemg as emg
    >>> emgfile = emg.askopenfile(filesource="OTB_refsig")
    >>> start_point, end_point = emg.showselect(emgfile, title="Select 2 points", nclic=2)
    >>> start_point, end_point
    16115 40473
    """

    # Show the signal for the selection
    plt.figure(num="Fig_ginput")
    plt.plot(emgfile["REF_SIGNAL"][0])
    plt.xlabel("Samples")
    plt.ylabel("MViF")
    plt.title(title, fontweight="bold")
    ginput_res = plt.ginput(n=-1, timeout=0, mouse_add=None)

    # Check if the user entered the correct number of clics
    if nclic != len(ginput_res):
        raise ValueError("Wrong number of inputs, read the title")

    # Act according to the number of clics
    if nclic == 1:
        start_point = round(ginput_res[0][0])

        plt.close()
        return start_point
    
    elif nclic == 2:
        # Sort the input range. Used to resize the signal,
        # select the steady-state, calculate MViF
        if ginput_res[0][0] < ginput_res[1][0]:
            start_point = round(ginput_res[0][0])
            end_point = round(ginput_res[1][0])
        else:
            start_point = round(ginput_res[1][0])
            end_point = round(ginput_res[0][0])

        plt.close()
        return start_point, end_point

    elif nclic == 4:  # Used for activation capacity
        points = [
            ginput_res[0][0],
            ginput_res[1][0],
            ginput_res[2][0],
            ginput_res[3][0],
        ]
        # Sort the input range
        points.sort()

        start_point_tw = round(points[0])
        end_point_tw = round(points[1])
        start_point_rest = round(points[2])
        end_point_rest = round(points[3])

        plt.close()
        return start_point_tw, end_point_tw, start_point_rest, end_point_rest
    
    else:
        raise ValueError(f"nclic can be only one of 1, 2, 4. {nclic} was passed instead")


def create_binary_firings(EMG_LENGTH, NUMBER_OF_MUS, MUPULSES):
    """
    Create a binary representation of the MU firing.

    Create a binary representation of the MU firing over time
    based on the times of firing of each MU.

    Parameters
    ----------
    EMG_LENGTH : int
        Number of samples (length) in the emg file.
    NUMBER_OF_MUS : int
        Number of MUs in the emg file.
    MUPULSES : list of ndarrays
        Each ndarray should contain the times of firing of each MU.

    Returns
    -------
    mat : pd.DataFrame
        A pd.DataFrame containing the requested variable
        or np.nan if the variable was not found.
    """

    if isinstance(MUPULSES, list):
        # skip the step if I don't have the MUPULSES (is nan)
        # create an empty pd.DataFrame containing zeros
        binary_MUs_firing = pd.DataFrame(np.zeros((EMG_LENGTH, NUMBER_OF_MUS)))
        # Loop through the columns (MUs) and isolate the data of interest
        for i in range(NUMBER_OF_MUS):
            this_mu_binary_firing = binary_MUs_firing[i]
            this_mu_pulses = pd.DataFrame(MUPULSES[i])

            # Loop through the rows (time) and assign 1 if the MU is firing
            for position in range(len(this_mu_pulses)):
                firing_point = int(this_mu_pulses.iloc[position])
                this_mu_binary_firing.iloc[firing_point] = 1

            # Merge the work done with the original pd.DataFrame of zeros
            binary_MUs_firing[i] = this_mu_binary_firing

        return binary_MUs_firing

    else:
        return np.nan


def resize_emgfile(emgfile, area=None):
    """
    Resize all the emgfile.

    This function can be useful to compute the various parameters only in the
    area of interest.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile to resize.
    area : None or list, default None
        The resizing area. If already known, it can be passed in samples, as a
        list (e.g., [120,2560]).
        If None, the user can select the area of interest manually.

    Returns
    -------
    rs_emgfile : dict
        the new (resized) emgfile.
    start_, end_ : int
        the start and end of the selection (can be used for code automation).

    Notes
    -----
    Suggested names for the returned objects: rs_emgfile, start_, end_.
    
    PNR and SIL are computed again in the new resized area.
    """

    # Identify the area of interest
    if isinstance(area, list) and len(area) == 2:
        start_ = area[0]
        end_ = area[1]

    else:
        # Visualise and select the area to resize
        start_, end_ = showselect(
            emgfile, title="Select the start/end area to resize then press enter"
        )

    # Create the object to store the resized emgfile.
    # Create a deepcopy to avoid changes in the original emgfile
    rs_emgfile = copy.deepcopy(emgfile)
    """
    PNR and SIL should be re-computed on the new portion of the file ==>.
    Need to be resized: ==>
    emgfile =   {
                "SOURCE": SOURCE,
                ==> "RAW_SIGNAL": RAW_SIGNAL,
                ==> "REF_SIGNAL": REF_SIGNAL,
                ==> "PNR": PNR,
                ==> "SIL": SIL,
                ==> "IPTS": IPTS,
                ==> "MUPULSES": MUPULSES,
                "FSAMP": FSAMP,
                "IED": IED,
                ==> "EMG_LENGTH": EMG_LENGTH,
                "NUMBER_OF_MUS": NUMBER_OF_MUS,
                ==> "BINARY_MUS_FIRING": BINARY_MUS_FIRING,
                }
    """
    rs_emgfile["RAW_SIGNAL"] = rs_emgfile["RAW_SIGNAL"].iloc[start_:end_]
    rs_emgfile["REF_SIGNAL"] = rs_emgfile["REF_SIGNAL"].iloc[start_:end_]
    rs_emgfile["IPTS"] = rs_emgfile["IPTS"].iloc[start_:end_]
    rs_emgfile["EMG_LENGTH"] = int(len(rs_emgfile["IPTS"].index))
    rs_emgfile["BINARY_MUS_FIRING"] = rs_emgfile["BINARY_MUS_FIRING"].iloc[start_:end_]
    for i in range(rs_emgfile["NUMBER_OF_MUS"]):
        # Here I need to mask the array based on a filter and return the values in an array with []
        rs_emgfile["MUPULSES"][i] = rs_emgfile["MUPULSES"][i][
            (rs_emgfile["MUPULSES"][i] >= start_) & (rs_emgfile["MUPULSES"][i] < end_)
        ]

    # Compute PNR and SIL
    if rs_emgfile["NUMBER_OF_MUS"] > 0:
        # Calculate the PNR
        to_append = []
        for mu in range(rs_emgfile["NUMBER_OF_MUS"]):
            res = compute_pnr(
                ipts=rs_emgfile["IPTS"][mu],
                mupulses=rs_emgfile["MUPULSES"][mu],
                fsamp=emgfile["FSAMP"],
            )
            to_append.append(res)
        rs_emgfile["PNR"] = pd.DataFrame(to_append)

        # Calculate the SIL
        to_append = []
        for mu in range(rs_emgfile["NUMBER_OF_MUS"]):
            res = compute_sil(
                ipts=rs_emgfile["IPTS"][mu],
                mupulses=rs_emgfile["MUPULSES"][mu],
            )
            to_append.append(res)
        rs_emgfile["SIL"] = pd.DataFrame(to_append)

    else:
        rs_emgfile["PNR"] = np.nan
        rs_emgfile["SIL"] = np.nan

    return rs_emgfile, start_, end_


def compute_idr(emgfile):
    """
    Compute the IDR. # TODO maybe it is not IDR

    This function computes the instantaneous discharge rate (IDR) from the
    MUPULSES.
    The IDR is very useful for plotting and visualisation of the MUs behaviour.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.

    Returns
    -------
    idr : dict
        A dict containing a pd.DataFrame for each MU (keys are integers).
        Accessing the key, we have a pd.DataFrame containing:
            mupulses: firing sample.
            diff_mupulses: delta between consecutive firing samples.
            timesec: delta between consecutive firing samples in seconds.
            idr: instantaneous discharge rate.

    Examples
    --------
    Load the EMG file, compute IDR and access the results for the first MU.

    >>> import openhdemg as emg
    >>> emgfile = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> idr = emg.compute_idr(emgfile=emgfile)
    >>> munumber = 0
    >>> idr[munumber]
        mupulses  diff_mupulses    timesec       idr
    0        9221            NaN   4.502441       NaN
    1        9580          359.0   4.677734  5.704735
    2        9973          393.0   4.869629  5.211196
    3       10304          331.0   5.031250  6.187311
    4       10617          313.0   5.184082  6.543131
    ..        ...            ...        ...       ...
    149     54521          395.0  26.621582  5.184810
    150     54838          317.0  26.776367  6.460568
    151     55417          579.0  27.059082  3.537133
    152     55830          413.0  27.260742  4.958838
    153     56203          373.0  27.442871  5.490617
    """

    # Compute the instantaneous discharge rate (IDR) from the MUPULSES
    if isinstance(emgfile["MUPULSES"], list):
        # Empty dict to fill with dataframes containing the MUPULSES in [0] and idr in [1]
        idr = {x: np.nan**2 for x in range(emgfile["NUMBER_OF_MUS"])}

        for mu in range(emgfile["NUMBER_OF_MUS"]):
            # Manage the exception of a single MU
            # Put the MUPULSES of the MU in the loop in a df
            df = pd.DataFrame(
                emgfile["MUPULSES"][mu]
                if emgfile["NUMBER_OF_MUS"] > 1
                else np.transpose(np.array(emgfile["MUPULSES"]))
            )

            # Calculate difference in MUPULSES and add it in column 1
            df[1] = df[0].diff()
            # Calculate time in seconds and add it in column 2
            df[2] = df[0] / emgfile["FSAMP"]
            # Calculate the istantaneous discharge rate (idr), add it in column 3
            df[3] = emgfile["FSAMP"] / df[0].diff()

            df.rename(
                columns={0: "mupulses", 1: "diff_mupulses", 2: "timesec", 3: "idr"},
                inplace=True,
            )

            # Add the idr to the idr dict
            idr[mu] = df

        return idr

    else:
        raise Exception("MUPULSES is probably absent or it is not contained in a list")


def delete_mus(emgfile, munumber, if_single_mu="ignore"):
    """
    Delete unwanted MUs.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    munumber : int, list of int
        The MUs to remove. If a single MU has to be removed, this should be an
        int (number of the MU).
        If multiple MUs have to be removed, a list of int should be passed.
        An unpacked (*) range can also be passed as munumber=[*range(0, 5)].
        munumber is expected to be with base 0 (i.e., the first MU in the file
        is the number 0).
    if_single_mu : str {"ignore", "remove"}, default "ignore"
        A string indicating how to behave in case of a file with a single MU.

            ``ignore``
            Ignore the process and return the original emgfile. (Default)
            ``remove``
            Remove the MU and return the emgfile without the MU. (Default)
            This should allow full compatibility with the use of this file
            in following processing (i.e., save/load and analyse).

    Returns
    -------
    emgfile : dict
        The dictionary containing the emgfile without the unwanted MUs.
    """

    # Check how to behave in case of a single MU
    if if_single_mu == "ignore":
        # Check how many MUs we have, if we only have 1 MU, the entire file should be deleted instead.
        if emgfile["NUMBER_OF_MUS"] <= 1:
            warnings.warn(
                "There is only 1 MU in the file, and it has not been removed. You can change this behaviour with if_single_mu='remove' in the function delete_mus"
            )

            return emgfile

    elif if_single_mu == "remove":
        pass

    else:
        raise ValueError(
            "if_single_mu must be one of 'ignore' or 'remove', {} was passed instead".format(
                if_single_mu
            )
        )

    # Create the object to store the new emgfile without the specified MUs.
    # Create a deepcopy to avoid changes in the original emgfile
    del_emgfile = copy.deepcopy(emgfile)
    """
    Need to be changed: ==>
    emgfile =   {
                "SOURCE" : SOURCE,
                "RAW_SIGNAL" : RAW_SIGNAL,
                "REF_SIGNAL" : REF_SIGNAL,
                ==> "PNR" : PNR,
                ==> "SIL" : SIL
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
    del_emgfile["PNR"] = del_emgfile["PNR"].drop(munumber)  # Works with lists and integers
    del_emgfile["PNR"].reset_index(inplace=True, drop=True)  # Drop the old index

    # Drop SIL values and rename the index
    del_emgfile["SIL"] = del_emgfile["SIL"].drop(munumber)
    del_emgfile["SIL"].reset_index(inplace=True, drop=True)

    # Drop IPTS by columns and rename the columns
    del_emgfile["IPTS"] = del_emgfile["IPTS"].drop(munumber, axis=1)
    del_emgfile["IPTS"].columns = range(del_emgfile["IPTS"].shape[1])

    # Drop BINARY_MUS_FIRING by columns and rename the columns
    del_emgfile["BINARY_MUS_FIRING"] = del_emgfile["BINARY_MUS_FIRING"].drop(munumber, axis=1)
    del_emgfile["BINARY_MUS_FIRING"].columns = range(del_emgfile["BINARY_MUS_FIRING"].shape[1])

    if isinstance(munumber, int):
        # Delete MUPULSES by position in the list.
        del del_emgfile["MUPULSES"][munumber]

        # Subrtact one MU to the total number
        del_emgfile["NUMBER_OF_MUS"] = del_emgfile["NUMBER_OF_MUS"] - 1

    elif isinstance(munumber, list):
        # Delete all the content in the del_emgfile["MUPULSES"] and append
        # only the MUs that we want to retain (exclude deleted MUs)
        # This is a workaround to directly deleting, for safer implementation
        del_emgfile["MUPULSES"] = []
        for mu in range(emgfile["NUMBER_OF_MUS"]):
            if mu not in munumber:
                del_emgfile["MUPULSES"].append(emgfile["MUPULSES"][mu])

        # Subrtact the number of deleted MUs to the total number
        del_emgfile["NUMBER_OF_MUS"] = del_emgfile["NUMBER_OF_MUS"] - len(munumber)

    else:
        raise Exception(
            "While calling the delete_mus function, you should pass an integer or a list to munumber= "
        )

    return del_emgfile


def sort_mus(emgfile):
    """
    Sort the MUs in order of recruitment (ascending order) 
    
    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.

    Returns
    -------
    sorted_emgfile : dict
        The dictionary containing the sorted emgfile.
    """

    # If we only have 1 MU, there is no necessity to sort it.
    if emgfile["NUMBER_OF_MUS"] <= 1:
        return emgfile

    # Create the object to store the sorted emgfile.
    # Create a deepcopy to avoid changing the original emgfile
    sorted_emgfile = copy.deepcopy(emgfile)
    """
    Need to be changed: ==>
    emgfile =   {
                "SOURCE" : SOURCE,
                "RAW_SIGNAL" : RAW_SIGNAL, 
                "REF_SIGNAL" : REF_SIGNAL, 
                ==> "PNR" : PNR,
                ==> "SIL": SIL,
                ==> "IPTS" : IPTS, 
                ==> "MUPULSES" : MUPULSES, 
                "FSAMP" : FSAMP, 
                "IED" : IED, 
                "EMG_LENGTH" : EMG_LENGTH, 
                "NUMBER_OF_MUS" : NUMBER_OF_MUS, 
                ==> "BINARY_MUS_FIRING" : BINARY_MUS_FIRING,
                }
    """

    # Identify sorting_order by sorting the the firsr MUpulse of every MUs
    df = pd.DataFrame()
    df["firstpulses"] = [
        emgfile["MUPULSES"][i][0] for i in range(emgfile["NUMBER_OF_MUS"])
    ]
    df.sort_values(by="firstpulses", inplace=True)
    sorting_order = list(df.index)

    # Sort PNR (single column)
    for origpos, newpos in enumerate(sorting_order):
        sorted_emgfile["PNR"].loc[origpos] = emgfile["PNR"].loc[newpos]
    
    # Sort SIL (single column)
    for origpos, newpos in enumerate(sorting_order):
        sorted_emgfile["SIL"].loc[origpos] = emgfile["SIL"].loc[newpos]

    # Sort IPTS (multiple columns, sort by columns, then reset columns' name)
    sorted_emgfile["IPTS"] = sorted_emgfile["IPTS"].reindex(columns=sorting_order)
    sorted_emgfile["IPTS"].columns = np.arange(emgfile["NUMBER_OF_MUS"])

    # Sort BINARY_MUS_FIRING (multiple columns, sort by columns, then reset columns' name)
    sorted_emgfile["BINARY_MUS_FIRING"] = sorted_emgfile["BINARY_MUS_FIRING"].reindex(
        columns=sorting_order
    )
    sorted_emgfile["BINARY_MUS_FIRING"].columns = np.arange(emgfile["NUMBER_OF_MUS"])

    # Sort MUPULSES (I preferred to use the sorting_order as a double-check, but could also use:
    # sorted_emgfile["MUPULSES"] = sorted(sorted_emgfile["MUPULSES"], key=min, reverse=False))
    for origpos, newpos in enumerate(sorting_order):
        sorted_emgfile["MUPULSES"][origpos] = emgfile["MUPULSES"][newpos]

    return sorted_emgfile


def compute_covsteady(emgfile, start_steady=-1, end_steady=-1):
    """
    Calculates the covsteady.

    This function calculates the coefficient of variation of the steady-state
    phase (covsteady of the REF_SIGNAL).

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    start_steady, end_steady : int, default -1
        The start and end point (in samples) of the steady-state phase.
        If < 0 (default), the user will need to manually select the start and
        end of the steady-state phase.

    Returns
    -------
    covsteady : float
        The coefficient of variation of the steady-state phase in %.

    See also
    --------
    compute_idr : computes the instantaneous discharge rate.

    Examples
    --------
    Load the EMG file, compute covsteady and access the result from GUI.

    >>> import openhdemg as emg
    >>> emgfile = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> covsteady = emg.compute_covsteady(emgfile=emgfile)
    >>> covsteady
    1.452806

    The process can be automated by bypassing the GUI.

    >>> import openhdemg as emg
    >>> emgfile = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> covsteady = emg.compute_covsteady(emgfile=emgfile, start_steady=3580, end_steady=15820)
    >>> covsteady
    35.611263
    """

    if (start_steady < 0 and end_steady < 0) or (start_steady < 0 or end_steady < 0):
        start_steady, end_steady = showselect(
            emgfile, title="Select the start/end of the steady-state then press enter"
        )

    ref = emgfile["REF_SIGNAL"].loc[start_steady:end_steady]
    covsteady = (ref.std() / ref.mean()) * 100

    return covsteady[0]


def filter_rawemg(emgfile, order=2, lowcut=20, highcut=500):
    """
    Band-pass filter RAW_SIGNAL.

    The filter is a Zero-lag band-pass Butterworth.
    
    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    order : int, default 2
        The filter order.
    lowcut : int, default 20
        The lower cut-off frequency in Hz.
    highcut : int, default 500
        The higher cut-off frequency in Hz.

    Returns
    -------
    filteredrawsig : dict
        The dictionary containing the emgfile with a filtered RAW_SIGNAL.
    """

    filteredrawsig = copy.deepcopy(emgfile)

    # Calculate the components of the filter and apply them with filtfilt to obtain Zero-lag filtering
    # sos should be preferred over filtfilt as second-order sections have fewer numerical problems.
    sos = signal.butter(N=order, Wn=[lowcut, highcut], btype="bandpass", output="sos", fs=filteredrawsig["FSAMP"])
    for col in filteredrawsig["RAW_SIGNAL"]:
        filteredrawsig["RAW_SIGNAL"][col] = signal.sosfiltfilt(sos, x=filteredrawsig["RAW_SIGNAL"][col])

    return filteredrawsig


def filter_refsig(emgfile, order=4, cutoff=15):
    """
    Low-pass filter REF_SIGNAL.

    This function is used to low-pass filter the REF_SIGNAL and remove noise.
    The filter is a Zero-lag low-pass Butterworth.
    
    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    order : int, default 4
        The filter order.
    cutoff : int, default 15
        The cut-off frequency in Hz.

    Returns
    -------
    filteredrefsig : dict
        The dictionary containing the emgfile with a filtered REF_SIGNAL.
    
    See also
    --------
    remove_offset : remove the offset from the REF_SIGNAL.
    """

    filteredrefsig = copy.deepcopy(emgfile)

    # Calculate the components of the filter and apply them with filtfilt to obtain Zero-lag filtering
    # sos should be preferred over filtfilt as second-order sections have fewer numerical problems.
    sos = signal.butter(N=order, Wn=cutoff, btype="lowpass", output="sos", fs=filteredrefsig["FSAMP"])
    filteredrefsig["REF_SIGNAL"][0] = signal.sosfiltfilt(sos, x=filteredrefsig["REF_SIGNAL"][0])

    return filteredrefsig


def remove_offset(emgfile, offsetval=0, auto=0):
    """
    Remove the offset from the REF_SIGNAL.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    offsetval : float, default 0
        Value of the offset. If offsetval is 0 (default), the user will be
        asked to manually select an aerea to compute the offset value.
        Otherwise, the value passed to offsetval will be used.
        Negative offsetval can be passed.
    auto : int, default 0
        If auto > 0, the script automatically removes the offset based on the
        number of samples passed in input.

    Returns
    -------
    offs_emgfile : dict
        The dictionary containing the emgfile with a corrected offset of the
        REF_SIGNAL.

    See also
    --------
    filter_refsig : low-pass filter REF_SIGNAL.
    """

    # Check that all the inputs are correct
    if not isinstance(offsetval, (float, int)):
        raise TypeError(
            f"offsetval must be one of the following types: float, int. {type(offsetval)} was passed instead."
        )
    if not isinstance(auto, (float, int)):
        raise TypeError(
            f"auto must be one of the following types: float, int. {type(auto)} was passed instead."
        )

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
            start_, end_ = showselect(
                offs_emgfile,
                title="Select the start/end of a resting area to calculate the offset, then press enter",
            )
            offsetval = offs_emgfile["REF_SIGNAL"].iloc[start_:end_].mean()
            # We need to convert the series offsetval into float
            offs_emgfile["REF_SIGNAL"][0] = offs_emgfile["REF_SIGNAL"][0] - float(offsetval)

    else:
        # Compute and subtract the offset value.
        offsetval = offs_emgfile["REF_SIGNAL"].iloc[0:auto].mean()
        # We need to convert the series offsetval into float
        offs_emgfile["REF_SIGNAL"][0] = offs_emgfile["REF_SIGNAL"][0] - float(offsetval)

    return offs_emgfile


def get_mvif(emgfile, how="showselect"):
    """
    Measure the MViF.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile with the reference signal.
    how : str {"showselect", "all"}, default "showselect"

        ``showselect``
            Ask the user to select the area where to calculate the MViF
            with a GUI.
        ``all``
            Calculate the MViF on the entire file.

    Returns
    -------
    mvif : float
        The MViF value in the original unit of measurement.

    See also
    --------
    compute_rfd : calculate the RFD.
    remove_offset : remove the offset from the REF_SIGNAL.
    filter_refsig : low-pass filter REF_SIGNAL.

    Examples
    --------
    Load the EMG file, remove reference signal offset and get MViF value.

    >>> import openhdemg as emg
    >>> emg_refsig = emg.askopenfile(filesource="OTB_refsig")
    >>> offs_refsig = emg.remove_offset(emgfile=emg_refsig)
    >>> mvif = emg.get_mvif(emgfile=offs_refsig )
    >>> mvif
    50.72

    The process can be automated by bypassing the GUI and
    calculating the MViF of the entire file.

    >>> import openhdemg as emg
    >>> emg_refsig = emg.askopenfile(filesource="OTB_refsig")
    >>> mvif = emg.get_mvif(emgfile=emg_refsig, how="all")
    >>> print(mvif)
    50.86
    """

    if how == "all":
        mvif = emgfile["REF_SIGNAL"].max()

    elif how == "showselect":
        # Select the area to measure the MViF (maximum value)
        start_, end_ = showselect(
            emgfile, title="Select the start/end area to measure the MViF, then press enter"
        )
        mvif = emgfile["REF_SIGNAL"].iloc[start_:end_].max()
        # We need to convert the series mvif into float

    else:
        raise ValueError(f"how must be one of 'showselect' or 'all', {how} was passed instead")


    mvif = round(float(mvif), 2)

    return mvif


def compute_rfd(
    emgfile,
    ms=[50, 100, 150, 200],
    startpoint=None,
    conversion_val=0
):
    """
    Calculate the RFD.

    Rate of force development (RFD) is reported as X/Sec
    where "X" is the unit of measurement based on conversion_val.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile with the reference signal.
    ms : list, default [50, 100, 150, 200]
        Milliseconds (ms). A list containing the ranges in ms to calculate the
        RFD.
    startpoint : None or int, default None
        The starting point to calculate the RFD in samples,
        If None, the user will be requested to manually select the starting
        point.
    conversion_val : float or int, default 0
        The conversion value to multiply the original reference signal.
        I.e., if the original reference signal is in kilogram (kg) and
        conversion_val=9.81, the output will be in Newton/Sec (N/Sec).
        If conversion_val=0 (default), the results will simply be Original
        measure unit/Sec. conversion_val can be any custom int or float.

    Returns
    -------
    rfd : pd.DataFrame
        A pd.DataFrame containing the RFD at the different times.

    See also
    --------
    get_mvif : measure the MViF.
    remove_offset : remove the offset from the REF_SIGNAL.
    filter_refsig : low-pass filter REF_SIGNAL.

    Examples
    --------
    Load the EMG file, low-pass filter the reference signal and compute RFD.

    >>> import openhdemg as emg
    >>> emg_refsig = emg.askopenfile(filesource="OTB_refsig")
    >>> filteredrefsig  = emg.filter_refsig(emgfile=emg_refsig, order=4, cutoff=15)
    >>> rfd = emg.compute_rfd(emgfile=filteredrefsig, ms=[50, 100, 200], conversion_val=9.81)
    >>> rfd
            50         100        200
    0  68.34342  79.296188  41.308215

    The process can be automated by bypassing the GUI.

    >>> import openhdemg as emg
    >>> emg_refsig = emg.askopenfile(filesource="OTB_refsig")
    >>> filteredrefsig  = emg.filter_refsig(emgfile=emg_refsig, order=4, cutoff=15)
    >>> rfd = emg.compute_rfd(emgfile=filteredrefsig, ms=[50, 100, 200], startpoint=3568)
    >>> rfd
            50         100        200
    0  68.34342  79.296188  41.308215
    """

    # Check if the startpoint was passed
    if isinstance(startpoint, int):
        start_ = startpoint
    else:
        # Otherwise select the starting point for the RFD
        start_ = showselect(
            emgfile,
            title="Select the starting point for RFD, then press enter",
            nclic=1,
        )

    # Create a dict to add the RFD
    rfd_dict = dict.fromkeys(ms, None)
    # Loop through the ms list and calculate the respective rfd.
    for thisms in ms:
        ms_insamples = round((int(thisms) * emgfile["FSAMP"]) / 1000)

        n_0 = emgfile["REF_SIGNAL"].iloc[start_]
        n_next = emgfile["REF_SIGNAL"].iloc[start_ + ms_insamples]

        rfdval = (n_next - n_0) / (thisms / 1000)  # (ms/1000 to convert mSec in Sec)

        rfd_dict[thisms] = rfdval

    rfd = pd.DataFrame(rfd_dict)

    if conversion_val != 0:
        rfd = rfd * conversion_val

    return rfd

# TODO function to calculate the amplification factor and convert the ref signal
# TODO in the article discuss also the correlation between PNR and SIL since we calculate both
# Quante MUs sono sopra o sotto una specificas soglia, distribuzioni ecc...
# TODO in the GUI, allow to convert the force for a conversion factor
# TODO write extended documentation of how emgfile should be structured and why and how it
# can be expanded to fit possible new necessities
