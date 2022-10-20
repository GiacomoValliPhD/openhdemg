"""
This module contains all the mathematical functions that are necessary for the library.
"""

import copy
import pandas as pd
from functools import reduce
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


def norm_twod_xcorr(sta_mu1, sta_mu2):
    """
    Normalised cross-correlation of two 2-dimensional STA matrices.

    Any pre-processing of the RAW_SIGNAL (i.e., normal, differential or double differential)
    can be passed as long as the two inputs have same shape.

    Parameters
    ----------
    sta_mu1: dict
        A dictionary containing the STA of the first MU.
    sta_mu2 : dict
        A dictionary containing the STA of the second MU.

    Returns
    -------
    normxcorr_df : pd.DataFrame
        The results of the normalised 2d cross-correlation.
    normxcorr_max: float
        The maximum value of the 2d cross-correlation.
    
    """

    # Build a common pd.DataFrame from the sta dict containing all the channels
    dfs = [
        sta_mu1["col0"],
        sta_mu1["col1"],
        sta_mu1["col2"],
        sta_mu1["col3"],
        sta_mu1["col4"],
    ]
    df1 = reduce(
        lambda left, right: pd.merge(left, right, left_index=True, right_index=True),
        dfs,
    )
    df1.dropna(axis=1, inplace=True)

    dfs = [
        sta_mu2["col0"],
        sta_mu2["col1"],
        sta_mu2["col2"],
        sta_mu2["col3"],
        sta_mu2["col4"],
    ]
    df2 = reduce(
        lambda left, right: pd.merge(left, right, left_index=True, right_index=True),
        dfs,
    )
    df2.dropna(axis=1, inplace=True)

    # Perform 2d xcorr
    correlate2d = signal.correlate2d(in1=df1, in2=df2)#TODO check inputs eg.mode

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
