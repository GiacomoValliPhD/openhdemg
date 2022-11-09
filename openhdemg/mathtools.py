"""
This module contains all the mathematical functions that are necessary for the library.
"""

import copy
import pandas as pd
from scipy import signal
import numpy as np


def min_max_scaling(series_or_df):
    """
    Min-max scaling of pd.series or pd.dataframes.

    Min-max feature scaling is often simply referred to as normalization,
    which rescales the dataset feature to a range of 0 - 1.
    It's calculated by subtracting the feature's minimum value from the value
    and then dividing it by the difference between the maximum and minimum value.

    The formula looks like this: xnorm = x - xmin / xmax - xmin.

    Parameters
    ----------
    series_or_df : pd.Series or pd.DataFrame
        The min-max scaling is performed on the entire series, or to single columns in a pd.DataFrame.

    Returns
    -------
    object : pd.Series or pd.DataFrame
        The normalised pd.Series or pd.DataFrame (normalised by column).
    """

    # Create a deepcopy to avoid modifying the original series or df
    object = copy.deepcopy(series_or_df)

    # Automatically act depending on the object received
    if isinstance(object, pd.Series):
        return (object - object.min()) / (object.max() - object.min())

    elif isinstance(object, pd.DataFrame):
        for col in object.columns:
            object[col] = (object[col] - object[col].min()) / (
                object[col].max() - object[col].min()
            )

        return object

    else:
        raise Exception(
            f"series_or_df must a pandas series or a dataframe. {type(series_or_df)} was passed instead."
        )


def norm_twod_xcorr(df1, df2, mode="full"):
    """
    Normalised 2-dimensional cross-correlation of STAs of two MUS.

    Any pre-processing of the RAW_SIGNAL (i.e., normal, differential or double differential)
    can be passed as long as the two inputs have same shape.

    Parameters
    ----------
    df1 : pd.DataFrame
        A pd.DataFrame containing the STA of the first MU without np.nan column. 
    df2 : pd.DataFrame
        A pd.DataFrame containing the STA of the second MU without np.nan column.
    mode : str {"full", "valid", "same"}, default "full"
        A string indicating the size of the output:

        ``full``
           The output is the full discrete linear cross-correlation
           of the inputs. (Default)
        ``valid``
           The output consists only of those elements that do not
           rely on the zero-padding. In 'valid' mode, either `sta_mu1` or `sta_mu2`
           must be at least as large as the other in every dimension.
        ``same``
           The output is the same size as `in1`, centered
           with respect to the 'full' output.

    Returns
    -------
    normxcorr_df : pd.DataFrame
        The results of the normalised 2d cross-correlation.
    normxcorr_max : float
        The maximum value of the 2d cross-correlation.
    
    See also
    --------
    align_by_xcorr : to align the two STAs before calling norm_twod_xcorr.
    unpack_sta : for unpacking the sta dict in a pd.DataFrame
        before passing it to norm_twod_xcorr.
    pack_sta : for packing the sta pd.DataFrame in a dict where
        each matrix column corresponds to a dict key.
    """
    
    # Perform 2d xcorr
    correlate2d = signal.correlate2d(in1=df1, in2=df2, mode=mode)

    # Normalise the result of 2d xcorr for the different energy levels
    # MATLAB equivalent: acor_norm = xcorr(x,y)/sqrt(sum(abs(x).^2)*sum(abs(y).^2))
    absx = df1.abs()
    absy = df2.abs()
    expx = absx**2
    expy = absy**2
    sumx = expx.sum().sum()
    sumy = expy.sum().sum()
    acor_norm = correlate2d / np.sqrt(sumx * sumy)

    normxcorr_df = pd.DataFrame(acor_norm)
    normxcorr_max = normxcorr_df.max().max()

    return normxcorr_df, normxcorr_max
