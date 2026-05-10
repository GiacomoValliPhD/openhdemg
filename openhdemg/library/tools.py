"""
This module contains the functions that don't properly apply to the plot
or analysis category but that are necessary for the usability of the library.
The functions contained in this module can be considered as "tools" or
shortcuts necessary to operate with the HD-EMG recordings.
"""

import copy
import warnings

import numpy as np
import pandas as pd
from scipy import signal
from scipy.stats import iqr
from sklearn.svm import SVR

from openhdemg.ui.widgets import (
    run_point_selector, run_manual_emgchannels_selection_dialog
)
from openhdemg.library.mathtools import (
    discrete_spike_xcorr, compute_sil, compute_pulses_agreement_rate
)


def standardise_emgfile_dtypes(emgfile):
    """
    Standardise the data types of fields in an emgfile dictionary.

    This function ensures that each standard key conforms to a predefined data
    type specification. It enforces numeric data types, and standardises array
    and scalar types to maintain consistency across saving/loading and
    processing of the emgfile.

    For motor unit pulse trains, all arrays are verified to be one-dimensional.
    If a non-1D array is detected, the function issues a warning and
    automatically flattens it to 1D to preserve compatibility.

    The following keys are checked and standardised:

    - `"SOURCE"` (str)
    - `"FILENAME"` (str)
    - `"RAW_SIGNAL"` (pandas.DataFrame, np.float64)
    - `"REF_SIGNAL"` (pandas.DataFrame, np.float64)
    - `"ACCURACY"` (pandas.DataFrame, np.float64)
    - `"IPTS"` (pandas.DataFrame, np.float64)
    - `"MUPULSES"` (list of 1D numpy.ndarray, np.int64)
    - `"FSAMP"` (float)
    - `"IED"` (float)
    - `"EMG_LENGTH"` (int)
    - `"NUMBER_OF_MUS"` (int)
    - `"BINARY_MUS_FIRING"` (pandas.DataFrame, np.uint8)

    - `"GOOD_CHANNELS"` (dict{str: int})
    - `"REFERENCE_MUPULSES"` (list of 1D numpy.ndarray, np.int64)
    - `"ROA_WITH_REFERENCE_MUPULSES"` (pandas.DataFrame, np.float64)

    Any additional keys (e.g., `"EXTRAS"`) are preserved but not type-checked.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.

    Returns
    -------
    dict
        A deep copy of the input emgfile where all recognised fields have been
        standardised to the expected data types.

    Raises
    ------
    TypeError
        If a recognised field does not match the expected data type or cannot
        be cast.

    Warns
    -----
    UserWarning
        If "MUPULSES"[n] or "REFERENCE_MUPULSES"[n] is not 1D and is flattened.

    Examples
    --------
    Check data types for IPTS of the sample emgfile.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.emg_from_samplefile()
    >>> print(emgfile["IPTS"].dtypes)
    0    float32
    1    float32
    2    float32
    3    float32
    4    float32
    dtype: object

    Standardise the emgfile and check again the data types for IPTS.

    >>> standard_emgfile = emg.standardise_emgfile_dtypes(emgfile)
    >>> print(standard_emgfile["IPTS"].dtypes)
    0    float64
    1    float64
    2    float64
    3    float64
    4    float64
    dtype: object
    """

    data = copy.deepcopy(emgfile)

    spec = {
        "SOURCE": str,
        "FILENAME": str,
        "RAW_SIGNAL": ("pd.DataFrame", np.float64),
        "REF_SIGNAL": ("pd.DataFrame", np.float64),
        "ACCURACY": ("pd.DataFrame", np.float64),
        "ROA_WITH_REFERENCE_MUPULSES": ("pd.DataFrame", np.float64),
        "IPTS": ("pd.DataFrame", np.float64),
        "MUPULSES": ("list_of_np", np.int64),
        "REFERENCE_MUPULSES": ("list_of_np", np.int64),
        "FSAMP": np.float64,
        "IED": np.float64,
        "EMG_LENGTH": np.int64,
        "NUMBER_OF_MUS": np.int64,
        "BINARY_MUS_FIRING": ("pd.DataFrame", np.uint8),  # TODO document uint8
        # "EXTRAS" => Skip checks for extras and any other custom key
    }

    for key, expected in spec.items():

        if key not in data:
            continue  # Skip

        if isinstance(expected, tuple):
            kind, dtype = expected

            if kind == "pd.DataFrame":
                if not isinstance(data[key], pd.DataFrame):
                    raise TypeError(f"{key} must be a pandas DataFrame")
                # Cast data
                data[key] = data[key].astype(dtype)

            elif kind == "list_of_np":
                if not isinstance(data[key], list) or not all(
                    isinstance(arr, np.ndarray) for arr in data[key]
                ):
                    raise TypeError(f"{key} must be a list of numpy arrays")

                # Flatten to 1D if not already  # TODO document this
                fixed_arrays = []
                for i, arr in enumerate(data[key]):
                    if arr.ndim != 1:
                        warnings.warn(
                            f"Array {i} in '{key}' is not 1D (got shape "
                            f"{arr.shape}). It will be flattened.",
                            UserWarning,
                            stacklevel=2
                        )
                        arr = arr.ravel()
                    fixed_arrays.append(arr.astype(dtype))

                data[key] = fixed_arrays

        else:
            # Single value casting
            data[key] = expected(data[key])

    # Non-standard keys
    # GOOD_CHANNELS => dict{str: int}
    if isinstance(data.get("GOOD_CHANNELS"), dict):
        data["GOOD_CHANNELS"] = {
            str(k): int(v)
            for k, v in data["GOOD_CHANNELS"].items()
        }

    return data


def showselect(
    emgfile,
    how="ref_signal",
    refsig_channel=0,
    title="",
    titlesize=12,
    nclic=2,
):
    """
    Visually select a part of the recording (X axis).

    The area can be selected based on the reference signal or based on the
    mean EMG signal. Users can move the mouse to track coordinates and press:

        - "A" or "a" to add a point at the current cursor location
        - "D" or "d" to delete the last selected point
        - "Enter" to confirm the selection and close the window

    This function does not check whether the selected points are within the
    effective file duration. This should be done based on user's need.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    how : str {"ref_signal", "mean_emg"}, default "ref_signal"
        What to display in the figure used to visually select the area to
        resize.

        ``ref_signal``
            Visualise the reference signal to select the area to resize.

        ``mean_emg``
            Visualise the mean EMG signal to select the area to resize.
    refsig_channel : int or str, Default 0
        The name of the reference signal channel (dataframe column) to plot.
    title : str
        The title of the plot. It is optional but strongly recommended.
        It should describe the task to do.
    titlesize : int, default 12
        The font size of the title.
    nclic: int, default 2
        The number of clics to be collected. If nclic < 1, all the clicks are
        collected.

    Returns
    -------
    points : list
        A list containing the selected points sorted in ascending order.

    Examples
    --------
    Load the EMG file and select the points based on the reference signal.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="OTB_REFSIG")
    >>> points = emg.showselect(
    ...     emgfile,
    ...     how="ref_signal",
    ...     title="Select 2 points",
    ...     nclic=2,
    ... )
    >>> points
    [16115, 40473]

    Load the EMG file and select the points based on the mean EMG signal.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="OPENHDEMG")
    >>> points = emg.showselect(
    ...     emgfile,
    ...     how="mean_emg",
    ...     title="Select 2 points",
    ...     nclic=2,
    ... )
    >>> points
    [135, 26598]
    """

    # Get the data to plot
    if how == "ref_signal":
        data_to_plot = emgfile["REF_SIGNAL"].loc[:, refsig_channel]
        y_label = "Reference signal"
    elif how == "mean_emg":
        data_to_plot = emgfile["RAW_SIGNAL"].mean(axis=1)
        y_label = "Mean EMG signal"
    else:
        raise ValueError(
            "Wrong argument in showselect(). how can only be 'ref_signal' or "
            f"'mean_emg'. {how} was passed instead."
        )
    # Normalise for plotting
    data_to_plot = np.asarray(data_to_plot, dtype=np.float64).ravel()

    res = run_point_selector(
        data=data_to_plot,
        nclic=nclic,
        y_label=y_label,
        title=title,
        title_fontsize=titlesize,
    )

    points = [round(point[0]) for point in res]
    points.sort()

    return points


def create_binary_firings(emg_length, number_of_mus, mupulses):
    """
    Create a binary representation of the MU firing.

    Create a binary representation of the MU firing over time
    based on the times of firing of each MU.

    Parameters
    ----------
    emg_length : int
        Number of samples (length) in the emg file.
    number_of_mus : int
        Number of MUs in the emg file.
    mupulses : list of ndarrays
        Each ndarray should contain the times of firing (in samples) of each
        MU.

    Returns
    -------
    binary_MUs_firing : pd.DataFrame
        A pd.DataFrame containing the binary representation of MUs firing.
        Please note that dtype=np.uint8. Please convert before processing.
    """

    # Skip the step if I don't have the mupulses (is nan)
    if not isinstance(mupulses, list):
        raise ValueError("mupulses is not a list of ndarrays")

    # Initialise a pd.DataFrame with zeros
    binary_MUs_firing = pd.DataFrame(
        np.zeros((emg_length, number_of_mus), dtype=np.uint8)
    )

    for mu in range(number_of_mus):
        if len(mupulses[mu]) > 0:
            firing_points = mupulses[mu].astype(int)
            binary_MUs_firing.iloc[firing_points, mu] = 1

    return binary_MUs_firing


def mupulses_from_binary(binarymusfiring):
    """
    Extract the MUPULSES from the binary MUs firings.

    Parameters
    ----------
    binarymusfiring : pd.DataFrame
        A pd.DataFrame containing the binary representation of MUs firings.

    Returns
    -------
    MUPULSES : list
        A list of ndarrays containing the firing time (in samples) of each MU.
    """

    # Create empty list of lists to fill with ndarrays containing the MUPULSES
    # (instants of the firing)
    numberofMUs = len(binarymusfiring.columns)
    MUPULSES = [[] for _ in range(numberofMUs)]

    for mu in binarymusfiring:  # Loop all the MUs
        my_ndarray = []
        for idx, x in binarymusfiring[mu].items():  # Loop the MU firing times
            if x > 0:
                my_ndarray.append(idx)
                # Take the firing time and add it to the ndarray

        MUPULSES[mu] = np.array(my_ndarray, dtype=np.int64)

    return MUPULSES


def resize_emgfile(
    emgfile,
    area=None,
    how="ref_signal",
    refsig_channel=0,
    accuracy="recalculate",
    compute_on_peaks_only=True,
    roa_with_reference_mupulses="recalculate",
    custom_dataframes=None,
    ignore_negative_ipts=None,
):
    """
    Resize all the **STANDARD** components in the emgfile.

    This function can be useful to compute the various parameters only in the
    area of interest.

    !!! note "Since version 0.2.0"
        Specific **NON-STANDARD** components in the emgfile are also resized.

    For **STANDARD** we refer to:

    - `RAW_SIGNAL`
    - `REF_SIGNAL`
    - `IPTS`
    - `MUPULSES`
    - `EMG_LENGTH`
    - `BINARY_MUS_FIRING`
    - `ACCURACY` (if recalculated in the new portion)

    For **NON-STANDARD** we refer to:

    - `REFERENCE_MUPULSES`
    - `ROA_WITH_REFERENCE_MUPULSES`

    Additional dataframes contained in the emgfile will be resized if
    specified in "custom_dataframes".

    !!! note "Since version 0.2.0"
        The behaviour of this function has changed to ensure a more accurate
        SIL estimation. To maintain the old behaviour, you can set
        ``compute_on_peaks_only=False`` when ``accuracy=="recalculate``".

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile to resize.
    area : None or list, default None
        The resizing area. If already known, it can be passed in samples, as a
        list (e.g., [120, 2560]).
        If None, the user can select the area of interest manually.
    how : str {"ref_signal", "mean_emg"}, default "ref_signal"
        If area==None, allow the user to visually select the area to resize
        based on how.

        ``ref_signal``
            Visualise the reference signal to select the area to resize.

        ``mean_emg``
            Visualise the mean EMG signal to select the area to resize.
    refsig_channel : int or str, Default 0
        The name of the reference signal channel (dataframe column) to plot.
    accuracy : str {"recalculate", "maintain"}, default "recalculate"

        ``recalculate``
            The Silhouette score is computed in the new resized file. This can
            be done only if IPTS is present.

        ``maintain``
            The original accuracy measure already contained in the emgfile is
            returned without any computation.
    compute_on_peaks_only : bool, default True
        If True, the silhouette (SIL) score is computed using **only the ipts
        peaks**, rather than all values in the source signal. This can improve
        accuracy estimation by comparing MU spikes only against other
        candidate spikes, ignoring baseline or negative ipts values.
        If False, the noise cluster is defined as all samples not selected as
        MU spikes.
    roa_with_reference_mupulses : str {"recalculate", "maintain"}, default "recalculate"
        Whether to re-calculate the rate of agreement (ROA) between "MUPULSES"
        and "REFERENCE_MUPULSES".

        ``recalculate``
            The ROA is computed in the new resized file. This can
            be done only if both "MUPULSES" and "REFERENCE_MUPULSES" are
            present.

        ``maintain``
            The original ROA measure already contained in the emgfile is
            returned without any computation.
    custom_dataframes : list or None, default None
        A list of strings pointing to the additional dataframes to resize. The
        strings should match the emgfile keys associated to the pd.DataFrames.
    ignore_negative_ipts : None
        This parameter is deprecated and will be removed in future releases.
        Please transform the 'ipts' before if needed. To replicate the
        behaviour of 'ignore_negative_ipts=True' you can use
        'ipts * np.abs(ipts)'.

    Returns
    -------
    rs_emgfile : dict
        the new (resized) emgfile.
    start_, end_ : int
        the start and end of the selection (can be used for code automation).

    Notes
    -----
    Suggested names for the returned objects: rs_emgfile, start_, end_.

    Examples
    --------
    Manually select the area to resize the emgfile based on mean EMG signal
    and recalculate the silhouette score in the new portion of the signal.

    >>> emgfile = emg.askloadmodule()
    >>> rs_emgfile, start_, end_ = emg.resize_emgfile(
    ...     emgfile,
    ...     how="mean_emg",
    ...     accuracy="recalculate",
    ... )

    Automatically resize the emgfile in the pre-specified area. Do not
    recalculate the silhouette score in the new portion of the signal.

    >>> emgfile = emg.askopenfile(filesource="CUSTOMCSV")
    >>> rs_emgfile, start_, end_ = emg.resize_emgfile(
    ...     emgfile,
    ...     area=[120, 25680],
    ...     accuracy="maintain",
    ... )
    """

    # Manage deprecated parameters
    # TODO DeprecationWarning issued by compute_sil. Remove if the future.

    # Create the object to store the resized emgfile.
    rs_emgfile = copy.deepcopy(emgfile)

    # Verify which STANDARD keys are present
    _has_raw_signal = "RAW_SIGNAL" in rs_emgfile
    _has_ref_signal = "REF_SIGNAL" in rs_emgfile
    _has_ipts = "IPTS" in rs_emgfile
    _has_mupulses = "MUPULSES" in rs_emgfile
    # "EMG_LENGTH" no need to check
    _has_binary_mus_firing = "BINARY_MUS_FIRING" in rs_emgfile
    _has_accuracy = "ACCURACY" in rs_emgfile

    # Verify which NON-STANDARD keys are present
    _has_reference_mupulses = "REFERENCE_MUPULSES" in rs_emgfile
    _has_roa = "ROA_WITH_REFERENCE_MUPULSES" in rs_emgfile

    # Identify the area of interest
    if isinstance(area, list) and len(area) == 2:
        start_ = area[0]
        end_ = area[1]
    else:
        # Visualise and select the area to resize
        title = (
            "Select the start/end area to resize by hovering the mouse"
            "\nand pressing the 'a'-key. Wrong points can be removed with "
            "the \n'd' -key. When ready, press enter."
        )
        points = showselect(
            emgfile=rs_emgfile,
            how=how,
            refsig_channel=refsig_channel,
            title=title,
            titlesize=10,
        )
        start_, end_ = points[0], points[1]

    # Force boundaries dtype
    start_ = int(start_)
    end_ = int(end_)

    # Double check that start_, end_ are within the real range.
    if start_ < 0:
        start_ = 0

    if _has_raw_signal is True:
        if end_ > rs_emgfile["RAW_SIGNAL"].shape[0]:
            end_ = rs_emgfile["RAW_SIGNAL"].shape[0]
    elif _has_ref_signal is True:
        if end_ > rs_emgfile["REF_SIGNAL"].shape[0]:
            end_ = rs_emgfile["REF_SIGNAL"].shape[0]
    else:
        raise KeyError(
            "No RAW_SIGNAL or REF_SIGNAL is present in the emgfile."
        )

    # Resize STANDARD dataframes and identify the first value of the
    # index to resize the mupulses. Then, reset the index.
    first_idx = 0

    # Raw signal
    if _has_raw_signal is True:
        rs_emgfile["RAW_SIGNAL"] = rs_emgfile["RAW_SIGNAL"].iloc[start_:end_]
        first_idx = np.int64(rs_emgfile["RAW_SIGNAL"].index[0])
        rs_emgfile["RAW_SIGNAL"] = rs_emgfile["RAW_SIGNAL"].reset_index(
            drop=True,
        )

        # EMG length
        rs_emgfile["EMG_LENGTH"] = int(rs_emgfile["RAW_SIGNAL"].shape[0])

    # Ref signal
    if _has_ref_signal is True:
        rs_emgfile["REF_SIGNAL"] = rs_emgfile["REF_SIGNAL"].iloc[
            start_:end_
        ].reset_index(drop=True)

    # IPTS
    if _has_ipts is True:
        rs_emgfile["IPTS"] = rs_emgfile["IPTS"].iloc[
            start_:end_
        ].reset_index(drop=True)

    # Binary MU firings
    if _has_binary_mus_firing is True:
        rs_emgfile["BINARY_MUS_FIRING"] = rs_emgfile["BINARY_MUS_FIRING"].iloc[
            start_:end_
        ].reset_index(drop=True)

    # MUPULSES, list of arrays
    if _has_mupulses is True:
        # If MUs are present, NUMBER_OF_MUS must be set.
        n_mus = rs_emgfile.get("NUMBER_OF_MUS", None)
        if n_mus is None:
            rs_emgfile["NUMBER_OF_MUS"] = int(len(rs_emgfile["MUPULSES"]))
            n_mus = rs_emgfile["NUMBER_OF_MUS"]
        # Do the rest only if any MU is present
        if n_mus > 0:
            for mu in range(n_mus):
                # Mask the array based on a filter and return the values in
                # an array.
                rs_emgfile["MUPULSES"][mu] = (
                    rs_emgfile["MUPULSES"][mu][
                        (rs_emgfile["MUPULSES"][mu] >= start_)
                        & (rs_emgfile["MUPULSES"][mu] < end_)
                    ] - first_idx
                )

    # REFERENCE MUPULSES, list of arrays
    if _has_reference_mupulses is True:
        # We assume that NUMBER_OF_MUS is already managed, at least by resizing
        # MUPULSES. Do the rest only if any MU is present.
        n_mus = rs_emgfile.get("NUMBER_OF_MUS", None)
        if n_mus > 0:
            for mu in range(n_mus):
                rs_emgfile["REFERENCE_MUPULSES"][mu] = (
                    rs_emgfile["REFERENCE_MUPULSES"][mu][
                        (rs_emgfile["REFERENCE_MUPULSES"][mu] >= start_)
                        & (rs_emgfile["REFERENCE_MUPULSES"][mu] < end_)
                    ] - first_idx
                )

    # Compute SIL or leave original ACCURACY
    if accuracy == "recalculate":
        if _has_accuracy is True and rs_emgfile.get("NUMBER_OF_MUS", 0) > 0:
            if _has_ipts is False:
                raise ValueError(
                    "Impossible to calculate ACCURACY (SIL). IPTS not "
                    "found. If IPTS is not present or empty, set "
                    "accuracy='maintain'"
                )
            if not rs_emgfile["IPTS"].empty:
                # Calculate SIL
                for mu in range(rs_emgfile["NUMBER_OF_MUS"]):
                    res = compute_sil(
                        ipts=rs_emgfile["IPTS"][mu],
                        mupulses=rs_emgfile["MUPULSES"][mu],
                        compute_on_peaks_only=compute_on_peaks_only,
                        ignore_negative_ipts=ignore_negative_ipts,
                    )  # TODO ignore_negative_ipts deprecated => remove
                    rs_emgfile["ACCURACY"].iloc[mu] = res

    elif accuracy != "maintain":
        raise ValueError(
            "Accuracy can only be 'recalculate' or 'maintain'."
            f"{accuracy} was passed instead."
        )

    # Compute ROA or leave original
    if roa_with_reference_mupulses == "recalculate":
        if _has_roa is True and rs_emgfile.get("NUMBER_OF_MUS", 0) > 0:
            if _has_reference_mupulses is False:
                raise ValueError(
                    "Impossible to calculate ROA. REFERENCE_MUPULSES not "
                    "found. If REFERENCE_MUPULSES is not present or empty, "
                    "set roa_with_reference_mupulses='maintain'"
                )
            if len(rs_emgfile["REFERENCE_MUPULSES"]) > 0:
                # Calculate ROA
                for mu in range(rs_emgfile["NUMBER_OF_MUS"]):
                    res = compute_pulses_agreement_rate(
                        estimated_pulses=rs_emgfile["MUPULSES"][mu],
                        reference_pulses=rs_emgfile["REFERENCE_MUPULSES"][mu],
                        method="dice_coefficient",
                    )
                    rs_emgfile["ROA_WITH_REFERENCE_MUPULSES"].iloc[mu] = res

    elif roa_with_reference_mupulses != "maintain":
        raise ValueError(
            "roa_with_reference_mupulses can only be 'recalculate' or "
            f"'maintain'. {accuracy} was passed instead."
        )

    # Custom dataframes
    if custom_dataframes is not None:
        if not isinstance(custom_dataframes, (list, tuple)):
            raise TypeError(
                "custom_dataframes must be a list (or tuple) of emgfile keys."
            )
        for k in custom_dataframes:
            if not isinstance(rs_emgfile[k], pd.DataFrame):
                raise TypeError(
                    f"custom_dataframes contains '{k}', but emgfile['{k}'] "
                    "is not a pandas DataFrame."
                )
            rs_emgfile[k] = rs_emgfile[k].iloc[start_:end_].reset_index(
                drop=True,
            )

    return standardise_emgfile_dtypes(rs_emgfile), start_, end_


def select_bad_channels(emgfile, manual_offset=0):
    """
    Select noisy channels via visual inspection.

    This function opens a modal graphical dialog that allows the user to
    visually inspect stacked EMG channels and mark noisy or unwanted
    channels. Channel selection is performed interactively; the calling
    code is blocked until the dialog is closed.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    manual_offset : int or float, default 0
        This parameter sets the scaling of the channels. If 0 (default), the
        channels' amplitude is scaled automatically to fit the plotting window.
        If > 0, the channels will be scaled based on the specified value.

    Returns
    -------
    edited_emgfile : dict or None
        The EMG file dictionary with an updated ``"GOOD_CHANNELS"`` entry
        (mapping channel indices as strings to booleans) if the user
        confirms the selection.
        Returns ``None`` if the dialog is cancelled.

    Examples
    --------
    >>> import openhdemg.library as emg
    >>> emgfile = emg.emg_from_samplefile()
    >>> edited_emgfile = emg.select_bad_channels(emgfile)
    >>> if edited_emgfile is not None:
    ...     print(edited_emgfile["GOOD_CHANNELS"])
    >>> else:
    ...     print("Selection cancelled by the user")
    """

    edited_emgfile = run_manual_emgchannels_selection_dialog(
        emgfile=emgfile,
        manual_offset=manual_offset,
    )

    return edited_emgfile


class EMGFileSectionsIterator:
    """
    An iterator for splitting a file into sections and performing actions.

    This iterator can be used to split the emgfile (or emg_refsig file) in
    multiple sections, to apply specific funtions to each of these sections
    and to gather their results.

    This class has a number of methods that help in the splitting process,
    in the iteration of the various sections, and in merging the results.

    Parameters
    ----------
    file : dict
        The dictionary containing the emgfile (or emg_refsig file).

    Attributes
    ----------
    file : dict
        The dictionary containing the file to split and iterate.
    file_length : int
        The file duration in samples.
    split_points : list of int
        A list of sample indices where the file should be split into sections.
    sections : list
        A list of sections of the file, created based on split_points.
    results : list
        A list to store the results of operations applied to each section of
        the file.

    Methods
    -------
    set_split_points_by_showselect()
        Manually set the points used to split the emgfile.
    set_split_points_by_equal_spacing()
        Set the points used to split the emgfile into equal sections.
    set_split_points_by_time()
        Set the points used to split the emgfile based on a fixed time window.
    set_split_points_by_samples()
        Set the points used to split the emgfile based on a samples window.
    set_split_points_by_list()
        Set the points used to split the emgfile based on a provided list of
        sample indices.
    split()
        Splits the file into sections using the set split points.
    iterate()
        Apply a collection of functions to the split sections, each with its
        own arguments.
    merge_dataframes()
        Merge a list of result DataFrames using the specified method.
    """

    def __init__(self, file):
        # Initializes the iterator for an emgfile.

        self.file = file
        self.split_points = []
        self.sections = []
        self.results = []
        self.file_length = 0

        # Get file duration based on wether we have an emgfile or an
        # emg_refsig file.
        if "EMG_LENGTH" in self.file:  # Standard emgfile
            self.file_length = self.file["EMG_LENGTH"]
        elif "RAW_SIGNAL" in self.file:  # Fallback
            self.file_length = self.file["RAW_SIGNAL"].shape[0]
        elif "REF_SIGNAL" in self.file:  # Standard emg_refsig
            self.file_length = self.file["REF_SIGNAL"].shape[0]
        else:
            raise ValueError(
                "Impossible to determine file length. None of EMG_LENGTH, " +
                "RAW_SIGNAL and REF_SIGNAL are available in the file."
            )
        self.file_length = int(self.file_length)

    def set_split_points_by_showselect(
        self,
        how="ref_signal",
        refsig_channel=0,
        title="",
        titlesize=10,
        nclic=-1,
    ):
        """
        Manually set the points used to split the emgfile.

        Calls the emg.showselect() function to manually select the split points
        based on the visualisation of the reference signal or of the EMG
        signal amplitude.

        Users can move the mouse to track coordinates and press:

        - "A" or "a" to add a point at the current cursor location
        - "D" or "d" to delete the last selected point
        - "Enter" to confirm the selection and close the window

        Sections are cut starting from the first point and then on the
        consecutive points.

        Parameters
        ----------
        how : str {"ref_signal", "mean_emg"}, default "ref_signal"
            What to display in the figure used to visually select the area to
            resize.

            ``ref_signal``
                Visualise the reference signal to select the area to resize.

            ``mean_emg``
                Visualise the mean EMG signal to select the area to resize.
        refsig_channel : int or str, Default 0
            The name of the reference signal channel (column) to plot.
        title : str
            The title of the plot. It is optional but strongly recommended.
            It should describe the task to do. A default title is provided when
            title="".
        titlesize : int, default 12
            The font size of the title.
        nclic: int, default -1
            The number of clics to be collected. If nclic < 1, all the clicks
            are collected.

        Returns
        -------
        None
            Stores the split points in `self.split_points`.

        Raises
        ------
        ValueError
            When the user clicked a wrong number of inputs in the GUI.

        Examples
        --------
        Manually set the points to resize the file by visualising the reference
        signal.

        >>> import openhdemg.library as emg
        >>> emgfile = emg.emg_from_samplefile()
        >>> iterator = emg.EMGFileSectionsIterator(file=emgfile)
        >>> iterator.set_split_points_by_showselect(how="ref_signal")
        >>> split_points = iterator.split_points
        >>> split_points
        [0, 6562, 19552, 41546, 55273, 62802]

        Manually set the points to resize the file by visualising the mean
        EMG signal amplitude.

        >>> import openhdemg.library as emg
        >>> emgfile = emg.emg_from_samplefile()
        >>> iterator = emg.EMGFileSectionsIterator(file=emgfile)
        >>> iterator.set_split_points_by_showselect(how="mean_emg")
        >>> split_points = iterator.split_points
        >>> split_points
        [5381, 23094, 38889, 50107]
        """

        # Fallback title
        if len(title) == 0:
            title = (
                "Select the points by hovering the mouse and pressing the" +
                "'a'-key.\nWrong points can be removed with the 'd' -key." +
                "\nWhen ready, press enter."
            )

        split_points = showselect(
            emgfile=self.file,
            how=how,
            refsig_channel=refsig_channel,
            title=title,
            titlesize=titlesize,
            nclic=nclic,
        )

        # Double check that split_points are within the real range.
        points_below = [x for x in split_points if x < 0]
        if len(points_below) > 1:
            raise ValueError(
                "More than 1 point has been selected below 0."
            )
        elif len(points_below) == 1:
            if split_points[0] < 0:
                split_points[0] = 0
            else:
                raise ValueError(
                    "There are points below 0 different from the firt " +
                    "element of the list, check points beeing sorted."
                )

        points_above = [x for x in split_points if x > self.file_length]
        if len(points_above) > 1:
            raise ValueError(
                "More than 1 point has been selected after the end of the " +
                "signal."
            )
        elif len(points_above) == 1:
            if split_points[-1] > self.file_length:
                split_points[-1] = self.file_length
            else:
                raise ValueError(
                    "There are points after the end of the file different " +
                    "from the firt element of the list, check points beeing " +
                    "sorted."
                )

        self.split_points = split_points

    def set_split_points_by_equal_spacing(self, n_sections):
        """
        Set the points used to split the emgfile into equal sections.

        All the sections will have approximately the same length (length
        rounding may apply), which is calculated based on n_sections.

        Parameters
        ----------
        n_sections : int
            The number of sections to divide the emgfile into.

        Returns
        -------
        None
            Stores the split points in `self.split_points`.

        Examples
        --------
        Divide the file in 3 sections of the same length.

        >>> import openhdemg.library as emg
        >>> emgfile = emg.emg_from_samplefile()
        >>> iterator = EMGFileSectionsIterator(file=emgfile)
        >>> iterator.set_split_points_by_equal_spacing(n_sections=3)
        >>> split_points = iterator.split_points
        >>> split_points
        [0, 22186, 44373, 66560]
        """

        space = self.file_length
        self.split_points = list(
            np.linspace(0, space, n_sections + 1, dtype=int)
        )

    def set_split_points_by_time(self, time_window, drop_shorter=False):
        """
        Set the points used to split the emgfile based on a fixed time window.


        Parameters
        ----------
        time_window : float
            The duration of each section in seconds.
        drop_shorter : bool, default False
            If True, the last section is discarded if it is shorter than
            `time_window`. If False, the last section will include the
            remaining samples even if it is shorter than `time_window`.

        Returns
        -------
        None
            Stores the split points in `self.split_points`.

        Examples
        --------
        Divide the file into consecutive 9-second sections, with any remaining
        data forming a final shorter section.

        >>> import openhdemg.library as emg
        >>> emgfile = emg.emg_from_samplefile()
        >>> iterator = emg.EMGFileSectionsIterator(file=emgfile)
        >>> iterator.set_split_points_by_time(
        ...     time_window=9,
        ...     drop_shorter=False,
        ... )
        >>> split_points = iterator.split_points
        >>> split_points
        [0, 18432, 36864, 55296, 66560]

        Divide the file into consecutive 9-second sections, discarding any
        remaining data if it is shorter than the specified duration.

        >>> import openhdemg.library as emg
        >>> emgfile = emg.emg_from_samplefile()
        >>> iterator = emg.EMGFileSectionsIterator(file=emgfile)
        >>> iterator.set_split_points_by_time(
        ...     time_window=9,
        ...     drop_shorter=True,
        ... )
        >>> split_points = iterator.split_points
        >>> split_points
        [0, 18432, 36864, 55296]
        """

        fsamp = self.file["FSAMP"]
        space = self.file_length

        step = int(round(time_window * fsamp))
        self.split_points = list(range(0, space + 1, step))

        # Append the last point if it's missing and drop_shorter is False
        if self.split_points[-1] != space:
            if not drop_shorter:
                self.split_points.append(space)

    def set_split_points_by_samples(self, samples_window, drop_shorter=False):
        """
        Set the points used to split the emgfile based on a samples window.

        Parameters
        ----------
        samples_window : int
            The duration of each section in samples.
        drop_shorter : bool, default False
            If True, the last section is discarded if it is shorter than
            `samples_window`. If False, the last section will include the
            remaining samples even if it is shorter than `samples_window`.

        Returns
        -------
        None
            Stores the split points in `self.split_points`.

        Examples
        --------
        Divide the file into consecutive 9-second sections, with any remaining
        data forming a final shorter section.

        >>> import openhdemg.library as emg
        >>> emgfile = emg.emg_from_samplefile()
        >>> iterator = emg.EMGFileSectionsIterator(file=emgfile)
        >>> iterator.set_split_points_by_samples(
        ...     samples_window=10000,
        ...     drop_shorter=False,
        ... )
        >>> split_points = iterator.split_points
        >>> split_points
        [0, 10000, 20000, 30000, 40000, 50000, 60000, 66560]

        Divide the file into consecutive 9-second sections, discarding any
        remaining data if it is shorter than the specified duration.

        >>> import openhdemg.library as emg
        >>> emgfile = emg.emg_from_samplefile()
        >>> iterator = emg.EMGFileSectionsIterator(file=emgfile)
        >>> iterator.set_split_points_by_samples(
        ...     samples_window=10000,
        ...     drop_shorter=True,
        ... )
        >>> split_points = iterator.split_points
        >>> split_points
        [0, 10000, 20000, 30000, 40000, 50000, 60000]
        """

        space = self.file_length
        step = samples_window
        self.split_points = list(range(0, space + 1, step))

        # Append the last point if it's missing and drop_shorter is False
        if self.split_points[-1] != space:
            if not drop_shorter:
                self.split_points.append(space)

    def set_split_points_by_list(self, split_points):
        """
        Set the points used to split the emgfile based on a provided list of
        sample indices.

        Parameters
        ----------
        split_points : list of int
            A list containing the sample indices at which to split the emgfile.
            These indices should correspond to the points where the data will
            be divided into sections.

        Returns
        -------
        None
            Stores the split points in `self.split_points`.

        Examples
        --------
        >>> import openhdemg.library as emg
        >>> emgfile = emg.emg_from_samplefile()
        >>> iterator = emg.EMGFileSectionsIterator(file=emgfile)
        >>> iterator.set_split_points_by_list(split_points=[0, 18432, 36864])
        >>> split_points = iterator.split_points
        >>> split_points
        [0, 18432, 36864]
        """

        self.split_points = split_points

    def split(
        self,
        accuracy="recalculate",
        compute_on_peaks_only=True,
        roa_with_reference_mupulses="recalculate",
        custom_dataframes=None,
        ignore_negative_ipts=None,
    ):
        """
        Splits the file into sections using the set split points.

        Parameters
        ----------
        accuracy : str {"recalculate", "maintain"}, default "recalculate"

            ``recalculate``
                The Silhouette score is computed in the new resized file. This
                can be done only if IPTS is present.

            ``maintain``
                The original accuracy measure already contained in the emgfile
                is returned without any computation.
        compute_on_peaks_only : bool, default True
            If True, the silhouette (SIL) score is computed using **only the
            ipts peaks**, rather than all values in the source signal. This can
            improve accuracy estimation by comparing MU spikes only against
            other candidate spikes, ignoring baseline or negative ipts values.
            If False, the noise cluster is defined as all samples not selected
            as MU spikes.
        roa_with_reference_mupulses : str {"recalculate", "maintain"}, default "recalculate"
            Whether to re-calculate the rate of agreement (ROA) between
            "MUPULSES" and "REFERENCE_MUPULSES".

            ``recalculate``
                The ROA is computed in the new resized file. This can
                be done only if both "MUPULSES" and "REFERENCE_MUPULSES" are
                present.

            ``maintain``
                The original ROA measure already contained in the emgfile is
                returned without any computation.
        custom_dataframes : list or None, default None
            A list of strings pointing to the additional dataframes to resize.
            The strings should match the emgfile keys associated to the
            pd.DataFrames.
        ignore_negative_ipts : None
            This parameter is deprecated and will be removed in future
            releases. Please transform the 'ipts' before if needed. To
            replicate the behaviour of 'ignore_negative_ipts=True' you can use
            'ipts * np.abs(ipts)'.

        Returns
        -------
        None
            Stores the split sections in `self.sections`.

        Examples
        --------
        >>> import openhdemg.library as emg
        >>> emgfile = emg.emg_from_samplefile()
        >>> iterator = emg.EMGFileSectionsIterator(file=emgfile)
        >>> iterator.set_split_points_by_equal_spacing(n_sections=4)
        >>> iterator.split()
        >>> sections = iterator.sections
        >>> len(sections)
        4
        """

        self.sections = []
        for start, end in zip(self.split_points[:-1], self.split_points[1:]):
            rs_emgfile, _, _ = resize_emgfile(
                self.file, area=[start, end],
                accuracy=accuracy,
                compute_on_peaks_only=compute_on_peaks_only,
                roa_with_reference_mupulses=roa_with_reference_mupulses,
                custom_dataframes=custom_dataframes,
                ignore_negative_ipts=ignore_negative_ipts,  # TODO deprecated, remove later
            )
            self.sections.append(rs_emgfile)

    def iterate(self, funcs=[], args_list=[[]], kwargs_list=[{}], **kwargs):
        """
        Apply a collection of functions to the split sections, each with its
        own arguments.

        Parameters
        ----------
        funcs : list of callables
            A list of functions to apply to each section. If multiple functions
            are provided, their count must match the number of sections. If
            only one function is given, it will be applied to all sections.
            IMPORTANT! Each function must take `file` as the first parameter.
        args_list : list of lists
            A list where each element is a list of positional arguments to be
            passed to the corresponding function in `funcs`. Must have the same
            length as `funcs`.
        kwargs_list : list of dicts, optional
            A list where each element is a dictionary of keyword arguments to
            be passed to the corresponding function in `funcs`. Must have the
            same length as `funcs`.
        **kwargs
            Additional keyword arguments that are passed to all functions in
            `funcs`. If `funcs` contains only 1 function, **kwargs can be used
            instead of kwargs_list for simpler syntax.

        Returns
        -------
        None
            Stores the results in `self.results`, where each function's output
            is collected.

        Examples
        --------
        Split the file in 3 sections and apply a custom function to each
        section to count the number of firings in each MU. Then visualise the
        results for the first section.

        >>> import openhdemg.library as emg
        >>> import pandas as pd
        >>> def count_firings(emgfile):
        ...     res = [len(mu_firings) for mu_firings in emgfile["MUPULSES"]]
        ...     return pd.DataFrame(res)
        >>> emgfile = emg.emg_from_samplefile()
        >>> iterator = emg.EMGFileSectionsIterator(file=emgfile)
        >>> iterator.set_split_points_by_equal_spacing(n_sections=3)
        >>> iterator.split()
        >>> iterator.iterate(funcs=[count_firings])
        >>> results = iterator.results
        >>> results[0]
            0
        0  48
        1  43
        2  63
        3  94
        4  95

        Split the file in 3 sections and calculate the discharge rate of each
        MU over the first 20 discharges.

        >>> import openhdemg.library as emg
        >>> emgfile = emg.emg_from_samplefile()
        >>> iterator = emg.EMGFileSectionsIterator(file=emgfile)
        >>> iterator.set_split_points_by_equal_spacing(n_sections=3)
        >>> iterator.split()
        >>> iterator.iterate(
        ...     funcs=[emg.compute_dr],
        ...     event_="rec",
        ...     n_firings_RecDerec=20,
        ... )
        >>> results = iterator.results
        >>> results[0]
             DR_rec     DR_all
        0  7.468962   7.714276
        1  7.091045   7.390155
        2  7.673784   8.583193
        3  9.004878  11.042002
        4  9.705901  11.202489
        """

        # Extensive input checking to help using the iterate function.
        if not isinstance(funcs, list):
            raise ValueError("Funcs must be a list")
        if not isinstance(args_list, list):
            raise ValueError("args_list must be a list")
        if not isinstance(kwargs_list, list):
            raise ValueError("kwargs_list must be a list")

        # Manage multiple functions
        if len(funcs) > 1:
            if len(funcs) != len(self.sections):
                raise ValueError(
                    "funcs must be a list containing 1 function to be " +
                    "applied to all the sections or 1 function for each " +
                    "section."
                )
            if len(args_list) > 0:
                if not isinstance(args_list[0], list):
                    raise ValueError(
                        "args_list must be a list containing 1 list of " +
                        "arguments for each function."
                    )
                if len(args_list) != len(self.sections):
                    raise ValueError(
                        "args_list must be a list containing 1 list of " +
                        "arguments for each function."
                    )
            if len(kwargs_list) > 0:
                if not isinstance(kwargs_list[0], dict):
                    raise ValueError(
                        "kwargs_list must be a list containing 1 dict of " +
                        "keyword arguments for each function."
                    )
                if len(kwargs_list) != len(self.sections):
                    raise ValueError(
                        "kwargs_list must be a list containing 1 dict of " +
                        "keyword arguments for each function."
                    )

        elif len(funcs) == 1:
            if len(args_list) == 1:
                if not isinstance(args_list[0], list):
                    raise ValueError(
                        "args_list must be a list containing 1 list of " +
                        "arguments for each function."
                    )
            elif len(args_list) > 1:
                raise ValueError(
                    "args_list must be a list containing 1 list of " +
                    "arguments for each function."
                )

            if len(kwargs_list) == 1:
                if not isinstance(kwargs_list[0], dict):
                    raise ValueError(
                        "kwargs_list must be a list containing 1 dict of " +
                        "keyword arguments for each function."
                    )
            elif len(kwargs_list) > 1:
                raise ValueError(
                    "kwargs_list must be a list containing 1 dict of " +
                    "keyword arguments for each function."
                )

        else:
            raise ValueError("No function provided to iterate")

        # Proagate single function to fit the number of sections
        if len(funcs) == 1 and len(self.sections) > 1:
            funcs = [funcs[0] for _ in self.sections]
            args_list = [args_list[0] for _ in self.sections]
            kwargs_list = [kwargs_list[0] for _ in self.sections]

        # Calculate the results for each section
        for idx, section in enumerate(self.sections):
            func = funcs[idx]
            func_args = args_list[idx]
            func_kwargs = kwargs_list[idx]
            combined_kwargs = {**func_kwargs, **kwargs}
            result = func(section, *func_args, **combined_kwargs)
            self.results.append(result)

    def merge_dataframes(self, method="long", fillna=None, agg_func=None):
        """
        Merge a list of result DataFrames using the specified method.

        Parameters
        ----------
        method : str, default "long"
            The merging method. When using built-in methods (except for
            `custom`), all DataFrames must have the same structure (i.e.,
            aligned columns and index).

            ``average``
                Computes the mean across all DataFrames.

            ``median``
                Computes the median across all DataFrames.

            ``sum``
                Computes the sum across all DataFrames.

            ``min``
                Takes the minimum value across all DataFrames.

            ``max``
                Takes the maximum value across all DataFrames.

            ``std``
                Computes the standard deviation across all DataFrames.

            ``cv``
                Computes the coefficient of variation (CV = std / mean).

            ``long``
                Stacks all DataFrames with an additional 'source_idx' column.

            ``custom``
                Uses a user-defined aggregation function provided via
                `agg_func`.
        fillna : float or None
            If specified, fills missing values (NaN) with this value before
            merging.
        agg_func : callable or None
            A custom aggregation function to apply when method="custom". The
            function should take a list of DataFrames and return a single
            DataFrame.

        Returns
        -------
        merged_df : pd.DataFrame
            The merged DataFrame.

        Raises
        ------
        ValueError
            If `self.results` is empty or contains non-DataFrame elements;
            or, `method` is unknown; or `agg_func` is missing when
            method="custom".

        Examples
        --------
        Merge all the results in a long format DataFrame. Best for statistical
        analyses.

        >>> import openhdemg.library as emg
        >>> emgfile = emg.emg_from_samplefile()
        >>> iterator = emg.EMGFileSectionsIterator(file=emgfile)
        >>> iterator.set_split_points_by_equal_spacing(n_sections=3)
        >>> iterator.split()
        >>> iterator.iterate(funcs=[emg.compute_dr], event_="rec")
        >>> merged_results = iterator.merge_dataframes()
        >>> merged_results
            source_idx  original_idx     DR_rec     DR_all
        0            0             0   3.341579   7.714276
        1            0             1   5.701081   7.390155
        2            0             2   5.699017   8.583193
        3            0             3   7.548770  11.042002
        4            0             4   8.344515  11.202489
        5            1             0  10.235710   8.155868
        6            1             1   6.769358   6.758350
        7            1             2   8.193645   8.054868
        8            1             3  10.952495  11.151536
        9            1             4  11.012249  10.691432
        10           2             0   6.430406   6.899233
        11           2             1   6.714442   6.274404
        12           2             2   7.057244   6.881602
        13           2             3  10.577538   9.578987
        14           2             4   9.708064   9.562182

        Apply a custom function to each section to count the number of firings
        in each MU, then get the mean and STD values across the 3 sections
        (just for didactical purposes).

        >>> import openhdemg.library as emg
        >>> import pandas as pd
        >>> def count_firings(emgfile):
        ...     res = [len(mu_firings) for mu_firings in emgfile["MUPULSES"]]
        ...     return pd.DataFrame(res)
        >>> emgfile = emg.emg_from_samplefile()
        >>> iterator = emg.EMGFileSectionsIterator(file=emgfile)
        >>> iterator.set_split_points_by_equal_spacing(n_sections=3)
        >>> iterator.split()
        >>> iterator.iterate(funcs=[count_firings])
        >>> mean_values = iterator.merge_dataframes(
        ...     method="average",
        ...     fillna=0,
        ... )
        >>> std_values = iterator.merge_dataframes(
        ...     method="std",
        ...     fillna=0,
        ... )
        >>> mean_values
                   0
        0  45.666667
        1  51.333333
        2  65.666667
        3  97.666667
        4  97.333333
        >>> std_values
                   0
        0   4.932883
        1  18.009257
        2  20.132892
        3  20.744477
        4  16.623277

        Apply a custom method by providing an external aggregation function
        which finds the maximum value at each position and the index of the
        DataFrame containing it.

        >>> import openhdemg.library as emg
        >>> import pandas as pd
        >>> def max_with_source(results_dataframes):
        ...     stacked = pd.concat(
        ...         results_dataframes, keys=range(len(results_dataframes))
        ...     )
        ...     max_values = stacked.groupby(level=1).max()
        ...     max_indices = stacked.groupby(level=1).idxmax().iloc[:, 0]
        ...     max_values["source_idx"] = max_indices.map(lambda x: x[0])
        ...     return max_values
        >>> emgfile = emg.emg_from_samplefile()
        >>> iterator = emg.EMGFileSectionsIterator(file=emgfile)
        >>> iterator.set_split_points_by_equal_spacing(n_sections=3)
        >>> iterator.split()
        >>> iterator.iterate(funcs=[emg.compute_dr], event_="rec")
        >>> max_values_with_source = iterator.merge_dataframes(
        ...     method="custom",
        ...     fillna=0,
        ...     agg_func=max_with_source,
        ... )
        >>> max_values_with_source
              DR_rec     DR_all  source_idx
        0  10.235710   8.155868           1
        1   6.769358   7.390155           1
        2   8.193645   8.583193           1
        3  10.952495  11.151536           1
        4  11.012249  11.202489           1
        """

        if not self.results:
            raise ValueError("The list of dataframes is empty.")

        if not all(isinstance(df, pd.DataFrame) for df in self.results):
            raise ValueError(
                "All elements in `self.results` must be pd.DataFrames."
            )

        # Optionally fill NaN values
        if fillna is not None:
            self.results = [df.fillna(fillna) for df in self.results]

        # Stack DataFrames along axis=0 for operations like std and cv
        merged_stack = pd.concat(
            self.results, axis=0, keys=range(len(self.results)),
        )

        if method == "average":
            merged_df = merged_stack.groupby(level=1).mean()

        elif method == "median":
            merged_df = merged_stack.groupby(level=1).median()

        elif method == "sum":
            merged_df = merged_stack.groupby(level=1).sum()

        elif method == "min":
            merged_df = merged_stack.groupby(level=1).min()

        elif method == "max":
            merged_df = merged_stack.groupby(level=1).max()

        elif method == "std":
            merged_df = merged_stack.groupby(level=1).std()

        elif method == "cv":
            mean_df = merged_stack.groupby(level=1).mean()
            std_df = merged_stack.groupby(level=1).std()
            merged_df = std_df / mean_df

        elif method == "long":
            # Preserve original index (often indicating the MU number) by
            # renaming it to 'original_idx', and assign source index to detect
            # from which DataFrame the results come from.
            merged_df = pd.concat(
                [
                    df.reset_index().rename(
                        columns={"index": "original_idx"}
                    ).assign(source_idx=i)
                    for i, df in enumerate(self.results)
                ],
                ignore_index=True
            )

            # Ensure consistent column order
            cols = ["source_idx", "original_idx"] + [
                col for col in merged_df.columns if col not in [
                    "source_idx", "original_idx"
                ]
            ]
            merged_df = merged_df[cols]

        elif method == "custom":
            if agg_func is None:
                raise ValueError(
                    "When using method='custom', `agg_func` must be provided."
                )
            merged_df = agg_func(self.results)

        else:
            raise ValueError(f"Unknown method '{method}'")

        return merged_df


def compute_idr(emgfile):
    """
    Compute the IDR.

    This function computes the instantaneous discharge rate (IDR) from the
    MUPULSES.
    The IDR is very useful for plotting and visualisation of the MUs behaviour.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.

    Returns
    -------
    idr : dict
        A dict containing a pd.DataFrame for each MU (keys are integers).
        Accessing the key, we have a pd.DataFrame containing:

        - mupulses: firing sample.
        - diff_mupulses: delta between consecutive firing samples.
        - timesec: delta between consecutive firing samples in seconds.
        - idr: instantaneous discharge rate.

    Examples
    --------
    Load the EMG file, compute IDR and access the results for the first MU.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> idr = emg.compute_idr(emgfile=emgfile)
    >>> munumber = 0
    >>> idr[munumber]
        mupulses  diff_mupulses    timesec       idr
    0        9221            NaN   4.502441       NaN
    1        9580          359.0   4.677734  5.704735
    2        9973          393.0   4.869629  5.211196
    3       10304          331.0   5.031250  6.187311
    4       10617          313.0   5.184082  6.543131
    ..        ...            ...        ...       ...
    149     54521          395.0  26.621582  5.184810
    150     54838          317.0  26.776367  6.460568
    151     55417          579.0  27.059082  3.537133
    152     55830          413.0  27.260742  4.958838
    153     56203          373.0  27.442871  5.490617
    """

    # Compute the instantaneous discharge rate (IDR) from the MUPULSES
    if isinstance(emgfile["MUPULSES"], list):
        # Empty dict to fill with dataframes containing the MUPULSES
        # information
        idr = {x: np.nan for x in range(emgfile["NUMBER_OF_MUS"])}

        for mu in range(emgfile["NUMBER_OF_MUS"]):
            # Manage the exception of a single MU and add MUPULSES in column 0
            df = pd.DataFrame(
                emgfile["MUPULSES"][mu]
                if emgfile["NUMBER_OF_MUS"] > 1
                else np.transpose(np.array(emgfile["MUPULSES"]))
            )

            # Calculate difference in MUPULSES and add it in column 1
            df[1] = df[0].diff()
            # Calculate time in seconds and add it in column 2
            df[2] = df[0] / emgfile["FSAMP"]
            # Calculate the idr and add it in column 3
            df[3] = emgfile["FSAMP"] / df[1]

            df = df.rename(
                columns={
                    0: "mupulses",
                    1: "diff_mupulses",
                    2: "timesec",
                    3: "idr",
                },
            )

            # Add the idr to the idr dict
            idr[mu] = df

        return idr

    else:
        raise Exception(
            "MUPULSES is probably absent or it is not contained in a list"
        )


def delete_mus(
    emgfile, munumber, if_single_mu="ignore", delete_delsys_muaps=True,
):
    """
    Delete unwanted MUs.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    munumber : int, list of int
        The MUs to remove. If a single MU has to be removed, this should be an
        int (number of the MU).
        If multiple MUs have to be removed, a list of int should be passed.
        An unpacked (*) range can also be passed as munumber=[*range(0, 5)].
        munumber is expected to be with base 0 (i.e., the first MU in the file
        is the number 0).
    if_single_mu : str {"ignore", "remove"}, default "ignore"
        A string indicating how to behave in case of a file with a single MU.

        ``ignore``
            Ignore the process and return the original emgfile. (Default)

        ``remove``
            Remove the MU and return the emgfile without the MU.
            This should allow full compatibility with the use of this file
            in following processing (i.e., save/load and analyse).
    delete_delsys_muaps : Bool, default True
        If true, deletes also the associated MUAPs computed by the Delsys
        software stored in emgfile["EXTRAS"].

    Returns
    -------
    emgfile : dict
        The dictionary containing the emgfile without the unwanted MUs.

    Examples
    --------
    Delete MUs 1,4,5 from the emgfile.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> emgfile = emg.delete_mus(emgfile=emgfile, munumber=[1,4,5])
    """

    # Check for "NUMBER_OF_MUS"
    if emgfile.get("NUMBER_OF_MUS", None) is None:
        raise ValueError(
            "The emgile does not contain the key 'NUMBER_OF_MUS' or this is"
            "set to None."
        )

    # Check if any MU
    if emgfile["NUMBER_OF_MUS"] == 0:
        warnings.warn("The file does not contain any MU.")
        return emgfile

    # TODO uniform this behaviour in the future
    # Check how to behave in case of a single MU
    if if_single_mu == "ignore":
        # Check how many MUs we have, if we only have 1 MU, the entire file
        # should be deleted instead.
        if emgfile["NUMBER_OF_MUS"] == 1:
            warnings.warn(
                "There is only 1 MU in the file, and it has not been removed. "
                "You can change this behaviour with if_single_mu='remove'"
            )
            return emgfile

    elif if_single_mu == "remove":
        pass

    else:
        raise ValueError(
            "if_single_mu must be one of 'ignore' or 'remove', "
            f"{if_single_mu} was passed instead"
        )

    # Create the object to store the new emgfile without the specified MUs.
    del_emgfile = copy.deepcopy(emgfile)
    """
    Need to be changed: ==>
    emgfile =   {
        "SOURCE" : SOURCE,
        "RAW_SIGNAL" : RAW_SIGNAL,
        "REF_SIGNAL" : REF_SIGNAL,

        ==> "ACCURACY" : ACCURACY
        ==> "IPTS" : IPTS,
        ==> "MUPULSES" : MUPULSES,

        "FSAMP" : FSAMP,
        "IED" : IED,
        "EMG_LENGTH" : EMG_LENGTH,

        ==> "NUMBER_OF_MUS" : NUMBER_OF_MUS,
        ==> "BINARY_MUS_FIRING" : BINARY_MUS_FIRING,

        ==> "EXTRAS" : EXTRAS but only for DELSYS file

        ==> "MU_LABELS" : optional labels for the MUs
        ==> "REFERENCE_MUPULSES" : optional set of reference MUPULSES
        ==> "ROA_WITH_REFERENCE_MUPULSES" : optional ROA dataframe
    }
    """

    # Convert munumber to a list of int
    if isinstance(munumber, int):
        munumber = [munumber]
    elif not isinstance(munumber, list):
        raise TypeError(
            "While calling the 'delete_mus' function, you should pass an "
            "integer or a list to 'munumber= '."
        )

    # Make sure that only ordered unique values are contained
    munumber = sorted(set(int(x) for x in munumber))

    # Drop ACCURACY values and reset the index
    if del_emgfile.get("ACCURACY", None) is not None:
        del_emgfile["ACCURACY"] = del_emgfile["ACCURACY"].drop(munumber)
        del_emgfile["ACCURACY"] = del_emgfile["ACCURACY"].reset_index(
            drop=True
        )

    # Drop ROA_WITH_REFERENCE_MUPULSES values and reset the index
    _this_str = "ROA_WITH_REFERENCE_MUPULSES"
    if del_emgfile.get(_this_str, None) is not None:
        del_emgfile[_this_str] = del_emgfile[_this_str].drop(munumber)
        del_emgfile[_this_str] = del_emgfile[_this_str].reset_index(
            drop=True
        )

    # Drop IPTS by columns and rename the columns
    if del_emgfile.get("IPTS", None) is not None:
        del_emgfile["IPTS"] = del_emgfile["IPTS"].drop(munumber, axis=1)
        del_emgfile["IPTS"].columns = range(del_emgfile["IPTS"].shape[1])

    # Drop BINARY_MUS_FIRING by columns and rename the columns
    if del_emgfile.get("BINARY_MUS_FIRING", None) is not None:
        del_emgfile["BINARY_MUS_FIRING"] = del_emgfile[
            "BINARY_MUS_FIRING"
        ].drop(munumber, axis=1)
        del_emgfile["BINARY_MUS_FIRING"].columns = range(
            del_emgfile["BINARY_MUS_FIRING"].shape[1]
        )

    # Delete all the content in the del_emgfile["MUPULSES"] and append
    # only the MUs that we want to retain (exclude deleted MUs).
    # This is a workaround to directly deleting, for safer implementation.
    if del_emgfile.get("MUPULSES", None) is not None:
        del_emgfile["MUPULSES"] = []
        for mu in range(emgfile["NUMBER_OF_MUS"]):
            if mu not in munumber:
                del_emgfile["MUPULSES"].append(emgfile["MUPULSES"][mu])

    # Delete REFERENCE_MUPULSES as for MUPULSES
    if del_emgfile.get("REFERENCE_MUPULSES", None) is not None:
        del_emgfile["REFERENCE_MUPULSES"] = []
        for mu in range(emgfile["NUMBER_OF_MUS"]):
            if mu not in munumber:
                del_emgfile["REFERENCE_MUPULSES"].append(
                    emgfile["REFERENCE_MUPULSES"][mu]
                )

    # Subrtact the number of deleted MUs to the total number
    del_emgfile["NUMBER_OF_MUS"] = del_emgfile["NUMBER_OF_MUS"] - len(munumber)

    # Update MU labels (optional)
    if del_emgfile.get("MU_LABELS", None) is not None:
        # Convert removal list to strings for comparison
        labels_to_remove = [str(mu) for mu in munumber]
        filtered_values = [
            v for k, v in sorted(
                del_emgfile["MU_LABELS"].items(), key=lambda x: int(x[0])
            )
            if k not in labels_to_remove
        ]
        del_emgfile["MU_LABELS"] = {
            str(i): v for i, v in enumerate(filtered_values)
        }  # Reindex keys from 0

    # Verify if all the MUs have been removed. In that case, restore column
    # names in empty pd.DataFrames.
    if del_emgfile["NUMBER_OF_MUS"] == 0:
        # pd.DataFrame
        if del_emgfile.get("IPTS", None) is not None:
            del_emgfile["IPTS"] = pd.DataFrame(columns=[0])
        if del_emgfile.get("BINARY_MUS_FIRING", None) is not None:
            del_emgfile["BINARY_MUS_FIRING"] = pd.DataFrame(columns=[0])
        if del_emgfile.get("ACCURACY", None) is not None:
            del_emgfile["ACCURACY"] = pd.DataFrame(columns=[0])
        # list of ndarray
        if del_emgfile.get("MUPULSES", None) is not None:
            del_emgfile["MUPULSES"] = []

    if del_emgfile.get("SOURCE", None) is not None:
        if del_emgfile["SOURCE"] == "DELSYS" and delete_delsys_muaps:
            # Remove also DELSYS MUAPs
            data = del_emgfile["EXTRAS"]

            for mu in munumber:
                # Get MU ID
                mu_id = f"MU_{mu}_"
                # Remove all columns with MU ID
                data = data[
                    [col for col in data.columns if not col.startswith(mu_id)]
                ]

            # Rescale the numbers in the remaining column names
            col_list = list(data.columns)
            if len(col_list) % 4 != 0:
                raise ValueError(
                    "Unexpected number of channels in Delsys MUAPS"
                )
            new_col_list = []
            for mu in range(del_emgfile["NUMBER_OF_MUS"]):
                new_col_list.extend(
                    [
                        f"MU_{mu}_CH_0",
                        f"MU_{mu}_CH_1",
                        f"MU_{mu}_CH_2",
                        f"MU_{mu}_CH_3",
                    ]
                )
            data.columns = new_col_list

            del_emgfile["EXTRAS"] = data

    return del_emgfile


def delete_empty_mus(emgfile):
    """
    Delete all the MUs without firings.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.

    Returns
    -------
    emgfile : dict
        The dictionary containing the emgfile without the empty MUs.
    """

    # Check if any MUs
    if emgfile["NUMBER_OF_MUS"] == 0:
        warnings.warn("The file does not contain any MU.")
        return copy.deepcopy(emgfile)

    # Find the index of empty MUs
    ind = []
    for i, mu in enumerate(range(emgfile["NUMBER_OF_MUS"])):
        if len(emgfile["MUPULSES"][mu]) == 0:
            ind.append(i)

    emgfile = delete_mus(emgfile, munumber=ind, if_single_mu="remove")

    return emgfile


def find_duplicates_within(
    emgfile,
    correlation_max_lag=50e-3,
    peak_window_half_width=2.5e-3,
    duplicate_threshold=30,
    which="accuracy",
):
    """
    Find duplicate MUs within the same file based on discharge times.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    correlation_max_lag : float, default 50e-3
        Maximum lag (in seconds) used when computing the cross-correlation
        between MU spike trains. Defines the full search range for possible
        synchronisation peaks. Larger values allow detection of synchrony
        over wider time shifts. This must be < 1.
    peak_window_half_width : float, default 2.5e-3
        Half-width (in seconds) of the window used around the cross-correlation
        peak to compute the duplication sensitivity metric. This window should
        capture the narrow temporal jitter expected for duplicate MUs.
        This must be < 1 and < `correlation_max_lag`.
    duplicate_threshold : float, default 30
        Threshold (in percent) for classifying two MUs as duplicates.
        The sensitivity metric is computed as the sum of the cross-correlation
        values within a ±`peak_window_half_width` window around the
        correlation peak, normalised by the size of the larger spike train.
    which : str {"accuracy", "covisi"}, default "accuracy"
        How to classify the duplicated MUs.

        ``accuracy``
            The MU with the lowest accuracy is considered duplicate. The
            emgfile must already contain the 'ACCURACY' dataframe.

        ``covisi``
            The MU with the highest CoV of interspike interval is is considered
            duplicate.

    Returns
    -------
    duplicates : list of int
        Sorted list of MU indices classified as duplicates and therefore
        recommended for removal.
    duplicates_info : list of dict
        Detailed information about each detected duplicate MU pair.
        Each element of the list is a dictionary describing one MU-MU
        comparison that exceeded the duplication threshold. The dictionary
        contains:

        ``pair`` : tuple of int
            A tuple "(mu1, mu2)" containing the indices of the two MUs
            identified as potential duplicates.

        ``accuracy`` : tuple of float, optional
            Present only when which="accuracy".
            Contains the SIL (accuracy) values of the two units in the same
            order as "pair". The MU with the lowest SIL is considered the
            duplicate.

        ``covisi`` : tuple of float, optional
            Present only when which="covisi".
            Contains the CoV of the interspike interval for the two units, in
            the same order as "pair". The MU with the highest CoV-ISI is
            considered the duplicate.

    See also
    --------
    - remove_duplicates_within : Remove duplicate MUs within the same file
        based on discharge times.

    Examples
    --------
    Starting from a generic file, the results will look similar to the
    following if which="accuracy":

    >>> duplicates, duplicate_info = find_duplicates_within(
    ...     emgfile,
    ...     which="accuracy",
    ... )
    >>> duplicates
    [0, 3, 4]

    >>> duplicate_info
    [
        {
            'pair': (0, 1),
            'accuracy': (0.8768360226084906, 0.9552696780856847)
        },
        {
            'pair': (1, 3),
            'accuracy': (0.9552696780856847, 0.8969855881081578)
        },
        {
            'pair': (1, 4),
            'accuracy': (0.9552696780856847, 0.9178590868820631)
        }
    ]

    Or similar to the following if which="covisi":

    >>> duplicates, duplicate_info = find_duplicates_within(
    ...     emgfile,
    ...     which="covisi",
    ... )
    >>> duplicates
    [0, 1, 2, 3]

    >>> duplicate_info
    [
        {
            'pair': (0, 1),
            'covisi': (76.9574103452168, 16.266055150945718)
        },
        {
            'pair': (1, 3),
            'covisi': (16.266055150945718, 19.07156533711372)
        },
        {
            'pair': (1, 4),
            'covisi': (16.266055150945718, 15.38224044131706)
        },
        {
            'pair': (2, 4),
            'covisi': (23.264925152223373, 15.38224044131706)
        }
    ]

    The returned ``duplicates`` list can be used later to remove the duplicate
    units by passing it to the ``delete_mus`` function:

    >>> duplicates, duplicate_info = find_duplicates_within(
    ...     emgfile,
    ...     which="accuracy",
    ... )
    >>> emgfile = emg.delete_mus(emgfile, munumber=duplicates)
    """

    # If emgfile["NUMBER_OF_MUS"] == 0 and emgfile["MUPULSES"] == [],
    # returns [], []

    if which not in ["accuracy", "covisi"]:
        raise ValueError(
            f"Invalid input '{which}'. Please use: 'accuracy' or 'covisi'."
        )

    emgfile = copy.deepcopy(emgfile)

    c_lag = round(correlation_max_lag * emgfile["FSAMP"])
    p_lag = round(peak_window_half_width * emgfile["FSAMP"])

    duplicates = []
    duplicate_info = []

    # Calculate CoV ISI if needed
    if which == "covisi":
        covisi = []
        for mu in range(emgfile["NUMBER_OF_MUS"]):
            pulses = emgfile["MUPULSES"][mu]
            if len(pulses) < 4:
                covisi.append(np.inf)
            else:
                isi = np.diff(pulses)
                covisi.append((np.std(isi) / np.mean(isi)) * 100)

    # Start searching for the duplicates
    for mu1_idx in range(emgfile["NUMBER_OF_MUS"]):
        if mu1_idx in duplicates:
            continue

        if which == "accuracy":
            mark1 = emgfile["ACCURACY"].iat[mu1_idx, 0]
        else:
            mark1 = covisi[mu1_idx]

        for mu2_idx in range(mu1_idx + 1, emgfile["NUMBER_OF_MUS"]):
            if mu2_idx in duplicates:
                continue

            # Cross-correlation over full ±lag range
            xcorr = discrete_spike_xcorr(
                spikes1=emgfile["MUPULSES"][mu1_idx],
                spikes2=emgfile["MUPULSES"][mu2_idx],
                max_lag=c_lag,
            )

            indmax = int(np.argmax(xcorr))
            lower_bound = p_lag
            upper_bound = len(xcorr) - 1 - p_lag

            # The peak must be safely away from the edges
            if not (lower_bound < indmax < upper_bound):
                continue

            # Compute duplication sensitivity
            start = indmax - p_lag
            end = indmax + p_lag + 1
            sens_num = np.sum(xcorr[start:end])
            sens_den = max(
                len(emgfile["MUPULSES"][mu1_idx]),
                len(emgfile["MUPULSES"][mu2_idx]),
            )
            sens = (sens_num / sens_den) * 100 if sens_den > 0 else 0

            # If they are duplicates, mark the lower-accuracy MU
            if sens > duplicate_threshold:
                if which == "accuracy":
                    mark2 = emgfile["ACCURACY"].iat[mu2_idx, 0]

                    # Store info BEFORE marking duplicates
                    duplicate_info.append({
                        "pair": (mu1_idx, mu2_idx),
                        "accuracy": (float(mark1), float(mark2))
                    })

                    # Duplicate is lowest SIL
                    if mark1 >= mark2:
                        duplicates.append(mu2_idx)
                    else:
                        duplicates.append(mu1_idx)
                        break  # break early: mu1 itself is invalid now

                else:  # covisi
                    mark2 = covisi[mu2_idx]

                    duplicate_info.append({
                        "pair": (mu1_idx, mu2_idx),
                        "covisi": (float(mark1), float(mark2))
                    })

                    # Duplicate is highest covisi
                    if mark1 >= mark2:
                        duplicates.append(mu1_idx)
                        break  # break early: mu1 itself is invalid now
                    else:
                        duplicates.append(mu2_idx)

    # Sort duplicate units and make sure that each MU index appears only once
    duplicates = sorted(set(duplicates))

    return duplicates, duplicate_info


def remove_duplicates_within(
    emgfile,
    correlation_max_lag=50e-3,
    peak_window_half_width=2.5e-3,
    duplicate_threshold=30,
    which="accuracy",
):
    """
    Remove duplicate MUs within the same file based on discharge times.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    correlation_max_lag : float, default 50e-3
        Maximum lag (in seconds) used when computing the cross-correlation
        between MU spike trains. Defines the full search range for possible
        synchronisation peaks. Larger values allow detection of synchrony
        over wider time shifts. This must be < 1.
    peak_window_half_width : float, default 2.5e-3
        Half-width (in seconds) of the window used around the cross-correlation
        peak to compute the duplication sensitivity metric. This window should
        capture the narrow temporal jitter expected for duplicate MUs.
        This must be < 1 and < `correlation_max_lag`.
    duplicate_threshold : float, default 30
        Threshold (in percent) for classifying two MUs as duplicates.
        The sensitivity metric is computed as the sum of the cross-correlation
        values within a ±`peak_window_half_width` window around the
        correlation peak, normalised by the size of the larger spike train.
    which : str {"accuracy", "covisi"}, default "accuracy"
        How to remove the duplicated MUs.

        ``accuracy``
            The MU with the lowest accuracy is removed. The emgfile must
            already contain the 'ACCURACY' dataframe.

        ``covisi``
            The MU with the highest CoV of interspike interval is removed.

    Returns
    -------
    emgfile : dict
        The dictionary containing the emgfile without duplicated MUs.

    See also
    --------
    - find_duplicates_within : Find duplicate MUs within the same file based
        on discharge times.
    - remove_duplicates_between : Remove duplicated MUs across two different
        files based on STA.
    """

    # Find duplicates
    duplicates, _ = find_duplicates_within(
        emgfile=emgfile,
        correlation_max_lag=correlation_max_lag,
        peak_window_half_width=peak_window_half_width,
        duplicate_threshold=duplicate_threshold,
        which=which,
    )

    # Delete duplicate MUs
    emgfile = delete_mus(emgfile, munumber=duplicates)

    return emgfile


def sort_mus(emgfile):
    """
    Sort the MUs in order of recruitment.

    The following emgfile keys are sorted:

    - `IPTS`
    - `MUPULSES`
    - `BINARY_MUS_FIRING`
    - `ACCURACY`
    - `REFERENCE_MUPULSES`
    - `ROA_WITH_REFERENCE_MUPULSES`
    - `MU_LABELS`

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.

    Returns
    -------
    sorted_emgfile : dict
        The dictionary containing the sorted emgfile.
    """

    # Create the object to store the sorted emgfile.
    # Create a deepcopy to avoid changing the original emgfile
    sorted_emgfile = copy.deepcopy(emgfile)

    # Pre-check
    n_mus = emgfile.get("NUMBER_OF_MUS", None)
    if n_mus is None:
        raise KeyError("NUMBER_OF_MUS is not present.")
    if "MUPULSES" not in emgfile:
        raise KeyError("MUPULSES is not present.")
    if n_mus <= 1:
        # If we only have 1 MU, there is no necessity to sort it.
        return sorted_emgfile

    # Identify the sorting_order by the first MUpulse of every MUs
    def _first_pulse(mu):
        pulses = emgfile["MUPULSES"][mu]
        return pulses[0] if len(pulses) > 0 else np.inf
    sorting_order = sorted(range(n_mus), key=_first_pulse)

    # Sort MUPULSES and REFERENCE_MUPULSES (list of arrays).
    # Also MU_LABELS (dict{str: str}).
    for origpos, newpos in enumerate(sorting_order):
        if "MUPULSES" in sorted_emgfile:
            # Preferable to use the sorting_order as a double-check in
            # alternative to: sorted_emgfile["MUPULSES"] = sorted(
            #   sorted_emgfile["MUPULSES"], key=min, reverse=False))
            sorted_emgfile["MUPULSES"][origpos] = emgfile["MUPULSES"][newpos]

        if "REFERENCE_MUPULSES" in sorted_emgfile:
            sorted_emgfile["REFERENCE_MUPULSES"][
                origpos
            ] = emgfile["REFERENCE_MUPULSES"][newpos]

    if "MU_LABELS" in sorted_emgfile:
        new_labels = {}
        for origpos, newpos in enumerate(sorting_order):
            new_labels[str(origpos)] = emgfile["MU_LABELS"].get(
                str(newpos), "none",
            )
        sorted_emgfile["MU_LABELS"] = new_labels

    # Sort ACCURACY and ROA_WITH_REFERENCE_MUPULSES (single column)
    if "ACCURACY" in sorted_emgfile:
        sorted_emgfile["ACCURACY"] = emgfile["ACCURACY"].reindex(
            sorting_order
        ).reset_index(drop=True)

    if "ROA_WITH_REFERENCE_MUPULSES" in sorted_emgfile:
        sorted_emgfile["ROA_WITH_REFERENCE_MUPULSES"] = emgfile[
            "ROA_WITH_REFERENCE_MUPULSES"
        ].reindex(sorting_order).reset_index(drop=True)

    # Sort IPTS and BINARY_MUS_FIRING (multiple columns, sort by columns, then
    # reset columns' name)
    if "IPTS" in sorted_emgfile:
        sorted_emgfile["IPTS"] = sorted_emgfile["IPTS"].reindex(
            columns=sorting_order
        )
        sorted_emgfile["IPTS"].columns = np.arange(n_mus)

    if "BINARY_MUS_FIRING" in sorted_emgfile:
        sorted_emgfile["BINARY_MUS_FIRING"] = sorted_emgfile[
            "BINARY_MUS_FIRING"
        ].reindex(columns=sorting_order)
        sorted_emgfile["BINARY_MUS_FIRING"].columns = np.arange(n_mus)

    return sorted_emgfile


def compute_covsteady(
    emgfile,
    start_steady=-1,
    end_steady=-1,
    refsig_channel=0,
):
    """
    Calculate the CoV of REF_SIGNAL during the steady-state phase.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    start_steady, end_steady : int, default -1
        The start and end point (in samples) of the steady-state phase.
        If < 0 (default), the user will need to manually select the start and
        end of the steady-state phase.
    refsig_channel : int or str, Default 0
        The name of the reference signal channel (dataframe column) to plot.

    Returns
    -------
    covsteady : float
        The coefficient of variation of the steady-state phase in %.

    See also
    --------
    - compute_idr : computes the instantaneous discharge rate.

    Examples
    --------
    Load the EMG file, compute covsteady and access the result from GUI.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> covsteady = emg.compute_covsteady(emgfile=emgfile)
    >>> covsteady
    1.452806

    The process can be automated by bypassing the GUI.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> covsteady = emg.compute_covsteady(
    ...     emgfile=emgfile,
    ...     start_steady=3580,
    ...     end_steady=15820,
    ... )
    >>> covsteady
    35.611263
    """

    if (start_steady < 0 and end_steady < 0) or (start_steady < 0 or end_steady < 0):
        title = (
            "Select the start/end area to resize by hovering the mouse" +
            "\nand pressing the 'a'-key. Wrong points can be removed with " +
            "the \n'd' -key. When ready, press enter."
        )
        points = showselect(
            emgfile=emgfile,
            refsig_channel=refsig_channel,
            title=title,
            titlesize=10,
        )
        start_steady, end_steady = points[0], points[1]

    ref = emgfile["REF_SIGNAL"].loc[start_steady:end_steady]
    covsteady = (ref.std() / ref.mean()) * 100

    return covsteady[0]


def filter_rawemg(emgfile, order=2, lowcut=20, highcut=500):
    """
    Band-pass filter the RAW_SIGNAL.

    The filter is a Zero-lag band-pass Butterworth.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    order : int, default 2
        The filter order. Note that a band-pass transformation doubles the
        order, so `order=2` produces a 4th-order band-pass filter.
    lowcut : int, default 20
        The lower cut-off frequency in Hz.
    highcut : int, default 500
        The higher cut-off frequency in Hz.

    Returns
    -------
    filteredrawsig : dict
        The dictionary containing the emgfile with a filtered RAW_SIGNAL.

    See also
    --------
    - filter_refsig : low-pass filter the REF_SIGNAL.

    Notes
    -----
    Currently, the returned filteredrawsig cannot be accurately compressed
    when using the functions ``save_json_emgfile()`` and ``asksavefile()``.
    We therefore suggest you to use high-level functions and classes for
    binary files such as: 'save_openhdemg_module', 'asksavemodule',
    'load_openhdemg_module', 'askopenmodule', 'openhdemg_Collection'.
    """

    filteredrawsig = copy.deepcopy(emgfile)

    # Calculate the components of the filter and apply them with filtfilt to
    # obtain Zero-lag filtering. sos should be preferred over filtfilt as
    # second-order sections have fewer numerical problems.
    sos = signal.butter(
        N=order,
        Wn=[lowcut, highcut],
        btype="bandpass",
        output="sos",
        fs=filteredrawsig["FSAMP"],
    )

    raw = filteredrawsig["RAW_SIGNAL"]
    x = raw.to_numpy(dtype=np.float64, copy=False)
    y = signal.sosfiltfilt(sos, x, axis=0)

    filteredrawsig["RAW_SIGNAL"] = pd.DataFrame(
        y,
        index=raw.index,
        columns=raw.columns,
    )

    return filteredrawsig


def filter_refsig(emgfile, order=4, cutoff=15, refsig_channels=[0]):
    """
    Low-pass filter the REF_SIGNAL.

    This function is used to low-pass filter the REF_SIGNAL and remove noise.
    The filter is a Zero-lag low-pass Butterworth applied to the selected
    channels.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    order : int, default 4
        The effective filter order.
    cutoff : int, default 15
        The cut-off frequency in Hz.
    refsig_channels : list, default [0]
        The reference signal channels (DataFrame columns) to filter.

    Returns
    -------
    filteredrefsig : dict
        The dictionary containing the emgfile with a filtered REF_SIGNAL.

    See also
    --------
    - remove_offset : remove the offset from the REF_SIGNAL.
    - filter_rawemg : band-pass filter the RAW_SIGNAL.
    """

    filteredrefsig = copy.deepcopy(emgfile)

    # Normalise channels input
    if isinstance(refsig_channels, (int, str)):
        refsig_channels = [refsig_channels]
    elif not isinstance(refsig_channels, list):
        raise TypeError(
            "refsig_channels must be a list (or a single channel). "
            f"{type(refsig_channels)} was passed instead."
        )

    sos = signal.butter(
        N=order,
        Wn=cutoff,
        btype="lowpass",
        output="sos",
        fs=filteredrefsig["FSAMP"],
    )

    ref = filteredrefsig["REF_SIGNAL"]

    # Filter only selected channels and assign back
    x = ref.loc[:, refsig_channels].to_numpy(dtype=np.float64, copy=False)
    y = signal.sosfiltfilt(sos, x, axis=0)
    ref.loc[:, refsig_channels] = y

    filteredrefsig["REF_SIGNAL"] = ref

    return filteredrefsig


def remove_powerline_harmonics(
    sig,
    fsamp,
    notch_freq=50.0,
    notch_width=5.0
):
    """
    Remove power-line interference by zeroing FFT bins around all harmonics
    of the mains frequency.

    Parameters
    ----------
    sig : np.ndarray
        2-D array of shape (n_channels, n_samples).
        Each row is a signal and each column is a time sample.
    fsamp : float
        Sampling frequency in Hz.
    notch_freq : float, default 50.0
        Fundamental power-line frequency (e.g., 50 or 60 Hz).
    notch_width : float, default 5.0
        Width of each notch (± notch_width/2), in Hz.

    Returns
    -------
    np.ndarray
        Filtered signals with the same shape as `sig`.

    Examples
    --------
    Remove powerline harmonics in emgfile["RAW_SIGNAL"].

    >>> import openhdemg.library as emg
    >>> import pandas as pd
    >>> import numpy as np
    >>> emgfile = emg.emg_from_samplefile()
    >>> filtered_sig = emg.remove_powerline_harmonics(
    ...     sig=np.transpose(emgfile["RAW_SIGNAL"].to_numpy()),
    ...     fsamp=emgfile["FSAMP"],
    ... )
    >>> emgfile["RAW_SIGNAL"] = pd.DataFrame(
    ...     filtered_sig.T,
    ...     dtype=np.float64,
    ... )
    """

    # Ensure 2-D
    sig = np.atleast_2d(sig).copy()
    _, n_samples = sig.shape

    # FFT
    Y = np.fft.rfft(sig, axis=1)
    freqs = np.fft.rfftfreq(n_samples, d=1/fsamp)

    # Convert notch width to number of FFT bins
    bin_width = freqs[1] - freqs[0]
    half_bins = int(np.ceil((notch_width / 2) / bin_width))

    # Determine harmonic indices
    max_harmonic = int(freqs.max() // notch_freq)
    harmonic_bins = (
        np.arange(1, max_harmonic + 1) * notch_freq / bin_width
    ).astype(int)

    # Build mask of frequency bins to keep
    mask = np.ones_like(freqs, dtype=bool)

    for h_idx in harmonic_bins:
        lo = max(h_idx - half_bins, 0)
        hi = min(h_idx + half_bins + 1, len(freqs))
        mask[lo:hi] = False

    # Apply notch mask
    Y[:, ~mask] = 0

    # Inverse FFT → time domain
    return np.fft.irfft(Y, n=n_samples, axis=1)


def remove_offset(
    emgfile,
    offsetval=0,
    auto=0,
    refsig_channels=[0],
):
    """
    Remove the offset from the REF_SIGNAL.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    offsetval : float or list, default 0
        Value of the offset(s) to subtract.

        - If a single value (float/int), the same offset is subtracted from all
          selected channels.
        - If a list, it must have the same length as `refsig_channels`
          and each value is subtracted from the corresponding channel.
        - If 0, the user is asked to manually select an area to compute the
          offset (one channel at a time).
    auto : int, default 0
        If auto > 0, automatically compute and remove the offset using the
        first `auto` samples.
    refsig_channels : list, default [0]
        The reference signal channels (DataFrame columns) to process.

    Returns
    -------
    offs_emgfile : dict
        The dictionary containing the emgfile with a corrected offset of the
        REF_SIGNAL.

    See also
    --------
    - filter_refsig : low-pass filter REF_SIGNAL.
    """

    if not isinstance(auto, int):
        raise TypeError(
            f"auto must be an int. {type(auto)} was passed instead."
        )

    # Create a deepcopy to avoid changing the original refsig
    offs_emgfile = copy.deepcopy(emgfile)

    # Normalise channels input
    if isinstance(refsig_channels, (int, str)):
        refsig_channels = [refsig_channels]
    elif not isinstance(refsig_channels, list):
        raise TypeError(
            "refsig_channels must be a list (or a single channel). "
            f"{type(refsig_channels)} was passed instead."
        )

    # Act differently if automatic removal of the offset is active (>0) or not
    if auto <= 0:
        if offsetval != 0:
            # Directly subtract the offset value.
            if isinstance(offsetval, (float, int)):
                for ch in refsig_channels:
                    offs_emgfile["REF_SIGNAL"][ch] = (
                        offs_emgfile["REF_SIGNAL"][ch] - float(offsetval)
                    )
            elif isinstance(offsetval, (list, tuple)):
                if len(offsetval) != len(refsig_channels):
                    raise ValueError(
                        "If offsetval is a list, it must have the same "
                        "length as refsig_channels. "
                        f"Got len(offsetval)={len(offsetval)} and "
                        f"len(refsig_channels)={len(refsig_channels)}."
                    )
                for ch, off in zip(refsig_channels, offsetval):
                    if not isinstance(off, (float, int)):
                        raise TypeError(
                            "All elements of offsetval must be float/int. "
                            f"{type(off)} was found."
                        )
                    offs_emgfile["REF_SIGNAL"][ch] = (
                        offs_emgfile["REF_SIGNAL"][ch] - float(off)
                    )
            else:
                raise TypeError(
                    "offsetval must be a float or a list of float. "
                    f"{type(offsetval)} was passed instead."
                )

        else:
            # Select the area to calculate the offset
            # (average value of the selected area)
            title = (
                "Select the start/end area to calculate offset by hovering " +
                "the mouse \nand pressing the 'a'-key. Wrong points can be " +
                "removed with the \n'd' -key. When ready, press enter."
            )
            for ch in refsig_channels:
                points = showselect(
                    emgfile=offs_emgfile,
                    how="ref_signal",
                    refsig_channel=ch,
                    title=title,
                    titlesize=10,
                )
                start_, end_ = points[0], points[1]

                off = offs_emgfile["REF_SIGNAL"][ch].loc[start_:end_].mean()
                offs_emgfile["REF_SIGNAL"][ch] = offs_emgfile[
                    "REF_SIGNAL"
                ][ch] - float(off)

    else:
        # Compute and subract the automatic offsets to each selected column
        offsets = offs_emgfile[
            "REF_SIGNAL"
        ].iloc[:auto, :].loc[:, refsig_channels].mean(axis=0)

        for ch in refsig_channels:
            offs_emgfile["REF_SIGNAL"][ch] = offs_emgfile[
                "REF_SIGNAL"
            ][ch] - float(offsets[ch])

    return offs_emgfile


def get_mvc(emgfile, how="showselect", conversion_val=0, refsig_channel=0):
    """
    Measure the maximum voluntary contraction (MVC).

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile with the reference signal.
    how : str {"showselect", "all"}, default "showselect"

        ``showselect``
            Ask the user to select the area where to calculate the MVC
            with a GUI.

        ``all``
            Calculate the MVC on the entire file.
    conversion_val : float or int, default 0
        The conversion value to multiply the original reference signal.
        I.e., if the original reference signal is in kilogram (kg) and
        conversion_val=9.81, the output will be in Newton (N).
        If conversion_val=0 (default), the results will simply be in the
        original measure unit. conversion_val can be any custom int or float.
    refsig_channel : int or str, Default 0
        The name of the reference signal channel (dataframe column) to plot.

    Returns
    -------
    mvc : float
        The MVC value in the original (or converted) unit of measurement.

    See also
    --------
    - compute_rfd : calculate the RFD.
    - remove_offset : remove the offset from the REF_SIGNAL.
    - filter_refsig : low-pass filter REF_SIGNAL.

    Examples
    --------
    Load the EMG file, remove reference signal offset and get MVC value.

    >>> import openhdemg.library as emg
    >>> emg_refsig = emg.askopenfile(filesource="OTB_REFSIG")
    >>> offs_refsig = emg.remove_offset(emgfile=emg_refsig)
    >>> mvc = emg.get_mvc(emgfile=offs_refsig )
    >>> mvc
    50.72

    The process can be automated by bypassing the GUI and
    calculating the MVC of the entire file.

    >>> import openhdemg.library as emg
    >>> emg_refsig = emg.askopenfile(filesource="OTB_REFSIG")
    >>> mvc = emg.get_mvc(emgfile=emg_refsig, how="all")
    >>> print(mvc)
    50.86
    """

    if how == "all":
        mvc = emgfile["REF_SIGNAL"][refsig_channel].max()

    elif how == "showselect":
        # Select the area to measure the MVC (maximum value)
        title = (
            "Select the start/end area to calculate MVC by hovering " +
            "the mouse \nand pressing the 'a'-key. Wrong points can be " +
            "removed with the \n'd' -key. When ready, press enter."
        )
        points = showselect(
            emgfile=emgfile,
            how="ref_signal",
            refsig_channel=refsig_channel,
            title=title,
            titlesize=10,
        )
        start_, end_ = points[0], points[1]

        mvc = emgfile["REF_SIGNAL"].iloc[start_:end_][refsig_channel].max()

    else:
        raise ValueError(
            f"'how' must be 'showselect' or 'all', {how} was passed instead"
        )

    mvc = float(mvc)

    if conversion_val != 0:
        mvc = mvc * conversion_val

    return mvc


def compute_rfd(
    emgfile,
    ms=[50, 100, 150, 200],
    startpoint=None,
    conversion_val=0,
    refsig_channel=0,
):
    """
    Calculate the RFD.

    Rate of force development (RFD) is reported as X/Sec
    where "X" is the unit of measurement based on conversion_val.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile with the reference signal.
    ms : list, default [50, 100, 150, 200]
        Milliseconds (ms). A list containing the ranges in ms to calculate the
        RFD.
    startpoint : None or int, default None
        The starting point to calculate the RFD in samples,
        If None, the user will be requested to manually select the starting
        point.
    conversion_val : float or int, default 0
        The conversion value to multiply the original reference signal.
        I.e., if the original reference signal is in kilogram (kg) and
        conversion_val=9.81, the output will be in Newton/Sec (N/Sec).
        If conversion_val=0 (default), the results will simply be Original
        measure unit/Sec. conversion_val can be any custom int or float.
    refsig_channel : int or str, Default 0
        The name of the reference signal channel (dataframe column) to plot.

    Returns
    -------
    rfd : pd.DataFrame
        A pd.DataFrame containing the RFD at the different times.

    See also
    --------
    - get_mvif : measure the MViF.
    - remove_offset : remove the offset from the REF_SIGNAL.
    - filter_refsig : low-pass filter REF_SIGNAL.

    Examples
    --------
    Load the EMG file, low-pass filter the reference signal and compute RFD.

    >>> import openhdemg.library as emg
    >>> emg_refsig = emg.askopenfile(filesource="OTB_REFSIG")
    >>> filteredrefsig  = emg.filter_refsig(
    ...     emgfile=emg_refsig,
    ...     order=4,
    ...     cutoff=15,
    ... )
    >>> rfd = emg.compute_rfd(
    ...     emgfile=filteredrefsig,
    ...     ms=[50, 100, 200],
    ...     conversion_val=9.81,
    ...     )
    >>> rfd
            50         100        200
    0  68.34342  79.296188  41.308215

    The process can be automated by bypassing the GUI.

    >>> import openhdemg.library as emg
    >>> emg_refsig = emg.askopenfile(filesource="OTB_REFSIG")
    >>> filteredrefsig  = emg.filter_refsig(
    ...     emgfile=emg_refsig,
    ...     order=4,
    ...     cutoff=15,
    ...     )
    >>> rfd = emg.compute_rfd(
    ...     emgfile=filteredrefsig,
    ...     ms=[50, 100, 200],
    ...     startpoint=3568,
    ...     )
    >>> rfd
            50         100        200
    0  68.34342  79.296188  41.308215
    """

    # Check if the startpoint was passed
    if isinstance(startpoint, int):
        start_ = startpoint
    else:
        # Otherwise select the starting point for the RFD
        title = (
            "Select the start point to calculate RFD by hovering " +
            "the mouse \nand pressing the 'a'-key. Wrong points can be " +
            "removed with the \n'd' -key. When ready, press enter."
        )
        points = showselect(
            emgfile,
            how="ref_signal",
            refsig_channel=refsig_channel,
            title=title,
            titlesize=10,
            nclic=1,
        )
        start_ = points[0]

    # Create a dict to add the RFD
    rfd_dict = dict.fromkeys(ms, None)
    # Loop through the ms list and calculate the respective rfd.
    for thisms in ms:
        ms_insamples = round((int(thisms) * emgfile["FSAMP"]) / 1000)

        force_sig = emgfile["REF_SIGNAL"][refsig_channel]
        n_0 = force_sig.iloc[start_]
        n_next = force_sig.iloc[start_ + ms_insamples]

        rfdval = (n_next - n_0) / (thisms / 1000)
        # (ms/1000 to convert mSec in Sec)

        rfd_dict[thisms] = rfdval

    rfd = pd.DataFrame([rfd_dict])

    if conversion_val != 0:
        rfd = rfd * conversion_val

    return rfd


def compute_svr(
    emgfile,
    gammain=1/1.6,
    regparam=1/0.370,
    endpointweights_numpulses=5,
    endpointweights_magnitude=5,
    discontfiring_dur=1.0,
):
    """
    Fit MU discharge rates with Support Vector Regression, nonlinear
    regression.

    Provides smooth and continous estimates of discharge rate useful for
    quantification and visualisation. Suggested hyperparameters and framework
    from Beauchamp et. al., 2022
    https://doi.org/10.1088/1741-2552/ac4594

    Author: James (Drew) Beauchamp

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    gammain : float,  default 1/1.6
        The kernel coefficient.
    regparam : float,  default 1/0.370
        The regularization parameter, must be positive.
    endpointweights_numpulses : int, default 5
        Number of discharge instances at the start and end of MU firing to
        apply a weighting coefficient.
    endpointweights_magnitude : int, default 5
        The scaling factor applied to the number of pulses provided by
        endpointweights_numpulses.
        The scaling is applied to the regularization parameter, per sample.
        Larger values force the classifier to put more emphasis on the number
        of discharge instances at the start and end of firing provided by
        endpointweights_numpulses.
    discontfiring_dur : int, default 1
        Duration of time in seconds that defines an instnance of discontinuous
        firing. SVR fits will not be returned at points of discontinuity.

    Returns
    -------
    svrfits : pd.DataFrame
        A pd.DataFrame containing the smooth/continous MU discharge rates and
        corresponding time vectors.

    See also
    --------
    - compute_deltaf : quantify delta F via paired motor unit analysis.

    Examples
    --------
    Quantify svr fits.

    >>> import openhdemg.library as emg
    >>> import pandas as pd
    >>> emgfile = emg.emg_from_samplefile()
    >>> emgfile = emg.sort_mus(emgfile=emgfile)
    >>> svrfits = emg.compute_svr(emgfile)

    Quick plot showing the results.

    >>> smoothfits = pd.DataFrame(svrfits["gensvr"]).transpose()
    >>> emg.plot_smoothed_dr(
    >>>     emgfile,
    >>>     smoothfits=smoothfits,
    >>>     munumber="all",
    >>>     addidr=False,
    >>>     stack=True,
    >>>     addrefsig=True,
    >>> )
    """

    # TODO input checking and edge cases
    idr = compute_idr(emgfile)  # Calc IDR

    svrfit_acm = []
    svrtime_acm = []
    gensvr_acm = []
    for mu in range(len(idr)):  # For all MUs
        # Skip if no data
        if idr[mu].size==0:
            svrfit_acm.append([])
            svrtime_acm.append([])
            gensvr_acm.append(np.nan*np.ones(emgfile["EMG_LENGTH"]))

        else:            # Train the model on the data.
            # Time vector, removing first element.
            xtmp = np.transpose([idr[mu].timesec[1:]])
            # Discharge rates, removing first element, since DR has been assigned
            # to second pulse.
            ytmp = idr[mu].idr[1:].to_numpy()
            # Time between discharges, will use for discontinuity calc
            xdiff = idr[mu].diff_mupulses[2:].values
            # Motor unit pulses, samples
            mup = np.array(idr[mu].mupulses[1:].values)

            # Defining weight vector. A scaling applied to the regularization
            # parameter, per sample.
            smpwht = np.ones(len(ytmp))
            smpwht[0:endpointweights_numpulses-1] = endpointweights_magnitude
            smpwht[(len(ytmp)-(endpointweights_numpulses-1)):len(ytmp)] = endpointweights_magnitude

            # Create an SVR model with a gausian kernel and supplied hyperparams.
            # Origional hyperparameters from Beauchamp et. al., 2022:
            # https://doi.org/10.1088/1741-2552/ac4594
            svr = SVR(
                kernel='rbf', gamma=gammain, C=np.abs(regparam),
                epsilon=iqr(ytmp)/11,
            )
            svr.fit(xtmp, ytmp, sample_weight=smpwht)

            # Defining prediction vector
            # TODO need to add custom range.
            # From the second firing to the end of firing, in samples.
            predind = np.arange(mup[0], mup[-1]+1)
            predtime = (predind/emgfile["FSAMP"]).reshape(-1, 1)  # In time (s)
            newtm = []
            # Initialise nan vector for tracking fits aligned in time. Usefull for
            # later quant metrics.
            gen_svr = np.nan*np.ones(emgfile["EMG_LENGTH"])

            # Check for discontinous firing
            bkpnt = mup[
                np.where((xdiff > (discontfiring_dur * emgfile["FSAMP"])))[0]
            ]
            bkpnt = bkpnt[np.where(bkpnt != mup[-1])]

            if len(bkpnt) == 1:
                if bkpnt[0] == mup[0]:  # When first firing is the only discontinuity
                    bkpnt = []
                    predind = np.arange(mup[1], mup[-1]+1)
                    predtime = (predind/emgfile["FSAMP"]).reshape(-1, 1)

            # Make predictions on the data
            if len(bkpnt) > 0:  # If there is a point of discontinuity
                if bkpnt[0] == mup[0]:  # When first firing is discontinuity
                    smoothfit = np.nan*np.ones(1)
                    newtm = np.nan*np.ones(1)
                    bkpnt = bkpnt[1:]

                tmptm = predtime[
                    0: np.where(
                        (bkpnt[0] >= predind[0:-1]) & (bkpnt[0] < predind[1:])
                    )[0][0],
                ]  # Break up time vector for first continous range of firing
                smoothfit = svr.predict(tmptm)  # Predict with svr model
                newtm = np.append(newtm,tmptm,)  # Track new time vector

                tmpind = predind[
                    0: np.where(
                        (bkpnt[0] >= predind[0:-1]) & (bkpnt[0] < predind[1:])
                    )[0][0]
                ]  # Sample vector of first continous range of firing
                
                # Fill corresponding sample indices with svr fit
                gen_svr[tmpind.astype(np.int64)] = smoothfit
                # Add last firing as discontinuity
                bkpnt = np.append(bkpnt, mup[-1])
                for ii in range(len(bkpnt)-1):  # All instances of discontinuity
                    curind = np.where(
                        (bkpnt[ii] > predind[0:-1]) & (bkpnt[ii] <= predind[1:])
                    )[0][0]  # Current index of discontinuity
                    nextind = np.where(
                        (bkpnt[ii+1] > predind[0:-1]) & (bkpnt[ii+1] <= predind[1:])
                    )[0][0]  # Next index of discontinuity

                    # MU firing before discontinuity
                    curmup = np.where(mup == bkpnt[ii])[0][0]
                    curind_nmup = np.where(
                        (mup[curmup+1] > predind[0:-1]) & (mup[curmup+1] <= predind[1:])
                    )[0][0]  # MU firing after discontinuity

                    # If the next discontinuity is the next MU firing, nan fill
                    if curind_nmup >= nextind:
                        # Edge case NEED TO CHECK THE GREATER THAN CASE>> WHY TODO
                        smoothfit = np.append(smoothfit, np.nan*np.ones(1))
                        newtm = np.append(newtm, np.nan*np.ones(1))
                    else:  # Fit next continuous region of firing
                        smoothfit = np.append(
                            smoothfit,
                            np.nan*np.ones(len(predtime[curind:curind_nmup])-2),
                        )
                        smoothfit = np.append(
                            smoothfit, svr.predict(predtime[curind_nmup:nextind]),
                        )
                        newtm = np.append(
                            newtm,
                            np.nan*np.ones(len(predtime[curind:curind_nmup])-2),
                        )
                        newtm = np.append(newtm, predtime[curind_nmup:nextind],)
                        gen_svr[predind[curind_nmup:nextind]] = svr.predict(
                            predtime[curind_nmup:nextind]
                        )
            else:
                smoothfit = svr.predict(predtime)
                newtm = predtime
                gen_svr[predind] = smoothfit


            # Append fits, new time vect, time aligned fits
            svrfit_acm.append(smoothfit.copy())
            svrtime_acm.append(np.squeeze(newtm.copy()))
            gensvr_acm.append(gen_svr.copy())

    svrfits = {
        "svrfit": svrfit_acm,
        "svrtime": svrtime_acm,
        "gensvr": gensvr_acm,
    }

    return svrfits
