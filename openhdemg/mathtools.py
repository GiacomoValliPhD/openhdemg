"""
This module contains all the mathematical functions that are necessary for the
library.
"""

import copy
import pandas as pd
from scipy import signal
import numpy as np
from scipy.spatial.distance import cdist


def min_max_scaling(series_or_df):
    """
    Min-max scaling of pd.series or pd.dataframes.

    Min-max feature scaling is often simply referred to as normalization,
    which rescales the dataset feature to a range of 0 - 1.
    It's calculated by subtracting the feature's minimum value from the value
    and then dividing it by the difference between the maximum and minimum 
    value.

    The formula looks like this: xnorm = x - xmin / xmax - xmin.

    Parameters
    ----------
    series_or_df : pd.Series or pd.DataFrame
        The min-max scaling is performed for the entire series,
        or for single columns in a pd.DataFrame.

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
        raise TypeError(
            f"series_or_df must a pandas series or a dataframe. {type(series_or_df)} was passed instead."
        )


def norm_twod_xcorr(df1, df2, mode="full"):
    """
    Normalised 2-dimensional cross-correlation of STAs of two MUS.

    Any pre-processing of the RAW_SIGNAL (i.e., normal, differential or double
    differential) can be passed as long as the two inputs have same shape.

    Parameters
    ----------
    df1 : pd.DataFrame
        A pd.DataFrame containing the STA of the first MU without np.nan 
        column.
    df2 : pd.DataFrame
        A pd.DataFrame containing the STA of the second MU without np.nan
        column.
    mode : str {"full", "valid", "same"}, default "full"
        A string indicating the size of the output:

        ``full``
           The output is the full discrete linear cross-correlation
           of the inputs. (Default)
        ``valid``
           The output consists only of those elements that do not
           rely on the zero-padding. In 'valid' mode, either `sta_mu1` or
           `sta_mu2` must be at least as large as the other in every dimension.
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

    Examples
    --------
    Full steps to pass two dataframes to norm_twod_xcorr from the same EMG
    file.
    1 Load the EMG file and band-pass filter the raw EMG signal
    2 Sort the matrix channels and compute the spike-triggered average
    3 Extract the STA of the MUs of interest from all the STAs
    4 Unpack the STAs of single MUs and remove np.nan to pas them to
        norm_twod_xcorr
    5 Compute 2dxcorr to identify a common lag/delay

    >>> import openhdemg as emg
    >>> emgfile = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> emgfile = emg.filter_rawemg(emgfile, order=2, lowcut=20, highcut=500)
    >>> sorted_rawemg = emg.sort_rawemg(emgfile, code="GR08MM1305", orientation=180)
    >>> sta = emg.sta(emgfile, sorted_rawemg, firings=[0, 50], timewindow=100)
    >>> mu0 = 0
    >>> mu1 = 1
    >>> sta_mu1 = sta[mu0]
    >>> sta_mu2 = sta[mu1]
    >>> df1 = emg.unpack_sta(sta_mu1)
    >>> no_nan_sta1 = df1.dropna(axis=1, inplace=False)
    >>> df2 = emg.unpack_sta(sta_mu2)
    >>> no_nan_sta2 = df2.dropna(axis=1, inplace=False)
    >>> normxcorr_df, normxcorr_max = emg.norm_twod_xcorr(no_nan_sta1, no_nan_sta2)
    >>> normxcorr_max
    0.7241553627564273
    >>> normxcorr_df
                0             1             2               125       126
    0   -0.000002 -1.467778e-05 -3.013564e-05 ... -1.052780e-06  0.000001
    1   -0.000004 -2.818055e-05 -6.024427e-05 ... -4.452469e-06  0.000001
    2   -0.000007 -4.192479e-05 -9.223725e-05 ... -1.549197e-05 -0.000002
    3   -0.000009 -5.071660e-05 -1.174545e-04 ... -3.078518e-05 -0.000007
    4   -0.000007 -4.841255e-05 -1.239106e-04 ... -4.232094e-05 -0.000012
    ..        ...           ...           ... ...           ...       ...
    402  0.000005  1.641773e-05  3.994943e-05 ...  8.170792e-07 -0.000006
    403 -0.000001  4.535878e-06  1.858700e-05 ...  2.087135e-06 -0.000003
    404 -0.000004 -1.241530e-06  5.704194e-06 ...  1.027966e-05  0.000002
    405 -0.000004 -1.693078e-06  1.054646e-06 ...  1.811828e-05  0.000007
    406 -0.000002 -2.473282e-07  6.006046e-07 ...  1.605406e-05  0.000007
    """

    # Perform 2d xcorr
    correlate2d = signal.correlate2d(in1=df1, in2=df2, mode=mode)

    # Normalise the result of 2d xcorr for the different energy levels
    # MATLAB equivalent:
    # acor_norm = xcorr(x,y)/sqrt(sum(abs(x).^2)*sum(abs(y).^2))
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


def compute_sil(ipts, mupulses):  # TODO _NEXT_ add refs in docs when necessary
    """
    Calculate the Silhouette score for a single MU.

    The SIL is defined as the difference between the within-cluster sums of
    point-to-centroid distances and the same measure calculated between clusters.
    The measure was normalized dividing by the maximum of the two values.

    Parameters
    ----------
    ipts : pd.Series
        The source of decomposition (or pulse train, IPTS[mu]) of the MU of
        interest.
    mupulses : ndarray
        The time of firing (MUPULSES[mu]) of the MU of interest.

    Returns
    -------
    sil : float
        The SIL score.

    See also
    --------
    compute_pnr : to calculate the Pulse to Noise ratio of a single MU.
    """

    # Extract source and peaks and align source and peaks based on IPTS
    # index to avoid errors in the resized files.
    source = ipts.to_numpy()
    peaks_idxs = mupulses - ipts.index[0]

    # Create clusters
    peak_cluster = source[peaks_idxs]
    noise_cluster = np.delete(source, peaks_idxs)

    # Create centroids for each cluster
    peak_centroid = peak_cluster.mean()
    noise_centroid = noise_cluster.mean()

    # Calculate within-cluster sums of point-to-centroid distances using the
    # squared Euclidean distance metric. It is defined as the sum of the
    # squares of the differences between the corresponding elements of the two
    # vectors.
    intra_sums = cdist(
        peak_cluster.reshape(-1, 1),
        peak_centroid.reshape(-1, 1),
        metric="sqeuclidean",
    ).sum()

    # Calculate between-cluster sums of point-to-centroid distances
    inter_sums = cdist(
        peak_cluster.reshape(-1, 1),
        noise_centroid.reshape(-1, 1),
        metric="sqeuclidean",
    ).sum()

    # Calculate silhouette coefficient
    sil = (inter_sums - intra_sums) / max(intra_sums, inter_sums)

    return sil


def compute_pnr(ipts, mupulses):  # TODO correct the function
    """
    Calculate the pulse to noise ratio for a single MU.

    Parameters
    ----------
    ipts : pd.Series
        The source of decomposition (or pulse train, IPTS[mu]) of the MU of
        interest.
    mupulses : ndarray
        The time of firing (MUPULSES[mu]) of the MU of interest.

    Returns
    -------
    pnr : float
        The PNR in decibels.

    See also
    --------
    compute_sil : to calculate the Silhouette score for a single MU.
    """

    # Extract source and peaks and align source and peaks based on IPTS
    # index to avoid errors in the resized files.
    source = ipts.to_numpy()
    peaks_idxs = mupulses - ipts.index[0]

    # Create clusters
    peak_cluster = source[peaks_idxs]
    noise_cluster = np.delete(source, peaks_idxs)

    # Calculate silhouette coefficient
    pnr = 10*np.log((peak_cluster.mean() / noise_cluster.std()))

    return pnr
