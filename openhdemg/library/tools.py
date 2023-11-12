"""
This module contains the functions that don't properly apply to the plot
or analysis category but that are necessary for the usability of the library.
The functions contained in this module can be considered as "tools" or
shortcuts necessary to operate with the HD-EMG recordings.
"""

import copy
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
import warnings
from openhdemg.library.mathtools import compute_sil


def showselect(emgfile, title="", titlesize=12, nclic=2):
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
    titlesize : int, default 12
        The font size of the title.
    nclic: int, default 2
        The number of clics to be collected. If nclic < 1, all the clicks are
        collected.

    Returns
    -------
    points : list
        A list containing the selected points sorted in ascending order.

    Raises
    ------
    ValueError
        When the user clicked a wrong number of inputs in the GUI.

    Examples
    --------
    Load the EMG file and select the points.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="OTB_REFSIG")
    >>> points = emg.showselect(
    ...     emgfile,
    ...     title="Select 2 points",
    ...     nclic=2,
    ... )
    >>> points
    [16115, 40473]
    """
    # Show the signal for the selection
    plt.figure(num="Fig_ginput")
    plt.plot(emgfile["REF_SIGNAL"][0])
    plt.xlabel("Samples")
    plt.ylabel("MVC")
    plt.title(title, fontweight="bold", fontsize=titlesize)

    ginput_res = plt.ginput(n=-1, timeout=0, mouse_add=False, show_clicks=True)

    plt.close()

    points = [round(point[0]) for point in ginput_res]
    points.sort()

    if nclic > 0 and nclic != len(points):
        raise ValueError("Wrong number of inputs, read the title")

    return points


def create_binary_firings(emg_length, number_of_mus, mupulses):
    """
    Create a binary representation of the MU firing.

    Create a binary representation of the MU firing over time
    based on the times of firing of each MU.

    Parameters
    ----------
    emg_length : int
        Number of samples (length) in the emg file.
    number_of_mus : int
        Number of MUs in the emg file.
    mupulses : list of ndarrays
        Each ndarray should contain the times of firing (in samples) of each
        MU.

    Returns
    -------
    binary_MUs_firing : pd.DataFrame
        A pd.DataFrame containing the binary representation of MUs firing.
    """

    # Skip the step if I don't have the mupulses (is nan)
    if not isinstance(mupulses, list):
        raise ValueError("mupulses is not a list of ndarrays")

    # Initialize a pd.DataFrame with zeros
    binary_MUs_firing = pd.DataFrame(
        np.zeros((emg_length, number_of_mus), dtype=int)
    )

    for mu in range(number_of_mus):
        if len(mupulses[mu]) > 0:
            firing_points = mupulses[mu].astype(int)
            binary_MUs_firing.iloc[firing_points, mu] = 1

    return binary_MUs_firing


def mupulses_from_binary(binarymusfiring):
    """
    Extract the MUPULSES from the binary MUs firings.

    Parameters
    ----------
    binarymusfiring : pd.DataFrame
        A pd.DataFrame containing the binary representation of MUs firings.

    Returns
    -------
    MUPULSES : list
        A list of ndarrays containing the firing time (in samples) of each MU.
    """

    # Create empty list of lists to fill with ndarrays containing the MUPULSES
    # (point of firing)
    numberofMUs = len(binarymusfiring.columns)
    MUPULSES = [[] for _ in range(numberofMUs)]

    for mu in binarymusfiring:  # Loop all the MUs
        my_ndarray = []
        for idx, x in binarymusfiring[mu].items():  # Loop the MU firing times
            if x > 0:
                my_ndarray.append(idx)
                # Take the firing time and add it to the ndarray

        MUPULSES[mu] = np.array(my_ndarray)

    return MUPULSES


def resize_emgfile(emgfile, area=None, accuracy="recalculate"):
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
    accuracy : str {"recalculate", "maintain"}, default "recalculate"
        ``recalculate``
            The Silhouette score is computed in the new resized file. This can
            be done only if IPTS is present.
        ``maintain``
            The original accuracy measure already contained in the emgfile is
            returned without any computation.

    Returns
    -------
    rs_emgfile : dict
        the new (resized) emgfile.
    start_, end_ : int
        the start and end of the selection (can be used for code automation).

    Notes
    -----
    Suggested names for the returned objects: rs_emgfile, start_, end_.
    """

    # Identify the area of interest
    if isinstance(area, list) and len(area) == 2:
        start_ = area[0]
        end_ = area[1]

    else:
        # Visualise and select the area to resize
        points = showselect(
            emgfile,
            title="Select the start/end area to resize by hovering the mouse\nand pressing the 'a'-key. Wrong points can be removed with right click.\nWhen ready, press enter.",
            titlesize=10,
        )
        start_, end_ = points[0], points[1]

    # Create the object to store the resized emgfile.
    rs_emgfile = copy.deepcopy(emgfile)
    """
    ACCURACY should be re-computed on the new portion of the file if possible.
    Need to be resized: ==>
    emgfile =   {
                "SOURCE": SOURCE,
                ==> "RAW_SIGNAL": RAW_SIGNAL,
                ==> "REF_SIGNAL": REF_SIGNAL,
                ==> "ACCURACY": ACCURACY,
                ==> "IPTS": IPTS,
                ==> "MUPULSES": MUPULSES,
                "FSAMP": FSAMP,
                "IED": IED,
                ==> "EMG_LENGTH": EMG_LENGTH,
                "NUMBER_OF_MUS": NUMBER_OF_MUS,
                ==> "BINARY_MUS_FIRING": BINARY_MUS_FIRING,
                }
    """

    # Resize the reference signal and identify the first value of the index to
    # resize the mupulses. Then, reset the index.
    rs_emgfile["REF_SIGNAL"] = rs_emgfile["REF_SIGNAL"].loc[start_:end_]
    first_idx = rs_emgfile["REF_SIGNAL"].index[0]
    rs_emgfile["REF_SIGNAL"] = rs_emgfile["REF_SIGNAL"].reset_index(drop=True)
    rs_emgfile["RAW_SIGNAL"] = (
        rs_emgfile["RAW_SIGNAL"].loc[start_:end_].reset_index(drop=True)
    )
    rs_emgfile["IPTS"] = rs_emgfile["IPTS"].loc[start_:end_].reset_index(drop=True)
    rs_emgfile["EMG_LENGTH"] = int(len(rs_emgfile["IPTS"].index))
    rs_emgfile["BINARY_MUS_FIRING"] = (
        rs_emgfile["BINARY_MUS_FIRING"].loc[start_:end_].reset_index(drop=True)
    )

    for mu in range(rs_emgfile["NUMBER_OF_MUS"]):
        # Mask the array based on a filter and return the values in an array
        rs_emgfile["MUPULSES"][mu] = (
            rs_emgfile["MUPULSES"][mu][
                (rs_emgfile["MUPULSES"][mu] >= start_)
                & (rs_emgfile["MUPULSES"][mu] < end_)
            ]
            - first_idx
        )

    # Compute SIL or leave original ACCURACY
    if accuracy == "recalculate":
        if rs_emgfile["NUMBER_OF_MUS"] > 0:
            if not rs_emgfile["IPTS"].empty:
                # Calculate SIL
                to_append = []
                for mu in range(rs_emgfile["NUMBER_OF_MUS"]):
                    res = compute_sil(
                        ipts=rs_emgfile["IPTS"][mu],
                        mupulses=rs_emgfile["MUPULSES"][mu],
                    )
                    to_append.append(res)
                rs_emgfile["ACCURACY"] = pd.DataFrame(to_append)

            else:
                raise ValueError(
                    "Impossible to calculate ACCURACY (SIL). IPTS not found." +
                    " If IPTS is not present or empty, set accuracy='maintain'"
                )

    elif accuracy == "maintain":
        rs_emgfile["ACCURACY"] = rs_emgfile["ACCURACY"]

    else:
        raise ValueError(
            f"Accuracy can only be 'recalculate' or 'maintain'. {accuracy} was passed instead."
        )

    return rs_emgfile, start_, end_


def compute_idr(emgfile):
    """
    Compute the IDR.

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

            - mupulses: firing sample.
            - diff_mupulses: delta between consecutive firing samples.
            - timesec: delta between consecutive firing samples in seconds.
            - idr: instantaneous discharge rate.

    Examples
    --------
    Load the EMG file, compute IDR and access the results for the first MU.

    >>> import openhdemg.library as emg
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
        # Empty dict to fill with dataframes containing the MUPULSES
        # information
        idr = {x: np.nan**2 for x in range(emgfile["NUMBER_OF_MUS"])}

        for mu in range(emgfile["NUMBER_OF_MUS"]):
            # Manage the exception of a single MU and add MUPULSES in column 0
            df = pd.DataFrame(
                emgfile["MUPULSES"][mu]
                if emgfile["NUMBER_OF_MUS"] > 1
                else np.transpose(np.array(emgfile["MUPULSES"]))
            )

            # Calculate difference in MUPULSES and add it in column 1
            df[1] = df[0].diff()
            # Calculate time in seconds and add it in column 2
            df[2] = df[0] / emgfile["FSAMP"]
            # Calculate the idr and add it in column 3
            df[3] = emgfile["FSAMP"] / df[1]

            df = df.rename(
                columns={
                    0: "mupulses",
                    1: "diff_mupulses",
                    2: "timesec",
                    3: "idr",
                },
            )

            # Add the idr to the idr dict
            idr[mu] = df

        return idr

    else:
        raise Exception(
            "MUPULSES is probably absent or it is not contained in a list"
        )


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

    Examples
    --------
    Delete MUs 1,4,5 from the emgfile.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> emgfile = emg.delete_mus(emgfile=emgfile, munumber=[1,4,5])
    """

    # Check how to behave in case of a single MU
    if if_single_mu == "ignore":
        # Check how many MUs we have, if we only have 1 MU, the entire file
        # should be deleted instead.
        if emgfile["NUMBER_OF_MUS"] <= 1:
            warnings.warn(
                "There is only 1 MU in the file, and it has not been removed. You can change this behaviour with if_single_mu='remove'"
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
    del_emgfile = copy.deepcopy(emgfile)
    """
    Need to be changed: ==>
    emgfile =   {
                "SOURCE" : SOURCE,
                "RAW_SIGNAL" : RAW_SIGNAL,
                "REF_SIGNAL" : REF_SIGNAL,
                ==> "ACCURACY" : ACCURACY
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
    # Drop ACCURACY values and reset the index
    del_emgfile["ACCURACY"] = del_emgfile["ACCURACY"].drop(munumber)
    # .drop() Works with lists and integers
    del_emgfile["ACCURACY"] = del_emgfile["ACCURACY"].reset_index(drop=True)

    # Drop IPTS by columns and rename the columns
    del_emgfile["IPTS"] = del_emgfile["IPTS"].drop(munumber, axis=1)
    del_emgfile["IPTS"].columns = range(del_emgfile["IPTS"].shape[1])

    # Drop BINARY_MUS_FIRING by columns and rename the columns
    del_emgfile["BINARY_MUS_FIRING"] = del_emgfile["BINARY_MUS_FIRING"].drop(
        munumber, axis=1
    )
    del_emgfile["BINARY_MUS_FIRING"].columns = range(
        del_emgfile["BINARY_MUS_FIRING"].shape[1]
    )

    if isinstance(munumber, int):
        # Delete MUPULSES by position in the list.
        del del_emgfile["MUPULSES"][munumber]

        # Subrtact one MU to the total number
        del_emgfile["NUMBER_OF_MUS"] = del_emgfile["NUMBER_OF_MUS"] - 1

    elif isinstance(munumber, list):
        # Delete all the content in the del_emgfile["MUPULSES"] and append
        # only the MUs that we want to retain (exclude deleted MUs).
        # This is a workaround to directly deleting, for safer implementation.
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

    # Verify if all the MUs have been removed. In that case, restore column
    # names in empty pd.DataFrames.
    if del_emgfile["NUMBER_OF_MUS"] == 0:
        # pd.DataFrame
        del_emgfile["IPTS"] = pd.DataFrame(columns=[0])
        del_emgfile["BINARY_MUS_FIRING"] = pd.DataFrame(columns=[0])
        # list of ndarray
        del_emgfile["MUPULSES"] = [np.array([])]

    return del_emgfile


def delete_empty_mus(emgfile):
    """
    Delete all the MUs without firings.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.

    Returns
    -------
    emgfile : dict
        The dictionary containing the emgfile without the empty MUs.
    """

    # Find the index of empty MUs
    ind = []
    for i, mu in enumerate(range(emgfile["NUMBER_OF_MUS"])):
        if len(emgfile["MUPULSES"][mu]) == 0:
            ind.append(i)

    emgfile = delete_mus(emgfile, munumber=ind, if_single_mu="remove")

    return emgfile


def sort_mus(emgfile):
    """
    Sort the MUs in order of recruitment.

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
                ==> "ACCURACY": ACCURACY,
                ==> "IPTS" : IPTS,
                ==> "MUPULSES" : MUPULSES,
                "FSAMP" : FSAMP,
                "IED" : IED,
                "EMG_LENGTH" : EMG_LENGTH,
                "NUMBER_OF_MUS" : NUMBER_OF_MUS,
                ==> "BINARY_MUS_FIRING" : BINARY_MUS_FIRING,
                }
    """

    # Identify the sorting_order by the first MUpulse of every MUs
    df = []
    for mu in range(emgfile["NUMBER_OF_MUS"]):
        if len(emgfile["MUPULSES"][mu]) > 0:
            df.append(emgfile["MUPULSES"][mu][0])
        else:
            df.append(np.inf)

    df = pd.DataFrame(df, columns=["firstpulses"])
    df.sort_values(by="firstpulses", inplace=True)
    sorting_order = list(df.index)

    # Sort ACCURACY (single column)
    for origpos, newpos in enumerate(sorting_order):
        sorted_emgfile["ACCURACY"].loc[origpos] = emgfile["ACCURACY"].loc[newpos]

    # Sort IPTS (multiple columns, sort by columns, then reset columns' name)
    sorted_emgfile["IPTS"] = sorted_emgfile["IPTS"].reindex(columns=sorting_order)
    sorted_emgfile["IPTS"].columns = np.arange(emgfile["NUMBER_OF_MUS"])

    # Sort BINARY_MUS_FIRING (multiple columns, sort by columns,
    # then reset columns' name)
    sorted_emgfile["BINARY_MUS_FIRING"] = sorted_emgfile["BINARY_MUS_FIRING"].reindex(
        columns=sorting_order
    )
    sorted_emgfile["BINARY_MUS_FIRING"].columns = np.arange(emgfile["NUMBER_OF_MUS"])

    # Sort MUPULSES.
    # Preferable to use the sorting_order as a double-check in alternative to:
    # sorted_emgfile["MUPULSES"] = sorted(
    #   sorted_emgfile["MUPULSES"], key=min, reverse=False)
    # )
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
    - compute_idr : computes the instantaneous discharge rate.

    Examples
    --------
    Load the EMG file, compute covsteady and access the result from GUI.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> covsteady = emg.compute_covsteady(emgfile=emgfile)
    >>> covsteady
    1.452806

    The process can be automated by bypassing the GUI.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> covsteady = emg.compute_covsteady(
    ...     emgfile=emgfile,
    ...     start_steady=3580,
    ...     end_steady=15820,
    ... )
    >>> covsteady
    35.611263
    """

    if (start_steady < 0 and end_steady < 0) or (start_steady < 0 or end_steady < 0):
        points = showselect(
            emgfile=emgfile,
            title="Select the start/end area of the steady-state by hovering the mouse\nand pressing the 'a'-key. Wrong points can be removed with right click.\nWhen ready, press enter.",
            titlesize=10,
        )
        start_steady, end_steady = points[0], points[1]

    ref = emgfile["REF_SIGNAL"].loc[start_steady:end_steady]
    covsteady = (ref.std() / ref.mean()) * 100

    return covsteady[0]


def filter_rawemg(emgfile, order=2, lowcut=20, highcut=500):
    """
    Band-pass filter the RAW_SIGNAL.

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

    See also
    --------
    - filter_refsig : low-pass filter the REF_SIGNAL.
    """

    filteredrawsig = copy.deepcopy(emgfile)

    # Calculate the components of the filter and apply them with filtfilt to
    # obtain Zero-lag filtering. sos should be preferred over filtfilt as
    # second-order sections have fewer numerical problems.
    sos = signal.butter(
        N=order,
        Wn=[lowcut, highcut],
        btype="bandpass",
        output="sos",
        fs=filteredrawsig["FSAMP"],
    )
    for col in filteredrawsig["RAW_SIGNAL"]:
        filteredrawsig["RAW_SIGNAL"][col] = signal.sosfiltfilt(
            sos,
            x=filteredrawsig["RAW_SIGNAL"][col],
        )

    return filteredrawsig


def filter_refsig(emgfile, order=4, cutoff=15):
    """
    Low-pass filter the REF_SIGNAL.

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
    - remove_offset : remove the offset from the REF_SIGNAL.
    - filter_rawemg : band-pass filter the RAW_SIGNAL.
    """

    filteredrefsig = copy.deepcopy(emgfile)

    # Calculate the components of the filter and apply them with filtfilt to
    # obtain Zero-lag filtering. sos should be preferred over filtfilt as
    # second-order sections have fewer numerical problems.
    sos = signal.butter(
        N=order,
        Wn=cutoff,
        btype="lowpass",
        output="sos",
        fs=filteredrefsig["FSAMP"],
    )
    filteredrefsig["REF_SIGNAL"][0] = signal.sosfiltfilt(
        sos,
        x=filteredrefsig["REF_SIGNAL"][0],
    )

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
    - filter_refsig : low-pass filter REF_SIGNAL.
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

    # Act differently if automatic removal of the offset is active (>0) or not
    if auto <= 0:
        if offsetval != 0:
            # Directly subtract the offset value.
            offs_emgfile["REF_SIGNAL"][0] = offs_emgfile["REF_SIGNAL"][0] - offsetval

        else:
            # Select the area to calculate the offset
            # (average value of the selected area)
            points = showselect(
                emgfile=offs_emgfile,
                title="Select the start/end of area to calculate the offset by hovering the mouse\nand pressing the 'a'-key. Wrong points can be removed with right click.\nWhen ready, press enter.",
                titlesize=10,
            )
            start_, end_ = points[0], points[1]

            offsetval = offs_emgfile["REF_SIGNAL"].loc[start_:end_].mean()
            # We need to convert the series offsetval into float
            offs_emgfile["REF_SIGNAL"][0] = (
                offs_emgfile["REF_SIGNAL"][0] - float(offsetval[0])
            )
            print(offsetval)

    else:
        # Compute and subtract the offset value.
        offsetval = offs_emgfile["REF_SIGNAL"].iloc[0:auto].mean()
        # We need to convert the series offsetval into float
        offs_emgfile["REF_SIGNAL"][0] = (
            offs_emgfile["REF_SIGNAL"][0] - float(offsetval[0])
        )

    return offs_emgfile


def get_mvc(emgfile, how="showselect", conversion_val=0):
    """
    Measure the maximum voluntary contraction (MVC).

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile with the reference signal.
    how : str {"showselect", "all"}, default "showselect"

        ``showselect``
            Ask the user to select the area where to calculate the MVC
            with a GUI.
        ``all``
            Calculate the MVC on the entire file.
    conversion_val : float or int, default 0
        The conversion value to multiply the original reference signal.
        I.e., if the original reference signal is in kilogram (kg) and
        conversion_val=9.81, the output will be in Newton (N).
        If conversion_val=0 (default), the results will simply be in the
        original measure unit. conversion_val can be any custom int or float.

    Returns
    -------
    mvc : float
        The MVC value in the original (or converted) unit of measurement.

    See also
    --------
    - compute_rfd : calculate the RFD.
    - remove_offset : remove the offset from the REF_SIGNAL.
    - filter_refsig : low-pass filter REF_SIGNAL.

    Examples
    --------
    Load the EMG file, remove reference signal offset and get MVC value.

    >>> import openhdemg.library as emg
    >>> emg_refsig = emg.askopenfile(filesource="OTB_REFSIG")
    >>> offs_refsig = emg.remove_offset(emgfile=emg_refsig)
    >>> mvc = emg.get_mvc(emgfile=offs_refsig )
    >>> mvc
    50.72

    The process can be automated by bypassing the GUI and
    calculating the MVC of the entire file.

    >>> import openhdemg.library as emg
    >>> emg_refsig = emg.askopenfile(filesource="OTB_REFSIG")
    >>> mvc = emg.get_mvc(emgfile=emg_refsig, how="all")
    >>> print(mvc)
    50.86
    """

    if how == "all":
        mvc = emgfile["REF_SIGNAL"].max()

    elif how == "showselect":
        # Select the area to measure the MVC (maximum value)
        points = showselect(
            emgfile=emgfile,
            title="Select the start/end area to compute MVC by hovering the mouse\nand pressing the 'a'-key. Wrong points can be removed with right click.\nWhen ready, press enter.",
            titlesize=10,
        )
        start_, end_ = points[0], points[1]

        mvc = emgfile["REF_SIGNAL"].loc[start_:end_].max()

    else:
        raise ValueError(
            f"how must be one of 'showselect' or 'all', {how} was passed instead"
        )

    mvc = float(mvc[0])

    if conversion_val != 0:
        mvc = mvc * conversion_val

    return mvc


def compute_rfd(
    emgfile,
    ms=[50, 100, 150, 200],
    startpoint=None,
    conversion_val=0,
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
    - get_mvif : measure the MViF.
    - remove_offset : remove the offset from the REF_SIGNAL.
    - filter_refsig : low-pass filter REF_SIGNAL.

    Examples
    --------
    Load the EMG file, low-pass filter the reference signal and compute RFD.

    >>> import openhdemg.library as emg
    >>> emg_refsig = emg.askopenfile(filesource="OTB_REFSIG")
    >>> filteredrefsig  = emg.filter_refsig(
    ...     emgfile=emg_refsig,
    ...     order=4,
    ...     cutoff=15,
    ... )
    >>> rfd = emg.compute_rfd(
    ...     emgfile=filteredrefsig,
    ...     ms=[50, 100, 200],
    ...     conversion_val=9.81,
    ...     )
    >>> rfd
            50         100        200
    0  68.34342  79.296188  41.308215

    The process can be automated by bypassing the GUI.

    >>> import openhdemg.library as emg
    >>> emg_refsig = emg.askopenfile(filesource="OTB_REFSIG")
    >>> filteredrefsig  = emg.filter_refsig(
    ...     emgfile=emg_refsig,
    ...     order=4,
    ...     cutoff=15,
    ...     )
    >>> rfd = emg.compute_rfd(
    ...     emgfile=filteredrefsig,
    ...     ms=[50, 100, 200],
    ...     startpoint=3568,
    ...     )
    >>> rfd
            50         100        200
    0  68.34342  79.296188  41.308215
    """

    # Check if the startpoint was passed
    if isinstance(startpoint, int):
        start_ = startpoint
    else:
        # Otherwise select the starting point for the RFD
        points = showselect(
            emgfile,
            title="Select the start area to compute the RFD by hovering the mouse\nand pressing the 'a'-key. Wrong points can be removed with right click.\nWhen ready, press enter.",
            titlesize=10,
            nclic=1,
        )
        start_ = points[0]

    # Create a dict to add the RFD
    rfd_dict = dict.fromkeys(ms, None)
    # Loop through the ms list and calculate the respective rfd.
    for thisms in ms:
        ms_insamples = round((int(thisms) * emgfile["FSAMP"]) / 1000)

        n_0 = emgfile["REF_SIGNAL"].loc[start_]
        n_next = emgfile["REF_SIGNAL"].loc[start_ + ms_insamples]

        rfdval = (n_next - n_0) / (thisms / 1000)
        # (ms/1000 to convert mSec in Sec)

        rfd_dict[thisms] = rfdval

    rfd = pd.DataFrame(rfd_dict)

    if conversion_val != 0:
        rfd = rfd * conversion_val

    return rfd
