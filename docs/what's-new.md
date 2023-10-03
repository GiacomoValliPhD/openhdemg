## :octicons-tag-24: 0.1.0-beta.2
:octicons-clock-24: September 2023

This release introduces important changes. It is mainly addressing the necessity of maximum flexibility and easy integration with any custom or proprietary file source. This release is not backward compatible.

MAJOR CHANGES:

- **Accuracy Measurement:** Replaced the double accuracy measures in the `emgfile` (i.e., “SIL” and “PNR”) with a single accuracy measure named “ACCURACY.” For files containing the decomposed source (also named “IPTS”), the “ACCURACY” variable will contain the silhouette score (Negro et al. 2016). For files that do not contain the decomposed source, the accuracy will be the original (often proprietary) accuracy estimate. This allows for maximum flexibility and is fundamental to interface the *openhdemg* library with any proprietary and custom implementation of the different decomposition algorithms currently available.

    To accommodate this change, all the functions in the `openfile` module have been updated. Consequently, the functions using the “SIL” or “PNR” variables have also been modified. Specifically:
    
    - The `basic_mus_properties` function has a new input parameter (i.e., “accuracy”) to customize the returned accuracy estimate.
    - In the function `remove_duplicates_between`, the input parameter “which” now only accepts “munumber” and “accuracy” instead of “munumber,” “SIL,” and “PNR.”

- **EXTRAS Variable:** Introduced a new “EXTRAS” variable to store any custom information in the opened file. This will be accessible in the `emgfile` dictionary with the “EXTRAS” key. This variable must contain a pd.DataFrame structure and will be preserved when saving the file. This change extends the customisability of the `emgfile`.

- **Handling Missing Variables:** Replaced “np.nan” with empty "pd.DataFrame” for missing variables upon import of files. This change ensures consistency and avoids compatibility issues with other functions.

- **File Import Restriction:** Restricted flexibility in the import of files. To import decomposed HD-EMG files, these must contain at least the raw EMG signal and one of the times of discharge of each MU ("MUPULSES") or their binary representation. This change ensures consistency and avoids compatibility issues with other functions.

**OTHER CHANGES:**

- **Sampling Frequency** and **Interelectrode Distance:** Sampling frequency and interelectrode distance are now represented by float point values to accommodate different source files.

- **emg_from_customcsv** and **emg_from_otb:** Improved robustness and flexibility, with the possibility to load custom information in “EXTRAS.”

- **emg_from_demuse:** Improved robustness and flexibility.

- **New Functions:**  
    - `refsig_from_customcsv` to load the reference signal from a custom .csv file.
    - `delete_empty_mus` to delete all the MUs without firings.

- **Exposed Function:** Exposed `mupulses_from_binary` to extract the times of firing from the binary representation of MUs firings.

- **Dependency Management:** Addressed reported functioning issues related to external dependencies invoked by *openhdemg*. Stricter rules have been adopted in the setup.py file for automatically installing the correct version of these dependencies.

- **Bug Fixes:**  
    - Fixed a BUG in the GUI when saving results in Excel files. The bug was due to changes in newer pandas versions.
    - Fixed a BUG in the function “sort_mus” when empty MUs were present.

<br>

## :octicons-tag-24: 0.1.0-beta.1
:octicons-clock-24: June 2023

What's new? Well, everything. This is our first release, if you are using it, congratulations, you are a pioneer!

Please note, this is a **beta** release, which means that a lot can change in this version and the library is not yet ready to be used without double-checking the results that you get.
