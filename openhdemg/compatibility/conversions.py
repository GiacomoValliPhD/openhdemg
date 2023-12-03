import pandas as pd
import numpy as np
from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
import json
import gzip
import os


class convert_json_output():
    """
    Convert .json files saved from previous openhdemg versions to the desired
    format (target openhdemg version).

    Parameters
    ----------
    old : str, default ""
        A path pointing to a .json file, or to a folder containing multiple
        .json files, saved from the openhdemg version specified in
        ``old_version``.
        The path can be a simple string, the use of Path() is not necessary.
        If ``old`` points to a folder, all the .json files contained in that
        folder will be converted. Make sure that the folder contains only .json
        files from the openhdemg version specified in ``old_version``.
    new : str, default ""
        A path pointing to the folder where the converted .json file/files
        will be saved. The path can be a simple string, the use of Path() is
        not necessary.
    old_version : str {0.1.0-beta.2}, default 0.1.0-beta.2
        The openhdemg version used to save the ``old`` files.
        Only "0.1.0-beta.2" is currently supported.
    new_version : str {0.1.0-beta.3}, default 0.1.0-beta.3
        The target openhdemg version for which you want to convert the files.
        Only "0.1.0-beta.3" is currently supported.
    append_name : str, default "converted"
        String to append to the name of the converted file. Use append_name=""
        to don't append any name.
    compresslevel : int, default 4
        An int from 0 to 9, where 0 is no compression and nine maximum
        compression. Compressed files will take less space, but will require
        more computation. The relationship between compression level and time
        required for the compression is not linear. For optimised performance,
        we suggest values between 2 and 6, with 4 providing the best balance.
    gui : bool, default True
        If true, the user will be able to select one or multiple .json files
        to convert and the output folder with a convenient graphical interface.
        If true, ``old`` and ``new`` can be ignored.
    ignore_safety_checks : bool, default False
        Safety checks are performed to avoid overwriting the original file. If
        ``ignore_safety_checks=True``, the original file could be overwritten
        without asking user permission. The risk of overwriting files happens
        when converted files are saved in their original directory and with
        ``append_name=""``.

    Examples
    --------
    Convert the file/s with a practical GUI.

    >>> from openhdemg.compatibility import convert_json_output
    >>> convert_json_output(gui=True, append_name="converted")

    Convert all the files in a folder without GUI. Save them in the same
    location with a different name.

    >>> from openhdemg.compatibility import convert_json_output
    >>> old = "C:/Users/.../test conversions/"
    >>> new = "C:/Users/.../test conversions/"
    >>> convert_json_output(
    ...     old=old,
    ...     new=new,
    ...     append_name="converted",
    ...     gui=False,
    ... )

    Convert a file in a folder without GUI and overwrite it.

    >>> from openhdemg.compatibility import convert_json_output
    >>> old = "C:/Users/.../test conversions/old_testfile.json"
    >>> new = "C:/Users/.../test conversions/"
    >>> convert_json_output(
    ...     old=old,
    ...     new=new,
    ...     append_name="",
    ...     gui=False,
    ...     ignore_safety_checks=True,
    ... )
    """

    def __init__(
        self,
        old="",
        new="",
        old_version="0.1.0-beta.2",
        new_version="0.1.0-beta.3",
        append_name="converted",
        compresslevel=4,
        gui=True,
        ignore_safety_checks=False,
    ):

        # Check if correct versions have been passed
        accepted_old_versions = [
            "0.1.0-beta.2",
        ]
        accepted_new_versions = [
            "0.1.0-beta.3",
        ]
        if old_version not in accepted_old_versions:
            raise ValueError("Unsupported old_version")
        if new_version not in accepted_new_versions:
            raise ValueError("Unsupported new_version")

        if gui:
            # Create and hide the tkinter root window necessary for the GUI
            # based load file/directory function.
            root = Tk()
            root.withdraw()

            # Get a tuple of files to open
            files_to_open = filedialog.askopenfilenames(
                title="Select one or multiple .json files to convert",
                filetypes=[("JSON files", "*.json")],
            )
            if len(files_to_open) < 1:
                # End class execution if cancel button has been pressed.
                return

            # Get the directory to save converted files
            save_directory = filedialog.askdirectory(
                title="Select the folder where to save the converted files",
            )
            if len(save_directory) < 1:
                # End class execution if cancel button has been pressed.
                return

            # Destroy the root since it is no longer necessary
            root.destroy()

            # Safety check to avoid overwriting the original file
            if not ignore_safety_checks and len(append_name) == 0:
                if save_directory == os.path.dirname(files_to_open[0]):
                    root = Tk()
                    root.withdraw()
                    # Ask for user confirmation
                    user_response = messagebox.askyesno(
                        "Confirmation",
                        "You are going to overwrite the original file/s." +
                        "Do you want to continue?",
                    )
                    # Destroy the main window
                    root.destroy()
                    if not user_response:
                        print("Conversion interrupted")
                        return

            # Iterate all the elements in files_toOpen. Convert and save all
            # the selected files.
            for pos, fin in enumerate(files_to_open):
                print(f"Converting {fin}")
                print(f"Converting n°{pos+1} out of {len(files_to_open)} files")
                # Load file
                emgfile = self.load_0_1_0_b2(filepath=fin)

                # Get the appropriate name and filepath
                base_name = os.path.basename(fin)
                base_name, _ = os.path.splitext(base_name)
                if len(append_name) > 0:
                    base_name = base_name + "_" + append_name
                filepath = (
                    save_directory + "/" + base_name + ".json"
                )

                # Save file
                self.save_0_1_0_b3(
                    emgfile,
                    filepath=filepath,
                    compresslevel=compresslevel,
                )
            print("Conversion completed")

        else:
            # Check if the path is a file
            if os.path.isfile(old):
                files_to_open = (old,)

            # Check if the path is a directory
            elif os.path.isdir(old):
                json_files = [
                    os.path.join(old, file)
                    for file in os.listdir(old)
                    if file.endswith(".json")
                ]
                files_to_open = tuple(json_files)

            else:
                raise FileNotFoundError("The path 'old' does not exist.")

            # Check if the new path is a directory
            if not os.path.isdir(new):
                raise ValueError("'new' is not pointing to a directory")

            # Safety check to avoid overwriting the original file
            if not ignore_safety_checks and len(append_name) == 0:
                res = input(
                    "You are going to overwrite the original file. "
                    "Continue? Y/n    ->"
                )
                if res not in ["Y", "y"]:
                    print("Conversion interrupted")
                    return

            # Iterate all the elements in files_toOpen. Convert and save all
            # the selected files.
            for pos, fin in enumerate(files_to_open):
                print(f"Converting {fin}")
                print(f"Converting n°{pos+1} out of {len(files_to_open)} files")
                # Load file
                emgfile = self.load_0_1_0_b2(filepath=fin)

                # Get the appropriate name and filepath
                base_name = os.path.basename(fin)
                base_name, _ = os.path.splitext(base_name)
                if len(append_name) > 0:
                    base_name = base_name + "_" + append_name
                filepath = (
                    new + "/" + base_name + ".json"
                )

                # Save file
                self.save_0_1_0_b3(
                    emgfile,
                    filepath=filepath,
                    compresslevel=compresslevel,
                )

            print("Conversion completed")

    def load_0_1_0_b2(self, filepath):
        """  """
        """
        Load the version 0.1.0-beta.2 emgfile and emg_refsig.

        Parameters
        ----------
        filepath : str or Path
            The directory and the name of the file to load (including file
            extension .json).
            This can be a simple string, the use of Path is not necessary.

        Returns
        -------
        emgfile : dict
            The dictionary containing the emgfile.
        """

        # Read and decompress json file
        with gzip.open(filepath, "r") as fin:
            json_bytes = fin.read()
            # Decode json file
            json_str = json_bytes.decode("utf-8")
            jsonemgfile = json.loads(json_str)

        # Access the dictionaries and extract the data
        # jsonemgfile[0] contains the SOURCE in a dictionary
        source_dict = json.loads(jsonemgfile[0])
        source = source_dict["SOURCE"]
        # jsonemgfile[1] contains the FILENAME in all the sources
        filename_dict = json.loads(jsonemgfile[1])
        filename = filename_dict["FILENAME"]

        if source in ["DEMUSE", "OTB", "CUSTOMCSV"]:
            # jsonemgfile[2] contains the RAW_SIGNAL in a dictionary, it can be
            # extracted in a new dictionary and converted into a pd.DataFrame.
            # index and columns are imported as str, we need to convert it to
            # int.
            raw_signal_dict = json.loads(jsonemgfile[2])
            raw_signal_dict = json.loads(raw_signal_dict["RAW_SIGNAL"])
            raw_signal = pd.DataFrame(raw_signal_dict)
            raw_signal.columns = raw_signal.columns.astype(int)
            raw_signal.index = raw_signal.index.astype(int)
            raw_signal.sort_index(inplace=True)
            # jsonemgfile[3] contains the REF_SIGNAL to be treated as
            # jsonemgfile[2]
            ref_signal_dict = json.loads(jsonemgfile[3])
            ref_signal_dict = json.loads(ref_signal_dict["REF_SIGNAL"])
            ref_signal = pd.DataFrame(ref_signal_dict)
            ref_signal.columns = ref_signal.columns.astype(int)
            ref_signal.index = ref_signal.index.astype(int)
            ref_signal.sort_index(inplace=True)
            # jsonemgfile[4] contains the ACCURACY to be treated as
            # jsonemgfile[2]
            accuracy_dict = json.loads(jsonemgfile[4])
            accuracy_dict = json.loads(accuracy_dict["ACCURACY"])
            accuracy = pd.DataFrame(accuracy_dict)
            accuracy.columns = accuracy.columns.astype(int)
            accuracy.index = accuracy.index.astype(int)
            accuracy.sort_index(inplace=True)
            # jsonemgfile[5] contains the IPTS to be treated as jsonemgfile[2]
            ipts_dict = json.loads(jsonemgfile[5])
            ipts_dict = json.loads(ipts_dict["IPTS"])
            ipts = pd.DataFrame(ipts_dict)
            ipts.columns = ipts.columns.astype(int)
            ipts.index = ipts.index.astype(int)
            ipts.sort_index(inplace=True)
            # jsonemgfile[6] contains the MUPULSES which is a list of lists but
            # has to be converted in a list of ndarrays.
            mupulses = json.loads(jsonemgfile[6])
            for num, element in enumerate(mupulses):
                mupulses[num] = np.array(element)
            # jsonemgfile[7] contains the FSAMP to be treated as jsonemgfile[0]
            fsamp_dict = json.loads(jsonemgfile[7])
            fsamp = float(fsamp_dict["FSAMP"])
            # jsonemgfile[8] contains the IED to be treated as jsonemgfile[0]
            ied_dict = json.loads(jsonemgfile[8])
            ied = float(ied_dict["IED"])
            # jsonemgfile[9] contains the EMG_LENGTH to be treated as
            # jsonemgfile[0]
            emg_length_dict = json.loads(jsonemgfile[9])
            emg_length = int(emg_length_dict["EMG_LENGTH"])
            # jsonemgfile[10] contains the NUMBER_OF_MUS to be treated as
            # jsonemgfile[0]
            number_of_mus_dict = json.loads(jsonemgfile[10])
            number_of_mus = int(number_of_mus_dict["NUMBER_OF_MUS"])
            # jsonemgfile[11] contains the BINARY_MUS_FIRING to be treated as
            # jsonemgfile[2]
            binary_mus_firing_dict = json.loads(jsonemgfile[11])
            binary_mus_firing_dict = json.loads(
                binary_mus_firing_dict["BINARY_MUS_FIRING"]
            )
            binary_mus_firing = pd.DataFrame(binary_mus_firing_dict)
            binary_mus_firing.columns = binary_mus_firing.columns.astype(int)
            binary_mus_firing.index = binary_mus_firing.index.astype(int)
            # jsonemgfile[12] contains the EXTRAS to be treated as
            # jsonemgfile[2]
            extras_dict = json.loads(jsonemgfile[12])
            extras_dict = json.loads(extras_dict["EXTRAS"])
            extras = pd.DataFrame(extras_dict)
            # extras.columns = extras.columns.astype(int)
            # extras.index = extras.index.astype(int)
            # extras.sort_index(inplace=True)
            # Don't alter extras, leave that to the user for maximum control

            emgfile = {
                "SOURCE": source,
                "FILENAME": filename,
                "RAW_SIGNAL": raw_signal,
                "REF_SIGNAL": ref_signal,
                "ACCURACY": accuracy,
                "IPTS": ipts,
                "MUPULSES": mupulses,
                "FSAMP": fsamp,
                "IED": ied,
                "EMG_LENGTH": emg_length,
                "NUMBER_OF_MUS": number_of_mus,
                "BINARY_MUS_FIRING": binary_mus_firing,
                "EXTRAS": extras,
            }

        elif source in ["OTB_REFSIG", "CUSTOMCSV_REFSIG"]:
            # jsonemgfile[2] contains the fsamp
            fsamp_dict = json.loads(jsonemgfile[2])
            fsamp = float(fsamp_dict["FSAMP"])
            # jsonemgfile[3] contains the REF_SIGNAL
            ref_signal_dict = json.loads(jsonemgfile[3])
            ref_signal_dict = json.loads(ref_signal_dict["REF_SIGNAL"])
            ref_signal = pd.DataFrame(ref_signal_dict)
            ref_signal.columns = ref_signal.columns.astype(int)
            ref_signal.index = ref_signal.index.astype(int)
            ref_signal.sort_index(inplace=True)
            # jsonemgfile[4] contains the EXTRAS
            extras_dict = json.loads(jsonemgfile[4])
            extras_dict = json.loads(extras_dict["EXTRAS"])
            extras = pd.DataFrame(extras_dict)

            emgfile = {
                "SOURCE": source,
                "FILENAME": filename,
                "FSAMP": fsamp,
                "REF_SIGNAL": ref_signal,
                "EXTRAS": extras,
            }

        else:
            raise Exception("\nFile source not recognised\n")

        return emgfile

    def save_0_1_0_b3(self, emgfile, filepath, compresslevel):
        """  """
        """
        Save the emgfile or emg_refsig compatible with openhdemg version
        0.1.0-beta.3.

        Parameters
        ----------
        emgfile : dict
            The dictionary containing the emgfile.
        filepath : str or Path
            The directory and the name of the file to save (including file
            extension .json).
            This can be a simple string; The use of Path is not necessary.
        compresslevel : int
            An int from 0 to 9, where 0 is no compression and nine maximum
            compression. Compressed files will take less space, but will
            require more computation. The relationship between compression
            level and time required for the compression is not linear. For
            optimised performance, we suggest values between 2 and 6, with 4
            providing the best balance.
        """

        if emgfile["SOURCE"] in ["DEMUSE", "OTB", "CUSTOMCSV", "DELSYS"]:
            """
            We need to convert all the components of emgfile to a dictionary
            and then to json object.
            pd.DataFrame cannot be converted with json.dumps.
            Once all the elements are converted to json objects, we create a
            dict of json objects and dump/save it into a single json file.
            emgfile = {
                "SOURCE": SOURCE,
                "FILENAME": FILENAME,
                "RAW_SIGNAL": RAW_SIGNAL,
                "REF_SIGNAL": REF_SIGNAL,
                "ACCURACY": ACCURACY,
                "IPTS": IPTS,
                "MUPULSES": MUPULSES,
                "FSAMP": FSAMP,
                "IED": IED,
                "EMG_LENGTH": EMG_LENGTH,
                "NUMBER_OF_MUS": NUMBER_OF_MUS,
                "BINARY_MUS_FIRING": BINARY_MUS_FIRING,
                "EXTRAS": EXTRAS,
            }
            """

            # str or float
            # Directly convert str or float to a json format.
            source = json.dumps(emgfile["SOURCE"])
            filename = json.dumps(emgfile["FILENAME"])
            fsamp = json.dumps(emgfile["FSAMP"])
            ied = json.dumps(emgfile["IED"])
            emg_length = json.dumps(emgfile["EMG_LENGTH"])
            number_of_mus = json.dumps(emgfile["NUMBER_OF_MUS"])

            # df
            # Access and convert the df to a json object.
            # orient='split' is fundamental for performance.
            raw_signal = emgfile["RAW_SIGNAL"].to_json(orient='split')
            ref_signal = emgfile["REF_SIGNAL"].to_json(orient='split')
            accuracy = emgfile["ACCURACY"].to_json(orient='split')
            ipts = emgfile["IPTS"].to_json(orient='split')
            binary_mus_firing = emgfile["BINARY_MUS_FIRING"].to_json(orient='split')
            extras = emgfile["EXTRAS"].to_json(orient='split')

            # list of ndarray.
            # Every array has to be converted in a list; then, the list of
            # lists can be converted to json.
            mupulses = []
            for ind, array in enumerate(emgfile["MUPULSES"]):
                mupulses.insert(ind, array.tolist())
            mupulses = json.dumps(mupulses)

            # Convert a dict of json objects to json. The result of the
            # conversion will be saved as the final json file.
            emgfile = {
                "SOURCE": source,
                "FILENAME": filename,
                "RAW_SIGNAL": raw_signal,
                "REF_SIGNAL": ref_signal,
                "ACCURACY": accuracy,
                "IPTS": ipts,
                "MUPULSES": mupulses,
                "FSAMP": fsamp,
                "IED": ied,
                "EMG_LENGTH": emg_length,
                "NUMBER_OF_MUS": number_of_mus,
                "BINARY_MUS_FIRING": binary_mus_firing,
                "EXTRAS": extras,
            }

            # Compress and write the json file
            with gzip.open(
                filepath,
                "wt",
                encoding="utf-8",
                compresslevel=compresslevel,
            ) as f:
                json.dump(emgfile, f)

        elif emgfile["SOURCE"] in [
            "OTB_REFSIG",
            "CUSTOMCSV_REFSIG",
            "DELSYS_REFSIG"
        ]:
            """
            refsig = {
                "SOURCE": SOURCE,
                "FILENAME": FILENAME,
                "FSAMP": FSAMP,
                "REF_SIGNAL": REF_SIGNAL,
                "EXTRAS": EXTRAS,
            }
            """
            # str or float
            # Directly convert str or float to a json format.
            source = json.dumps(emgfile["SOURCE"])
            filename = json.dumps(emgfile["FILENAME"])
            fsamp = json.dumps(emgfile["FSAMP"])

            # df
            # Access and convert the df to a json object.
            ref_signal = emgfile["REF_SIGNAL"].to_json(orient='split')
            extras = emgfile["EXTRAS"].to_json(orient='split')

            # Merge all the objects in one dict
            refsig = {
                "SOURCE": source,
                "FILENAME": filename,
                "FSAMP": fsamp,
                "REF_SIGNAL": ref_signal,
                "EXTRAS": extras,
            }

            # Compress and save
            with gzip.open(
                filepath,
                "wt",
                encoding="utf-8",
                compresslevel=compresslevel,
            ) as f:
                json.dump(refsig, f)

        else:
            raise ValueError("\nFile source not recognised\n")
