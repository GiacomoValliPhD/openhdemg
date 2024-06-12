"""
This module contains all the functions used to visualise the content of the
imported EMG file, the MUs properties or to save figures.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from openhdemg.library.tools import compute_idr
from openhdemg.library.mathtools import min_max_scaling


def showgoodlayout(tight_layout=True, despined=False):
    """
    Despine and show plots with a good layout.

    This function is called by the various plot functions contained in the
    library but can also be used by the user to quickly adjust the layout of
    custom plots.

    Parameters
    ----------
    tight_layout : bool, default True
        If true (default), plt.tight_layout() is applied to the figure.
    despined : bool or str {"2yaxes"}, default False

        False: left and bottom is not despined (standard plotting).

        True: all the sides are despined.

        ``2yaxes``
            Only the top is despined.
            This is used to show y axes both on the right and left side at the
            same time.
    """

    if despined is False:
        sns.despine()
    elif despined is True:
        sns.despine(top=True, bottom=True, left=True, right=True)
    elif despined == "2yaxes":
        sns.despine(top=True, bottom=False, left=False, right=False)
    else:
        raise ValueError(
            f"despined can be True, False or 2yaxes. {despined} was passed instead"
        )

    if tight_layout is True:
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
    Plot the RAW_SIGNAL. Single or multiple channels.

    Up to 12 channels (a common matrix row) can be easily observed togheter,
    but more can be plotted.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    channels : int or list
        The channel (int) or channels (list of int) to plot.
        The list can be passed as a manually-written list or with:
        channels=[*range(0, 13)].
        We need the " * " operator to unpack the results of range into a list.
        channels is expected to be with base 0 (i.e., the first channel
        in the file is the number 0).
    addrefsig : bool, default True
        If True, the REF_SIGNAL is plotted in front of the signal with a
        separated y-axes.
    timeinseconds : bool, default True
        Whether to show the time on the x-axes in seconds (True)
        or in samples (False).
    figsize : list, default [20, 15]
        Size of the figure in centimeters [width, height].
    showimmediately : bool, default True
        If True (default), plt.show() is called and the figure showed to the
        user.
        It is useful to set it to False when calling the function from the GUI.
    tight_layout : bool, default True
        If True (default), the plt.tight_layout() is called and the figure's
        layout is improved.
        It is useful to set it to False when calling the function from the GUI.

    Returns
    -------
    fig : pyplot `~.figure.Figure`

    See also
    --------
    - plot_differentials : plot the differential derivation of the RAW_SIGNAL
        by matrix column.

    Examples
    --------
    Plot channels 0 to 12 and overlay the reference signal.
    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> emg.plot_emgsig(
    ...     emgfile=emgfile,
    ...     channels=[*range(0,13)],
    ...     addrefsig=True,
    ...     timeinseconds=True,
    ...     figsize=[20, 15],
    ... )
    """

    # Check to have the RAW_SIGNAL in a pandas dataframe
    if isinstance(emgfile["RAW_SIGNAL"], pd.DataFrame):
        emgsig = emgfile["RAW_SIGNAL"]
    else:
        raise TypeError(
            "RAW_SIGNAL is probably absent or it is not contained in a dataframe"
        )

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
        plt.plot(x_axis, emgsig[channels])
        plt.ylabel("Ch {}".format(channels))
        # set_ylabel is useful because if the channe is empty it won't
        # show the channel number
        plt.xlabel("Time (s)" if timeinseconds else "Samples")

    elif isinstance(channels, list):
        # Plot all the channels in the subplots
        for count, thisChannel in enumerate(channels):
            # Normalise the series
            norm_raw = min_max_scaling(emgfile["RAW_SIGNAL"][thisChannel])
            # TODO option to scale all the df or the single channel
            # Add 1 to the previous channel to avoid overlapping
            norm_raw = norm_raw + count
            plt.plot(x_axis, norm_raw)

        # Ensure correct and complete ticks on the left y axis
        ax1.set_yticks([*range(len(channels))])
        ax1.set_yticklabels([str(x) for x in channels])
        # Set axes labels
        ax1.set_ylabel("Channels")
        ax1.set_xlabel("Time (Sec)" if timeinseconds else "Samples")

    else:
        raise TypeError(
            "While calling the plot_emgsig function, you should pass an "
            + "integer or a list to channels"
        )

    if addrefsig:
        ax2 = ax1.twinx()
        # Plot the ref signal
        xref = (
            emgfile["REF_SIGNAL"].index / emgfile["FSAMP"]
            if timeinseconds
            else emgfile["REF_SIGNAL"].index
        )
        sns.lineplot(
            x=xref,
            y=emgfile["REF_SIGNAL"][0],
            color="0.4",
            ax=ax2,
        )
        ax2.set_ylabel("MVC")

    showgoodlayout(tight_layout, despined="2yaxes" if addrefsig else False)
    if showimmediately:
        plt.show()

    return fig


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
        The dictionary containing the differential derivation of the
        RAW_SIGNAL.
    column : str {"col0", "col1", "col2", "col3", "col4", ...}, default "col0"
        The matrix column to plot.
        Options are usyally "col0", "col1", "col2", "col3", "col4".
        but might change based on the size of the matrix used.
    addrefsig : bool, default True
        If True, the REF_SIGNAL is plotted in front of the signal with a
        separated y-axes.
    timeinseconds : bool, default True
        Whether to show the time on the x-axes in seconds (True)
        or in samples (False).
    figsize : list, default [20, 15]
        Size of the figure in centimeters [width, height].
    showimmediately : bool, default True
        If True (default), plt.show() is called and the figure showed to the
        user.
        It is useful to set it to False when calling the function from the GUI.
    tight_layout : bool, default True
        If True (default), the plt.tight_layout() is called and the figure's
        layout is improved.
        It is useful to set it to False when calling the function from the GUI.

    Returns
    -------
    fig : pyplot `~.figure.Figure`

    See also
    --------
    - diff : calculate single differential of RAW_SIGNAL on matrix rows.
    - double_diff : calculate double differential of RAW_SIGNAL on matrix rows.
    - plot_emgsig : pot the RAW_SIGNAL. Single or multiple channels.

    Examples
    --------
    Plot the differential derivation of the first matrix column (col0).

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> sorted_rawemg = emg.sort_rawemg(
    >>>     emgfile=emgfile,
    >>>     code="GR08MM1305",
    >>>     orientation=180,
    >>> )
    >>> sd=emg.diff(sorted_rawemg=sorted_rawemg)
    >>> emg.plot_differentials(
    ...     emgfile=emgfile,
    ...     differential=sd,
    ...     column="col0",
    ...     addrefsig=False,
    ...     timeinseconds=True,
    ...     figsize=[20, 15],
    ...     showimmediately=True,
    ... )
    """

    # Check to have the RAW_SIGNAL in a pandas dataframe
    if isinstance(differential[column], pd.DataFrame):
        emgsig = differential[column]
    else:
        raise TypeError(
            "RAW_SIGNAL is probably absent or it is not contained in a dataframe"
        )

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
        plt.plot(x_axis, norm_raw)

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
        sns.lineplot(
            x=xref,
            y=emgfile["REF_SIGNAL"][0],
            color="0.4",
            ax=ax2,
        )
        ax2.set_ylabel("MVC")

    showgoodlayout(tight_layout, despined="2yaxes" if addrefsig else False)
    if showimmediately:
        plt.show()

    return fig


def plot_refsig(
    emgfile,
    ylabel="MVC",
    timeinseconds=True,
    figsize=[20, 15],
    showimmediately=True,
    tight_layout=True,
):
    """
    Plot the REF_SIGNAL.

    The REF_SIGNAL is usually expressed as % MVC for submaximal contractions
    or as Kilograms (Kg) or Newtons (N) for maximal contractions, but any
    value can be plotted.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    ylabel : str, default "MVC"
        The unit of measure to show on the Y axis.
    timeinseconds : bool, default True
        Whether to show the time on the x-axes in seconds (True)
        or in samples (False).
    figsize : list, default [20, 15]
        Size of the figure in centimeters [width, height].
    showimmediately : bool, default True
        If True (default), plt.show() is called and the figure showed to the
        user.
        It is useful to set it to False when calling the function from the GUI.
    tight_layout : bool, default True
        If True (default), the plt.tight_layout() is called and the figure's
        layout is improved.
        It is useful to set it to False when calling the function from the GUI.

    Returns
    -------
    fig : pyplot `~.figure.Figure`

    Examples
    --------
    Plot the reference signal.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> emg.plot_refsig(emgfile=emgfile)

    Change Y axis label and show time in samples.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> emg.plot_refsig(
    >>>     emgfile=emgfile,
    >>>     ylabel="Custom unit e.g., N or kg",
    >>>     timeinseconds=False,
    >>> )
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
        ax.set_ylabel(ylabel)
        ax.set_xlabel("Time (Sec)" if timeinseconds else "Samples")

        showgoodlayout(tight_layout)
        if showimmediately:
            plt.show()

        return fig

    else:
        raise TypeError(
            "REF_SIGNAL is probably absent or it is not contained in a dataframe"
        )


def plot_mupulses(
    emgfile,
    munumber="all",
    linewidths=0.5,
    addrefsig=True,
    timeinseconds=True,
    figsize=[20, 15],
    showimmediately=True,
    tight_layout=True,
):
    """
    Plot all the MUPULSES (binary representation of the firings time).

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    munumber : str, int or list, default "all"

        ``all``
            IPTS of all the MUs is plotted.

        Otherwise, a single MU (int) or multiple MUs (list of int) can be
        specified.
        The list can be passed as a manually-written list or with:
        munumber=[*range(0, 12)].
        We need the " * " operator to unpack the results of range into a list.
        munumber is expected to be with base 0 (i.e., the first MU in the file
        is the number 0).
    linewidths : float, default 0.5
        The width of the vertical lines representing the MU firing.
    addrefsig : bool, default True
        If True, the REF_SIGNAL is plotted in front of the MUs pulses with a
        separated y-axes.
    timeinseconds : bool, default True
        Whether to show the time on the x-axes in seconds (True)
        or in samples (False).
    figsize : list, default [20, 15]
        Size of the figure in centimeters [width, height].
    showimmediately : bool, default True
        If True (default), plt.show() is called and the figure showed to the
        user.
        It is useful to set it to False when calling the function from the GUI.
    tight_layout : bool, default True
        If True (default), the plt.tight_layout() is called and the figure's
        layout is improved.
        It is useful to set it to False when calling the function from the GUI.

    Returns
    -------
    fig : pyplot `~.figure.Figure`

    See also
    --------
    - plot_ipts : plot the MUs impulse train per second (IPTS).
    - plot_idr : plot the instantaneous discharge rate.

    Examples
    --------
    Plot MUs pulses based on recruitment order and overlay the reference
    signal.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> emg.plot_mupulses(
    ...     emgfile=emgfile,
    ...     linewidths=0.5,
    ...     order=True,
    ...     addrefsig=True,
    ...     timeinseconds=True,
    ...     figsize=[20, 15],
    ...     showimmediately=True,
    ... )
    """

    # Check to have the correct input
    if isinstance(emgfile["MUPULSES"], list):
        mupulses = emgfile["MUPULSES"]
    else:
        raise TypeError(
            "MUPULSES is probably absent or it is not contained in a np.array"
        )

    if addrefsig:
        if not isinstance(emgfile["REF_SIGNAL"], pd.DataFrame):
            raise TypeError(
                "REF_SIGNAL is probably absent or it is not contained in a dataframe"
            )

    # Check if all the MUs have to be plotted and create the y labels
    if isinstance(munumber, str):
        # Manage exception of single MU
        if emgfile["NUMBER_OF_MUS"] > 1:
            y_tick_lab = [*range(0, emgfile["NUMBER_OF_MUS"])]
            ylab = "Motor units"
        else:
            y_tick_lab = []
            ylab = "MU n. 0"

    elif isinstance(munumber, int):
        mupulses = [mupulses[munumber]]
        y_tick_lab = []
        ylab = f"MU n. {munumber}"
    elif isinstance(munumber, list):
        if len(munumber) > 1:
            mupulses = [mupulses[mu] for mu in munumber]
            y_tick_lab = munumber
            ylab = "Motor units"
        else:
            mupulses = [mupulses[munumber[0]]]
            y_tick_lab = []
            ylab = f"MU n. {munumber[0]}"
    else:
        raise TypeError(
            "While calling the plot_mupulses function, you should pass an integer, a list or 'all' to munumber"
        )

    # Convert x axes in seconds if timeinseconds==True.
    # This has to be done both for the REF_SIGNAL and the mupulses, for the
    # MUPULSES we need to convert the point of firing from samples to seconds.
    if timeinseconds:
        mupulses = [n / emgfile["FSAMP"] for n in mupulses]

    # Create colors list for the firings and plot them
    colors1 = ["C{}".format(i) for i in range(len(mupulses))]

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
    ax1.set_yticks([*range(len(mupulses))])
    ax1.set_yticklabels([str(mu) for mu in y_tick_lab])
    # Set axes labels
    ax1.set_ylabel(ylab)
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
        sns.lineplot(x=xref, y=emgfile["REF_SIGNAL"][0], color="0.4", ax=ax2)
        ax2.set_ylabel("MVC")

    showgoodlayout(tight_layout, despined="2yaxes" if addrefsig else False)
    if showimmediately:
        plt.show()

    return fig


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
    Plot the IPTS (decomposed source).

    IPTS is the non-binary representation of the MUs firing times.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    munumber : str, int or list, default "all"

        ``all``
            IPTS of all the MUs is plotted.

        Otherwise, a single MU (int) or multiple MUs (list of int) can be
        specified.
        The list can be passed as a manually-written list or with:
        munumber=[*range(0, 12)].
        We need the " * " operator to unpack the results of range into a list.
        munumber is expected to be with base 0 (i.e., the first MU in the file
        is the number 0).
    timeinseconds : bool, default True
        Whether to show the time on the x-axes in seconds (True)
        or in samples (False).
    figsize : list, default [20, 15]
        Size of the figure in centimeters [width, height].
    showimmediately : bool, default True
        If True (default), plt.show() is called and the figure showed to the
        user.
        It is useful to set it to False when calling the function from the GUI.
    tight_layout : bool, default True
        If True (default), the plt.tight_layout() is called and the figure's
        layout is improved.
        It is useful to set it to False when calling the function from the GUI.

    Returns
    -------
    fig : pyplot `~.figure.Figure`

    See also
    --------
    - plot_mupulses : plot the binary representation of the firings.
    - plot_idr : plot the instantaneous discharge rate.

    Notes
    -----
    munumber = "all" corresponds to:
    munumber = [*range(0, emgfile["NUMBER_OF_MUS"])]

    Examples
    --------
    Plot IPTS of all the MUs and overlay the reference signal.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> emg.plot_ipts(
    ...     emgfile=emgfile,
    ...     munumber="all",
    ...     addrefsig=True,
    ...     timeinseconds=True,
    ...     figsize=[20, 15],
    ...     showimmediately=True,
    ... )

    Plot IPTS of two MUs.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> emg.plot_ipts(
    ...     emgfile=emgfile,
    ...     munumber=[1, 3],
    ...     addrefsig=False,
    ...     timeinseconds=True,
    ...     figsize=[20, 15],
    ...     showimmediately=True,
    ... )
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
    else:
        raise TypeError(
            "IPTS is probably absent or it is not contained in a dataframe"
        )

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
        plt.plot(x_axis, ipts[munumber])
        plt.ylabel("MU {}".format(munumber))
        # Use set_ylabel because if the MU is empty,
        # the channel number won't show.

    elif isinstance(munumber, list):
        # Plot all the MUs.
        for count, thisMU in enumerate(munumber):
            norm_ipts = min_max_scaling(ipts[thisMU])
            y_axis = norm_ipts + count
            plt.plot(x_axis, y_axis)

            # Ensure correct and complete ticks on the left y axis
            plt.yticks([*range(len(munumber))])
            plt.gca().set_yticklabels([str(mu) for mu in munumber])
            plt.ylabel("Motor units")

    else:
        raise TypeError(
            "While calling the plot_ipts function, you should pass an integer, a list or 'all' to munumber"
        )

    ax1.set_xlabel("Time (Sec)" if timeinseconds else "Samples")

    if addrefsig:
        ax2 = ax1.twinx()
        # Plot the ref signal
        xref = (
            emgfile["REF_SIGNAL"].index / emgfile["FSAMP"]
            if timeinseconds
            else emgfile["REF_SIGNAL"].index
        )
        sns.lineplot(
            x=xref,
            y=emgfile["REF_SIGNAL"][0],
            color="0.4",
            ax=ax2,
        )
        ax2.set_ylabel("MVC")

    showgoodlayout(tight_layout, despined="2yaxes" if addrefsig else False)
    if showimmediately:
        plt.show()

    return fig


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
    Plot the instantaneous discharge rate (IDR).

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    munumber : str, int or list, default "all"

        ``all``
            IDR of all the MUs is plotted.

        Otherwise, a single MU (int) or multiple MUs (list of int) can be
        specified.
        The list can be passed as a manually-written list or with:
        munumber=[*range(0, 12)].
        We need the " * " operator to unpack the results of range into a list.
        munumber is expected to be with base 0 (i.e., the first MU in the file
        is the number 0).
    addrefsig : bool, default True
        If True, the REF_SIGNAL is plotted in front of the MUs IDR with a
        separated y-axes.
    timeinseconds : bool, default True
        Whether to show the time on the x-axes in seconds (True)
        or in samples (False).
    figsize : list, default [20, 15]
        Size of the figure in centimeters [width, height].
    showimmediately : bool, default True
        If True (default), plt.show() is called and the figure showed to the
        user.
        It is useful to set it to False when calling the function from the GUI.
    tight_layout : bool, default True
        If True (default), the plt.tight_layout() is called and the figure's
        layout is improved.
        It is useful to set it to False when calling the function from the GUI.

    Returns
    -------
    fig : pyplot `~.figure.Figure`

    See also
    --------
    - plot_mupulses : plot the binary representation of the firings.
    - plot_ipts : plot the impulse train per second (IPTS).

    Notes
    -----
    munumber = "all" corresponds to
    munumber = [*range(0, emgfile["NUMBER_OF_MUS"])]

    Examples
    --------
    Plot IDR of all the MUs and overlay the reference signal.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> emg.plot_idr(
    ...     emgfile=emgfile,
    ...     munumber="all",
    ...     addrefsig=True,
    ...     timeinseconds=True,
    ...     figsize=[20, 15],
    ...     showimmediately=True,
    ... )

    Plot IDR of two MUs.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> emg.plot_idr(
    ...     emgfile=emgfile,
    ...     munumber=[1, 3],
    ...     addrefsig=False,
    ...     timeinseconds=True,
    ...     figsize=[20, 15],
    ...     showimmediately=True,
    ... )
    """

    # Compute the IDR
    idr = compute_idr(emgfile=emgfile)

    if addrefsig:
        if not isinstance(emgfile["REF_SIGNAL"], pd.DataFrame):
            raise TypeError(
                "REF_SIGNAL is probably absent or it is not contained in a dataframe"
            )

    # Check if all the MUs have to be plotted
    if isinstance(munumber, str):
        if emgfile["NUMBER_OF_MUS"] == 1:  # Manage exception of single MU
            munumber = 0
        else:
            munumber = [*range(0, emgfile["NUMBER_OF_MUS"])]

    # Use the subplot function to allow for the use of twinx()
    fig, ax1 = plt.subplots(
        figsize=(figsize[0] / 2.54, figsize[1] / 2.54),
        num="IDR",
    )

    # Check if we have a single MU or a list of MUs to plot.
    if isinstance(munumber, int):
        ax1 = sns.scatterplot(
            x=idr[munumber]["timesec" if timeinseconds else "mupulses"],
            y=idr[munumber]["idr"],
        )  # sns.scatterplot breaks if x or y are nan

        ax1.set_ylabel(
            "MU {} (PPS)".format(munumber)
        )  # Useful because if the MU is empty it won't show the channel number
        ax1.set_xlabel("Time (Sec)" if timeinseconds else "Samples")

    elif isinstance(munumber, list):
        if len(munumber) > 1:
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
            ax1.set_yticklabels([str(mu) for mu in munumber])
            # Set axes labels
            ax1.set_ylabel("Motor units")
            ax1.set_xlabel("Time (Sec)" if timeinseconds else "Samples")

        elif len(munumber) == 1:
            # TODO remove this part and check len before.
            # See plot_smoothed_dr as a reference
            ax1 = sns.scatterplot(
                x=idr[munumber[0]]["timesec" if timeinseconds else "mupulses"],
                y=idr[munumber[0]]["idr"],
            )

            ax1.set_ylabel(
                "MU {} (PPS)".format(munumber[0])
            )  # Useful because if the MU is empty it won't show the channel n
            ax1.set_xlabel("Time (Sec)" if timeinseconds else "Samples")

    else:
        raise TypeError(
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
        ax2.set_ylabel("MVC")

    showgoodlayout(tight_layout, despined="2yaxes" if addrefsig else False)
    if showimmediately:
        plt.show()

    return fig


def plot_smoothed_dr(
    emgfile,
    smoothfits,
    munumber="all",
    addidr=True,
    stack=True,
    addrefsig=True,
    timeinseconds=True,
    figsize=[20, 15],
    showimmediately=True,
    tight_layout=True,
):
    """
    Plot the smoothed discharge rate.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    smoothfits : pd.DataFrame
        Smoothed discharge rate estimates aligned in time. Columns should
        contain the smoothed discharge rate for each MU.
    munumber : str, int or list, default "all"

        ``all``
            IDR of all the MUs is plotted.

        Otherwise, a single MU (int) or multiple MUs (list of int) can be
        specified.
        The list can be passed as a manually-written list or with:
        munumber=[*range(0, 12)].
        We need the " * " operator to unpack the results of range into a list.
        munumber is expected to be with base 0 (i.e., the first MU in the file
        is the number 0).
    addidr : bool, default True
        Whether to show also the IDR behind the smoothed DR line.
    stack : bool, default True
        Whether to stack multiple MUs. If False, all the MUs smoothed DR will
        be plotted on the same line.
    addrefsig : bool, default True
        If True, the REF_SIGNAL is plotted in front of the MUs IDR with a
        separated y-axes.
    timeinseconds : bool, default True
        Whether to show the time on the x-axes in seconds (True)
        or in samples (False).
    figsize : list, default [20, 15]
        Size of the figure in centimeters [width, height].
    showimmediately : bool, default True
        If True (default), plt.show() is called and the figure showed to the
        user.
        It is useful to set it to False when calling the function from the GUI.
    tight_layout : bool, default True
        If True (default), the plt.tight_layout() is called and the figure's
        layout is improved.
        It is useful to set it to False when calling the function from the GUI.

    Returns
    -------
    fig : pyplot `~.figure.Figure`

    See also
    --------
    - compute_svr : Fit MU discharge rates with Support Vector Regression,
        nonlinear regression.

    Notes
    -----
    munumber = "all" corresponds to:
    munumber = [*range(0, emgfile["NUMBER_OF_MUS"])]

    Examples
    --------
    Smooth MUs DR using Support Vector Regression.

    >>> import openhdemg.library as emg
    >>> import pandas as pd
    >>> emgfile = emg.emg_from_samplefile()
    >>> emgfile = emg.sort_mus(emgfile=emgfile)
    >>> svrfits = emg.compute_svr(emgfile)

    Plot the stacked smoothed DR of all the MUs and overlay the IDR and the
    reference signal.

    >>> smoothfits = pd.DataFrame(svrfits["gensvr"]).transpose()
    >>> emg.plot_smoothed_dr(
    >>>     emgfile,
    >>>     smoothfits=smoothfits,
    >>>     munumber="all",
    >>>     addidr=True,
    >>>     stack=True,
    >>>     addrefsig=True,
    >>> )
    """

    # Compute the IDR
    idr = compute_idr(emgfile=emgfile)

    if addrefsig:
        if not isinstance(emgfile["REF_SIGNAL"], pd.DataFrame):
            raise TypeError(
                "REF_SIGNAL is probably absent or it is not contained in a dataframe"
            )

    # Check if all the MUs have to be plotted
    if isinstance(munumber, list):
        if len(munumber) == 1:  # Manage exception of single MU
            munumber = munumber[0]
    elif isinstance(munumber, str):
        if emgfile["NUMBER_OF_MUS"] == 1:  # Manage exception of single MU
            munumber = 0
        else:
            munumber = [*range(0, emgfile["NUMBER_OF_MUS"])]

    # Check smoothfits type
    if not isinstance(smoothfits, pd.DataFrame):
        raise TypeError("smoothfits must be a pd.DataFrame")

    # Use the subplot function to allow for the use of twinx()
    fig, ax1 = plt.subplots(
        figsize=(figsize[0] / 2.54, figsize[1] / 2.54),
        num="Smoothed DR",
    )

    # Check if we have a single MU or a list of MUs to plot.
    if isinstance(munumber, int):
        # Plot IDR
        if addidr:
            sns.scatterplot(
                x=idr[munumber]["timesec" if timeinseconds else "mupulses"],
                y=idr[munumber]["idr"],
                ax=ax1,
                alpha=0.4,
            )  # sns.scatterplot breaks if x or y are nan?

        # Plot smoothed DR
        if timeinseconds:
            x_smooth = np.arange(len(smoothfits[munumber])) / emgfile["FSAMP"]
        else:
            x_smooth = np.arange(len(smoothfits[munumber]))
        ax1.plot(x_smooth, smoothfits[munumber], linewidth=2)

        # Labels
        ax1.set_ylabel(
            "MU {} (PPS)".format(munumber)
        )  # Useful because if the MU is empty it won't show the channel number
        ax1.set_xlabel("Time (Sec)" if timeinseconds else "Samples")

    elif isinstance(munumber, list) and stack:
        for count, thisMU in enumerate(munumber):
            # Plot IDR
            if addidr:
                # Normalise the IDR series and add 1 to the previous MUs to
                # avoid overlapping of the MUs.
                norm_idr = min_max_scaling(idr[thisMU]["idr"]) + count
                sns.scatterplot(
                    x=idr[thisMU]["timesec" if timeinseconds else "mupulses"],
                    y=norm_idr,
                    ax=ax1,
                    alpha=0.4,
                )

            # Plot smoothed DR
            if timeinseconds:
                x_smooth = np.arange(
                    len(smoothfits[thisMU])
                ) / emgfile["FSAMP"]
            else:
                x_smooth = np.arange(len(smoothfits[thisMU]))

            if addidr:
                # Scale factor to match smoothed DR and IDR when stacked
                delta = (
                    (smoothfits[thisMU].max() - smoothfits[thisMU].min()) /
                    (idr[thisMU]["idr"].max() - idr[thisMU]["idr"].min())
                )
                delta_min = (
                    (smoothfits[thisMU].min() - idr[thisMU]["idr"].min()) /
                    (idr[thisMU]["idr"].max() - idr[thisMU]["idr"].min())
                )
                norm_fit = min_max_scaling(smoothfits[thisMU])
                norm_fit = norm_fit * delta + delta_min + count
                ax1.plot(x_smooth, norm_fit, linewidth=2)
            else:
                norm_fit = min_max_scaling(smoothfits[thisMU]) + count
                ax1.plot(x_smooth, norm_fit, linewidth=2)

        # Ensure correct and complete ticks on the left y axis
        ax1.set_yticks([*range(len(munumber))])
        ax1.set_yticklabels([str(mu) for mu in munumber])
        # Set axes labels
        ax1.set_ylabel("Motor units")
        ax1.set_xlabel("Time (Sec)" if timeinseconds else "Samples")

    elif isinstance(munumber, list) and not stack:
        for count, thisMU in enumerate(munumber):
            # Plot IDR
            if addidr:
                sns.scatterplot(
                    x=idr[thisMU]["timesec" if timeinseconds else "mupulses"],
                    y=idr[thisMU]["idr"],
                    ax=ax1,
                    alpha=0.4,
                )

            # Plot smoothed DR
            if timeinseconds:
                x_smooth = np.arange(
                    len(smoothfits[thisMU])
                ) / emgfile["FSAMP"]
            else:
                x_smooth = np.arange(len(smoothfits[thisMU]))
            ax1.plot(x_smooth, smoothfits[thisMU], linewidth=2)

        # Set axes labels
        ax1.set_ylabel("Discharge rate (PPS)")
        ax1.set_xlabel("Time (Sec)" if timeinseconds else "Samples")

    else:
        raise TypeError(
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
        ax2.set_ylabel("MVC")

    showgoodlayout(tight_layout, despined="2yaxes" if addrefsig else False)
    if showimmediately:
        plt.show()

    return fig


def plot_muaps(
    sta_dict,
    title="MUAPs from STA",
    figsize=[20, 15],
    showimmediately=True,
    tight_layout=False,
):
    """
    Plot MUAPs obtained from STA from one or multiple MUs.

    Parameters
    ----------
    sta_dict : dict or list
        dict containing STA of the specified MU or a list of dicts containing
        STA of specified MUs.
        If a list is passed, different MUs are overlayed. This is useful for
        visualisation of MUAPs during tracking or duplicates removal.
    title : str, default "MUAPs from STA"
        Title of the plot.
    figsize : list, default [20, 15]
        Size of the figure in centimeters [width, height].
    showimmediately : bool, default True
        If True (default), plt.show() is called and the figure showed to the
        user.
        It is useful to set it to False when calling the function from the GUI.
    tight_layout : bool, default False
        If True (default), the plt.tight_layout() is called and the figure's
        layout is improved.
        It is useful to set it to False when calling the function from the GUI
        or if the final layout is not correct.

    Returns
    -------
    fig : pyplot `~.figure.Figure`

    See also
    --------
    - sta : computes the spike-triggered average (STA) of every MUs.
    - plot_muap : for overplotting all the STAs and the average STA of a MU.
    - align_by_xcorr : for alignin the STAs of two different MUs.

    Notes
    -----
    There is no limit to the number of MUs and STA files that can be
    overplotted.

    ``Remember: the different STAs should be matched`` with same number of
        electrode, processing (i.e., differential) and computed on the same
        timewindow.

    Examples
    --------
    Plot MUAPs of a single MU.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> sorted_rawemg = emg.sort_rawemg(
    ...     emgfile=emgfile,
    ...     code="GR08MM1305",
    ...     orientation=180,
    ...     dividebycolumn=True,
    ... )
    >>> sta = emg.sta(
    ...     emgfile=emgfile,
    ...     sorted_rawemg=sorted_rawemg,
    ...     firings="all",
    ...     timewindow=50,
    ... )
    >>> emg.plot_muaps(sta_dict=sta[1])

    Plot single differential derivation MUAPs of a single MU.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> sorted_rawemg = emg.sort_rawemg(
    ...     emgfile=emgfile,
    ...     code="GR08MM1305",
    ...     orientation=180,
    ...     dividebycolumn=True,
    ... )
    >>> sorted_rawemg = emg.diff(sorted_rawemg=sorted_rawemg)
    >>> sta = emg.sta(
    ...     emgfile=emgfile,
    ...     sorted_rawemg=sorted_rawemg,
    ...     firings="all",
    ...     timewindow=50,
    ... )
    >>> emg.plot_muaps(sta_dict=sta[1])

    Plot single differential derivation MUAPs of two MUs from the same file.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> sorted_rawemg = emg.sort_rawemg(
    ...     emgfile=emgfile,
    ...     code="GR08MM1305",
    ...     orientation=180,
    ...     dividebycolumn=True,
    ... )
    >>> sorted_rawemg = emg.diff(sorted_rawemg=sorted_rawemg)
    >>> sta = emg.sta(
    ...     emgfile=emgfile,
    ...     sorted_rawemg=sorted_rawemg,
    ...     firings="all",
    ...     timewindow=50,
    ... )
    >>> emg.plot_muaps(sta_dict=[sta[1], sta[2]])
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

        # Obtain number of columns and rows
        cols = len(sta_dict[0])
        rows = len(sta_dict[0]["col0"].columns)
        fig, axs = plt.subplots(
            rows,
            cols,
            figsize=(figsize[0] / 2.54, figsize[1] / 2.54),
            num=title,
            sharex=True,
        )

        # Manage exception of arrays instead of matrices and check that they
        # are correctly oriented.
        if cols > 1 and rows > 1:
            # Matrices
            for thisdict in sta_dict:
                # Plot all the MUAPs, c means matrix columns, r rows
                for r in range(rows):
                    for pos, c in enumerate(thisdict.keys()):
                        axs[r, pos].plot(thisdict[c].iloc[:, r])

                        axs[r, pos].set_ylim(xmin, xmax)
                        axs[r, pos].xaxis.set_visible(False)
                        axs[r, pos].set(yticklabels=[])
                        axs[r, pos].tick_params(left=False)

        elif cols == 1 and rows > 1:
            # Arrays
            for thisdict in sta_dict:
                # Plot all the MUAPs, c means matrix columns, r rows
                for r in range(rows):
                    for pos, c in enumerate(thisdict.keys()):
                        axs[r].plot(thisdict[c].iloc[:, r])

                        axs[r].set_ylim(xmin, xmax)
                        axs[r].xaxis.set_visible(False)
                        axs[r].set(yticklabels=[])
                        axs[r].tick_params(left=False)

        elif cols > 1 and rows == 1:
            raise ValueError(
                "Arrays should be organised as 1 column, multiple rows. " +
                "Not as 1 row, multiple columns."
            )

        else:
            raise ValueError(
                "Unacceptable number of rows and columns to plot"
            )

        showgoodlayout(tight_layout=tight_layout, despined=True)
        if showimmediately:
            plt.show()

        return fig

    else:
        raise TypeError("sta_dict must be dict or list")


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
        The number of the MU to plot.
    column : str
        The matrix columns.
        Options are usyally "col0", "col1", "col2", ..., last column.
    channel : int
        The channel of the matrix to plot.
        This can be the real channel number if channelprog=False (default),
        or a progressive number (from 0 to the length of the matrix column)
        if channelprog=True.
    channelprog : bool, default False
        Whether to use the real channel number or a progressive number
        (see channel).
    average : bool, default True
        Whether to plot also the MUAPs average obtained by spike triggered
        average.
    timeinseconds : bool, default True
        Whether to show the time on the x-axes in seconds (True)
        or in samples (False).
    figsize : list, default [20, 15]
        Size of the figure in centimeters [width, height].
    showimmediately : bool, default True
        If True (default), plt.show() is called and the figure showed to the
        user.
        It is useful to set it to False when calling the function from the GUI.
    tight_layout : bool, default True
        If True (default), the plt.tight_layout() is called and the figure's
        layout is improved.
        It is useful to set it to False when calling the function from the GUI.

    Returns
    -------
    fig : pyplot `~.figure.Figure`

    See also
    --------
    - plot_muaps : Plot MUAPs obtained from STA from one or multiple MUs.
    - st_muap : Generate spike triggered MUAPs of every MUs
        (as input to this function).

    Examples
    --------
    Plot all the consecutive MUAPs of a single MU.
    In this case we are plotting the matrix channel 45 which is placed in
    column 4 ("col3" as Python numbering is base 0).

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> sorted_rawemg = emg.sort_rawemg(
    ...     emgfile,
    ...     code="GR08MM1305",
    ...     orientation=180,
    ...     dividebycolumn=True,
    ... )
    >>> stmuap = emg.st_muap(
    ...     emgfile=emgfile,
    ...     sorted_rawemg=sorted_rawemg,
    ...     timewindow=50,
    ... )
    >>> emg.plot_muap(
    ...     emgfile=emgfile,
    ...     stmuap=stmuap,
    ...     munumber=1,
    ...     column="col3",
    ...     channel=45,
    ...     channelprog=False,
    ...     average=False,
    ...     timeinseconds=True,
    ...     figsize=[20, 15],
    ...     showimmediately=True,
    ... )

    To avoid the problem of remebering which channel number is present in
    which matrix column, we can set channelprog=True and locate the channel
    with a value ranging from 0 to the length of each column.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> sorted_rawemg = emg.sort_rawemg(
    ...     emgfile=emgfile,
    ...     code="GR08MM1305",
    ...     orientation=180,
    ...     dividebycolumn=True,
    ... )
    >>> stmuap = emg.st_muap(
    ...     emgfile=emgfile,
    ...     sorted_rawemg=sorted_rawemg,
    ...     timewindow=50,
    ... )
    >>> emg.plot_muap(
    ...     emgfile=emgfile,
    ...     stmuap=stmuap,
    ...     munumber=1,
    ...     column="col3",
    ...     channel=5,
    ...     channelprog=True,
    ...     average=False,
    ...     timeinseconds=True,
    ...     figsize=[20, 15],
    ...     showimmediately=True,
    ... )

    It is also possible to visualise the spike triggered average
    of the MU with average=True.
    In this example the single differential derivation is used.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> sorted_rawemg = emg.sort_rawemg(
    ...     emgfile=emgfile,
    ...     code="GR08MM1305",
    ...     orientation=180,
    ...     dividebycolumn=True,
    ... )
    >>> sorted_rawemg = emg.diff(sorted_rawemg=sorted_rawemg)
    >>> stmuap = emg.st_muap(
    ...     emgfile=emgfile,
    ...     sorted_rawemg=sorted_rawemg,
    ...     timewindow=50,
    ... )
    >>> emg.plot_muap(
    ...     emgfile=emgfile,
    ...     stmuap=stmuap,
    ...     munumber=1,
    ...     column="col2",
    ...     channel=6,
    ...     channelprog=True,
    ...     average=True,
    ...     timeinseconds=True,
    ...     figsize=[20, 15],
    ...     showimmediately=True,
    ... )
    """

    # Check if munumber is within the number of MUs
    if munumber >= emgfile["NUMBER_OF_MUS"]:
        raise ValueError(
            "munumber exceeds the the number of MUs in the emgfile ({})".format(
                emgfile["NUMBER_OF_MUS"]
            )
        )

    # Get the MUAPs to plot
    if channelprog:
        keys = list(stmuap[munumber][column].keys())

        # Check that the specified channel is within the matrix column range
        if channel >= len(keys):
            raise ValueError(
                "Channel exceeds the the length of the matrix column, verify the use of channelprog"
            )

        my_muap = stmuap[munumber][column][keys[channel]]
        channelnumb = keys[channel]

    else:
        keys = list(stmuap[munumber][column].keys())

        # Check that the specified channel is within the matrix channels
        if channel not in keys:
            raise ValueError(
                "Channel is not included in this matrix column, please check"
            )

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

    return fig


def plot_muaps_for_cv(
    sta_dict,
    xcc_sta_dict,
    title="MUAPs for CV",
    figsize=[20, 15],
    showimmediately=True,
    tight_layout=False,
):
    """
    Visualise MUAPs on which to calculate MUs CV.

    Plot MUAPs obtained from the STA of the double differential signal and
    their paired cross-correlation value.

    Parameters
    ----------
    sta_dict : dict
        dict containing the STA of the double-differential derivation of a
        specific MU.
    xcc_sta_dict : dict
        dict containing the normalised cross-correlation coefficient of the
        double-differential derivation of a specific MU.
    title : str, default "MUAPs from STA"
        Title of the plot.
    figsize : list, default [20, 15]
        Size of the figure in centimeters [width, height].
    showimmediately : bool, default True
        If True (default), plt.show() is called and the figure showed to the
        user.
        It is useful to set it to False when calling the function from the GUI.
    tight_layout : bool, default False
        If True (default), the plt.tight_layout() is called and the figure's
        layout is improved.
        It is useful to set it to False when calling the function from the GUI
        or if the final layout is not correct.

    Returns
    -------
    fig : pyplot `~.figure.Figure`

    Examples
    --------
    Plot the double differential derivation and the XCC of adjacent channels
    for the first MU (0).

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
    >>> fig = emg.plot_muaps_for_cv(
    ...     sta_dict=sta[0],
    ...     xcc_sta_dict=xcc_sta[0],
    ...     showimmediately=True,
    ... )
    """

    if not isinstance(sta_dict, dict):
        raise TypeError("sta_dict must be a dict")

    # Find the largest and smallest value to define y axis limits.
    ymax = 0
    ymin = 0
    # Loop each column (c)
    for c in sta_dict:
        max_ = sta_dict[c].max().max()
        min_ = sta_dict[c].min().min()
        if max_ > ymax:
            ymax = max_
        if min_ < ymin:
            ymin = min_

    # Obtain number of columns and rows, this changes if we use different
    # matrices.
    cols = len(sta_dict)
    rows = len(sta_dict["col0"].columns)
    fig, axs = plt.subplots(
        rows,
        cols,
        figsize=(figsize[0] / 2.54, figsize[1] / 2.54),
        num=title,
        sharex=True,
    )

    # Plot all the MUAPs, c means matrix columns, r rows
    keys = list(sta_dict.keys())
    # Manage exception of arrays instead of matrices and check that they
    # are correctly oriented.
    if cols > 1 and rows > 1:
        for r in range(rows):
            for pos, c in enumerate(keys):
                axs[r, pos].plot(sta_dict[c].iloc[:, r])

                axs[r, pos].set_ylim(ymin, ymax)
                axs[r, pos].xaxis.set_visible(False)
                axs[r, pos].set(yticklabels=[])
                axs[r, pos].tick_params(left=False)

                if r != 0:
                    xcc = round(xcc_sta_dict[c].iloc[:, r].iloc[0], 2)
                    title = xcc
                    color = "k" if xcc >= 0.8 else "r"
                    axs[r, pos].set_title(
                        title, fontsize=8, color=color, loc="left", pad=3
                    )

                else:
                    axs[r, pos].set_title(c, fontsize=12, pad=20)

                axs[r, pos].set_ylabel(r, fontsize=6, rotation=0, labelpad=0)

    elif cols == 1 and rows > 1:
        for r in range(rows):
            for pos, c in enumerate(keys):
                axs[r].plot(sta_dict[c].iloc[:, r])

                axs[r].set_ylim(ymin, ymax)
                axs[r].xaxis.set_visible(False)
                axs[r].set(yticklabels=[])
                axs[r].tick_params(left=False)

                if r != 0:
                    xcc = round(xcc_sta_dict[c].iloc[:, r].iloc[0], 2)
                    title = xcc
                    color = "k" if xcc >= 0.8 else "r"
                    axs[r].set_title(
                        title, fontsize=8, color=color, loc="left", pad=3
                    )

                else:
                    axs[r].set_title(c, fontsize=12, pad=20)

                axs[r].set_ylabel(r, fontsize=6, rotation=0, labelpad=0)

    elif cols > 1 and rows == 1:
        raise ValueError(
            "Arrays should be organised as 1 column, multiple rows. " +
            "Not as 1 row, multiple columns."
        )

    else:
        raise ValueError(
            "Unacceptable number of rows and columns to plot"
        )

    showgoodlayout(tight_layout=False, despined=True)
    if showimmediately:
        plt.show()

    return fig
