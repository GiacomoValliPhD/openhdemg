"""
This module contains informations about the electrodes commonly used for
HD-EMG recordings.
Functions to sort the electrode position are also included.
"""

import numpy as np
import copy
import itertools

OTBelectrodes_tuple = (
    "GR04MM1305",
    "GR08MM1305",
    "GR100ML1305",
    "GR10MM0804",
    "GR10MM0808",
    "HD04MM1305",
    "HD08MM1305",
    "HD10MM0804",
    "HD10MM0808",
)
"""
Tuple containing the names of different recording electrodes.

>>> OTBelectrodes_tuple
(
    'GR04MM1305',
    'GR08MM1305',
    'GR100ML1305',
    'GR10MM0804',
    'GR10MM0808',
    'HD04MM1305',
    'HD08MM1305',
    'HD10MM0804',
    'HD10MM0808',
)
"""

OTBelectrodes_ied = {
    "GR04MM1305": 4,
    "GR08MM1305": 8,
    "GR100ML1305": 2.5,
    "GR10MM0804": 10,
    "GR10MM0808": 10,
    "HD04MM1305": 4,
    "HD08MM1305": 8,
    "HD10MM0804": 10,
    "HD10MM0808": 10,
}
"""
A dict containing information about the interelectrode distance for each
matrix in OTBelectrodes_tuple.

>>> OTBelectrodes_ied
{
    'GR04MM1305': 4,
    'GR08MM1305': 8,
    'GR100ML1305': 2.5,
    'GR10MM0804': 10,
    'GR10MM0808': 10,
    'HD04MM1305': 4,
    'HD08MM1305': 8,
    'HD10MM0804': 10,
    'HD10MM0808': 10,
}
"""

OTBelectrodes_Nelectrodes = {
    "GR04MM1305": 64,
    "GR08MM1305": 64,
    "GR100ML1305": 64,
    "GR10MM0804": 32,
    "GR10MM0808": 64,
    "HD04MM1305": 64,
    "HD08MM1305": 64,
    "HD10MM0804": 32,
    "HD10MM0808": 64,
}
"""
A dict containing information about the number of electrodes for each
matrix in OTBelectrodes_tuple.

>>> OTBelectrodes_Nelectrodes
{
    'GR04MM1305': 64,
    'GR08MM1305': 64,
    'GR100ML1305': 64,
    'GR10MM0804': 32,
    'GR10MM0808': 64,
    'HD04MM1305': 64,
    'HD08MM1305': 64,
    'HD10MM0804': 32,
    'HD10MM0808': 64,
}
"""

DELSYSelectrodes_tuple = (
    "Trigno Galileo Sensor",
)
"""
Tuple containing the names of different recording electrodes.

>>> DELSYSelectrodes_tuple
(
    'Trigno Galileo Sensor',
)
"""

DELSYSelectrodes_ied = {
    "Trigno Galileo Sensor": 5,
}
"""
A dict containing information about the interelectrode distance for each
matrix in DELSYSelectrodes_tuple.

>>> DELSYelectrodes_ied
{
    'Trigno Galileo Sensor': 5,
}
"""

DELSYSelectrodes_Nelectrodes = {
    "Trigno Galileo Sensor": 4,
}
"""
A dict containing information about the number of electrodes for each
matrix in DELSYSelectrodes_tuple.

>>> DELSYSelectrodes_Nelectrodes
{
    'Trigno Galileo Sensor': 4,
}
"""


# ---------------------------------------------------------------------
# Sort the electrodes of different matrices.


def sort_rawemg(
    emgfile,
    code="GR08MM1305",
    orientation=180,
    dividebycolumn=True,
    n_rows=None,
    n_cols=None,
    custom_sorting_order=None,
):
    """
    Sort RAW_SIGNAL based on matrix type and orientation.

    To date, built-in sorting functions have been implemented for the matrices:

        Code                    (Orientation)
        GR08MM1305              (0, 180)
        GR04MM1305              (0, 180)
        GR10MM0808              (0, 180)
        Trigno Galileo Sensor   (na)
        Custom order            (any)

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    code : str, default "GR08MM1305"
        The code of the matrix used. It can be one of:

        ``GR08MM1305``

        ``GR04MM1305``

        ``GR10MM0808``

        ``Trigno Galileo Sensor``

        ``Custom order``

        ``None``

        If "None", the electodes are not sorted but n_rows and n_cols must be
        specified when dividebycolumn == True.
        If "Custom order", the electrodes are sorted based on
        custom_sorting_order.
    orientation : int {0, 180}, default 180
        Orientation in degree of the matrix.
        E.g. 180 corresponds to the matrix connection toward the researcher or
        the ground (depending on the limb).
        Ignore if using the "Trigno Galileo Sensor". In this case, channels
        will be oriented as in the Delsys Neuromap Explorer software.
        This Parameter is ignored if code=="Custom order" or code=="None".
    dividebycolumn = bool, default True
        Whether to return the sorted channels classified by matrix column.
    n_rows : None or int, default None
        The number of rows of the matrix. This parameter is used to divide the
        channels based on the matrix shape. These are inferred by the matrix
        code and must be specified only if code==None.
    n_cols : None or int, default None
        The number of columns of the matrix. This parameter is used to divide
        the channels based on the matrix shape. These are inferred by the
        matrix code and must be specified only if code==None.
    custom_sorting_order : None or list, default None
        If code=="Custom order", custom_sorting_order will be used for
        channels sorting. In this case, custom_sorting_order must be a list of
        lists containing the order of the matrix channels.
        Specifically, the number of columns are defined by
        len(custom_sorting_order) while the number of rows by
        len(custom_sorting_order[0]). np.nan can be used to specify empty
        channels. Please refer to the Notes and Examples section for the
        structure of the custom sorting order.

    Returns
    -------
    sorted_rawemg : dict or pd.DataFrame
        If dividebycolumn == True, a dict containing the sorted electrodes is
        returned. Every key of the dictionary represents a different column of
        the matrix. Rows are stored in the dict as a pd.DataFrame.
        If dividebycolumn == False a pd.DataFrame containing the sorted
        electrodes is returned. The matrix channels are stored in the
        pd.DataFrame columns.

    Notes
    -----
    The returned file is called ``sorted_rawemg`` for convention.

    Additional info on how to create the custom sorting order is available at:
    https://www.giacomovalli.com/openhdemg/gui_settings/#electrodes

    Examples
    --------
    Sort emgfile RAW_SIGNAL and divide it by columns with built-in sorting
    orders.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> sorted_rawemg = emg.sort_rawemg(
    ...     emgfile=emgfile,
    ...     code="GR08MM1305",
    ...     orientation=180,
    ...     dividebycolumn=True,
    ... )
    >>> sorted_rawemg["col0"]
            0          1          2 ...        10         11         12
    0     NaN -11.189778   3.560384 ... -2.034505  -3.051758  -0.508626
    1     NaN -12.715657   4.577637 ...  2.034505  -7.120768  -0.508626
    2     NaN   0.508626  21.870932 ... 17.801920   8.646647  16.276041
    3     NaN   6.103516  26.957193 ... 26.448568  19.327799  19.836426
    4     NaN  -5.594889  13.224284 ... 10.681152   2.034505   3.560384
    ...    ..        ...        ... ...       ...        ...        ...
    63483 NaN -15.767415 -22.379557 ...-12.207031 -12.207031 -15.767415
    63484 NaN  -9.155273 -19.327799 ... -7.629395  -8.138021  -8.138021
    63485 NaN  -6.103516 -12.207031 ... -6.103516  -5.086263  -3.051758
    63486 NaN  -6.103516 -15.767415 ... -3.560384  -0.508626   2.543132
    63487 NaN  -8.138021 -18.819174 ... -2.034505  -1.525879   3.560384

    Sort emgfile RAW_SIGNAL without dividing it by columns.

    >>> emgfile = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> sorted_rawemg = emg.sort_rawemg(
    ...     emgfile,
    ...     code="GR08MM1305",
    ...     orientation=180,
    ...     dividebycolumn=False,
    ... )
    >>> sorted_rawemg
           0          1          2  ...        62         63         64
    0     NaN -11.189778   3.560384 ... -5.086263  -9.663899   2.034505
    1     NaN -12.715657   4.577637 ... -3.560384  -8.646647   1.017253
    2     NaN   0.508626  21.870932 ... 11.189778   6.612142  17.293295
    3     NaN   6.103516  26.957193 ... 22.888184  14.750163  21.362305
    4     NaN  -5.594889  13.224284 ...  9.663899   1.525879   6.612142
    ...    ..        ...        ... ...       ...        ...        ...
    63483 NaN -15.767415 -22.379557 ... -8.646647 -20.345053 -15.258789
    63484 NaN  -9.155273 -19.327799 ... -7.120768 -19.327799 -13.732910
    63485 NaN  -6.103516 -12.207031 ... -3.051758 -10.681152  -6.103516
    63486 NaN  -6.103516 -15.767415 ...  2.543132  -7.120768  -4.069010
    63487 NaN  -8.138021 -18.819174 ...  2.034505  -3.051758  -0.508626

    Avoid RAW_SIGNAL sorting but divide it by columns.

    >>> emgfile = emg.askopenfile(filesource="CUSTOM")
    >>> sorted_rawemg = emg.sort_rawemg(
    ...     emgfile, code="None", n_cols=5, n_rows=13,
    ...     )
    >>> sorted_rawemg["col0"]
                 0         1         2  ...       10        11  12
    0      0.008138  0.001017  0.002035 ... 0.005595  0.008647 NaN
    1     -0.005595 -0.011190 -0.014750 ... 0.000000  0.005086 NaN
    2     -0.017293 -0.020854 -0.021871 ... 0.009664 -0.004578 NaN
    3     -0.003560 -0.012716 -0.009155 ... 0.004578  0.007121 NaN
    4      0.001526 -0.005595 -0.005595 ... 0.007121  0.010173 NaN
    ...         ...       ...       ... ...      ...       ...  ..
    62459  0.011698  0.015259  0.004069 ... 0.000000  0.031026 NaN
    62460  0.007629  0.011698  0.002543 ... 0.002035  0.026449 NaN
    62461  0.001526  0.009664  0.000000 ... 0.001526  0.025940 NaN
    62462  0.033061  0.037130  0.027974 ... 0.022380  0.049845 NaN
    62463  0.020854  0.028992  0.017802 ... 0.013733  0.037638 NaN

    Sort RAW_SIGNAL based on a custom order and divide it by columns.
    The custom_sorting_order refers to a grid of 13 rows and 5 columns with the
    empty channel in last position.

    Additional info on how to create the custom sorting order is available at:
    https://www.giacomovalli.com/openhdemg/gui_settings/#electrodes

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> custom_sorting_order = [
    ...     [63, 62, 61, 60, 59, 58, 57, 56, 55, 54, 53, 52,     51,],
    ...     [38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49,     50,],
    ...     [37, 36, 35, 34, 33, 32, 31, 30, 29, 28, 27, 26,     25,],
    ...     [12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,     24,],
    ...     [11, 10,  9,  8,  7,  6,  5,  4,  3,  2,  1,  0, np.nan,],
    ... ]  # 13 rows and 5 columns
    >>> sorted_rawemg = emg.sort_rawemg(
    ...     emgfile=emgfile,
    ...     code="Custom order",
    ...     dividebycolumn=True,
    ...     custom_sorting_order=custom_sorting_order,
    ... )
    >>> sorted_rawemg["col0"]
                  0          1          2  ...         10         11         12
    0       2.034505  -9.663899  -5.086263 ... -26.957193  -8.138021  -2.034505
    1       1.017253  -8.646647  -3.560384 ... -26.957193  -8.138021  -9.663899
    2      17.293295   6.612142  11.189778 ... -13.224284   9.663899   6.612142
    3      21.362305  14.750163  22.888184 ...  -9.155273  17.293295  12.715657
    ...          ...        ...        ... ...        ...        ...        ...
    63483 -15.258789 -20.345053  -8.646647 ... -20.853678 -15.767415 -10.681152
    63484 -13.732910 -19.327799  -7.120768 ... -21.362305 -17.801920 -14.241536
    """

    valid_codes = [
        "GR08MM1305",
        "GR04MM1305",
        "GR10MM0808",
        "Trigno Galileo Sensor",
        "None",
        "Custom order",
    ]
    if code not in valid_codes:
        return ValueError("Unsupported code in sort_rawemg()")

    # Work on a copy of the RAW_SIGNAL
    rawemg = copy.deepcopy(emgfile["RAW_SIGNAL"])

    # Get sorting order by matrix code
    if code == "Custom order":
        # Theck that custom_sorting_order has been specified
        if not isinstance(custom_sorting_order, list):
            raise ValueError(
                "In sort_rawemg(), custom_sorting_order must be a list of " +
                "lists when code=='Custom order'"
            )

        # Get custom sorting order
        base0_sorting_order = custom_sorting_order

    elif code in ["GR08MM1305", "GR04MM1305"]:
        # Get sorting order by matrix orientation
        if orientation == 0:
            """
            MUST REMEMBER: python loops from 0 and the emg channels start
            from 0 but the channel order reflects the real channels and
            starts from 1! This order is for the user, while the script
            uses the base0_sorting_order.

            base0_sorting_order provides the sorting order while
            base0_nanpos indicates the position of the empty (np.nan)
            channel.

            Channel Order GR08MM1305
                   0   1   2   3   4
            0     64  39  38  13  12
            1     63  40  37  14  11
            2     62  41  36  15  10
            3     61  42  35  16   9
            4     60  43  34  17   8
            5     59  44  33  18   7
            6     58  45  32  19   6
            7     57  46  31  20   5
            8     56  47  30  21   4
            9     55  48  29  22   3
            10    54  49  28  23   2
            11    53  50  27  24   1
            12    52  51  26  25 NaN
            """
            base0_sorting_order = [
                [63, 62, 61, 60, 59, 58, 57, 56, 55, 54, 53, 52,     51],
                [38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49,     50],
                [37, 36, 35, 34, 33, 32, 31, 30, 29, 28, 27, 26,     25],
                [12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,     24],
                [11, 10,  9,  8,  7,  6,  5,  4,  3,  2,  1,  0, np.nan],
            ]

        elif orientation == 180:
            """
            Channel Order GR08MM1305
                   0   1   2   3   4
            0    NaN  25  26  51  52
            1      1  24  27  50  53
            2      2  23  28  49  54
            3      3  22  29  48  55
            4      4  21  30  47  56
            5      5  20  31  46  57
            6      6  19  32  45  58
            7      7  18  33  44  59
            8      8  17  34  43  60
            9      9  16  35  42  61
            10    10  15  36  41  62
            11    11  14  37  40  63
            12    12  13  38  39  64
            """
            base0_sorting_order = [
                [np.nan,  0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11],
                [24,     23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12],
                [25,     26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37],
                [50,     49, 48, 47, 46, 45, 44, 43, 42, 41, 40, 39, 38],
                [51,     52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63],
            ]

    elif code == "GR10MM0808":
        if orientation == 0:
            """
            Channel Order GR10MM0808
                0   1   2   3   4   5   6   7
            0  57  49  41  33  25  17   9   1
            1  58  50  42  34  26  18  10   2
            2  59  51  43  35  27  19  11   3
            3  60  52  44  36  28  20  12   4
            4  61  53  45  37  29  21  13   5
            5  62  54  46  38  30  22  14   6
            6  63  55  47  39  31  23  15   7
            7  64  56  48  40  32  24  16   8
            """
            base0_sorting_order = [
                [56, 57, 58, 59, 60, 61, 62, 63],
                [48, 49, 50, 51, 52, 53, 54, 55],
                [40, 41, 42, 43, 44, 45, 46, 47],
                [33, 33, 34, 35, 36, 37, 38, 39],
                [24, 25, 26, 27, 28, 29, 30, 31],
                [16, 17, 18, 19, 20, 21, 22, 23],
                [8,  9, 10, 11, 12, 13, 14, 15],
                [0,  1,  2,  3,  4,  5,  6,  7],
            ]

        elif orientation == 180:
            """
            Channel Order GR10MM0808
                0   1   2   3   4   5   6   7
            0   8  16  24  32  40  48  56  64
            1   7  16  23  31  39  47  55  63
            2   6  14  22  30  38  46  54  62
            3   5  13  21  29  37  45  53  61
            4   4  12  20  28  36  44  52  60
            5   3  11  19  27  35  43  51  59
            6   2  10  18  26  34  42  50  58
            7   1   9  17  25  33  41  49  57
            """
            base0_sorting_order = [
                [7,   6,  5,  4,  3,  2,  1,  0],
                [15, 14, 13, 12, 11, 10,  9,  8],
                [23, 22, 21, 20, 19, 18, 17, 16],
                [31, 30, 29, 28, 27, 26, 25, 24],
                [39, 38, 37, 36, 35, 34, 33, 32],
                [47, 46, 45, 44, 43, 42, 41, 40],
                [55, 54, 53, 52, 51, 50, 49, 48],
                [63, 62, 61, 60, 59, 58, 57, 56],
            ]

    elif code == "Trigno Galileo Sensor":
        """
        Channel Order Trigno Galileo Sensor

            1
        4       2
            3

        Will be represented as:
            0
        0   1
        1   2
        2   3
        3   4
        """
        base0_sorting_order = [[0, 1, 2, 3]]

    else:  # elif code == "None":
        pass

    # Once the order to sort channels has been retrieved,
    # Sort the channels based on pre-specified order and reset columns
    if code not in [None, "None"]:
        flattened_base0_sorting_order = list(
            itertools.chain(*base0_sorting_order),
        )
        sorted_rawemg = rawemg.reindex(columns=flattened_base0_sorting_order)
        sorted_rawemg.columns = range(sorted_rawemg.columns.size)
    else:
        # Always allow a way to avoid electrodes sorting.
        # Return a copy of the RAW_SIGNAL
        sorted_rawemg = rawemg

    # Check if we need the sorted RAW_SIGNAL divided by column
    if dividebycolumn:
        if code not in [None, "None"]:
            n_cols = len(base0_sorting_order)
            n_rows = len(base0_sorting_order[0])

        else:
            # Check if n_rows and n_cols have been passed
            if not isinstance(n_rows, int):
                raise ValueError(
                    "In sort_rawemg(), n_rows and n_cols must be integers " +
                    "when code == 'None'"
                )
            if not isinstance(n_cols, int):
                raise ValueError(
                    "In sort_rawemg(), n_rows and n_cols must be integers " +
                    "when code == 'None'"
                )

        # Create the empty dict to fill with the sorted_rawemg divided by
        # columns. But first check for missing empty channel.
        if n_rows * n_cols != sorted_rawemg.shape[1]:
            raise ValueError(
                "Number of rows * columns must match the number of channels."
            )

        empty_dict = {f"col{n}": None for n in range(n_cols)}

        for pos, col in enumerate(empty_dict.keys()):
            empty_dict[col] = sorted_rawemg.iloc[:, n_rows*pos:n_rows*(pos+1)]

        sorted_rawemg = empty_dict

    return sorted_rawemg
