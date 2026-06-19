The flexibility of the *openhdemg* framework allows you to interface with various software applications, enabling a smooth integration of data and workflows.

Since the release of v0.2.0, the import workflow aims to be completely platform neutral. This means that *openhdemg* should not depend on private internals from every acquisition system or decomposition program. The safest and most reproducible workflow is instead to:

1. export the data from the original platform using an official export option;
2. write a small custom loading function that converts that export into an *openhdemg* `emgfile`;
3. validate the resulting `emgfile`;
4. save it as an *openhdemg* binary module.

Once the file is saved as a module, the rest of your analysis can be independent from the original platform. You can load the module with *openhdemg*, share it with collaborators, and process it with the standard library functions.

More info about the *openhdemg* data structure can be found in the tutorial [Structure of the emgfile](emgfile_structure.md).

## The Standard Workflow

The standard workflow is:

1. Export from the original software

    Use the export tools officially supported by the acquisition or decomposition platform. Common examples are `.csv`, `.mat`, `.txt`, etc... Avoid building a workflow around temporary files, private binary files, or undocumented internal structures unless there is no supported alternative.

2. Convert the export into an `emgfile`

    An `emgfile` is a Python dictionary with recognised keys such as `RAW_SIGNAL`, `REF_SIGNAL`, `MUPULSES`, `FSAMP`, etc... See [Structure of the emgfile](emgfile_structure.md) for the complete structure.

3. Standardise the data types

    Use `standardise_emgfile_dtypes()` after creating or modifying an `emgfile`. This keeps recognised keys in the expected pandas, NumPy, and scalar data types.

4. Inspect the imported file

    Check the file structure with `emg.info().data(emgfile)`, inspect the signals visually, and verify that the signal or motor unit discharge times are accurate.

5. Save a binary module

    Save the validated `emgfile` with `save_openhdemg_module()` or `asksavemodule()`. Modules are the recommended persistence format for version 0.2.0 and later. See [Save and load binary modules](binary_modules.md).

## Decide What You Need To Import

The minimum content depends on the workflow.

| Goal | Minimum useful content |
| --- | --- |
| Raw HDsEMG file for decomposition | `SOURCE`, `FILENAME`, `RAW_SIGNAL`, `FSAMP`. `REF_SIGNAL` and `EMG_LENGTH` are strongly recommended. |
| Reference-signal-only file | `SOURCE`, `FILENAME`, `REF_SIGNAL`, `FSAMP`. |
| Decomposed file for MU analysis | `SOURCE`, `FILENAME`, `RAW_SIGNAL`, `REF_SIGNAL`, `ACCURACY`, `IPTS`, `MUPULSES`, `FSAMP`, `IED` `EMG_LENGTH`, `NUMBER_OF_MUS`, `BINARY_MUS_FIRING`. |

## DataFrame Column Rules

Use pandas DataFrames for signals and tabular data.

All standard DataFrames except `REF_SIGNAL` and `EXTRAS` should have columns named as base-0 integers:

```python
raw_signal = pd.DataFrame(raw_signal_array)
raw_signal.columns = range(raw_signal.shape[1])
```

This applies to standard DataFrames such as `RAW_SIGNAL`, `ACCURACY`, `IPTS` and `BINARY_MUS_FIRING`.

`REF_SIGNAL` is more flexible. String column names are accepted and can make Python scripts easier to read. However, integer-based column names can make interaction with the ***[openhdemg software](https://www.giacomovalli.com/openhdemg_software/){:target="_blank"}*** more straightforward, because channel selection is often naturally expressed as channel 0, channel 1, and so on. Therefore, this is mostly a personal preference.

If your file does not contain a reference signal, it is good practice to include a zero-filled `REF_SIGNAL` with one column named `0`. This improves compatibility with workflows that expect a reference signal to exist:

```python
ref_signal = pd.DataFrame(0, index=raw_signal.index, columns=[0])
```

## Example custom load function

Below you can find an example function to create an emgfile starting from a MATLAB (.mat) file. Please note that virtually any file can be opened in Python. You will only need to know the [structure of the emgfile](emgfile_structure.md) to reconstruct an *openhdemg* compatible python dictionary.

```python
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.io import loadmat

import openhdemg.library as emg


def load_custom_mat_64ch(filepath):
    """Load a custom .mat export into a raw openhdemg emgfile.

    This example assumes that the .mat file contains:
    - res["SamplingFrequency"]: sampling frequency in Hz;
    - res["Data"]: a samples-by-signals array;
    - columns 0 to 63: raw HDsEMG channels;
    - column 64: one reference signal.

    Adapt the key names and column positions to match your own official export.
    """

    # Load a matlab file using scipy
    res = loadmat(filepath, simplify_cells=True)

    # Create the emgfile dictionary
    emgfile = {}

    # Define basic entries
    emgfile["SOURCE"] = "EMG_SOFTWARE_ABC"
    emgfile["FILENAME"] = Path(filepath).stem
    emgfile["FSAMP"] = float(res["SamplingFrequency"])
    emgfile["IED"] = 8

    # Extract the EMG and reference signal and their duration. Signals'
    # duration MUST be the same. If your signals have a different duration,
    # you will need to resample them.

    # RAW_SIGNAL must be a samples-by-channels DataFrame.
    # Standard openhdemg DataFrames should use base-0 integer columns.
    emgfile["RAW_SIGNAL"] = pd.DataFrame(
        res["Data"][:, 0:64],
        columns=[*range(0, 64)],
        dtype=np.float64,
    )
    emgfile["EMG_LENGTH"] = emgfile["RAW_SIGNAL"].shape[0]

    # REF_SIGNAL can contain one or more reference-signal columns.
    # Here the single reference signal is stored as column 0.
    emgfile["REF_SIGNAL"] = pd.DataFrame(
        res["Data"][:, 64],
        columns=[0],
        dtype=np.float64,
    )

    # Standardise recognised openhdemg keys before returning the emgfile.
    emgfile = emg.standardise_emgfile_dtypes(emgfile)

    return emgfile
```

## Save The Imported File

After importing and checking the file, save it as an *openhdemg* binary module:

```python
import openhdemg.library as emg

emg.save_openhdemg_module(
    emgfile=emgfile,
    path="C:/Users/.../Desktop/openhdemg_modules",
    module_name="participant_01_trial_01",
)
```

You can also use a dialog:

```python
emg.asksavemodule(emgfile=emgfile)
```

<br>

## Built-In Compatibility Importers

The functions below remain available for backward compatibility and should be understood as compatibility helpers, not as the only or preferred way to make *openhdemg* work with another platform.

!!! note "Recommended v0.2.0 workflow"
    Built-in import functions such as `emg_from_otb()`, `emg_from_demuse()`, `emg_from_delsys()`, and `emg_from_customcsv()` are still available and can be useful when your exported files match the expected format. However, for new projects, the most robust workflow is to create a custom loader based on an official export from the platform that produced the data.

### From .csv files

*openhdemg* currently has two functions dedicated to loading data from .csv files. Please refer to the [API](../api_openfiles.md) of the specific function to see what data your .csv file should contain to be opened in *openhdemg*:

- [emg_from_customcsv()](../api_openfiles.md#openhdemg.library.openfiles.emg_from_customcsv): This function is used to import the decomposition outcome from a custom .csv file.
- [refsig_from_customcsv()](../api_openfiles.md#openhdemg.library.openfiles.refsig_from_customcsv): This function is used to import the reference signal from a custom .csv file.

#### Export the decomposition outcome

The decomposition outcome can differ between decomposition algorithms and, therefore, the function [emg_from_customcsv()](../api_openfiles.md#openhdemg.library.openfiles.emg_from_customcsv) is quite flexible, so that it can adapt to different user needs.

However, some variables must always be present in the exported file. These include:

- The raw EMG signal.
- At least one of "MUPULSES" (instants of firing) or "BINARY_MUS_FIRING" (binary representation of MUs firings).

If "MUPULSES" is absent, it will be calculated from "BINARY_MUS_FIRING" and viceversa.

Other default variables that can be exported include:

- The reference signal.
- The decomposed source.

All these variables should be stored in different columns because the import function detects the content of the .csv by parsing the .csv columns. When assigning a name to the columns, you can decide to simply use the *openhdemg* standard names or custom ones, as follows:

**Using the *openhdemg* standard names**

If you use *openhdemg* standard names for column labels, you won't need to specify these in the import function. Standard names include:

- Reference Signal: Label the column containing the reference signal "REF_SIGNAL".
- Raw EMG Signal: Label the columns containing the raw EMG signal with "RAW_SIGNAL" + channel number. For example, "RAW_SIGNAL_0", "RAW_SIGNAL_1", "RAW_SIGNAL_2", "RAW_SIGNAL_n-1".
- Pulse Train (decomposed source): Label the column(s) containing the decomposed source with "IPTS" + MU number. For example, "IPTS_0", "IPTS_1", "IPTS_2", "IPTS_n-1".
- Times of Firing (mupulses): Label the column(s) containing the times of firing with "MUPULSES' + MU number. For example, "MUPULSES_0", "MUPULSES_1", "MUPULSES_2", "MUPULSES_n-1".
- Binary MUs Firing: Label the column(s) containing the binary representation of the MUs firings with "BINARY_MUS_FIRING" + MU number. For example, "BINARY_MUS_FIRING_0", "BINARY_MUS_FIRING_1", "BINARY_MUS_FIRING_2", "BINARY_MUS_FIRING_n-1".
- Accuracy Score: Label the column(s) containing the accuracy score of the MUs firings with "ACCURACY" + MU number. For example, "ACCURACY_0", "ACCURACY_1", "ACCURACY_2", "ACCURACY_n-1".

Interestingly, this function allows also to import additional signals compared to what you saw before. Therefore, you could also export other signals together with what previously mentioned. Please note that files saved with "extra" information can only be loaded from the library (the use of "EXTRAS" is not supported in the graphical user interface) Please read the [specific API](../api_openfiles.md#openhdemg.library.openfiles.emg_from_customcsv) for more information.

- Extras: Label the column containing custom values with "EXTRAS" or, if more columns are needed, with "EXTRAS" + n. For example, "EXTRAS_0", "EXTRAS_1", "EXTRAS_2", "EXTRAS_n-1".

If some of the variables are not present, simply don't specify them in your .csv file.

Once you structured your table in Excel or any other tool, you can easily save it as type: "CSV (Comma delimited)", and that's all it takes.

**Using custom names**

Obviously, you have the flexibility to decide any name you want for your columns. However, in this case, you should specify the label you used to describe each variable when calling the function [emg_from_customcsv()](../api_openfiles.md#openhdemg.library.openfiles.emg_from_customcsv).

Please remember that different representations of the same variable (e.g., the EMG signal from different channels or the accuracy of different MUs) must have the same basic label. For example, the column(s) containing the times of firing should be labeled with "MYLABEL' + MU number (i.e., "MYLABEL_0", "MYLABEL_1", "MYLABEL_2", "MYLABEL_n-1").

Although custom column labels can be used, the information that can be exported is the same described above in "**Using the *openhdemg* standard names**".

If some of the possible variables are not present, simply don't specify them in your .csv file.

Once you structured your table in Excel or any other tool, you can easily save it as type: "CSV (Comma delimited)", and that's all it takes.

#### Export the reference signal

In some cases, like for example for MVC trials, you might want to export only the reference signal. Exporting the reference signal is as simple as exporting a table with only one column. Also in this case, you can decide to label the column containing the refere signal with *openhdemg* standard names or with custom names. Please refer to the previous section for further details.

Also the function [refsig_from_customcsv()](../api_openfiles.md#openhdemg.library.openfiles.refsig_from_customcsv) allows to import additional signals. Therefore, you could also export other signals together withthe reference signal. Please note that files saved with "extra" information can only be loaded from the library (the use of "EXTRAS" is not supported in the graphical user interface) and the parameter "extras=" must be specified when calling the function. Please read the [specific API](../api_openfiles.md#openhdemg.library.openfiles.refsig_from_customcsv) for more information and read the previous section of this tutorial.

Once you structured your table in Excel or any other tool, you can easily save it as type: "CSV (Comma delimited)", and that's all it takes.

### From DEMUSE

For years, DEMUSE has been the only commercially available tool for MUs decomposition non related to a specific acquisition device. DEMUSE is essentially a MATLAB-based application and it allows to export files in .mat format. Also in this case, it is quite easy to save files, as the only thing the user needs to do after decomposition and manual editing of the spike train, is to click: "save results".

Once the results are saved, these can be loaded in *openhdemg* with the function:

- [emg_from_demuse()](../api_openfiles.md#openhdemg.library.openfiles.emg_from_demuse): This function is used to import the decomposition outcome saved from the DEMUSE tool.

### From OTBioLab+

OTBioLab+ is the software used to record EMG signals from the OTB "Quattrocento", "Sessantaquattro+" and other devices. However, it also allows to perform MUs decomposition and editing. Once the decomposition is done, the user can export the decomposition outcome in different file formats. Among them, the option to export .mat files is the one that provides the most convenient and easy way to export all the needed information.

*openhdemg* currently has two functions dedicated to loading data from .mat files exported from OTBioLab+. Please refer to the [API](../api_openfiles.md) of the specific function for more information:

- [emg_from_otb()](../api_openfiles.md#openhdemg.library.openfiles.emg_from_otb): This function is used to import the decomposition outcome from a .mat file exported from the OTBioLab+ software.
- [refsig_from_otb()](../api_openfiles.md#openhdemg.library.openfiles.refsig_from_otb): This function is used to import the reference signal from a .mat file exported from the OTBioLab+ software.

Depending on whether you want to export all the decomposition outcome or only the reference signal, follow these steps:

#### Export the decomposition outcome

Once the decomposition and manual editing is completed, the software saves the decomposition outcome in a new tab. The decomposition outcome includes:

- Binary firings: the binary representation of the MUs discharge times. This is usually named "Decomposition of ...".
- Decomposed source: the source signal used to detect the discharge times. This is usually named "Source for decomposition ...".

Before exporting the decomposition outcome, copy in the new tab containing the decomposition outcome also:

- The EMG signal with all channels, without exception.
- The reference signal. This is usually named "acquired data".

At this point:

1. Select all the signals in the new tab (or a portion of them if that's all you need).
2. Click on "Export".
3. Click on "As .mat file".
4. During the export process, you will be asked if you want to save the signal in different files. Click "No".

Now that the .mat file has been created, it can be easily loaded in *openhdemg* with the function [emg_from_otb()](../api_openfiles.md#openhdemg.library.openfiles.emg_from_otb).

Interestingly, this function allows also to import additional signals compared to what you saw before. Therefore, you could also export other signals together with what previously mentioned. Please note that files saved with "extra" information can only be loaded from the library (the use of "EXTRAS" is not supported in the graphical user interface) and the parameter "extras=" must be specified when calling the function. Please read the [specific API](../api_openfiles.md#openhdemg.library.openfiles.emg_from_otb) for more information.

#### Export the reference signal

In some cases, like for example for MVC trials, you might want to export only the reference signal. This can be simply done by:

1. Select the reference signals, usually named "acquired data" (or a portion of it if that's all you need).
2. Click on "Export".
3. Click on "As .mat file".

Now that the .mat file has been created, it can be easily loaded in *openhdemg* with the function [refsig_from_otb()](../api_openfiles.md#openhdemg.library.openfiles.refsig_from_otb).

Interestingly, this function allows also to import additional signals. Therefore, you could also export other signals together withthe reference signal. Please note that files saved with "extra" information can only be loaded from the library (the use of "EXTRAS" is not supported in the graphical user interface) and the parameter "extras=" must be specified when calling the function. Please read the [specific API](../api_openfiles.md#openhdemg.library.openfiles.refsig_from_otb) for more information.

### From Delsys

!!! Please note, the following two functions underwent limited testing. If they don't work, [report to us](../contacts.md) the issue and we will try to make you load your files !!!

Delsys has a number of software that can be used to record EMG signals from their acquisition systems. Additionally, some of them also allow to perform automatic MUs decomposition and some analyses.

*openhdemg* currently has two functions dedicated to loading data from Delsys software. Please refer to the [API](../api_openfiles.md) of the specific function for more information:

- [emg_from_delsys()](../api_openfiles.md#openhdemg.library.openfiles.emg_from_delsys): This function is used to import the decomposition outcome from the EMGworks and NeuroMap software.
- [refsig_from_delsys()](../api_openfiles.md#openhdemg.library.openfiles.refsig_from_delsys): This function is used to import the reference signal from the EMGworks software.

Depending on whether you want to export all the decomposition outcome or only the reference signal, follow these steps:

#### Export the decomposition outcome

For the raw EMG signal:

- Collect the data in EMGworks Analysis with the correct sensors settings to allow for decomposition in the NeuroMap software. (Correct sensor settings will be indicated by the NeuroMap symbol next to compatible options in the sampling rate, range, and bandwidth settings).
- The data will save as a .hpf file.
- Open the Delsys File Utility and convert the .hpf file to a .mat file.
- Ensure that you still have access to the original .hpf file for the decomposition process.

For the decomposition outcome:

- Open the NeuroMap software.
- Import the .hpf file that was collected previously.
- Press decompose.
- This will produce a .dhpf file.
- Open the .dhpf file in NeuroMap Explorer.
- Export the files as .txt from the export options.

At this point, you will have a .mat file containing the raw EMG signal and the reference signal, and a folder containing different .txt files. The .txt files contain the decomposition outcome, the MUAPs and some MUs statistics, including their accuracy score. Please, do not rename the .txt files or, if you rename them, do not alter the ending identifier (e.g., _MUAPs).

Now that the .mat and .txt files have been created, they can be easily loaded in *openhdemg* with the function [emg_from_delsys()](../api_openfiles.md#openhdemg.library.openfiles.emg_from_delsys).

Interestingly, this function allows also to import the MUAPs computed by Deslys during the decomposition. The computed MUAPs will be stored under the "EXTRAS" key and will be easily accessible with the function [extract_delsys_muaps()](../api_muap.md#openhdemg.library.muap.extract_delsys_muaps).

#### Export the reference signal

You can export the reference signal in a .mat file from the NeuroMap software by following the steps proposed in the previous section. Once the .mat file has been created, it can be easily loaded in *openhdemg* with the function [refsig_from_delsys()](../api_openfiles.md#openhdemg.library.openfiles.refsig_from_delsys).

## More questions?

We hope that this tutorial was useful. If you need any additional information, do not hesitate to read the answers or ask a question in the [*openhdemg* discussion section](https://github.com/GiacomoValliPhD/openhdemg/discussions){:target="_blank"}. If you are not familiar with GitHub discussions, please read this [post](https://github.com/GiacomoValliPhD/openhdemg/discussions/42){:target="_blank"}. This will allow the *openhdemg* community to answer your questions.