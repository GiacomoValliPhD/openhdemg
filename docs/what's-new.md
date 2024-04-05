## :octicons-tag-24: 0.1.0-beta.4
:octicons-clock-24: April 2024 

This release is aimed at increasing the robustness of the implemented functions and at improving the usability of the graphical user interface (GUI).

### Backward Compatibility

This version is fully backward compatible (with v0.1.0-beta.3) although the PNR (pulse to noise ratio) estimation might slightly differ from the previous versions.

### Major Achievements
- **Much faster**
- **More accurate**
- **More robust**
- **More user-friendly**

### Major Changes

- **Restyled, debugged and more flexible GUI**:

    - Almost all the functioning issues affecting the GUI have been solved. Enjoy a much better experience with this new release.
    - New settings file: it is now possible to customise the functions behaviour directly from the GUI. This increases the number of possible analyses that can be performed from the GUI.
    - New modern look
    - Better responsiveness
    - Expandable main window and figure
    - New modular structure of the source code for easier implementation of new functionalities.

- **Awesome performance improvements**:

    - The estimation of MUs conduction velocity is 96% faster compared to the previous implementation, making it suitable also for the estimation of global conduction velocity.

- **New functions**:

    - The function `estimate_cv_via_mle` has been created to allow the user to estimate CV of any given signal with only 1 line of code.

- **Updated functions**:
    - The function `compute_sil` has a new argument that allows to include or exclude negative source values from the SIL estimation. This increases the estimation robustness when the source has large negative components.
    - The function `compute_pnr` has a new argument that allows to select whether to cluster firings/noise via a heuristic penalty function or by using the provided discharge times.
    - It is now possible to specify how to estimate accuracy in `emg_from_demuse`, `emg_from_otb` and `basic_mus_properties` based on the new implementation of `compute_sil` and `compute_pnr`.
    - The function `sort_rawemg` now allows to sort channels based on custom orders with a custom number of empty channels.
    - The function `resize_emgfile` now allows to select the area to resize based on the reference signal or on the mean EMG signal.
    - The function `delete_mus` now allows to delete also the MUAPs computed in the Delsys software (stored in emgfile[“EXTRAS”]) simultaneously with the removal of MUs firing. This is now the default in the GUI.

- **New modules**: With this release, we introduce dedicated test modules. These will progressively allow for automated extensive testing of the implemented functions and to exit the beta phase. Currently, test functions have been created for the `openfiles` module.

### Other changes

- It is now possible to pass OTB EXTRAS to the function `askopenfile`.
- Improved readability of the string values in the docstrings and in the online documentation.

### Tutorials

- Added new troubleshooting in setup working env
- Added new tutorial explaining how to use the GUI settings

<br>

## :octicons-tag-24: 0.1.0-beta.3
:octicons-clock-24: November 2023

This release is focused on expanding the range of supported input files (decomposition outcomes) and to increase the speed and efficiency of the code. Furthermore, the introduction of a new backward compatibility module brings *openhdemg* a step closer to exiting the beta phase.

### Backward Compatibility

By default, the .json files saved from *openhdemg* version 0.1.0-beta.2 (released in September 2023) cannot be opened in *openhdemg* version 0.1.0-beta.3. However, these files can be easily converted to the newer file format thanks to the new backward compatibility module. We also created a [tutorials section](tutorials/convert_old_json_files.md) where the users are guided to the migration towards newer versions of the library. This will ensure easy migration to the latest *openhdemg* release.

### Major Achievements

- **Extended input file compatibility**: now supporting a wider range of input files, making it easily accessible to anybody.
- **Much faster**: Spend more time on research and less time with tools.
- **Backward compatibility**: enjoy a smooth transition without concerns about compatibility.

### Major Changes

- **Support for Delsys decomposition outcome**: users of the 4 pin Galileo sensors can now directly open and analyze their motor units in *openhdemg*. This will expand the user base of the *openhdemg* framework.

    - New function `emg_from_delsys` to load the Delsys decomposition outcome.
    - New function `refsig_from_delsys` to load the reference signal from Delsys.
    - New function `extract_delsys_muaps` to use the MUAPs computed during Delsys decomposition wherever the MUAPs are necessary.

- **Awesome performance improvements**:

    - The `save_json_emgfile` function has been modified, and it is now possible to adjust the level of compression of the output file. It is now up to 90-95% faster than the previous implementation, with the output file 50% smaller than before and 50% smaller than the corresponding file in .mat format. This will facilitate and promote the adoption of the *openhdemg* file format.
    - The `emg_from_json` function has been modified, and you can now load files 55% faster than the previous implementation. This will facilitate and promote the adoption of the *openhdemg* file format.
    - The function `emg_from_demuse` can now load files 25 to 50% faster than the previous implementation. This will promote the use of other file sources in the *openhdemg* framework.
    - The functions performing spike-triggered averaging (`sta` and `st_muap`) have been optimized and are now 95% faster. This allows for a faster execution of all the functions requiring the MU action potential shape.

- **Backward compatibility**: we introduced a dedicated [module](api_compatibility.md) to ensure backward compatibility starting from this version and going forward. This will permit any user to easily migrate to newer versions of the library.

### Other Changes

- 90% Faster execution of the function `create_binary_firings`.
- Support for arrays: The various functions using MUAPs now support also grids with only one column (arrays of electrodes). This is predisposing *openhdemg* to interface also with arrays and not only with grids.
- MUs conduction velocity estimation now allows to set the size of the figure to make it as large and easy to see as you wish. It also returns which column and rows have been used to estimate conduction velocity. The functions used to estimate conduction velocity will undergo a major optimisation in the next releases to make them faster and more flexible.
- When calculating recruitment and derecruitment thresholds with the functions `compute_thresholds` and `basic_mus_properties`, it is now possible to calculate the thresholds as the average value of n firings.

### Bug Fixes

- Fixed a bug in the `emg.info().data()` function that crashed when called with CUSTOMCSV file sources.
- Class docstrings can now be accessed directly from Visual Studio Code.

### Tutorials

Added new tutorials explaining:

- How to export your decomposed files to directly load them in *openhdemg*.
- How to use the backward compatibility module to easily migrate to the newer *openhdemg* releases.
- In the tutorial “Setup working environment,” we specified that *openhdemg* is currently working with Python up to the 3.11.x version. We are working to make it compatible with Python 3.12.

<br>

## :octicons-tag-24: 0.1.0-beta.2
:octicons-clock-24: September 2023

This release is mainly addressing the necessity of maximum flexibility and easy integration with any custom or proprietary file source. This release is not backward compatible.

### Major changes

- **Accuracy Measurement:** Replaced the double accuracy measures in the `emgfile` (i.e., “SIL” and “PNR”) with a single accuracy measure named “ACCURACY.” For files containing the decomposed source (also named “IPTS”), the “ACCURACY” variable will contain the silhouette score (Negro et al. 2016). For files that do not contain the decomposed source, the accuracy will be the original (often proprietary) accuracy estimate. This allows for maximum flexibility and is fundamental to interface the *openhdemg* library with any proprietary and custom implementation of the different decomposition algorithms currently available.

    To accommodate this change, all the functions in the `openfile` module have been updated. Consequently, the functions using the “SIL” or “PNR” variables have also been modified. Specifically:
    
    - The `basic_mus_properties` function has a new input parameter (i.e., “accuracy”) to customize the returned accuracy estimate.
    - In the function `remove_duplicates_between`, the input parameter “which” now only accepts “munumber” and “accuracy” instead of “munumber,” “SIL,” and “PNR.”

- **EXTRAS Variable:** Introduced a new “EXTRAS” variable to store any custom information in the opened file. This will be accessible in the `emgfile` dictionary with the “EXTRAS” key. This variable must contain a pd.DataFrame structure and will be preserved when saving the file. This change extends the customisability of the `emgfile`.

- **Handling Missing Variables:** Replaced “np.nan” with empty "pd.DataFrame” for missing variables upon import of files. This change ensures consistency and avoids compatibility issues with other functions.

- **File Import Restriction:** Restricted flexibility in the import of files. To import decomposed HD-EMG files, these must contain at least the raw EMG signal and one of the times of discharge of each MU ("MUPULSES") or their binary representation. This change ensures consistency and avoids compatibility issues with other functions.

### Other changes

- Sampling Frequency and Interelectrode Distance: Sampling frequency and interelectrode distance are now represented by float point values to accommodate different source files.

- `emg_from_customcsv` and `emg_from_otb`: Improved robustness and flexibility, with the possibility to load custom information in “EXTRAS.”

- `emg_from_demuse`: Improved robustness and flexibility.

- New Functions:  
    - `refsig_from_customcsv` to load the reference signal from a custom .csv file.
    - `delete_empty_mus` to delete all the MUs without firings.

- Exposed Function: Exposed `mupulses_from_binary` to extract the times of firing from the binary representation of MUs firings.

- Dependency Management: Addressed reported functioning issues related to external dependencies invoked by *openhdemg*. Stricter rules have been adopted in the setup.py file for automatically installing the correct version of these dependencies.

### Bug Fixes
 
- Fixed a BUG in the GUI when saving results in Excel files. The bug was due to changes in newer pandas versions.
- Fixed a BUG in the function “sort_mus” when empty MUs were present.

<br>

## :octicons-tag-24: 0.1.0-beta.1
:octicons-clock-24: June 2023

What's new? Well, everything. This is our first release, if you are using it, congratulations, you are a pioneer!

Please note, this is a **beta** release, which means that a lot can change in this version and the library is not yet ready to be used without double-checking the results that you get.
