""" 
This module contains informations about the electrodes sold by OTB and commonly used for HD-EMG recordings.
Functions to sort the electrode position are also included. These functions are used only for the OTBiolab+
software since DEMUSE already provides sorted channels.
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
# - GR08MM1305(180)

# TODO other orientations and matrices
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
        Position of the empty (np.nan) channel.

    Notes
    -----
    The returned files are called ``base0_sorting_order, base0_nanpos``.
    """

    if code == "GR08MM1305" and orientation == 180:
        """
        MUST REMEMBER: python loops from 0 and the emg channels start from 0
        but the channel order reflects the real channels and starts from 1!
        This order is for the user, while the script uses the base0_sorting_order.

        base0_sorting_order provides the sorting order while
        base0_nanpos indicates the position of the empty (np.nan) channel.
        """

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
        pass  # TODO add other electrodes and orientations

    return base0_sorting_order, base0_nanpos


def rawemg_sortool(emgfile, base0_sorting_order, base0_nanpos):
    """
    Sort RAW_SIGNAL if base0_sorting_order and base0_nanpos are known.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    base0_sorting_order : list
        Sorting order with base 0.
    base0_nanpos : int
        Position of the empty (np.nan) channel.

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

        # Now rename columns considering the added column of np.nan
        newcol_list = list(sorted_rawemg.columns)
        for pos, col in enumerate(newcol_list):
            if col >= base0_nanpos:
                newcol_list[pos] = col + 1
        
        newcol_list[base0_nanpos] = base0_nanpos

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
    sorted_rawemg : pd.DataFrame
        Same as emgfile["RAW_SIGNAL"] but with a different columns order.
        Since DEMUSE file is supposed to be already sorted, if DEMUSE files are passesd,
        a deepcopy of emgfile['RAW_SIGNAL'] will be returned instead.

    Notes
    -----
    The returned file is called ``sorted_rawemg`` for convention.
    """
    
    # Obtain sorting order and position of the missing channel
    base0_sorting_order, base0_nanpos = get_rawemg_sortingorder(
        code=code, orientation=orientation
    )

    # Once obtained the sorting order, sort the emgfile
    sorted_rawemg = rawemg_sortool(
        emgfile=emgfile,
        base0_sorting_order=base0_sorting_order,
        base0_nanpos=base0_nanpos,
    )

    if code == "GR08MM1305":
        # Separate columns of the matrix
        if emgfile["SOURCE"] == "OTB":
            sorted_rawemg = {
                "col0":sorted_rawemg.loc[:,0:12],
                "col1":sorted_rawemg.loc[:,25:13],
                "col2":sorted_rawemg.loc[:,26:38],
                "col3":sorted_rawemg.loc[:,51:39],
                "col4":sorted_rawemg.loc[:,52:64]
            }
        elif emgfile["SOURCE"] == "DEMUSE":
            sorted_rawemg = {
                "col0":sorted_rawemg.loc[:,0:12],
                "col1":sorted_rawemg.loc[:,13:25],
                "col2":sorted_rawemg.loc[:,26:38],
                "col3":sorted_rawemg.loc[:,39:51],
                "col4":sorted_rawemg.loc[:,52:64]
            }

    return sorted_rawemg
