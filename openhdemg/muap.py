""" 
This module contains functions to produce MUs anction potentials (MUAP).
"""

import pandas as pd


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
        dict containing a dict of STA for every MUs.

    Notes
    -----
    The returned file is called ``sta_dict`` for convention.
    """

    # Compute half of the timewindow in samples
    timewindow_samples = round((timewindow / 1000) * emgfile["FSAMP"])
    halftime = round(timewindow_samples / 2)

    # Comtainer of the STA for every MUs
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
