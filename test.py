import os, sys
from openhdemg.openfiles import emg_from_demuse, emg_from_otb
from openhdemg.analysis import basic_mus_properties
from openhdemg.plotemg import plot_idr
import numpy as np
	# Test DEMUSE file
file_toOpen = os.path.join(sys.path[0], "C:/Users/admin/Documents/OpenEMG/Open_HD-EMG/openhdemg/Decomposed Test files/DEMUSE_10MViF_TRAPEZOIDAL_testfile.mat") # Test it on a common trapezoidal contraction
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