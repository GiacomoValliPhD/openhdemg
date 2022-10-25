""" 
This module contains functions to produce MUs anction potentials (MUAP).
"""

import pandas as pd
from openhdemg.mathtools import norm_twod_xcorr
from scipy import signal
import matplotlib.pyplot as plt
from functools import reduce


def diff(sorted_rawemg):
    """
    Calculate single differential (SD) of RAW_SIGNAL on matrix rows.

    Parameters
    ----------
    sorted_rawemg : dict
        A dict containing the sorted electrodes.
        Every key of the dictionary represents a different column of the matrix.
        Rows are stored in the dict as a pd.DataFrame.
    
    Returns
    -------
    sd : dict
        A dict containing the double differential signal.
        Every key of the dictionary represents a different column of the matrix.
        Rows are stored in the dict as a pd.DataFrame.
    
    Notes
    -----
    The returned sd will contain one less matrix row.
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
                    sorted_rawemg[col].loc[:, row - 1]
                    - sorted_rawemg[col].loc[:, row]
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
    
    Returns
    -------
    dd : dict
        A dict containing the double differential signal.
        Every key of the dictionary represents a different column of the matrix.
        Rows are stored in the dict as a pd.DataFrame.
    
    Notes
    -----
    The returned dd will contain two less matrix rows.
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


def sta(emgfile, sorted_rawemg, firings=[0, 50], timewindow=100):
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
    firings : list, default [0, 50]
        The range of firnings to be used for the STA.
        If a MU has less firings than the range, the upper limit
        is adjusted accordingly.
    timewindow : int, default 100
        Timewindow to compute STA in milliseconds.

    Returns
    -------
    sta_dict : dict
        dict containing a dict of STA (pd.DataFrame) for every MUs.

    Notes
    -----
    The returned file is called ``sta_dict`` for convention.
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
        # Loop the matrix columns
        sorted_rawemg_sta = {}
        for col in sorted_rawemg.keys():
            # Container of STA for matrix rows
            row_dict = {}
            # Loop the matrix rows
            for row in sorted_rawemg[col].columns:
                # Find the mupulses
                thismups = emgfile["MUPULSES"][mu][firings[0] : firings[1]]
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
    Build a common pd.DataFrame from the sta dict containing all the channels

    Parameters
    ----------
    sta_mu1 : dict
        A dict containing the STA of the MU.
    
    Returns
    -------
    df1 : pd.DataFrame
        A pd.DataFrame containing the STA of the MU (including the empty channel).
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
    """
    
    packed_sta = {
            "col0":df_sta1.iloc[:,0:12],
            "col1":df_sta1.iloc[:,13:25],
            "col2":df_sta1.iloc[:,26:38],
            "col3":df_sta1.iloc[:,39:51],
            "col4":df_sta1.iloc[:,52:64]
        }
    
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
        A dictionary containing the aligned and STA of the first MU
        with the final expected timewindow (duration of sta_mu1 * finalduration).
    aligned_sta2 : dict
        A dictionary containing the aligned and STA of the second MU
        with the final expected timewindow (duration of sta_mu1 * finalduration).
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
    corr_lags = signal.correlation_lags(len(no_nan_sta1.index), len(no_nan_sta2.index), mode='same')
    normxcorr_df.set_index(corr_lags, inplace=True)
    lag = normxcorr_df.idxmax().median() # First signal compared to second

    # Be sure that the lag/delay does not exceed values suitable for the final expected duration.
    finalduration_samples = round(len(df1.index) * finalduration)
    if lag > (finalduration_samples/2):
        lag = finalduration_samples/2

    # Align the signals
    dfmin = normxcorr_df.index.min()
    dfmax = normxcorr_df.index.max()
    
    start1 = dfmin + abs(lag) if lag > 0 else dfmin
    stop1 = dfmax if lag > 0 else dfmax - abs(lag)
    
    start2 = dfmin + abs(lag) if lag < 0 else dfmin
    stop2 = dfmax if lag < 0 else dfmax - abs(lag)

    df1cut = df1.set_index(corr_lags).loc[start1:stop1 , :]
    df2cut = df2.set_index(corr_lags).loc[start2:stop2 , :]
    
    # Cut the signal to respect the final duration
    tocutstart = round((len(df1cut.index) - finalduration_samples)/2)
    tocutend = round(len(df1cut.index) - tocutstart)

    df1cut = df1cut.iloc[tocutstart:tocutend , :]
    df2cut = df2cut.iloc[tocutstart:tocutend , :]
    
    # Reset index to have a common index
    df1cut.reset_index(drop=True, inplace=True)
    df2cut.reset_index(drop=True, inplace=True)
    
    # Convert the STA to the original dict structure
    aligned_sta1 = pack_sta(df1cut)
    aligned_sta2 = pack_sta(df2cut)

    return aligned_sta1, aligned_sta2


def tracking():
    return #TODO