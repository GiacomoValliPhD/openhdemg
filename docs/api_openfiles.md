Description
-----------

!!! note "New in version 0.2.0"
    The recommended workflow for saving and loading *openhdemg* data now relies on the following high-level functions and classes for binary files:
    
    - [`save_openhdemg_module`](#openhdemg.library.openfiles.save_openhdemg_module)
    - [`asksavemodule`](#openhdemg.library.openfiles.asksavemodule)
    - [`load_openhdemg_module`](#openhdemg.library.openfiles.load_openhdemg_module)
    - [`askloadmodule`](#openhdemg.library.openfiles.askloadmodule)
    - [`openhdemg_Collection`](#openhdemg.library.openfiles.openhdemg_Collection)

This module contains all the functions that are necessary to open or save *openhdemg* binary files for modules and collections, in addition to MATLAB (.mat), text (.txt), JSON (.json) or custom (.csv) files. MATLAB files are used to store data from a number of software including DEMUSE, OTBiolab+ and Delsys, while JSON files are the older format used by the openhdemg library.

**If you are using an *openhdemg* version >= 0.2, it is recommended to use binary data (modules and collections), as these provide the best performance and flexibility** within the *openhdemg* framework, but also for optimal portability across operating systems and storage in private and public repositories. Indeed, our binary structures allow to compress files and check their integrity, if needed.

The content of the loaded emgfile can differ depending on the file type. In general, decomposed files are dictionaries containing the following keys:<br>

```python
"SOURCE" : source of the file (e.g., "OPENHDEMG", "CUSTOMCSV")
"FILENAME" : the name of the opened file
"RAW_SIGNAL" : the raw EMG signal
"REF_SIGNAL" : the reference signal
"ACCURACY" : accuracy score (depending on source file type)
"IPTS" : pulse train (decomposed source, depending on source file type)
"MUPULSES" : instants of firing
"FSAMP" : sampling frequency
"IED" : interelectrode distance
"EMG_LENGTH" : length of the emg file (in samples)
"NUMBER_OF_MUS" : total number of MUs
"BINARY_MUS_FIRING" : binary representation of MU firings
"EXTRAS" : additional custom values
```

More keys might be present if additional pd.DataFrames or Dictionaries are present in the emgfiles saved with 'save_emgfile_module'.

Similarly, less keys might be present if there is no decomposition result or no EMG signal.

As an example, when files are loaded with just the reference signal:

```python
"SOURCE" : source of the file (i.e., "CUSTOMCSV_REFSIG", "OTB_REFSIG", "DELSYS_REFSIG")
"FILENAME" : the name of the opened file
"FSAMP" : sampling frequency
"REF_SIGNAL" : the reference signal
"EXTRAS" : additional custom values
```

Additional information can be found in the [info module](api_info.md#openhdemg.library.info.data) and in the function's description.

!!! note "Structure of the emgfile"
    To really understand the official structure of the emgfile, all the users are encouraged to read the dedicated tutorial [Structure of the emgfile](tutorials/emgfile_structure.md).

<br/>

::: openhdemg.library.openfiles.save_openhdemg_module
    options:
        show_root_full_path: False
        show_root_heading: True

<br/>

::: openhdemg.library.openfiles.asksavemodule
    options:
        show_root_full_path: False
        show_root_heading: True

<br/>

::: openhdemg.library.openfiles.load_openhdemg_module
    options:
        show_root_full_path: False
        show_root_heading: True

<br/>

::: openhdemg.library.openfiles.askloadmodule
    options:
        show_root_full_path: False
        show_root_heading: True

<br/>

::: openhdemg.library.openfiles.openhdemg_Collection
    options:
        show_root_full_path: False
        show_root_heading: True

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

::: openhdemg.library.openfiles.emg_from_demuse
    options:
        show_root_full_path: False
        show_root_heading: True

<br/>

::: openhdemg.library.openfiles.emg_from_delsys
    options:
        show_root_full_path: False
        show_root_heading: True

<br/>

::: openhdemg.library.openfiles.emg_from_customcsv
    options:
        show_root_full_path: False
        show_root_heading: True

<br/>

::: openhdemg.library.openfiles.refsig_from_otb
    options:
        show_root_full_path: False
        show_root_heading: True

<br/>

::: openhdemg.library.openfiles.refsig_from_delsys
    options:
        show_root_full_path: False
        show_root_heading: True

<br/>

::: openhdemg.library.openfiles.refsig_from_customcsv
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

::: openhdemg.library.openfiles.is_safe_openhdemg_folder
    options:
        show_root_full_path: False
        show_root_heading: True

<br/>

::: openhdemg.library.openfiles.sha256_file
    options:
        show_root_full_path: False
        show_root_heading: True

<br/>
