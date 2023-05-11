Description
-----------
This module contains all the functions that are necessary to open or save
MATLAB (.mat), JSON (.json) or custom (.csv) files.<br>
MATLAB files are used to store data from the DEMUSE and the OTBiolab+
software while JSON files are used to save and load files from this
library.<br>
The choice of saving files in the open standard JSON file format was
preferred over the MATLAB file format since it has a better integration
with Python and has a very high cross-platform compatibility.

Function's scope
----------------
- **emg_from_samplefile**:<br>
    Used to load the sample file provided with the library.
- **emg_from_otb** and **emg_from_demuse**:<br>
    Used to load .mat files coming from the DEMUSE or the OTBiolab+
    software. Demuse has a fixed file structure while the OTB file, in
    order to be compatible with this library should be exported with a
    strict structure as described in the function emg_from_otb.
    In both cases, the input file is a .mat file.
- **refsig_from_otb**:<br>
    Used to load files from the OTBiolab+ software that contain only
    the REF_SIGNAL.
- **emg_from_customcsv**:<br>
    Used to load custom file formats contained in .csv files.
- **save_json_emgfile**, **emg_from_json**:<br>
    Used to save the working file to a .json file or to load the .json
    file.
- **askopenfile**, **asksavefile**:<br>
    A quick GUI implementation that allows users to select the file to
    open or save.

Notes
-----
Once opened, the file is returned as a dictionary with keys:<br>

"SOURCE" : source of the file (i.e., "DEMUSE", "OTB", "custom")<br>
"RAW_SIGNAL" : the raw EMG signal<br>
"REF_SIGNAL" : the reference signal<br>
"PNR" : pulse to noise ratio<br>
"SIL" : silouette score<br>
"IPTS" : pulse train<br>
"MUPULSES" : instants of firing<br>
"FSAMP" : sampling frequency<br>
"IED" : interelectrode distance<br>
"EMG_LENGTH" : length of the emg file (in samples)<br>
"NUMBER_OF_MUS" : total number of MUs<br>
"BINARY_MUS_FIRING" : binary representation of MUs firings<br>

The only exception is when OTB files are loaded with just the reference signal:

"SOURCE": source of the file (i.e., "OTB_refsig")<br>
"FSAMP": sampling frequency<br>
"REF_SIGNAL": the reference signal<br>

Additional informations can be found in the
[info module](API_info.md#openhdemg.library.info.info.data) and in the
function's description.

<br/>

::: openhdemg.library.openfiles.emg_from_samplefile
    options:
        show_root_full_path: False
        show_root_heading: True

<br/>

::: openhdemg.library.openfiles.emg_from_otb
    options:
        show_root_full_path: False
        show_root_heading: True

<br/>

::: openhdemg.library.openfiles.refsig_from_otb
    options:
        show_root_full_path: False
        show_root_heading: True

<br/>

::: openhdemg.library.openfiles.emg_from_demuse
    options:
        show_root_full_path: False
        show_root_heading: True

<br/>

::: openhdemg.library.openfiles.emg_from_customcsv
    options:
        show_root_full_path: False
        show_root_heading: True

<br/>

::: openhdemg.library.openfiles.save_json_emgfile
    options:
        show_root_full_path: False
        show_root_heading: True

<br/>

::: openhdemg.library.openfiles.emg_from_json
    options:
        show_root_full_path: False
        show_root_heading: True

<br/>

::: openhdemg.library.openfiles.askopenfile
    options:
        show_root_full_path: False
        show_root_heading: True

<br/>

::: openhdemg.library.openfiles.asksavefile
    options:
        show_root_full_path: False
        show_root_heading: True

<br/>
