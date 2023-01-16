"""
This module contains informations about the electrodes sold by OTB and
commonly used for HD-EMG recordings.
Functions to sort the electrode position are also included. These functions
are used only for the OTBiolab+ software since DEMUSE already provides sorted
channels.
"""

import numpy as np
import copy

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
Electrodes name.

>>> OTBelectrodes_tuple
('GR04MM1305', 'GR08MM1305', 'GR100ML1305', 'GR10MM0804', 'GR10MM0808', 'HD04MM1305', 'HD08MM1305', 'HD10MM0804', 'HD10MM0808')
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
Interelectrode distance for each matrix.

>>> OTBelectrodes_ied
{'GR04MM1305': 4, 'GR08MM1305': 8, 'GR100ML1305': 2.5, 'GR10MM0804': 10, 'GR10MM0808': 10, 'HD04MM1305': 4, 'HD08MM1305': 8, 'HD10MM0804': 10, 'HD10MM0808': 10}
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
Number of electrodes for each matrix.

>>> OTBelectrodes_Nelectrodes
{'GR04MM1305': 64, 'GR08MM1305': 64, 'GR100ML1305': 64, 'GR10MM0804': 32, 'GR10MM0808': 64, 'HD04MM1305': 64, 'HD08MM1305': 64, 'HD10MM0804': 32, 'HD10MM0808': 64}
"""


# ---------------------------------------------------------------------
# Sort the electrodes of different matrices.
# Sorting orders have been implemented for name(orientation):
# - GR08MM1305(0, 180)
# - GR04MM1305(0, 180)
# - GR10MM0808(0, 180)


def sort_rawemg(
    emgfile,
    code="GR08MM1305",
    orientation=180,
    dividebycolumn=True
):
    """
    Sort RAW_SIGNAL based on matrix type and orientation.

    Built-in sorting functions have been implemented for code(orientation):
        GR08MM1305(0, 180),
        GR04MM1305(0, 180),
        GR10MM0808(0, 180).

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    code : str {"GR08MM1305", "GR04MM1305", "GR10MM0808"}, default "GR08MM1305"
        The code of the matrix used.
    orientation : int {0, 180}, default 180
        Orientation in degree of the matrix (same as in OTBiolab).
        E.g. 180 corresponds to the matrix connection toward the user.

    Returns
    -------
    sorted_rawemg : dict or pd.DataFrame
        If dividebycolumn == True a dict containing the sorted electrodes.
        Every key of the dictionary represents a different column of the
        matrix. Rows are stored in the dict as a pd.DataFrame.
        If dividebycolumn == False a pd.DataFrame containing the sorted
        electrodes. The matrix channels are stored in the pd.DataFrame columns.

    Notes
    -----
    The returned file is called ``sorted_rawemg`` for convention.
    Files coming from DEMUSE or OTBiolab+ have the same final format.

    DEMUSE files are supposed to be already sorted and are therefore only
    divided by columns if requested.

    Examples
    --------
    Sort emgfile RAW_SIGNAL and divide it by columns.

    >>> import openhdemg as emg
    >>> emgfile = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> sorted_rawemg = emg.sort_rawemg(emgfile, code="GR08MM1305", orientation=180, dividebycolumn=True)
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
    >>> sorted_rawemg = emg.sort_rawemg(emgfile, code="GR08MM1305", orientation=180, dividebycolumn=False)
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
    """

    # DEMUSE files are supposed to be already sorted
    if emgfile["SOURCE"] == "OTB":
        # Work on a copy of the RAW_SIGNAL
        rawemg = copy.deepcopy(emgfile["RAW_SIGNAL"])

        # Get sorting order by matrix
        if code in ["GR08MM1305", "GR04MM1305"]:
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
                    63,62,61,60,59,58,57,56,55,54,53,52,    51,
                    38,39,40,41,42,43,44,45,46,47,48,49,    50,
                    37,36,35,34,33,32,31,30,29,28,27,26,    25,
                    12,13,14,15,16,17,18,19,20,21,22,23,    24,
                    11,10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0,np.nan
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
                    np.nan,0, 1 ,2 ,3 ,4 ,5 ,6 ,7 ,8 ,9 ,10,11,
                    24    ,23,22,21,20,19,18,17,16,15,14,13,12,
                    25    ,26,27,28,29,30,31,32,33,34,35,36,37,
                    50    ,49,48,47,46,45,44,43,42,41,40,39,38,
                    51    ,52,53,54,55,56,57,58,59,60,61,62,63
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
                    56, 57, 58, 59, 60, 61, 62, 63,
                    48, 49, 50, 51, 52, 53, 54, 55,
                    40, 41, 42, 43, 44, 45, 46, 47,
                    33, 33, 34, 35, 36, 37, 38, 39,
                    24, 25, 26, 27, 28, 29, 30, 31,
                    16, 17, 18, 19, 20, 21, 22, 23,
                     8,  9, 10, 11, 12, 13, 14, 15,
                     0,  1,  2,  3,  4,  5,  6,  7,
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
                    7,   6,  5,  4,  3,  2,  1,  0,
                    15, 14, 13, 12, 11, 10,  9,  8,
                    23, 22, 21, 20, 19, 18, 17, 16,
                    31, 30, 29, 28, 27, 26, 25, 24,
                    39, 38, 37, 36, 35, 34, 33, 32,
                    47, 46, 45, 44, 43, 42, 41, 40,
                    55, 54, 53, 52, 51, 50, 49, 48,
                    63, 62, 61, 60, 59, 58, 57, 56,
                ]

        else:
            pass # TODO_NEXT_ add other electrodes, and orientations?

        # Once the order to sort channels has been retrieved,
        # Sort the channels based on pre-specified order and reset columns
        sorted_rawemg = rawemg.reindex(columns=base0_sorting_order)
        sorted_rawemg.columns = range(sorted_rawemg.columns.size)

    elif emgfile["SOURCE"] == "DEMUSE":
        # For DEMUSE files (supposed to be already sorted)
        # Work on a copy of the RAW_SIGNAL
        sorted_rawemg = copy.deepcopy(emgfile["RAW_SIGNAL"])

    elif emgfile["SOURCE"] == "custom":
        pass # TODO what do we do with a custom file?

    # Check if we need the sorted RAW_SIGNAL divided by column
    if dividebycolumn:
        if code in ["GR08MM1305", "GR04MM1305"]:
            if orientation in [0, 180]:
                sorted_rawemg = {
                            "col0":sorted_rawemg.loc[:,0:12],
                            "col1":sorted_rawemg.loc[:,13:25],
                            "col2":sorted_rawemg.loc[:,26:38],
                            "col3":sorted_rawemg.loc[:,39:51],
                            "col4":sorted_rawemg.loc[:,52:64]
                        }

        elif code == "GR10MM0808":
            if orientation in [0, 180]:
                sorted_rawemg = {
                            "col0":sorted_rawemg.loc[:,0:7],
                            "col1":sorted_rawemg.loc[:,8:15],
                            "col2":sorted_rawemg.loc[:,16:23],
                            "col3":sorted_rawemg.loc[:,24:31],
                            "col4":sorted_rawemg.loc[:,32:39],
                            "col5":sorted_rawemg.loc[:,40:47],
                            "col6":sorted_rawemg.loc[:,48:55],
                            "col7":sorted_rawemg.loc[:,56:63]
                        }

        return sorted_rawemg

    else:
        return sorted_rawemg
