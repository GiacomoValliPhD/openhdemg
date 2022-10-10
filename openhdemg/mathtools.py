"""
This module contains all the mathematical functions that are necessary for the library.
"""

import copy
import pandas as pd


def min_max_scaling(series_or_df):
    """
    Min-max scaling of pd.series or pd.dataframes.

    Min-max feature scaling is often simply referred to as normalization,
    which rescales the dataset feature to a range of 0 - 1.
    It's calculated by subtracting the feature's minimum value from the value
    and then dividing it by the difference between the maximum and minimum value.

    The formula looks like this: xnorm = x - xmin / xmax - xmin

    Pandas makes it quite easy to apply the normalization via the min-max feature scaling method.

    Parameters
    ----------
    series_or_df : pd.Series or pd.DataFrame
        The min-max scaling is performed on the entire series, or to single columns in a pd.DataFrame.

    Returns
    -------
    pd.Series or pd.DataFrame
        The function returns the normalised pd.Series or pd.DataFrame (normalised by column).
    """
    # Create a deepcopy to avoid modifying the original series or df
    object = copy.deepcopy(series_or_df)

    # Automatically act depending on the object received
    if isinstance(object, pd.Series):
        return (object - object.min()) / (object.max() - object.min())

    elif isinstance(object, pd.DataFrame):
        for col in object.columns:
            object[col] = (object[col] - object[col].min()) / (object[col].max() - object[col].min())

        return object

    else:
        raise Exception(
            f"series_or_df must a pandas series or a dataframe. {type(series_or_df)} was passed instead."
        )
