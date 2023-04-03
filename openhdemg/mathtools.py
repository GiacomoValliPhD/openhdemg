"""
This module contains all the mathematical functions that are necessary for the
library.
"""

import copy
import pandas as pd
import numpy as np
import numpy.polynomial.polynomial as poly
import math
from scipy import signal
from scipy.spatial.distance import cdist
from scipy.fftpack import fft
import sys


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


def compute_pnr(ipts, mupulses, fsamp):
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

    # According to Holobar 2014, the PNR is calculated as:
    # 10 * log10((mean of firings) / (mean of noise))
    # Where instants in the source of decomposition are classified as firings
    # or noise based on a threshold value named "Pi" or "r".
    #
    # Pi is calculated via a heuristic penalty funtion described in Holobar
    # 2012 as:
    # Pi = D · χ[3,50](D) + CoVIDI + CoVpIDI
    # Where:
    # D is the median of the low-pass filtered instantaneous motor unit
    # discharge rate (first-order Butterworth filter, cut-off frequency 3 Hz)
    # χ[3,50](D) stands for an indicator function that penalizes motor units
    # with filtered discharge rate D below 3 pulses per second (pps) or above
    # 50 pps:
    # χ[3,50](D) = 0 if D is between 3 and 50 or 1 if D is not between 3 and 50
    # Two separate coefficients of variation for inter-discharge interval (IDI)
    # calculated as standard deviation (SD) of IDI divided by the mean IDI,
    # are used. CoVIDI is the coefficient of variation for IDI of non-paired
    # MUs discharges only, whereas CoVpIDI is the coefficient of variation for
    # IDI of paired MUs discharges.
    # Holobar 2012 considered MUs discharges paired whenever the second
    # discharge was within 50 ms of the first.
    # Paired discharges are typical in pathological tremor and the use of both
    # CoVIDI and CoVpIDI accounts for this condition.
    #
    # However, this heuristic penalty function does not work in particular
    # types of contractions like explosive contractions (MUs discharge up to
    # 200 pps). Therefore, in this implementation of the PNR estimation we did
    # not use a penality based on MUs discharge rate and we estimate
    # Pi = CoVIDI + CoVpIDI
    # which remains valid also in tremor.

    # Calculate IDI
    # Compute differences between consecutive elements
    idi = np.diff(mupulses)

    # In order to increase robustness to outlier values, remove values greater
    # than mean + 3* STD in the idi array. Do not remove the values below
    # mean - 3* STD that could be common in tremor.
    # Compute upper bound for accepted range of values
    mean, std = np.mean(idi), np.std(idi)
    upper_bound = mean + 3*std

    # Remove values above upper bound
    idi = idi[idi <= upper_bound]

    # Divide the paired and non-paired IDIs before calculating specific CoV
    idinonp = idi[idi >= (fsamp * 0.05)]
    idip = idi[idi < (fsamp * 0.05)]

    CoVIDI = np.std(idinonp) / np.average(idinonp)
    if math.isnan(CoVIDI):
        CoVIDI = 0

    CoVpIDI = np.std(idip) / np.average(idip)
    if math.isnan(CoVpIDI):
        CoVpIDI = 0

    # Calculate Pi
    Pi = CoVIDI + CoVpIDI

    # Extract the source
    source = ipts.to_numpy()

    # Create clusters
    peak_cluster = source[source >= Pi]
    noise_cluster = source[source < Pi]

    peak_cluster = np.square(peak_cluster)
    noise_cluster = np.square(noise_cluster)

    # Calculate PNR
    pnr = 10 * np.log10((peak_cluster.mean() / noise_cluster.mean()))

    return pnr


def derivatives_beamforming(sig, row, teta): # TODO
    """
    Calculate devivatives for the beamforming technique.
    
    
    Calculate the first and second devivative of the mean square error for the beamforming technique with the first signal as reference.

    Parameters
    ----------
    sig : pd.Dataframe
        The source signal to be used for the calculation.
        Different channels should be organised in different rows.
    row : int
        The actual row in the iterative procedure.
    teta : float
        The value of teta. # TODO

    Returns
    -------
    de1, de2 : float
        The value of the first and second derivative.

    See also
    --------
    # TODO

    Examples
    --------
    # TODO
    """
    
    # TODO Use nympy arrays for performance instead of pd.Series

    # Define some necessary variables
    total_rows = len(sig)
    m = total_rows - 1
    total_columns =len(sig.columns)
    half_of_the_columns = pd.Series(np.arange((round(total_columns/2)))) + 1 # To overcome base 0
    
    # Create a custom position index with negative and mirrored values for index < row
    position = np.zeros(len(sig.index))
    position[0] = row + 1 # + 1 used to overcome base 0 here and following
    
    for i in range(1, row+1):
        position[i] = i-(row+1)
    
    for i in range(m-row):
        position[i+row+1] = i + 1
    
    position = np.delete(position, 0)

    # Shift sig and move row to sig[0]
    this_row = pd.DataFrame(sig.iloc[row]).transpose()
    sig = sig.drop(row).reset_index(drop=True)
    sig = pd.concat([this_row, sig], ignore_index=True)
    
    # Calculate fft row-wise
    sigfft = pd.DataFrame(0, index=np.arange(total_rows), columns=sig.columns)
    for i in range(total_rows):
        sigfft.iloc[i] = fft(sig.iloc[i].to_numpy())

    # Create the series used to store the terms of the derivatives
    term_de1 = pd.Series(0, np.arange(len(half_of_the_columns)))
    term_de2 = pd.Series(0, np.arange(len(half_of_the_columns)))
    term_de12 = pd.Series(0, np.arange(len(half_of_the_columns)))
    term_de22 = pd.Series(0, np.arange(len(half_of_the_columns)))

    # Calculate the first term of the first derivative
    for i in range(m):
        for u in range(i+1, m):
            
            s_fft = sigfft.iloc[i+1, list(half_of_the_columns)]
            s_conj = np.conj(sigfft.iloc[u+1, list(half_of_the_columns)])
            s_exp = np.exp(1j * 2 * np.pi * half_of_the_columns * (position[i]-position[u]) * teta / total_columns)
            s_last = 2 * np.pi * half_of_the_columns * (position[i]-position[u]) / total_columns

            s_fft  = s_fft.reset_index(drop=True)
            s_conj = s_conj.reset_index(drop=True)
            s_exp  = s_exp.reset_index(drop=True)
            s_last = s_last.reset_index(drop=True)

            image = np.imag(s_fft * s_conj * s_exp * s_last)
            
            term_de1 = term_de1-image

    term_de1= (term_de1*2) / (m**2)
    
    # Calculate the second term of the first derivative
    for i in range(m):
        
        s_fft = sigfft.iloc[i+1, list(half_of_the_columns)]
        s_exp = np.exp(1j * 2 * np.pi * half_of_the_columns * position[i] * teta / total_columns)
        s_last = 2 * np.pi * half_of_the_columns * position[i] / total_columns

        s_fft  = s_fft.reset_index(drop=True)
        s_exp  = s_exp.reset_index(drop=True)
        s_last = s_last.reset_index(drop=True)

        term_de2 = term_de2 + (s_fft * s_exp * s_last)
    
    s_conj = np.conj(sigfft.iloc[0, list(half_of_the_columns)])
    s_conj = s_conj.reset_index(drop=True)

    term_de2 = 2 * np.imag(s_conj * term_de2) / m
    
    # Calculate the first derivative
    de1 = 2 / total_columns * np.sum(term_de1 + term_de2)

    # Calculate the first term of the second derivative
    for i in range(m):
        for u in range(i+1, m):
            
            s_fft = sigfft.iloc[i+1, list(half_of_the_columns)]
            s_conj = np.conj(sigfft.iloc[u+1, list(half_of_the_columns)])
            s_exp = np.exp(1j * 2 * np.pi * half_of_the_columns * (position[i]-position[u]) * teta / total_columns)
            s_last = 2 * np.pi * half_of_the_columns * (position[i]-position[u]) / total_columns

            s_fft  = s_fft.reset_index(drop=True)
            s_conj = s_conj.reset_index(drop=True)
            s_exp  = s_exp.reset_index(drop=True)
            s_last = s_last.reset_index(drop=True)
            
            term_de12 = term_de12 - np.real(s_fft * s_conj * s_exp * (s_last**2))
            
    term_de12= (term_de12*2) / (m**2)

    # Calculate the second term of the second derivative
    for i in range(m):
        
        s_fft = sigfft.iloc[i+1, list(half_of_the_columns)]
        s_exp = np.exp(1j * 2 * np.pi * half_of_the_columns * position[i] * teta / total_columns)
        s_last = 2 * np.pi * half_of_the_columns * position[i] / total_columns

        s_fft  = s_fft.reset_index(drop=True)
        s_exp  = s_exp.reset_index(drop=True)
        s_last = s_last.reset_index(drop=True)

        term_de22 = term_de22 + (s_fft * s_exp * (s_last**2))
    
    s_conj = np.conj(sigfft.iloc[0, list(half_of_the_columns)])
    s_conj = s_conj.reset_index(drop=True)

    term_de22 = 2 * np.real(s_conj * term_de22) / m
    
    # Calculate the second derivative
    de2 = 2 / total_columns * np.sum(term_de12 + term_de22)
    
    return de1, de2


def mle_cv_est(sig, initial_teta, ied, fsamp):
    """
    Estimate CV via MLE.

    Estimate conduction velocity (CV) via maximum likelihood estimation.
    
    Parameters
    ----------
    sig : pd.Dataframe
        The source signal to be used for the calculation.
        Different channels should be organised in different columns,
        for coherence with the structure of emgfile["RAW_SIGNAL"].
    initial_teta : int
        The starting value teta.
    ied : int
        Interelectrode distance (mm).
    fsamp : int
        Sampling frequency (Hz).

    Returns
    -------
    cv : float
        Conduction velocity (M/s).
    teta : float
        The final value of teta.

    See also
    --------
    # TODO

    Examples
    --------
    # TODO
    """
    
    # Transpose the signal to represent each channel in a different row
    sig = sig.transpose()
    # Calculate ied in meters
    ied = ied / 1000

    # Assign the initial value of teta to t
    t = initial_teta
    # Set teta to 10 just to start the while loop
    teta = 10
    trial = 0
    eps = sys.float_info.epsilon

    while abs(teta - t) >= 5e-5 and trial < 30:
        trial = trial+1
        teta = t
        # Initialize the first and second derivatives
        de1 = 0
        de2 = 0

        # Calculate the first and second derivatives
        for row in range(len(sig)):
            de1t, de2t = derivatives_beamforming(sig=sig, row=row, teta=teta)
            de1 = de1 + de1t + eps
            de2 = de2 + de2t + eps

        # Newton's criteria
        if de2 > 0:
            # calculate step size using Newton's method
            u = -de1 / de2
            # if the step size is too large, limit it to 0.5
            if abs(u) > 0.5:
                u = -0.5 * abs(de1) / de1
            
        else:
            u = -0.5 * abs(de1) / de1
        
        # Update t using step size and teta
        t = teta + u

    cv = ied / (teta / fsamp)
    
    return cv, teta


def find_teta(sig1, sig2, ied, fsamp): # TODO
    """
    Find the starting value for teta.

    It is important to don't fix teta and use a non-fixed starting point for the CV algorithm.

    Parameters
    ----------
    sig1, sig2 : pd.Series
        The two signals based on which to calculate teta.
        These must be pd.Series, i.e., 1-dimensional data structures.
    ied : int
        Interelectrode distance (mm).
    fsamp : int
        Sampling frequency (Hz).
    
    Returns
    -------
    teta : int
        The starting value teta.

    See also
    --------
    # TODO

    Examples
    --------
    # TODO
    """

    # Define an arbitrary range for possible CV values (slightly larger than the physiological range) based on which to calculate teta.
    min_cv = 1
    max_cv = 10
    teta_min = math.floor(ied / max_cv * fsamp)
    teta_max = math.ceil(ied / min_cv * fsamp)

    # Work with numpy arrays for better performance
    sig1 = sig1.to_numpy()
    sig2 = sig2.to_numpy()

    # Verify that the input is a 1D array. If not, it will affect the calculation of corrloc.
    if sig1.ndim != 1:
        raise ValueError("sig1 is not 1 dimensional")
    if sig2.ndim != 1:
        raise ValueError("sig2 is not 1 dimesional")

    delay = np.arange(teta_min, teta_max+1)
    corrloc = np.zeros(len(delay))
    for idx, i in enumerate(delay):
        sig1_tosum = sig1[:len(sig1)-i]
        sig2_tosum = sig2[i:]
        
        corrloc[idx-teta_min+1] = np.sum(sig1_tosum * sig2_tosum) 
        
    pos = corrloc.argmax() + 1 # To overcome base 0 and prevent beta from beeing 0

    if pos > 1 and pos < len(delay):
        x = delay[pos-2 : pos+1]
        y = corrloc[pos-2 : pos+1]

        coefs = poly.polyfit(x=x, y=y, deg=2)
        # The polyfit function originally returns flipped coefficients
        coefs = np.flip(coefs)

        teta = -coefs[1] / (2 * coefs[0])

    else:
        teta = pos

    return teta
