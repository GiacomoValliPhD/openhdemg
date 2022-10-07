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
    tight_layout: bool, default True
        If true (default), plt.tight_layout() is applied to the figure.
    despined: bool or str, default False
        False: left and bottom is not despined (standard plotting)
        True: all the sides are despined
        "2yaxes": only the top is despined. This is used for y axes both on the right and left side at the same time
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
    timeinseconds=True,
    figsize=[20, 15],
    showimmediately=True,
    tight_layout=True,
):
    """
    Pot the RAW_SIGNAL. Single or multiple channels.

    Parameters
    ----------
    emgfile: dict
        The dictionary containing the emgfile.
    channels: int or list
        The channel (int) or channels (list of int) to plot. 
        The list can be passed as a manually-written list or with: channels=[*range(0, 12)],
        We need the "*" operator to unpack the results of range and build a list.
        channels is expected to be with base 0 (i.e., the first channel in the file is the number 0).
    timeinseconds: bool, default True
        Whether to show the time on the x-axes in seconds (True) or in samples (False).
    figsize: list, default [20, 15]
        Size of the figure in centimeters [width, height].
    showimmediately: bool, default True
        If True (default), plt.show() is called and the figure showed to the user.
        It is useful to set it to False when calling the function from the GUI.
    tight_layout: bool, default True
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

        # Check if we have a single channel or a list of channels to plot
        if isinstance(channels, int):
            fig = plt.figure(
                f"Channel n.{channels}", figsize=(figsize[0] / 2.54, figsize[1] / 2.54)
            )
            ax = sns.lineplot(x=x_axis, y=emgsig[channels])
            ax.set_ylabel("Ch {}".format(channels))  # Useful because if the channe is empty it won't show the channel number
            ax.set_xlabel("Time (s)" if timeinseconds else "Samples")

            showgoodlayout(tight_layout)
            if showimmediately:
                plt.show()

        elif isinstance(channels, list):
            """
            A list can be passed in input as a manually-written list or with:
            channels=[*range(0, 12)]
            We need the "*" operator to unpack the results of range and build a list
            """
            figname = "Channels n.{}".format(channels)
            fig, axes = plt.subplots(
                len(channels),
                1,
                figsize=(figsize[0] / 2.54, figsize[1] / 2.54),
                num=figname,
            )

            # Plot all the channels in the subplots, up to 12 channels are clearly visible
            for count, channel in enumerate(reversed(channels)):
                ax = sns.lineplot(x=x_axis, y=emgsig[channel], ax=axes[count])
                ax.set_ylabel(channel)

                # Remove all the unnecessary for nice and clear plotting
                if channel != channels[0]:
                    ax.xaxis.set_visible(False)
                    ax.set(yticklabels=[])
                    ax.tick_params(left=False)

                else:
                    ax.set(yticklabels=[])
                    ax.tick_params(left=False)
                    ax.set_xlabel("Time (Sec)" if timeinseconds else "Samples")

            showgoodlayout(tight_layout, despined=True)
            if showimmediately:
                plt.show()

        else:
            raise Exception(
                "While calling the plot_emgsig function, you should pass an integer, a list or 'all' to channels"
            )

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
    emgfile: dict
        The dictionary containing the emgfile.
    timeinseconds: bool, default True
        Whether to show the time on the x-axes in seconds (True) or in samples (False).
    figsize: list, default [20, 15]
        Size of the figure in centimeters [width, height].
    showimmediately: bool, default True
        If True (default), plt.show() is called and the figure showed to the user.
        It is useful to set it to False when calling the function from the GUI.
    tight_layout: bool, default True
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

        #TODO Needed for the GUI? To check the other plot functions
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
    emgfile: dict
        The dictionary containing the emgfile.
    linewidths: float, default 0.5
        The width of the vertical lines representing the MU firing.
    order: bool, default False
        If True, MUs are sorted and plotted based on the order of recruitment.
    addrefsig: bool, default True
        If True, the REF_SIGNAL is plotted in front of the MUs pulses with a separated y-axes.
    timeinseconds: bool, default True
        Whether to show the time on the x-axes in seconds (True) or in samples (False).
    figsize: list, default [20, 15]
        Size of the figure in centimeters [width, height].
    showimmediately: bool, default True
        If True (default), plt.show() is called and the figure showed to the user.
        It is useful to set it to False when calling the function from the GUI.
    tight_layout: bool, default True
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

    if addrefsig:
        # Create the second (right) y axes
        ax2 = ax1.twinx()

        # Plot the MUPULSES.
        ax1.eventplot(
            mupulses,
            linewidths=linewidths,
            linelengths=0.9, # Assign 90% of the space in the plot to linelengths
            lineoffsets=1,
            colors=colors1,
        )

        # Plot REF_SIGNAL on the right y axes
        xref = (
            emgfile["REF_SIGNAL"].index / emgfile["FSAMP"]
            if timeinseconds
            else emgfile["REF_SIGNAL"].index
        )
        sns.lineplot(y=emgfile["REF_SIGNAL"][0], x=xref, color="0.4", ax=ax2)

        ax2.set_ylabel("MViF (%)")

    else:
        ax1.eventplot(
            mupulses,
            linewidths=linewidths,
            linelengths=0.9,
            lineoffsets=1,
            colors=colors1,
        )

    # Set axes labels
    ax1.set_ylabel("MUs")
    ax1.set_xlabel("Time (Sec)" if timeinseconds else "Samples")

    if addrefsig:
        showgoodlayout(tight_layout, despined="2yaxes")
    else:
        showgoodlayout(tight_layout)

    if showimmediately:
        plt.show()


def plot_ipts(
    emgfile,
    munumber="all",
    timeinseconds=True,
    figsize=[20, 15],
    showimmediately=True,
    tight_layout=True,
):
    """
    Plot the IPTS. Single or multiple MUs.

    Parameters
    ----------
    emgfile: dict
        The dictionary containing the emgfile.
    munumber: str, int or list, default "all"
        By default, IPTS of all the MUs is plotted.
        Otherwise, a single MU (int) or multiple MUs (list of int) can be specified.
        The list can be passed as a manually-written list or with: munumber=[*range(0, 12)],
        We need the "*" operator to unpack the results of range and build a list.
        munumber is expected to be with base 0 (i.e., the first MU in the file is the number 0).

    timeinseconds: bool, default True
        Whether to show the time on the x-axes in seconds (True) or in samples (False).
    figsize: list, default [20, 15]
        Size of the figure in centimeters [width, height].
    showimmediately: bool, default True
        If True (default), plt.show() is called and the figure showed to the user.
        It is useful to set it to False when calling the function from the GUI.
    tight_layout: bool, default True
        If True (default), the plt.tight_layout() is called and the figure's layout is improved.
        It is useful to set it to False when calling the function from the GUI.
    
    Notes
    -----
    munumber = "all" corresponds to munumber = [*range(0, emgfile["NUMBER_OF_MUS"])]
    """

    # Check if all the MUs have to be plotted
    if isinstance(munumber, str):
        if emgfile["NUMBER_OF_MUS"] == 1: # Manage exception of single MU
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

        # Check if we have a single MU or a list of MUs to plot
        if isinstance(munumber, int):
            fig = plt.figure(
                f"Motor unit n.{munumber}",
                figsize=(figsize[0] / 2.54, figsize[1] / 2.54),
            )
            ax = sns.lineplot(x=x_axis, y=ipts[munumber])
            ax.set_ylabel(
                "MU {}".format(munumber)
            )  # Useful because if the MU is empty it won't show the channel number
            ax.set_xlabel("Time (Sec)" if timeinseconds else "Samples")

            showgoodlayout(tight_layout)
            if showimmediately:
                plt.show()

        elif isinstance(munumber, (list, str)):
            figname = "Motor unit n.{}".format(munumber)
            fig, axes = plt.subplots(
                len(munumber),
                1,
                figsize=(figsize[0] / 2.54, figsize[1] / 2.54),
                num=figname,
            )

            # Plot all the MUs in the subplots. Enumerate reversed munumber to show the first MUs below
            for count, thisMU in enumerate(reversed(munumber)):
                ax = sns.lineplot(x=x_axis, y=ipts[thisMU], ax=axes[count])
                ax.set_ylabel(thisMU)

                # Remove all the unnecessary for nice and clear plotting
                if thisMU != munumber[0]:
                    ax.xaxis.set_visible(False)
                    ax.set(yticklabels=[])
                    ax.tick_params(left=False)

                else:
                    ax.set(yticklabels=[])
                    ax.tick_params(left=False)
                    ax.set_xlabel("Time (Sec)" if timeinseconds else "Samples")

            showgoodlayout(tight_layout, despined=True)
            if showimmediately:
                plt.show()

        else:
            raise Exception(
                "While calling the plot_ipts function, you should pass an integer, a list or 'all' to munumber"
            )

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
    emgfile: dict
        The dictionary containing the emgfile.
    munumber: str, int or list, default "all"
        By default, IDR of all the MUs is plotted.
        Otherwise, a single MU (int) or multiple MUs (list of int) can be specified.
        The list can be passed as a manually-written list or with: munumber=[*range(0, 12)],
        We need the "*" operator to unpack the results of range and build a list.
        munumber is expected to be with base 0 (i.e., the first MU in the file is the number 0).
    addrefsig: bool, default True
        If True, the REF_SIGNAL is plotted in front of the MUs IDR with a separated y-axes.
    timeinseconds: bool, default True
        Whether to show the time on the x-axes in seconds (True) or in samples (False).
    figsize: list, default [20, 15]
        Size of the figure in centimeters [width, height].
    showimmediately: bool, default True
        If True (default), plt.show() is called and the figure showed to the user.
        It is useful to set it to False when calling the function from the GUI.
    tight_layout: bool, default True
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
        if emgfile["NUMBER_OF_MUS"] == 1: # Manage exception of single MU
            munumber = 0
        else:
            munumber = [*range(0, emgfile["NUMBER_OF_MUS"])]

    # Check if we have a single MU or a list of MUs to plot
    if isinstance(munumber, int):
        fig = plt.figure(
            f"Motor unit n.{munumber}", figsize=(figsize[0] / 2.54, figsize[1] / 2.54)
        )
        ax = sns.scatterplot(
            x=idr[munumber]["timesec" if timeinseconds else "mupulses"],
            y=idr[munumber]["idr"],
        )

        if addrefsig:
            ax2 = ax.twinx()
            # Plot the ref signal
            xref = (
                emgfile["REF_SIGNAL"].index / emgfile["FSAMP"]
                if timeinseconds
                else emgfile["REF_SIGNAL"].index
            )
            sns.lineplot(y=emgfile["REF_SIGNAL"][0], x=xref, color="0.4", ax=ax2)
            ax2.set_ylabel("MViF (%)")

        ax.set_ylabel("MU {} (pps)".format(munumber))  # Useful because if the MU is empty it won't show the channel number
        ax.set_xlabel("Time (Sec)" if timeinseconds else "Samples")

        if addrefsig:
            showgoodlayout(tight_layout, despined="2yaxes")
        else:
            showgoodlayout(tight_layout)

        if showimmediately:
            plt.show()

    elif isinstance(munumber, list):
        # Behave differently if you plot both the ref signal and the idr or only the idr
        if not addrefsig:
            figname = "Motor unit n.{}".format(munumber)
            # sharex is fundamental to ensure correct representation of the idr over the different subplots
            fig, axes = plt.subplots(
                len(munumber),
                1,
                figsize=(figsize[0] / 2.54, figsize[1] / 2.54),
                num=figname,
                sharex=True,
            )
            # Create colors list for the firings and plot them. Loop backward because then you are plotting MUs in reversed order
            colors1 = [
                "C{}".format(i) for i in range(emgfile["NUMBER_OF_MUS"] - 1, -1, -1)
            ]
            # Plot all the MUs in the subplots. Enumerate reversed munumber to show the first MUs below
            for count, thisMU in enumerate(reversed(munumber)):
                ax = sns.scatterplot(
                    x=idr[thisMU]["timesec" if timeinseconds else "mupulses"],
                    y=idr[thisMU]["idr"],
                    color=colors1[count],
                    ax=axes[count],
                )
                ax.set_ylabel(thisMU)

                # Remove all the unnecessary for nice and clear plotting
                if thisMU != munumber[0]:
                    ax.xaxis.set_visible(False)
                    ax.set(yticklabels=[])
                    ax.tick_params(left=False)
                else:
                    ax.set(yticklabels=[])
                    ax.tick_params(left=False)

            # Set axes labels
            ax.set_xlabel("Time (Sec)" if timeinseconds else "Samples")

            showgoodlayout(tight_layout, despined=True)
            if showimmediately:
                plt.show()

        else:
            # Initialise figure and plots
            figname = "Motor unit n.{}".format(munumber)
            fig, ax1 = plt.subplots(
                figsize=(figsize[0] / 2.54, figsize[1] / 2.54), num=figname
            )
            # Apply twinx to ax2, which is the second y axis.
            ax2 = ax1.twinx()

            for count, thisMU in enumerate(munumber):
                # Normalise the series
                norm_idr = min_max_scaling(idr[thisMU]["idr"])
                # Add 1 compare to the previous MUs to avoid overlapping of the MUs
                norm_idr = norm_idr + count

                sns.scatterplot(
                    x=idr[thisMU]["timesec" if timeinseconds else "mupulses"],
                    y=norm_idr,
                    ax=ax1,
                )

            # Then plot the ref signal
            xref = (
                emgfile["REF_SIGNAL"].index / emgfile["FSAMP"]
                if timeinseconds
                else emgfile["REF_SIGNAL"].index
            )
            sns.lineplot(y=emgfile["REF_SIGNAL"][0], x=xref, ax=ax2)

            # Set axes labels
            ax2.set_ylabel("MViF (%)")
            ax1.set_ylabel("MUs number")
            ax1.set_xlabel("Time (Sec)" if timeinseconds else "Samples")

            showgoodlayout(tight_layout, despined="2yaxes")
            if showimmediately:
                plt.show()

    else:
        raise Exception(
            "While calling the plot_idr function, you should pass an integer, a list or 'all' to munumber"
        )

    return fig
