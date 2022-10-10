""" 
This file contains informations about the electrodes sold by OTB and commonly used for HD-EMG recordings.
Info on how to sort the electrode positions is also included.
"""

import numpy as np
import pandas as pd

# Tuple of electrodes name
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
>>> OTBelectrodes_tuple
('GR04MM1305', 'GR08MM1305', 'GR100ML1305', 'GR10MM0804', 'GR10MM0808', 'HD04MM1305', 'HD08MM1305', 'HD10MM0804', 'HD10MM0808')
"""

# Interelectrode distance for each matrix
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
>>> OTBelectrodes_ied
{'GR04MM1305': 4, 'GR08MM1305': 8, 'GR100ML1305': 2.5, 'GR10MM0804': 10, 'GR10MM0808': 10, 'HD04MM1305': 4, 'HD08MM1305': 8, 'HD10MM0804': 10, 'HD10MM0808': 10}
"""

# Number of electrodes for each matrix
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

# ---------------------------------------------------------------------
# Define the order to sort the electrodes of different matrices.
"""
MUST REMEMBER: python loops from 0 and the emg channels start from 0
but this channel order reflects the real channels and starts from 1!

Sorting orders have been implemented for:
- GR08MM1305
"""

# Build a pd.DataFrame to sort the GR08MM1305 matrix channels
r1 =  [np.nan, 25, 26, 51, 52]
r2 =  [     1, 24, 27, 50, 53]
r3 =  [     2, 23, 28, 49, 54]
r4 =  [     3, 22, 29, 48, 55]
r5 =  [     4, 21, 30, 47, 56]
r6 =  [     5, 20, 31, 46, 57]
r7 =  [     6, 19, 32, 45, 58]
r8 =  [     7, 18, 33, 44, 59]
r9 =  [     8, 17, 34, 43, 60]
r10 = [     9, 16, 35, 42, 61]
r11 = [    10, 15, 36, 41, 62]
r12 = [    11, 14, 37, 40, 63]
r13 = [    12, 13, 38, 39, 64]

rlist = [r1, r2, r3, r4, r5, r6, r7, r8, r9, r10, r11, r12, r13]

channelOrder_GR08MM1305 = pd.DataFrame(rlist)
"""
channelOrder_GR08MM1305

       0   1   2   3   4
0    NaN  25  26  51  52
1    1.0  24  27  50  53
2    2.0  23  28  49  54
3    3.0  22  29  48  55
4    4.0  21  30  47  56
5    5.0  20  31  46  57
6    6.0  19  32  45  58
7    7.0  18  33  44  59
8    8.0  17  34  43  60
9    9.0  16  35  42  61
10  10.0  15  36  41  62
11  11.0  14  37  40  63
12  12.0  13  38  39  64
"""
