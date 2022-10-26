""" 
This module contains functions to produce and analyse MUs anction potentials (MUAP).
"""

import pandas as pd
from openhdemg.mathtools import norm_twod_xcorr
from openhdemg.otbelectrodes import sort_rawemg
from openhdemg.plotemg import plot_muaps
from scipy import signal
import matplotlib.pyplot as plt
from functools import reduce
import numpy as np
import time
from joblib import Parallel, delayed


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

    slice = int(np.ceil(len(df_sta1.columns) / 5))

    packed_sta = {
        "col0": df_sta1.iloc[:, 0:slice],
        "col1": df_sta1.iloc[:, slice : slice * 2],
        "col2": df_sta1.iloc[:, slice * 2 : slice * 3],
        "col3": df_sta1.iloc[:, slice * 3 : slice * 4],
        "col4": df_sta1.iloc[:, slice * 4 : slice * 5],
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

    Notes
    -----
    STAs are aligned by a common lag/delay and not channel by channel because
    this might lead to misleading results (and provides better performance).
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


def tracking(
    emgfile1,
    emgfile2,
    firings=[0, 20],
    timewindow=50,
    threshold=0.8,
    matrixcode="GR08MM1305",
    orientation=180,
    exclude_belowthreshold=True,
    # filter=True, #TODO add also in docstring
    show=False,
    runparallel=True,
):
    """
    Track MUs across two different contractions.

    Parameters
    ----------
    emgfile1 : dict
        The dictionary containing the first emgfile.
    emgfile2 : dict
        The dictionary containing the second emgfile.
    firings : list, default [0, 20]
        The range of firnings to be used for the STA.
        If a MU has less firings than the range, the upper limit
        is adjusted accordingly.
    timewindow : int, default 50
        Timewindow to compute STA in milliseconds.
    threshold : float, default 0.8
        The 2-dimensional cross-correlation minimum value
        to consider two MUs to be the same. Ranges 0-1.
    matrixcode : str, default "GR08MM1305"
        The code of the matrix used.
    orientation : int, default 180
        Orientation in degree of the matrix (same as in OTBiolab).
        E.g. 180 corresponds to the matrix connection toward the user.
    exclude_belowthreshold : bool, default True
        Whether to exclude results with XCC below threshold.
    show : bool, default False
        Whether to plot ste STA of pairs of MUs with XCC above threshold.
    runparallel : bool, default True
        Whether to execute the tracking function exploiting parallel
        processing for drastic performance improvements.

    Returns
    -------
    tracking_res : pd.DataFrame
        The results of the tracking including the MU from file 1,
        MU from file 2 and the normalised cross-correlation value (XCC).

    Notes
    -----
    Parallel processing can be disabled with runparallel=False.
    This can be useful if some computers incur in execution errors.
    However, wenever working, runparallel=True is recommended to
    obtain a performance improvement of 5-10 times compared to serial
    processing.
    """

    # Get the STAs
    emgfile1_sorted = sort_rawemg(emgfile1, code=matrixcode, orientation=orientation)
    sta_emgfile1 = sta(
        emgfile1, emgfile1_sorted, firings=firings, timewindow=timewindow * 2
    )
    emgfile2_sorted = sort_rawemg(emgfile2, code=matrixcode, orientation=orientation)
    sta_emgfile2 = sta(
        emgfile2, emgfile2_sorted, firings=firings, timewindow=timewindow * 2
    )

    if not runparallel:
        # Serial implementation
        # Meausere running time
        t0 = time.time()

        # Dict to store tracking results
        res = {"MU_file1": [], "MU_file2": [], "XCC": []}

        # Loop all the MUs of file 1
        for mu_file1 in range(emgfile1["NUMBER_OF_MUS"]):
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

                    if show and normxcorr_max >= threshold:
                        title = "MUAPs from MU '{}' in file 1 and MU '{}' in file 2, XCC = {}".format(
                            int(mu_file1), int(mu_file2), round(normxcorr_max, 2)
                        )
                        plot_muaps(
                            [aligned_sta1, aligned_sta2],
                            title=title,
                            showimmediately=False,
                        )

                elif exclude_belowthreshold and normxcorr_max >= threshold:
                    res["MU_file1"].append(mu_file1)
                    res["MU_file2"].append(mu_file2)
                    res["XCC"].append(normxcorr_max)

                    if show:
                        title = "MUAPs from MU '{}' in file 1 and MU '{}' in file 2, XCC = {}".format(
                            int(mu_file1), int(mu_file2), round(normxcorr_max, 2)
                        )
                        plot_muaps(
                            [aligned_sta1, aligned_sta2],
                            title=title,
                            showimmediately=False,
                        )

        # Running time
        t1 = time.time()
        print(
            "\nTime of tracking serial processing: {} Sec\nUse runparallel=True for better performance\n".format(
                round(t1 - t0, 2)
            )
        )

        # Print the full results
        pd.set_option("display.max_rows", None)
        tracking_res = pd.DataFrame(res)
        print(tracking_res)

        if show:
            plt.show()

        return tracking_res

    else:
        # Function to run in parallel
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
        """ if filter:
            pass #TODO """

        # Print the full results
        pd.set_option("display.max_rows", None)
        convert_dict = {"MU_file1": int, "MU_file2": int, "XCC": float}
        tracking_res = tracking_res.astype(convert_dict)
        print("Tracking results:\n", tracking_res)

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
