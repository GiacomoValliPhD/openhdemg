""" 
This module contains informations about the electrodes sold by OTB and commonly used for HD-EMG recordings.
Functions to sort the electrode position are also included. These functions are used only for the OTBiolab+
software since DEMUSE already provides sorted channels.
Built-in sorting functions have been implemented for "GR08MM1305" and "GR04MM1305" matrices with 0 or 180° orientation.
"""
#TODO check str inputs and describe allowed cases allover the different modules
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
Electrodes name

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
Interelectrode distance for each matrix

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
Number of electrodes for each matrix

>>> OTBelectrodes_Nelectrodes
{'GR04MM1305': 64, 'GR08MM1305': 64, 'GR100ML1305': 64, 'GR10MM0804': 32, 'GR10MM0808': 64, 'HD04MM1305': 64, 'HD08MM1305': 64, 'HD10MM0804': 32, 'HD10MM0808': 64}
"""


# ---------------------------------------------------------------------
# Sort the electrodes of different matrices.
# Sorting orders have been implemented for name(orientation):
# - GR08MM1305(0, 180)
# - GR04MM1305(0, 180)

def get_rawemg_sortingorder(code, orientation):
    """
    Obtain order for sorting RAW_SIGNAL based on matrix type and orientation.

    Parameters
    ----------
    code : str
        The code of the matrix used.
    orientation : int
        Orientation in degree of the matrix (same as in OTBiolab).
        E.g. 180 corresponds to the matrix connection toward the user.

    Returns
    -------
    base0_sorting_order : list
        Sorting order with base 0.
    base0_nanpos : int
        Position of the empty (np.nan) channel with base 0.

    Notes
    -----
    The returned files are called ``base0_sorting_order, base0_nanpos``.
    """

    if code == "GR08MM1305" or code == "GR04MM1305":
        if orientation == 0:
            """
            MUST REMEMBER: python loops from 0 and the emg channels start from 0
            but the channel order reflects the real channels and starts from 1!
            This order is for the user, while the script uses the base0_sorting_order.

            base0_sorting_order provides the sorting order while
            base0_nanpos indicates the position of the empty (np.nan) channel.

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
            base0_nanpos = 64

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
            base0_nanpos = 0

    else:
        pass  # TODO add other electrodes

    return base0_sorting_order, base0_nanpos


def rawemg_sortool(emgfile, orientation, base0_sorting_order, base0_nanpos):
    """
    Sort RAW_SIGNAL if base0_sorting_order and base0_nanpos are known.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    orientation : int
        Orientation in degree of the matrix (same as in OTBiolab).
        E.g. 180 corresponds to the matrix connection toward the user.
    base0_sorting_order : list
        Sorting order with base 0.
    base0_nanpos : int
        Position of the empty (np.nan) channel with base 0.

    Returns
    -------
    sorted_rawemg : pd.DataFrame
        Same as emgfile["RAW_SIGNAL"] but with a different columns order.
        Since DEMUSE file is supposed to be already sorted, if DEMUSE files are passesd,
        a deepcopy of emgfile['RAW_SIGNAL'] will be returned instead.

    Notes
    -----
    The returned file is called ``sorted_rawemg`` for convention.
    """

    rawemg = copy.deepcopy(emgfile["RAW_SIGNAL"])

    if emgfile["SOURCE"] == "OTB":
        # Don't sort the DEMUSE file that is supposed to be already sorted.
        # Sort the channels based on pre-specified order
        sorted_rawemg = rawemg.reindex(columns=base0_sorting_order)

        if orientation == 0 or orientation == 180:
            # Now rename columns considering the added column of np.nan
            newcol_list = list(sorted_rawemg.columns)
            for pos, col in enumerate(newcol_list):
                newcol_list[pos] = col + 1

            newcol_list[base0_nanpos] = 0

            # Convert columns name to int
            newcol_list = [int(i) for i in newcol_list]
            sorted_rawemg.columns = newcol_list

        return sorted_rawemg
    
    elif emgfile["SOURCE"] == "DEMUSE":
        print("DEMUSE file is supposed to be already sorted. A deepcopy of emgfile['RAW_SIGNAL'] has been returned instead")
        
        return rawemg


def sort_rawemg(emgfile, code="GR08MM1305", orientation=180):
    """
    Sort RAW_SIGNAL based on matrix type and orientation.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    code : str, default "GR08MM1305"
        The code of the matrix used.
    orientation : int, default 180
        Orientation in degree of the matrix (same as in OTBiolab).
        E.g. 180 corresponds to the matrix connection toward the user.

    Returns
    -------
    sorted_rawemg : dict
        A dict containing the sorted electrodes.
        Every key of the dictionary represents a different column of the matrix.
        Rows are stored in the dict as a pd.DataFrame.

    Notes
    -----
    The returned file is called ``sorted_rawemg`` for convention.
    Files coming from DEMUSE or OTBiolab+ have the same final format.
    """
    
    # Obtain sorting order and position of the missing channel
    base0_sorting_order, base0_nanpos = get_rawemg_sortingorder(
        code=code, orientation=orientation
    )

    # Once obtained the sorting order, sort the emgfile
    sorted_rawemg = rawemg_sortool(
        emgfile=emgfile,
        orientation=orientation,
        base0_sorting_order=base0_sorting_order,
        base0_nanpos=base0_nanpos,
    )

    if emgfile["SOURCE"] == "OTB":
        # Separate columns of the matrix
        if code == "GR08MM1305" or code == "GR04MM1305":
            if orientation == 0:
                sorted_rawemg = {
                    "col0":sorted_rawemg.loc[:,64:52],
                    "col1":sorted_rawemg.loc[:,39:51],
                    "col2":sorted_rawemg.loc[:,38:26],
                    "col3":sorted_rawemg.loc[:,13:25],
                    "col4":sorted_rawemg.loc[:,12:0]
                }
                # Then convert all the columns going backward to
                # obtain the same format of the DEMUSE file
                sorted_rawemg["col0"].columns = [*range(52,64+1)]
                sorted_rawemg["col2"].columns = [*range(26,38+1)]
                sorted_rawemg["col4"].columns = [*range(0,12+1)]
            
            elif orientation == 180:
                sorted_rawemg = {
                    "col0":sorted_rawemg.loc[:,0:12],
                    "col1":sorted_rawemg.loc[:,25:13],
                    "col2":sorted_rawemg.loc[:,26:38],
                    "col3":sorted_rawemg.loc[:,51:39],
                    "col4":sorted_rawemg.loc[:,52:64]
                }
                # Then convert all the columns going backward to
                # obtain the same format of the DEMUSE file
                sorted_rawemg["col1"].columns = [*range(13,25+1)]
                sorted_rawemg["col3"].columns = [*range(39,51+1)]

    elif emgfile["SOURCE"] == "DEMUSE":
        sorted_rawemg = {
            "col0":sorted_rawemg.loc[:,0:12],
            "col1":sorted_rawemg.loc[:,13:25],
            "col2":sorted_rawemg.loc[:,26:38],
            "col3":sorted_rawemg.loc[:,39:51],
            "col4":sorted_rawemg.loc[:,52:64]
        }

    return sorted_rawemg
