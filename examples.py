""" 
------------------------------------------------------------------------------------------------
------------------------------------ Welcome to Open_HD-EMG ------------------------------------
--------------------- a free and open source framework for HD-EMG analysis ---------------------
------------------------------------------------------------------------------------------------
Authors: 
Giacomo Valli   -> (University of Padova) giacomo.valli@phd.unipd.it
                    For library implementation
Paul Ritsche    -> (University of Basel) paul.ritsche@unibas.ch
                    For GUI implementation
------------------------------------------------------------------------------------------------

This tutorial is aimed at those using the library for the first time. Users with a minimum
experience with python, should already have all the knowledge necessary to follow this tutorial.

If this is your first time using python, instructions on how to set-up your python environment,
create virtual environments and install all the necessary packages can be found in the online 
documentation.

All the library has been built to provide all the necessary functions to analyse HD-EMG
recordings with few lines of code. The library can be used to open, modify and analyse both
MUs properties and force profile. Funtions for visualisation (plotting) specific for HD-EMG
users are also provided.

Sample files necessary to test this code can be downloade from:
#TODO
"""

# Step 0: load the library and its functions
import openhdemg as emg

# Step 1: load your file coming from OTBiolab+ from GUI
emgfile = emg.askopenfile(filesource="OTB")
"""
Alternatively, the file can be opened without using a GUI as:
emgfile = emg.emg_from_otb(filepath="/Decomposed Test files/OTB_25MViF_TRAPEZOIDAL_testfile.mat")

The returned file is called emgfile for convention or emg_refsig if we only loaded the reference
signal.

emgfile is a python dictionary containing:
    {
    "SOURCE": SOURCE,
    "RAW_SIGNAL": RAW_SIGNAL,
    "REF_SIGNAL": REF_SIGNAL,
    "PNR": PNR,
    "IPTS": IPTS,
    "MUPULSES": MUPULSES,
    "FSAMP": FSAMP,
    "IED": IED,
    "EMG_LENGTH": EMG_LENGTH,
    "NUMBER_OF_MUS": NUMBER_OF_MUS,
    "BINARY_MUS_FIRING": BINARY_MUS_FIRING,
    }

emg_refsig is a python dictionary containing:
    {
    "SOURCE": SOURCE,
    "FSAMP": FSAMP,
    "REF_SIGNAL": REF_SIGNAL,
    }

You can access any key by name as:
    res =  emgfile["IPTS"]

To visualise what there is inside and what it is:
    print(res)
                0         1         2         3
    0     -0.000103  1.663745  0.009211  0.240553
    1     -0.085057  0.100281  0.198663 -0.093538
    2     -0.035111 -0.017855 -0.045185  0.602539
    3      0.289869  0.051465 -0.069350 -0.118240
    4      0.224776 -0.081736 -0.003066 -0.001913
    ...         ...       ...       ...       ...
    63483  0.000000  0.000000  0.000000  0.000000
    63484  0.000000  0.000000  0.000000  0.000000
    63485  0.000000  0.000000  0.000000  0.000000
    63486  0.000000  0.000000  0.000000  0.000000
    63487  0.000000  0.000000  0.000000  0.000000

    [63488 rows x 4 columns]

    print(type(res))
    <class 'pandas.core.frame.DataFrame'>
"""

# Step 2: visualise MUPULSES
emg.plot_mupulses(emgfile=emgfile)

# Step 3: compute all the mus properties on a trapezoidal contraction
results = emg.basic_mus_properties(emgfile=emgfile)
"""
The function basic_mus_properties will show you the reference signal and ask to select the
steady-state phase (click a keybord key to select, mouse right click to deselect. Press 
enter when satisfied).

Then you will be requested to enter the MViF in the terminal, press enter when satisfied.
    
    print(results)
         MVC  MU_number      abs_RT    abs_DERT     rel_RT   rel_DERT    DR_rec  DR_derec  DR_start_steady  DR_end_steady  DR_all_steady     DR_all  COVisi_steady  COVisi_all  COV_steady
    0  333.0          1  608.297117  522.472243  18.620979  15.993738  5.701081  4.662196         7.386206       6.328858       6.929079   6.814342      11.359317   16.309681    1.339767
    1    NaN          2  146.377683  191.859357   4.480863   5.873132  7.051127  6.752467        14.872484      10.155221      11.957891  11.683134      16.707256   21.233615         NaN
    2    NaN          3  335.771578  371.421870  10.278522  11.369837  6.101529  4.789000         8.051849       5.818215       7.713086   8.055731      35.717607   35.308650         NaN
    3    NaN          4  146.377683  153.627211   4.480863   4.702783  6.345692  5.333535        11.429030       9.658024      11.596454  11.109796      24.280790   29.372524         NaN

The results can be easily saved to a .cvs file with:
    results.to_csv("mypath/results.csv")
"""

# Great! 4 lines of code have been sufficient to analyse your MUs.
# But of course there is much more that we can do.
"""
We can load files coming from OTBiolab+ (as seen), but also form the DEMUSE software.
Also in this case, files can be loaded using a GUI or by specific functions.

Available functions to load files are:
    emg_from_otb : load file exported from OTB (please refer to the official documentation
        of this function to know how to export files from OTBiolab+)
    refsig_from_otb : load file exported from OTB containing only the reference signal
        (please refer to the official documentation of this function to know how to export 
        files from OTBiolab+)
    emg_from_demuse : load decomposed DEMUSE file
    emg_from_json : load files in JSON format. .json files are created with this library.
        They can be used to save original files modified by the user (see below).

Files that have modified by the user, can be save with:
    save_json_emgfile : saves the file in JSON format (.json)
"""

# Now, try to modify the original file and save the changes in a new file
# 