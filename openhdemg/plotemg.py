import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import copy
from openhdemg.tools import compute_idr
from openhdemg.mathtools import min_max_scaling


def showgoodlayout(despined=False):
    """
    This function is a simple shortcut to despine the plots.

    It takes as input:
    - False: left and bottom is not despined (standard plotting)
    - True: all the sides are despined
    - "2yaxes": only the top is despined. This is used for y axes both on the right and left side at the same time
    """
    # Check the input
    if not isinstance(despined, (bool, str)):
        raise Exception(f"despined can be True, False of 2yaxes. {despined} was passed instead")
    
    if despined == False:
        sns.despine()
    elif despined == True:
        sns.despine(top=True, bottom=True, left=True, right=True)
    elif despined == "2yaxes":
        sns.despine(top=True, bottom=False, left=False, right=False)
    else:
        raise Exception(f"despined can be True, False of 2yaxes. {despined} was passed instead")
    
    plt.tight_layout()


def plot_emgsig(emgfile, channels, timeinseconds=True, figsize=[20,15], showimmediately=True):
    """ 
    This function plots the raw EMG signal. It can plot a single or multiple channels.

    The first argument should be the emgfile.
    
    An integer or a list of channels can be passed in input. The list can be passed as a manually-written list or with:
    channels=[*range(0, 12)], 
    We need the "*" operator to unpack the results of range and build a list.

    The x-axes can be shown in seconds if timeinseconds=False or samples if True.

    figsize can be used to define the plot size in centimeters. Input is a list [width, height].

    showimmediately=True immediately shows the plot by calling plt.show().
    """
    # Check to have the raw EMG signal in a pandas dataframe
    if isinstance(emgfile["RAW_SIGNAL"], pd.DataFrame):
        # Transpose it for quick plotting by column
        emgsig = emgfile["RAW_SIGNAL"]

        # Here we produce an x axis in seconds or samples
        if timeinseconds:
            x_axis = emgsig.index / emgfile["FSAMP"]
        else:
            x_axis = emgsig.index

        # Check if we have a single channel or a list of channels to plot
        if isinstance(channels, int):
            fig = plt.figure(f"Channel n.{channels}", figsize=(figsize[0]/2.54, figsize[1]/2.54))
            ax = sns.lineplot(x=x_axis, y=emgsig[channels])
            ax.set_ylabel("Ch {}".format(channels)) # Useful because if the channe is empty it won't show the channel number
            ax.set_xlabel("Time (s)" if timeinseconds else "Samples")
            
            showgoodlayout()
            if showimmediately: plt.show()

        elif isinstance(channels, list):
            """ 
            A list can be passed in input as a manually-written list or with:
            channels=[*range(0, 12)]
            We need the "*" operator to unpack the results of range and build a list 
            """
            figname = "Channels n.{}".format(channels)
            fig, axes = plt.subplots(len(channels), 1, figsize=(figsize[0]/2.54, figsize[1]/2.54), num=figname)

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

            showgoodlayout(despined= True)
            if showimmediately: plt.show()
        
        else:
            raise Exception("While calling the plot_emgsig function, you should pass an integer or a list to channels= ") 
        
    else:
        raise Exception("RAW_SIGNAL is probably absent or it is not contained in a dataframe") 


def plot_refsig(emgfile, timeinseconds=True, figsize=[20,15], showimmediately=True):
    """ 
    This function plots the reference (force) signal. The reference signal is expected to be expressed as % MViF.

    The first argument should be the emgfile.
    
    The x-axes can be shown in seconds if timeinseconds=False or samples if True.

    figsize can be used to define the plot size in centimeters. Input is a list [width, height].

    showimmediately=True immediately shows the plot by calling plt.show().
    """
    # Check to have the reference signal in a pandas dataframe
    if isinstance(emgfile["REF_SIGNAL"], pd.DataFrame):
        refsig = emgfile["REF_SIGNAL"]

        # Here we produce an x axis in seconds or samples
        if timeinseconds:
            x_axis = refsig.index / emgfile["FSAMP"]
        else:
            x_axis = refsig.index

        fig = plt.figure("Reference signal", figsize=(figsize[0]/2.54, figsize[1]/2.54))
        ax = sns.lineplot(x=x_axis, y=refsig[0])
        ax.set_ylabel("% MViF")
        ax.set_xlabel("Time (s)" if timeinseconds else "Samples")
            
        showgoodlayout()
        if showimmediately: plt.show()
    
    else:
       raise Exception("REF_SIGNAL is probably absent or it is not contained in a dataframe") 


def plot_mupulses(emgfile, linewidths=0.5, timeinseconds=True, order=False, addrefsig=True, figsize=[20,15], showimmediately=True):
    """ 
    This function plots the MUs pulses (i.e., binary firing point).

    The first argument should be the emgfile.

    The width of the lines can be adjusted with linewidths=
    
    The x-axes can be shown in seconds if timeinseconds=False or samples if True.

    The reference signal is also shown if addrefsig=True and it is expected to be expressed as % MViF.

    figsize can be used to define the plot size in centimeters. Input is a list [width, height].
    
    showimmediately=True immediately shows the plot by calling plt.show().
    """
    # Check to have the correct input
    if isinstance(emgfile["MUPULSES"], list):
        # Create a deepcopy to modify mupulses without affecting the original file
        mupulses = copy.deepcopy(emgfile["MUPULSES"])
    else:
        raise Exception("MUPULSES is probably absent or it is not contained in a list")

    if addrefsig:
        if not isinstance(emgfile["REF_SIGNAL"], pd.DataFrame):
            raise Exception("REF_SIGNAL is probably absent or it is not contained in a dataframe")

    # Convert x axes in seconds if timeinseconds==True
    # This has to be done both for the reference signal and the mupulses, for the mupulses
    # we need to convert the point of firing from samples to seconds
    if timeinseconds:
        mupulses = [n/emgfile["FSAMP"] for i, n in enumerate(emgfile["MUPULSES"])]

    # Sort the mupulses based on order of recruitment. If True mupulses are sorted in ascending order
    if order and emgfile["NUMBER_OF_MUS"] > 1:
        mupulses = sorted(mupulses, key=min, reverse=False)
        
    # Create colors list for the firings and plot them
    colors1 = ['C{}'.format(i) for i in range(emgfile["NUMBER_OF_MUS"])]

    # Use the subplot to allow the use of twinx
    fig, ax1 = plt.subplots(figsize=(figsize[0]/2.54, figsize[1]/2.54), num="MUs pulses")

    if addrefsig:
        # Assign 90% of the space in the plot to linelengths and 8% to lineoffsets, 2% free
        linelengths = (max(emgfile["REF_SIGNAL"][0]) * 0.9) / emgfile["NUMBER_OF_MUS"]
        lineoffsets = linelengths + (max(emgfile["REF_SIGNAL"][0]) * 0.08) / emgfile["NUMBER_OF_MUS"]
            
        if emgfile["NUMBER_OF_MUS"] == 1:
            # Specify a different lineoffset if I have only 1 MU
            lineoffsets = linelengths/2
            
        # Plot the mupulses. Use ax1.plot to allow the use of twinx, instead of ax1=plt.eventplot
        ax1.eventplot(mupulses, linewidths=linewidths, linelengths=linelengths, lineoffsets=lineoffsets, colors=colors1)
        
        # Create the second (right) y axes
        ax2 = ax1.twinx()
        xref = emgfile["REF_SIGNAL"].index / emgfile["FSAMP"] if timeinseconds else emgfile["REF_SIGNAL"].index
        sns.lineplot(y=emgfile["REF_SIGNAL"][0], x=xref, color="0.4", ax=ax2)
            
        ax2.set_ylabel("MViF (%)")

    else:    
        ax1.eventplot(mupulses, linewidths=linewidths, linelengths=0.9, lineoffsets=1, colors=colors1)
        
    # Set axes labels
    ax1.set_ylabel("MUs")
    ax1.set_xlabel("Time (Sec)" if timeinseconds else "Samples")

    if addrefsig:
        showgoodlayout(despined="2yaxes")
    else:
        showgoodlayout()

    if showimmediately: plt.show()


def plot_ipts(emgfile, munumber, timeinseconds=True, figsize=[20,15], showimmediately=True):
    """ 
    This function plots the impuls train (i.e., non-binary firing).

    The first argument should be the emgfile.
    
    An integer or a list of MUs can be passed in input. The list can be passed as a manually-written list or with:
    munumber=[*range(0, 12)], 
    We need the "*" operator to unpack the results of range and build a list.
    
    The x-axes can be shown in seconds if timeinseconds=False or samples if True.

    figsize can be used to define the plot size in centimeters. Input is a list [width, height].
    
    showimmediately=True immediately shows the plot by calling plt.show().
    """
    # Check to have the raw EMG signal in a pandas dataframe
    if isinstance(emgfile["IPTS"], pd.DataFrame):
        ipts = emgfile["IPTS"]

        # Here we produce an x axis in seconds or samples
        if timeinseconds:
            x_axis = ipts.index / emgfile["FSAMP"]
        else:
            x_axis = ipts.index

        # Check if we have a single MU or a list of MUs to plot
        if isinstance(munumber, int):
            fig = plt.figure(f"Motor unit n.{munumber}", figsize=(figsize[0]/2.54, figsize[1]/2.54))
            ax = sns.lineplot(x=x_axis, y=ipts[munumber])
            ax.set_ylabel("MU {}".format(munumber)) # Useful because if the MU is empty it won't show the channel number
            ax.set_xlabel("Time (Sec)" if timeinseconds else "Samples")
            
            showgoodlayout()
            if showimmediately: plt.show()

        elif isinstance(munumber, list):
            """ 
            A list can be passed in input as a manually-written list or with:
            munumber=[*range(0, 12)]
            We need the "*" operator to unpack the results of range and build a list 
            """
            figname = "Motor unit n.{}".format(munumber)
            fig, axes = plt.subplots(len(munumber), 1, figsize=(figsize[0]/2.54, figsize[1]/2.54), num=figname)

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

            showgoodlayout(despined= True)
            if showimmediately: plt.show()
        
        else:
            raise Exception("While calling the plot_ipts function, you should pass an integer or a list in munumber= ")
        
    else:
        raise Exception("IPTS is probably absent or it is not contained in a dataframe")


def plot_idr(emgfile, munumber, timeinseconds=True, addrefsig=True, figsize=[20,15], showimmediately=True):
    """ 
    This function plots the instantaneous discharge rate.

    The first argument should be the emgfile.
    
    An integer or a list of MUs can be passed in input. The list can be passed as a manually-written list or with:
    munumber=[*range(0, 12)], 
    We need the "*" operator to unpack the results of range and build a list.
    
    The x-axes can be shown in seconds if timeinseconds=False or samples if True.

    figsize can be used to define the plot size in centimeters. Input is a list [width, height].

    showimmediately=True immediately shows the plot by calling plt.show().
    """
    # Compute the instantaneous discharge rate (IDR) from the MUPULSES and check the input
    idr = compute_idr(emgfile = emgfile)

    if addrefsig:
        if not isinstance(emgfile["REF_SIGNAL"], pd.DataFrame):
            raise Exception("REF_SIGNAL is probably absent or it is not contained in a dataframe")

    # Check if we have a single MU or a list of MUs to plot
    if isinstance(munumber, int):
        fig = plt.figure(f"Motor unit n.{munumber}", figsize=(figsize[0]/2.54, figsize[1]/2.54))
        ax = sns.scatterplot(x=idr[munumber]["timesec" if timeinseconds else "mupulses"], y= idr[munumber]["idr"])

        if addrefsig:
            ax2 = ax.twinx() 
            # Plot the ref signal
            xref = emgfile["REF_SIGNAL"].index / emgfile["FSAMP"] if timeinseconds else emgfile["REF_SIGNAL"].index
            sns.lineplot(y=emgfile["REF_SIGNAL"][0], x=xref, color="0.4", ax=ax2)
            ax2.set_ylabel("MViF (%)")

        ax.set_ylabel("MU {} (pps)".format(munumber)) # Useful because if the MU is empty it won't show the channel number
        ax.set_xlabel("Time (Sec)" if timeinseconds else "Samples")
        
        
        if addrefsig:
            showgoodlayout(despined="2yaxes")
        else:
            showgoodlayout()

        if showimmediately: plt.show()
    
    elif isinstance(munumber, list):
        """
        A list can be passed in input as a manually-written list or with:
        munumber=[*range(0, 12)]
        We need the "*" operator to unpack the results of range and build a list
        """ 
        # Behave differently if you plot both the ref signal and the idr or only the idr
        if not addrefsig:
            figname = "Motor unit n.{}".format(munumber)
            # sharex is fundamental to ensure correct representation of the idr over the different subplots
            fig, axes = plt.subplots(len(munumber), 1, figsize=(figsize[0]/2.54, figsize[1]/2.54), num=figname, sharex=True)
            # Create colors list for the firings and plot them. Loop backward because then you are plotting MUs in reversed order
            colors1 = ['C{}'.format(i) for i in range(emgfile["NUMBER_OF_MUS"]-1, -1, -1)]
            # Plot all the MUs in the subplots. Enumerate reversed munumber to show the first MUs below 
            for count, thisMU in enumerate(reversed(munumber)):
                ax = sns.scatterplot(x=idr[thisMU]["timesec" if timeinseconds else "mupulses"], y=idr[thisMU]["idr"], color=colors1[count], ax=axes[count])
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

            showgoodlayout(despined= True)
            if showimmediately: plt.show()
        
        else:
            # Initialise figure and plots
            figname = "Motor unit n.{}".format(munumber)
            fig, ax1 = plt.subplots(figsize=(figsize[0]/2.54, figsize[1]/2.54), num=figname)
            # Apply twinx to ax2, which is the second y axis.
            ax2 = ax1.twinx() 

            # Plot every MUs. The MUs IDR is normalised in a range 0-1 to allow efficient plotting of the various MUs in the y axes.
            for num, col in enumerate(idr):
                # Normalise the series
                norm_idr = min_max_scaling(idr[col]["idr"])
                # Add 1 compare to the previous MUs to avoid overlapping of the MUs
                norm_idr = norm_idr + num
                
                sns.scatterplot(x=idr[num]["timesec" if timeinseconds else "mupulses"], y=norm_idr, ax = ax1)

            # Then plot the ref signal
            xref = emgfile["REF_SIGNAL"].index / emgfile["FSAMP"] if timeinseconds else emgfile["REF_SIGNAL"].index
            sns.lineplot(y=emgfile["REF_SIGNAL"][0], x=xref, ax=ax2)
            
            # Set axes labels
            ax2.set_ylabel("MViF (%)")
            ax1.set_ylabel("MUs number")
            ax1.set_xlabel("Time (Sec)" if timeinseconds else "Samples")
        
            showgoodlayout(despined="2yaxes")
            if showimmediately: plt.show()
    
    else:
        raise Exception("While calling the plot_idr function, you should pass an integer or a list in munumber= ")



###########################################################################################################################################################
###########################################################################################################################################################
###########################################################################################################################################################
# Test part
if __name__ == "__main__":
    import os, sys
    from openfiles import emg_from_demuse, emg_from_otb
    from analysis import basic_mus_properties
    import numpy as np

    # Test DEMUSE file
    file_toOpen = os.path.join(sys.path[0], "Decomposed Test files/DEMUSE_10MViF_TRAPEZOIDAL_testfile.mat") # Test it on a common trapezoidal contraction
    #file_toOpen = os.path.join(sys.path[0], "Decomposed Test files/DEMUSE_10MViF_TRAPEZOIDAL_only1MU_testfile.mat") # Test it on a contraction with a single MU
    emgfile = emg_from_demuse(file=file_toOpen)

    """ # Test OTB file
    file_toOpen = os.path.join(sys.path[0], "Decomposed Test files/OTB_25MViF_TRAPEZOIDAL_testfile.mat") # Test it on a common trapezoidal contraction
    emgfile = emg_from_otb(file=file_toOpen, refsig=[True, "filtered"]) """
    

    #plot_emgsig(emgfile=emgfile, channels=[*range(0, 12)]) # We need the "*" to unpack the results of range and build a list - *range(0, 12)
    plot_idr(emgfile=emgfile, munumber=[*range(0, emgfile["NUMBER_OF_MUS"])]) 
    #plot_refsig(emgfile=emgfile)
    #plot_mupulses(emgfile=emgfile, order=True, addrefsig=True)
    #plot_ipts(emgfile=emgfile, munumber=[*range(4, 6)]) # We need the "*" to unpack the results of range and build a list - *range(0, 12)
    #plot_idr(emgfile=emgfile, munumber=2, timeinseconds=True)
    