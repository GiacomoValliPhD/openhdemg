"""
Module docstring explaining how to change the GUI settings.

The settings can be related to both the GUI appearence and the analyses
functions. Parameters for the analyses functions are clustered based on the
openhdemg library's modules (here described as #----- MODULE NAME -----) and
can be better known from the API section of the openhdemg website.

Each parameter for the analyses functions is named FunctionName__Parameter.
An extensive explanation of each "Parameter" can be found in the specific
API module and in the specific "FunctionName".

A tutorial on how to use this settings file is available at:
# TODO add link to docs tutorial
"""

# These graphic parameters are updated only after restarting the GUI
#
# --------------------------------- GUI LOOK ----------------------------------
background_color = "LightBlue4"
# Options are #TODO Paul please explain what colors can be used, I will add these in the tutorial
#TODO we also must rename this file in something more specific like gui_settings.py


# The following parameters are updated without restarting the GUI
#
# --------------------------------- openfiles ---------------------------------

# in emg_from_demuse()
emg_from_demuse__ignore_negative_ipts = False

# in emg_from_otb()
emg_from_otb__ext_factor = 8
emg_from_otb__refsig = [True, "fullsampled"]
emg_from_otb__extras = None
emg_from_otb__ignore_negative_ipts = False

# in refsig_from_otb()
refsig_from_otb__refsig = "fullsampled"
refsig_from_otb__extras = None

# in emg_from_delsys()
emg_from_delsys__emg_sensor_name = "Galileo sensor"
emg_from_delsys__refsig_sensor_name = "Trigno Load Cell"
emg_from_delsys__filename_from = "mus_directory"

# in refsig_from_delsys()
refsig_from_delsys__refsig_sensor_name = "Trigno Load Cell"

# in emg_from_customcsv()
emg_from_customcsv__ref_signal = "REF_SIGNAL"
emg_from_customcsv__raw_signal = "RAW_SIGNAL"
emg_from_customcsv__ipts = "IPTS"
emg_from_customcsv__mupulses = "MUPULSES"
emg_from_customcsv__binary_mus_firing = "BINARY_MUS_FIRING"
emg_from_customcsv__accuracy = "ACCURACY"
emg_from_customcsv__extras = "EXTRAS"
emg_from_customcsv__fsamp = 2048
emg_from_customcsv__ied = 8
# TODO in main window and in advanced tools, when selecting OTB, delsys and custom CSV write to check settings file

# in refsig_from_customcsv()
refsig_from_customcsv__ref_signal = "REF_SIGNAL"
refsig_from_customcsv__extras = "EXTRAS"

# in save_json_emgfile()
save_json_emgfile__compresslevel = 4


# ---------------------------------- analysis ---------------------------------

# in compute_thresholds()
compute_thresholds__n_firings = 1

# in basic_mus_properties()
basic_mus_properties__n_firings_rt_dert = 1
basic_mus_properties__accuracy = "default"
basic_mus_properties__ignore_negative_ipts = False
basic_mus_properties__constrain_pulses = [True, 3]


# ----------------------------------- tools -----------------------------------

# in resize_emgfile()
resize_emgfile__how = "ref_signal"
resize_emgfile__accuracy = "recalculate"
resize_emgfile__ignore_negative_ipts = False


# ------------------------------------ muap -----------------------------------
# TODO missing custom order (2 variables) in traking and duplicates

# in tracking()
tracking__firings = "all"
tracking__derivation = "sd"

# in remove_duplicates_between()
remove_duplicates_between__firings = "all"
remove_duplicates_between__derivation = "sd"

# in MUcv_gui()
MUcv_gui__n_firings = [0, 50]
MUcv_gui__muaps_timewindow = 50
MUcv_gui__figsize = [25, 20]

# --------------------------------- electrodes --------------------------------
sort_rawemg__custom_sorting_order = None
