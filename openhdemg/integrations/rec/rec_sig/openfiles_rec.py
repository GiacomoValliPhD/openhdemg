"""
Loaders for the .sig files exportable from ReC_Bioengineering
ReC/MEACS and ReC/BAM acquisition systems.
"""

import os
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from openhdemg.library.tools import standardise_emgfile_dtypes


def emg_from_rec(filepath, gam_filepath=None, gam_channels=None, ied=10.0):
    """
    Generic loader for ReC/MEACS and ReC/BAM .sig files.

    The acquisition system that produced ``filepath`` is identified from
    the system code embedded in its filename (the underscore-delimited
    segment immediately preceding "_EMG_raw", e.g. "M02CF1" in
    "Dy14042025_180733_M02CF1_EMG_raw.sig"). Based on the first letter of
    that code, the file is loaded with the matching system-specific
    loader:

        "M" -> emg_from_rec_meacs
        "B" -> emg_from_rec_bam

    Optionally, one or more channels from a GAM auxiliary file
    can be appended as extra columns of REF_SIGNAL.

    Parameters
    ----------
    filepath : str or Path
        Path to the *_EMG_raw.sig file to load. This is typically the
        path returned by the file-selection interface in
        openhdemg.integrations.rec.rec.
    gam_filepath : str or Path or None, default None
        Optional path to a GAM auxiliaryfile. Its filename
        carries "G" in the same position as "M"/"B", and it does not end
        in "_EMG_raw" (e.g. "Dy14042025_180733_G01AA3_AUX_raw.sig"). If
        None, or if the file does not exist, no GAM data is loaded and
        REF_SIGNAL is unaffected by this parameter.
    gam_channels : int or list of int or None, default None
        0-based channel indices to extract from the GAM file and append
        as extra columns of REF_SIGNAL. Required if gam_filepath is
        provided and points to an existing file.
    ied : float, default 10.0
        The interelectrode distance, in mm, of the matrix used to
        acquire filepath. Passed through to emg_from_rec_meacs or
        emg_from_rec_bam.

    Returns
    -------
    emgfile : dict
        The dictionary returned by emg_from_rec_meacs or emg_from_rec_bam
        (depending on the system identified from filepath), with
        REF_SIGNAL additionally containing the requested GAM channels as
        extra columns, if gam_filepath was provided and found.

    See also
    --------
    - emg_from_rec_meacs : Import .sig files from ReC/MEACs systems.
    - emg_from_rec_bam : Import .sig files from ReC/BAM systems.

    Raises
    ------
    ValueError
        If the system code cannot be identified from filepath, if it
        starts with a letter other than "M" or "B", if gam_channels is
        not provided while gam_filepath points to an existing file, or if
        a requested GAM channel index is out of range.

    Examples
    --------
    >>> import openhdemg.library as emg
    >>> emgfile = emg.emg_from_rec(
    ...     filepath="path/Dy14042025_180733_M02CF1_EMG_raw.sig",
    ...     gam_filepath="path/Dy14042025_180733_G01AA3_AUX_raw.sig",
    ...     gam_channels=[4],
    ...     ied=10.0,
    ... )
    """
    filepath = Path(filepath)
    FILENAME = filepath.name

    stem_before_emg = FILENAME.split("_EMG_raw")[0]
    if stem_before_emg == FILENAME or "_" not in stem_before_emg:
        raise ValueError(
            f"\nCould not identify the system code in {FILENAME}. "
            "emg_from_rec() expects a *_EMG_raw.sig file with the system "
            "code as the underscore-delimited segment right before "
            "'_EMG_raw' (e.g. '..._M02CF1_EMG_raw.sig').\n"
        )
    code_segment = stem_before_emg.rsplit("_", 1)[-1]

    system_letter = code_segment[0].upper()

    if system_letter == "M":
        emgfile = emg_from_rec_meacs(filepath, ied=ied)
    elif system_letter == "B":
        emgfile = emg_from_rec_bam(filepath, ied=ied)
    else:
        raise ValueError(
            f"\nUnrecognized ReC system code '{code_segment}' in "
            f"{FILENAME}. The code must start with 'M' (ReC/MEACs) or "
            "'B' (ReC/BAM).\n"
        )

    if gam_filepath is not None:
        gam_filepath = Path(gam_filepath)

        if gam_filepath.exists():
            if gam_channels is None:
                raise ValueError(
                    "\ngam_channels must be specified (as an int or a "
                    "list of channel indices) when gam_filepath is "
                    "provided.\n"
                )

            gam_df = aux_from_rec_gam(
                gam_filepath=gam_filepath,
                gam_channels=gam_channels,
                emg_length=emgfile["EMG_LENGTH"],
            )

            # If the GAM signal and the rest of the emgfile do not have
            # the same number of samples, truncate everything (RAW_SIGNAL,
            # REF_SIGNAL, EMG_LENGTH and the GAM channels) to the shorter
            # of the two, so that all columns of REF_SIGNAL stay aligned
            # sample-by-sample 
            min_len = min(emgfile["EMG_LENGTH"], gam_df.shape[0])
            if min_len != emgfile["EMG_LENGTH"]:
                emgfile["RAW_SIGNAL"] = (
                    emgfile["RAW_SIGNAL"].iloc[:min_len].reset_index(drop=True)
                )
                if not emgfile["REF_SIGNAL"].empty:
                    emgfile["REF_SIGNAL"] = (
                        emgfile["REF_SIGNAL"].iloc[:min_len]
                        .reset_index(drop=True)
                    )
                emgfile["EMG_LENGTH"] = min_len
            if gam_df.shape[0] != min_len:
                gam_df = gam_df.iloc[:min_len].reset_index(drop=True)

            if emgfile["REF_SIGNAL"].empty:
                combined = gam_df
            else:
                combined = pd.concat(
                    [
                        emgfile["REF_SIGNAL"].reset_index(drop=True),
                        gam_df.reset_index(drop=True),
                    ],
                    axis=1,
                )
            combined.columns = [*range(combined.shape[1])]
            emgfile["REF_SIGNAL"] = combined
        else:
            warnings.warn(
                f"\nGAM file {gam_filepath.name} not found. No GAM "
                "channels were added to REF_SIGNAL.\n"
            )

    # Always standardise the emgfile dtypes before returning
    emgfile = standardise_emgfile_dtypes(emgfile)

    return emgfile
# ---------------------------------------------------------------------
def aux_from_rec_gam(gam_filepath, gam_channels, emg_length):
    """
    Read one or more channels from a ReC GAM auxiliary file.

    Parameters
    ----------
    gam_filepath : str or Path
        Path to the GAM auxiliary file (its filename carries "G" in the
        same position as "M"/"B", e.g.
        "Dy14042025_180733_G01AA3_AUX_raw.sig").
    gam_channels : int or list of int
        0-based channel indices to extract from the GAM file.
    emg_length : int
        The expected number of samples, typically the EMG_LENGTH of the
        emgfile the GAM channels will be appended to. If the GAM file
        contains a different number of samples, a warning is raised;
        emg_from_rec() then truncates the whole emgfile (RAW_SIGNAL,
        REF_SIGNAL, EMG_LENGTH) and the GAM channels to the shorter of
        the two, so that everything stays aligned sample-by-sample.

    Returns
    -------
    gam_df : pd.DataFrame
        The requested GAM channels converted to Volts, as columns
        0, 1, ... in the same order as gam_channels.

    See also
    --------
    - emg_from_rec : Uses this function to optionally append GAM channels
        to REF_SIGNAL.

    Raises
    ------
    ValueError
        If any index in gam_channels is out of range (the GAM file has a
        fixed number of 14 channels, 0 to 13).

    Examples
    --------
    >>> from openhdemg.integrations.rec.rec_sig.openfiles_rec import (
    ...     aux_from_rec_gam,
    ... )
    >>> gam_df = aux_from_rec_gam(
    ...     gam_filepath="path/Dy14042025_180733_G01AA3_AUX_raw.sig",
    ...     gam_channels=[4],
    ...     emg_length=122880,
    ... )
    """
    gam_filepath = Path(gam_filepath)

    if isinstance(gam_channels, int):
        gam_channels = [gam_channels]

    n_gam_chs = 14
    gam_dyn_range = 3.3 # volt
    gam_dtype = np.dtype("uint16")

    if any(ch < 0 or ch >= n_gam_chs for ch in gam_channels):
        raise ValueError(
            f"\ngam_channels must be indices between 0 and "
            f"{n_gam_chs - 1} ({n_gam_chs} GAM channels available).\n"
        )

    gam_size = os.path.getsize(gam_filepath)
    gam_bytes_per_sample = gam_dtype.itemsize
    gam_samples = gam_size // gam_bytes_per_sample
    gam_length = gam_samples // n_gam_chs

    gam_raw = np.fromfile(
        gam_filepath,
        dtype=gam_dtype,
        count=gam_length * n_gam_chs,
    )
    gam_raw = gam_raw.reshape((gam_length, n_gam_chs)).astype(np.float64)

    gam_max_lev = 2 ** 16
    gam_raw = (gam_raw / gam_max_lev) * gam_dyn_range

    gam_selected = gam_raw[:, gam_channels]

    if gam_selected.shape[0] != emg_length:
        warnings.warn(
            f"\nGAM signal length ({gam_selected.shape[0]}) does not "
            f"match RAW_SIGNAL length ({emg_length}). The whole emgfile "
            "and the GAM channels will be truncated to the shorter of "
            "the two.\n"
        )

    return pd.DataFrame(gam_selected)
# ---------------------------------------------------------------------
def emg_from_rec_meacs(filepath, ied=10.0):
    """
    Import the .sig file exportable from ReC/MEACS systems.

    Parameters
    ----------
    filepath : str or Path
        The directory and the name of the file to load
        (including file extension .sig).
        This can be a simple string, the use of Path is not necessary.
    ied : float, default 10.0
        The interelectrode distance, in mm, of the matrix used to
        acquire filepath.

    Returns
    -------
    emgfile : dict
        A dictionary containing all the useful variables. RAW_SIGNAL is
        expressed in microvolts (µV), centered on 0. Since .sig files
        contain no decomposition, ACCURACY, IPTS, MUPULSES and
        BINARY_MUS_FIRING are returned empty and NUMBER_OF_MUS is 0.
        
    Raises
    ------
    ValueError
        If the file is too short to contain even a single full sample
        across all channels.

    Examples
    --------
    >>> import openhdemg.library as emg
    >>> emgfile = emg.emg_from_rec_meacs(filepath="path/filename.sig")
    >>> info = emg.info()
    >>> info.data(emgfile)
    """
    fsamp_hz=2048
    n_chs=32
    dtype='uint16'
    adc_res=16
    din=2.4 # volt
    gain=192

    SOURCE = "REC"
    filepath = Path(filepath)
    FILENAME = filepath.name

    np_dtype = np.dtype(dtype)
    bytes_per_sample = np_dtype.itemsize

    # Raises FileNotFoundError on its own if filepath does not exist.
    file_size = os.path.getsize(filepath)
    total_samples = file_size // bytes_per_sample
    EMG_LENGTH = total_samples // n_chs

    if EMG_LENGTH <= 0:
        raise ValueError(
            f"\nFile {FILENAME} is too short to contain a full sample "
            f"across {n_chs} channels\n"
        )

    if total_samples % n_chs != 0:
        warnings.warn(
            f"\nFile size is not an exact multiple of {n_chs} channels. "
            "Truncating excess samples.\n"
        )

    # Read the raw, unsigned ADC codes
    raw = np.fromfile(filepath, dtype=np_dtype, count=EMG_LENGTH * n_chs)
    raw = raw.reshape((EMG_LENGTH, n_chs)).astype(np.float64)

    zero_ref = 2 ** (adc_res - 1)
    max_lev = 2 ** adc_res
    raw = ((raw - zero_ref) / max_lev) * din / gain * 1e6

    RAW_SIGNAL = pd.DataFrame(raw, columns=[*range(n_chs)])

     # Look for a synchronization/AUX file in the same folder
    aux_filepath = filepath.with_name(
        filepath.name.replace("EMG_raw", "AUX1_raw")
    )

    if aux_filepath.exists():
        aux_size = os.path.getsize(aux_filepath)
        aux_samples = aux_size // bytes_per_sample
        aux_raw = np.fromfile(
            aux_filepath, dtype=np_dtype, count=aux_samples,
        ).astype(np.float64)

        aux_raw = (aux_raw / max_lev) * din / gain  # Volts, no *1e6
        if len(aux_raw) != EMG_LENGTH:
            warnings.warn(
                f"\nAUX signal length ({len(aux_raw)}) does not match "
                f"RAW_SIGNAL length ({EMG_LENGTH}). Truncating to the "
                "shorter of the two.\n"
            )
            min_len = min(len(aux_raw), EMG_LENGTH)
            aux_raw = aux_raw[:min_len]

        REF_SIGNAL = pd.DataFrame(aux_raw, columns=[0])
    else:
        REF_SIGNAL = pd.DataFrame(columns=[0])
        warnings.warn(
            f"\nSynchronization file {aux_filepath.name} not found next "
            f"to {FILENAME}. REF_SIGNAL will be empty, it might be "
            "necessary for some analyses.\n"
        )

    emgfile = {
        "SOURCE": SOURCE,
        "FILENAME": FILENAME,
        "RAW_SIGNAL": RAW_SIGNAL,
        "REF_SIGNAL": REF_SIGNAL,
        "ACCURACY": pd.DataFrame(columns=[0]),
        "IPTS": pd.DataFrame(columns=[0]),
        "MUPULSES": [],
        "FSAMP": float(fsamp_hz),
        "IED":float(ied),
        "EMG_LENGTH": EMG_LENGTH,
        "NUMBER_OF_MUS": 0,
        "BINARY_MUS_FIRING": pd.DataFrame(columns=[0]),
        "EXTRAS": pd.DataFrame(columns=[0]),
    }

    return emgfile
# ---------------------------------------------------------------------
def emg_from_rec_bam(filepath, ied=10.0):
    """
    Import the .sig file exportable from ReC/BAM systems.

    Parameters
    ----------
    filepath : str or Path
        The directory and the name of the file to load
        (including file extension .sig).
        This can be a simple string, the use of Path is not necessary.
    ied : float, default 10.0
        The interelectrode distance, in mm, of the matrix used to
        acquire filepath.

    Returns
    -------
    emgfile : dict
        A dictionary containing all the useful variables. RAW_SIGNAL is
        expressed in microvolts (µV), centered on 0. Since .sig files
        contain no decomposition, ACCURACY, IPTS, MUPULSES and
        BINARY_MUS_FIRING are returned empty and NUMBER_OF_MUS is 0.

    Raises
    ------
    ValueError
        if the file is too short to contain even a single full sample 
        across all channels.

    Examples
    --------
    >>> import openhdemg.library as emg
    >>> emgfile = emg.emg_from_rec_bam(filepath="path/filename.sig")
    >>> info = emg.info()
    >>> info.data(emgfile)
    """
    fsamp_hz=2048
    n_chs=64
    dtype='uint16'
    adc_res=16
    din=3.3 # volt
    gain=1

    SOURCE = "REC"
    filepath = Path(filepath)
    FILENAME = filepath.name

    np_dtype = np.dtype(dtype)
    bytes_per_sample = np_dtype.itemsize

    # Raises FileNotFoundError on its own if filepath does not exist.
    file_size = os.path.getsize(filepath)
    total_samples = file_size // bytes_per_sample
    EMG_LENGTH = total_samples // n_chs

    if EMG_LENGTH <= 0:
        raise ValueError(
            f"\nFile {FILENAME} is too short to contain a full sample "
            f"across {n_chs} channels\n"
        )

    if total_samples % n_chs != 0:
        warnings.warn(
            f"\nFile size is not an exact multiple of {n_chs} channels. "
            "Truncating excess samples.\n"
        )

    # Read the raw, unsigned ADC codes
    raw = np.fromfile(filepath, dtype=np_dtype, count=EMG_LENGTH * n_chs)
    raw = raw.reshape((EMG_LENGTH, n_chs)).astype(np.float64)

    zero_ref = 2 ** (adc_res - 1)
    max_lev = 2 ** adc_res
    raw = ((raw - zero_ref) / max_lev) * din / gain * 1e6

    RAW_SIGNAL = pd.DataFrame(raw, columns=[*range(n_chs)])

    # Look for a synchronization/AUX file in the same folder
    aux_filepath = filepath.with_name(
        filepath.name.replace("EMG_raw", "AUX1_raw")
    )

    if aux_filepath.exists():
        aux_size = os.path.getsize(aux_filepath)
        aux_samples = aux_size // bytes_per_sample
        aux_raw = np.fromfile(
            aux_filepath, dtype=np_dtype, count=aux_samples,
        ).astype(np.float64)

        aux_raw = (aux_raw / max_lev) * din / gain  # Volts, no *1e6
        if len(aux_raw) != EMG_LENGTH:
            warnings.warn(
                f"\nAUX signal length ({len(aux_raw)}) does not match "
                f"RAW_SIGNAL length ({EMG_LENGTH}). Truncating to the "
                "shorter of the two.\n"
            )
            min_len = min(len(aux_raw), EMG_LENGTH)
            aux_raw = aux_raw[:min_len]

        REF_SIGNAL = pd.DataFrame(aux_raw, columns=[0])
    else:
        REF_SIGNAL = pd.DataFrame(columns=[0])
        warnings.warn(
            f"\nSynchronization file {aux_filepath.name} not found next "
            f"to {FILENAME}. REF_SIGNAL will be empty, it might be "
            "necessary for some analyses.\n"
        )

    emgfile = {
        "SOURCE": SOURCE,
        "FILENAME": FILENAME,
        "RAW_SIGNAL": RAW_SIGNAL,
        "REF_SIGNAL": REF_SIGNAL,
        "ACCURACY": pd.DataFrame(columns=[0]),
        "IPTS": pd.DataFrame(columns=[0]),
        "MUPULSES": [],
        "FSAMP": float(fsamp_hz),
        "IED": float(ied),
        "EMG_LENGTH": EMG_LENGTH,
        "NUMBER_OF_MUS": 0,
        "BINARY_MUS_FIRING": pd.DataFrame(columns=[0]),
        "EXTRAS": pd.DataFrame(columns=[0]),
    }

    return emgfile
