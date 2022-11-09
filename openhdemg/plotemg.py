"""
This module contains all the functions used to visualise the emg file,
the MUs properties or to save figures.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import copy
from openhdemg.tools import compute_idr
from openhdemg.mathtools import min_max_scaling


def showgoodlayout(tight_layout=True, despined=False):
    """
    Despine and show plots with a good layout.

    Parameters
    ----------
    tight_layout : bool, default True
        If true (default), plt.tight_layout() is applied to the figure.
    despined : bool or str {"2yaxes"}, default False
        False: left and bottom is not despined (standard plotting).
        True: all the sides are despined.
        ``2yaxes``
            Only the top is despined. 
            This is used for y axes both on the right and left side at the same time.
    """

    # Check the input
    if not isinstance(despined, (bool, str)):
        raise Exception(
            f"despined can be True, False of 2yaxes. {despined} was passed instead"
        )

    if despined == False:
        sns.despine()
    elif despined == True:
        sns.despine(top=True, bottom=True, left=True, right=True)
    elif despined == "2yaxes":
        sns.despine(top=True, bottom=False, left=False, right=False)
    else:
        raise Exception(
            f"despined can be True, False or 2yaxes. {despined} was passed instead"
        )

    if tight_layout == True:
        plt.tight_layout()


def plot_emgsig(
    emgfile,
    channels,
    addrefsig=False,
    timeinseconds=True,
    figsize=[20, 15],
    showimmediately=True,
    tight_layout=True,
):
    """
    Pot the RAW_SIGNAL. Single or multiple channels.

    Up to 12 channels can be easily observed togheter (but more can be plotted of course).

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    channels : int or list
        The channel (int) or channels (list of int) to plot.
        The list can be passed as a manually-written list or with: channels=[*range(0, 12)],
        We need the "*" operator to unpack the results of range and build a list.
        channels is expected to be with base 0 (i.e., the first channel in the file is the number 0).
    addrefsig : bool, default True
        If True, the REF_SIGNAL is plotted in front of the signal with a separated y-axes.
    timeinseconds : bool, default True
        Whether to show the time on the x-axes in seconds (True) or in samples (False).
    figsize : list, default [20, 15]
        Size of the figure in centimeters [width, height].
    showimmediately : bool, default True
        If True (default), plt.show() is called and the figure showed to the user.
        It is useful to set it to False when calling the function from the GUI.
    tight_layout : bool, default True
        If True (default), the plt.tight_layout() is called and the figure's layout is improved.
        It is useful to set it to False when calling the function from the GUI.
    """

    # Check to have the RAW_SIGNAL in a pandas dataframe
    if isinstance(emgfile["RAW_SIGNAL"], pd.DataFrame):
        emgsig = emgfile["RAW_SIGNAL"]

        # Here we produce an x axis in seconds or samples
        if timeinseconds:
            x_axis = emgsig.index / emgfile["FSAMP"]
        else:
            x_axis = emgsig.index

        figname = "Channels n.{}".format(channels)
        fig, ax1 = plt.subplots(
            figsize=(figsize[0] / 2.54, figsize[1] / 2.54),
            num=figname,
        )

        # Check if we have a single channel or a list of channels to plot
        if isinstance(channels, int):
            ax = sns.lineplot(x=x_axis, y=emgsig[channels])
            ax.set_ylabel(
                "Ch {}".format(channels)
            )  # Useful because if the channe is empty it won't show the channel number
            ax.set_xlabel("Time (s)" if timeinseconds else "Samples")

        elif isinstance(channels, list):
            # Plot all the channels in the subplots, up to 12 channels are clearly visible
            for count, thisChannel in enumerate(channels):
                # Normalise the series
                norm_raw = min_max_scaling(emgfile["RAW_SIGNAL"][thisChannel])
                # Add 1 to the previous channel to avoid overlapping
                norm_raw = norm_raw + count
                ax = sns.lineplot(x=x_axis, y=norm_raw)

            # Ensure correct and complete ticks on the left y axis
            ax1.set_yticks([*range(len(channels))])
            ax1.set_yticklabels([str(x) for x in channels])
            # Set axes labels
            ax1.set_ylabel("Channels")
            ax1.set_xlabel("Time (Sec)" if timeinseconds else "Samples")

        else:
            raise Exception(
                "While calling the plot_emgsig function, you should pass an integer, a list or 'all' to channels"
            )

        if addrefsig:
            ax2 = ax1.twinx()
            # Plot the ref signal
            xref = (
                emgfile["REF_SIGNAL"].index / emgfile["FSAMP"]
                if timeinseconds
                else emgfile["REF_SIGNAL"].index
            )
            sns.lineplot(y=emgfile["REF_SIGNAL"][0], x=xref, color="0.4", ax=ax2)
            ax2.set_ylabel("MViF (%)")

        showgoodlayout(tight_layout, despined="2yaxes" if addrefsig else False)
        if showimmediately:
            plt.show()

    else:
        raise Exception(
            "RAW_SIGNAL is probably absent or it is not contained in a dataframe"
        )


def plot_differentials(
    emgfile,
    differential,
    column="col0",
    addrefsig=False,
    timeinseconds=True,
    figsize=[20, 15],
    showimmediately=True,
    tight_layout=True,
):
    """
    Plot the differential derivation of the RAW_SIGNAL by matrix column.

    Both the single and the double differencials can be plotted.
    This function is used to plot also the sorted RAW_SIGNAL.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the original emgfile.
    differential : dict
        The dictionary containing the differential derivation of the RAW_SIGNAL.
    column : str {"col0", "col1", "col2", "col3", "col4"}, default "col0"
        The matrix column to plot.
        Options are usyally "col0", "col1", "col2", "col3", "col4".
        but might change based on the matrix used.
    addrefsig : bool, default True
        If True, the REF_SIGNAL is plotted in front of the signal with a separated y-axes.
    timeinseconds : bool, default True
        Whether to show the time on the x-axes in seconds (True) or in samples (False).
    figsize : list, default [20, 15]
        Size of the figure in centimeters [width, height].
    showimmediately : bool, default True
        If True (default), plt.show() is called and the figure showed to the user.
        It is useful to set it to False when calling the function from the GUI.
    tight_layout : bool, default True
        If True (default), the plt.tight_layout() is called and the figure's layout is improved.
        It is useful to set it to False when calling the function from the GUI.
    """

    # Check to have the RAW_SIGNAL in a pandas dataframe
    if isinstance(differential[column], pd.DataFrame):
        emgsig = differential[column]

        # Here we produce an x axis in seconds or samples
        if timeinseconds:
            x_axis = emgsig.index / emgfile["FSAMP"]
        else:
            x_axis = emgsig.index

        figname = "Column n.{}".format(column)
        fig, ax1 = plt.subplots(
            figsize=(figsize[0] / 2.54, figsize[1] / 2.54),
            num=figname,
        )

        # Plot all the channels of every column in the subplots
        for count, thisChannel in enumerate(emgsig.columns):
            # Normalise the series
            norm_raw = min_max_scaling(emgsig[thisChannel])
            # Add 1 to the previous channel to avoid overlapping
            norm_raw = norm_raw + count
            ax = sns.lineplot(x=x_axis, y=norm_raw)

        # Ensure correct and complete ticks on the left y axis
        ax1.set_yticks([*range(len(emgsig.columns))])
        ax1.set_yticklabels([str(x) for x in emgsig.columns])
        # Set axes labels
        ax1.set_ylabel("Channels")
        ax1.set_xlabel("Time (Sec)" if timeinseconds else "Samples")

        if addrefsig:
            ax2 = ax1.twinx()
            # Plot the ref signal
            xref = (
                emgfile["REF_SIGNAL"].index / emgfile["FSAMP"]
                if timeinseconds
                else emgfile["REF_SIGNAL"].index
            )
            sns.lineplot(y=emgfile["REF_SIGNAL"][0], x=xref, color="0.4", ax=ax2)
            ax2.set_ylabel("MViF (%)")

        showgoodlayout(tight_layout, despined="2yaxes" if addrefsig else False)
        if showimmediately:
            plt.show()

    else:
        raise Exception(
            "RAW_SIGNAL is probably absent or it is not contained in a dataframe"
        )


def plot_refsig(
    emgfile,
    timeinseconds=True,
    figsize=[20, 15],
    showimmediately=True,
    tight_layout=True,
):
    """
    Plot the REF_SIGNAL.

    The REF_SIGNAL is expected to be expressed as % MViF for submaximal
    contractions or as Kilograms (Kg) or Newtons (N) for maximal contractions.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    timeinseconds : bool, default True
        Whether to show the time on the x-axes in seconds (True) or in samples (False).
    figsize : list, default [20, 15]
        Size of the figure in centimeters [width, height].
    showimmediately : bool, default True
        If True (default), plt.show() is called and the figure showed to the user.
        It is useful to set it to False when calling the function from the GUI.
    tight_layout : bool, default True
        If True (default), the plt.tight_layout() is called and the figure's layout is improved.
        It is useful to set it to False when calling the function from the GUI.
    """

    # Check to have the REF_SIGNAL in a pandas dataframe
    if isinstance(emgfile["REF_SIGNAL"], pd.DataFrame):
        refsig = emgfile["REF_SIGNAL"]

        # Here we produce an x axis in seconds or samples
        if timeinseconds:
            x_axis = refsig.index / emgfile["FSAMP"]
        else:
            x_axis = refsig.index

        fig = plt.figure(
            "Reference signal", figsize=(figsize[0] / 2.54, figsize[1] / 2.54)
        )
        ax = sns.lineplot(x=x_axis, y=refsig[0])
        ax.set_ylabel("% MViF")
        ax.set_xlabel("Time (s)" if timeinseconds else "Samples")

        showgoodlayout(tight_layout)
        if showimmediately:
            plt.show()

        # TODO Needed for the GUI? To check the other plot functions and add to the returned
        return fig

    else:
        raise Exception(
            "REF_SIGNAL is probably absent or it is not contained in a dataframe"
        )


def plot_mupulses(
    emgfile,
    linewidths=0.5,
    order=False,
    addrefsig=True,
    timeinseconds=True,
    figsize=[20, 15],
    showimmediately=True,
    tight_layout=True,
):
    """
    Plot all the MUPULSES.

    MUPULSES are the binary representation of the firings.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    linewidths : float, default 0.5
        The width of the vertical lines representing the MU firing.
    order : bool, default False
        If True, MUs are sorted and plotted based on the order of recruitment.
    addrefsig : bool, default True
        If True, the REF_SIGNAL is plotted in front of the MUs pulses with a separated y-axes.
    timeinseconds : bool, default True
        Whether to show the time on the x-axes in seconds (True) or in samples (False).
    figsize : list, default [20, 15]
        Size of the figure in centimeters [width, height].
    showimmediately : bool, default True
        If True (default), plt.show() is called and the figure showed to the user.
        It is useful to set it to False when calling the function from the GUI.
    tight_layout : bool, default True
        If True (default), the plt.tight_layout() is called and the figure's layout is improved.
        It is useful to set it to False when calling the function from the GUI.
    """

    # Check to have the correct input
    if isinstance(emgfile["MUPULSES"], list):
        # Create a deepcopy to modify mupulses without affecting the original file
        mupulses = copy.deepcopy(emgfile["MUPULSES"])
    else:
        raise Exception(
            "MUPULSES is probably absent or it is not contained in a np.array"
        )

    if addrefsig:
        if not isinstance(emgfile["REF_SIGNAL"], pd.DataFrame):
            raise Exception(
                "REF_SIGNAL is probably absent or it is not contained in a dataframe"
            )

    # Convert x axes in seconds if timeinseconds==True
    # This has to be done both for the REF_SIGNAL and the mupulses, for the MUPULSES
    # we need to convert the point of firing from samples to seconds
    if timeinseconds:
        mupulses = [n / emgfile["FSAMP"] for i, n in enumerate(emgfile["MUPULSES"])]

    # Sort the MUPULSES based on order of recruitment. If True, MUPULSES are sorted in ascending order
    if order and emgfile["NUMBER_OF_MUS"] > 1:
        mupulses = sorted(mupulses, key=min, reverse=False)

    # Create colors list for the firings and plot them
    colors1 = ["C{}".format(i) for i in range(emgfile["NUMBER_OF_MUS"])]

    # Use the subplot to allow the use of twinx
    fig, ax1 = plt.subplots(
        figsize=(figsize[0] / 2.54, figsize[1] / 2.54), num="MUs pulses"
    )

    # Plot the MUPULSES.
    ax1.eventplot(
        mupulses,
        linewidths=linewidths,
        linelengths=0.9,  # Assign 90% of the space in the plot to linelengths
        lineoffsets=1,
        colors=colors1,
    )

    # Ensure correct and complete ticks on the left y axis
    ax1.set_yticks([*range(emgfile["NUMBER_OF_MUS"])])
    ax1.set_yticklabels([str(x) for x in [*range(emgfile["NUMBER_OF_MUS"])]])
    # Set axes labels
    ax1.set_ylabel("MUs")
    ax1.set_xlabel("Time (Sec)" if timeinseconds else "Samples")

    if addrefsig:
        # Create the second (right) y axes
        ax2 = ax1.twinx()

        # Plot REF_SIGNAL on the right y axes
        xref = (
            emgfile["REF_SIGNAL"].index / emgfile["FSAMP"]
            if timeinseconds
            else emgfile["REF_SIGNAL"].index
        )
        sns.lineplot(y=emgfile["REF_SIGNAL"][0], x=xref, color="0.4", ax=ax2)
        ax2.set_ylabel("MViF (%)")

    showgoodlayout(tight_layout, despined="2yaxes" if addrefsig else False)
    if showimmediately:
        plt.show()


def plot_ipts(
    emgfile,
    munumber="all",
    addrefsig=False,
    timeinseconds=True,
    figsize=[20, 15],
    showimmediately=True,
    tight_layout=True,
):
    """
    Plot the IPTS. Single or multiple MUs.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    munumber : str {"all"}, int or list, default "all"
        ``all``
            IPTS of all the MUs is plotted.
        Otherwise, a single MU (int) or multiple MUs (list of int) can be specified.
        The list can be passed as a manually-written list or with: munumber=[*range(0, 12)],
        We need the "*" operator to unpack the results of range and build a list.
        munumber is expected to be with base 0 (i.e., the first MU in the file is the number 0).
    timeinseconds : bool, default True
        Whether to show the time on the x-axes in seconds (True) or in samples (False).
    figsize : list, default [20, 15]
        Size of the figure in centimeters [width, height].
    showimmediately : bool, default True
        If True (default), plt.show() is called and the figure showed to the user.
        It is useful to set it to False when calling the function from the GUI.
    tight_layout : bool, default True
        If True (default), the plt.tight_layout() is called and the figure's layout is improved.
        It is useful to set it to False when calling the function from the GUI.

    Notes
    -----
    munumber = "all" corresponds to munumber = [*range(0, emgfile["NUMBER_OF_MUS"])]
    """

    # Check if all the MUs have to be plotted
    if isinstance(munumber, str):
        if emgfile["NUMBER_OF_MUS"] == 1:  # Manage exception of single MU
            munumber = 0
        else:
            munumber = [*range(0, emgfile["NUMBER_OF_MUS"])]

    # Check to have the IPTS in a pandas dataframe
    if isinstance(emgfile["IPTS"], pd.DataFrame):
        ipts = emgfile["IPTS"]

        # Here we produce an x axis in seconds or samples
        if timeinseconds:
            x_axis = ipts.index / emgfile["FSAMP"]
        else:
            x_axis = ipts.index

        # Use the subplot function to allow for the use of twinx()
        fig, ax1 = plt.subplots(
            figsize=(figsize[0] / 2.54, figsize[1] / 2.54),
            num="IPTS",
        )

        # Check if we have a single MU or a list of MUs to plot
        if isinstance(munumber, int):
            ax1 = sns.lineplot(x=x_axis, y=ipts[munumber])
            ax1.set_ylabel(
                "MU {}".format(munumber)
            )  # Useful because if the MU is empty it won't show the channel number
            ax1.set_xlabel("Time (Sec)" if timeinseconds else "Samples")

        elif isinstance(munumber, list):
            # Plot all the MUs.
            for count, thisMU in enumerate(munumber):
                y_axis = ipts[thisMU] + count
                sns.lineplot(x=x_axis, y=y_axis, ax=ax1)

                # Ensure correct and complete ticks on the left y axis
                ax1.set_yticks([*range(len(munumber))])
                ax1.set_yticklabels([str(x) for x in munumber])
                ax1.set_ylabel("Motor units")

        else:
            raise Exception(
                "While calling the plot_ipts function, you should pass an integer, a list or 'all' to munumber"
            )

        if addrefsig:
            ax2 = ax1.twinx()
            # Plot the ref signal
            xref = (
                emgfile["REF_SIGNAL"].index / emgfile["FSAMP"]
                if timeinseconds
                else emgfile["REF_SIGNAL"].index
            )
            sns.lineplot(y=emgfile["REF_SIGNAL"][0], x=xref, color="0.4", ax=ax2)
            ax2.set_ylabel("MViF (%)")

        showgoodlayout(tight_layout, despined="2yaxes" if addrefsig else False)
        if showimmediately:
            plt.show()

    else:
        raise Exception("IPTS is probably absent or it is not contained in a dataframe")


def plot_idr(
    emgfile,
    munumber="all",
    addrefsig=True,
    timeinseconds=True,
    figsize=[20, 15],
    showimmediately=True,
    tight_layout=True,
):
    """
    This function plots the IDR.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    munumber : str, int or list, default "all"
        ``all"
            IDR of all the MUs is plotted.
        Otherwise, a single MU (int) or multiple MUs (list of int) can be specified.
        The list can be passed as a manually-written list or with: munumber=[*range(0, 12)],
        We need the "*" operator to unpack the results of range and build a list.
        munumber is expected to be with base 0 (i.e., the first MU in the file is the number 0).
    addrefsig : bool, default True
        If True, the REF_SIGNAL is plotted in front of the MUs IDR with a separated y-axes.
    timeinseconds : bool, default True
        Whether to show the time on the x-axes in seconds (True) or in samples (False).
    figsize : list, default [20, 15]
        Size of the figure in centimeters [width, height].
    showimmediately : bool, default True
        If True (default), plt.show() is called and the figure showed to the user.
        It is useful to set it to False when calling the function from the GUI.
    tight_layout : bool, default True
        If True (default), the plt.tight_layout() is called and the figure's layout is improved.
        It is useful to set it to False when calling the function from the GUI.

    Notes
    -----
    munumber = "all" corresponds to munumber = [*range(0, emgfile["NUMBER_OF_MUS"])]
    """

    # Compute the instantaneous discharge rate (IDR) from the MUPULSES and check the input
    idr = compute_idr(emgfile=emgfile)

    if addrefsig:
        if not isinstance(emgfile["REF_SIGNAL"], pd.DataFrame):
            raise Exception(
                "REF_SIGNAL is probably absent or it is not contained in a dataframe"
            )

    # Check if all the MUs have to be plotted
    if isinstance(munumber, str):
        if emgfile["NUMBER_OF_MUS"] == 1:  # Manage exception of single MU
            munumber = 0
        else:
            munumber = [*range(0, emgfile["NUMBER_OF_MUS"])]

    # Use the subplot function to allow for the use of twinx()
    fig, ax1 = plt.subplots(figsize=(figsize[0] / 2.54, figsize[1] / 2.54), num="IDR")

    # Check if we have a single MU or a list of MUs to plot
    # In this case, the use of plt.figure has been preferred to plt.subplots for implementation  the MUs cleaning.
    if isinstance(munumber, int):
        ax1 = sns.scatterplot(
            x=idr[munumber]["timesec" if timeinseconds else "mupulses"],
            y=idr[munumber]["idr"],
        )

        ax1.set_ylabel(
            "MU {} (pps)".format(munumber)
        )  # Useful because if the MU is empty it won't show the channel number
        ax1.set_xlabel("Time (Sec)" if timeinseconds else "Samples")

    elif isinstance(munumber, list):
        for count, thisMU in enumerate(munumber):
            # Normalise the series
            norm_idr = min_max_scaling(idr[thisMU]["idr"])
            # Add 1 to the previous MUs to avoid overlapping of the MUs
            norm_idr = norm_idr + count
            sns.scatterplot(
                x=idr[thisMU]["timesec" if timeinseconds else "mupulses"],
                y=norm_idr,
                ax=ax1,
            )

        # Ensure correct and complete ticks on the left y axis
        ax1.set_yticks([*range(len(munumber))])
        ax1.set_yticklabels([str(x) for x in munumber])
        # Set axes labels
        ax1.set_ylabel("Motor units")
        ax1.set_xlabel("Time (Sec)" if timeinseconds else "Samples")

    else:
        raise Exception(
            "While calling the plot_idr function, you should pass an integer, a list or 'all' to munumber"
        )

    if addrefsig:
        ax2 = ax1.twinx()
        # Plot the ref signal
        xref = (
            emgfile["REF_SIGNAL"].index / emgfile["FSAMP"]
            if timeinseconds
            else emgfile["REF_SIGNAL"].index
        )
        sns.lineplot(y=emgfile["REF_SIGNAL"][0], x=xref, color="0.4", ax=ax2)
        ax2.set_ylabel("MViF (%)")

    showgoodlayout(tight_layout, despined="2yaxes" if addrefsig else False)
    if showimmediately:
        plt.show()

    return fig


def plot_muaps(sta_dict, title="MUAPs from STA", figsize=[20, 15], showimmediately=True):
    """
    Plot MUAPs obtained from STA from one or multiple MUs.

    Parameters
    ----------
    sta_dict : dict or list
        dict containing STA of the specified MU or a list of dicts containing STA
        of specified MUs.
        If a list is passed, different MUs are overlayed. This is useful for
        visualisation of MUAPs during tracking or duplicates removal.
    tile : str, default "MUAPs from STA"
        Title of the plot.
    figsize : list, default [20, 15]
        Size of the figure in centimeters [width, height].
    showimmediately : bool, default True
        If True (default), plt.show() is called and the figure showed to the user.
        It is useful to set it to False when calling the function from the GUI.

    Notes
    -----
    There is no limit to the number of MUs and STA files that can be overplotted.
    ``Remember: the different STAs should be matched`` with same number of electrode,
        processing (i.e., differential) and computed on the same timewindow.

    See also
    --------
    plot_muap : for overplotting all the STAs and the average STA of a single MU.
    align_by_xcorr : for alignin the STAs of two different MUs before plotting them.
    """

    if isinstance(sta_dict, dict):
        sta_dict = [sta_dict]

    if isinstance(sta_dict, list):
        # Find the largest and smallest value to define y axis limits.
        xmax = 0
        xmin = 0
        # Loop each sta_dict and MU, c means matrix columns
        for thisdict in sta_dict:
            for c in thisdict:
                max_ = thisdict[c].max().max()
                min_ = thisdict[c].min().min()
                if max_ > xmax:
                    xmax = max_
                if min_ < xmin:
                    xmin = min_

        # Obtain number of columns and rows, this changes if we use differential derivations
        cols = len(sta_dict[0])
        rows = len(sta_dict[0]["col0"].columns)
        fig, axs = plt.subplots(
            rows,
            cols,
            figsize=(figsize[0] / 2.54, figsize[1] / 2.54),
            num=title,
            sharex=True,
        )

        for thisdict in sta_dict:
            # Plot all the MUAPs, c means matrix columns, r rows
            for r in range(rows):
                for pos, c in enumerate(thisdict.keys()):
                    axs[r, pos].plot(thisdict[c].iloc[:, r])

                    axs[r, pos].set_ylim(xmin, xmax)
                    axs[r, pos].xaxis.set_visible(False)
                    axs[r, pos].set(yticklabels=[])
                    axs[r, pos].tick_params(left=False)

        showgoodlayout(tight_layout=False, despined=True)
        if showimmediately:
            plt.show()

    else:
        raise Exception("sta_dict must be dict or list")


def plot_muap(
    emgfile,
    stmuap,
    munumber,
    column,
    channel,
    channelprog=False,
    average=True,
    timeinseconds=True,
    figsize=[20, 15],
    showimmediately=True,
    tight_layout=True,
):
    """
    Plot the MUAPs of a specific matrix channel.

    Plot the MUs action potential (MUAPs) shapes with or without average.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    stmuap : dict
        dict containing a dict of ST MUAPs (pd.DataFrame) for every MUs.
    munumber : int
        The number of MU to plot.
    column : str {"col0", col1", "col2", "col3", "col4"}
        The matrix columns.
        Options are usyally "col0", "col1", "col2", "col3", "col4".
    channel : int
        The channel of the matrix to plot.
        This can be the real channel number if channelprog=False (default),
        or a progressive number (from 0 to the length of the matrix column)
        if channelprog=True.
    channelprog : bool, default False
        Whether to use the real channel number or a progressive number
        (see channel).
    average : bool, default True 
        Whether to plot also the MUAPs average obtained by spyke triggered average.
    timeinseconds : bool, default True
        Whether to show the time on the x-axes in seconds (True) or in samples (False).
    figsize : list, default [20, 15]
        Size of the figure in centimeters [width, height].
    showimmediately : bool, default True
        If True (default), plt.show() is called and the figure showed to the user.
        It is useful to set it to False when calling the function from the GUI.
    tight_layout : bool, default True
        If True (default), the plt.tight_layout() is called and the figure's layout is improved.
        It is useful to set it to False when calling the function from the GUI.
    
    See also
    --------
    plot_muaps : Plot MUAPs obtained from STA from one or multiple MUs.
    st_muap : Generate spike triggered MUAPs of every MUs (as input to this function).
    """

    # Check if munumber is within the number of MUs
    if munumber >= emgfile["NUMBER_OF_MUS"]:
        raise Exception(
            "munumber exceeds the the number of MUs in the emgfile ({})".format(
                emgfile["NUMBER_OF_MUS"]
            )
        )#TODO Check if these exceptions are necessary also in other STA functions/plot
    
    # Get the MUAPs to plot
    if channelprog:
        keys = list(stmuap[munumber][column].keys())

        # Check that the specified channel is within the matrix column range
        if channel >= len(keys):
            raise Exception(
                "Channel exceeds the the length of the matrix column, verify the use of channelprog"
            )
        
        my_muap = stmuap[munumber][column][keys[channel]]
        channelnumb = keys[channel]

    else:
        keys = list(stmuap[munumber][column].keys())

        # Check that the specified channel is within the matrix channels
        if not channel in keys:
            raise Exception(
                "Channel is not included in this matrix column, please check"
            )#TODO Check if these exceptions are necessary also in other STA functions/plot

        my_muap = stmuap[munumber][column][channel]
        channelnumb = channel

    # Here we produce an x axis in milliseconds or samples
    if timeinseconds:
        x_axis = (my_muap.index / emgfile["FSAMP"]) * 1000
    else:
        x_axis = my_muap.index

    # Set figure and name based on original channel number
    figname = "ST MUAPs of MU {}, column {}, channel {}".format(
        munumber, column, channelnumb
    )
    fig, ax1 = plt.subplots(
        figsize=(figsize[0] / 2.54, figsize[1] / 2.54),
        num=figname,
    )

    # Plot all the MUAPs
    if average:
        plt.plot(x_axis, my_muap, color="0.6", linewidth=0.2)
        plt.plot(x_axis, my_muap.mean(axis="columns"), color="red")

    else:
        plt.plot(x_axis, my_muap, linewidth=0.2)

    ax1.set_ylabel("Amplitude")
    ax1.set_xlabel("Time (ms)" if timeinseconds else "Samples")

    showgoodlayout(tight_layout)
    if showimmediately:
        plt.show()
