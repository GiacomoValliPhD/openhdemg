"""
This module contains functions to produce and analyse MUs anction potentials
(MUAPs).
"""

import pandas as pd
from openhdemg.library.tools import delete_mus
from openhdemg.library.mathtools import (
    norm_twod_xcorr,
    norm_xcorr,
    find_teta,
    mle_cv_est,
)
from openhdemg.library.electrodes import sort_rawemg
from openhdemg.library.plotemg import plot_muaps, plot_muaps_for_cv
from scipy import signal
import matplotlib.pyplot as plt
from functools import reduce
import numpy as np
import time
from joblib import Parallel, delayed
import copy
import os
import warnings
import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pyperclip


def diff(sorted_rawemg):
    """
    Calculate single differential (SD) of RAW_SIGNAL on matrix rows.

    Parameters
    ----------
    sorted_rawemg : dict
        A dict containing the sorted electrodes.
        Every key of the dictionary represents a different column of the
        matrix. Rows are stored in the dict as a pd.DataFrame.
        Electrodes can be sorted with the function emg.sort_rawemg.

    Returns
    -------
    sd : dict
        A dict containing the double differential signal.
        Every key of the dictionary represents a different column of the
        matrix.
        Rows are stored in the dict as a pd.DataFrame.

    See also
    --------
    - double_diff : calculate double differential of RAW_SIGNAL on matrix rows.

    Notes
    -----
    The returned sd will contain one less matrix row.

    Examples
    --------
    Calculate single differential of a DEMUSE file with the channels already
    sorted.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="DEMUSE")
    >>> sorted_rawemg = emg.sort_rawemg(
    >>>     emgfile,
    ...     code="None",
    ...     orientation=180,
    ...     dividebycolumn=True,
    ...     n_rows=13,
    ...     n_cols=5,
    ... )
    >>> sd = emg.diff(sorted_rawemg)
    >>> sd["col0"]
                 1         2         3  ...        10        11  12
    0     -0.003052  0.005086 -0.009155 ...  0.001526  0.016785 NaN
    1     -0.008647  0.008138 -0.010173 ... -0.001017 -0.015259 NaN
    2     -0.005595  0.005595 -0.013733 ...  0.003560  0.007629 NaN
    3     -0.010681  0.007121 -0.009664 ... -0.001526 -0.015259 NaN
    4     -0.005595  0.005086 -0.011190 ...  0.001017  0.017293 NaN
    ...         ...       ...       ... ...       ...       ...  ..
    63483 -0.000509  0.007121 -0.007629 ... -0.006612  0.022380 NaN
    63484 -0.005086  0.005595 -0.004578 ... -0.005595 -0.045776 NaN
    63485 -0.004069  0.001017 -0.003560 ... -0.005086 -0.005086 NaN
    63486 -0.002035  0.006104 -0.010681 ... -0.007121  0.020345 NaN
    63487 -0.008647  0.000000 -0.010681 ... -0.011190 -0.027466 NaN

    Calculate single differential of an OTB file where the channels need to be
    sorted.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> sorted_rawemg = emg.sort_rawemg(
    ...     emgfile,
    ...     code="GR08MM1305",
    ...     orientation=180,
    ... )
    >>> sd = emg.diff(sorted_rawemg)
    """

    # Create a dict of pd.DataFrames for the single differential
    # {"col0": {}, "col1": {}, "col2": {}, "col3": {}, "col4": {}}
    sd = {col: {} for col in sorted_rawemg.keys()}

    # Loop matrix columns
    for col in sorted_rawemg.keys():
        # Loop matrix rows
        for pos, row in enumerate(sorted_rawemg[col].columns):
            if pos > 0:
                res = (
                    sorted_rawemg[col].loc[:, row - 1] - sorted_rawemg[col].loc[:, row]
                )
                sd[col][row] = res

        sd[col] = pd.DataFrame(sd[col])

    return sd


def double_diff(sorted_rawemg):
    """
    Calculate double differential (DD) of RAW_SIGNAL on matrix rows.

    Parameters
    ----------
    sorted_rawemg : dict
        A dict containing the sorted electrodes.
        Every key of the dictionary represents a different column of the
        matrix. Rows are stored in the dict as a pd.DataFrame.
        Electrodes can be sorted with the function emg.sort_rawemg.

    Returns
    -------
    dd : dict
        A dict containing the double differential signal.
        Every key of the dictionary represents a different column of the
        matrix. Rows are stored in the dict as a pd.DataFrame.

    See also
    --------
    - diff : Calculate single differential of RAW_SIGNAL on matrix rows.

    Notes
    -----
    The returned dd will contain two less matrix rows.

    Examples
    --------
    Calculate double differential of a DEMUSE file with the channels already
    sorted.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="DEMUSE")
    >>> sorted_rawemg = emg.sort_rawemg(
    >>>     emgfile,
    ...     code="None",
    ...     orientation=180,
    ...     dividebycolumn=True,
    ...     n_rows=13,
    ...     n_cols=5,
    ... )
    >>> dd = emg.double_diff(sorted_rawemg)
    >>> dd["col0"]
                 2         3         4  ...            10        11  12
    0      0.008138 -0.014242  0.012716 ...  4.577637e-03  0.015259 NaN
    1      0.016785 -0.018311  0.022380 ...  8.138018e-03 -0.014242 NaN
    2      0.011190 -0.019328  0.021362 ...  1.780192e-02  0.004069 NaN
    3      0.017802 -0.016785  0.014750 ...  1.118978e-02 -0.013733 NaN
    4      0.010681 -0.016276  0.017802 ...  4.577637e-03  0.016276 NaN
    ...         ...       ...       ... ...           ...       ...  ..
    63483  0.007629 -0.014750  0.011698 ... -4.656613e-10  0.028992 NaN
    63484  0.010681 -0.010173  0.011698 ... -2.543131e-03 -0.040181 NaN
    63485  0.005086 -0.004578  0.004069 ... -6.612142e-03  0.000000 NaN
    63486  0.008138 -0.016785  0.013733 ... -1.068115e-02  0.027466 NaN
    63487  0.008647 -0.010681  0.019836 ... -1.068115e-02 -0.016276 NaN

    Calculate single differential of an OTB file where the channels need to be
    sorted.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> sorted_rawemg = emg.sort_rawemg(
    ...     emgfile=emgfile,
    ...     code="GR08MM1305",
    ...     orientation=180,
    ...     dividebycolumn=True,
    ... )
    >>> dd = emg.double_diff(sorted_rawemg)
    """

    # Create a dict of pd.DataFrames for the double differential
    # {"col0": {}, "col1": {}, "col2": {}, "col3": {}, "col4": {}}
    dd = {col: {} for col in sorted_rawemg.keys()}

    # Loop matrix columns
    for col in sorted_rawemg.keys():
        # Loop matrix rows
        for pos, row in enumerate(sorted_rawemg[col].columns):
            if pos > 1:
                res = (
                    -sorted_rawemg[col].loc[:, row - 2]
                    + 2 * sorted_rawemg[col].loc[:, row - 1]
                    - sorted_rawemg[col].loc[:, row]
                )
                dd[col][row] = res

        dd[col] = pd.DataFrame(dd[col])

    return dd


def extract_delsys_muaps(emgfile):
    """
    Extract MUAPs obtained from Delsys decomposition.

    The extracted MUAPs will be stored in the same structure of the MUAPs
    obtained with the ``sta`` funtion.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.

    Returns
    -------
    muaps_dict : dict
        dict containing a dict of MUAPs (pd.DataFrame) for every MUs.

    See also
    --------
    - sta : Computes the spike-triggered average (STA) of every MUs.

    Notes
    -----
    The returned file can be used wherever MUAPs from spike triggered
    averaging are required.

    Examples
    --------
    Visualise the MUAPs of the first MU.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="DELSYS")
    >>> muaps = emg.extract_delsys_muaps(emgfile)
    >>> emg.plot_muaps(muaps[0])

    Visualise the MUAPs of the first 3 MUs.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="DELSYS")
    >>> muaps = emg.extract_delsys_muaps(emgfile)
    >>> emg.plot_muaps([muaps[0], muaps[1], muaps[2]])
    """

    all_muaps = emgfile["EXTRAS"]
    muaps_dict = {mu: None for mu in range(emgfile["NUMBER_OF_MUS"])}
    for mu in range(emgfile["NUMBER_OF_MUS"]):
        df = pd.DataFrame(all_muaps.filter(regex=f"MU_{mu}_CH_"))
        df.columns = range(len(df.columns))
        muaps_dict[mu] = {"col0": df}

    return muaps_dict


def sta(
    emgfile, sorted_rawemg, firings=[0, 50], timewindow=50
):
    """
    Computes the spike-triggered average (STA) of every MUs.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    sorted_rawemg : dict
        A dict containing the sorted electrodes.
        Every key of the dictionary represents a different column of the
        matrix. Rows are stored in the dict as a pd.DataFrame.
    firings : list or str {"all"}, default [0, 50]
        The range of firings to be used for the STA.
        If a MU has less firings than the range, the upper limit
        is adjusted accordingly.

        ``all``
            The STA is calculated over all the firings.
    timewindow : int, default 50
        Timewindow to compute STA in milliseconds.

    Returns
    -------
    sta_dict : dict
        dict containing a dict of STA (pd.DataFrame) for every MUs.

    See also
    --------
    - unpack_sta : build a common pd.DataFrame from the sta dict containing
        all the channels.
    - pack_sta : pack the pd.DataFrame containing STA to a dict.
    - st_muap : generate spike triggered MUs action potentials
        over the entire spike train of every MUs.

    Notes
    -----
    The returned file is called ``sta_dict`` for convention.

    Examples
    --------
    Calculate STA of all the MUs in the emgfile on the first 25 firings
    and in a 50 ms time-window.
    Access the STA of the column 0 of the first MU (number 0).

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> sorted_rawemg = emg.sort_rawemg(
    ...     emgfile=emgfile,
    ...     code="GR08MM1305",
    ...     orientation=180,
    ... )
    >>> sta = emg.sta(
    ...     emgfile=emgfile,
    ...     sorted_rawemg=sorted_rawemg,
    ...     firings=[0,25],
    ...     timewindow=50,
    ... )
    >>> sta[0]["col0"]
         0          1          2  ...        10         11         12
    0   NaN  -7.527668  -7.141111 ... -1.464846 -21.606445 -14.180500
    1   NaN -16.662600 -14.038087 ...  2.868650 -19.246420 -15.218098
    2   NaN -21.443687 -15.116375 ...  5.615236 -16.052244 -13.854978
    3   NaN -17.822264  -9.989420 ...  6.876628 -12.451175 -12.268069
    4   NaN -14.567060  -8.748373 ... -1.403812 -14.241538 -16.703283
    ..   ..        ...        ... ...       ...        ...        ...
    97  NaN  19.388836  25.166826 ... 39.591473  23.681641  19.653318
    98  NaN   8.870444  16.337074 ... 28.706865  20.548504   8.422853
    99  NaN  -1.037601   7.446290 ... 18.086752  16.276041   0.040688
    100 NaN  -2.766926   5.371094 ... 11.006674  14.261881  -0.712078
    101 NaN   3.214517   9.562176 ...  4.475910  10.742184  -0.284828

    Calculate STA of the differential signal on all the firings.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> sorted_rawemg = emg.sort_rawemg(
    ...     emgfile=emgfile,
    ...     code="GR08MM1305",
    ...     orientation=180,
    ... )
    >>> sd = emg.diff(sorted_rawemg=sorted_rawemg)
    >>> sta = emg.sta(
    ...     emgfile=emgfile,
    ...     sorted_rawemg=sd,
    ...     firings="all",
    ...     timewindow=50,
    ... )
    >>> sta[0]["col0"]
         1         2          3  ...         10         11         12
    0   NaN -0.769545  11.807394 ...   3.388641  14.423187   1.420190
    1   NaN -1.496154  11.146843 ...   4.637086  12.312718   3.408456
    2   NaN -3.263135   9.660598 ...   6.258748   9.478946   5.974706
    3   NaN -4.125159   9.257659 ...   6.532877   5.558562   7.708665
    4   NaN -4.234151   9.379863 ...   6.034157   1.506064   8.722610
    ..   ..       ...        ... ...        ...        ...        ...
    97  NaN -6.126635   1.225329 ... -10.050324   1.522576  -9.568117
    98  NaN -6.565903   0.571378 ...  -8.669765   4.643692 -10.714180
    99  NaN -6.153056  -0.105689 ...  -6.836730   7.272696 -12.623180
    100 NaN -5.452869  -0.587892 ...  -7.411412   8.504627 -14.727043
    101 NaN -4.587545  -0.855417 ... -10.549041   9.802613 -15.820260
    """

    # Compute half of the timewindow in samples
    timewindow_samples = round((timewindow / 1000) * emgfile["FSAMP"])
    halftime = round(timewindow_samples / 2)
    tottime = halftime * 2

    # Container of the STA for every MUs
    # {0: {}, 1: {}, 2: {}, 3: {}}
    sta_dict = {mu: {} for mu in range(emgfile["NUMBER_OF_MUS"])}

    # Calculate STA on sorted_rawemg for every mu and put it into sta_dict[mu]
    for mu in sta_dict.keys():
        # Check if there are firings in this MU
        tot_firings = len(emgfile["MUPULSES"][mu])
        if tot_firings == 0:
            raise ValueError(
                "Empty MU in sta(). First use delete_empty_mus()."
            )

        # Set firings if firings="all"
        if firings == "all":
            firings_ = [0, tot_firings]
        else:
            firings_ = firings

        # Get current mupulses
        thismups = emgfile["MUPULSES"][mu][firings_[0]: firings_[1]]

        # Calculate STA for each column in sorted_rawemg
        sorted_rawemg_sta = {}
        for col in sorted_rawemg.keys():
            row_dict = {}
            for row in sorted_rawemg[col].columns:
                emg_array = sorted_rawemg[col][row].to_numpy()
                # Calculate STA using NumPy vectorized operations
                sta_values = []
                for pulse in thismups:
                    ls = emg_array[pulse - halftime: pulse + halftime]
                    # Avoid incomplete muaps
                    if len(ls) == tottime:
                        sta_values.append(ls)
                row_dict[row] = np.mean(sta_values, axis=0)
            sorted_rawemg_sta[col] = pd.DataFrame(row_dict)
        sta_dict[mu] = sorted_rawemg_sta

    return sta_dict


def st_muap(emgfile, sorted_rawemg, timewindow=50):
    """
    Generate spike triggered MUAPs of every MUs.

    Generate single spike triggered (ST) MUs action potentials (MUAPs)
    over the entire spike train of every MUs.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    sorted_rawemg : dict
        A dict containing the sorted electrodes.
        Every key of the dictionary represents a different column of the
        matrix. Rows are stored in the dict as a pd.DataFrame.
    timewindow : int, default 50
        Timewindow to compute ST MUAPs in milliseconds.

    Returns
    -------
    stmuap : dict
        dict containing a dict of ST MUAPs (pd.DataFrame) for every MUs.
        The pd.DataFrames containing the ST MUAPs are organised based on matrix
        rows (dict) and matrix channels.
        For example, the ST MUAPs of the first MU (0), in the second electrode
        of the first matrix column can be accessed as stmuap[0]["col0"][1].

    See also
    --------
    - sta : computes the STA of every MUs.

    Notes
    -----
    The returned file is called ``stmuap`` for convention.

    Examples
    --------
    Calculate the MUAPs of the differential signal.
    Access the MUAPs of the first MU (number 0), channel 15 that is contained
    in the second matrix column ("col1").

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> sorted_rawemg = emg.sort_rawemg(
    ...     emgfile=emgfile,
    ...     code="GR08MM1305",
    ...     orientation=180,
    ... )
    >>> sd = emg.diff(sorted_rawemg=sorted_rawemg)
    >>> stmuap = emg.st_muap(emgfile=emgfile, sorted_rawemg=sd, timewindow=50)
    >>> stmuap[0]["col1"][15]
               0          1          2   ...        151         152         153
    0   -14.750162 -26.957193   6.103516 ...  23.905434    4.069008  150.553375
    1    -9.155273 -22.379557  12.715660 ...   8.138023    0.000000  133.260086
    2    -4.069010 -12.207031  17.293289 ...  -6.612144    6.612141   74.768066
    3     1.525879  -6.612143  22.379562 ... -25.939949   21.362305  -14.750168
    4     3.051758  -4.577637  24.414062 ... -35.603844   34.586590  -83.923347
    ..         ...        ...        ... ...        ...         ...         ...
    97    9.155273 -24.922688  43.233238 ... -92.569984 -107.320145  -40.181477
    98   -2.543133 -14.241535  28.483074 ...-102.233887  -68.155922  -19.836430
    99  -23.905437 -13.732906  15.767414 ... -89.518234  -42.215984  -10.681152
    100 -52.388512 -20.853680  14.241537 ... -71.716309  -26.448566    0.000000
    101 -61.543785 -16.784668  21.362305 ... -52.388504   -3.560385    6.103516
    """

    # Compute half of the timewindow in samples
    timewindow_samples = round((timewindow / 1000) * emgfile["FSAMP"])
    halftime = round(timewindow_samples / 2)
    tottime = halftime * 2

    # Container of the ST for every MUs
    # {0: {}, 1: {}, 2: {}, 3: {} ...}
    sta_dict = {mu: {} for mu in range(emgfile["NUMBER_OF_MUS"])}

    # Calculate ST on sorted_rawemg for every mu and put it into sta_dict[mu]
    for mu in sta_dict.keys():
        # Check if there are firings in this MU
        tot_firings = len(emgfile["MUPULSES"][mu])
        if tot_firings == 0:
            raise ValueError(
                "Empty MU in sta(). First use delete_empty_mus()."
            )

        # Container for the st of each MUs' matrix column.
        sta_dict_cols = {}
        # Get MUPULSES for this MU
        thismups = emgfile["MUPULSES"][mu]
        # Calculate ST for each channel in each column in sorted_rawemg
        for col in sorted_rawemg.keys():
            # Container for the st of each channel (row) in that matrix column.
            sta_dict_crows = {}
            for row in sorted_rawemg[col].columns:
                this_emgsig = sorted_rawemg[col][row].to_numpy()
                # Container for the pd.DataFrame with MUAPs of each channel.
                crow_muaps = {}
                # Calculate ST using NumPy vectorized operations
                for pos, pulse in enumerate(thismups):
                    muap = this_emgsig[pulse - halftime: pulse + halftime]
                    # Avoid incomplete muaps
                    if len(muap) == tottime:
                        crow_muaps[pos] = muap
                sta_dict_crows[row] = pd.DataFrame(crow_muaps)
            sta_dict_cols[col] = sta_dict_crows
        sta_dict[mu] = sta_dict_cols

    return sta_dict


def unpack_sta(sta_mu):
    """
    Build a common pd.DataFrame from the sta_dict containing all the channels.

    Parameters
    ----------
    sta_mu : dict
        A dict containing the STA of a single MU.

    Returns
    -------
    df1 : pd.DataFrame
        A pd.DataFrame containing the STA of the MU
        (including the empty channel).
    keys : list
        The matrix columns (dict keys) of the unpacked sta.

    See also
    --------
    - sta : computes the STA of every MUs.
    - pack_sta : pack the pd.DataFrame containing STA to a dict.
    """

    # Identify the matrix columns
    keys = sta_mu.keys()

    # extract all the pd.DataFrames in a list
    dfs = [sta_mu[key] for key in keys]

    # Merge in a single pd.DataFrame
    df1 = reduce(
        lambda left,
        right: pd.merge(left, right, left_index=True, right_index=True),
        dfs,
    )

    return df1, list(keys)


def pack_sta(df_sta, keys):
    """
    Pack the pd.DataFrame containing STA to a dict.

    Parameters
    ----------
    df_sta : A pd.DataFrame containing the STA of a single MU
        (including the empty channel).
    keys : list
        The matrix columns (dict keys) by which to pack the sta.

    Returns
    -------
    packed_sta : dict
        dict containing STA of the input pd.DataFrame divided by matrix column.
        Dict columns are "col0", col1", "col2", "col3", "col4".

    See also
    --------
    - sta : computes the STA of every MUs.
    - unpack_sta : build a common pd.DataFrame from the sta dict containing
        all the channels.
    """

    # Detect the number of columns per pd.DataFrame (matrix columns)
    slice = int(np.ceil(len(df_sta.columns) / len(keys)))

    # Pack the sta accordingly
    packed_sta = {
        k: df_sta.iloc[:, slice*p:slice*(p+1)] for p, k in enumerate(keys)
    }

    # packed_sta = {
    #     "col0": df_sta.iloc[:, 0:slice],
    #     "col1": df_sta.iloc[:, slice:slice * 2],
    #     "col2": df_sta.iloc[:, slice * 2: slice * 3],
    #     "col3": df_sta.iloc[:, slice * 3: slice * 4],
    #     "col4": df_sta.iloc[:, slice * 4: slice * 5],
    # }

    return packed_sta


def align_by_xcorr(sta_mu1, sta_mu2, finalduration=0.5):
    """
    Align the STA of 2 MUs by cross-correlation.

    Any pre-processing of the RAW_SIGNAL
    (i.e., normal, differential or double differential)
    can be passed as long as the two inputs have same shape.
    Since the returned STA is cut based on finalduration,
    the input STA should account for this.

    Parameters
    ----------
    sta_mu1 : dict
        A dictionary containing the STA of the first MU.
    sta_mu2 : dict
        A dictionary containing the STA of the second MU.
    finalduration : float, default 0.5
        Duration of the aligned STA compared to the original
        in percent. (e.g., 0.5 corresponds to 50%).

    Returns
    -------
    aligned_sta1 : dict
        A dictionary containing the aligned STA of the first MU with the final
        expected timewindow (duration of sta_mu * finalduration).
    aligned_sta2 : dict
        A dictionary containing the aligned STA of the second MU with the
        final expected timewindow (duration of sta_mu * finalduration).

    See also
    --------
    - sta : computes the STA of every MUs.
    - norm_twod_xcorr : normalised 2-dimensional cross-correlation of STAs of
        two MUs.

    Notes
    -----
    STAs are aligned by a common lag/delay for the entire matrix and not
    channel by channel because this might lead to misleading results.

    Examples
    --------
    Align two MUs with a final duration of 50% the original one.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> sorted_rawemg = emg.sort_rawemg(
    ...     emgfile=emgfile,
    ...     code="GR08MM1305",
    ...     orientation=180,
    ... )
    >>> sta = emg.sta(
    ...     emgfile=emgfile,
    ...     sorted_rawemg=sorted_rawemg,
    ...     timewindow=100,
    ... )
    >>> aligned_sta1, aligned_sta2 = emg.align_by_xcorr(
    ...     sta_mu1=sta[0], sta_mu2=sta[1], finalduration=0.5,
    ... )
    >>> aligned_sta1["col0"]
         0          1          2  ...        10         11         12
    0   NaN -10.711670  -7.008868 ... 21.809900 -33.447262 -21.545408
    1   NaN  -5.584714  -2.380372 ... 22.664387 -33.081059 -18.931072
    2   NaN  -4.262290  -1.139323 ... 23.244226 -33.020020 -17.456057
    3   NaN  -4.638671  -1.078290 ... 23.111980 -34.118645 -18.147787
    4   NaN  -7.405599  -4.018145 ... 22.888189 -35.797115 -22.247314
    ..   ..        ...        ... ...       ...        ...        ...
    97  NaN   6.764731  13.081865 ... 30.954998  39.672852  42.429604
    98  NaN   4.455567  10.467529 ... 31.311037  41.280106  44.403072
    99  NaN   0.356039   6.856283 ... 30.436195  43.701172  46.142574
    100 NaN  -2.960206   4.872639 ... 30.008953  44.342041  46.366371
    101 NaN  -7.008870   1.708984 ... 25.634764  40.100101  43.009445
    """

    # Obtain a pd.DataFrame for the 2d xcorr without empty column
    # but mantain the original pd.DataFrame with empty column to return the
    # aligned STAs.
    df1, d_keys = unpack_sta(sta_mu1)
    no_nan_sta1 = df1.dropna(axis=1, inplace=False)
    df2, d_keys = unpack_sta(sta_mu2)
    no_nan_sta2 = df2.dropna(axis=1, inplace=False)

    # Compute 2dxcorr to identify a common lag/delay
    normxcorr_df, normxcorr_max = norm_twod_xcorr(
        no_nan_sta1, no_nan_sta2, mode="same"
    )

    # Detect the time leads or lags from 2dxcorr
    corr_lags = signal.correlation_lags(
        len(no_nan_sta1.index), len(no_nan_sta2.index), mode="same"
    )
    normxcorr_df = normxcorr_df.set_index(corr_lags)
    lag = normxcorr_df.idxmax().median()  # First signal compared to second

    # Be sure that the lag/delay does not exceed values suitable for the final
    # expected duration.
    finalduration_samples = round(len(df1.index) * finalduration)
    if lag > (finalduration_samples / 2):
        lag = finalduration_samples / 2

    # Align the signals
    dfmin = normxcorr_df.index.min()
    dfmax = normxcorr_df.index.max()

    start1 = dfmin + abs(lag) if lag > 0 else dfmin
    stop1 = dfmax if lag > 0 else dfmax - abs(lag)

    start2 = dfmin + abs(lag) if lag < 0 else dfmin
    stop2 = dfmax if lag < 0 else dfmax - abs(lag)

    df1cut = df1.set_index(corr_lags).loc[start1:stop1, :]
    df2cut = df2.set_index(corr_lags).loc[start2:stop2, :]

    # Cut the signal to respect the final duration
    tocutstart = round((len(df1cut.index) - finalduration_samples) / 2)
    tocutend = round(len(df1cut.index) - tocutstart)

    df1cut = df1cut.iloc[tocutstart:tocutend, :]
    df2cut = df2cut.iloc[tocutstart:tocutend, :]

    # Reset index to have a common index
    df1cut.reset_index(drop=True, inplace=True)
    df2cut.reset_index(drop=True, inplace=True)

    # Convert the STA to the original dict structure
    aligned_sta1 = pack_sta(df1cut, d_keys)
    aligned_sta2 = pack_sta(df2cut, d_keys)

    return aligned_sta1, aligned_sta2


# TODO update examples for code="None"

# This function exploits parallel processing:
#   - align and xcorr are processed in parallel
#   - plotting is processed in parallel
def tracking(
    emgfile1,
    emgfile2,
    firings="all",
    derivation="sd",
    timewindow=50,
    threshold=0.8,
    matrixcode="GR08MM1305",
    orientation=180,
    n_rows=None,
    n_cols=None,
    custom_sorting_order=None,
    custom_muaps=None,
    exclude_belowthreshold=True,
    filter=True,
    show=False,
):
    """
    Track MUs across two files comparing the MUAPs' shape and distribution.

    Parameters
    ----------
    emgfile1 : dict
        The dictionary containing the first emgfile.
    emgfile2 : dict
        The dictionary containing the second emgfile.
    firings : list or str {"all"}, default "all"
        The range of firings to be used for the STA.
        If a MU has less firings than the range, the upper limit
        is adjusted accordingly.
        ``all``
            The STA is calculated over all the firings.
        A list can be passed as [start, stop] e.g., [0, 25]
        to compute the STA on the first 25 firings.
    derivation : str {mono, sd, dd}, default sd
        Whether to compute the sta on the monopolar signal, or on the single or
        double differential derivation.
    timewindow : int, default 50
        Timewindow to compute STA in milliseconds.
    threshold : float, default 0.8
        The 2-dimensional cross-correlation minimum value
        to consider two MUs to be the same. Ranges 0-1.
    matrixcode : str, default "GR08MM1305"
        The code of the matrix used. It can be one of:

        ``GR08MM1305``
        ``GR04MM1305``
        ``GR10MM0808``
        ``Custom order``
        ``None``
        This is necessary to sort the channels in the correct order.
        If matrixcode="None", the electrodes are not sorted.
        In this case, n_rows and n_cols must be specified.
        If "Custom order", the electrodes are sorted based on
        custom_sorting_order.
    orientation : int {0, 180}, default 180
        Orientation in degree of the matrix (same as in OTBiolab).
        E.g. 180 corresponds to the matrix connection toward the user.
        This Parameter is ignored if code=="Custom order" or code=="None".
    n_rows : None or int, default None
        The number of rows of the matrix. This parameter is used to divide the
        channels based on the matrix shape. These are normally inferred by the
        matrix code and must be specified only if code == None.
    n_cols : None or int, default None
        The number of columns of the matrix. This parameter is used to divide
        the channels based on the matrix shape. These are normally inferred by
        the matrix code and must be specified only if code == None.
    custom_sorting_order : None or list, default None
        If code=="Custom order", custom_sorting_order will be used for
        channels sorting. In this case, custom_sorting_order must be a list of
        lists containing the order of the matrix channels.
        Specifically, the number of columns are defined by
        len(custom_sorting_order) while the number of rows by
        len(custom_sorting_order[0]). np.nan can be used to specify empty
        channels. Please refer to the Examples section for the structure of
        the custom sorting order.
    custom_muaps : None or list, default None
        With this parameter, it is possible to perform MUs tracking on MUAPs
        computed with custom techniques. If this parameter is None (default),
        MUs tracking is performed on the MUAPs computed via spike triggered
        averaging. Otherwise, it is possible to pass a list of 2 dictionaries
        containing the MUAPs of the MUs from 2 different files. These
        dictionaries should be structured as the output of the ``sta``
        function. If custom MUAPs are passed, all the previous parameters
        (except for ``emgfile1`` and ``emgfile2`` can be ignored).
        If custom MUAPs are provided, these are not aligned by the algorithm,
        contrary to what is done for MUAPs obtained via spike triggered
        averaging.
    exclude_belowthreshold : bool, default True
        Whether to exclude results with XCC below threshold.
    filter : bool, default True
        If true, when the same MU has a match of XCC > threshold with
        multiple MUs, only the match with the highest XCC is returned.
    show : bool, default False
        Whether to plot the STA of pairs of MUs with XCC above threshold.

    Returns
    -------
    tracking_res : pd.DataFrame
        The results of the tracking including the MU from file 1,
        MU from file 2 and the normalised cross-correlation value (XCC).

    Warns
    -----
    UserWarning
        If the number of plots to show exceeds that of available cores.

    See also
    --------
    - sta : computes the STA of every MUs.
    - norm_twod_xcorr : normalised 2-dimensional cross-correlation of STAs of
        two MUs.
    - remove_duplicates_between : remove duplicated MUs across two different
        files based on STA.

    Notes
    -----
    Parallel processing can improve performances by 5-10 times compared to
    serial processing. In this function, parallel processing has been
    implemented for the tasks involving 2-dimensional cross-correlation, and
    plotting. This might change in future releases.

    Examples
    --------
    Track MUs between two OTB files and show the filtered results.

    >>> import openhdemg.library as emg
    >>> emgfile1 = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> emgfile2 = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> tracking_res = emg.tracking(
    ...     emgfile1=emgfile1,
    ...     emgfile2=emgfile2,
    ...     firings="all",
    ...     derivation="sd",
    ...     timewindow=50,
    ...     threshold=0.8,
    ...     matrixcode="GR08MM1305",
    ...     orientation=180,
    ...     n_rows=None,
    ...     n_cols=None,
    ...     exclude_belowthreshold=True,
    ...     filter=True,
    ...     show=False,
    ... )
        MU_file1  MU_file2       XCC
    0          0         3  0.820068
    1          2         4  0.860272
    2          4         8  0.857346
    3          5         0  0.878373
    4          6         9  0.877321
    5          7         1  0.823371
    6          9        13  0.873388
    7         11         5  0.862537
    8         19        10  0.802635
    9         21        14  0.896419
    10        22        16  0.836356

    Track MUs between two files where channels are sorted with a custom order.

    >>> import openhdemg.library as emg
    >>> emgfile1 = emg.askopenfile(filesource="CUSTOMCSV")
    >>> emgfile2 = emg.askopenfile(filesource="CUSTOMCSV")
    >>> custom_sorting_order = [
    ...     [63, 62, 61, 60, 59, 58, 57, 56, 55, 54, 53, 52,     51,],
    ...     [38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49,     50,],
    ...     [37, 36, 35, 34, 33, 32, 31, 30, 29, 28, 27, 26,     25,],
    ...     [12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,     24,],
    ...     [11, 10,  9,  8,  7,  6,  5,  4,  3,  2,  1,  0, np.nan,],
    ... ]  # 13 rows and 5 columns
    >>> tracking_res = emg.tracking(
    ...     emgfile1=emgfile1,
    ...     emgfile2=emgfile2,
    ...     firings="all",
    ...     derivation="sd",
    ...     timewindow=50,
    ...     threshold=0.8,
    ...     matrixcode="Custom order",
    ...     orientation=180,
    ...     n_rows=None,
    ...     n_cols=None,
    ...     custom_sorting_order=custom_sorting_order,
    ...     exclude_belowthreshold=True,
    ...     filter=True,
    ...     show=False,
    ... )
    """

    # Obtain STAs
    if not isinstance(custom_muaps, list):
        # Sort the rawemg for the STAs
        emgfile1_sorted = sort_rawemg(
            emgfile1,
            code=matrixcode,
            orientation=orientation,
            n_rows=n_rows,
            n_cols=n_cols,
            custom_sorting_order=custom_sorting_order,
        )
        emgfile2_sorted = sort_rawemg(
            emgfile2,
            code=matrixcode,
            orientation=orientation,
            n_rows=n_rows,
            n_cols=n_cols,
            custom_sorting_order=custom_sorting_order,
        )

        # Calculate the derivation if needed
        if derivation == "mono":
            pass
        elif derivation == "sd":
            emgfile1_sorted = diff(sorted_rawemg=emgfile1_sorted)
            emgfile2_sorted = diff(sorted_rawemg=emgfile2_sorted)
        elif derivation == "dd":
            emgfile1_sorted = double_diff(sorted_rawemg=emgfile1_sorted)
            emgfile2_sorted = double_diff(sorted_rawemg=emgfile2_sorted)
        else:
            raise ValueError(
                f"derivation can be one of 'mono', 'sd', 'dd'. {derivation} was passed instead"
                )

        # Get the STAs
        sta_emgfile1 = sta(
            emgfile1,
            emgfile1_sorted,
            firings=firings,
            timewindow=timewindow * 2,
        )
        sta_emgfile2 = sta(
            emgfile2,
            emgfile2_sorted,
            firings=firings,
            timewindow=timewindow * 2,
        )

    # Obtain custom MUAPs
    else:
        if len(custom_muaps) == 2:
            sta_emgfile1 = custom_muaps[0]
            sta_emgfile2 = custom_muaps[1]
            if not isinstance(sta_emgfile1, dict):
                raise ValueError("custom_muaps[0] is not a dictionary")
            if not isinstance(sta_emgfile2, dict):
                raise ValueError("custom_muaps[1] is not a dictionary")
        else:
            raise ValueError("custom_muaps is not a list of two dictionaries")

    print("\nTracking started")

    # Tracking function to run in parallel
    def parallel(mu_file1):  # Loop all the MUs of file 1
        # Dict to fill with the 2d cross-correlation results
        res = {"MU_file1": [], "MU_file2": [], "XCC": []}

        # Compare mu_file1 against all the MUs in file2
        for mu_file2 in range(emgfile2["NUMBER_OF_MUS"]):
            # Firs, align the STAs
            if not isinstance(custom_muaps, list):
                aligned_sta1, aligned_sta2 = align_by_xcorr(
                    sta_emgfile1[mu_file1],
                    sta_emgfile2[mu_file2],
                    finalduration=0.5
                )
            else:
                aligned_sta1 = sta_emgfile1[mu_file1]
                aligned_sta2 = sta_emgfile2[mu_file2]

            # Second, compute 2d cross-correlation
            df1, _ = unpack_sta(aligned_sta1)
            df1.dropna(axis=1, inplace=True)
            df2, _ = unpack_sta(aligned_sta2)
            df2.dropna(axis=1, inplace=True)
            normxcorr_df, normxcorr_max = norm_twod_xcorr(
                df1, df2, mode="full"
            )

            # Third, fill the tracking_res
            if exclude_belowthreshold is False:
                res["MU_file1"].append(mu_file1)
                res["MU_file2"].append(mu_file2)
                res["XCC"].append(normxcorr_max)

            elif exclude_belowthreshold and normxcorr_max >= threshold:
                res["MU_file1"].append(mu_file1)
                res["MU_file2"].append(mu_file2)
                res["XCC"].append(normxcorr_max)

        return res

    # Start parallel execution
    # Measure running time
    t0 = time.time()

    res = Parallel(n_jobs=-1)(
        delayed(parallel)(mu_file1) for mu_file1 in range(emgfile1["NUMBER_OF_MUS"])
    )

    t1 = time.time()
    print(f"\nTime of tracking parallel processing: {round(t1-t0, 2)} Sec\n")

    # Convert res to pd.DataFrame
    tracking_res = []
    for pos, i in enumerate(res):
        if pos == 0:
            tracking_res = pd.DataFrame(i)
        else:
            tracking_res = pd.concat([tracking_res, pd.DataFrame(i)])
    tracking_res.reset_index(drop=True, inplace=True)

    # Filter the results
    if filter:
        # Sort file by MUs in file 1 and XCC to have first the highest XCC
        sorted_res = tracking_res.sort_values(
            by=["MU_file1", "XCC"], ascending=False
        )
        # Get unique MUs from file 1
        unique = sorted_res["MU_file1"].unique()

        res_unique = pd.DataFrame(columns=sorted_res.columns)

        # Get the combo uf unique MUs from file 1 with MUs from file 2
        for pos, mu1 in enumerate(unique):
            this_res = sorted_res[sorted_res["MU_file1"] == mu1]
            # Fill the result df with the first row (highest XCC)
            res_unique.loc[pos, :] = this_res.iloc[0, :]

        # Now repeat the task with MUs from file 2
        sorted_res = res_unique.sort_values(
            by=["MU_file2", "XCC"], ascending=False
        )
        unique = sorted_res["MU_file2"].unique()
        res_unique = pd.DataFrame(columns=sorted_res.columns)
        for pos, mu2 in enumerate(unique):
            this_res = sorted_res[sorted_res["MU_file2"] == mu2]
            res_unique.loc[pos, :] = this_res.iloc[0, :]

        tracking_res = res_unique.sort_values(by=["MU_file1"])

    # Print the full results
    pd.set_option("display.max_rows", None)
    convert_dict = {"MU_file1": int, "MU_file2": int, "XCC": float}
    tracking_res = tracking_res.astype(convert_dict)
    tracking_res.reset_index(drop=True, inplace=True)
    text = "Filtered tracking results:\n\n" if filter else "Total tracking results:\n\n"
    print(text, tracking_res, "\n")
    pd.reset_option("display.max_rows")

    # Plot the MUs pairs
    if show:
        def parallel(ind):  # Function for the parallel execution of plotting
            if tracking_res["XCC"].loc[ind] >= threshold:
                # Align STA
                if not isinstance(custom_muaps, list):
                    aligned_sta1, aligned_sta2 = align_by_xcorr(
                        sta_emgfile1[tracking_res["MU_file1"].loc[ind]],
                        sta_emgfile2[tracking_res["MU_file2"].loc[ind]],
                        finalduration=0.5,
                    )
                else:
                    aligned_sta1 = sta_emgfile1[tracking_res["MU_file1"].loc[ind]]
                    aligned_sta2 = sta_emgfile2[tracking_res["MU_file2"].loc[ind]]

                title = "MUAPs from MU '{}' in file 1 and MU '{}' in file 2, XCC = {}".format(
                    tracking_res["MU_file1"].loc[ind],
                    tracking_res["MU_file2"].loc[ind],
                    round(tracking_res["XCC"].loc[ind], 2),
                )
                plot_muaps(
                    sta_dict=[aligned_sta1, aligned_sta2],
                    title=title,
                    showimmediately=False
                )

            plt.show()

        # Check that the number of plots does not exceed the number of cores
        num_cores = os.cpu_count()
        if len(tracking_res.index) > num_cores:
            # If yes, raise a warning
            warnings.warn("\n\nThere are more plots to show than available cores\n")

        # Parallel execution of plotting
        Parallel(n_jobs=-1)(delayed(parallel)(ind) for ind in tracking_res.index)

    return tracking_res


def remove_duplicates_between(
    emgfile1,
    emgfile2,
    firings="all",
    derivation="sd",
    timewindow=50,
    threshold=0.9,
    matrixcode="GR08MM1305",
    orientation=180,
    n_rows=None,
    n_cols=None,
    custom_sorting_order=None,
    custom_muaps=None,
    filter=True,
    show=False,
    which="munumber",
):
    """
    Remove duplicated MUs across two different files based on STA.

    Parameters
    ----------
    emgfile1 : dict
        The dictionary containing the first emgfile.
    emgfile2 : dict
        The dictionary containing the second emgfile.
    firings : list or str {"all"}, default "all"
        The range of firings to be used for the STA.
        If a MU has less firings than the range, the upper limit
        is adjusted accordingly.
        ``all``
            The STA is calculated over all the firings.
        A list can be passed as [start, stop] e.g., [0, 25]
        to compute the STA on the first 25 firings.
    derivation : str {mono, sd, dd}, default sd
        Whether to compute the sta on the monopolar signal, or on the single or
        double differential derivation.
    timewindow : int, default 50
        Timewindow to compute STA in milliseconds.
    threshold : float, default 0.9
        The 2-dimensional cross-correlation minimum value
        to consider two MUs to be the same. Ranges 0-1.
    matrixcode : str, default "GR08MM1305"
        The code of the matrix used. It can be one of:

        ``GR08MM1305``
        ``GR04MM1305``
        ``GR10MM0808``
        ``Custom order``
        ``None``
        This is necessary to sort the channels in the correct order.
        If matrixcode="None", the electrodes are not sorted.
        In this case, n_rows and n_cols must be specified.
        If "Custom order", the electrodes are sorted based on
        custom_sorting_order.
    orientation : int {0, 180}, default 180
        Orientation in degree of the matrix (same as in OTBiolab).
        E.g. 180 corresponds to the matrix connection toward the user.
        This Parameter is ignored if code=="Custom order" or code=="None".
    n_rows : None or int, default None
        The number of rows of the matrix. This parameter is used to divide the
        channels based on the matrix shape. These are normally inferred by the
        matrix code and must be specified only if code == None.
    n_cols : None or int, default None
        The number of columns of the matrix. This parameter is used to divide
        the channels based on the matrix shape. These are normally inferred by
        the matrix code and must be specified only if code == None.
    custom_sorting_order : None or list, default None
        If code=="Custom order", custom_sorting_order will be used for
        channels sorting. In this case, custom_sorting_order must be a list of
        lists containing the order of the matrix channels.
        Specifically, the number of columns are defined by
        len(custom_sorting_order) while the number of rows by
        len(custom_sorting_order[0]). np.nan can be used to specify empty
        channels. Please refer to the Examples section for the structure of
        the custom sorting order.
    custom_muaps : None or list, default None
        With this parameter, it is possible to perform MUs tracking on MUAPs
        computed with custom techniques. If this parameter is None (default),
        MUs tracking is performed on the MUAPs computed via spike triggered
        averaging. Otherwise, it is possible to pass a list of 2 dictionaries
        containing the MUAPs of the MUs from 2 different files. These
        dictionaries should be structured as the output of the ``sta``
        function. If custom MUAPs are passed, all the previous parameters
        (except for ``emgfile1`` and ``emgfile2`` can be ignored).
        If custom MUAPs are provided, these are not aligned by the algorithm,
        contrary to what is done for MUAPs obtained via spike triggered
        averaging.
    filter : bool, default True
        If true, when the same MU has a match of XCC > threshold with
        multiple MUs, only the match with the highest XCC is returned.
    show : bool, default False
        Whether to plot the STA of pairs of MUs with XCC above threshold.
    which : str {"munumber", "accuracy"}, default "munumber"
        How to remove the duplicated MUs.

        ``munumber``
            Duplicated MUs are removed from the file with more MUs.
        ``accuracy``
            The MU with the lowest accuracy is removed.

    Returns
    -------
    emgfile1, emgfile2 : dict
        The original emgfiles without the duplicated MUs.
    tracking_res : pd.DataFrame
        The results of the tracking including the MU from file 1,
        MU from file 2 and the normalised cross-correlation value (XCC).

    See also
    --------
    - sta : computes the STA of every MUs.
    - norm_twod_xcorr : normalised 2-dimensional cross-correlation of STAs of
        two MUs.
    - tracking : track MUs across two different files.

    Examples
    --------
    Remove duplicated MUs between two OTB files and save the emgfiles
    without duplicates. The duplicates are removed from the file with
    more MUs.

    >>> import openhdemg.library as emg
    >>> emgfile1 = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> emgfile2 = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> emgfile1, emgfile2, tracking_res = emg.remove_duplicates_between(
    ...     emgfile1,
    ...     emgfile2,
    ...     firings="all",
    ...     derivation="mono",
    ...     timewindow=50,
    ...     threshold=0.9,
    ...     matrixcode="GR08MM1305",
    ...     orientation=180,
    ...     n_rows=None,
    ...     n_cols=None,
    ...     filter=True,
    ...     show=False,
    ...     which="munumber",
    ... )
    >>> emg.asksavefile(emgfile1)
    >>> emg.asksavefile(emgfile2)

    Remove duplicated MUs between two files where channels are sorted with a
    custom order and save the emgfiles without duplicates. Of the 2 duplicated
    MUs, the one with the lowest accuracy is removed.

    >>> import openhdemg.library as emg
    >>> emgfile1 = emg.askopenfile(filesource="CUSTOMCSV")
    >>> emgfile2 = emg.askopenfile(filesource="CUSTOMCSV")
    >>> custom_sorting_order = [
    ...     [63, 62, 61, 60, 59, 58, 57, 56, 55, 54, 53, 52,     51,],
    ...     [38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49,     50,],
    ...     [37, 36, 35, 34, 33, 32, 31, 30, 29, 28, 27, 26,     25,],
    ...     [12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,     24,],
    ...     [11, 10,  9,  8,  7,  6,  5,  4,  3,  2,  1,  0, np.nan,],
    ... ]  # 13 rows and 5 columns
    >>> emgfile1, emgfile2, tracking_res = emg.remove_duplicates_between(
    ...     emgfile1,
    ...     emgfile2,
    ...     firings="all",
    ...     derivation="sd",
    ...     timewindow=50,
    ...     threshold=0.9,
    ...     matrixcode="Custom order",
    ...     orientation=180,
    ...     n_rows=None,
    ...     n_cols=None,
    ...     custom_sorting_order=custom_sorting_order,
    ...     filter=True,
    ...     show=False,
    ...     which="accuracy",
    ... )
    >>> emg.asksavefile(emgfile1)
    >>> emg.asksavefile(emgfile2)
    """

    # Work on deepcopies
    emgfile1 = copy.deepcopy(emgfile1)
    emgfile2 = copy.deepcopy(emgfile2)

    # Get tracking results to identify duplicated MUs
    tracking_res = tracking(
        emgfile1=emgfile1,
        emgfile2=emgfile2,
        firings=firings,
        derivation=derivation,
        timewindow=timewindow,
        threshold=threshold,
        matrixcode=matrixcode,
        orientation=orientation,
        n_rows=n_rows,
        n_cols=n_cols,
        custom_sorting_order=custom_sorting_order,
        custom_muaps=custom_muaps,
        exclude_belowthreshold=True,
        filter=filter,
        show=show,
    )

    # Identify how to remove MUs
    if which == "munumber":
        if emgfile1["NUMBER_OF_MUS"] >= emgfile2["NUMBER_OF_MUS"]:
            # Remove MUs from emgfile1
            mus_to_remove = list(tracking_res["MU_file1"])
            emgfile1 = delete_mus(
                emgfile=emgfile1, munumber=mus_to_remove, if_single_mu="remove"
            )

            return emgfile1, emgfile2, tracking_res

        else:
            # Remove MUs from emgfile2
            mus_to_remove = list(tracking_res["MU_file2"])

            emgfile2 = delete_mus(
                emgfile=emgfile2, munumber=mus_to_remove, if_single_mu="remove"
            )

            return emgfile1, emgfile2, tracking_res

    elif which == "accuracy":
        # Create a list containing which MU to remove in which file based
        # on ACCURACY value.
        to_remove1 = []
        to_remove2 = []
        for i, row in tracking_res.iterrows():
            acc1 = emgfile1["ACCURACY"].loc[int(row["MU_file1"])]
            acc2 = emgfile2["ACCURACY"].loc[int(row["MU_file2"])]

            if acc1[0] <= acc2[0]:
                # This MU should be removed from emgfile1
                to_remove1.append(int(row["MU_file1"]))
            else:
                # This MU should be removed from emgfile2
                to_remove2.append(int(row["MU_file2"]))

        # Delete the MUs
        emgfile1 = delete_mus(
            emgfile=emgfile1, munumber=to_remove1, if_single_mu="remove"
        )
        emgfile2 = delete_mus(
            emgfile=emgfile2, munumber=to_remove2, if_single_mu="remove"
        )

        return emgfile1, emgfile2, tracking_res

    else:
        raise ValueError(
            f"which can be one of 'munumber' or 'accuracy'. {which} was passed instead"
        )


def xcc_sta(sta):
    """
    Cross-correlation between the STA of adjacent channels.

    Calculate the normalised cross-correlation coefficient (XCC) between the
    MUs action potential shapes on adjacent channels.
    The XCC will be calculated for all the MUs and all the pairs of electrodes.

    Parameters
    ----------
    sta : dict
        The dict containing the spike-triggered average (STA) of all the MUs
        computed with the function sta().

    Returns
    -------
    xcc_sta : dict
        A dict containing the XCC for all the pairs of channels and all the
        MUs. This dict is organised as the sta dict.

    Examples
    --------
    Calculate the XCC of adjacent channels of the double differential
    derivation as done to calculate MUs conduction velocity.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> sorted_rawemg = emg.sort_rawemg(
    ...     emgfile,
    ...     code="GR08MM1305",
    ...     orientation=180,
    ...     dividebycolumn=True
    ... )
    >>> dd = emg.double_diff(sorted_rawemg)
    >>> sta = emg.sta(
    ...     emgfile=emgfile,
    ...     sorted_rawemg=dd,
    ...     firings=[0, 50],
    ...     timewindow=50,
    ... )
    >>> xcc_sta = emg.xcc_sta(sta)
    """

    # Obtain the structure of the sta_xcc dict
    xcc_sta = copy.deepcopy(sta)

    # Access all the MUs and matrix columns
    for mu_number in sta:
        for matrix_col in sta[mu_number].keys():
            df = sta[mu_number][matrix_col]

            # Reverse matrix columns to start pairs comparison from the last
            reversed_col = list(df.columns)
            reversed_col.reverse()

            for pos, col in enumerate(reversed_col):
                if pos != len(reversed_col)-1:
                    # Use np.ndarrays for performance
                    this_c = df.loc[:, reversed_col[pos]].to_numpy()
                    next_c = df.loc[:, reversed_col[pos+1]].to_numpy()
                    xcc = norm_xcorr(sig1=this_c, sig2=next_c, out="max")
                else:
                    xcc = np.nan

                xcc_sta[mu_number][matrix_col][col] = xcc

            xcc_sta[mu_number][matrix_col] = xcc_sta[mu_number][matrix_col].drop_duplicates()

    return xcc_sta


def estimate_cv_via_mle(emgfile, signal):
    """
    Estimate signal conduction velocity via maximum likelihood estimation.

    This function can be used for the estimation of conduction velocity for 2
    or more signals. These can be either MUAPs or global EMG signals.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile from whic "signal" has been
        extracted. This is used to know IED and FSAMP.
    signal : pd.DataFrame
        A dataframe containing the signals on which to estimate CV. The signals
        should be organised in colums.

    Returns
    -------
    cv : float
        The conduction velocity value in M/s.

    See also
    --------
    - MUcv_gui : Graphical user interface for the estimation of MUs conduction
        velocity.

    Examples
    --------
    Calculate the CV for the first MU (number 0) on the channels 31, 32, 34,
    34 that are contained in the second column ("col2") of the double
    differential representation of the MUAPs. First, obtain the spike-
    triggered average of the double differential derivation.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> emgfile = emg.filter_rawemg(emgfile)
    >>> sorted_rawemg = emg.sort_rawemg(
    ...     emgfile,
    ...     code="GR08MM1305",
    ...     orientation=180,
    ...     dividebycolumn=True
    ... )
    >>> dd = emg.double_diff(sorted_rawemg=sorted_rawemg)
    >>> sta = emg.sta(
    ...     emgfile=emgfile,
    ...     sorted_rawemg=sorted_rawemg,
    ...     firings=[0,50],
    ...     timewindow=50,
    ... )

    Second, extract the channels of interest and estimate CV.

    >>> signal = sta[0]["col2"].loc[:, 31:34]
    >>> cv = estimate_cv_via_mle(emgfile=emgfile, signal=signal)
    """

    """
    sta_mu is a pandas dataframe containing the signals where to estimate CV
    sta = emg.sta(emgfile, dd)
    sta_mu = sta[0]["col2"].loc[:, 31:34]
    """
    ied = emgfile["IED"]
    fsamp = emgfile["FSAMP"]

    # Work with numpy vectorised operations for better performance
    sig = signal.to_numpy()
    sig = sig.T

    # Prepare the input 1D signals for find_teta
    if np.shape(sig)[0] > 3:
        sig1 = sig[1, :]
        sig2 = sig[2, :]
    else:
        sig1 = sig[0, :]
        sig2 = sig[1, :]

    teta = find_teta(
        sig1=sig1,
        sig2=sig2,
        ied=ied,
        fsamp=fsamp,
    )

    cv, teta = mle_cv_est(
        sig=sig,
        initial_teta=teta,
        ied=ied,
        fsamp=fsamp,
    )

    cv = abs(cv)

    return cv


class MUcv_gui():
    """
    Graphical user interface for the estimation of MUs conduction velocity.

    GUI for the estimation of MUs conduction velocity (CV) and amplitude of
    the action potentials (root mean square - RMS).

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    sorted_rawemg : dict
        A dict containing the sorted electrodes.
        Every key of the dictionary represents a different column of the
        matrix.
        Rows are stored in the dict as a pd.DataFrame.
    n_firings : list or str {"all"}, default [0, 50]
        The range of firings to be used for the STA.
        If a MU has less firings than the range, the upper limit
        is adjusted accordingly.
        ``all``
            The STA is calculated over all the firings.
    muaps_timewindow : int, default 50
        Timewindow to compute ST MUAPs in milliseconds.

    See also
    --------
    - estimate_cv_via_mle : Estimate signal conduction velocity via maximum
        likelihood estimation.

    Examples
    --------
    Call the GUI.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> emgfile = emg.filter_rawemg(emgfile)
    >>> sorted_rawemg = emg.sort_rawemg(
    ...     emgfile,
    ...     code="GR08MM1305",
    ...     orientation=180,
    ...     dividebycolumn=True
    ... )
    >>> gui = emg.MUcv_gui(
    ...     emgfile=emgfile,
    ...     sorted_rawemg=sorted_rawemg,
    ...     n_firings=[0,50],
    ...     muaps_timewindow=50
    ... )
    """

    def __init__(
        self,
        emgfile,
        sorted_rawemg,
        n_firings=[0, 50],
        muaps_timewindow=50,
        figsize=[25, 20],
    ):
        # On start, compute the necessary information
        self.emgfile = emgfile
        self.dd = double_diff(sorted_rawemg)
        self.st = sta(
            emgfile=emgfile,
            sorted_rawemg=self.dd,
            firings=n_firings,
            timewindow=muaps_timewindow,
        )
        self.sta_xcc = xcc_sta(self.st)
        self.figsize = figsize

        # After that, set up the GUI
        self.root = tk.Tk()
        self.root.title('MUs cv estimation')
        root_path = os.path.dirname(os.path.abspath(__file__))
        iconpath = os.path.join(
            root_path,
            "..",
            "gui",
            "gui_files",
            "Icon.ico"
        )
        self.root.iconbitmap(iconpath)

        # Create main frame, assign structure and minimum spacing
        self.frm = ttk.Frame(self.root, padding=15)
        # Assign grid structure
        self.frm.grid()

        # Label MU number combobox
        munumber_label = ttk.Label(self.frm, text="MU number", width=15)
        munumber_label.grid(row=0, column=0, columnspan=1, sticky=tk.W)

        # Create a combobox to change MU
        self.all_mus = list(range(emgfile["NUMBER_OF_MUS"]))

        self.selectmu_cb = ttk.Combobox(
            self.frm,
            textvariable=tk.StringVar(),
            values=self.all_mus,
            state='readonly',
            width=15,
        )
        self.selectmu_cb.grid(row=1, column=0, columnspan=1, sticky=tk.W)
        self.selectmu_cb.current(0)
        # gui_plot() takes one positional argument (self), but the bind()
        # method is passing two arguments: the event object and the function
        # itself. Use lambda to avoid the error.
        self.selectmu_cb.bind(
            '<<ComboboxSelected>>',
            lambda event: self.gui_plot(),
        )

        # Add 2 empty columns
        emp0 = ttk.Label(self.frm, text="", width=15)
        emp0.grid(row=0, column=1, columnspan=1, sticky=tk.W)
        emp1 = ttk.Label(self.frm, text="", width=15)
        emp1.grid(row=0, column=2, columnspan=1, sticky=tk.W)

        # Create the widgets to calculate CV
        # Label and combobox to select the matrix column
        col_label = ttk.Label(self.frm, text="Column", width=15)
        col_label.grid(row=0, column=3, columnspan=1, sticky=tk.W)

        self.columns = list(self.st[0].keys())

        self.col_cb = ttk.Combobox(
            self.frm,
            textvariable=tk.StringVar(),
            values=self.columns,
            state='readonly',
            width=15,
        )
        self.col_cb.grid(row=1, column=3, columnspan=1, sticky=tk.W)
        self.col_cb.current(0)

        # Label and combobox to select the matrix channels
        self.rows = list(range(len(list(self.st[0][self.columns[0]].columns))))

        start_label = ttk.Label(self.frm, text="From row", width=15)
        start_label.grid(row=0, column=4, columnspan=1, sticky=tk.W)

        self.start_cb = ttk.Combobox(
            self.frm,
            textvariable=tk.StringVar(),
            values=self.rows,
            state='readonly',
            width=15,
        )
        self.start_cb.grid(row=1, column=4, columnspan=1, sticky=tk.W)
        self.start_cb.current(0)

        self.stop_label = ttk.Label(self.frm, text="To row", width=15)
        self.stop_label.grid(row=0, column=5, columnspan=1, sticky=tk.W)

        self.stop_cb = ttk.Combobox(
            self.frm,
            textvariable=tk.StringVar(),
            values=self.rows,
            state='readonly',
            width=15,
        )
        self.stop_cb.grid(row=1, column=5, columnspan=1, sticky=tk.W)
        self.stop_cb.current(max(self.rows))

        # Button to start CV estimation
        self.ied = emgfile["IED"]
        self.fsamp = emgfile["FSAMP"]
        button_est = ttk.Button(
            self.frm,
            text="Estimate",
            command=self.compute_cv,
            width=15,
        )
        button_est.grid(row=1, column=6, columnspan=1, sticky="we")

        # Add empty column
        self.emp2 = ttk.Label(self.frm, text="", width=5)
        self.emp2.grid(row=0, column=7, columnspan=1, sticky=tk.W)

        # Add text frame to show the results (only CV and RMS)
        self.res_df = pd.DataFrame(
            data=0,
            index=self.all_mus,
            columns=["CV", "RMS", "XCC", "Column", "From_Row", "To_Row"],
        )
        self.textbox = tk.Text(self.frm, width=20)
        self.textbox.grid(row=2, column=8, sticky="ns")
        self.textbox.insert('1.0', self.res_df.loc[:, ["CV", "RMS"]].to_string())

        # Create a button to copy the dataframe to clipboard
        copy_btn = ttk.Button(
            self.frm,
            text="Copy results",
            command=self.copy_to_clipboard,
            width=20,
        )
        copy_btn.grid(row=1, column=8, columnspan=1, sticky="we")

        # Plot MU 0 while opening the GUI,
        # this will move the GUI in the background ??.
        self.gui_plot()

        # Bring back the GUI in in the foreground
        self.root.lift()

        # Start the main loop
        self.root.mainloop()

    # Define functions necessary for the GUI
    # Use empty docstrings to hide the functions from the documentation.
    def gui_plot(self):
        # Plot the MUAPs used to estimate CV.

        # Get MU number
        mu = int(self.selectmu_cb.get())

        # Get the figure
        fig = plot_muaps_for_cv(
            sta_dict=self.st[mu],
            xcc_sta_dict=self.sta_xcc[mu],
            showimmediately=False,
            figsize=self.figsize,
        )

        # Place the figure in the GUI
        canvas = FigureCanvasTkAgg(fig, master=self.frm)
        canvas.draw()
        canvas.get_tk_widget().grid(row=2, column=0, columnspan=7, sticky="we")
        plt.close()

    def copy_to_clipboard(self):
        # Copy the dataframe to clipboard in csv format.

        pyperclip.copy(self.res_df.to_csv(index=False, sep='\t'))

    # Define functions for cv estimation
    def compute_cv(self):
        # Compute conduction velocity.

        # Get the muaps of the selected columns.
        sig = self.st[int(self.selectmu_cb.get())][self.col_cb.get()]
        col_list = list(range(int(self.start_cb.get()), int(self.stop_cb.get())+1))

        sig = sig.iloc[:, col_list]

        # Verify that the signal is correcly oriented
        if len(sig) < len(sig.columns):
            raise ValueError(
                "The number of signals exceeds the number of samples. Verify that each row represents a signal"
            )

        # Estimate CV
        cv = estimate_cv_via_mle(emgfile=self.emgfile, signal=sig)

        # Calculate RMS
        sig = sig.to_numpy()
        rms = np.mean(np.sqrt((np.mean(sig**2, axis=0))))

        # Update the self.res_df and the self.textbox
        mu = int(self.selectmu_cb.get())

        self.res_df.loc[mu, "CV"] = cv
        self.res_df.loc[mu, "RMS"] = rms

        xcc_col_list = list(range(int(self.start_cb.get())+1, int(self.stop_cb.get())+1))
        xcc = self.sta_xcc[mu][self.col_cb.get()].iloc[:, xcc_col_list].mean().mean()
        self.res_df.loc[mu, "XCC"] = xcc

        self.res_df.loc[mu, "Column"] = self.col_cb.get()
        self.res_df.loc[mu, "From_Row"] = self.start_cb.get()
        self.res_df.loc[mu, "To_Row"] = self.stop_cb.get()

        self.textbox.replace(
            '1.0',
            'end',
            self.res_df.loc[:, ["CV", "RMS"]].round(3).to_string(),
        )
