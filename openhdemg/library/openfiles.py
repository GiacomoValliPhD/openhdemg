"""
Description
-----------
This module contains all the functions that are necessary to open or save
openhdemg binary files for modules and collections, in addition to
MATLAB (.mat), text (.txt), JSON (.json) or custom (.csv) files.
MATLAB files are used to store data from the DEMUSE, OTBiolab+ and Delsys
software while binary and JSON files are used to save and load files from this
library.

If you are using an openhdemg version >= 0.2, it is recommended to use binary
data (modules and collections), as these provide the best performance and
flexibility within the openhdemg framework, but also for optimal portability
across operating systems and storage in private and public repositories.
Indeed, our binary structures allow to compress files and check their
integrity, if needed.

The content of the loaded emgfile can differ depending on the file type.
In general, decomposed files are dictionaries containing at least the following
keys:

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
    "BINARY_MUS_FIRING" : binary representation of MUs firings
    "EXTRAS" : additional custom values in a pd.DataFrame

More keys might be present if additional pd.DataFrames or Dictionaries are
present in the emgfiles saved with 'save_emgfile_module'.

Similarly, less keys might be present if there is no decomposition result or no
EMG signal.

As an example, when files are loaded with just the reference signal:

    "SOURCE": source of the file (i.e., "CUSTOMCSV_REFSIG", "OTB_REFSIG", "DELSYS_REFSIG")
    "FILENAME" : the name of the opened file
    "FSAMP": sampling frequency
    "REF_SIGNAL": the reference signal
    "EXTRAS" : additional custom values

Additional information can be found in the info module (emg.info()) and in
the function's description.
"""

# Some functions contained in this file are called internally and should not
# be exposed to the final user. Refer to the __init__ file.

import os
import sys
import gzip
import json
import copy
import shutil
import fnmatch
import hashlib
import platform
import warnings
from io import StringIO
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from scipy.io import loadmat

import openhdemg
from openhdemg.library.electrodes import (
    OTBelectrodes_ied, OTBelectrodes_Nelectrodes,
)
from openhdemg.library.mathtools import compute_sil
from openhdemg.library.tools import create_binary_firings, mupulses_from_binary

from openhdemg.ui.widgets import (
    run_custom_file_dialog, run_custom_directory_dialog,
)


# --------------------------------------------------------------------- #
# Functions to open binary openhdemg modules and collections.

def is_safe_openhdemg_folder(path, marker_name=".openhdemg_module"):
    """
    Check if a given folder is safe to overwrite as an openhdemg directory.

    This function verifies that the target folder:

    1. Exists and is a directory.
    2. Is not a dangerous system directory (like '/', 'C:\\', etc.).
    3. Contains the expected marker file (e.g., '.openhdemg_module' or
        '.openhdemg_collection') indicating it was previously created by
        openhdemg.

    Parameters
    ----------
    path : Path or str
        The path to check.
    marker_name : str, default '.openhdemg_module'
        The name of the marker file that identifies a valid openhdemg
        directory.

    Returns
    -------
    bool
        True if the folder is safe to remove or overwrite, False otherwise.

    Notes
    -----
    An empty folder is considered a safe folder.
    """

    path = Path(path).resolve()

    # 1. Sanity check
    if not path.exists():
        return False
    if not path.is_dir():
        return False

    # 2. Protect against system-critical or top-level folders
    system = platform.system().lower()
    # Common dangerous paths across all OSes
    dangerous_paths = {
        Path("/").resolve(),
        Path("/bin").resolve(),
        Path("/boot").resolve(),
        Path("/dev").resolve(),
        Path("/etc").resolve(),
        Path("/lib").resolve(),
        Path("/lib64").resolve(),
        Path("/mnt").resolve(),
        Path("/opt").resolve(),
        Path("/proc").resolve(),
        Path("/root").resolve(),
        Path("/run").resolve(),
        Path("/sbin").resolve(),
        Path("/srv").resolve(),
        Path("/sys").resolve(),
        Path("/usr").resolve(),
        Path("/var").resolve(),
        Path("/tmp").resolve(),
        Path("/home").resolve(),
        Path("/media").resolve(),
    }
    if system == "darwin":
        dangerous_paths.update({
            Path("/Applications").resolve(),
            Path("/System").resolve(),
            Path("/Users").resolve(),
            Path("/Volumes").resolve(),
        })
    elif system == "windows":
        dangerous_paths.update({
            Path("C:\\").resolve(),
            Path("C:\\Windows").resolve(),
            Path("C:\\Program Files").resolve(),
            Path("C:\\Program Files (x86)").resolve(),
            Path("C:\\Users").resolve(),
            Path("C:\\ProgramData").resolve(),
            Path(os.environ.get("TEMP", "C:\\Temp")).resolve(),
            Path("D:\\").resolve(),
            Path("E:\\").resolve(),
        })
    # Check dangerous directories
    if path in dangerous_paths:
        return False

    # 3. Verify it looks like an openhdemg folder
    marker = path / marker_name
    manifest = path / "manifest.json"
    if marker.exists() and manifest.exists():
        return True

    # 4. If folder is empty, it’s safe (nothing to lose)
    if not any(path.iterdir()):
        return True

    # Otherwise, treat as unsafe
    return False


def sha256_file(path, chunk_size=8192):
    """
    Compute the SHA-256 checksum of a file.

    Reads the file at the given path in binary mode and computes a
    SHA-256 hash over its contents in chunks to avoid excessive
    memory usage.

    Parameters
    ----------
    path : Path
        Path to the file for which the checksum should be computed.
    chunk_size : int, default 8192
        Number of bytes read per iteration.

    Returns
    -------
    str
        The SHA-256 hex digest of the file, prefixed with ``"sha256:"``.

    Examples
    --------
    >>> from pathlib import Path
    >>> sha256_file(Path("data.bin"))
    'sha256:9f2c2e6d14efc02e3f6b4f41a93d85e1b3...'
    """

    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(chunk_size), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def save_openhdemg_module(
    emgfile,
    path,
    module_name,
    filename=None,
    compresslevel=None,
    add_checksum=False,
):
    """
    Save an openhdemg module to a structured directory.

    This function serialises an `emgfile` into a folder containing a manifest
    file (``manifest.json``) and binary uncompressed or gzip-compressed data
    files. It supports optional checksum generation and performs automatic
    overwriting of existing module directories.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    path : str
        Directory where the module folder should be created. The use of
        absolute paths should be preferred.
    module_name : str
        Name of the module folder to create under ``path``.
    filename : str, default None
        Optional filename to override the existing ``emgfile["FILENAME"]``.
    compresslevel : {None, int}, default None
        Compression level (0-9). If ``None``, saves as raw binary files
        without compression. Saving the file without compression will allow
        for random access in the future (not yet implemented). Consider saving
        always uncompressed binary if you are working with large files. If you
        prefer working with compressed files to save space, we suggest using a
        `compresslevel=1`` for the best compression/performance balance.
    add_checksum : bool, default False
        If ``True``, compute and store a SHA-256 checksum for each
        binary file to enable integrity verification on load.
        Default is ``False``.

    Returns
    -------
    Path
        Path to the root directory where the openhdemg module has been saved.

    See also
    --------
    - asksavemodule : Select the folder where to save the module with an UI
        and save it.

    Notes
    -----
    If a folder with the same ``module_name`` already exists at ``path``,
    it will be completely overwritten.

    The resulting folder contains:

    - ``.openhdemg_module`` : Marker file indicating an openhdemg module
    - ``manifest.json`` : Metadata and file index
    - ``files/`` : Binary data files (optionally compressed)
    """

    # Create root folder based on file name and path
    root = Path(path).resolve() / module_name  # TODO resolve
    if root.exists():
        if is_safe_openhdemg_folder(
            path=root, marker_name=".openhdemg_module",
        ):
            shutil.rmtree(root)  # Overwrite folder content
        else:
            raise RuntimeError(f"Unsafe or unknown folder: {root}")
    root.mkdir(parents=True, exist_ok=True)

    # Create directory to store all the files
    files_path = root / "files"
    files_path.mkdir(parents=True, exist_ok=True)

    # Path to the manifest file for this module
    manifest_path = root / "manifest.json"
    manifest_path.touch(exist_ok=True)

    # Path to the marker file for this module
    marker_path = root / ".openhdemg_module"
    marker_path.touch(exist_ok=True)

    # "manifest.json" and ".openhdemg_module" determine an openhdemg
    # folder when is_safe_openhdemg_folder() is called.

    # Create the manifest file
    manifest = {
        # For monitoring and compatibility purposes
        "_metadata": {
            "created": datetime.now(timezone.utc).isoformat(),
            "system_byte_order": sys.byteorder,  # 'little' or 'big'
            "os": platform.system(),  # 'Windows', 'Linux', 'Darwin'
            "os_version": platform.version(),  # detailed version string
            "platform": platform.platform(),  # eg. 'Windows-10-10.0.19045-SP0'
            "python_version": platform.python_version(),
            "openhdemg_version": openhdemg.__version__,
            "data_structure_version": "1.0"
        },
        # For the actual emgfile
        "SOURCE": {
            "data_type": "str",
            "text": "OPENHDEMG",
        },
        "FILENAME": {
            "data_type": "str",
            "text": emgfile["FILENAME"] if filename is None else filename,
        },
        "FSAMP": {
            "data_type": "float",
            "value": emgfile["FSAMP"],
        },
    }

    # Make sure that these are json serialisable
    # np Dtypes are not!
    IED = emgfile.get("IED", None)
    if IED is not None:
        manifest["IED"] = {
            "data_type": "float",
            "value": float(emgfile["IED"]),
        }

    EMG_LENGTH = emgfile.get("EMG_LENGTH", None)
    if EMG_LENGTH is not None:
        manifest["EMG_LENGTH"] = {
            "data_type": "int",
            "value": int(emgfile["EMG_LENGTH"]),
        }

    NUMBER_OF_MUS = emgfile.get("NUMBER_OF_MUS", None)
    if NUMBER_OF_MUS is not None:
        manifest["NUMBER_OF_MUS"] = {
            "data_type": "int",
            "value": int(emgfile["NUMBER_OF_MUS"]),
        }

    # Add any custom informative dict to the manifest
    dicts_keys = [key for key, val in emgfile.items() if isinstance(val, dict)]
    if len(dicts_keys) > 0:
        for key in dicts_keys:
            # Verify if the dict is json serialisable
            try:
                json.dumps(emgfile[key])
            except (TypeError, OverflowError):
                warnings.warn(
                    message=(
                        f"The dict {key} is not json serialisable. "
                        "It will not be saved"
                    )
                )
                continue
            manifest[key] = {
                "data_type": "dict",
                "value": emgfile[key],
            }

    # Save any DataFrames and reference in manifest
    df_keys = [
        key for key, val in emgfile.items() if isinstance(val, pd.DataFrame)
    ]
    for key in df_keys:
        # Verify if the dataframe contains data
        df = emgfile.get(key, None)
        if df.empty:
            # Add info to the manifest
            manifest[key] = {
                "data_type": "empty pd.DataFrame",
                "columns": list(df.columns),
                "columns_dtypes": [type(c).__name__ for c in df.columns],
                "shape": list(df.shape),
            }
            continue

        # np.ascontiguousarray returns a contiguous array (ndim >= 1) in C
        # order. It also forces a common data type to the one of highest
        # precision.
        arr = np.ascontiguousarray(df.to_numpy())

        # Write file
        if compresslevel is None:
            # Uncompressed
            out_path = files_path / f"{key}.bin"
            compression = None
            with open(out_path, "wb") as f:
                f.write(arr.tobytes())
        else:
            # Compressed
            out_path = files_path / f"{key}.bin.gz"
            compression = "gzip"
            with gzip.open(out_path, "wb", compresslevel=compresslevel) as f:
                f.write(arr.tobytes())

        # Add checksum for integrity checks if desired
        if add_checksum:
            checksum = sha256_file(out_path)
        else:
            checksum = None

        # Add info to the manifest
        manifest[key] = {
            "data_type": "pd.DataFrame",
            "data_file_path": str(out_path.relative_to(root)),
            "compression": compression,
            "order": "C",
            "columns": list(df.columns),
            "columns_dtypes": [type(c).__name__ for c in df.columns],
            "shape": list(arr.shape),
            "dtypes": [str(dtype) for dtype in df.dtypes],
            "endian_dtype": arr.dtype.str,
            "checksum": checksum
        }

    # Save MUPULSES and REFERENCE_MUPULSES and reference them in manifest
    for mupulses_name in ["MUPULSES", "REFERENCE_MUPULSES"]:
        MUPULSES = emgfile.get(mupulses_name, None)
        if MUPULSES is not None:

            MUPULSES_offsets = []
            MUPULSES_lengths = []
            dtypes = []
            endian_dtypes = []

            # Write file
            if compresslevel is None:
                # Uncompressed
                MUPULSES_path = files_path / f"{mupulses_name}.bin"
                compression = None
                with open(MUPULSES_path, "wb") as f:
                    pos = 0
                    # Save as a ragged array with reference to split points
                    for arr in MUPULSES:
                        arr = np.ascontiguousarray(arr)
                        f.write(arr.tobytes())
                        MUPULSES_lengths.append(arr.shape[0])
                        MUPULSES_offsets.append(pos)
                        dtypes.append(str(arr.dtype))
                        endian_dtypes.append(arr.dtype.str)
                        pos += arr.nbytes
            else:
                # Compressed
                MUPULSES_path = files_path / f"{mupulses_name}.bin.gz"
                compression = "gzip"
                with gzip.open(
                    MUPULSES_path, "wb", compresslevel=compresslevel,
                ) as f:
                    pos = 0
                    # Save as a ragged array with reference to split points
                    for arr in MUPULSES:
                        arr = np.ascontiguousarray(arr)
                        f.write(arr.tobytes())
                        MUPULSES_lengths.append(arr.shape[0])
                        MUPULSES_offsets.append(pos)
                        dtypes.append(str(arr.dtype))
                        endian_dtypes.append(arr.dtype.str)
                        pos += arr.nbytes

            # Add checksum for integrity checks if desired
            if add_checksum:
                checksum = sha256_file(MUPULSES_path)
            else:
                checksum = None

            # Add info to the manifest
            manifest[mupulses_name] = {
                "data_type": "list_of_1D_np.ndarray",  # e.g., (137,)  # TODO document this
                "data_file_path": str(MUPULSES_path.relative_to(root)),
                "compression": compression,
                "order": "C",
                "lengths": MUPULSES_lengths,
                "offsets": MUPULSES_offsets,
                "dtypes": dtypes,
                "endian_dtypes": endian_dtypes,
                "checksum": checksum
            }

    # Save the manifest file
    manifest_path.write_text(json.dumps(manifest, indent=4))

    # Return the folder where the openhdemg module has been saved
    return root


def asksavemodule(
    emgfile,
    filename=None,
    compresslevel=None,
    add_checksum=False,
):
    """
    Select or create the folder where to save the module with an UI.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    filename : str or None, default None
        Optional filename to override the existing ``emgfile["FILENAME"]``.
        If ``None``, the saving name will be used.
    compresslevel : {None, int}, default None
        Compression level (0-9). If ``None``, saves as raw binary files
        without compression. Saving the file without compression will allow
        for random access in the future (not yet implemented). Consider saving
        always uncompressed binary if you are working with large files. If you
        prefer working with compressed files to save space, we suggest using a
        `compresslevel=1`` for the best compression/performance balance.
    add_checksum : bool, default False
        If ``True``, compute and store a SHA-256 checksum for each
        binary file to enable integrity verification on load.
        Default is ``False``.

    Returns
    -------
    Path
        Path to the root directory where the openhdemg module has been saved.

    See also
    --------
    - save_openhdemg_module : Save an openhdemg module to a structured
        directory.

    Notes
    -----
    If a folder with the same ``module_name`` already exists at ``path``,
    it will be completely overwritten.

    The resulting folder contains:

    - ``.openhdemg_module`` : Marker file indicating an openhdemg module
    - ``manifest.json`` : Metadata and file index
    - ``files/`` : Binary data files (optionally compressed)
    """

    # Get the filepath
    dirpath = run_custom_directory_dialog(
        window_title="Select a folder to save the module",
        mode="save",
    )
    parent_path, dirname = os.path.split(dirpath)

    print("\n---------------\nSaving module\n")

    # Save the module
    path = save_openhdemg_module(
        emgfile=emgfile,
        path=parent_path,
        module_name=dirname,
        filename=dirname if filename is None else filename,
        compresslevel=compresslevel,
        add_checksum=add_checksum,
    )

    print(f"Module saved at {path}\n---------------\n")

    return path


def load_openhdemg_module(
    path,
    module_name,
    verify_checksum=False,
    return_metadata=False,
):
    """
    Load an openhdemg module saved with `save_openhdemg_module`.

    This function reconstructs the original `emgfile` dictionary
    (including pandas DataFrames and NumPy arrays) from the directory
    created by `save_openhdemg_module`. Optionally, it verifies the integrity
    of stored binary files using SHA-256 checksums if they are present in
    the manifest.

    Parameters
    ----------
    path : str
        Directory containing the module folder. The use of absolute paths
        should be preferred.
    module_name : str
        Name of the module folder to load. The module folder is the one
        containing the module's ``manifest.json`` file and associated binary
        files.
    verify_checksum : bool, default False
        If ``True``, verify SHA-256 checksums of all data files when
        present in the manifest.
    return_metadata : bool, default False
        Whether to return the module metadata. If true, an additional object
        is returned.

    Returns
    -------
    emgfile : dict
        A reconstructed dictionary representing the original `emgfile`.
        Keys and values mirror those in the saved structure, including:

            - Scalar data (e.g. ``FSAMP``, ``EMG_LENGTH``)
            - ``pandas.DataFrame`` objects
            - Lists of NumPy array (``MUPULSES``)
            - Other emgfile-related metadata from the manifest
    metadata : dict
        This is returned only if ``return_metadata`` is ``True``. An example of
        it content is:

            - "created": "2025-10-06T15:36:11.084657+00:00",
            - "system_byte_order": "little",
            - "os": "Windows",
            - "os_version": "10.0.19045",
            - "platform": "Windows-10-10.0.19045-SP0",
            - "python_version": "3.13.1",
            - "openhdemg_version": "0.2.0-beta.1",
            - "data_structure_version": "1.0"

    See also
    --------
    - askloadmodule : Select the module folder to load with an UI.

    Raises
    ------
    FileNotFoundError
        If the manifest file (``manifest.json``) is missing from the module
        directory.
    ValueError
        If ``verify_checksum`` is enabled and a checksum mismatch is detected.
    Warning
        If unexpected keys or malformed entries are found in the manifest.
    """

    # Read the manifest file
    root = Path(path).resolve()
    root = root / module_name
    manifest_path = root / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found at {root}")
    manifest = json.loads(manifest_path.read_text())

    # Initialise emgfile dict
    emgfile = {}

    # Remove _metadata
    _metadata = manifest.pop("_metadata")

    # Load all the present data
    for key, info in manifest.items():
        if not isinstance(info, dict):
            warnings.warn(f"Unexpected manifest description for key: '{key}'")
            continue

        # str
        if info["data_type"] == "str":
            emgfile[key] = str(info["text"])

        # float
        if info["data_type"] == "float":
            emgfile[key] = float(info["value"])

        # int
        if info["data_type"] == "int":
            emgfile[key] = int(info["value"])

        # dict
        if info["data_type"] == "dict":
            emgfile[key] = info["value"]

        # pd.DataFrame
        if info["data_type"] == "pd.DataFrame":
            file_path = root / info["data_file_path"]
            # Verify checksum
            if verify_checksum and info.get("checksum") is not None:
                hash_val = sha256_file(file_path)
                if hash_val != info["checksum"]:
                    raise ValueError(
                        f"Checksum mismatch for {key}. "
                        f"Expected {info['checksum']}, got {hash_val}."
                    )
            # Load file
            if info.get("compression") == "gzip":
                with gzip.open(file_path, "rb") as f:
                    arr = np.frombuffer(
                        f.read(), dtype=info["endian_dtype"],
                    )
            else:
                with open(file_path, "rb") as f:
                    arr = np.fromfile(f, dtype=info["endian_dtype"])
                    # TODO this allows to avoid preloading the data into
                    # memory and will allow for partial loading.
            # Reshape and assign columns dtypes
            arr = arr.reshape(info["shape"], order=info["order"])
            columns = []
            for val, tname in zip(info["columns"], info["columns_dtypes"]):
                if tname == "int":
                    val = int(val)
                elif tname == "float":
                    val = float(val)
                columns.append(val)  # str fine as is
            df = pd.DataFrame(arr, columns=columns)
            for col, dtype_str in zip(df.columns, info["dtypes"]):
                df[col] = df[col].astype(dtype_str)
            # Assign
            emgfile[key] = df

        # empty pd.DataFrame
        if info["data_type"] == "empty pd.DataFrame":
            columns = []
            for val, tname in zip(info["columns"], info["columns_dtypes"]):
                if tname == "int":
                    val = int(val)
                elif tname == "float":
                    val = float(val)
                columns.append(val)  # str fine as is
            df = pd.DataFrame(columns=columns)
            # Assign
            emgfile[key] = df

        # Load list of 1D arrays (MUPULSES)
        if info["data_type"] == "list_of_1D_np.ndarray":
            file_path = root / info["data_file_path"]
            # Verify checksum
            if verify_checksum and info.get("checksum") is not None:
                hash_val = sha256_file(file_path)
                if hash_val != info["checksum"]:
                    raise ValueError(
                        f"Checksum mismatch for {key}. "
                        f"Expected {info['checksum']}, got {hash_val}."
                    )
            # Load file
            opener = gzip.open if info.get("compression") == "gzip" else open
            with opener(file_path, "rb") as f:
                raw_bytes = f.read()
            # Split different MUs
            offsets = info["offsets"]
            lengths = info["lengths"]
            endian_dtypes = info["endian_dtypes"]
            arrays = []
            for offset, length, edtype in zip(offsets, lengths, endian_dtypes):
                dt = np.dtype(edtype)
                nbytes = dt.itemsize * length
                arr = np.frombuffer(
                    raw_bytes[offset: offset + nbytes], dtype=edtype,
                )
                arrays.append(arr)
            emgfile[key] = arrays

    # Return required objects
    if return_metadata:
        return emgfile, _metadata
    else:
        return emgfile


def askloadmodule(
    verify_checksum=False,
    return_metadata=False,
    return_path=False,
):
    """
    Select the module folder to load with an UI and load it.

    This function reconstructs the original `emgfile` dictionary
    (including pandas DataFrames and NumPy arrays) from the directory
    created by `save_openhdemg_module`. Optionally, it verifies the integrity
    of stored binary files using SHA-256 checksums if they are present in
    the manifest.

    Parameters
    ----------
    verify_checksum : bool, default False
        If ``True``, verify SHA-256 checksums of all data files when
        present in the manifest.
    return_metadata : bool, default False
        Whether to return the module metadata. If true, an additional object
        is returned.
    return_path : bool, default False
        Whether to return the path to the module, including module name.

    Returns
    -------
    emgfile : dict
        A reconstructed dictionary representing the original `emgfile`.
        Keys and values mirror those in the saved structure, including:

            - Scalar data (e.g. ``FSAMP``, ``EMG_LENGTH``)
            - ``pandas.DataFrame`` objects
            - Lists of NumPy array (``MUPULSES``)
            - Other emgfile-related metadata from the manifest
    metadata : dict, optional
        This is returned only if ``return_metadata`` is ``True``. An example of
        it content is:

            - "created": "2025-10-06T15:36:11.084657+00:00",
            - "system_byte_order": "little",
            - "os": "Windows",
            - "os_version": "10.0.19045",
            - "platform": "Windows-10-10.0.19045-SP0",
            - "python_version": "3.13.1",
            - "openhdemg_version": "0.2.0-beta.1",
            - "data_structure_version": "1.0"
    path : pathlib.Path, optional
        The resolved (absolute) path to the module, including module name.
        This is returned only if ``return_path`` is ``True``.

    See also
    --------
    - load_openhdemg_module : Load an openhdemg module saved with
        `save_openhdemg_module`.

    Raises
    ------
    FileNotFoundError
        If the manifest file (``manifest.json``) is missing from the module
        directory.
    ValueError
        If ``verify_checksum`` is enabled and a checksum mismatch is detected.
    RuntimeError
        If the selected directory is not a valid openhdemg module folder.
    Warning
        If unexpected keys or malformed entries are found in the manifest.
    """

    path_to_module = run_custom_directory_dialog(
        window_title="Select the module folder to load"
    )

    # Check if a file has been selected. If not, return None
    if path_to_module is None:
        return path_to_module

    if not is_safe_openhdemg_folder(
        path=path_to_module,
        marker_name=".openhdemg_module",
    ):
        raise RuntimeError(
            f"'{path_to_module}' is not a valid openhdemg module folder."
        )

    print("\n--------------\nLoading module\n")

    # Open file
    path = Path(path_to_module).resolve()
    res = load_openhdemg_module(
        path=path.parent,
        module_name=path.name,
        verify_checksum=verify_checksum,
        return_metadata=return_metadata,
    )

    print("\n--------------\nModule loaded\n")

    if return_path is True:
        return res, path
    else:
        return res


class openhdemg_Collection():
    """
    A container for managing openhdemg collections.

    This class represents a collection of openhdemg modules, along with
    shared data (e.g. reference signals) and  participant metadata.
    It provides methods to set, retrieve, and reset each component, and to
    save/load the entire collection to disk in a structured and versioned
    format.

    Attributes
    ----------
    root : pathlib.Path or None
        Root directory where the collection is saved.
    manifest_path : pathlib.Path or None
        Path to the manifest file (``manifest.json``).
    marker_path : pathlib.Path or None
        Path to the marker file (``.openhdemg_collection``) identifying
        a valid collection directory.
    modules : dict
        Dictionary of openhdemg modules belonging to the collection.
    shared_dataframe : pandas.DataFrame or None
        Shared data (e.g. reference or synchronisation signals).
    participant_info : dict or None
        Dictionary containing participant-level metadata (e.g. ID, age, etc.).
    manifest : dict
        Dictionary describing the structure and metadata of the collection.

    Methods
    -------
    set_root()
        Define the root directory for the collection.
    get_root()
        Return the collection root path as a string.
    reset_root()
        Reset root and related paths to None.
    set_shared_dataframe()
        Assign a shared DataFrame for data common to all the modules.
    get_shared_dataframe()
        Retrieve a deep copy of the shared DataFrame.
    reset_shared_dataframe()
        Reset the shared DataFrame to None.
    set_participant_info()
        Set and validate participant information (must be JSON serialisable).
    get_participant_info()
        Retrieve a deep copy of participant information.
    reset_participant_info()
        Reset the participant information to None.
    add_module()
        Add a module to the collection.
    get_module()
        Retrieve a module by name.
    remove_module()
        Remove a module from the collection.
    save_module()
        Save a single module to disk.
    save_shared_dataframe()
        Save the shared DataFrame to disk and update the manifest.
    save_manifest()
        Write the current manifest file (``manifest.json``).
    save()
        Save the entire collection to disk, overwriting existing content.
    asksave()
        Save the entire collection to disk using a UI to select the location.
    load_manifest()
        Load the manifest file (manifest.json) and update internal metadata.
    load_module()
        Load a specific module from disk and add it to the collection.
    load_shared_dataframe()
        Load the shared DataFrame from disk and add it to the collection.
    load()
        Load the entire openhdemg collection from disk.
    askload()
        Load the entire openhdemg collection using an UI to select the
        directory.
    """

    def __init__(self):
        self.root = None
        self.manifest_path = None
        self.marker_path = None
        self.modules = {}
        self.shared_dataframe = None
        self.participant_info = None
        self.manifest = {
            # For monitoring and compatibility purposes
            "_metadata": {
                "created": datetime.now(timezone.utc).isoformat(),
                "edited": None,
                "os": platform.system(),  # 'Windows', 'Linux', 'Darwin'
                "python_version": platform.python_version(),
                "openhdemg_version": openhdemg.__version__,
                "data_structure_version": "1.0"
            },
            # Modified by the user
            "modules": [],
            "shared_dataframe": None,
            "participant_info": None,
        }

    def set_root(self, root):
        """
        Define the root directory for the collection.

        Parameters
        ----------
        root : str or pathlib.Path
            Path to the root directory where the collection will be saved.
        """

        self.root = Path(root).resolve()
        self.manifest_path = self.root / "manifest.json"
        self.marker_path = self.root / ".openhdemg_collection"

    def get_root(self):
        """
        Return the root directory.

        Returns
        -------
        str
            Absolute path of the collection root directory.
        """

        return str(self.root)

    def reset_root(self):
        """
        Reset root and related paths to ``None``.
        """

        self.root = None
        self.manifest_path = None
        self.marker_path = None

    def set_shared_dataframe(self, df):
        """
        Set the shared DataFrame for the collection.

        This DataFrame should contain data that is common across modules
        (e.g. triggers, reference signals, synchronisation traces).

        Parameters
        ----------
        df : pandas.DataFrame
            Shared data to attach to the collection. A deep copy is stored.
        """

        self.shared_dataframe = copy.deepcopy(df)

    def get_shared_dataframe(self):
        """
        Get a deep copy of the shared DataFrame.

        Returns
        -------
        pandas.DataFrame or None
            The shared DataFrame, or ``None`` if not set.
        """

        return copy.deepcopy(self.shared_dataframe)

    def reset_shared_dataframe(self):
        """
        Reset the shared_dataframe to ``None``.
        """

        self.shared_dataframe = None

    def set_participant_info(self, info):
        """
        Set participant information and ensure it is JSON serialisable.

        Parameters
        ----------
        info : dict
            Dictionary containing participant details such as ID, age,
            height, weight, and notes.

        Raises
        ------
        TypeError
            If the dictionary is not JSON serialisable.
        """

        # Verify if the dict is json serialisable
        try:
            json.dumps(info)
        except (TypeError, OverflowError) as e:
            raise TypeError(
                "The 'info' dictionary is not JSON serialisable. "
                "It cannot be stored or saved."
            ) from e

        # Update participant_info and the manifest
        self.participant_info = copy.deepcopy(info)

    def get_participant_info(self):
        """
        Get a deep copy of participant information.

        Returns
        -------
        dict or None
            Participant information, or ``None`` if not set.
        """

        return copy.deepcopy(self.participant_info)

    def reset_participant_info(self):
        """
        Reset the participant_info to ``None`` and update the manifest
        accordingly.
        """

        self.participant_info = None

    def add_module(self, module, module_name, replace=True):
        """
        Add a module to the collection.

        Parameters
        ----------
        module : dict
            Module data to add.
        module_name : str
            Name of the module (used as an identifier).
        replace : bool, default=True
            If ``False``, a warning is raised and the module is not replaced
            when a module with the same name already exists.

        Warns
        -----
        UserWarning
            If ``replace=False`` and the module already exists.
        """

        if replace is False:
            if self.modules.get(module_name, None) is not None:
                warnings.warn(
                    message=(
                        f"Module {module_name} is already present. "
                        "The module was not added. You can change this "
                        "behaviour with 'replace=True'"
                    )
                )
                return
        self.modules[module_name] = module

    def get_module(self, module_name):
        """
        Retrieve a module by name.

        Parameters
        ----------
        module_name : str
            Name of the module.

        Returns
        -------
        dict or None
            A deep copy of the module dictionary, or ``None`` if not found.
        """

        return copy.deepcopy(self.modules.get(module_name, None))

    def remove_module(self, module_name):
        """
        Remove a module from the collection and its reference from the
        manifest.

        Parameters
        ----------
        module_name : str
            Name of the module to remove.

        Returns
        -------
        dict
            A deep copy of the removed module.

        Raises
        ------
        KeyError
            If the key is not found.
        """

        removed_module = self.modules.pop(module_name)

        # Remove module key from manifest.
        # Do not enforce it since self.manifest["modules"] will not contain
        # anything until first save.
        if module_name in self.manifest["modules"]:
            self.manifest["modules"].remove(module_name)

        return copy.deepcopy(removed_module)

    def save_module(
        self,
        module_name,
        filename=None,
        compresslevel=None,
        add_checksum=False,
        save_updated_manifest=True,
    ):
        """
        Save an individual module to disk.

        Parameters
        ----------
        module_name : str
            Name of the module to save.
        filename : str, default None
            Optional filename to override the existing ``emgfile["FILENAME"]``.
        compresslevel : {None, int}, default None
            Compression level (0-9). If ``None``, saves as raw binary files
            without compression. Saving the file without compression will allow
            for random access in the future (not yet implemented). Consider
            saving always uncompressed binary if you are working with large
            files. If you prefer working with compressed files to save space,
            we suggest using a `compresslevel=1`` for the best
            compression/performance balance.
        add_checksum : bool, default False
            If ``True``, compute and store a SHA-256 checksum for each
            binary file to enable integrity verification on load.
            Default is ``False``.
        save_updated_manifest : bool, default True
            If True, automatically save also the updated manifest. If False,
            The user should take care of this by calling the ``save_manifest``
            method.

        Raises
        ------
        ValueError
            If the module does not exist in the collection.
        """

        # Check if the root is set.
        self._check_root_set()

        # Check if the data to save is present.
        module = self.modules.get(module_name, None)
        if not isinstance(module, dict):
            raise ValueError(
                f"module '{module_name}' not found. Available modules "
                f"are: {self.modules.keys()}"
            )

        save_openhdemg_module(
            emgfile=module,
            path=self.root,
            module_name=module_name,
            filename=filename,
            compresslevel=compresslevel,
            add_checksum=add_checksum,
        )

        if module_name not in self.manifest["modules"]:
            self.manifest["modules"].append(module_name)

        if save_updated_manifest is True:
            self.save_manifest()

    def save_shared_dataframe(
        self,
        compresslevel=None,
        add_checksum=False,
        save_updated_manifest=True,
    ):
        """
        Save the shared DataFrame to disk.

        Parameters
        ----------
        compresslevel : {None, int}, default None
            Compression level (0-9). If ``None``, saves as raw binary files
            without compression. Saving the file without compression will allow
            for random access in the future (not yet implemented). Consider
            saving always uncompressed binary if you are working with large
            files. If you prefer working with compressed files to save space,
            we suggest using a `compresslevel=1`` for the best
            compression/performance balance.
        add_checksum : bool, default False
            If ``True``, compute and store a SHA-256 checksum for each
            binary file to enable integrity verification on load.
            Default is ``False``.
        save_updated_manifest : bool, default True
            If True, automatically save also the updated manifest. If False,
            The user should take care of this by calling the ``save_manifest``
            method.

        Warns
        -----
        UserWarning
            If no shared DataFrame is set or if it is empty.
        """

        # Check if the root is set.
        self._check_root_set()

        # Additional checks
        df = self.shared_dataframe
        if df is None:
            warnings.warn(
                "No shared_dataframe has been set. Use the "
                "'set_shared_dataframe' method before saving."
            )
            return
        if not isinstance(df, pd.DataFrame):
            raise ValueError(
                "The shared_dataframe must be a pd.DataFrame. " +
                f"It is a {type(df)} instead."
            )
        if df.empty:
            warnings.warn("Empty shared_dataframe has not been saved")
            return

        # np.ascontiguousarray returns a contiguous array (ndim >= 1) in C
        # order. It also forces a common data type to the one of highest
        # precision.
        arr = np.ascontiguousarray(df.to_numpy())

        # Write file
        if compresslevel is None:
            # Uncompressed
            out_path = self.root / "shared_dataframe.bin"
            compression = None
            with open(out_path, "wb") as f:
                f.write(arr.tobytes())
        else:
            # Compressed
            out_path = self.root / "shared_dataframe.bin.gz"
            compression = "gzip"
            with gzip.open(out_path, "wb", compresslevel=compresslevel) as f:
                f.write(arr.tobytes())

        # Add checksum for integrity checks if desired
        if add_checksum:
            checksum = sha256_file(out_path)
        else:
            checksum = None

        # Add info to the manifest
        self.manifest["shared_dataframe"] = {
            "data_type": "pd.DataFrame",
            "data_file_path": str(out_path.relative_to(self.root)),
            "compression": compression,
            "order": "C",
            "columns": list(df.columns),
            "columns_dtypes": [type(c).__name__ for c in df.columns],
            "shape": list(arr.shape),
            "dtypes": [str(dtype) for dtype in df.dtypes],
            "endian_dtype": arr.dtype.str,
            "checksum": checksum
        }

        if save_updated_manifest is True:
            self.save_manifest()

    def save_manifest(self):
        """
        Write the current manifest to disk in JSON format.
        """

        # Check if the root is set.
        self._check_root_set()

        # Add participant info to the manifest
        if self.participant_info is not None:
            self.manifest["participant_info"] = {
                "data_type": "dict",
                "value": self.participant_info,
            }

        # Update the manifest _metadata
        self.manifest["_metadata"]["edited"] = datetime.now(
            timezone.utc
        ).isoformat()
        self.manifest["_metadata"]["os"] = platform.system()
        self.manifest["_metadata"]["python_version"] = platform.python_version()
        self.manifest["_metadata"]["openhdemg_version"] = openhdemg.__version__
        self.manifest["_metadata"]["data_structure_version"] = "1.0"

        self.manifest_path.write_text(json.dumps(self.manifest, indent=4))

    def save(
        self,
        update_filename=True,
        compresslevel=None,
        add_checksum=False,
    ):
        """
        Save the entire collection to disk.

        Deletes any pre-existing content in the target directory if it is
        recognised as a valid openhdemg folder (checked via marker file).

        Parameters
        ----------
        update_filename : bool, default True
            If True, override the existing ``emgfile["FILENAME"]`` for all
            modules to match module name.
        compresslevel : {None, int}, default None
            Compression level (0-9). If ``None``, saves as raw binary files
            without compression. Saving the file without compression will allow
            for random access in the future (not yet implemented). Consider
            saving always uncompressed binary if you are working with large
            files. If you prefer working with compressed files to save space,
            we suggest using a `compresslevel=1`` for the best
            compression/performance balance.
        add_checksum : bool, default False
            If ``True``, compute and store a SHA-256 checksum for each
            binary file to enable integrity verification on load.
            Default is ``False``.

        Raises
        ------
        ValueError
            If root is not set or no modules have been added.
        RuntimeError
            If the target folder is not a safe openhdemg folder.
        """

        # Check if the root is set.
        self._check_root_set()

        # Check if the data to save is present.
        if not self.modules:
            raise ValueError(
                "No modules were found to save. You can add new modules "
                "to the collection using the 'add_module' method."
            )

        # Check if the folder exists and can be overwritten
        if self.root.exists():
            if is_safe_openhdemg_folder(
                path=self.root, marker_name=self.marker_path.name,
            ):
                shutil.rmtree(self.root)  # Overwrite folder content
            else:
                raise RuntimeError(f"Unsafe or unknown folder: {self.root}")
        self.root.mkdir(parents=True, exist_ok=True)

        # Create a manifest and marker file for this module
        self.manifest_path.touch(exist_ok=True)
        self.marker_path.touch(exist_ok=True)

        # Save modules and update manifest
        for module_name in self.modules.keys():
            self.save_module(
                module_name=module_name,
                filename=module_name if update_filename else None,
                compresslevel=compresslevel,
                add_checksum=add_checksum,
                save_updated_manifest=False,
            )

        # Save shared_dataframe and update manifest
        if self.shared_dataframe is not None:
            self.save_shared_dataframe(
                compresslevel=compresslevel, add_checksum=add_checksum,
            )

        # Save the updated manifest file (including participant info)
        self.save_manifest()

    def asksave(
        self,
        update_filename=True,
        compresslevel=None,
        add_checksum=False,
    ):
        """
        Save the entire collection to disk using an UI to select the target
        directory.

        Deletes any pre-existing content in the target directory if it is
        recognised as a valid openhdemg folder (checked via marker file).

        Parameters
        ----------
        update_filename : bool, default True
            If True, override the existing ``emgfile["FILENAME"]`` for all
            modules to match module name.
        compresslevel : {None, int}, default None
            Compression level (0-9). If ``None``, saves as raw binary files
            without compression. Saving the file without compression will allow
            for random access in the future (not yet implemented). Consider
            saving always uncompressed binary if you are working with large
            files. If you prefer working with compressed files to save space,
            we suggest using a `compresslevel=1`` for the best
            compression/performance balance.
        add_checksum : bool, default False
            If ``True``, compute and store a SHA-256 checksum for each
            binary file to enable integrity verification on load.
            Default is ``False``.

        Raises
        ------
        ValueError
            If root is not set or no modules have been added.
        RuntimeError
            If the target folder is not a safe openhdemg folder.
        """

        # Get the module root
        root = run_custom_directory_dialog(
            window_title=(
                "Select or create a folder to contain the saved collection"
            )
        )
        self.set_root(root=root)

        print("\n-----------------\nSaving collection\n")

        # Save the module
        self.save(
            update_filename=update_filename,
            compresslevel=compresslevel,
            add_checksum=add_checksum,
        )

        print(f"Module saved at {root}\n-----------------\n")

    def load_manifest(self):
        """
        Load the manifest file (manifest.json) and update internal metadata.

        Returns
        -------
        dict
            Retrieve a deep copy of the loaded manifest dictionary.

        Raises
        ------
        ValueError
            If `manifest_path` is not set (e.g. `set_root()` not called).
        FileNotFoundError
            If the manifest file path is set but the file does not exist.
        """

        # Check if the root is set.
        self._check_root_set()

        # Additional checks
        if self.manifest_path is None:
            raise ValueError(
                "'manifest_path' not set. Use 'set_root()' "
                "before loading the manifest."
            )
        if not self.manifest_path.exists():
            raise FileNotFoundError(
                f"Manifest file not found at: {self.manifest_path}"
            )

        # Load the manifest
        self.manifest = json.loads(self.manifest_path.read_text())

        return copy.deepcopy(self.manifest)

    def load_module(
        self,
        module_name,
        verify_checksum=False,
        return_metadata=False,
    ):
        """
        Load a specific module from disk and add it to the collection.

        Parameters
        ----------
        module_name : str
            Name of the module folder to load. The module folder is the one
            containing the module's ``manifest.json`` file and associated
            binary files.
        verify_checksum : bool, default False
            If ``True``, verify SHA-256 checksums of all data files when
            present in the manifest.
        return_metadata : bool, default False
            Whether to return the module metadata. If true, an additional
            object is returned.

        Returns
        -------
        dict or (dict, dict)
            The loaded module dictionary, or a tuple ``(module, metadata)``
            if ``return_metadata=True``.

        Raises
        ------
        ValueError
            If the root is not set, if the manifest does not contain modules,
            if the specified module name is not listed in the manifest or if
            checksum verification fails.
        FileNotFoundError
            If the module file cannot be found at the expected path.
        """

        # Check if the root is set.
        self._check_root_set()

        # Check if any module is present in the manifest
        if len(self.manifest["modules"]) == 0:
            raise ValueError(
                "No module detected in the manifest. "
                "Try to use 'load_manifest()' first."
            )
        if module_name not in self.manifest["modules"]:
            raise ValueError(
                f"The module {module_name} is not listed in the manifest."
            )

        # Load the module
        if return_metadata is False:
            emgfile = load_openhdemg_module(
                path=self.root,
                module_name=module_name,
                verify_checksum=verify_checksum,
                return_metadata=return_metadata,
            )
        else:
            emgfile, metadata = load_openhdemg_module(
                path=self.root,
                module_name=module_name,
                verify_checksum=verify_checksum,
                return_metadata=return_metadata,
            )

        # Add the module to the collection
        self.add_module(
            module=emgfile,
            module_name=module_name,
            replace=True,
        )

        if return_metadata is False:
            return emgfile
        else:
            return emgfile, metadata

    def load_shared_dataframe(self, verify_checksum=False):
        """
        Load the shared DataFrame from disk and add it to the collection.

        Parameters
        ----------
        verify_checksum : bool, default False
            If ``True``, verify SHA-256 checksums of all data files when
            present in the manifest.

        Returns
        -------
        pandas.DataFrame
            A deep copy of the loaded shared DataFrame or None if not present.

        Raises
        ------
        ValueError
            If the root is not set, if the manifest does not contain
            a ``shared_dataframe`` entry, or if checksum verification fails.
        FileNotFoundError
            If the binary file corresponding to the shared DataFrame
            cannot be found at the expected path.
        """

        # Check if the root is set.
        self._check_root_set()

        # Check if the shared_dataframe key is present in the manifest
        info = self.manifest.get("shared_dataframe", False)
        if info is False:
            raise ValueError(
                "No 'shared_dataframe' key detected in the manifest. "
                "Try to use 'load_manifest()' first."
            )
        # Check if the shared_dataframe was saved and needs to be loaded
        if info is None:
            warnings.warn("No 'shared_dataframe' detected.")
            return None

        file_path = self.root / info["data_file_path"]

        # Verify checksum
        if verify_checksum and info.get("checksum") is not None:
            hash_val = sha256_file(file_path)
            if hash_val != info["checksum"]:
                raise ValueError(
                    f"Checksum mismatch for shared_dataframe. "
                    f"Expected {info['checksum']}, got {hash_val}."
                )
        # Load file
        if info.get("compression") == "gzip":
            with gzip.open(file_path, "rb") as f:
                arr = np.frombuffer(f.read(), dtype=info["endian_dtype"])
        else:
            with open(file_path, "rb") as f:
                arr = np.fromfile(f, dtype=info["endian_dtype"])
                # TODO this allows to avoid preloading the data into memory
                # and will allow for partial loading.
        # Reshape and assign columns dtypes
        arr = arr.reshape(info["shape"], order=info["order"])
        columns = []
        for val, tname in zip(info["columns"], info["columns_dtypes"]):
            if tname == "int":
                val = int(val)
            elif tname == "float":
                val = float(val)
            columns.append(val)  # str fine as is
        df = pd.DataFrame(arr, columns=columns)
        for col, dtype_str in zip(df.columns, info["dtypes"]):
            df[col] = df[col].astype(dtype_str)

        # Assign
        self.shared_dataframe = df

        return copy.deepcopy(self.shared_dataframe)

    def load(self, verify_checksum=False):
        """
        Load the entire openhdemg collection from disk.

        This method loads the manifest and reconstructs all modules and the
        shared DataFrame into memory. Use ``load_module`` or
        ``load_shared_dataframe`` instead for selective loading.

        Parameters
        ----------
        verify_checksum : bool, default False
            If ``True``, verifies the integrity of all binary files against the
            checksums stored in the manifest.

        Raises
        ------
        ValueError
            If the root is not set or if the target folder is not recognised
            as a valid openhdemg collection (missing or invalid marker file).
        FileNotFoundError
            If the root directory or manifest file does not exist.
        """

        # Check if the root is set.
        self._check_root_set()

        # Check if the root folder exists.
        if not self.root.exists():
            raise FileNotFoundError(f"Root folder does not exist: {self.root}")

        # Verify this is a valid openhdemg folder.
        if not is_safe_openhdemg_folder(
            path=self.root,
            marker_name=self.marker_path.name,
        ):
            raise RuntimeError(
                f"'{self.root}' is not a valid openhdemg collection folder."
            )

        # Verify the manifest exists
        if not self.manifest_path.exists():
            raise FileNotFoundError(
                f"Manifest file not found at: {self.manifest_path}"
            )

        # Load the manifest
        self.manifest = json.loads(self.manifest_path.read_text())

        # Load the modules
        for module in self.manifest["modules"]:
            self.load_module(
                module_name=module,
                verify_checksum=verify_checksum,
                return_metadata=False,
            )

        # Load the load_shared_dataframe
        self.load_shared_dataframe(verify_checksum=verify_checksum)

    def askload(self, verify_checksum=False):
        """
        Load the entire openhdemg collection from disk using an UI to select
        the directory.

        This method loads the manifest and reconstructs all modules and the
        shared DataFrame into memory. Use ``load_module`` or
        ``load_shared_dataframe`` instead for selective loading.

        Parameters
        ----------
        verify_checksum : bool, default False
            If ``True``, verifies the integrity of all binary files against the
            checksums stored in the manifest.

        Raises
        ------
        ValueError
            If the root is not set or if the target folder is not recognised
            as a valid openhdemg collection (missing or invalid marker file).
        FileNotFoundError
            If the root directory or manifest file does not exist.
        """

        # Get the module root
        root = run_custom_directory_dialog(
            window_title="Select the collection folder to load",
        )
        self.set_root(root=root)

        self.load(verify_checksum=verify_checksum)

    def _check_root_set(self):
        # Check if the root is set. Raise ValueError if not.
        if not isinstance(self.root, Path):
            raise ValueError(
                "'root' not set. Use the 'set_root' method first."
            )


# --------------------------------------------------------------------- #
# Function to open decomposed files coming from DEMUSE.

def emg_from_demuse(filepath, ignore_negative_ipts=False):
    """
    Import the .mat file decomposed in DEMUSE.

    Parameters
    ----------
    filepath : str or Path
        The directory and the name of the file to load
        (including file extension .mat).
        This can be a simple string, the use of Path is not necessary.
    ignore_negative_ipts : bool, default False
        This parameter determines the silhouette score estimation. If True,
        only positive ipts values are used during peak and noise clustering.
        This is particularly important for compensating sources with large
        negative components.

    Returns
    -------
    emgfile : dict
        A dictionary containing all the useful variables.

    See also
    --------
    - emg_from_otb : import the decomposed .mat file exportable by OTBiolab+.
    - refsig_from_otb : import REF_SIGNAL in the .mat file exportable by
        OTBiolab+.
    - emg_from_customcsv : Import custom data from a .csv file.
    - askopenfile : Select and open files with a GUI.

    Notes
    -----
    The returned file is called ``emgfile`` for convention.

    The demuse file contains 65 raw EMG channels (1 empty) instead of 64
    (as for OTB matrix standards) in the case of a 64 electrodes matrix.

    Structure of the emgfile:

        emgfile = {
            "SOURCE": SOURCE,
            "FILENAME": FILENAME,
            "RAW_SIGNAL": RAW_SIGNAL,
            "REF_SIGNAL": REF_SIGNAL,
            "ACCURACY": SIL
            "IPTS": IPTS,
            "MUPULSES": MUPULSES,
            "FSAMP": FSAMP,
            "IED": IED,
            "EMG_LENGTH": EMG_LENGTH,
            "NUMBER_OF_MUS": NUMBER_OF_MUS,
            "BINARY_MUS_FIRING": BINARY_MUS_FIRING,
            "EXTRAS": EXTRAS,
        }

    For DEMUSE files, the accuracy is estimated with the silhouette (SIL)
    score.

    Examples
    --------
    For an extended explanation of the imported emgfile:

    >>> import openhdemg.library as emg
    >>> emgfile = emg.emg_from_demuse(filepath="path/filename.mat")
    >>> info = emg.info()
    >>> info.data(emgfile)
    """

    # Load the .mat file
    mat_file = loadmat(filepath, simplify_cells=True)

    # Parse .mat obtained from DEMUSE to see the available variables
    """
    print(
        "\n--------------------------------\nAvailable dict keys are:\n\n{}\n".format(
            mat_file.keys()
        )
    )
    """

    # First, get the basic information and compulsory variables (i.e.,
    # RAW_SIGNAL, IPTS, MUPULSES, BINARY_MUS_FIRING) in a pd.DataFrame (df) or
    # list (for matlab cell arrays).

    # Use this to know the data source and name of the file
    SOURCE = "DEMUSE"
    FILENAME = os.path.basename(filepath)
    FSAMP = float(mat_file["fsamp"])
    IED = float(mat_file["IED"])

    # Get RAW_SIGNAL
    if "SIG" in mat_file.keys():
        mat = mat_file["SIG"].ravel(order="F")
        # "F" means to index the elements in column-major
        RAW_SIGNAL = pd.DataFrame(list(map(np.ravel, mat))).transpose()

    else:
        raise ValueError(
            "\nVariable 'SIG' not found in the .mat file\n"
        )

    # Get IPTS
    if "IPTs" in mat_file.keys():
        # Catch the exception of a single MU that would create an alrerady
        # transposed pd.DataFrame
        if len(mat_file["IPTs"].shape) == 1:
            IPTS = pd.DataFrame(mat_file["IPTs"])

        else:
            IPTS = pd.DataFrame(mat_file["IPTs"]).transpose()

    else:
        raise ValueError(
            "\nVariable 'IPTS' not found in the .mat file\n"
        )

    # Get EMG_LENGTH and NUMBER_OF_MUS
    EMG_LENGTH, NUMBER_OF_MUS = IPTS.shape

    # Get MUPULSES/BINARY_MUS_FIRING
    # Subtract 1 to MUPULSES because these are values in base 1 (MATLAB) and
    # manage exception of single MU thah would create a list and not a list of
    # arrays.
    if "MUPulses" in mat_file.keys():
        MUPULSES = list(mat_file["MUPulses"])
        for pos, pulses in enumerate(MUPULSES):
            MUPULSES[pos] = pulses - 1

        if NUMBER_OF_MUS == 1:
            MUPULSES = [np.array(MUPULSES)]

    else:
        raise ValueError(
            "\nVariable 'MUPulses' not found in the .mat file\n"
        )

    # Calculate BINARY_MUS_FIRING
    BINARY_MUS_FIRING = create_binary_firings(
        emg_length=EMG_LENGTH,
        number_of_mus=NUMBER_OF_MUS,
        mupulses=MUPULSES,
    )

    # Second, get/generate the other variables
    # Get REF_SIGNAL
    if "ref_signal" in mat_file.keys():
        # Catch the case for float values that cannot be directly added to a
        # dataframe
        if isinstance(mat_file["ref_signal"], float):
            res = {0: mat_file["ref_signal"]}
            REF_SIGNAL = pd.DataFrame(res, index=[0])

        else:
            REF_SIGNAL = pd.DataFrame(mat_file["ref_signal"])

    else:
        REF_SIGNAL = pd.DataFrame(columns=[0])
        warnings.warn(
            "\nVariable ref_signal not found in the .mat file, it might be necessary for some analyses\n"
        )

    # Estimate ACCURACY (SIL)
    if NUMBER_OF_MUS > 0:
        to_append = []
        for mu in range(NUMBER_OF_MUS):
            sil = compute_sil(
                ipts=IPTS[mu],
                mupulses=MUPULSES[mu],
                ignore_negative_ipts=ignore_negative_ipts,
            )
            to_append.append(sil)
        ACCURACY = pd.DataFrame(to_append)

    else:
        ACCURACY = pd.DataFrame(columns=[0])

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
        "EXTRAS": pd.DataFrame(columns=[0]),
    }

    return emgfile


# ---------------------------------------------------------------------
# Define functions used in the OTB openfile function.
# These functions are not exposed to the final user.

def get_otb_refsignal(df, refsig):
    """
    Extract the REF_SIGNAL from the OTB .mat file.

    Parameters
    ----------
    df : pd.DataFrame
        A pd.DataFrame containing all the informations extracted
        from the OTB .mat file.
    refsig : list
        Whether to seacrh also for the REF_SIGNAL and whether to load the full
        or sub-sampled one. The list is composed as [bool, str]. str can be
        "fullsampled" or "subsampled".
        Please read the documentation of emg_from_otb.

    Returns
    -------
    REF_SIGNAL : pd.DataFrame or np.nan
        A pd.DataFrame containing the requested variable
        or np.nan if the variable was not found.
    """

    assert refsig[0] in [
        True,
        False,
    ], f"refsig[0] must be 'true' or 'false'. {refsig[0]} was passed instead."
    assert refsig[1] in [
        "fullsampled",
        "subsampled",
    ], f"refsig[1] must be 'fullsampled' or 'subsampled'. {refsig[1]} was passed instead."

    if refsig[0] is True:
        if refsig[1] == "subsampled":
            # Extract the performed path (subsampled data)
            REF_SIGNAL_SUBSAMPLED = df.filter(regex="performed path")
            # Check if the REF_SIGNAL is available
            if not REF_SIGNAL_SUBSAMPLED.empty:
                REF_SIGNAL_SUBSAMPLED = REF_SIGNAL_SUBSAMPLED.rename(
                    columns={REF_SIGNAL_SUBSAMPLED.columns[0]: 0}
                )
                # Verify that there is no value above 100% since the
                # REF_SIGNAL is expected to be expressed as % of the MVC
                if max(REF_SIGNAL_SUBSAMPLED[0]) > 100:
                    warnings.warn(
                        "\nALERT! Ref signal greater than 100, did you use values normalised to the MVC?\n"
                    )

                return REF_SIGNAL_SUBSAMPLED

            else:
                warnings.warn(
                    "\nReference signal not found, it might be necessary for some analyses\n"
                )

                return pd.DataFrame(columns=[0])

        elif refsig[1] == "fullsampled":
            # Extract the acquired path (raw data)
            REF_SIGNAL_FULLSAMPLED = df.filter(regex="acquired data")
            if not REF_SIGNAL_FULLSAMPLED.empty:
                REF_SIGNAL_FULLSAMPLED = REF_SIGNAL_FULLSAMPLED.rename(
                    columns={REF_SIGNAL_FULLSAMPLED.columns[0]: 0}
                )
                # Verify that there is no value above 100% since the
                # REF_SIGNAL is expected to be expressed as % of the MVC
                if max(REF_SIGNAL_FULLSAMPLED[0]) > 100:
                    warnings.warn(
                        "\nALERT! Ref signal grater than 100, did you use values normalised to the MVC?\n"
                    )

                return REF_SIGNAL_FULLSAMPLED

            else:
                warnings.warn(
                    "\nReference signal not found, it might be necessary for some analyses\n"
                )

                return pd.DataFrame(columns=[0])

    else:
        warnings.warn("\nNot searched for reference signal, it might be necessary for some analyses\n")

        return pd.DataFrame(columns=[0])


def get_otb_decomposition(df):
    """
    Extract the IPTS and BINARY_MUS_FIRING from the OTB .mat file.

    Parameters
    ----------
    df : pd.DataFrame
        A pd.DataFrame containing all the informations extracted
        from the OTB .mat file.

    Returns
    -------
    IPTS, BINARY_MUS_FIRING : pd.DataFrame or np.nan
        pd.DataFrames containing the requested variables
        or np.nan if the variables were not found.
    """

    # Extract the IPTS and rename columns progressively
    IPTS = df.filter(regex="Source for decomposition")
    IPTS.columns = np.arange(len(IPTS.columns))
    # Verify to have the IPTS
    if IPTS.empty:
        raise ValueError(
            "\nSource for decomposition (IPTS) not found in the .mat file\n"
        )

    # Extract the BINARY_MUS_FIRING and rename columns progressively
    BINARY_MUS_FIRING = df.filter(regex="Decomposition of")
    BINARY_MUS_FIRING.columns = np.arange(len(BINARY_MUS_FIRING.columns))
    # Verify to have the BINARY_MUS_FIRING
    if BINARY_MUS_FIRING.empty:
        raise ValueError(
            "\nDecomposition of (BINARY_MUS_FIRING) not found in the .mat file\n"
        )

    return IPTS, BINARY_MUS_FIRING


def get_otb_ied(df):
    """
    Extract the IED from the OTB .mat file.

    Parameters
    ----------
    df : pd.DataFrame
        A pd.DataFrame containing all the informations extracted
        from the OTB .mat file.

    Returns
    -------
    IED : float
        The interelectrode distance in millimeters.
    """

    for matrix in OTBelectrodes_ied.keys():
        # Check the matrix used in the columns name
        # (in the df obtained from OTBiolab+)
        if matrix in str(df.columns):
            IED = float(OTBelectrodes_ied[matrix])

            return IED

    # If no matrix is found and we exit the loop:
    warnings.warn(
        "OTB recording grid not found, IED could not be inferred"
    )

    return np.nan


def get_otb_rawsignal(df, extras_regex):
    """
    Extract the raw signal from the OTB .mat file.

    Parameters
    ----------
    df : pd.DataFrame
        A pd.DataFrame containing all the informations extracted
        from the OTB .mat file.
    extras_regex : str
        A regex pattern unequivocally identifying the EXTRAS.

    Returns
    -------
    RAW_SIGNAL : pd.DataFrame
        A pd.DataFrame containing the RAW_SIGNAL.
    """

    # Drop all the known columns different from the raw EMG signal.
    # This is a workaround since the OTBiolab+ software does not export a
    # unique name for the raw EMG signal.
    base_pattern = "Source for decomposition|Decomposition of|acquired data|performed path"
    if extras_regex is None:
        pattern = base_pattern
    else:
        pattern = base_pattern + "|" + extras_regex

    emg_df = df[df.columns.drop(list(df.filter(regex=pattern)))]

    # Check if the number of remaining columns matches the expected number of
    # matrix channels.
    expectedchannels = np.nan
    for matrix in OTBelectrodes_Nelectrodes.keys():
        # Check the matrix used in the columns name (in the emg_df) to know
        # the number of expected channels.
        if matrix in str(emg_df.columns):
            expectedchannels = int(OTBelectrodes_Nelectrodes[matrix])
            break

    if expectedchannels is np.nan:
        raise ValueError("Matrix not recognised")

    if len(emg_df.columns) == expectedchannels:
        emg_df.columns = np.arange(len(emg_df.columns))
        RAW_SIGNAL = emg_df

        return RAW_SIGNAL

    else:
        # This check here is usefull to control that only the appropriate
        # elements have been included in the .mat file exported from OTBiolab+.
        raise ValueError(
            "\nFailure in searching the raw signal, please check that it is present in the .mat file and that only the accepted parameters have been included\n"
        )


def get_otb_extras(df, extras):
    """
    Extract the EXTRAS from the OTB .mat file.

    Parameters
    ----------
    df : pd.DataFrame
        A pd.DataFrame containing all the informations extracted
        from the OTB .mat file.

    Returns
    -------
    EXTRAS : pd.DataFrame
        A pd.DataFrame containing the EXTRAS.
    """

    if extras is None:

        return pd.DataFrame(columns=[0])

    else:
        EXTRAS = df.filter(regex=extras)

        return EXTRAS


# ---------------------------------------------------------------------
# Main function to open decomposed files coming from OTBiolab+.
# This function calls the functions defined above

def emg_from_otb(
    filepath,
    ext_factor=8,
    refsig=[True, "fullsampled"],
    version="1.5.9.3",
    extras=None,
    ignore_negative_ipts=False,
):
    """
    Import the .mat file exportable from OTBiolab+.

    This function is used to import the .mat file exportable by the OTBiolab+
    software as a dictionary of Python objects (mainly pandas dataframes).

    Parameters
    ----------
    filepath : str or Path
        The directory and the name of the file to load
        (including file extension .mat).
        This can be a simple string, the use of Path is not necessary.
    ext_factor : int, default 8
        The extension factor used for the decomposition in OTbiolab+.
    refsig : list, default [True, "fullsampled"]
        Whether to seacrh also for the REF_SIGNAL and whether to load the full
        or sub-sampled one. The list is composed as [bool, str]. str can be
        "fullsampled" or "subsampled". Please read notes section.
    version : str, default "1.5.9.3"
        Version of the OTBiolab+ software used (4 points).
        Tested versions are:
            "1.5.3.0",
            "1.5.4.0",
            "1.5.5.0",
            "1.5.6.0",
            "1.5.7.2",
            "1.5.7.3",
            "1.5.8.0",
            "1.5.9.3",
        If your specific version is not available in the tested versions,
        trying with the closer one usually works.
    extras : None or str, default None
        Extras is used to store additional custom values. These information
        will be stored in a pd.DataFrame with columns named as in the .mat
        file. If not None, pass a regex pattern unequivocally identifying the
        variable in the .mat file to load as extras.
    ignore_negative_ipts : bool, default False
        This parameter determines the silhouette score estimation. If True,
        only positive ipts values are used during peak and noise clustering.
        This is particularly important for compensating sources with large
        negative components.

    Returns
    -------
    emgfile : dict
        A dictionary containing all the useful variables.

    See also
    --------
    - refsig_from_otb : import REF_SIGNAL in the .mat file exportable from
        OTBiolab+.
    - emg_from_demuse : import the .mat file used in DEMUSE.
    - emg_from_customcsv : Import custom data from a .csv file.
    - askopenfile : Select and open files with a GUI.

    Raises
    ------
    ValueError
        When a wrong value is passed to version=.

    Notes
    ---------
    The returned file is called ``emgfile`` for convention.

    The input .mat file exported from the OTBiolab+ software must have a
    specific content:

    - The reference signal is optional but, if present, there should be the
        fullsampled or the subsampled version (in OTBioLab+ the "performed
        path" refers to the subsampled signal, the "acquired data" to the
        fullsampled signal), REF_SIGNAL is expected to be expressed as % of
        the MVC (but not compulsory).
    - Both the IPTS ('Source for decomposition...' in OTBioLab+) and the
        BINARY_MUS_FIRING ('Decomposition of...' in OTBioLab+) must be
        present.
    - The raw EMG signal must be present (it has no specific name in
        OTBioLab+) with all the channels. Don't exclude unwanted channels
        before exporting the .mat file.
    - NO OTHER ELEMENTS SHOULD BE PRESENT, unless an appropriate regex pattern
    is passed to 'extras='!

    Structure of the returned emgfile:

        emgfile = {
            "SOURCE": SOURCE,
            "FILENAME": FILENAME,
            "RAW_SIGNAL": RAW_SIGNAL,
            "REF_SIGNAL": REF_SIGNAL,
            "ACCURACY": SIL,
            "IPTS": IPTS,
            "MUPULSES": MUPULSES,
            "FSAMP": FSAMP,
            "IED": IED,
            "EMG_LENGTH": EMG_LENGTH,
            "NUMBER_OF_MUS": NUMBER_OF_MUS,
            "BINARY_MUS_FIRING": BINARY_MUS_FIRING,
            "EXTRAS": EXTRAS,
        }

    For OTBiolab+ files, the accuracy is estimated with the silhouette (SIL)
    score.

    Examples
    --------
    For an extended explanation of the imported emgfile use:

    >>> import openhdemg.library as emg
    >>> emgfile = emg.emg_from_otb(filepath="path/filename.mat")
    >>> info = emg.info()
    >>> info.data(emgfile)
    """

    mat_file = loadmat(filepath, simplify_cells=True)

    # Parse .mat obtained from OTBiolab+ to see the available variables
    """ print(
        "\n--------------------------------\nAvailable dict keys are:\n\n{}\n".format(
            mat_file.keys()
        )
    ) """

    # Check if a valid version has been specified
    valid_versions = [
        "1.5.3.0",
        "1.5.4.0",
        "1.5.5.0",
        "1.5.6.0",
        "1.5.7.2",
        "1.5.7.3",
        "1.5.8.0",
        "1.5.9.3",
    ]
    if version not in valid_versions:
        raise ValueError(
            f"\nSpecified version is not valid. Use one of:\n{valid_versions}\n"
        )

    if version in [
        "1.5.3.0",
        "1.5.4.0",
        "1.5.5.0",
        "1.5.6.0",
        "1.5.7.2",
        "1.5.7.3",
        "1.5.8.0",
        "1.5.9.3",
    ]:
        # Simplify (rename) columns description and extract all the parameters
        # in a pd.DataFrame
        df = pd.DataFrame(mat_file["Data"], columns=mat_file["Description"])

        # First, get the basic information and compulsory variables (i.e.,
        # RAW_SIGNAL, IPTS, MUPULSES, BINARY_MUS_FIRING) in a pd.DataFrame (df) or
        # list (for matlab cell arrays).

        # Use this to know the data source and name of the file
        SOURCE = "OTB"
        FILENAME = os.path.basename(filepath)
        FSAMP = float(mat_file["SamplingFrequency"])
        IED = get_otb_ied(df=df)

        # Get RAW_SIGNAL
        RAW_SIGNAL = get_otb_rawsignal(df=df, extras_regex=extras)

        # Get IPTS and BINARY_MUS_FIRING
        IPTS, BINARY_MUS_FIRING = get_otb_decomposition(df=df)
        # Align BINARY_MUS_FIRING to IPTS
        BINARY_MUS_FIRING = BINARY_MUS_FIRING.shift(- int(ext_factor))
        BINARY_MUS_FIRING.fillna(value=0, inplace=True)

        # Get MUPULSES
        MUPULSES = mupulses_from_binary(binarymusfiring=BINARY_MUS_FIRING)

        # Get EMG_LENGTH and NUMBER_OF_MUS
        EMG_LENGTH, NUMBER_OF_MUS = IPTS.shape

        # Get REF_SIGNAL
        REF_SIGNAL = get_otb_refsignal(df=df, refsig=refsig)

        # Estimate ACCURACY (SIL)
        if NUMBER_OF_MUS > 0:
            to_append = []
            for mu in range(NUMBER_OF_MUS):
                sil = compute_sil(
                    ipts=IPTS[mu],
                    mupulses=MUPULSES[mu],
                    ignore_negative_ipts=ignore_negative_ipts,
                )
                to_append.append(sil)
            ACCURACY = pd.DataFrame(to_append)

        else:
            ACCURACY = pd.DataFrame(columns=[0])

        # Get EXTRAS
        EXTRAS = get_otb_extras(df=df, extras=extras)

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

    return emgfile


# ---------------------------------------------------------------------
# Function to load the reference signal from OBIolab+.

def refsig_from_otb(
    filepath,
    refsig="fullsampled",
    version="1.5.9.3",
    extras=None,
):
    """
    Import the reference signal in the .mat file exportable by OTBiolab+.

    This function is used to import the .mat file exportable by the OTBiolab+
    software as a dictionary of Python objects (mainly pandas dataframes).
    Compared to the function emg_from_otb, this function only imports the
    REF_SIGNAL and, therefore, it can be used for special cases where only the
    REF_SIGNAL is necessary. This will allow for a faster execution of the
    script and to avoid exceptions for missing data.

    Parameters
    ----------
    filepath : str or Path
        The directory and the name of the file to load (including file
        extension .mat). This can be a simple string, the use of Path is not
        necessary.
    refsig : str {"fullsampled", "subsampled"}, default "fullsampled"
        Whether to load the full or sub-sampled one.
        Please read notes section.
    version : str, default "1.5.9.3"
        Version of the OTBiolab+ software used (4 points).
        Tested versions are:
            "1.5.3.0",
            "1.5.4.0",
            "1.5.5.0",
            "1.5.6.0",
            "1.5.7.2",
            "1.5.7.3",
            "1.5.8.0",
            "1.5.9.3",
        If your specific version is not available in the tested versions,
        trying with the closer one usually works, but please double check the
        results.
    extras : None or str, default None
        Extras is used to store additional custom values. These information
        will be stored in a pd.DataFrame with columns named as in the .mat
        file. If not None, pass a regex pattern unequivocally identifying the
        variable in the .mat file to load as extras.

    Returns
    -------
    emg_refsig : dict
        A dictionary containing all the useful variables.

    See also
    --------
    - emg_from_otb : import the .mat file exportable by OTBiolab+.
    - emg_from_demuse : import the .mat file used in DEMUSE.
    - emg_from_customcsv : Import custom data from a .csv file.
    - refsig_from_customcsv : Import the reference signal from a custom .csv.
    - askopenfile : Select and open files with a GUI.

    Notes
    ---------
    The returned file is called ``emg_refsig`` for convention.

    The input .mat file exported from the OTBiolab+ software must contain:

    - Reference signal: there must be the fullsampled or the subsampled
        version (in OTBioLab+ the "performed path" refers to the subsampled
        signal, the "acquired data" to the fullsampled signal), REF_SIGNAL is
        expected to be expressed as % of the MVC (but not compulsory).
    - NO OTHER ELEMENTS SHOULD BE PRESENT, unless an appropriate regex pattern
    is passed to 'extras='!

    Structure of the returned emg_refsig:

        emg_refsig = {
            "SOURCE": SOURCE,
            "FILENAME": FILENAME,
            "FSAMP": FSAMP,
            "REF_SIGNAL": REF_SIGNAL,
            "EXTRAS": EXTRAS,
        }

    Examples
    --------
    For an extended explanation of the imported emgfile use:

    >>> import openhdemg.library as emg
    >>> emgfile = emg.refsig_from_otb(filepath="path/filename.mat")
    >>> info = emg.info()
    >>> info.data(emgfile)
    """

    mat_file = loadmat(filepath, simplify_cells=True)

    # Parse .mat obtained from OTBiolab+ to see the available variables
    """ print(
        "\n--------------------------------\nAvailable dict keys are:\n\n{}\n".format(
            mat_file.keys()
        )
    ) """

    # Check if a valid version has been specified
    valid_versions = [
        "1.5.3.0",
        "1.5.4.0",
        "1.5.5.0",
        "1.5.6.0",
        "1.5.7.2",
        "1.5.7.3",
        "1.5.8.0",
        "1.5.9.3",
    ]
    if version not in valid_versions:
        raise ValueError(
            f"\nSpecified version is not valid. Use one of:\n{valid_versions}\n"
        )

    if version in [
        "1.5.3.0",
        "1.5.4.0",
        "1.5.5.0",
        "1.5.6.0",
        "1.5.7.2",
        "1.5.7.3",
        "1.5.8.0",
        "1.5.9.3",
    ]:
        # Simplify (rename) columns description and extract all the parameters
        # in a pd.DataFrame
        if isinstance(mat_file["Description"], str):
            col = [mat_file["Description"]]
        else:
            col = mat_file["Description"]

        df = pd.DataFrame(mat_file["Data"], columns=col)

        # Use this to know the data source and name of the file
        SOURCE = "OTB_REFSIG"
        FILENAME = os.path.basename(filepath)
        FSAMP = float(mat_file["SamplingFrequency"])

        # Convert the input passed to refsig in a list compatible with the
        # function get_otb_refsignal
        refsig_ = [True, refsig]
        REF_SIGNAL = get_otb_refsignal(df=df, refsig=refsig_)

        # Get EXTRAS
        EXTRAS = get_otb_extras(df=df, extras=extras)

    emg_refsig = {
        "SOURCE": SOURCE,
        "FILENAME": FILENAME,
        "FSAMP": FSAMP,
        "REF_SIGNAL": REF_SIGNAL,
        "EXTRAS": EXTRAS,
    }

    return emg_refsig


# --------------------------------------------------------------------- #
# Function to open decomposed files coming from Delsys.
def emg_from_delsys(
        rawemg_filepath,
        mus_directory,
        emg_sensor_name="Galileo sensor",
        refsig_sensor_name="Trigno Load Cell",
        filename_from="mus_directory",
):
    """
    Import the .mat and .txt files exportable from Delsys softwares.

    This function is used to load .mat files from the Delsys Neuromap software
    (containing the RAW EMG signal and the reference signal) and .txt files
    from the Delsys Neuromap Explorer software (containing the decomposition
    outcome, accuracy measure and MUAPs).

    We currenlty support only recordings performed with the "Galileo sensor"
    (4-pin). Support for the 5-pin sensor will be provided in the next
    releases.

    Parameters
    ----------
    rawemg_filepath : str or Path
        The directory and the name of the file containing the raw EMG data to
        load (including file extension .mat).
        This can be a simple string, the use of Path is not necessary.
    mus_directory : str or Path
        The directory (path to the folder) containing .txt files with firing
        times, MUAPs, and accuracy data.
        This can be a simple string, the use of Path is not necessary.
        The .txt files should all be contained in the same folder and should
        follow the standard Deslys naming convention (e.g., the file
        containing accuracy data will have the string "Stats" in its name).
    emg_sensor_name : str, default "Galileo sensor"
        The name of the EMG sensor used to collect the data. We currently
        support only the "Galileo sensor" (4-pin).
    refsig_sensor_name : str, default "Trigno Load Cell"
        The name of the sensor used to record the reference signal. This is by
        default "Trigno Load Cell". However, since this can have any name (and
        can also be renamed by the user), here you should pass the effective
        name (or regex pattern) by which you identify the sensor.
        Ignore if no reference signal was recorded.
    filename_from : str {"rawemg_file", "mus_directory"}, default "mus_directory"
        The source by which the imported file will be named. This can either be
        the same name of the file containing the raw EMG signal or of the
        folder containing the decomposition outcome.

    Returns
    --------
    emgfile : dict
        A dictionary containing all the useful variables.

    See also
    --------
    - refsig_from_delsys : Import the reference signal exportable from Delsys.
    - askopenfile : Select and open files with a GUI.

    Notes
    ---------
    The returned file is called ``emgfile`` for convention.

    Structure of the returned emgfile:

        emgfile = {
            "SOURCE": SOURCE,
            "FILENAME": FILENAME,
            "RAW_SIGNAL": RAW_SIGNAL,
            "REF_SIGNAL": REF_SIGNAL,
            "ACCURACY": PROPRIETARY ACCURACY MEASURE,
            "IPTS": IPTS,
            "MUPULSES": MUPULSES,
            "FSAMP": FSAMP,
            "IED": IED,
            "EMG_LENGTH": EMG_LENGTH,
            "NUMBER_OF_MUS": NUMBER_OF_MUS,
            "BINARY_MUS_FIRING": BINARY_MUS_FIRING,
            "EXTRAS": EXTRAS,
        }

    For Delsys files, the accuracy is the one provided after the decomposition
    and it is not computed internally, being this a proprietary measure.

    We collect the raw EMG and the reference signal from the .mat file because
    the .csv doesn't contain the information about sampling frequency.
    Similarly, we collect the firing times, MUAPs and accuracy from the .txt
    files because in the .mat file, the accuracy is contained in a table,
    which is not compatible with Python.

    Examples
    --------
    For an extended explanation of the imported emgfile use:

    >>> import openhdemg.library as emg
    >>> emgfile = emg.emg_from_delsys(
    ...     rawemg_filepath="path/filename.mat",
    ...     mus_directory="/directory",
    ... )
    >>> info = emg.info()
    >>> info.data(emgfile)
    """

    # From the rawemg_filepath:
    # Parse the .mat obtained from Delsys to see the available variables.
    # We start from the file containing the raw EMG as this also contains the
    # sampling frequency.
    rawemg_file = loadmat(rawemg_filepath, simplify_cells=True)
    """ print(
        "\n--------------------------------\nAvailable dict keys are:\n\n{}\n".format(
            rawemg_file.keys()
        )
    ) """

    # Use this to know the data source and name of the file
    SOURCE = "DELSYS"
    if filename_from == "rawemg_file":
        FILENAME = os.path.basename(rawemg_filepath)
    elif filename_from == "mus_directory":
        FILENAME = os.path.basename(mus_directory)
    else:
        raise ValueError(
            "\nfilename_from not valid, it must be one of 'rawemg_file', 'mus_directory'\n"
        )
    FSAMP = float(rawemg_file["Fs"][0])
    IED = float(5)

    # Extract the data contained in the Data variable of the rawemg_file.
    # This contains the raw EMG and the reference signal.
    df = pd.DataFrame(rawemg_file["Data"].T, columns=rawemg_file["Channels"])

    # Get RAW_SIGNAL
    # Create a list of indexes where emg_sensor_name is found
    RAW_SIGNAL = df.filter(regex=emg_sensor_name)
    RAW_SIGNAL.columns = np.arange(len(RAW_SIGNAL.columns))
    # Verify to have the IPTS
    if RAW_SIGNAL.empty:
        raise ValueError(
            "\nRaw EMG signal not found in the .mat file\n"
        )

    # Get REF_SIGNAL
    REF_SIGNAL = df.filter(regex=refsig_sensor_name)
    REF_SIGNAL.columns = np.arange(len(REF_SIGNAL.columns))
    if REF_SIGNAL.empty:
        warnings.warn(
            "\nReference signal not found, it might be necessary for some analyses\n"
        )
        REF_SIGNAL = pd.DataFrame(columns=[0])

    # From the mus_directory:
    # Obtain the name (and path) of the files containing MUPULSES, ACCURACY
    # and EXTRAS. Automate this because it will be too boring manually.
    # Get all file names in the directory
    files = os.listdir(mus_directory)
    # Define the keywords to match
    keywords = ["Firings", "Stats", "MUAPs"]
    # Initialize a dictionary to store the keyword-path mapping
    keyword_paths = {}
    # Iterate over the files and match keywords
    for keyword in keywords:
        for file in files:
            if fnmatch.fnmatch(file, f"*{keyword}*"):
                keyword_paths[keyword] = os.path.join(mus_directory, file)
    # Check if we have found paths for all three keywords
    if not all(keyword in keyword_paths for keyword in keywords):
        missing_keywords = [
            keyword for keyword in keywords if keyword not in keyword_paths
        ]
        raise ValueError(
            f"Missing paths for: {', '.join(missing_keywords)}"
        )
    # Now, 'keyword_paths' contains the mapping of keywords to file paths:
    # For example, keyword_paths["Firings"] contains the path to the "Firings",
    # file and so on for the other keywords.

    # Get MUPULSES
    MUPULSES = np.genfromtxt(
        keyword_paths["Firings"],
        delimiter='\t',
        skip_header=True,
    ).T
    # Store MUPULSES as a list of np.arrays
    to_append = []
    for pulse in MUPULSES:
        # Drop nan and convert from seconds to samples
        pulse = pulse[~np.isnan(pulse)] * FSAMP
        # Store int samples
        to_append.append(np.round(pulse).astype(int))
    MUPULSES = to_append

    # Get EMG_LENGTH and NUMBER_OF_MUS
    EMG_LENGTH = len(RAW_SIGNAL)
    NUMBER_OF_MUS = len(MUPULSES)

    # Get BINARY_MUS_FIRING
    BINARY_MUS_FIRING = create_binary_firings(
        emg_length=EMG_LENGTH,
        number_of_mus=NUMBER_OF_MUS,
        mupulses=MUPULSES,
    )

    # Get IPTS
    # Empty pd.DataFrame as we don't have this from Delsys decomposition.
    IPTS = pd.DataFrame(columns=np.arange(NUMBER_OF_MUS))

    # Get ACCURACY
    ACCURACY = pd.read_csv(keyword_paths["Stats"], sep='\t')
    ACCURACY = ACCURACY[["Accuracy"]]
    ACCURACY.columns = [0]

    # Get EXTRAS (MUAPs for Delsys)
    # MUAPs from Delsys for all the MUs are all stored in the same table.
    # We want them divided in different columns based on MU and channel.
    EXTRAS = pd.read_csv(keyword_paths["MUAPs"], sep='\t')
    df = {}
    for mu in range(1, NUMBER_OF_MUS + 1):  # Named in base 1 from Delsys
        this_mu_all_ch = EXTRAS.loc[EXTRAS["MU_Num"] == mu]
        for ch in range(1, 5):  # Galileo has 4 recording pins, in base 1
            col_name = f"MU_{mu-1}_CH_{ch-1}"
            arr = this_mu_all_ch.filter(regex=str(ch)).to_numpy()
            df[col_name] = arr[:, 0]
    EXTRAS = pd.DataFrame(df)

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

    return emgfile


# --------------------------------------------------------------------- #
# Function to open the reference signal from Delsys.
def refsig_from_delsys(filepath, refsig_sensor_name="Trigno Load Cell"):
    """
    Import the reference signal in the .mat file exportable by Delsys Neuromap.

    This function is used to import the .mat file exportable by the Delsys
    Neuromap software as a dictionary of Python objects (mainly pandas
    dataframes). Compared to the function emg_from_delsys, this function only
    imports the REF_SIGNAL and, therefore, it can be used for special cases
    where only the REF_SIGNAL is necessary. This will allow for a faster
    execution of the script and to avoid exceptions for missing data.

    Parameters
    ----------
    filepath : str or Path
        The directory and the name of the file to load (including file
        extension .mat). This can be a simple string, the use of Path is not
        necessary.
    refsig_sensor_name : str, default "Trigno Load Cell"
        The name of the sensor used to record the reference signal. This is by
        default "Trigno Load Cell". However, since this can have any name (and
        can also be renamed by the user), here you should pass the effective
        name (or regex pattern) by which you identify the sensor.

    Returns
    -------
    emg_refsig : dict
        A dictionary containing all the useful variables.

    See also
    --------
    - emg_from_delsys : Import the Delsys decomposition outcome.
    - askopenfile : Select and open files with a GUI.

    Notes
    ---------
    The returned file is called ``emg_refsig`` for convention.

    Structure of the returned emg_refsig:

        emg_refsig = {
            "SOURCE": SOURCE,
            "FILENAME": FILENAME,
            "FSAMP": FSAMP,
            "REF_SIGNAL": REF_SIGNAL,
            "EXTRAS": EXTRAS,
        }

    Examples
    --------
    For an extended explanation of the imported emgfile use:

    >>> import openhdemg.library as emg
    >>> emgfile = emg.refsig_from_delsys(filepath="path/filename.mat")
    >>> info = emg.info()
    >>> info.data(emgfile)
    """
    # TODO add extras option

    # Parse the .mat obtained from Delsys to see the available variables.
    # The .mat file should containing the reference signal and the sampling
    # frequency.
    refsig_file = loadmat(filepath, simplify_cells=True)
    """ print(
        "\n--------------------------------\nAvailable dict keys are:\n\n{}\n".format(
            rawemg_file.keys()
        )
    ) """

    # Use this to know the data source and name of the file
    SOURCE = "DELSYS_REFSIG"
    FILENAME = os.path.basename(filepath)
    FSAMP = float(refsig_file["Fs"][0])

    # Extract the data contained in the Data variable of the .mat file.
    # This contains the reference signal.
    df = pd.DataFrame(refsig_file["Data"].T, columns=refsig_file["Channels"])
    # Get REF_SIGNAL
    REF_SIGNAL = df.filter(regex=refsig_sensor_name)
    REF_SIGNAL.columns = np.arange(len(REF_SIGNAL.columns))
    if REF_SIGNAL.empty:
        raise ValueError(
            "\nReference signal not found\n"
        )

    emg_refsig = {
        "SOURCE": SOURCE,
        "FILENAME": FILENAME,
        "FSAMP": FSAMP,
        "REF_SIGNAL": REF_SIGNAL,
        "EXTRAS": pd.DataFrame(columns=[0]),
    }

    return emg_refsig


# ---------------------------------------------------------------------
# Function to load custom CSV documents.
def emg_from_customcsv(
    filepath,
    ref_signal="REF_SIGNAL",
    raw_signal="RAW_SIGNAL",
    ipts="IPTS",
    mupulses="MUPULSES",
    binary_mus_firing="BINARY_MUS_FIRING",
    accuracy="ACCURACY",
    extras="EXTRAS",
    fsamp=2048,
    ied=8,
):
    """
    Import the emgfile from a custom .csv file.

    The variables of interest should be contained in columns. The name of the
    columns containing each variable can be specified by the user if different
    from the default values.

    This function detects the content of the .csv by parsing the .csv columns.
    For parsing, column labels should be provided. A label is a term common
    to all the columns containing the same information.
    For example, if the raw signal is contained in the columns 'RAW_SIGNAL_1',
    'RAW_SIGNAL_2', ... , 'RAW_SIGNAL_n', the label of the columns should be
    'RAW_SIGNAL'.
    If the parameters in input are not present in the .csv file, the user
    should leave the original inputs.

    The .csv file must contain at least the raw_signal and one of 'mupulses' or
    'binary_mus_firing'. If 'mupulses' is absent, it will be calculated from
    'binary_mus_firing' and viceversa.

    Parameters
    ----------
    filepath : str or Path
        The directory and the name of the file to load
        (including file extension .mat).
        This can be a simple string, the use of Path is not necessary.
    ref_signal : str, default 'REF_SIGNAL'
        Label of the column containing the reference signal.
    raw_signal : str, default 'RAW_SIGNAL'
        Label of the column(s) containing the raw emg signal.
    ipts : str, default 'IPTS'
        Label of the column(s) containing the pulse train (decomposed source).
    mupulses : str, default 'MUPULSES'
        Label of the column(s) containing the times of firing.
    binary_mus_firing : str, default 'BINARY_MUS_FIRING'
        Label of the column(s) containing the binary representation
        of the MUs firings.
    accuracy : str, default 'ACCURACY'
        Label of the column(s) containing the accuracy score of the MUs
        firings.
    extras : str, default 'EXTRAS'
        Label of the column(s) containing custom values. This information will
        be stored in a pd.DataFrame with columns named as in the .csv file.
    fsamp : int or float, default 2048
        Tha sampling frequency.
    ied : int or float, default 8
        The inter-electrode distance in mm.

    Returns
    -------
    emgfile : dict
        A dictionary containing all the useful variables.

    See also
    --------
    - emg_from_demuse : import the .mat file used in DEMUSE.
    - emg_from_otb : import the .mat file exportable by OTBiolab+.
    - refsig_from_otb : import reference signal in the .mat file exportable by
        OTBiolab+.
    - refsig_from_customcsv : Import the reference signal from a custom .csv.
    - askopenfile : Select and open files with a GUI.

    Notes
    -----
    The returned file is called ``emgfile`` for convention.

    Structure of the emgfile:

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

    Examples
    --------
    An example of the .csv file to load:
    >>>
    REF_SIGNAL  RAW_SIGNAL (1)  RAW_SIGNAL (2)  RAW_SIGNAL (3)  RAW_SIGNAL (4)  ...  MUPULSES (2)  BINARY_MUS_FIRING (1)  BINARY_MUS_FIRING (2)  ACCURACY (1)  ACCURACY (2)
             1        0.100000        0.100000        0.100000        0.100000  ...           1.0                      0                      0          0.89          0.95
             2        2.000000        2.000000        2.000000        2.000000  ...           2.0                      0                      0                                  
             3        0.500000        0.500000        0.500000        0.500000  ...           9.0                      0                      0                                  
             4        0.150000        0.150000        0.150000        0.150000  ...          15.0                      0                      1                                  
             5        0.350000        0.350000        0.350000        0.350000  ...          18.0                      1                      1                                  
             6        0.215000        0.215000        0.215000        0.215000  ...          22.0                      1                      0                            

    For an extended explanation of the imported emgfile use:

    >>> import openhdemg.library as emg
    >>> emgfile = emg_from_customcsv(filepath = "mypath/file.csv")
    >>> info = emg.info()
    >>> info.data(emgfile)
    """

    # Load the csv
    csv = pd.read_csv(filepath)

    # First, get the basic information and compulsory variables (i.e.,
    # RAW_SIGNAL, MUPULSES, BINARY_MUS_FIRING).

    # Use this to know the data source and name of the file
    SOURCE = "CUSTOMCSV"
    FILENAME = os.path.basename(filepath)

    # Get RAW_SIGNAL
    RAW_SIGNAL = csv.filter(regex=raw_signal, axis=1).dropna()
    if not RAW_SIGNAL.empty:
        RAW_SIGNAL.columns = [i for i in range(len(RAW_SIGNAL.columns))]
    else:
        raise ValueError(
            "\nraw_signal not found\n"
        )

    # Get MUPULSES/BINARY_MUS_FIRING
    df_mupulses = csv.filter(regex=mupulses, axis=1)
    BINARY_MUS_FIRING = csv.filter(regex=binary_mus_firing, axis=1).dropna()

    if df_mupulses.empty and BINARY_MUS_FIRING.empty:
        raise ValueError(
            "\nmupulses and binary_mus_firing not found. At least one of the two must be present\n")
    elif not df_mupulses.empty and not BINARY_MUS_FIRING.empty:
        MUPULSES = []
        for col in df_mupulses.columns:
            toappend = df_mupulses[col].dropna().to_numpy(dtype=int)
            MUPULSES.append(toappend)

        BINARY_MUS_FIRING.columns = [
            i for i in range(len(BINARY_MUS_FIRING.columns))
        ]

    elif df_mupulses.empty and not BINARY_MUS_FIRING.empty:
        BINARY_MUS_FIRING.columns = [
            i for i in range(len(BINARY_MUS_FIRING.columns))
        ]

        MUPULSES = mupulses_from_binary(binarymusfiring=BINARY_MUS_FIRING)

    else:  # if not df_mupulses.empty and BINARY_MUS_FIRING.empty:
        MUPULSES = []
        for col in df_mupulses.columns:
            toappend = df_mupulses[col].dropna().to_numpy(dtype=int)
            MUPULSES.append(toappend)

        l, _ = RAW_SIGNAL.shape
        BINARY_MUS_FIRING = create_binary_firings(
            emg_length=l,
            number_of_mus=len(MUPULSES),
            mupulses=MUPULSES,
        )

    # Get EMG_LENGTH and NUMBER_OF_MUS
    EMG_LENGTH, NUMBER_OF_MUS = BINARY_MUS_FIRING.shape

    # Second, get/generate the other variables
    # Get REF_SIGNAL
    REF_SIGNAL = csv.filter(regex=ref_signal, axis=1).dropna()
    if not REF_SIGNAL.empty:
        REF_SIGNAL.columns = [i for i in range(len(REF_SIGNAL.columns))]
        if len(REF_SIGNAL.columns) > 1:
            warnings.warn(
                "\nMore than 1 reference signal detected. You should place other signals in 'EXTRAS'\n"
            )
    else:
        REF_SIGNAL = pd.DataFrame(columns=[0])
        warnings.warn(
            "\nref_signal not found, it might be necessary for some analyses\n"
        )  # returns empty pd.DataFrame with 1 column

    # Get IPTS
    IPTS = csv.filter(regex=ipts, axis=1).dropna()
    if not IPTS.empty:
        IPTS.columns = [i for i in range(len(IPTS.columns))]
    else:
        IPTS = pd.DataFrame(columns=[*range(NUMBER_OF_MUS)])
        warnings.warn(
            "\nipts not found, it might be necessary for some analyses\n"
        )  # returns empty pd.DataFrame with n columns

    # Get ACCURACY
    ACCURACY = csv.filter(regex=accuracy, axis=1).dropna()
    if not ACCURACY.empty:
        # Merge all the accuracies of each MU in a single column.
        ACCURACY = ACCURACY.melt(value_name=0).drop(labels="variable", axis=1)
    else:
        ACCURACY = pd.DataFrame(columns=[0])
        warnings.warn(
            "\naccuracy not found. It might be necessary for some analyses\n"
        )  # returns empty pd.DataFrame with 1 column

    # Get EXTRAS
    EXTRAS = csv.filter(regex=extras, axis=1)
    if EXTRAS.empty:
        EXTRAS = pd.DataFrame(columns=[0])
        # returns empty pd.DataFrame with 1 column

    emgfile = {
        "SOURCE": SOURCE,
        "FILENAME": FILENAME,
        "RAW_SIGNAL": RAW_SIGNAL,
        "REF_SIGNAL": REF_SIGNAL,
        "ACCURACY": ACCURACY,
        "IPTS": IPTS,
        "MUPULSES": MUPULSES,
        "FSAMP": float(fsamp),
        "IED": float(ied),
        "EMG_LENGTH": EMG_LENGTH,
        "NUMBER_OF_MUS": NUMBER_OF_MUS,
        "BINARY_MUS_FIRING": BINARY_MUS_FIRING,
        "EXTRAS": EXTRAS,
    }

    return emgfile


# ---------------------------------------------------------------------
# Function to load the reference signal from custom CSV documents.

def refsig_from_customcsv(
    filepath,
    ref_signal="REF_SIGNAL",
    extras="EXTRAS",
    fsamp=2048,
):
    """
    Import the reference signal from a custom .csv file.

    Compared to the function emg_from_customcsv, this function only imports the
    REF_SIGNAL and, therefore, it can be used for special cases where only the
    REF_SIGNAL is necessary. This will allow for a faster execution of the
    script and to avoid exceptions for missing data.

    This function detects the content of the .csv by parsing the .csv columns.
    For parsing, column labels should be provided. A label is a term common
    to all the columns containing the same information.
    For example, if the ref signal is contained in the column 'REF_SIGNAL', the
    label of the columns should be 'REF_SIGNAL' or a part of it (e.g., 'REF').
    If the parameters in input are not present in the .csv file (e.g.,
    'EXTRAS'), the user should leave the original inputs.

    Parameters
    ----------
    filepath : str or Path
        The directory and the name of the file to load
        (including file extension .mat).
        This can be a simple string, the use of Path is not necessary.
    ref_signal : str, default 'REF_SIGNAL'
        Label of the column containing the reference signal.
    extras : str, default 'EXTRAS'
        Label of the column(s) containing custom values. These information
        will be stored in a pd.DataFrame with columns named as in the .csv
        file.
    fsamp : int or float, default 2048
        Tha sampling frequency.

    Returns
    -------
    emg_refsig : dict
        A dictionary containing all the useful variables.

    See also
    --------
    - emg_from_customcsv : Import the emgfile from a custom .csv file.
    - askopenfile : Select and open files with a GUI.

    Notes
    ---------
    The returned file is called ``emg_refsig`` for convention.

    Structure of the returned emg_refsig:

        emg_refsig = {
            "SOURCE": SOURCE,
            "FILENAME": FILENAME,
            "FSAMP": FSAMP,
            "REF_SIGNAL": REF_SIGNAL,
            "EXTRAS": EXTRAS,
        }

    Examples
    --------
    An example of the .csv file to load:
    >>>
    REF_SIGNAL  EXTRAS (1)  EXTRAS (2)
             1         0.1           0
             2         0.2           0
             3         0.3           0
             4         0.4           0
             5         0.5           1
             6         0.6           1

    For an extended explanation of the imported emgfile use:

    >>> import openhdemg.library as emg
    >>> emgfile = refsig_from_customcsv(filepath = "mypath/file.csv")
    >>> info = emg.info()
    >>> info.data(emgfile)
    """

    # Load the csv
    csv = pd.read_csv(filepath)

    # Use this to know the data source and name of the file
    SOURCE = "CUSTOMCSV_REFSIG"
    FILENAME = os.path.basename(filepath)

    # Get REF_SIGNAL
    REF_SIGNAL = csv.filter(regex=ref_signal, axis=1).dropna()
    if not REF_SIGNAL.empty:
        REF_SIGNAL.columns = [i for i in range(len(REF_SIGNAL.columns))]
        if len(REF_SIGNAL.columns) > 1:
            warnings.warn(
                "\nMore than 1 reference signal detected. You should place other signals in 'EXTRAS'\n"
            )
    else:
        REF_SIGNAL = pd.DataFrame(columns=[0])
        warnings.warn(
            "\nref_signal not found, it might be necessary for some analyses\n"
        )  # returns empty pd.DataFrame with 1 column

    # Get EXTRAS
    EXTRAS = csv.filter(regex=extras, axis=1)
    if EXTRAS.empty:
        EXTRAS = pd.DataFrame(columns=[0])
        # returns empty pd.DataFrame with 1 column

    emgfile = {
        "SOURCE": SOURCE,
        "FILENAME": FILENAME,
        "FSAMP": float(fsamp),
        "REF_SIGNAL": REF_SIGNAL,
        "EXTRAS": EXTRAS,
    }

    return emgfile


# ---------------------------------------------------------------------
# Functions to convert and save the emgfile to JSON.

def save_json_emgfile(emgfile, filepath, compresslevel=4):
    """
    Save the emgfile or emg_refsig as a JSON file.

    !!! note "Since version 0.2.0"
        The recommended workflow for saving and loading openhdemg data now
        relies on the following high-level functions and classes for binary
        files:

        - `save_openhdemg_module`
        - `asksavemodule`
        - `load_openhdemg_module`
        - `askloadmodule`
        - `openhdemg_Collection`

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    filepath : str or Path
        The directory and the name of the file to save (including file
        extension .json).
        This can be a simple string; The use of Path is not necessary.
    compresslevel : int, default 4
        An int from 0 to 9, where 0 is no compression and nine maximum
        compression. Compressed files will take less space, but will require
        more computation. The relationship between compression level and time
        required for the compression is not linear. For optimised performance,
        we suggest values between 2 and 6, with 4 providing the best balance.
    """

    if emgfile["SOURCE"] == "OPENHDEMG":
        warnings.warn(
            "openhdemg modules and collections should be saved using "
            "high-level functions and classes for binary files "
            "(save_openhdemg_module, asksavemodule, load_openhdemg_module, "
            "askloadmodule, openhdemg_Collection). Saving them "
            "using save_json_emgfile might fail or omit data."
        )

    full_emgfile_sources = [
        "DEMUSE", "OTB", "CUSTOMCSV", "DELSYS", "OPENHDEMG",
    ]
    if emgfile["SOURCE"] in full_emgfile_sources:
        """
        We need to convert all the components of emgfile to a dictionary and
        then to json object.
        pd.DataFrame cannot be converted with json.dumps.
        Once all the elements are converted to json objects, we create a dict
        of json objects and dump/save it into a single json file.
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
        # Every array has to be converted in a list; then, the list of lists
        # can be converted to json.
        mupulses = []
        for ind, array in enumerate(emgfile["MUPULSES"]):
            mupulses.insert(ind, array.tolist())
        mupulses = json.dumps(mupulses)

        # Convert a dict of json objects to json. The result of the conversion
        # will be saved as the final json file.
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
            compresslevel=compresslevel
        ) as f:
            json.dump(emgfile, f)

        # Adapted from:
        # https://stackoverflow.com/questions/39450065/python-3-read-write-compressed-json-objects-from-to-gzip-file
        """ with gzip.open(filepath, "w", compresslevel=compresslevel) as f:
            # Encode json
            json_bytes = json_to_save.encode("utf-8")
            # Write to a file
            f.write(json_bytes) """

    elif emgfile["SOURCE"] in ["OTB_REFSIG", "CUSTOMCSV_REFSIG", "DELSYS_REFSIG"]:
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
            compresslevel=compresslevel
        ) as f:
            json.dump(refsig, f)

    else:
        raise ValueError(
            "\nFile source not recognised. Use instead high-level functions "
            "and classes for binary files (save_openhdemg_module, "
            "asksavemodule, load_openhdemg_module, askloadmodule, "
            "openhdemg_Collection).\n"
        )


def emg_from_json(filepath):
    """
    Load the emgfile or emg_refsig stored in json format.

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

    See also
    --------
    - save_json_emgfile : Save the emgfile or emg_refsig as a JSON file.
    - askopenfile : Select and open files with a GUI.

    Notes
    -----
    The returned file is called ``emgfile`` for convention
    (or ``emg_refsig`` if SOURCE in ["OTB_REFSIG", "CUSTOMCSV_REFSIG", "DELSYS_REFSIG"]).

    Examples
    --------
    For an extended explanation of the imported emgfile use:

    >>> import openhdemg.library as emg
    >>> emgfile = emg.emg_from_json(filepath="path/filename.json")
    >>> info = emg.info()
    >>> info.data(emgfile)
    """

    # Read and decompress json file
    with gzip.open(filepath, "rt", encoding="utf-8") as f:
        jsonemgfile = json.load(f)

    """
    print(type(jsonemgfile))
    <class 'dict'>
    """

    # Access the dictionaries and extract the data.
    source = json.loads(jsonemgfile["SOURCE"])
    filename = json.loads(jsonemgfile["FILENAME"])

    if source in ["DEMUSE", "OTB", "CUSTOMCSV", "DELSYS", "OPENHDEMG"]:
        # RAW_SIGNAL
        # df are stored in json as a dictionary, it can be directly extracted
        # and converted into a pd.DataFrame.
        # index and columns are imported as str, we need to convert it to int.
        raw_signal = pd.read_json(
            StringIO(jsonemgfile["RAW_SIGNAL"]),
            orient='split',
        )
        # Check dtypes for safety, little computational cost
        raw_signal.columns = raw_signal.columns.astype(int)
        raw_signal.index = raw_signal.index.astype(int)
        raw_signal.sort_index(inplace=True)
        # REF_SIGNAL
        ref_signal = pd.read_json(
            StringIO(jsonemgfile["REF_SIGNAL"]),
            orient='split',
        )
        ref_signal.columns = ref_signal.columns.astype(int)
        ref_signal.index = ref_signal.index.astype(int)
        ref_signal.sort_index(inplace=True)
        # ACCURACY
        accuracy = pd.read_json(
            StringIO(jsonemgfile["ACCURACY"]),
            orient='split',
        )
        try:
            accuracy.columns = accuracy.columns.astype(int)
        except Exception:
            accuracy.columns = [*range(len(accuracy.columns))]
            warnings.warn(
                "Error while loading accuracy, check or recalculate accuracy"
            )
            # TODO error occurring when accuracy was recalculated on empty MUs.
            # Check if the error is present also for other params.
        accuracy.index = accuracy.index.astype(int)
        accuracy.sort_index(inplace=True)
        # IPTS
        ipts = pd.read_json(StringIO(jsonemgfile["IPTS"]), orient='split')
        ipts.columns = ipts.columns.astype(int)
        ipts.index = ipts.index.astype(int)
        ipts.sort_index(inplace=True)
        # MUPULSES
        # It is s list of lists but has to be converted in a list of ndarrays.
        mupulses = json.loads(jsonemgfile["MUPULSES"])
        for num, element in enumerate(mupulses):
            mupulses[num] = np.array(element)
        # FSAMP
        # Make sure to convert it to float
        fsamp = float(json.loads(jsonemgfile["FSAMP"]))
        # IED
        ied = float(json.loads(jsonemgfile["IED"]))
        # EMG_LENGTH
        # Make sure to convert it to int
        emg_length = int(json.loads(jsonemgfile["EMG_LENGTH"]))
        # NUMBER_OF_MUS
        number_of_mus = int(json.loads(jsonemgfile["NUMBER_OF_MUS"]))
        # BINARY_MUS_FIRING
        binary_mus_firing = pd.read_json(
            StringIO(jsonemgfile["BINARY_MUS_FIRING"]),
            orient='split',
        )
        binary_mus_firing.columns = binary_mus_firing.columns.astype(int)
        binary_mus_firing.index = binary_mus_firing.index.astype(int)
        binary_mus_firing.sort_index(inplace=True)
        # EXTRAS
        # Don't alter index and columns as these could contain anything.
        extras = pd.read_json(StringIO(jsonemgfile["EXTRAS"]), orient='split')

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

    elif source in ["OTB_REFSIG", "CUSTOMCSV_REFSIG", "DELSYS_REFSIG"]:
        # FSAMP
        fsamp = float(json.loads(jsonemgfile["FSAMP"]))
        # REF_SIGNAL
        ref_signal = pd.read_json(
            StringIO(jsonemgfile["REF_SIGNAL"]),
            orient='split',
        )
        ref_signal.columns = ref_signal.columns.astype(int)
        ref_signal.index = ref_signal.index.astype(int)
        ref_signal.sort_index(inplace=True)
        # EXTRAS
        extras = pd.read_json(StringIO(jsonemgfile["EXTRAS"]), orient='split')

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


# ---------------------------------------------------------------------
# Functions to open files from a GUI in a single line of code.

def askopenfile(filesource="OPENHDEMG", **kwargs):
    """
    Select and open files with a GUI.

    !!! note "Since version 0.2.0"
        The recommended workflow for saving and loading openhdemg data now
        relies on the following high-level functions and classes for binary
        files:

        - `save_openhdemg_module`
        - `asksavemodule`
        - `load_openhdemg_module`
        - `askloadmodule`
        - `openhdemg_Collection`

    Parameters
    ----------
    filesource : str {"OPENHDEMG", "DEMUSE", "OTB", "DELSYS", "CUSTOMCSV", "OTB_REFSIG", "DELSYS_REFSIG", CUSTOMCSV_REFSIG}, default "OPENHDEMG"
        The source of the file. See notes for how files should be exported
        from other softwares or platforms.

        ``OPENHDEMG``
            File saved from openhdemg (.json).

        ``DEMUSE``
            File saved from DEMUSE (.mat).

        ``OTB``
            File exported from OTB with decomposition and EMG signal.
            (.mat).

        ``DELSYS``
            Files exported from Delsys Neuromap and Neuromap explorer with
            decomposition and EMG signal (.mat + .txt).

        ``CUSTOMCSV``
            Custom file format (.csv) with decomposition and EMG signal.

        ``OTB_REFSIG``
            File exported from OTB with only the reference signal (.mat).

        ``DELSYS_REFSIG``
            File exported from DELSYS Neuromap with the reference signal
            (.mat).

        ``CUSTOMCSV_REFSIG``
            Custom file format (.csv) containing only the reference signal.
    ignore_negative_ipts : bool, default False
        This parameter determines the silhouette score estimation. If True,
        only positive ipts values are used during peak and noise clustering.
        This is particularly important for compensating sources with large
        negative components. Currently, this parameter is used when loading
        files decomposed in DEMUSE or OTB.
    otb_ext_factor : int, default 8
        The extension factor used for the decomposition in the OTbiolab+
        software.
        Ignore if loading other files.
    otb_refsig_type : list, default [True, "fullsampled"]
        Whether to seacrh also for the REF_SIGNAL and whether to load the full
        or sub-sampled one. The list is composed as [bool, str]. str can be
        "fullsampled" or "subsampled".
        Ignore if loading other files.
    otb_version : str, default "1.5.9.3"
        Version of the OTBiolab+ software used (4 points).
        Tested versions are:
            "1.5.3.0",
            "1.5.4.0",
            "1.5.5.0",
            "1.5.6.0",
            "1.5.7.2",
            "1.5.7.3",
            "1.5.8.0",
            "1.5.9.3",
        If your specific version is not available in the tested versions,
        trying with the closer one usually works, but please double check the
        results. Ignore if loading other files.
    otb_extras : None or str, default None
        Extras is used to store additional custom values. These information
        will be stored in a pd.DataFrame with columns named as in the .mat
        file. If not None, pass a regex pattern unequivocally identifying the
        variable in the .mat file to load as extras.
    delsys_emg_sensor_name : str, default "Galileo sensor"
        The name of the EMG sensor used to collect the data. We currently
        support only the "Galileo sensor".
        Ignore if loading other files or only the reference signal.
    delsys_refsig_sensor_name : str, default "Trigno Load Cell"
        The name of the sensor used to record the reference signal. This is by
        default "Trigno Load Cell". However, since this can have any name (and
        can also be renamed by the user), here you should pass the effective
        name (or regex pattern) by which you identify the sensor.
        Ignore if loading other files or if no reference signal was recorded.
    delsys_filename_from : str {"rawemg_file", "mus_directory"}, default "mus_directory"
        The source by which the imported file will be named. This can either be
        the same name of the file containing the raw EMG signal or of the
        folder containing the decomposition outcome.
        Ignore if loading other files or only the reference signal.
    custom_ref_signal : str, default 'REF_SIGNAL'
        Label of the column(s) containing the reference signal of the custom
        file.
        This and the following arguments are needed only for custom files.
        Ignore if loading other files.
    custom_raw_signal : str, default 'RAW_SIGNAL'
        Label of the column(s) containing the raw emg signal of the custom
        file. Ignore if loading other files.
    custom_ipts : str, default 'IPTS'
        Label of the column(s) containing the pulse train of the custom file.
        Ignore if loading other files.
    custom_mupulses : str, default 'MUPULSES'
        Label of the column(s) containing the times of firing of the custom
        file. Ignore if loading other files.
    custom_binary_mus_firing : str, default 'BINARY_MUS_FIRING'
        Label of the column(s) containing the binary representation
        of the MUs firings of the custom file.
        Ignore if loading other files.
    custom_accuracy : str, default 'ACCURACY'
        Label of the column(s) containing the accuracy score of the
        decomposed MUs in the custom file.
        Ignore if loading other files.
    custom_extras : str, default 'EXTRAS'
        Label of the column(s) containing custom values in the custom file.
        This information will be stored in a pd.DataFrame with columns named
        as in the .csv file.
        Ignore if loading other files.
    custom_fsamp : int, default 2048
        Tha sampling frequency of the custom file.
        Ignore if loading other files.
    custom_ied : int, default 8
        The inter-electrode distance in mm of the custom file.
        Ignore if loading other files.

    Returns
    -------
    emgfile : dict or None
        The dictionary containing the emgfile. If the selection process was
        cancelled, it returns None.

    See also
    --------
    - asksavefile : select where to save files with a GUI.

    Notes
    -----
    The returned file is called ``emgfile`` for convention (or ``emg_refsig``
    if SOURCE in ["OTB_REFSIG", "CUSTOMCSV_REFSIG", "DELSYS_REFSIG"]).

    The input .mat file exported from the OTBiolab+ software should have a
    specific content:

    - refsig signal is optional but, if present, there should be both the
        fullsampled and the subsampled version (in OTBioLab+ the "performed
        path" refers to the subsampled signal, the "acquired data" to the
        fullsampled signal), REF_SIGNAL is expected to be expressed as % of
        the MViF (but not compulsory).
    - Both the IPTS ('Source for decomposition...' in OTBioLab+) and the
        BINARY_MUS_FIRING ('Decomposition of...' in OTBioLab+) should be
        present.
    - The raw EMG signal should be present (it has no specific name in
        OTBioLab+) with all the channels. Don't exclude unwanted channels
        before exporting the .mat file.
    - NO OTHER ELEMENTS SHOULD BE PRESENT! unless an appropriate regex pattern
    is passed to 'extras='!

    For Delsys files:
    We collect the raw EMG and the reference signal from the .mat file
    exported from the Delsys Neuromap software because the .csv doesn't
    contain the information about sampling frequency.
    Similarly, we collect the firing times, MUAPs and accuracy from the .txt
    files exported from the Delsys Neuromap Explorer software because in the
    .mat file, the accuracy is contained in a table, which is not compatible
    with Python.

    For custom .csv files:
    The variables of interest should be contained in columns. The name of the
    columns containing each variable can be specified by the user if different
    from the default values.
    This function detects the content of the .csv by parsing the .csv columns.
    For parsing, column labels should be provided. A label is a term common
    to all the columns containing the same information.
    For example, if the raw signal is contained in the columns 'RAW_SIGNAL_1',
    'RAW_SIGNAL_2', ... , 'RAW_SIGNAL_n', the label of the columns should be
    'RAW_SIGNAL'.
    If the parameters in input are not present in the .csv file, the user
    can simply leave the original inputs.
    Please see the documentation of the function emg_from_customcsv for
    additional informations.
    The .csv file must contain all the variables. The only admitted exceptions
    are 'ref_signal' and 'ipts'.

    Structure of the returned emgfile:

        emgfile = {
            "SOURCE": SOURCE,
            "FILENAME": FILENAME,
            "RAW_SIGNAL": RAW_SIGNAL,
            "REF_SIGNAL": REF_SIGNAL,
            "ACCURACY": accuracy score (depending on source file type),
            "IPTS": IPTS (depending on source file type),
            "MUPULSES": MUPULSES,
            "FSAMP": FSAMP,
            "IED": IED,
            "EMG_LENGTH": EMG_LENGTH,
            "NUMBER_OF_MUS": NUMBER_OF_MUS,
            "BINARY_MUS_FIRING": BINARY_MUS_FIRING,
            "EXTRAS": EXTRAS,
        }

    Structure of the returned emg_refsig:

        emg_refsig = {
            "SOURCE": SOURCE,
            "FILENAME": FILENAME,
            "FSAMP": FSAMP,
            "REF_SIGNAL": REF_SIGNAL,
            "EXTRAS": EXTRAS,
        }

    Examples
    --------
    For an extended explanation of the imported emgfile use:

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="OPENHDEMG")
    >>> info = emg.info()
    >>> info.data(emgfile)
    """

    # Warn for the use of a deprecated parameter
    if kwargs.get("initialdir") is not None:
        msg = (
            "The initialdir parameter is deprecated and no longer valid. " +
            "The UI now remembers the last accessed directory."
        )
        warnings.warn(msg, DeprecationWarning, stacklevel=2)

    # Get the path to the file
    if filesource in ["DEMUSE", "OTB", "OTB_REFSIG", "DELSYS_REFSIG"]:
        file_toOpen = run_custom_file_dialog(
            mode="open",
            filesource=filesource,
            filetypes=[("MATLAB files", "*.mat")],
        )
    elif filesource == "DELSYS":
        emg_file_toOpen = run_custom_file_dialog(
            mode="open",
            filesource=filesource,
            filetypes=[("MATLAB files", "*.mat")],
        )
        mus_file_toOpen = run_custom_directory_dialog(
            window_title="Select the folder containing DELSYS decomposition",
        )
    elif filesource == "OPENHDEMG":
        file_toOpen = run_custom_file_dialog(
            mode="open",
            filesource=filesource,
            filetypes=[("JSON files", "*.json")],
        )
    elif filesource in ["CUSTOMCSV", "CUSTOMCSV_REFSIG"]:
        file_toOpen = run_custom_file_dialog(
            mode="open",
            filesource=filesource,
            filetypes=[("CSV files", "*.csv")],
        )
    else:
        raise ValueError(
            "\nfilesource not valid, it must be one of " +
            "'DEMUSE', 'OTB', 'DELSYS', 'OTB_REFSIG', 'DELSYS_REFSIG', " +
            "'OPENHDEMG', 'CUSTOMCSV', 'CUSTOMCSV_REFSIG'\n"
        )

    # Check if a file has been selected. If not, return None
    if file_toOpen is None:
        return file_toOpen

    print("Loading file\n------------\n")

    # Open file depending on file origin
    if filesource == "DEMUSE":
        emgfile = emg_from_demuse(
            filepath=file_toOpen,
            ignore_negative_ipts=kwargs.get("ignore_negative_ipts", False),
        )
    elif filesource == "OTB":
        emgfile = emg_from_otb(
            filepath=file_toOpen,
            ext_factor=kwargs.get("otb_ext_factor", 8),
            refsig=kwargs.get("otb_refsig_type", [True, "fullsampled"]),
            version=kwargs.get("otb_version", "1.5.9.3"),
            extras=kwargs.get("otb_extras", None),
            ignore_negative_ipts=kwargs.get("ignore_negative_ipts", False),
        )
    elif filesource == "OTB_REFSIG":
        ref = kwargs.get("otb_refsig_type", [True, "fullsampled"])
        emgfile = refsig_from_otb(
            filepath=file_toOpen,
            refsig=ref[1],
            version=kwargs.get("otb_version", "1.5.9.3"),
            extras=kwargs.get("otb_extras", None),
        )
    elif filesource == "DELSYS":
        emgfile = emg_from_delsys(
            rawemg_filepath=emg_file_toOpen,
            mus_directory=mus_file_toOpen,
            emg_sensor_name=kwargs.get(
                "delsys_emg_sensor_name", "Galileo sensor"
            ),
            refsig_sensor_name=kwargs.get(
                "delsys_refsig_sensor_name", "Trigno Load Cell"
            ),
            filename_from=kwargs.get(
                "delsys_filename_from", "mus_directory"
            ),
        )
    elif filesource == "DELSYS_REFSIG":
        emgfile = refsig_from_delsys(
            filepath=file_toOpen,
            refsig_sensor_name=kwargs.get(
                "delsys_refsig_sensor_name", "Trigno Load Cell"
            ),
        )
    elif filesource == "OPENHDEMG":
        emgfile = emg_from_json(filepath=file_toOpen)
    elif filesource == "CUSTOMCSV":
        emgfile = emg_from_customcsv(
            filepath=file_toOpen,
            ref_signal=kwargs.get("custom_ref_signal", "REF_SIGNAL"),
            raw_signal=kwargs.get("custom_raw_signal", "RAW_SIGNAL"),
            ipts=kwargs.get("custom_ipts", "IPTS"),
            mupulses=kwargs.get("custom_mupulses", "MUPULSES"),
            binary_mus_firing=kwargs.get(
                "custom_binary_mus_firing",
                "BINARY_MUS_FIRING"
            ),
            accuracy=kwargs.get("custom_accuracy", "ACCURACY"),
            extras=kwargs.get("custom_extras", "EXTRAS"),
            fsamp=kwargs.get("custom_fsamp", 2048),
            ied=kwargs.get("custom_ied", 8),
        )
    else:  # CUSTOMCSV_REFSIG
        emgfile = refsig_from_customcsv(
            filepath=file_toOpen,
            ref_signal=kwargs.get("custom_ref_signal", "REF_SIGNAL"),
            extras=kwargs.get("custom_extras", "EXTRAS"),
            fsamp=kwargs.get("custom_fsamp", 2048),
        )

    print("File loaded\n------------\n")

    return emgfile


def asksavefile(emgfile, compresslevel=4):
    """
    Select where to save files with a GUI.

    !!! note "Since version 0.2.0"
        The recommended workflow for saving and loading openhdemg data now
        relies on the following high-level functions and classes for binary
        files:

        - `save_openhdemg_module`
        - `asksavemodule`
        - `load_openhdemg_module`
        - `askloadmodule`
        - `openhdemg_Collection`

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile to save.
    compresslevel : int, default 4
        An int from 0 to 9, where 0 is no compression and nine maximum
        compression. Compressed files will take less space, but will require
        more computation. The relationship between compression level and time
        required for the compression is not linear. For optimised performance,
        we suggest values between 2 and 6, with 4 providing the best balance.

    See also
    --------
    - askopenfile : select and open files with a GUI.
    """

    # Get the filepath
    filepath = run_custom_file_dialog(
        mode="save",
        filesource="OPENHDEMG",
        filetypes=[("JSON files", "*.json")],
    )

    print("\n-----------\nSaving file\n")

    save_json_emgfile(emgfile, filepath, compresslevel)

    print("File saved\n-----------\n")


def emg_from_samplefile():
    """
    Load the sample file. This file has been decomposed with the OTBiolab+
    software and contains some reference MUs together with the force/reference
    signal.

    This file contains only few MUs for storage reasons.

    Returns
    -------
    emgfile : dict
        The dictionary containing the emgfile.
    """

    # Get the absolute path to the script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the absolute path to the file in the data subfolder
    file_path = os.path.join(
        script_dir,
        'decomposed_test_files',
        'otb_testfile.mat',
    )

    # Load the file
    emgfile = emg_from_otb(
        filepath=file_path,
        ext_factor=8,
        refsig=[True, "fullsampled"],
        version="1.5.8.0",
    )

    return emgfile
