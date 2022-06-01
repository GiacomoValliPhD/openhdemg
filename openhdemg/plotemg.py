import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

def showgoodlayout():
    sns.despine()
    plt.tight_layout()
    plt.show()

def showfullydespinedlayout():
    sns.despine(top=True, bottom=True, left=True, right=True)
    plt.tight_layout()
    plt.show()

def plot_emgsig(emgfile, channels, timeinseconds=True):
    # Check to have the raw EMG signal in a pandas dataframe
    if isinstance(emgfile["RAW_SIGNAL"], pd.DataFrame):
        # Transpose it for quick plotting by column
        emgsig = emgfile["RAW_SIGNAL"].transpose()

        # Here I produce an x axis in seconds or samples
        if timeinseconds == True:
            x_axis = emgsig.index / emgfile["FSAMP"]
        else:
            x_axis = emgsig.index

        # Check if we have a single channel or a list of channels to plot
        if isinstance(channels, int):
            fig = plt.figure(f"Channel n.{channels}", figsize=(20/2.54, 15/2.54))
            ax = sns.lineplot(x=x_axis, y=emgsig[channels])
            ax.set_ylabel("Ch {}".format(channels)) # Useful because if the channe is empty it won't show the channel number
            
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

            showfullydespinedlayout()
        
        else:
            print("Error: while calling the plot_emgsig function, you should pass an integer or a list in channels= ")
        
    else:
        print("RAW_SIGNAL is probably absent or it is not contained in a dataframe")








if __name__ == "__main__":
    import os, sys
    from openfiles import emg_from_demuse, emg_from_otb
    from analysis import basic_mus_properties
    import numpy as np

    file_toOpen = os.path.join(sys.path[0], "Decomposed Test files/DEMUSE_10MViF_TRAPEZOIDAL_testfile.mat") # Test it on a common trapezoidal contraction
    emgfile = emg_from_demuse(file=file_toOpen)
    

    plot_emgsig(emgfile=emgfile, channels=[*range(0, 12)]) # We need the "*" to unpack the results of range and build a list - *range(0, 12)
