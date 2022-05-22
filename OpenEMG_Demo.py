""" 
------------------------------------------------------------------------------------------------
-------------------------------------- Welcome to OpenEMG --------------------------------------
--------------------- a free and open source framework for HD-EMG analysis ---------------------
------------------------------------------------------------------------------------------------
----------- Author: Giacomo Valli (University of Padova) giacomo.valli@phd.unipd.it ------------
------------------------------------------------------------------------------------------------
"""

""" 
Step 0: we need to import the functions used in this demo. All the function are stored in the files:
    OpenEMG_openfilesLIB    (to open the decomposed files)
    OpenEMG_analysisLIB     (to analyse the EMG and force signal)
    .
    .
    .
We can import the entire library wit:   from library_file_name import *
or only the necessary funtions with:    from library_file_name import function_name

To know all the functions and how to use them please refer to the official documentation.
"""
from OpenEMG_openfilesLIB import *
from OpenEMG_analysisLIB import *

""" 
Permanently changes the pandas visualisation settings to display all the results
"""
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)

""" 
Step 1: open the decomposed EMG file. This should be a Matlab (.mat) file coming from the softwares DEMUSE and OTBioLab+

To open the file simply call the corresponding function:
    emg_from_DEMUSE ==> for DEMUSE output
    emg_from_OTB    ==> for OTB output
The only input necessary is the file path (file extension included)

There are at least two ways to open a file:
1- file path and file name coded (example below) --> please be careful to use "/" and not "\"
2- browse the folder and files and select the one you want to open (below commented out with ")
"""

import os, sys

file_toOpen = os.path.join(sys.path[0], "Decomposed Test files/DEMUSE_10MViF_TRAPEZOIDAL_testfile.mat") # Test it on a common trapezoidal contraction


""" 
import tkinter
from tkinter import filedialog

def openfile_gui():
    root = tkinter.Tk()
    root.wm_withdraw() # this completely hides the root window that remains opened and is annoying
    file_toOpen = filedialog.askopenfilename()
    root.destroy() # this destroys the root window
    
    return file_toOpen

file_toOpen = openfile_gui()
"""


""" 
Step 2: extract all the variables from a file originating from DEMUSE (below) or from OTBioLab+ in the next example 
"""
SOURCE, RAW_SIGNAL, REF_SIGNAL, PNR, IPTS, MUPULSES, FSAMP, IED, EMG_LENGTH, NUMBER_OF_MUS, BINARY_MUS_FIRING = emg_from_DEMUSE(file=file_toOpen)

""" 
Step 3: compute the basic MUs properties (e.g., Recruitment threshold and discharge rate) of a trapezoidal contraction. 
Read the the documentation to understand the input parameters.
"""
df_basic_MUs_properties = basic_MUs_properties(SOURCE, NUMBER_OF_MUS, PNR, MUPULSES, REF_SIGNAL, FSAMP, 
                                                n_firings_RecDerec = 4, # Can be omitted. If not specified n_firings_RecDerec = 4
                                                n_firings_steady = 10   # Can be omitted. If not specified n_firings_steady (start/end) = 10
                                                ) 




""" 
Start over and use the .mat file exported from OTBioLab+ 

Step 1: open the decomposed EMG file
Step 2: extract all the variables
Step 3: compute the basic MUs properties of a trapezoidal contraction
"""
file_toOpen = os.path.join(sys.path[0], "Decomposed Test files/OTB_25MViF_TRAPEZOIDAL_testfile.mat") # Test it on a common trapezoidal contraction

SOURCE, RAW_SIGNAL, REF_SIGNAL, PNR, IPTS, MUPULSES, FSAMP, IED, EMG_LENGTH, NUMBER_OF_MUS, BINARY_MUS_FIRING = emg_from_OTB(file=file_toOpen, refsig=[True, "filtered"])

df_basic_MUs_properties = basic_MUs_properties(SOURCE, NUMBER_OF_MUS, PNR, MUPULSES, REF_SIGNAL, FSAMP, 
                                                n_firings_RecDerec = 4, # Can be omitted. If not specified n_firings_RecDerec = 4
                                                n_firings_steady = 10   # Can be omitted. If not specified n_firings_steady (start/end) = 10
                                                ) 
