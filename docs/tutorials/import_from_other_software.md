*openhdemg* is designed to seamlessly interface with various software applications, enabling a smooth integration of data and workflows.

In this article, we will explore how you can import EMG data from other software into *openhdemg*.

The *openhdemg* team is committed to simplifying the data import process. Through continuous efforts, they regularly introduce new functions designed to automatically load files exported from third-party software. These efforts prioritize compatibility with the most commonly used software applications; however, it's important to note that the provided functions may not always fulfill every user's unique needs. If you cannot find a solution that fits your needs, you can always implement your own function to load any file with the *openhdemg* data structure. More info about the *openhdemg* data structure can be found in the tutorial [Structure of the emgfile](emgfile_structure.md).

## From .csv files

Since it is not possible to predict any data format, we created dedicated functions to load any possible dataset from .csv files. Several considerations guided us in choosing the .csv format for loading custom files:

- Ubiquitous Data Structure: .csv (Comma-Separated Values) stands out as one of the most widely used data structures in data analyses.
  
- Universal Export Compatibility: It can be exported from virtually any software, making it a versatile choice for compatibility with various data sources.
  
- Language and Software Agnosticism: .csv files can be read by any programming language, ensuring flexibility and ease of integration across diverse software environments, including popular tools like Microsoft Excel.

- Structured Layout: With its clear organization into columns and rows, .csv simplifies the storage of labeled information. This structured format not only enhances data interpretation but also facilitates seamless integration into analytical workflows.

Therefore, anybody developing scripts and algorithms for data analysis is familar with the .csv format. If you are not, just think that any table that you usually populate in Microsoft Excel, LibreOffice Calc, Google Sheets and many other tools, can be easily exported in .csv format.

*openhdemg* currently has two functions dedicated to loading data from .csv files. Please refer to the [API](../api_openfiles.md) of the specific function to see what data your .csv file should contain to be opened in *openhdemg*:

- [emg_from_customcsv()](../api_openfiles.md#openhdemg.library.openfiles.emg_from_customcsv): This function is used to import the decomposition outcome from a custom .csv file.
- [refsig_from_customcsv()](../api_openfiles.md#openhdemg.library.openfiles.refsig_from_customcsv): This function is used to import the reference signal from a custom .csv file.

### Export the decomposition outcome

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

### Export the reference signal

In some cases, like for example for MVC trials, you might want to export only the reference signal. Exporting the reference signal is as simple as exporting a table with only one column. Also in this case, you can decide to label the column containing the refere signal with *openhdemg* standard names or with custom names. Please refer to the previous section for further details.

Also the function [refsig_from_customcsv()](../api_openfiles.md#openhdemg.library.openfiles.refsig_from_customcsv) allows to import additional signals. Therefore, you could also export other signals together withthe reference signal. Please note that files saved with "extra" information can only be loaded from the library (the use of "EXTRAS" is not supported in the graphical user interface) and the parameter "extras=" must be specified when calling the function. Please read the [specific API](../api_openfiles.md#openhdemg.library.openfiles.refsig_from_customcsv) for more information and read the previous section of this tutorial.

Once you structured your table in Excel or any other tool, you can easily save it as type: "CSV (Comma delimited)", and that's all it takes.

## From DEMUSE

For years, DEMUSE has been the only commercially available tool for MUs decomposition non related to a specific acquisition device. DEMUSE is essentially a MATLAB-based application and it allows to export files in .mat format. Also in this case, it is quite easy to save files, as the only thing the user needs to do after decomposition and manual editing of the spike train, is to click: "save results".

Once the results are saved, these can be loaded in *openhdemg* with the function:

- [emg_from_demuse()](../api_openfiles.md#openhdemg.library.openfiles.emg_from_demuse): This function is used to import the decomposition outcome saved from the DEMUSE tool.

## From OTBioLab+

OTBioLab+ is the software used to record EMG signals from the OTB "Quattrocento", "Sessantaquattro+" and other devices. However, it also allows to perform MUs decomposition and editing. Once the decomposition is done, the user can export the decomposition outcome in different file formats. Among them, the option to export .mat files is the one that provides the most convenient and easy way to export all the needed information.

*openhdemg* currently has two functions dedicated to loading data from .mat files exported from OTBioLab+. Please refer to the [API](../api_openfiles.md) of the specific function for more information:

- [emg_from_otb()](../api_openfiles.md#openhdemg.library.openfiles.emg_from_otb): This function is used to import the decomposition outcome from a .mat file exported from the OTBioLab+ software.
- [refsig_from_otb()](../api_openfiles.md#openhdemg.library.openfiles.refsig_from_otb): This function is used to import the reference signal from a .mat file exported from the OTBioLab+ software.

Depending on whether you want to export all the decomposition outcome or only the reference signal, follow these steps:

### Export the decomposition outcome

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

### Export the reference signal

In some cases, like for example for MVC trials, you might want to export only the reference signal. This can be simply done by:

1. Select the reference signals, usually named "acquired data" (or a portion of it if that's all you need).
2. Click on "Export".
3. Click on "As .mat file".

Now that the .mat file has been created, it can be easily loaded in *openhdemg* with the function [refsig_from_otb()](../api_openfiles.md#openhdemg.library.openfiles.refsig_from_otb).

Interestingly, this function allows also to import additional signals. Therefore, you could also export other signals together withthe reference signal. Please note that files saved with "extra" information can only be loaded from the library (the use of "EXTRAS" is not supported in the graphical user interface) and the parameter "extras=" must be specified when calling the function. Please read the [specific API](../api_openfiles.md#openhdemg.library.openfiles.refsig_from_otb) for more information.

## From Delsys

!!! Please note, the following two functions underwent limited testing. If they don't work, [report to us](../contacts.md) the issue and we will try to make you load your files !!!

Delsys has a number of software that can be used to record EMG signals from their acquisition systems. Additionally, some of them also allow to perform automatic MUs decomposition and some analyses.

*openhdemg* currently has two functions dedicated to loading data from Delsys software. Please refer to the [API](../api_openfiles.md) of the specific function for more information:

- [emg_from_delsys()](../api_openfiles.md#openhdemg.library.openfiles.emg_from_delsys): This function is used to import the decomposition outcome from the EMGworks and NeuroMap software.
- [refsig_from_delsys()](../api_openfiles.md#openhdemg.library.openfiles.refsig_from_delsys): This function is used to import the reference signal from the EMGworks software.

Depending on whether you want to export all the decomposition outcome or only the reference signal, follow these steps:

### Export the decomposition outcome

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

### Export the reference signal

You can export the reference signal in a .mat file from the NeuroMap software by following the steps proposed in the previous section. Once the .mat file has been created, it can be easily loaded in *openhdemg* with the function [refsig_from_delsys()](../api_openfiles.md#openhdemg.library.openfiles.refsig_from_delsys).

## More questions?

We hope that this tutorial was useful. If you need any additional information, do not hesitate to read the answers or ask a question in the [*openhdemg* discussion section](https://github.com/GiacomoValliPhD/openhdemg/discussions){:target="_blank"}. If you are not familiar with GitHub discussions, please read this [post](https://github.com/GiacomoValliPhD/openhdemg/discussions/42){:target="_blank"}. This will allow the *openhdemg* community to answer your questions.