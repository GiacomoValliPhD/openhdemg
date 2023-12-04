## What is the emgfile

The `emgfile` is the basic data structure of the *openhdemg* framework. In practical terms, it is a Python object containing all the information of the decomposed HD-EMG file loaded in the [working environment](setup_working_env.md) via the dedicated *openhdemg* functions.

For example:

```Python
# Import the library with the short name 'emg'
import openhdemg.library as emg

# Load the sample file and assign it to the emgfile object
emgfile = emg.emg_from_samplefile()
```

Loads the decomposed sample file provided with *openhdemg* and assigns its content to the object `emgfile`.

## Structure of the emgfile

The `emgfile` has a simple structure. Indeed, it is a Python dictionary with keys:

```Python
# Import the library with the short name 'emg'
import openhdemg.library as emg

# Load the sample file and assign it to the emgfile object
emgfile = emg.emg_from_samplefile()

# Visualise the type of the emgfile
print(type(emgfile))

"""Output
<class 'dict'>
"""

# Visualise the keys of the emgfile dictionary
print(emgfile.keys())

"""Output
dict_keys(['SOURCE', 'FILENAME', 'RAW_SIGNAL', 'REF_SIGNAL', 'ACCURACY', 'IPTS', 'MUPULSES', 'FSAMP', 'IED', 'EMG_LENGTH', 'NUMBER_OF_MUS', 'BINARY_MUS_FIRING', 'EXTRAS'])
"""
```

That means that the `emgfile` contains the following keys (or variables, in simpler terms):

- "SOURCE" : source of the file (i.e., "CUSTOMCSV", "DEMUSE", "OTB", "DELSYS")
- "FILENAME" : the name of the original file
- "RAW_SIGNAL" : the raw EMG signal
- "REF_SIGNAL" : the reference signal
- "ACCURACY" : accuracy score (depending on source file type)
- "IPTS" : pulse train (decomposed source)
- "MUPULSES" : instants of firing
- "FSAMP" : sampling frequency
- "IED" : interelectrode distance
- "EMG_LENGTH" : length of the emg file (in samples)
- "NUMBER_OF_MUS" : total number of MUs
- "BINARY_MUS_FIRING" : binary representation of MUs firings
- "EXTRAS" : additional custom values

Each key has a specific content and structure that will be presented in the next code block.

It must be noted that some of these keys might be empty (e.g., absence of a reference signal) and, therefore, the specific content of each key must be assessed from case to case. This can be simply done taking advantage of the info class:

```Python
# Import the library with the short name 'emg'
import openhdemg.library as emg

# Load the sample file and assign it to the emgfile object
emgfile = emg.emg_from_samplefile()

# Obtain info on the content of the emgfile
info = emg.info()
info.data(emgfile)

"""Output
Data structure of the emgfile
-----------------------------

emgfile type is:
<class 'dict'>

emgfile keys are:
dict_keys(['SOURCE', 'FILENAME', 'RAW_SIGNAL', 'REF_SIGNAL', 'ACCURACY', 'IPTS', 'MUPULSES', 'FSAMP', 'IED', 'EMG_LENGTH', 'NUMBER_OF_MUS', 'BINARY_MUS_FIRING', 'EXTRAS'])

Any key can be acced as emgfile[key].

emgfile['SOURCE'] is a <class 'str'> of value:
OTB

emgfile['FILENAME'] is a <class 'str'> of value:
otb_testfile.mat

MUST NOTE: emgfile from OTB has 64 channels, from DEMUSE 65 (includes empty channel).
emgfile['RAW_SIGNAL'] is a <class 'pandas.core.frame.DataFrame'> of value:
              0          1          2          3          4          5          6          7          8   ...         55         56         57         58         59         60         61         62         63
0      10.172526   5.086263  12.715657  11.189778   9.155273   8.138021   9.155273  13.224284   2.034505  ...   7.120768   6.612142  10.172526   8.138021  10.681152   2.034505  14.750163   4.577637  11.698405
1      14.750163   8.138021  12.715657  12.715657  10.681152   6.612142  13.732910  16.276041   3.051758  ...   4.577637   3.560384  11.698405   7.120768  10.681152   0.508626  10.681152   4.069010  11.698405
2       6.103516   1.017253   6.103516  15.767415   6.103516   3.051758   6.103516  11.698405   2.034505  ...   1.525879   1.525879   3.560384  -1.017253   4.069010  -4.577637   8.138021  -1.525879   5.086263
3      -3.051758  -7.120768  -3.051758   4.577637  -4.069010  -8.138021  -2.543132   2.543132  -7.120768  ...  -8.646647  -9.155273  -3.560384  -9.155273  -6.103516 -13.732910  -1.017253 -11.698405  -2.543132
4     -11.189778 -15.767415 -15.767415  -5.086263 -11.698405 -13.732910  -7.120768  -3.560384 -12.207031  ... -15.767415 -18.310547 -12.207031 -12.715657 -11.189778 -17.293295  -8.646647 -17.293295 -11.189778
...          ...        ...        ...        ...        ...        ...        ...        ...        ...  ...        ...        ...        ...        ...        ...        ...        ...        ...        ...
66555  11.189778  17.801920  16.276041  17.801920   2.034505  22.379557   8.646647  14.750163  14.750163  ...  -2.034505   0.508626   2.034505   2.034505  13.224284   0.000000  10.172526  10.172526  17.801920
66556  12.715657  22.888184  21.362305  20.853678  10.172526  26.448568  12.207031  19.836426  16.276041  ...   2.034505   7.120768   4.577637   8.646647  14.241536   5.086263  18.819174  16.276041  16.276041
66557   6.103516   7.120768  12.207031  12.715657   0.508626  16.276041   3.051758   9.663899   5.594889  ...  -5.594889  -1.525879  -6.103516  -1.525879   6.103516  -1.525879   7.629395   8.646647   8.646647
66558  -9.663899  -9.663899  -7.120768  -7.629395 -14.241536  -1.017253 -14.750163  -7.629395 -10.681152  ... -23.905436 -17.801920 -22.888184 -20.853678 -10.681152 -17.801920 -13.224284  -8.646647  -9.155273
66559   0.508626   1.017253   0.000000   4.577637  -2.543132   6.612142  -3.051758   1.525879  -2.034505  ... -12.715657  -6.612142 -14.750163 -10.172526   0.000000  -6.103516   1.017253  -3.051758  -2.543132

[66560 rows x 64 columns]

emgfile['REF_SIGNAL'] is a <class 'pandas.core.frame.DataFrame'> of value:
              0
0      1.640534
1      1.660370
2      1.700043
3      1.719879
4      1.739716
...         ...
66555  1.462006
66556  1.481842
66557  1.501679
66558  1.481842
66559  1.481842

[66560 rows x 1 columns]

emgfile['ACCURACY'] is a <class 'pandas.core.frame.DataFrame'> of value:
          0
0  0.879079
1  0.955819
2  0.917190
3  0.899082
4  0.919601

emgfile['IPTS'] is a <class 'pandas.core.frame.DataFrame'> of value:
                  0             1         2         3         4
0     -1.208628e-04  3.242122e-09  0.000004  0.000186  0.000038
1     -4.316778e-04 -8.801236e-05 -0.000053  0.000095 -0.000063
2     -6.112677e-06 -1.158515e-04  0.000619 -0.000379  0.000035
3      5.843681e-05 -1.308242e-05 -0.000033 -0.000001 -0.000168
4      4.365258e-06  5.634868e-05 -0.000423 -0.000112  0.000001
...             ...           ...       ...       ...       ...
66555 -6.366898e-08  0.000000e+00  0.000000  0.000000  0.000000
66556 -5.846209e-05  0.000000e+00  0.000000  0.000000  0.000000
66557 -4.853265e-05  0.000000e+00  0.000000  0.000000  0.000000
66558  1.100347e-05  0.000000e+00  0.000000  0.000000  0.000000
66559  1.217465e-04  0.000000e+00  0.000000  0.000000  0.000000

[66560 rows x 5 columns]

emgfile['MUPULSES'] is a <class 'list'> of length depending on total MUs number.
MUPULSES for each MU can be accessed as emgfile['MUPULSES'][MUnumber].

emgfile['MUPULSES'][0] is a <class 'numpy.ndarray'> of value:
[ 4990  6659  8310  8581  9424  9662  9905 10046 10200 10543 10762 11179
 11469 11743 11973 12243 12580 12795 13038 13258 13396 13642 13890 14161
 14357 14672 14975 15250 15564 15920 16281 16572 16837 17182 17321 17634
 17973 18999 19388 19906 20178 20331 20523 20797 21020 21321 21705 21863
 22190 22283 22656 23297 23397 23445 23598 24045 24206 24430 24678 24764
 24982 25095 25277 25939 26581 26942 27652 28303 28515 28602 28893 29136
 29363 30399 30604 31277 32005 32227 32780 33030 33255 33550 34239 34889
 35261 37394 37932 38439 39061 39564 40393 41056 41919 43357 43742 44039
 44335 44721 45182 45913 46083 46745 47076 47343 47635 47976 48147 48578
 48880 49428 49742 49887 50516 50850 50957 51194 51350 51678 52110 52892
 53161 53390 53795 54154 54386 54823 55032 55283 55653 56026 56282 56538
 56931 57578 57871 58429 59077]

emgfile['FSAMP'] is a <class 'float'> of value:
2048.0

emgfile['IED'] is a <class 'float'> of value:
8.0

emgfile['EMG_LENGTH'] is a <class 'int'> of value:
66560

emgfile['NUMBER_OF_MUS'] is a <class 'int'> of value:
5

emgfile['BINARY_MUS_FIRING'] is a <class 'pandas.core.frame.DataFrame'> of value:
         0    1    2    3    4
0      0.0  0.0  0.0  0.0  0.0
1      0.0  0.0  0.0  0.0  0.0
2      0.0  0.0  0.0  0.0  0.0
3      0.0  0.0  0.0  0.0  0.0
4      0.0  0.0  0.0  0.0  0.0
...    ...  ...  ...  ...  ...
66555  0.0  0.0  0.0  0.0  0.0
66556  0.0  0.0  0.0  0.0  0.0
66557  0.0  0.0  0.0  0.0  0.0
66558  0.0  0.0  0.0  0.0  0.0
66559  0.0  0.0  0.0  0.0  0.0

[66560 rows x 5 columns]

emgfile['EXTRAS'] is a <class 'pandas.core.frame.DataFrame'> of value:
Empty DataFrame
Columns: [0]
Index: []
"""
```

As you can see, `info.data(emgfile)` provides you with all the information regarding the content of the `emgfile`, on how it is structured and on how each element can be accessed. This information is crucial to interact with the `emgfile` and, understanding its structure, is fundamental to performed advanced customisation of the functions and to exploit the full flexibility/customisability of the *openhdemg* framework.

Please take some time to learn this!

## Alternative structures of the emgfile

At the moment, the only alternative to the basic `emgfile` structure is reserved for the loading of those files containing only the reference signal. This can be, for example, the case of the force signal used to calculate the maximum voluntary contraction (MVC) value.

In this case, the `emg_refsig` is a Python dictionary with the following keys:

- "SOURCE": source of the file (i.e., "CUSTOMCSV_REFSIG", "OTB_REFSIG", "DELSYS_REFSIG")
- "FSAMP": sampling frequency
- "REF_SIGNAL": the reference signal
- "EXTRAS" : additional custom values

## Modify the emgfile to fit your needs

This is a fundamental part of this tutorial. You can modify the `emgfile` as you wish, but there are 2 simple rules that must be followed to allow a seamless integration with the *openhdemg* functions.

1. Do not alter the `emgfile` keys. You should not add or remove keys and you should not alter the data type under each key. If you need to do so, please remember that some of the built-in functions might not work anymore and you might encounter unexpected errors.
2. Preserve data structures. If there is missing data you should fill the `emgfile` keys with the original data structure. The original data structure is the one presented in section [Structure of the emgfile](#structure-of-the-emgfile). For example, the reference signal is by default contained in a pd.DataFrame. Therefore, if the reference signal is absent, the dict key "REF_SIGNAL" should contain an empty pd.DataFrame.

To modify the `emgfile` you can simply act as for modifying any Python dictionary:

```Python
# Import the necessary libraries
import openhdemg.library as emg

import pandas as pd
import numpy as np

# Load the sample file and assign it to the emgfile object
emgfile = emg.emg_from_samplefile()

# Visualise the keys of the emgfile dictionary
print(emgfile.keys())

"""Output
dict_keys(['SOURCE', 'FILENAME', 'RAW_SIGNAL', 'REF_SIGNAL', 'ACCURACY', 'IPTS', 'MUPULSES', 'FSAMP', 'IED', 'EMG_LENGTH', 'NUMBER_OF_MUS', 'BINARY_MUS_FIRING', 'EXTRAS'])
"""

# Visualise the original data structure contained in the 'REF_SIGNAL' key
print(type(emgfile['REF_SIGNAL']))

"""Output
<class 'pandas.core.frame.DataFrame'>
"""

# Replace the current 'REF_SIGNAL' with a random reference signal.
random_data = np.random.randint(0 ,20, size=(emgfile['EMG_LENGTH'], 1))
rand_ref = pd.DataFrame(random_data, columns=[0])
emgfile['REF_SIGNAL'] = rand_ref

print(emgfile['REF_SIGNAL'])

"""Output
        0
0       2
1      15
2      13
3      18
4       3
...    ..
66555  13
66556  11
66557  13
66558   1
66559   7
"""
```

## Create your own emgfile

*openhdemg* offers a number of built-in functions to load the data from different sources. However, there might be special circumnstances that require more flexibility. In this case, the user can create custom functions to load any type of decomposed HD-EMG files. However, in order to interact with the *openhdemg* functions, the `emgfile` loaded with any custom function must respect the original [structure](#structure-of-the-emgfile).

In case your decomposed HD-EMG file does not contain a specific variable, you should mantain the original `emgfile` keys and the original data structure, although empty.


## More questions?

We hope that this tutorial was useful. If you need any additional information, do not hesitate to read the answers or ask a question in the [*openhdemg* discussion section](https://github.com/GiacomoValliPhD/openhdemg/discussions){:target="_blank"}. If you are not familiar with GitHub discussions, please read this [post](https://github.com/GiacomoValliPhD/openhdemg/discussions/42){:target="_blank"}. This will allow the *openhdemg* community to answer your questions.