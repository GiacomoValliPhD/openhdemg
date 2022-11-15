""" 
This module contains functions to produce and analyse MUs anction potentials (MUAPs).
"""

import pandas as pd
from openhdemg.tools import delete_mus
from openhdemg.mathtools import norm_twod_xcorr
from openhdemg.otbelectrodes import sort_rawemg
from openhdemg.plotemg import plot_muaps
from scipy import signal
import matplotlib.pyplot as plt
from functools import reduce
import numpy as np
import time
from joblib import Parallel, delayed
import copy


def diff(sorted_rawemg):
    """
    Calculate single differential (SD) of RAW_SIGNAL on matrix rows.

    Parameters
    ----------
    sorted_rawemg : dict
        A dict containing the sorted electrodes.
        Every key of the dictionary represents a different column of the matrix.
        Rows are stored in the dict as a pd.DataFrame.
        Electrodes can be sorted with the function emg.sort_rawemg.
        DEMUSE files should be also passed to emg.sort_rawemg since
        this function, altough not sorting DEMUSE files, will still divide the 
        channels by matrix row.

    Returns
    -------
    sd : dict
        A dict containing the double differential signal.
        Every key of the dictionary represents a different column of the matrix.
        Rows are stored in the dict as a pd.DataFrame.

    See also
    --------
    double_diff : calculate double differential of RAW_SIGNAL on matrix rows.

    Notes
    -----
    The returned sd will contain one less matrix row.

    Examples
    --------
    Calculate single differential of a DEMUSE file.

    >>> import openhdemg as emg
    >>> emgfile = emg.askopenfile(filesource="DEMUSE")
    >>> sorted_rawemg = emg.sort_rawemg(emgfile)
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

    While alculating the single differential of an OTB file,
    matrix code and orientation should be also specified.

    >>> import openhdemg as emg
    >>> emgfile = emg.askopenfile(filesource="OTB")
    >>> sorted_rawemg = emg.sort_rawemg(emgfile, code="GR08MM1305", orientation=180)
    >>> sd = emg.diff(sorted_rawemg)
    """

    # Create a dict of pd.DataFrames for the single differential
    sd = {"col0": {}, "col1": {}, "col2": {}, "col3": {}, "col4": {}}

    # Loop matrix columns
    for col in sorted_rawemg.keys():
        # Loop matrix rows
        # TODO check this part for compatibility with different sorting orders
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
        Every key of the dictionary represents a different column of the matrix.
        Rows are stored in the dict as a pd.DataFrame.
        Electrodes can be sorted with the function emg.sort_rawemg.
        DEMUSE files should be also passed to emg.sort_rawemg since
        this function, altough not sorting DEMUSE files, will still divide the 
        channels by matrix row.

    Returns
    -------
    dd : dict
        A dict containing the double differential signal.
        Every key of the dictionary represents a different column of the matrix.
        Rows are stored in the dict as a pd.DataFrame.

    See also
    --------
    diff : Calculate single differential of RAW_SIGNAL on matrix rows.

    Notes
    -----
    The returned dd will contain two less matrix rows.
    
    Examples
    --------
    Calculate double differential.

    >>> import openhdemg as emg
    >>> emgfile = emg.askopenfile(filesource="DEMUSE")
    >>> sorted_rawemg = emg.sort_rawemg(emgfile)
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

    While alculating the double differential of an OTB file,
    matrix code and orientation should be also specified.

    >>> import openhdemg as emg
    >>> emgfile = emg.askopenfile(filesource="OTB")
    >>> sorted_rawemg = emg.double_diff(emgfile, code="GR08MM1305", orientation=180)
    >>> dd = emg.diff(sorted_rawemg)
    """

    # Create a dict of pd.DataFrames for the double differential
    dd = {"col0": {}, "col1": {}, "col2": {}, "col3": {}, "col4": {}}

    # Loop matrix columns
    for col in sorted_rawemg.keys():
        # Loop matrix rows
        # TODO check this part for compatibility with different sorting orders
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


def sta(
    emgfile, sorted_rawemg, firings=[0, 50], timewindow=100
):  # TODO performance improvements, parallel proc?
    """
    Computes the spike-triggered average (STA) of every MUs.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    sorted_rawemg : dict
        A dict containing the sorted electrodes.
        Every key of the dictionary represents a different column of the matrix.
        Rows are stored in the dict as a pd.DataFrame.
    firings : list or str {"all"}, default [0, 50]
        The range of firnings to be used for the STA.
        If a MU has less firings than the range, the upper limit
        is adjusted accordingly.
        ``all``
            The STA is calculated over all the firings.
    timewindow : int, default 100
        Timewindow to compute STA in milliseconds.

    Returns
    -------
    sta_dict : dict
        dict containing a dict of STA (pd.DataFrame) for every MUs.

    See also
    --------
    unpack_sta : build a common pd.DataFrame from the sta dict containing
        all the channels.
    pack_sta : pack the pd.DataFrame containing STA to a dict.
    st_muap : generate spike triggered MUs action potentials
        over the entire spike train of every MUs.

    Notes
    -----
    The returned file is called ``sta_dict`` for convention.

    Examples
    --------
    Calculate STA of all the MUs in the emgfile on the first 25 firings
    and in a 50 ms time-window.
    Access the STA of the column 0 of the first MU (number 0).
    
    >>> import openhdemg as emg
    >>> emgfile = emg.askopenfile(filesource="OTB")
    >>> sorted_rawemg = emg.sort_rawemg(emgfile, code="GR08MM1305", orientation=180)
    >>> sta = emg.sta(emgfile=emgfile, sorted_rawemg=sorted_rawemg, firings=[0,25], timewindow=50)
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

    >>> import openhdemg as emg
    >>> emgfile = emg.askopenfile(filesource="OTB")
    >>> sorted_rawemg = emg.sort_rawemg(emgfile, code="GR08MM1305", orientation=180)
    >>> sd = emg.diff(sorted_rawemg=sorted_rawemg)
    >>> sta = emg.sta(emgfile=emgfile, sorted_rawemg=sd, firings="all", timewindow=50)
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

    # Container of the STA for every MUs
    sta_dict = {}
    for mu in [*range(emgfile["NUMBER_OF_MUS"])]:
        sta_dict[mu] = {}
        """
        sta_dict
        {0: {}, 1: {}, 2: {}, 3: {}}
        """

    # Calculate STA on sorted_rawemg for every mu and put it into sta_dict[mu]
    # Loop all the MUs to fill sta_dict
    for mu in sta_dict.keys():
        # Set firings if firings="all"
        if firings == "all":
            firings_ = [0, len(emgfile["MUPULSES"][mu])]
        else:
            firings_ = firings

        # Loop the matrix columns
        sorted_rawemg_sta = {}
        for col in sorted_rawemg.keys():

            # Container of STA for matrix rows
            row_dict = {}
            # Loop the matrix rows
            for row in sorted_rawemg[col].columns:

                # Find the mupulses
                thismups = emgfile["MUPULSES"][mu][firings_[0] : firings_[1]]

                # Container of ST area for averaging
                df = {}
                for pos, pulse in enumerate(thismups):
                    df[pos] = (
                        sorted_rawemg[col][row]
                        .iloc[pulse - halftime : pulse + halftime]
                        .reset_index(drop=True)
                    )

                # Average df columns and fill df
                df = pd.DataFrame(df)
                df = df.mean(axis="columns")

                row_dict[row] = df

            sorted_rawemg_sta[col] = pd.DataFrame(row_dict)

        sta_dict[mu] = sorted_rawemg_sta

    return sta_dict


def unpack_sta(sta_mu1):
    """
    Build a common pd.DataFrame from the sta dict containing all the channels.

    Parameters
    ----------
    sta_mu1 : dict
        A dict containing the STA of the MU.

    Returns
    -------
    df1 : pd.DataFrame
        A pd.DataFrame containing the STA of the MU (including the empty channel).

    See also
    --------
    sta : computes the STA of every MUs.
    pack_sta : pack the pd.DataFrame containing STA to a dict.
    """

    dfs = [
        sta_mu1["col0"],
        sta_mu1["col1"],
        sta_mu1["col2"],
        sta_mu1["col3"],
        sta_mu1["col4"],
    ]
    df1 = reduce(
        lambda left, right: pd.merge(left, right, left_index=True, right_index=True),
        dfs,
    )

    return df1


def pack_sta(df_sta1):
    """
    Pack the pd.DataFrame containing STA to a dict.

    Parameters
    ----------
    df_sta1 : A pd.DataFrame containing the STA of the MU (including the empty channel).

    Returns
    -------
    packed_sta : dict
        dict containing STA of the input pd.DataFrame divided by matrix column.
        Dict columns are "col0", col1", "col2", "col3", "col4".
    
    See also
    --------
    sta : computes the STA of every MUs.
    unpack_sta : build a common pd.DataFrame from the sta dict containing
        all the channels.
    """

    slice = int(np.ceil(len(df_sta1.columns) / 5))

    packed_sta = {
        "col0": df_sta1.iloc[:, 0:slice],
        "col1": df_sta1.iloc[:, slice : slice * 2],
        "col2": df_sta1.iloc[:, slice * 2 : slice * 3],
        "col3": df_sta1.iloc[:, slice * 3 : slice * 4],
        "col4": df_sta1.iloc[:, slice * 4 : slice * 5],
    }

    return packed_sta

#TODO incredibly slow and must be documented well to understand how to access elements inside (this and other datasets as well)
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
        Every key of the dictionary represents a different column of the matrix.
        Rows are stored in the dict as a pd.DataFrame.
    timewindow : int, default 50
        Timewindow to compute ST MUAPs in milliseconds.

    Returns
    -------
    stmuap : dict
        dict containing a dict of ST MUAPs (pd.DataFrame) for every MUs.
        pd.DataFrames containing the ST MUAPs are organised based on matrix
        rows (dict) and matrix channel.
        For example, the ST MUAPs of the first MU (0), in the second electrode 
        of the matrix can be accessed as stmuap[0]["col0"][1].

    See also
    --------
    sta : computes the STA of every MUs.

    Notes
    -----
    The returned file is called ``stmuap`` for convention.

    Examples
    --------
    Calculate the MUAPs of the differential signal.
    Access the MUAPs of the first MU (number 0), channel 15 that is contained in
    the second matrix column ("col1").

    >>> import openhdemg as emg
    >>> emgfile = emg.askopenfile(filesource="OTB")
    >>> sorted_rawemg = emg.sort_rawemg(emgfile, code="GR08MM1305", orientation=180)
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

    # Container of the STA for every MUs
    stmuap = {}
    for mu in [*range(emgfile["NUMBER_OF_MUS"])]:
        stmuap[mu] = {}
        """
        sta_dict
        {0: {}, 1: {}, 2: {}, 3: {}}
        """

    # Calculate ST MUAPs on sorted_rawemg for every mu and put it into sta_dict[mu]
    # Loop all the MUs to fill sta_dict
    for mu in stmuap.keys():
        # Loop the matrix columns
        sorted_rawemg_st = {}
        for col in sorted_rawemg.keys():

            # Container of ST MUAPs for matrix rows
            row_dict = {}
            # Loop the matrix rows
            for row in sorted_rawemg[col].columns:

                # Find the mupulses
                thismups = emgfile["MUPULSES"][mu]

                # Container of ST area for averaging
                df = {}
                for pos, pulse in enumerate(thismups):
                    df[pos] = (
                        sorted_rawemg[col][row]
                        .iloc[pulse - halftime : pulse + halftime]
                        .reset_index(drop=True)
                    )

                # Fill df with ST MUAPs
                df = pd.DataFrame(df)

                row_dict[row] = df

            sorted_rawemg_st[col] = row_dict

        stmuap[mu] = sorted_rawemg_st

    return stmuap


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
        A dictionary containing the aligned and STA of the first MU
        with the final expected timewindow (duration of sta_mu1 * finalduration).
    aligned_sta2 : dict
        A dictionary containing the aligned and STA of the second MU
        with the final expected timewindow (duration of sta_mu1 * finalduration).

    See also
    --------
    sta : computes the STA of every MUs.
    norm_twod_xcorr : normalised 2-dimensional cross-correlation of STAs of two MUS.

    Notes
    -----
    STAs are aligned by a common lag/delay and not channel by channel because
    this might lead to misleading results (and provides better performance).

    Examples
    --------
    Align two MUs with a final duration of 50% the original one.

    >>> import openhdemg as emg
    >>> emgfile = emg.askopenfile(filesource="OTB")
    >>> sorted_rawemg = emg.sort_rawemg(emgfile, code="GR08MM1305", orientation=180)
    >>> sta = emg.sta(emgfile=emgfile, sorted_rawemg=sorted_rawemg, timewindow=100)
    >>> aligned_sta1, aligned_sta2 = emg.align_by_xcorr(
    ...     sta_mu1=sta[0], sta_mu2=sta[1], finalduration=0.5
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
    # but mantain the original pd.DataFrame with empty column to return the aligned STAs
    df1 = unpack_sta(sta_mu1)
    no_nan_sta1 = df1.dropna(axis=1, inplace=False)
    df2 = unpack_sta(sta_mu2)
    no_nan_sta2 = df2.dropna(axis=1, inplace=False)

    # Compute 2dxcorr to identify a common lag/delay
    normxcorr_df, normxcorr_max = norm_twod_xcorr(no_nan_sta1, no_nan_sta2, mode="same")

    # Detect the time leads or lags from 2dxcorr
    corr_lags = signal.correlation_lags(
        len(no_nan_sta1.index), len(no_nan_sta2.index), mode="same"
    )
    normxcorr_df.set_index(corr_lags, inplace=True)
    lag = normxcorr_df.idxmax().median()  # First signal compared to second

    # Be sure that the lag/delay does not exceed values suitable for the final expected duration.
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
    aligned_sta1 = pack_sta(df1cut)
    aligned_sta2 = pack_sta(df2cut)

    return aligned_sta1, aligned_sta2

#TODO_NEXT_ update matrixcode and orientation here and in otbelectrodes
def tracking(
    emgfile1,
    emgfile2,
    firings="all",
    timewindow=25,
    threshold=0.8,
    matrixcode="GR08MM1305",
    orientation=180,
    exclude_belowthreshold=True,
    filter=True,
    show=False,
):  # TODO check tracking function implementation and performance overall
    """
    Track MUs across two different files.

    Parameters
    ----------
    emgfile1 : dict
        The dictionary containing the first emgfile.
    emgfile2 : dict
        The dictionary containing the second emgfile.
    firings : list or str {"all"}, default "all"
        The range of firnings to be used for the STA.
        If a MU has less firings than the range, the upper limit
        is adjusted accordingly.
        ``all``
            The STA is calculated over all the firings.
        A list can be passed as [start, stop] e.g., [0, 25]
        to compute the STA on the first 25 firings.
    timewindow : int, default 25
        Timewindow to compute STA in milliseconds.
    threshold : float, default 0.8
        The 2-dimensional cross-correlation minimum value
        to consider two MUs to be the same. Ranges 0-1.
    matrixcode : str {"GR08MM1305", "GR04MM1305"}, default "GR08MM1305"
        The code of the matrix used.
    orientation : int {0, 180}, default 180
        Orientation in degree of the matrix (same as in OTBiolab).
        E.g. 180 corresponds to the matrix connection toward the user.
    exclude_belowthreshold : bool, default True
        Whether to exclude results with XCC below threshold.
    filter : bool, default True
        If true, when the same MU has a match of XCC > threshold with
        multiple MUs, only the match with the highest XCC is returned.
    show : bool, default False
        Whether to plot ste STA of pairs of MUs with XCC above threshold.

    Returns
    -------
    tracking_res : pd.DataFrame
        The results of the tracking including the MU from file 1,
        MU from file 2 and the normalised cross-correlation value (XCC).

    See also
    --------
    sta : computes the STA of every MUs.
    norm_twod_xcorr : normalised 2-dimensional cross-correlation of STAs of two MUS.
    remove_duplicates_between : remove duplicated MUs across two different files based on STA.

    Notes
    -----
    Parallel processing can improve performances by 5-10 times compared to serial
    processing. In this function, parallel processing has been implemented for the tasks
    involving 2-dimensional cross-correlation but not yet for sta and plotting that still
    constitute a bottlneck. Parallel processing of these features will be implemented
    in the next releases.

    Examples
    --------
    Track MUs between two OTB files and show the filtered results.
    If loading a DEMUSE file, matrixcode and orientation can be ignored.
     
    >>> import openhdemg as emg
    >>> emgfile1 = emg.askopenfile(filesource="OTB")
    >>> emgfile2 = emg.askopenfile(filesource="OTB")
    >>> tracking_res = emg.tracking(
    ...     emgfile1=emgfile1,
    ...     emgfile2=emgfile2,
    ...     firings="all",
    ...     timewindow=25,
    ...     threshold=0.8,
    ...     matrixcode="GR08MM1305",
    ...     orientation=180,
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
    """

    # Get the STAs
    emgfile1_sorted = sort_rawemg(emgfile1, code=matrixcode, orientation=orientation)
    t0 = time.time()
    sta_emgfile1 = sta(
        emgfile1, emgfile1_sorted, firings=firings, timewindow=timewindow * 2
    )
    t1 = time.time()
    print(f"sta time: {t1-t0}")  # TODO remove this after improving performance
    emgfile2_sorted = sort_rawemg(emgfile2, code=matrixcode, orientation=orientation)
    sta_emgfile2 = sta(
        emgfile2, emgfile2_sorted, firings=firings, timewindow=timewindow * 2
    )

    # Tracking function to run in parallel
    def parallel(mu_file1):  # Loop all the MUs of file 1
        # Dict to fill with the 2d cross-correlation results
        res = {"MU_file1": [], "MU_file2": [], "XCC": []}

        # Compare mu_file1 against all the MUs in file2
        for mu_file2 in range(emgfile2["NUMBER_OF_MUS"]):
            # Firs, align the STAs
            aligned_sta1, aligned_sta2 = align_by_xcorr(
                sta_emgfile1[mu_file1], sta_emgfile2[mu_file2], finalduration=0.5
            )

            # Second, compute 2d cross-correlation
            df1 = unpack_sta(aligned_sta1)
            df1.dropna(axis=1, inplace=True)
            df2 = unpack_sta(aligned_sta2)
            df2.dropna(axis=1, inplace=True)
            normxcorr_df, normxcorr_max = norm_twod_xcorr(df1, df2, mode="full")

            # Third, fill the tracking_res
            if exclude_belowthreshold == False:
                res["MU_file1"].append(mu_file1)
                res["MU_file2"].append(mu_file2)
                res["XCC"].append(normxcorr_max)

            elif exclude_belowthreshold and normxcorr_max >= threshold:
                res["MU_file1"].append(mu_file1)
                res["MU_file2"].append(mu_file2)
                res["XCC"].append(normxcorr_max)

        return res

    # Start parallel execution
    # Meausere running time
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
        sorted_res = tracking_res.sort_values(by=["MU_file1", "XCC"], ascending=False)
        # Get unique MUs from file 1
        unique = sorted_res["MU_file1"].unique()

        res_unique = pd.DataFrame(columns=sorted_res.columns)

        # Get the combo uf unique MUs from file 1 with MUs from file 2
        for pos, mu1 in enumerate(unique):
            this_res = sorted_res[sorted_res["MU_file1"] == mu1]
            # Fill the result df with the first row (highest XCC)
            res_unique.loc[pos, :] = this_res.iloc[0, :]

        # Now repeat the task with MUs from file 2
        sorted_res = res_unique.sort_values(by=["MU_file2", "XCC"], ascending=False)
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
    if show:  # TODO improve performance
        t0 = time.time()
        for ind in tracking_res.index:
            if tracking_res["XCC"].loc[ind] >= threshold:
                # Align STA
                aligned_sta1, aligned_sta2 = align_by_xcorr(
                    sta_emgfile1[tracking_res["MU_file1"].loc[ind]],
                    sta_emgfile2[tracking_res["MU_file2"].loc[ind]],
                    finalduration=0.5,
                )

                title = "MUAPs from MU '{}' in file 1 and MU '{}' in file 2, XCC = {}".format(
                    tracking_res["MU_file1"].loc[ind],
                    tracking_res["MU_file2"].loc[ind],
                    round(tracking_res["XCC"].loc[ind], 2),
                )
                plot_muaps(
                    [aligned_sta1, aligned_sta2], title=title, showimmediately=False
                )

        t1 = time.time()
        print(
            f"\nTime of plotting: {round(t1-t0, 2)} Sec. Will be improved in the next releases\n"
        )

        plt.show()

    return tracking_res


def remove_duplicates_between(
    emgfile1,
    emgfile2,
    firings="all",
    timewindow=25,
    threshold=0.9,
    matrixcode="GR08MM1305",
    orientation=180,
    exclude_belowthreshold=True,
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
        The range of firnings to be used for the STA.
        If a MU has less firings than the range, the upper limit
        is adjusted accordingly.
        ``all``
            The STA is calculated over all the firings.
        A list can be passed as [start, stop] e.g., [0, 25]
        to compute the STA on the first 25 firings.
    timewindow : int, default 25
        Timewindow to compute STA in milliseconds.
    threshold : float, default 0.9
        The 2-dimensional cross-correlation minimum value
        to consider two MUs to be the same. Ranges 0-1.
    matrixcode : str {"GR08MM1305", "GR04MM1305"}, default "GR08MM1305"
        The code of the matrix used.
    orientation : int {0, 180}, default 180
        Orientation in degree of the matrix (same as in OTBiolab).
        E.g. 180 corresponds to the matrix connection toward the user.
    exclude_belowthreshold : bool, default True
        Whether to exclude results with XCC below threshold.
    filter : bool, default True
        If true, when the same MU has a match of XCC > threshold with
        multiple MUs, only the match with the highest XCC is returned.
    show : bool, default False
        Whether to plot ste STA of pairs of MUs with XCC above threshold.
    which : str {"munumber", "PNR"}
        How to remove the duplicated MUs. 
        
        ``munumber``
            Duplicated MUs are removed from the file with more MUs.
        ``PNR``
            The MU with the lowest PNR is removed (valid only for DEMUSE files).
    
    Returns
    -------
    emgfile1, emgfile2 : dict
        The original emgfiles without the duplicated MUs.
    
    See also
    --------
    sta : computes the STA of every MUs.
    norm_twod_xcorr : normalised 2-dimensional cross-correlation of STAs of two MUS.
    tracking : track MUs across two different files.
    """

    # Work on deepcopies to prevent changing the original file
    emgfile1 = copy.deepcopy(emgfile1)
    emgfile2 = copy.deepcopy(emgfile2)

    # Get tracking results to identify duplicated MUs
    tracking_res = tracking(
        emgfile1,
        emgfile2,
        firings,
        timewindow,
        threshold,
        matrixcode,
        orientation,
        exclude_belowthreshold,
        filter,
        show,
    )

    # Identify how to remove MUs
    if which == "munumber":
        if emgfile1["NUMBER_OF_MUS"] >= emgfile2["NUMBER_OF_MUS"]:
            # Remove MUs from emgfile1
            mus_to_remove = list(tracking_res["MU_file1"])
            emgfile1 = delete_mus(
                emgfile=emgfile1, munumber=mus_to_remove, if_single_mu="remove"
            )

            return emgfile1, emgfile2

        else:
            # Remove MUs from emgfile2
            mus_to_remove = list(tracking_res["MU_file2"])

            emgfile2 = delete_mus(
                emgfile=emgfile2, munumber=mus_to_remove, if_single_mu="remove"
            )

            return emgfile1, emgfile2

    elif which == "PNR":
        if emgfile1["SOURCE"] == "DEMUSE" and emgfile2["SOURCE"] == "DEMUSE":
            # Create a list containing which MU to remove in which file based on PNR
            to_remove1 = []
            to_remove2 = []
            for i, row in tracking_res.iterrows():
                pnr1 = emgfile1["PNR"].loc[int(row["MU_file1"])]
                pnr2 = emgfile2["PNR"].loc[int(row["MU_file2"])]

                if pnr1[0] <= pnr2[0]:
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

            return emgfile1, emgfile2

        else:
            raise Exception(
                "To remove duplicated MUs by PNR, you should load files from DEMUSE"
            )

    else:
        pass  # TODO_NEXT_ implement with SIL as with PNR
