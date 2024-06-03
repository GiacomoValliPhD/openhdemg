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


def norm_xcorr(sig1, sig2, out="both"):
    """
    Normalized cross-correlation of 2 signals.

    Parameters
    ----------
    sig1, sig2 : pd.Series or np.ndarray
        The two signals to correlate.
        These signals must be 1-dimensional and of same length.
    out : str {"both", "max"}, default "both"
        A string indicating the output value:

        ``both``
           The output is the greatest positive or negative cross-correlation
           value.

        ``max``
           The output is the maximum cross-correlation value.

    Returns
    -------
    xcc : float
        The cross-correlation value depending on "out".

    See also
    --------
    - norm_twod_xcorr : Normalised 2-dimensional cross-correlation of STAs of
        two MUS.
    """

    # Convert input to ndarray
    sig1 = np.asarray(sig1)
    sig2 = np.asarray(sig2)

    # Implementation corresponding to:
    # MATLAB => xcorr(a, b, 'normalized')
    # From:
    # https://stackoverflow.com/questions/53436231/normalized-cross-correlation-in-python
    norm_a = np.linalg.norm(sig1)
    a = sig1 / norm_a
    norm_b = np.linalg.norm(sig2)
    b = sig2 / norm_b
    c = np.correlate(a, b, mode='full')

    # `numpy.correlate` may perform slowly in large arrays (i.e. n = 1e5)
    # because it does not use the FFT to compute the convolution; in that case,
    # `scipy.signal.correlate` might be preferable. No need in our use case.

    # Calculate xcc based on out
    if out == "max":
        xcc = np.max(c)
    else:
        max_abs_index = np.abs(c).argmax()
        xcc = np.abs(c[max_abs_index]) * np.sign(c[max_abs_index])

    return xcc


def norm_twod_xcorr(df1, df2, mode="full"):
    """
    Normalised 2-dimensional cross-correlation of 2.

    The two inputs must have same shape.
    When this function is used to cross-correlate MUAPs obtained via STA,
    df1 and df2 should contain the unpacked STA of the first and second MU,
    respectively, without np.nan columns.

    Parameters
    ----------
    df1 : pd.DataFrame
        A pd.DataFrame containing the first 2-dimensional signal.
    df2 : pd.DataFrame
        A pd.DataFrame containing the second 2-dimensional signal.
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
    - align_by_xcorr : to align the two STAs before calling norm_twod_xcorr.
    - unpack_sta : for unpacking the sta dict in a pd.DataFrame
        before passing it to norm_twod_xcorr.
    - pack_sta : for packing the sta pd.DataFrame in a dict where
        each matrix column corresponds to a dict key.

    Examples
    --------
    Full steps to pass two dataframes to norm_twod_xcorr from the same EMG
    file.

    1. Load the EMG file and band-pass filter the raw EMG signal
    2. Sort the matrix channels and compute the spike-triggered average
    3. Extract the STA of the MUs of interest from all the STAs
    4. Unpack the STAs of single MUs and remove np.nan to pass them to
        norm_twod_xcorr
    5. Compute 2dxcorr to identify a common lag/delay

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> emgfile = emg.filter_rawemg(emgfile, order=2, lowcut=20, highcut=500)
    >>> sorted_rawemg = emg.sort_rawemg(
    ...     emgfile,
    ...     code="GR08MM1305",
    ...     orientation=180,
    ...     )
    >>> sta = emg.sta(emgfile, sorted_rawemg, firings=[0, 50], timewindow=100)
    >>> mu0 = 0
    >>> mu1 = 1
    >>> sta_mu1 = sta[mu0]
    >>> sta_mu2 = sta[mu1]
    >>> df1 = emg.unpack_sta(sta_mu1)
    >>> no_nan_sta1 = df1.dropna(axis=1)
    >>> df2 = emg.unpack_sta(sta_mu2)
    >>> no_nan_sta2 = df2.dropna(axis=1)
    >>> normxcorr_df, normxcorr_max = emg.norm_twod_xcorr(
    ...     no_nan_sta1,
    ...     no_nan_sta2,
    ...     )
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

    # There is no need to work with numpy.ndarrays as signal.correlate2d is
    # already converting the pd.DataFrame into numpy.ndarray, and the rest of
    # the code does not take much time to run.

    # Normalise the result of 2d xcorr for the different energy levels
    # MATLAB equivalent:
    # acor_norm = xcorr(x,y)/sqrt(sum(abs(x).^2)*sum(abs(y).^2))
    # http://gaidi.ca/weblog/normalizing-a-cross-correlation-in-matlab
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


def compute_sil(ipts, mupulses, ignore_negative_ipts=False):
    """
    Calculate the Silhouette score for a single MU.

    The SIL is defined as the difference between the within-cluster sums of
    point-to-centroid distances and the same measure calculated between
    clusters. The output measure is normalised in a range between 0 and 1.

    Parameters
    ----------
    ipts : pd.Series
        The  decomposed source (or pulse train, IPTS[mu]) of the MU of
        interest.
    mupulses : ndarray
        The time of firing (MUPULSES[mu]) of the MU of interest.
    ignore_negative_ipts : bool, default False
        If True, only use positive ipts during peak and noise clustering. This
        is particularly important for sources with large negative components.

    Returns
    -------
    sil : float
        The SIL score.

    See also
    --------
    - compute_pnr : to calculate the Pulse to Noise ratio of a single MU.

    Examples
    --------
    Calculate the SIL score for the third MU (MU number 2) ignoring the
    negative component of the decomposed source.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.emg_from_samplefile()
    >>> mu_of_interest = 2
    >>> sil_value = emg.compute_sil(
    ...     ipts=emgfile["IPTS"][mu_of_interest],
    ...     mupulses=emgfile["MUPULSES"][mu_of_interest],
    ...     ignore_negative_ipts=True,
    ... )
    """

    # Manage exception of no firings
    if len(mupulses) == 0:
        return np.nan

    # Extract source and peaks and align source and peaks based on IPTS
    source = ipts.to_numpy()

    if ignore_negative_ipts:
        # Ignore negative values, this is particularly needed for negative
        # unbalanced sources.
        source = source * np.abs(source)

    peaks_idxs = mupulses - ipts.index[0]

    # Create clusters
    peak_cluster = source[peaks_idxs]
    noise_cluster = np.delete(source, peaks_idxs)

    # Create centroids for each cluster
    peak_centroid = np.mean(peak_cluster)
    noise_centroid = np.mean(noise_cluster)

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


def compute_pnr(
    ipts,
    mupulses,
    fsamp,
    constrain_pulses=[True, 3],
    separate_paired_firings=True,
):
    """
    Calculate the pulse to noise ratio for a single MU.

    Parameters
    ----------
    ipts : pd.Series
        The decomposed source (or pulse train, IPTS[mu]) of the MU of
        interest.
    mupulses : ndarray
        The time of firing (MUPULSES[mu]) of the MU of interest.
    constrain_pulses : list, default [True, 3]
        If constrain_pulses[0] == True, the times of firing are considered
        those in mupulses +- the number of samples specified in
        constrain_pulses[1].
        If constrain_pulses[0] == False, the times of firing are estimated via
        a heuristic penalty funtion (see Notes).
        constrain_pulses[1] must be an integer (see Notes for instructions on
        how to set the appropriate value).
    separate_paired_firings : bool, default False
        Whether to treat differently paired and non-paired firings during
        the estimation of the signal/noise threshold (heuristic penalty
        funtion, see Notes). This is relevant only if
        constrain_pulses[0] == False. Otherwise, this argument is ignored.

    Returns
    -------
    pnr : float
        The PNR in decibels.

    See also
    --------
    - compute_sil : to calculate the Silhouette score for a single MU.

    Notes
    -----
    The behaviour of the compute_pnr() function is determined by the argument
    constrain_pulses.

    If constrain_pulses[0] == True, the times of firing are considered those
    in mupulses +- a number of samples specified in constrain_pulses[1].
    The inclusion of the samples around the mupulses values allows to capture
    the full ipts corresponding to the time of firing (e.g., including also
    the raising and falling wedges). The appropriate value of
    constrain_pulses[1] must be determined by the user and depends on the
    sampling frequency. It is suggested to use 3 when the sampling frequency is
    2000 or 2048 Hz and increase it if the sampling frequency is higher (e.g.
    use 6 at 4000 or 4096 Hz). With this approach, the PNR estimation is not
    related to the variability of the firings.

    If constrain_pulses[0] == False, the ipts values are classified as firings
    or noise based on a threshold value (named "Pi" or "r") estimated from the
    euristic penalty funtion described in Holobar 2012, as proposed in
    Holobar 2014. If the variability of the firings is relevant, this
    apoproach should be preferred. Specifically:
    Pi = D · χ[3,50](D) + CoVIDI + CoVpIDI
    Where:
    D is the median of the low-pass filtered instantaneous motor unit discharge
    rate (first-order Butterworth filter, cut-off frequency 3 Hz).
    χ[3,50](D) stands for an indicator function that penalizes motor units
    with filtered discharge rate D below 3 pulses per second (pps) or above
    50 pps:
    χ[3,50](D) = 0 if D is between 3 and 50 or D if D is not between 3 and 50.
    Two separate coefficients of variation for inter-discharge interval (IDI)
    calculated as standard deviation (SD) of IDI divided by the mean IDI,
    are used. CoVIDI is the coefficient of variation for IDI of non-paired
    MUs discharges only, whereas CoVpIDI is the coefficient of variation for
    IDI of paired MUs discharges.
    Holobar 2012 considered MUs discharges paired whenever the second
    discharge was within 50 ms of the first.
    Paired discharges are typical in pathological tremor and the use of both
    CoVIDI and CoVpIDI accounts for this condition.
    However, this heuristic penalty function penalizes MUs firing during
    specific types of contractions like explosive contractions
    (MUs discharge up to 200 pps).
    Therefore, in this implementation of the PNR, we did ``not`` include the
    penalty based on MUs discharge.
    Additionally, the user can decide whether to adopt the two coefficients
    of variations to estimate Pi or not.
    If both are used, Pi would be calculated as:
    Pi = CoVIDI + CoVpIDI
    Otherwise, Pi would be calculated as:
    Pi = CoV_all_IDI

    Examples
    --------
    Calculate the PNR value for the third MU (MU number 2) forcing the
    selction of the times of firing.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.emg_from_samplefile()
    >>> mu_of_interest = 2
    >>> pnr_value = emg.compute_pnr(
    ...     ipts=emgfile["IPTS"][mu_of_interest],
    ...     mupulses=emgfile["MUPULSES"][mu_of_interest],
    ...     fsamp=emgfile["FSAMP"],
    ...     constrain_pulses=[True, 3],
    ... )

    Calculate the PNR value for the third MU (MU number 2) selecting the times
    of firing based on the euristic penalty funtion described in Holobar 2012
    and considering, separately, the paired and the non-paired firings.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.emg_from_samplefile()
    >>> mu_of_interest = 2
    >>> pnr_value = emg.compute_pnr(
    ...     ipts=emgfile["IPTS"][mu_of_interest],
    ...     mupulses=emgfile["MUPULSES"][mu_of_interest],
    ...     fsamp=emgfile["FSAMP"],
    ...     constrain_pulses=[False],
    ...     separate_paired_firings=True,
    ... )
    """

    # Manage exception of no firings
    if len(mupulses) == 0:
        return np.nan

    # Extract the source
    source = ipts.to_numpy()

    # Normalise source
    source = source / np.mean(source[mupulses])

    # Check how to estimate PNR
    if constrain_pulses[0] is True:
        # Estimate by mupulses
        start, stop = -int(constrain_pulses[1]), int(constrain_pulses[1])
        extended_mupulses = np.concatenate(
            [mupulses + t for t in range(start, stop+1)]
        )

        # Consider noise what outside the extenbded mupulses
        noise_times = np.setdiff1d(
            np.arange(mupulses[0], mupulses[-1]+1), extended_mupulses,
        )

        # Create clusters
        peak_cluster = source[mupulses]
        noise_cluster = source[noise_times]
        noise_cluster = noise_cluster[~np.isnan(noise_cluster)]
        noise_cluster = noise_cluster[noise_cluster >= 0]

    elif constrain_pulses[0] is False:
        # Estimate by Pi
        # Calculate IDI
        idi = np.diff(mupulses)

        # In order to increase robustness to outlier values, remove values
        # with more than 500ms of difference between each others.
        idi = idi[idi <= (fsamp * 0.5)]

        # Calculate Pi
        if separate_paired_firings is False:
            # Calculate Pi on all IDI
            CoV_all_IDI = np.std(idi) / np.mean(idi)

            if math.isnan(CoV_all_IDI):
                CoV_all_IDI = 0

            Pi = CoV_all_IDI

        else:
            # Divide paired and non-paired IDIs before calculating specific
            # CoV. De Luca 1985 considered dublets < 10 ms, Holobar < 50 ms.
            idinonp = idi[idi >= (fsamp * 0.05)]
            idip = idi[idi < (fsamp * 0.05)]

            if len(idinonp) > 1:
                CoVIDI = np.std(idinonp) / np.mean(idinonp)
            else:
                CoVIDI = 0

            if len(idip) > 1:
                CoVpIDI = np.std(idip) / np.mean(idip)
            else:
                CoVpIDI = 0

            # Calculate Pi
            Pi = CoVIDI + CoVpIDI

        # Create clusters
        peak_cluster = source[source >= Pi]
        noise_cluster = source[source < Pi]

    else:
        raise ValueError(
            "constrain_pulses[0] can only be True or False. " +
            f"{constrain_pulses[0]} was passed instead."
        )

    # Calculate PNR
    peak_cluster = np.square(peak_cluster)
    noise_cluster = np.square(noise_cluster)
    pnr = 10 * np.log10(np.mean(peak_cluster) / np.mean(noise_cluster))

    return pnr


def derivatives_beamforming(sig, row, teta):
    """
    Calculate devivatives for the beamforming technique.

    Calculate the first and second devivative of the mean square error for the
    beamforming technique with the first signal as reference.

    Parameters
    ----------
    sig : np.ndarray
        The source signal to be used for the calculation.
        Different channels should be organised in different rows.
    row : int
        The actual row in the iterative procedure.
    teta : float
        The value of teta.

    Returns
    -------
    de1, de2 : float
        The value of the first and second derivative.

    See also
    --------
    - estimate_cv_via_mle : Estimate signal conduction velocity via maximum
        likelihood estimation.
    - MUcv_gui : Graphical user interface for the estimation of MUs conduction
        velocity.
    """

    # Define some necessary variables
    total_rows = np.shape(sig)[0]
    m = total_rows - 1
    total_columns = np.shape(sig)[1]
    half_of_the_columns = np.arange((round(total_columns/2))) + 1

    # Create a custom position index with negative and mirrored values for
    # index < row.
    position = np.zeros(np.shape(sig)[0])
    position[0] = row + 1  # + 1 used to overcome base 0 here and following

    for i in range(1, row+1):
        position[i] = i-(row+1)

    for i in range(m-row):
        position[i+row+1] = i + 1

    position = np.delete(position, 0)

    # Shift sig and move the value contained in sig[row] to sig[0]
    this_row = sig[row, :]
    sig = np.delete(sig, (row), axis=0)  # axis=0 to delete rows
    sig = np.insert(sig, 0, this_row, axis=0)

    # Calculate fft row-wise (for each signal)
    sigfft = np.zeros_like(sig, dtype=np.complex128)  # Specify dtype as complex
    for i in range(total_rows):
        sigfft[i, :] = fft(sig[i, :])

    # Create the series used to store the terms of the derivatives
    term_de1 = np.zeros(np.shape(half_of_the_columns)[0])
    term_de2 = np.zeros(np.shape(half_of_the_columns)[0])
    term_de12 = np.zeros(np.shape(half_of_the_columns)[0])
    term_de22 = np.zeros(np.shape(half_of_the_columns)[0])

    # Calculate the first term of the first derivative
    for i in range(m):
        for u in range(i+1, m):

            s_fft = sigfft[i+1, half_of_the_columns]
            s_conj = np.conj(sigfft[u+1, half_of_the_columns])
            s_exp = np.exp(1j * 2 * np.pi * half_of_the_columns * (position[i]-position[u]) * teta / total_columns)
            s_last = 2 * np.pi * half_of_the_columns * (position[i]-position[u]) / total_columns

            image = np.imag(s_fft * s_conj * s_exp * s_last)

            term_de1 = term_de1-image

    term_de1 = (term_de1*2) / (m**2)

    # Calculate the second term of the first derivative
    for i in range(m):

        s_fft = sigfft[i+1, half_of_the_columns]
        s_exp = np.exp(1j * 2 * np.pi * half_of_the_columns * position[i] * teta / total_columns)
        s_last = 2 * np.pi * half_of_the_columns * position[i] / total_columns

        term_de2 = term_de2 + (s_fft * s_exp * s_last)

    s_conj = np.conj(sigfft[0, half_of_the_columns])

    term_de2 = 2 * np.imag(s_conj * term_de2) / m

    # Calculate the first derivative
    de1 = 2 / total_columns * np.sum(term_de1 + term_de2)

    # Calculate the first term of the second derivative
    for i in range(m):
        for u in range(i+1, m):

            s_fft = sigfft[i+1, half_of_the_columns]
            s_conj = np.conj(sigfft[u+1, half_of_the_columns])
            s_exp = np.exp(1j * 2 * np.pi * half_of_the_columns * (position[i]-position[u]) * teta / total_columns)
            s_last = 2 * np.pi * half_of_the_columns * (position[i]-position[u]) / total_columns

            term_de12 = term_de12 - np.real(s_fft * s_conj * s_exp * (s_last**2))

    term_de12 = (term_de12 * 2) / (m ** 2)

    # Calculate the second term of the second derivative
    for i in range(m):

        s_fft = sigfft[i+1, half_of_the_columns]
        s_exp = np.exp(1j * 2 * np.pi * half_of_the_columns * position[i] * teta / total_columns)
        s_last = 2 * np.pi * half_of_the_columns * position[i] / total_columns

        term_de22 = term_de22 + (s_fft * s_exp * (s_last**2))

    s_conj = np.conj(sigfft[0, half_of_the_columns])

    term_de22 = 2 * np.real(s_conj * term_de22) / m

    # Calculate the second derivative
    de2 = 2 / total_columns * np.sum(term_de12 + term_de22)

    return de1, de2


def mle_cv_est(sig, initial_teta, ied, fsamp):
    """
    Estimate conduction velocity (CV) via maximum likelihood estimation.

    Parameters
    ----------
    sig : np.ndarray
        The source signal to be used for the calculation.
        Different channels should be organised in different rows.
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
    - estimate_cv_via_mle : Estimate signal conduction velocity via maximum
        likelihood estimation.
    - MUcv_gui : Graphical user interface for the estimation of MUs conduction
        velocity.

    Examples
    --------
    Refer to the examples of find_mle_teta to obtain sig and initial_teta.
    """

    # Calculate ied in meters
    ied = ied / 1000

    # Assign the initial value of teta to t
    t = initial_teta
    # Set teta to 10 just to start the while loop
    teta = 10
    trial = 0
    eps = sys.float_info.epsilon

    while abs(teta - t) >= 5e-5 and trial < 30:
        trial = trial + 1
        teta = t
        # Initialize the first and second derivatives
        de1 = 0
        de2 = 0

        # Calculate the first and second derivatives
        for row in range(np.shape(sig)[0]):
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


def find_mle_teta(sig1, sig2, ied, fsamp):
    """
    Find the starting value for teta.

    It is important to don't fix teta and use a non-fixed starting point for
    the CV algorithm.

    Parameters
    ----------
    sig1, sig2 : np.ndarray
        The two signals based on which to calculate teta.
        These must be 1-dimensional arrays where the data is contained in a row.
    ied : int or float
        Interelectrode distance (mm).
    fsamp : int or float
        Sampling frequency (Hz).

    Returns
    -------
    teta : int
        The starting value teta.

    See also
    --------
    - estimate_cv_via_mle : Estimate signal conduction velocity via maximum
        likelihood estimation.
    - MUcv_gui : Graphical user interface for the estimation of MUs conduction
        velocity.

    Examples
    --------
    Calculate the starting point for the maximum likelihood estimation.
    In this example, we calculate teta for the first MU (number 0) on the
    channels 31, 32, 34, 34 that are contained in the second column ("col2")
    of the double differential representation of the MUAPs.
    First, obtain the spike-triggered average of the double differential
    derivation.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> emgfile = emg.filter_rawemg(emgfile)
    >>> sorted_rawemg = emg.sort_rawemg(
    ...     emgfile,
    ...     code="GR08MM1305",
    ...     orientation=180,
    ...     dividebycolumn=True
    ... )
    >>> dd = emg.double_diff(sorted_rawemg=sorted_rawemg)
    >>> sta = emg.sta(
    ...     emgfile=emgfile,
    ...     sorted_rawemg=sorted_rawemg,
    ...     firings=[0,50],
    ...     timewindow=50,
    ... )

    Second, prepare the signals for the estimation of teta.
    The input (sig) provided for the estimation of teta contains a channel
    each row and all the instants are contained in columns. For this reason,
    the original content of the spike-triggered average has to be transposed.
    After that, the 1D signals used to estimate teta are defined based on the
    number of available channels. Please note that the original signal
    contained in a pandas DataFrame has to be convertedn in a numpy array.

    >>> sig = sta[0]["col2"].loc[:, 31:34]
    >>> sig = sig.to_numpy()
    >>> if np.shape(sig)[0] > 3:
    ...     sig1 = sig[1, :]
    ...     sig2 = sig[2, :]
    >>> else:
    ...     sig1 = sig[0, :]
    ...     sig2 = sig[1, :]

    Third, estimate teta.

    >>> initial_teta = emg.find_mle_teta(
    ...     sig1=sig1,
    ...     sig2=sig2,
    ...     ied=emgfile["IED"],
    ...     fsamp=emgfile["FSAMP"],
    ... )
    1
    """

    # Define an arbitrary range for possible CV values (slightly larger than
    # the physiological range) based on which to calculate teta.
    min_cv = 1
    max_cv = 10
    teta_min = math.floor(ied / max_cv * fsamp)
    teta_max = math.ceil(ied / min_cv * fsamp)

    # Verify that the input is a 1D array. If not, it will affect the
    # calculation of corrpos.
    if sig1.ndim != 1:
        raise ValueError("sig1 is not 1 dimensional")
    if sig2.ndim != 1:
        raise ValueError("sig2 is not 1 dimesional")

    delay = np.arange(teta_min, teta_max+1)
    corrpos = np.zeros(len(delay))
    for idx, i in enumerate(delay):
        sig1_tosum = sig1[:len(sig1)-i]
        sig2_tosum = sig2[i:]

        corrpos[idx-teta_min+1] = np.sum(sig1_tosum * sig2_tosum)

    pos = corrpos.argmax() + 1
    # +1 is necessary to overcome base 0 and prevent teta from beeing 0

    if pos > 1 and pos < len(delay):
        x = delay[pos-2: pos+1]
        y = corrpos[pos-2: pos+1]

        coefs = poly.polyfit(x=x, y=y, deg=2)
        # The polyfit function originally returns flipped coefficients
        coefs = np.flip(coefs)

        teta = -coefs[1] / (2 * coefs[0])

    else:
        teta = pos

    return teta
