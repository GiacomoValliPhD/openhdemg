import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from tools import compute_idr


def showgoodlayout(despined= False):
    if despined == False:
        sns.despine()
    elif despined == True:
        sns.despine(top=True, bottom=True, left=True, right=True)
    
    plt.tight_layout()
    plt.show()

def plot_emgsig(emgfile, channels, timeinseconds=True):
    """ 
    This function plots the raw EMG signal. It can plot a single or multiple channels.

    The first argument should be the emgfile.
    
    A list of channels can be passed in input as a manually-written list or with:
    channels=[*range(0, 12)], 
    We need the "*" operator to unpack the results of range and build a list.

    The x-axes can be shown in seconds if timeinseconds=False or samples if True.
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
            fig = plt.figure(f"Channel n.{channels}", figsize=(20/2.54, 15/2.54))
            ax = sns.lineplot(x=x_axis, y=emgsig[channels])
            ax.set_ylabel("Ch {}".format(channels)) # Useful because if the channe is empty it won't show the channel number
            ax.set_xlabel("Time (s)" if timeinseconds else "Samples")
            
            showgoodlayout()

        elif isinstance(channels, list):
            """ 
            A list can be passed in input as a manually-written list or with:
            channels=[*range(0, 12)]
            We need the "*" operator to unpack the results of range and build a list 
            """
            figname = "Channels n.{}".format(channels)
            fig, axes = plt.subplots(len(channels), 1, figsize=(20/2.54, 15/2.54), num=figname)

            # Plot all the channels in the subplots, up to 12 channels are clearly visible
            for count, channel in enumerate(channels):
                ax = sns.lineplot(x=x_axis, y=emgsig[channel], ax=axes[count])
                ax.set_ylabel(channel)
                
                # Remove all the unnecessary for nice and clear plotting
                if channel != channels[-1]:
                    ax.xaxis.set_visible(False)
                    ax.set(yticklabels=[])
                    ax.tick_params(left=False)

                else:
                    ax.set(yticklabels=[])
                    ax.tick_params(left=False)

            showgoodlayout(despined= True)
        
        else:
            print("Error: while calling the plot_emgsig function, you should pass an integer or a list to channels= ")
        
    else:
        print("RAW_SIGNAL is probably absent or it is not contained in a dataframe")

def plot_refsig(emgfile, timeinseconds=True):
    """ 
    This function plots the reference (force) signal. The reference signal is expected to be expressed as % MViF.

    The first argument should be the emgfile.
    
    The x-axes can be shown in seconds if timeinseconds=False or samples if True.
    """
    # Check to have the reference signal in a pandas dataframe
    if isinstance(emgfile["REF_SIGNAL"], pd.DataFrame):
        refsig = emgfile["REF_SIGNAL"]

        # Here we produce an x axis in seconds or samples
        if timeinseconds:
            x_axis = refsig.index / emgfile["FSAMP"]
        else:
            x_axis = refsig.index

        fig = plt.figure("Reference signal", figsize=(20/2.54, 15/2.54))
        ax = sns.lineplot(x=x_axis, y=refsig[0])
        ax.set_ylabel("% MViF")
        ax.set_xlabel("Time (s)" if timeinseconds else "Samples")
            
        showgoodlayout()
    
    else:
       print("REF_SIGNAL is probably absent or it is not contained in a dataframe") 

def plot_mupulses(emgfile, linewidths=0.5, timeinseconds=True, order=False, addrefsig=True):
    """ 
    This function plots the MUs pulses (i.e., binary firing point).

    The first argument should be the emgfile.

    The width of the lines can be adjusted with linewidths=
    
    The x-axes can be shown in seconds if timeinseconds=False or samples if True.

    The reference signal is also shown if addrefsig=True and it is expected to be expressed as % MViF.
    """
    # Check to have the reference signal in a pandas dataframe
    if isinstance(emgfile["MUPULSES"], list):
        mupulses = emgfile["MUPULSES"]

        # Convert x axes in seconds if timeinseconds==True (always check if the reference signal is present)
        # This has to be done both for the reference signal and the mupulses, for the mupulses
        # we need to convert the point of firing from samples to seconds
        if timeinseconds:
            if isinstance(emgfile["REF_SIGNAL"], pd.DataFrame):
                emgfile["REF_SIGNAL"].index = emgfile["REF_SIGNAL"].index/emgfile["FSAMP"]
            
            mupulses = [n/emgfile["FSAMP"] for i, n in enumerate(emgfile["MUPULSES"])]

        # Sort the mupulses based on order of recruitment. If True mupulses are sorted in ascending order
        if order and emgfile["NUMBER_OF_MUS"] > 1:
            mupulses = sorted(mupulses, key=min, reverse=False)
        
        # Create colors list for the firings and plot them
        colors1 = ['C{}'.format(i) for i in range(emgfile["NUMBER_OF_MUS"])]

        fig = plt.figure("MUs pulses", figsize=(20/2.54, 15/2.54))

        # Plot ref signal and mupulses if both are available, otherwise only mupulses
        if isinstance(emgfile["REF_SIGNAL"], pd.DataFrame) and addrefsig:
            # Assign 90% of the space in the plot to linelengths and 8% to lineoffsets, 2% free
            linelengths = (max(emgfile["REF_SIGNAL"][0]) * 0.9) / emgfile["NUMBER_OF_MUS"]
            lineoffsets = linelengths + (max(emgfile["REF_SIGNAL"][0]) * 0.08) / emgfile["NUMBER_OF_MUS"]
            
            if emgfile["NUMBER_OF_MUS"] == 1:
                lineoffsets = linelengths/2
            
            ax1 = plt.eventplot(mupulses, linewidths=linewidths, linelengths=linelengths, lineoffsets=lineoffsets, colors=colors1)
            ax2 = plt.plot(emgfile["REF_SIGNAL"], color="0.4")
            
            plt.ylabel("% MViF")

        else:    
            ax1 = plt.eventplot(mupulses, linewidths=linewidths, linelengths=0.9, lineoffsets=1, colors=colors1)
            plt.ylabel("MUs")
        
        plt.xlabel("Time (s)" if timeinseconds else "Samples")

        showgoodlayout()

    else:
       print("MUPULSES is probably absent or it is not contained in a list")

def plot_ipts(emgfile, munumber, timeinseconds=True):
    """ 
    This function plots the impuls train (i.e., non-binary firing).

    The first argument should be the emgfile.
    
    A list of MUs can be passed in input as a manually-written list or with:
    munumber=[*range(0, 12)], 
    We need the "*" operator to unpack the results of range and build a list.
    
    The x-axes can be shown in seconds if timeinseconds=False or samples if True.
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
            fig = plt.figure(f"Motor unit n.{munumber}", figsize=(20/2.54, 15/2.54))
            ax = sns.lineplot(x=x_axis, y=ipts[munumber])
            ax.set_ylabel("MU {}".format(munumber)) # Useful because if the MU is empty it won't show the channel number
            ax.set_xlabel("Time (s)" if timeinseconds else "Samples")
            
            showgoodlayout()

        elif isinstance(munumber, list):
            """ 
            A list can be passed in input as a manually-written list or with:
            munumber=[*range(0, 12)]
            We need the "*" operator to unpack the results of range and build a list 
            """
            figname = "Motor unit n.{}".format(munumber)
            fig, axes = plt.subplots(len(munumber), 1, figsize=(20/2.54, 15/2.54), num=figname)

            # Plot all the MUs in the subplots
            for count, thisMU in enumerate(munumber):
                ax = sns.lineplot(x=x_axis, y=ipts[thisMU], ax=axes[count])
                ax.set_ylabel(thisMU)
                
                # Remove all the unnecessary for nice and clear plotting
                if thisMU != munumber[-1]:
                    ax.xaxis.set_visible(False)
                    ax.set(yticklabels=[])
                    ax.tick_params(left=False)

                else:
                    ax.set(yticklabels=[])
                    ax.tick_params(left=False)

            showgoodlayout(despined= True)
        
        else:
            print("Error: while calling the plot_ipts function, you should pass an integer or a list in munumber= ")
        
    else:
        print("IPTS is probably absent or it is not contained in a dataframe")

def plot_idr(emgfile, munumber, timeinseconds=True, addrefsig=True):
    """ 
    This function plots the instantaneous discharge rate.

    The first argument should be the emgfile.
    
    A list of MUs can be passed in input as a manually-written list or with:
    munumber=[*range(0, 12)], 
    We need the "*" operator to unpack the results of range and build a list.
    
    The x-axes can be shown in seconds if timeinseconds=False or samples if True.
    """
    # Compute the instantaneous discharge rate (IDR) from the MUPULSES
    idr = compute_idr(emgfile = emgfile)

    # Check if we have a single MU or a list of MUs to plot
    if isinstance(munumber, int):
        fig = plt.figure(f"Motor unit n.{munumber}", figsize=(20/2.54, 15/2.54))
        ax = sns.scatterplot(x=idr[munumber]["timesec" if timeinseconds else "mupulses"], y= idr[munumber]["idr"])

        """ if addrefsig:
            if isinstance(emgfile["REF_SIGNAL"], pd.DataFrame):
                if timeinseconds:
                    emgfile["REF_SIGNAL"].index = emgfile["REF_SIGNAL"].index/emgfile["FSAMP"]

            else:
                print("REF_SIGNAL is absent or it is not contained in a dataframe")

            plt.plot(emgfile["REF_SIGNAL"], color="0.4") """

        ax.set_ylabel("MU {}".format(munumber)) # Useful because if the MU is empty it won't show the channel number
        ax.set_xlabel("Time (s)" if timeinseconds else "Samples")
        
        showgoodlayout()
    
    elif isinstance(munumber, list):
        """ 
        A list can be passed in input as a manually-written list or with:
        munumber=[*range(0, 12)]
        We need the "*" operator to unpack the results of range and build a list 
        """
        figname = "Motor unit n.{}".format(munumber)
        fig, axes = plt.subplots(len(munumber), 1, figsize=(20/2.54, 15/2.54), num=figname)
        # Plot all the MUs in the subplots
        for count, thisMU in enumerate(munumber):
            ax = sns.scatterplot(x=idr[thisMU]["timesec" if timeinseconds else "mupulses"], y=idr[thisMU]["idr"], ax=axes[count])
            ax.set_ylabel(thisMU)
            
            # Remove all the unnecessary for nice and clear plotting
            if thisMU != munumber[-1]:
                ax.xaxis.set_visible(False)
                ax.set(yticklabels=[])
                ax.tick_params(left=False)
            else:
                ax.set(yticklabels=[])
                ax.tick_params(left=False)
        
        showgoodlayout(despined= True)
    
    else:
            print("Error: while calling the plot_idr function, you should pass an integer or a list in munumber= ")



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
    #plot_refsig(emgfile=emgfile)
    #plot_mupulses(emgfile=emgfile, order=True, addrefsig=True)
    #plot_ipts(emgfile=emgfile, munumber=[*range(4, 6)]) # We need the "*" to unpack the results of range and build a list - *range(0, 12)
    plot_idr(emgfile=emgfile, munumber=2, timeinseconds=True)
    