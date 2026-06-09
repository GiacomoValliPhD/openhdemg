import warnings
from math import comb
from itertools import combinations

import numpy as np
import pandas as pd
from scipy import signal
from scipy.optimize import curve_fit
from scipy.special import erfcinv, digamma
from scipy.sparse.csgraph import connected_components


def pooled_intramuscular_coherence(
    emgfile,
    number_of_mus_cst=-1,
    number_iterations=100,
    window_type="hanning",
    window_duration_seconds=1,
    overlap_seconds=0.5,
    nfft=None,
    random_state=42,
):
    """
    Estimate common synaptic input oscillations using coherence analysis
    between two cumulative spike trains.

    The procedure follows these steps:

    1. Randomly split motor units into two groups.
    2. Sum the binary spike trains within each group to obtain two cumulative
    spike trains (CSTs).
    3. Estimate auto-spectra of CST 1 and CST 2.
    4. Estimate cross-spectrum between CST 1 and CST 2.
    5. Repeat over random permutations (default: 100).
    6. Pool spectra across iterations.
    7. Compute coherence from the pooled spectra.

    References:

    - Negro et al., 2012 (https://doi.org/10.1371/journal.pone.0044894)
    - Castronovo et al., 2015 (https://doi.org/10.1152/japplphysiol.00255.2015)
    - Cabral et al., 2024 (https://doi.org/10.1113/JP286078)
    - Cabral et al., 2024 (https://doi.org/10.1523/ENEURO.0043-24.2024)

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    number_of_mus_cst : int, default -1
        Number of motor units included in each group for the cumulative spike
        train. If -1, defaults to floor(number_of_mus / 2).
    number_iterations : int, default 100
        Number of random permutations.
    window_type : str, default "hanning"
        Type of window used for spectral estimation.
    window_duration_seconds : float, default 1
        Size of the window for coherence estimation in seconds.
    overlap_seconds : float, default 0.5
        Number of seconds of overlap between adjoining segments. Considering a
        window_duration_seconds of 1 second, an overlap of 0.5 seconds means a
        50% overlap.
    nfft : int, optional
        Number of FFT points. If None, defaults to 10 * fsamp.
    random_state : int, default 42
        Random seed for reproducible random permutations.

    Returns
    -------
    coherence_results : dict
        Dictionary containing the following keys:

        - "coherence": the coherence curve (numpy array).
        - "frequency": the frequency values corresponding to the coherence
        curve (numpy array).
        - "window_duration_seconds": the window duration in seconds (float).
        - "window": the window used for spectral estimation (numpy array).
        - "overlap_seconds": the overlap between segments in seconds (float).
        - "cst_duration_seconds": the duration of the cumulative spike trains
        in seconds (float).
        - "fsamp": the sampling frequency in Hz (float).
    """

    # ----------------------------------
    # Validate inputs
    # ----------------------------------

    if not emgfile["MUPULSES"]:
        raise ValueError(
            "There are no motor unit pulses in the emgfile. "
            "Please check that MUPULSES is not empty."
        )

    tot_mus = emgfile["NUMBER_OF_MUS"]

    if tot_mus < 2:
        raise ValueError(
            "To calculate coherence, total number of mus units must be at "
            "least 2."
        )

    # Determine the number of motor units in each cumulative spike train group
    # (number_of_mus_cst).
    if number_of_mus_cst == -1:
        number_of_mus_cst = tot_mus // 2
    elif number_of_mus_cst > (tot_mus // 2):
        msg = (
            "number_of_mus_cst is greater than half of total number of motor "
            "units. number_of_mus_cst will be set to half of total number of "
            "motor units."
        )
        warnings.warn(msg, UserWarning)
        number_of_mus_cst = tot_mus // 2
    elif number_of_mus_cst < 1:
        raise ValueError("number_of_mus_cst must be at least 1.")

    if window_duration_seconds <= 0:
        raise ValueError("window_duration_seconds must be a positive number.")

    fsamp = emgfile["FSAMP"]
    window_samples = int(round(fsamp * window_duration_seconds))

    if window_type == "hanning":
        window = signal.windows.hann(window_samples, sym=True)
    elif window_type == "hamming":
        window = signal.windows.hamming(window_samples, sym=True)
    else:
        raise ValueError(
            "Unsupported window_type. Supported types are 'hanning' and "
            "'hamming'."
        )

    if nfft is None:
        nfft = int(round(10 * fsamp))

    if overlap_seconds < 0:
        raise ValueError("overlap_seconds must be >= 0.")

    overlap_samples = int(round(fsamp * overlap_seconds))

    if overlap_samples >= window_samples:
        raise ValueError(
            "overlap_seconds must be smaller than the window_duration_seconds."
        )

    binary_mus_firing = emgfile["BINARY_MUS_FIRING"].to_numpy(dtype=np.int64)

    rng = np.random.default_rng(random_state)

    # ----------------------------------
    # Number of unique unordered group pairs (group1 vs group2 is the same as
    # group2 vs group1).
    # ----------------------------------
    unique_split_count = (
        comb(tot_mus, number_of_mus_cst)
        * comb(tot_mus - number_of_mus_cst, number_of_mus_cst)
        // 2
    ) 

    # If the number of unique splits is smaller than the requested number of
    # iterations, use all unique splits and warn the user.
    use_all_unique_splits = unique_split_count < number_iterations

    if use_all_unique_splits:
        warnings.warn(
            f"Only {unique_split_count} unique CST group splits are possible. "
            f"number_iterations will be set to {unique_split_count}.",
            UserWarning,
        )

        group_pairs = []
        used_splits = set()

        for group_1 in combinations(np.arange(tot_mus), number_of_mus_cst):

            remaining_units = np.setdiff1d(np.arange(tot_mus), group_1)

            for group_2 in combinations(remaining_units, number_of_mus_cst):

                group_1_tuple = tuple(sorted(group_1))
                group_2_tuple = tuple(sorted(group_2))

                # Makes group1/group2 order irrelevant.
                # Example: (0,1) vs (2,3) is the same as (2,3) vs (0,1)
                split_key = tuple(sorted([group_1_tuple, group_2_tuple]))

                if split_key not in used_splits:
                    used_splits.add(split_key)

                    group_pairs.append(
                        (
                            np.asarray(group_1_tuple, dtype=np.int64),
                            np.asarray(group_2_tuple, dtype=np.int64),
                        )
                    )

        number_iterations = len(group_pairs)

    else:
        group_pairs = None

    # ----------------------------------
    # Main loop over iterations
    # ----------------------------------

    # Initialize variables
    pooled_auto_spectra_1 = None
    pooled_auto_spectra_2 = None
    pooled_cross_spectra = None
    frequency = None

    for iteration in range(number_iterations):

        print(f"Iteration {iteration + 1}/{number_iterations}...")

        if use_all_unique_splits:
            group_1_indices, group_2_indices = group_pairs[iteration]
        else:
            unit_indices = rng.permutation(tot_mus)
            group_1_indices = unit_indices[:number_of_mus_cst]
            group_2_indices = unit_indices[-number_of_mus_cst:]

        # Cumulative spike trains
        cst_1 = np.sum(binary_mus_firing[:, group_1_indices], axis=1)
        cst_2 = np.sum(binary_mus_firing[:, group_2_indices], axis=1)

        # Detrend signals (removes the mean)
        cst_1 = signal.detrend(cst_1, type="constant")
        cst_2 = signal.detrend(cst_2, type="constant")

        # Spectral estimation using Welch's method
        frequency, auto_spectra_1 = signal.csd(
            cst_1,
            cst_1,
            fs=fsamp,
            window=window,
            noverlap=overlap_samples,
            nfft=nfft,
            detrend=False,  # already detrended above
            return_onesided=True,
            scaling="density",
        )

        _, auto_spectra_2 = signal.csd(
            cst_2,
            cst_2,
            fs=fsamp,
            window=window,
            noverlap=overlap_samples,
            nfft=nfft,
            detrend=False,  # already detrended above
            return_onesided=True,
            scaling="density",
        )

        _, cross_spectra = signal.csd(
            cst_1,
            cst_2,
            fs=fsamp,
            window=window,
            noverlap=overlap_samples,
            nfft=nfft,
            detrend=False,  # already detrended above
            return_onesided=True,
            scaling="density",
        )

        if pooled_auto_spectra_1 is None:
            pooled_auto_spectra_1 = np.zeros_like(
                auto_spectra_1, dtype=np.float64
            )
            pooled_auto_spectra_2 = np.zeros_like(
                auto_spectra_2, dtype=np.float64
            )
            pooled_cross_spectra = np.zeros_like(
                cross_spectra, dtype=np.complex128
            )  # cross-spectra is complex-valued

        # Pool spectra across iterations by summing them up
        pooled_auto_spectra_1 += auto_spectra_1
        pooled_auto_spectra_2 += auto_spectra_2
        pooled_cross_spectra += cross_spectra

    # Average the pooled spectra by dividing by the number of iterations
    pooled_auto_spectra_1 /= number_iterations
    pooled_auto_spectra_2 /= number_iterations
    pooled_cross_spectra /= number_iterations

    # Compute coherence from the pooled spectra using the formula:
    # C(f) = |Pxy(f)|^2 / (Pxx(f) * Pyy(f))
    coherence = np.abs(pooled_cross_spectra) ** 2 / (
        pooled_auto_spectra_1 * pooled_auto_spectra_2
    )

    length_signal, _ = binary_mus_firing.shape

    # Ensure that variables are in the proper data type (e.g., float64) before
    # returning the results.
    coherence = np.asarray(coherence, dtype=np.float64)
    frequency = np.asarray(frequency, dtype=np.float64)
    window_duration_seconds = float(window_duration_seconds)
    window = np.asarray(window, dtype=np.float64)
    cst_duration_seconds = float(round(length_signal)/fsamp)
    overlap_seconds = float(overlap_seconds)

    coherence_results = {
        "coherence": coherence,
        "frequency": frequency,
        "window_duration_seconds": window_duration_seconds,
        "window": window,
        "overlap_seconds": overlap_seconds,
        "cst_duration_seconds": cst_duration_seconds,
        "fsamp": fsamp,
    }

    return coherence_results


def z_score_coherence(coherence_results):
    """
    Z-score coherence following two possible cases:

    1. No overlap:

        z = sqrt(2 * L) * atanh(sqrt(coherence))

        where L is the number of non-overlapping time segments used in the
        Welch method.

    2. With overlap:

        z = sqrt(2 * K_tilde) * atanh(sqrt(coherence))

        where K_tilde is the corrected number of independent segments
        accounting for overlap between Welch segments.

    Parameters
    ----------
    coherence_results : dict
        Dictionary returned by pooled_intramuscular_coherence.

    Returns
    -------
    z_score_results : dict
        Dictionary containing the same keys of pooled_intramuscular_coherence
        plus the following keys:

        - "z_score": the z-scored coherence curve (numpy array)
        - "factor": the factor used for z-scoring (float)
    """

    # ----------------------------------
    # Validate inputs
    # ----------------------------------
    coherence = coherence_results["coherence"]

    fsamp = coherence_results["fsamp"]
    window = coherence_results["window"]

    window_duration_seconds = coherence_results["window_duration_seconds"]
    window_samples = int(round(fsamp * window_duration_seconds))

    cst_duration_seconds = coherence_results["cst_duration_seconds"]
    cst_duration_samples = int(round(fsamp * cst_duration_seconds))

    overlap_seconds = coherence_results["overlap_seconds"]

    # ----------------------------------
    # Case 1: no overlap
    # ----------------------------------
    if overlap_seconds == 0:

        L = int(np.floor(cst_duration_seconds / window_duration_seconds))

        factor = np.sqrt(2 * L)
    # ----------------------------------
    # Case 2: overlap
    # ----------------------------------
    else:

        step_samples = window_samples - int(round(fsamp * overlap_seconds))

        K = int(np.floor(cst_duration_samples / window_samples))

        # Effective number of independent segments
        # following the overlap correction logic.
        correction_factor_cw = 1.0

        rho_denominator = np.sum(window ** 2)

        for j in range(1, K):

            shift_samples = j * step_samples

            if shift_samples >= window_samples:
                rho_t = 0.0
            else:
                rho_numerator = np.sum(
                    window[: window_samples - shift_samples]
                    * window[shift_samples: window_samples]
                )

                rho_t = rho_numerator / rho_denominator

            correction_factor_cw += 2 * ((K - j) / K) * (rho_t ** 2)

        k_tilde = K / correction_factor_cw

        factor = np.sqrt(2 * k_tilde)

    z_score = factor * np.arctanh(np.sqrt(coherence))

    # Ensure that variables are in the proper data type (e.g., float64) before
    # returning the results
    z_score = np.asarray(z_score, dtype=np.float64)
    factor = float(factor)

    # Update the results dictionary with z-score and factor
    z_score_results = coherence_results.copy()

    z_score_results.update(
        {
            "z_score": z_score,
            "factor": factor,
        }
    )

    return z_score_results


def calculate_coherence_bands(
    coherence_results,
    confidence_level_type="high_frequency_bias",
    bias_frequency_range=[250, 500],
    delta_frequency_range=[1, 5],
    alpha_frequency_range=[5, 15],
    beta_frequency_range=[15, 35],
    gamma_frequency_range=[35, 60],
):
    """
    Calculate band-specific parameters from either a z-scored coherence curve
    or a raw coherence curve.

    If coherence_results contains "z_score", the function uses it.
    Otherwise, the function uses raw coherence curve.

    For each frequency band, this function calculates:

    1. Average coherence/z-score above the confidence level.
    2. Area under the coherence/z-score curve above the confidence level.

    Parameters
    ----------
    coherence_results : dict
        Dictionary containing either keys {"z_score", "frequency"} or
        {"coherence", "frequency"}.
    confidence_level_type : str {"high_frequency_bias", "theoretical"}, default "high_frequency_bias"
        Type of confidence level used to determine which parts of the
        coherence/z-score curve are considered significant.

        ``high_frequency_bias``
            The confidence level is defined as the average coherence/z-score
            in the high-frequency bias band defined by bias_frequency_range.

        ``theoretical``
            The confidence level is defined as 95% confidence level based on
            the theoretical distribution.

            - For z-score: 1.65 (95th percentile of the standard normal
            distribution).

            - For coherence: 1 - 0.05 ** (1 / (L - 1)), where L is the number
            of non-overlapping segments used in the Welch method.

    bias_frequency_range : list, default [250, 500]
        Frequency range for the bias band in Hz when confidence_level_type is
        "high_frequency_bias".
    delta_frequency_range : list, default [1, 5]
        Frequency range for the delta band in Hz.
    alpha_frequency_range : list, default [5, 15]
        Frequency range for the alpha band in Hz.
    beta_frequency_range : list, default [15, 35]
        Frequency range for the beta band in Hz.
    gamma_frequency_range : list, default [35, 60]
        Frequency range for the gamma band in Hz.

    Returns
    -------
    coherence_band_results : pd.DataFrame
        Dataframe with the following columns:

        - "coherence_type": "z_score" or "coherence".
        - "confidence_level": confidence level used (float).
        - "average_delta": average coherence/z-score in the delta band above
        the confidence level.
        - "auc_delta": area under the coherence/z-score curve in the delta
        band above the confidence level.
        - "average_alpha": average coherence/z-score in the alpha band above
        the confidence level.
        - "auc_alpha": area under the coherence/z-score curve in the alpha
        band above the confidence level.
        - "average_beta": average coherence/z-score in the beta band above the
        confidence level.
        - "auc_beta": area under the coherence/z-score curve in the beta band
        above the confidence level.
        - "average_gamma": average coherence/z-score in the gamma band above
        the confidence level.
        - "auc_gamma": area under the coherence/z-score curve in the gamma
        band above the confidence level.
    """

    # ----------------------------------
    # Validate inputs
    # ----------------------------------
    frequency = coherence_results["frequency"]
    cst_duration_seconds = coherence_results["cst_duration_seconds"]
    window_duration_seconds = coherence_results["window_duration_seconds"]

    bias_frequency_range = sorted(bias_frequency_range)
    bias_mask = (
        (frequency >= bias_frequency_range[0])
        & (frequency <= bias_frequency_range[1])
    )

    # ----------------------------------
    # Case 1: use z-score if available
    # ----------------------------------
    if "z_score" in coherence_results:
        coherence_curve = coherence_results["z_score"]
        coherence_type = "z_score"
    # ----------------------------------
    # Case 2: otherwise use raw coherence
    # ----------------------------------
    elif "coherence" in coherence_results:
        coherence_curve = coherence_results["coherence"]
        coherence_type = "coherence"
    else:
        raise KeyError(
            "coherence_results must contain either 'z_score' or 'coherence'."
        )

    # ----------------------------------
    # Define confidence level based on the confidence_level_type
    # ----------------------------------
    if confidence_level_type == "high_frequency_bias":
        confidence_level = float(np.mean(coherence_curve[bias_mask]))
    elif confidence_level_type == "theoretical":
        if coherence_type == "z_score":
            confidence_level = 1.65
            # 95th percentile of the standard normal distribution
        else:
            L = int(np.floor(cst_duration_seconds / window_duration_seconds))
            confidence_level = 1 - 0.05 ** (1 / (L - 1))
    else:
        msg = (
            "Confidence level type must be 'high_frequency_bias' or "
            "'theoretical'. It will be used 'high_frequency_bias'."
        )
        warnings.warn(msg, UserWarning)
        confidence_level = float(np.mean(coherence_curve[bias_mask]))

    # ----------------------------------
    # Internal function to calculate parameters for one frequency band
    # ----------------------------------
    def _calculate_band_parameters(frequency_range):
        lower_freq, upper_freq = frequency_range

        band_mask = (
            (frequency >= lower_freq)
            & (frequency < upper_freq)
            & (coherence_curve > confidence_level)
        )

        if not np.any(band_mask):
            average = 0.0
            auc = 0.0
        else:
            frequency_band = frequency[band_mask]
            coherence_band = coherence_curve[band_mask]

            average = float(np.mean(coherence_band))

            if len(coherence_band) > 1:
                auc = float(np.trapezoid(coherence_band, frequency_band))
            else:
                auc = 0.0

        return average, auc

    # ----------------------------------
    # Calculate parameters for each frequency band
    # ----------------------------------
    average_delta, auc_delta = _calculate_band_parameters(
        delta_frequency_range
    )

    average_alpha, auc_alpha = _calculate_band_parameters(
        alpha_frequency_range
    )

    average_beta, auc_beta = _calculate_band_parameters(
        beta_frequency_range
    )

    average_gamma, auc_gamma = _calculate_band_parameters(
        gamma_frequency_range
    )

    # Return coherence_band_results as a dataframe
    coherence_band_results = {
        "coherence_type": coherence_type,
        "confidence_level": confidence_level,

        "average_delta": average_delta,
        "auc_delta": auc_delta,

        "average_alpha": average_alpha,
        "auc_alpha": auc_alpha,

        "average_beta": average_beta,
        "auc_beta": auc_beta,

        "average_gamma": average_gamma,
        "auc_gamma": auc_gamma,
    }

    return pd.DataFrame([coherence_band_results])


def smooth_spiketrains_convolution(
    binary_mus_firing,
    fsamp,
    window_type="hanning",
    window_duration_seconds=0.4
):
    """
    Smooth a binary spike train by convolving it with a window.

    Parameters
    ----------
    binary_mus_firing : np.ndarray
        The binary motor unit firing data.
    window_type : str, default "hanning"
        Type of window used for smoothing.
    window_duration_seconds : float, default 0.4
        Smoothing window duration in seconds.

    Returns
    -------
    smoothed_mus_firing : np.ndarray
        Smoothed motor unit discharge rates obtained by convolving the binary
        spike train with the specified window. Arrangement of the output array
        is the same as binary_mus_firing (samples x motor units).
    """

    # ----------------------------------
    # Validate inputs
    # ----------------------------------
    if window_duration_seconds <= 0:
        raise ValueError("window_duration_seconds must be a positive number.")

    window_samples = int(round(fsamp * window_duration_seconds))

    if window_type == "hanning":
        window = signal.windows.hann(window_samples, sym=True)
    elif window_type == "hamming":
        window = signal.windows.hamming(window_samples, sym=True)
    else:
        raise ValueError(
            "Unsupported window_type. Use 'hanning' or 'hamming'."
        )

    # Smoothing spike trains by convolving with the window and scaling to
    # preserve units in pps.
    scaling_factor = fsamp / np.sum(window)

    smoothed_mus_firing = signal.lfilter(
        scaling_factor * window,
        [1.0],
        binary_mus_firing,
        axis=0,
    )
    # Ensure that variables are in the proper data type (e.g., float64) before
    # returning the results.
    smoothed_mus_firing = np.asarray(smoothed_mus_firing, dtype=np.float64)

    return smoothed_mus_firing


def pca_components(
    emgfile,
    window_type="hanning",
    window_duration_seconds=0.4,
    filter_highcut=0.75,
    filter_order=3,
    remove_edge_seconds=1,
    method_n_components="parallel_analysis",
    number_iterations_pa=1000,
    percentile_pa=95,
    variance_threshold=80.0,
    random_state=42,
):
    """
    Estimate low-dimensional components from motor unit spike trains
    using PCA applied to smoothed discharge-rate profiles.

    The procedure follows this pipeline:

    1. Convert binary motor unit spike trains to smoothed discharge-rate
    profiles.
    2. High-pass filter the smoothed discharge rates to remove offsets and
    slow trends.
    3. Standardize each motor unit discharge profile.
    4. Calculate the covariance/correlation matrix.
    5. Extract eigenvalues and eigenvectors.
    6. Use parallel analysis to estimate the number of components to
    retain.
    7. Project the standardized discharge profiles onto the retained
    eigenvectors.

    References:

    - Negro et al., 2009 (https://doi.org/10.1113/jphysiol.2009.178509)
    - Cabral et al., 2025 (https://doi.org/10.1016/j.isci.2025.113483)

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    window_duration_seconds : float, default 0.4
        Duration of the Hann window used to smooth binary spike trains.
    filter_highcut : float, default 0.75
        High-pass cutoff frequency used to remove offsets and slow trends.
    filter_order : int, default 3
        Butterworth filter order.
    remove_edge_seconds : float, default 1
        Number of seconds to remove from the beginning and end of the smoothed
        discharge profiles to avoid edge artifacts from convolution and
        filtering.
    method_n_components : str, default "parallel_analysis"
        Method used to estimate the number of components to retain.

        ``parallel_analysis``
            Retain the number of components that present eigenvalues greater
            than the percentile (e.g., 95th) of eigenvalues generated from
            randomly shuffling the data.

        ``variance_greater_than_threshold``
            Retain the number of components that explain more than a certain
            percentage (e.g., 80%) of the variance.

        ``eigenvalue_greater_than_one``
            (Kaiser's criterion). Retain the number of components with
            eigenvalues greater than 1.
    number_iterations_pa : int, default 1000
        Number of iterations for parallel analysis.
    percentile_pa : float, default 95
        Percentile used in parallel analysis.
    variance_threshold : float, default 80.0
        Threshold if "variance_greater_than_threshold" is used.
    random_state : int, default 42
        Seed for reproducibility.

    Returns
    -------
    pca_results : dict
        Dictionary containing the following keys:

        - "smoothed_mus_firing": the smoothed binary spike trains calculated
        by window convolution (numpy array) smoothed_mus_firing has the same
        shape as the input binary_mus_firing (samples x motor units).
        - "kmo": the Kaiser-Meyer-Olkin measure of sampling adequacy (float).
        - "method_n_components": the selected method to estimate the number of
        components to retain (str).
        - "eigenvalues_threshold_pa": the eigenvalue threshold based on
        parallel analysis (float).
        - "variance_threshold": the variance threshold used if
        method_n_components is "variance_greater_than_threshold" (float).
        - "number_of_components_retained": the number of components retained
        based on parallel analysis (int).
        - "eigenvalues": the eigenvalues of the covariance/correlation matrix
        (numpy array).
        - "eigenvectors": the eigenvectors of the covariance/correlation
        matrix (numpy array).
        - "explained_variance": the explained variance in percentage of each
        component (numpy array).
        - "cumulative_explained_variance": the cumulative explained variance
        in percentage (numpy array).
        - "low_dimensional_components": the low-dimensional components (numpy
        array).

    Notes
    -------
    1. Kaiser-Meyer-Olkin (KMO) measure is calculated to assess the
    factorability of the dataset before performing PCA. Typically, a KMO value
    above 0.7 is considered acceptable (Hoelzle & Meyer, 2012;
    https://doi.org/10.1002/9781118133880.hop202006).
    2. Altough other methods to define the number of components are available,
    we reccomend using parallel analysis as it is more robust and data-driven
    than arbitrary thresholds (e.g., eigenvalue > 1 or variance explained >
    80%).
    """

    # ----------------------------------
    # Validate inputs
    # ----------------------------------
    if not emgfile["MUPULSES"]:
        raise ValueError(
            "There are no motor unit pulses in the emgfile. "
            "Please check that MUPULSES is not empty."
        )

    fsamp = emgfile["FSAMP"]
    tot_mus = emgfile["NUMBER_OF_MUS"]

    if tot_mus < 2:
        raise ValueError(
            "At least 2 MUs are required for PCA common input analysis."
        )

    binary_mus_firing = emgfile["BINARY_MUS_FIRING"].to_numpy(dtype=np.int64)

    if window_duration_seconds <= 0:
        raise ValueError("window_duration_seconds must be positive.")

    if filter_highcut <= 0:
        raise ValueError("filter_highcut must be positive.")

    if filter_highcut >= fsamp / 2:
        raise ValueError(
            "filter_highcut must be lower than Nyquist frequency."
        )

    rng = np.random.default_rng(random_state)

    # Smooth binary spike trains by convolving with the window and scaling to
    # preserve units in pps.
    smoothed_mus_firing = smooth_spiketrains_convolution(
        binary_mus_firing,
        fsamp,
        window_type=window_type,
        window_duration_seconds=window_duration_seconds,
        )

    # Remove edge samples affected by convolution and filtering
    remove_edge_samples = int(round(fsamp * remove_edge_seconds))
    if remove_edge_samples > 0:
        smoothed_mus_firing = smoothed_mus_firing[
            remove_edge_samples: -remove_edge_samples, :
        ]

    # High-pass filter smoothed discharge rates
    sos = signal.butter(
        N=filter_order,
        Wn=filter_highcut,
        btype="highpass",
        output="sos",
        fs=fsamp,
    )

    smoothed_mus_firing = signal.sosfiltfilt(sos, smoothed_mus_firing, axis=0)

    # ----------------------------------
    # Internal function to perform KMO test; i.e., check if the dataset is
    # factorable.
    # ----------------------------------
    def _calculate_kmo(x):
        """
        Calculate Kaiser-Meyer-Olkin (KMO) measure.

        Parameters
        ----------
        x : np.ndarray
            Data matrix with shape samples x features.

        Returns
        -------
        kmo : float
            Overall KMO value.
        """

        # Correlation matrix
        corr_matrix = np.corrcoef(x, rowvar=False)

        # Inverse correlation matrix
        inv_corr_matrix = np.linalg.pinv(corr_matrix)

        # Partial correlation matrix
        denominator = np.sqrt(
            np.outer(
                np.diag(inv_corr_matrix),
                np.diag(inv_corr_matrix),
            )
        )

        partial_corr_matrix = -inv_corr_matrix / denominator
        np.fill_diagonal(partial_corr_matrix, 1.0)

        n_features = corr_matrix.shape[0]

        corr_squared_sum = np.sum(corr_matrix ** 2) - n_features
        partial_corr_squared_sum = np.sum(
            partial_corr_matrix ** 2
        ) - n_features

        kmo = corr_squared_sum / (
            corr_squared_sum + partial_corr_squared_sum
        )

        kmo = round(float(kmo), 4)

        return kmo

    # Calculate KMO measure
    kmo = _calculate_kmo(smoothed_mus_firing)

    # Standardize columns: equivalent to zscore(smoothed_mus_firing)
    column_mean = np.mean(smoothed_mus_firing, axis=0)
    column_std = np.std(smoothed_mus_firing, axis=0, ddof=1)

    if np.any(column_std == 0):
        raise ValueError(
            "At least one motor unit has zero standard deviation after "
            "smoothing. PCA cannot be performed."
        )

    z_smoothed_mus_firing = (smoothed_mus_firing - column_mean) / column_std

    # ----------------------------------
    # PCA using covariance matrix of standardized data
    # For standardized data, this is equivalent to correlation PCA.
    # ----------------------------------
    covariance_matrix = np.cov(z_smoothed_mus_firing, rowvar=False)

    eigenvalues, eigenvectors = np.linalg.eigh(covariance_matrix)

    # Sort descending
    sort_idx = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[sort_idx]
    eigenvectors = eigenvectors[:, sort_idx]

    explained_variance = (eigenvalues / np.sum(eigenvalues))*100
    cumulative_explained_variance = np.cumsum(explained_variance)

    # ----------------------------------
    # Estimate the number of components to retain
    # ----------------------------------
    # Option 1: Parallel analysis (default)
    if method_n_components == "parallel_analysis":
        # Parallel analysis
        def _parallel_analysis_eigenvalues(
            dataset,
            number_iterations_pa=1000,
            percentile_pa=95,
            rng=42,
        ):
            """
            Parallel analysis for PCA.

            Each motor unit column is independently shuffled, preserving the
            marginal distribution of each motor unit but destroying temporal
            covariance between them.

            Parameters
            ----------
            dataset : np.ndarray
                Data matrix with shape samples x motor units.
            number_iterations_pa : int, default 1000
                Number of shuffled datasets.
            percentile_pa : float, default 95
                Percentile of simulated eigenvalues.
            rng : np.random.Generator, default 42
                NumPy random generator.

            Returns
            -------
            mean_eigenvalues_pa : np.ndarray
                Mean simulated eigenvalue for each component.
            percentile_eigenvalues_pa : np.ndarray
                Percentile simulated eigenvalue for each component.
            """

            if dataset.ndim != 2:
                raise ValueError(
                    "dataset must be a 2D matrix: samples x features."
                )

            if rng is None:
                rng = np.random.default_rng()

            _, number_of_mus = dataset.shape

            simulated_eigenvalues = np.empty(
                (number_of_mus, number_iterations_pa),
                dtype=np.float64,
            )

            for iteration in range(number_iterations_pa):

                shuffled_dataset = np.empty_like(dataset)

                for mu_idx in range(number_of_mus):
                    shuffled_dataset[:, mu_idx] = rng.permutation(
                        dataset[:, mu_idx]
                    )

                corr_matrix = np.corrcoef(shuffled_dataset, rowvar=False)

                eigenvalues = np.linalg.eigvalsh(corr_matrix)

                eigenvalues = np.sort(eigenvalues)[::-1]

                simulated_eigenvalues[:, iteration] = eigenvalues

            mean_eigenvalues_pa = np.mean(
                simulated_eigenvalues,
                axis=1,
            )

            percentile_eigenvalues_pa = np.percentile(
                simulated_eigenvalues,
                percentile_pa,
                axis=1,
            )

            return mean_eigenvalues_pa, percentile_eigenvalues_pa
            # TODO mean_eigenvalues_pa is never used, do we really need to return it?

        # Run parallel analysis to get mean and percentile eigenvalues from
        # shuffled data.
        _, percentile_eigenvalues_pa = _parallel_analysis_eigenvalues(
            dataset=smoothed_mus_firing,
            number_iterations_pa=number_iterations_pa,
            percentile_pa=percentile_pa,
            rng=rng,
        )

        # Number of components with eigenvalues higher than simulated
        # percentile.
        number_of_components_retained = int(
            np.sum(eigenvalues > percentile_eigenvalues_pa)
        )

    # Option 2: Variance threshold method:
    elif method_n_components == "variance_greater_than_threshold":
        number_of_components_retained = int(
            np.sum(cumulative_explained_variance < variance_threshold)
        )
        percentile_eigenvalues_pa = None

    # Option 3: Eigenvalue > 1 method:
    elif method_n_components == "eigenvalue_greater_than_one":
        number_of_components_retained = int(np.sum(eigenvalues > 1.0))
        percentile_eigenvalues_pa = None

    else:
        raise ValueError(
            "Invalid method_n_components. The method must be one of the "
            "following: 'parallel_analysis', "
            "'variance_greater_than_threshold', or "
            "'eigenvalue_greater_than_one'."
        )

    if number_of_components_retained < 1:
        warnings.warn(
            "Parallel analysis selected zero components. "
            "number_of_components will be set to 1.",
            UserWarning,
        )
        number_of_components_retained = 1

    selected_eigenvectors = eigenvectors[:, :number_of_components_retained]

    # Principal component scores
    low_dimensional_components = z_smoothed_mus_firing @ selected_eigenvectors

    # Give results as a dataframe
    # Store results
    pca_results = {
        "smoothed_mus_firing": smoothed_mus_firing,

        "kmo": kmo,
        "method_n_components": method_n_components,
        "variance_threshold": variance_threshold,
        "percentile_eigenvalues_pa": percentile_eigenvalues_pa,
        "number_of_components_retained": number_of_components_retained,

        "eigenvalues": eigenvalues,
        "eigenvectors": eigenvectors,
        "explained_variance": explained_variance,
        "cumulative_explained_variance": cumulative_explained_variance,

        "low_dimensional_components": low_dimensional_components,
        }

    return pca_results


def common_drive_index(
    emgfile,
    window_type="hanning",
    window_duration_seconds=0.4,
    filter_highcut=0.75,
    filter_order=3,
    remove_edge_seconds=1.0,
    window_corr_seconds=5.0,
    overlap_corr_seconds=0.0,
    max_lag_seconds=0.1,
    number_of_surrogates=2,
    confidence_percentile=95,
    random_state=42,
):
    """
    Calculate the common drive index as the average pairwise cross-correlation
    between smoothed motor unit discharge profiles.

    Cross-correlation is calculated in windows of window_corr_seconds.
    For each motor unit pair, the maximum absolute correlation within
    +/- max_lag_seconds is extracted for each segment and then averaged
    across segments.

    References:

    - De Luca et al., 1985 (https://doi.org/10.1113/jphysiol.1982.sp014294)
    - Negro et al., 2009 (https://doi.org/10.1113/jphysiol.2009.178509)
    - Negro et al., 2012 (https://doi.org/10.1371/journal.pone.0044894)

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    window_duration_seconds : float, default 0.4
        Duration of the Hann window used to smooth binary spike trains.
    filter_highcut : float, default 0.75
        High-pass cutoff frequency used to remove offsets and slow trends.
    filter_order : int, default 3
        Butterworth filter order.
    remove_edge_seconds : float, default 1
        Number of seconds to remove from the beginning and end of the smoothed
        discharge profiles to avoid edge artifacts from convolution and
        filtering.
    window_corr_seconds : float, default 5.0
        Segment duration in seconds for pairwise cross-correlation.
        If -1, the entire signal is used.
    overlap_corr_seconds : float, default 0.0
        Overlap duration in seconds for pairwise cross-correlation.
        Segments will overlap by overlap_corr_seconds. 0.0 means no overlap.
    max_lag_seconds : float, default 0.1
        Maximum lag for cross-correlation, in seconds.

    Returns
    -------
    cdi_results : dict
        Dictionary containing pairwise correlations and common drive index with
        keys:

        - "smoothed_mus_firing": the smoothed binary spike trains
        calculated by window convolution (numpy array). smoothed_mus_firing
        has the same shape as the input binary_mus_firing (samples x motor
        units).
        - "pairwise_correlation": dataframe of average pairwise correlation
        and if it is significant for each motor unit pair (dataframe).
        - "pairwise_correlation_matrix": square matrix of average pairwise
        correlations between all motor unit pairs (numpy array).
        pairwise_correlation_matrix[i,j] contains the average pairwise
        correlation between motor unit i and j.
        - "pairwise_correlation_matrix_thresholded": thresholded
        pairwise_correlation_matrix (numpy array). correlation values that are
        not significant are set to zero.
        - "common_drive_index_mean": mean of cross-correlation values across
        all motor unit pairs (float).
        - "common_drive_index_std": standard deviation of cross-correlation
        values across all motor unit pairs (float).
        - "common_drive_index_thresholded_mean": mean of cross-correlation
        values across all motor unit pairs that are above the significance
        threshold (float).
        - "common_drive_index_thresholded_std": standard deviation of
        cross-correlation values across all motor unit pairs that are above
        the significance threshold (float).
        - "confidence_level": the confidence level used to determine if a
        pairwise correlation is significant (float).
        - "percentage_significant_pairs": percentage of motor unit pairs with
        significant correlation (float).
        - "corr_signals_all_pairs": list of numpy arrays containing the
        cross-correlation signals for all pairs (list of numpy arrays).
        - "grand_average_corr_values": grand average of the
        corr_signals_all_pairs (numpy array).
        - "lags_seconds": lags used to calculate the cross-correlation signals
        (numpy array).
    """

    # ----------------------------------
    # Validate inputs
    # ----------------------------------
    if not emgfile["MUPULSES"]:
        raise ValueError(
            "There are no motor unit pulses in the emgfile. "
            "Please check that MUPULSES is not empty."
        )

    fsamp = float(emgfile["FSAMP"])
    tot_mus = int(emgfile["NUMBER_OF_MUS"])

    if tot_mus < 2:
        raise ValueError(
            "At least 2 MUs are required for common drive index analysis."
        )

    if window_duration_seconds <= 0:
        raise ValueError("window_duration_seconds must be positive.")

    if overlap_corr_seconds < 0:
        raise ValueError("ovelap_corr_seconds must be positive.")

    if window_corr_seconds != -1 and window_corr_seconds <= 0:
        raise ValueError(
            "window_corr_seconds must be positive or -1 for no segmentation."
        )

    if window_corr_seconds != -1:
        if overlap_corr_seconds >= window_corr_seconds:
            raise ValueError(
                "overlap_corr_seconds must be smaller than "
                "window_corr_seconds."
            )

    if filter_highcut <= 0:
        raise ValueError("filter_highcut must be positive.")

    if filter_highcut >= fsamp / 2:
        raise ValueError(
            "filter_highcut must be lower than Nyquist frequency."
        )

    if max_lag_seconds < 0:
        raise ValueError("max_lag_seconds must be >= 0.")

    binary_mus_firing = emgfile["BINARY_MUS_FIRING"].to_numpy(dtype=np.int64)

    rng = np.random.default_rng(random_state)

    # ----------------------------------
    # Internal function to generate surrogate binary spike trains by shuffling
    # ISIs independently for each motor unit.
    # ----------------------------------
    def _generate_shuffled_binary_mus_firing(
        binary_mus_firing,
        total_n_mus,
        number_of_surrogates,
        rng,
    ):
        """
        Generate surrogate versions of binary_mus_firing by independently
        shuffling the interspike intervals of each motor unit.
        """

        surrogate_binary_mus_firing_list = []

        for surrogate_idx in range(number_of_surrogates):

            surrogate_binary_mus_firing = np.zeros_like(
                binary_mus_firing,
                dtype=np.int64,
            )
            n_samples = binary_mus_firing.shape[0]

            for mu_idx in range(total_n_mus):

                binary_spike_train = binary_mus_firing[:, mu_idx]
                spike_indices = np.flatnonzero(binary_spike_train)
                shuffled_spike_train = np.zeros(n_samples, dtype=np.int64)
                isi = np.diff(spike_indices)
                shuffled_isi = rng.permutation(isi)
                first_spike = spike_indices[0]

                shuffled_spike_indices = np.concatenate(
                    (
                        [first_spike],
                        first_spike + np.cumsum(shuffled_isi),
                    )
                )
                shuffled_spike_indices = shuffled_spike_indices[
                    (shuffled_spike_indices >= 0)
                    & (shuffled_spike_indices < n_samples)
                ]
                shuffled_spike_train[shuffled_spike_indices] = 1

                surrogate_binary_mus_firing[:, mu_idx] = shuffled_spike_train

            surrogate_binary_mus_firing_list.append(
                surrogate_binary_mus_firing
            )

        return surrogate_binary_mus_firing_list

    surrogate_binary_mus_firing_list = _generate_shuffled_binary_mus_firing(
        binary_mus_firing=binary_mus_firing,
        total_n_mus=tot_mus,
        number_of_surrogates=number_of_surrogates,
        rng=rng,
        )

    # Smooth binary spike trains by convolving with the window and scaling to
    # preserve units in pps.
    smoothed_mus_firing = smooth_spiketrains_convolution(
        binary_mus_firing,
        fsamp,
        window_type=window_type,
        window_duration_seconds=window_duration_seconds,
    )

    # Remove edge samples affected by convolution and filtering
    remove_edge_samples = int(round(fsamp * remove_edge_seconds))
    if remove_edge_samples > 0:
        smoothed_mus_firing = smoothed_mus_firing[
            remove_edge_samples: -remove_edge_samples, :
        ]

    # High-pass filter smoothed discharge rates
    sos = signal.butter(
        N=filter_order,
        Wn=filter_highcut,
        btype="highpass",
        output="sos",
        fs=fsamp,
    )
    smoothed_mus_firing = signal.sosfiltfilt(sos, smoothed_mus_firing, axis=0)

    # Apply the same smoothing and filtering to surrogate data
    surrogate_smoothed_mus_firing_list = []

    for surrogate_binary_mus_firing in surrogate_binary_mus_firing_list:

        surrogate_smoothed_mus_firing = smooth_spiketrains_convolution(
            surrogate_binary_mus_firing,
            fsamp,
            window_type=window_type,
            window_duration_seconds=window_duration_seconds,
        )

        if remove_edge_samples > 0:
            surrogate_smoothed_mus_firing = surrogate_smoothed_mus_firing[
                remove_edge_samples:-remove_edge_samples, :
            ]

        surrogate_smoothed_mus_firing = signal.sosfiltfilt(
            sos, surrogate_smoothed_mus_firing, axis=0,
        )

        surrogate_smoothed_mus_firing_list.append(
            surrogate_smoothed_mus_firing
        )

    n_samples = smoothed_mus_firing.shape[0]

    if window_corr_seconds == -1:
        segment_samples = n_samples
        overlap_corr_samples = segment_samples
    else:
        segment_samples = int(round(window_corr_seconds * fsamp))
        if overlap_corr_seconds == 0:
            overlap_corr_samples = segment_samples
        else:
            overlap_corr_samples = int(round(overlap_corr_seconds * fsamp))
    max_lag_samples = int(round(max_lag_seconds * fsamp))

    n_windows = int(
        np.floor((n_samples - segment_samples) / overlap_corr_samples) + 1
        )

    if n_windows < 1:
        raise ValueError(
            "The signal is shorter than window_corr_seconds after edge "
            "removal."
        )

    # ----------------------------------
    # Internal function to calculate normalized cross-correlation between two
    # signals with lag limits.
    # ----------------------------------
    # TODO compare this with norm_xcorr in mathtools and think if these can be
    # merged or _normalized_cross_correlation should be moved in mathtools.
    # Not urgent.
    def _normalized_cross_correlation(
        signal_1,
        signal_2,
        max_lag_samples,
    ):
        """
        Returns normalized cross-correlation values and lags.
        """

        signal_1 = signal_1 - np.mean(signal_1)
        signal_2 = signal_2 - np.mean(signal_2)

        denominator = np.sqrt(
            np.sum(signal_1 ** 2) * np.sum(signal_2 ** 2)
        )

        if denominator == 0:
            corr_values = np.zeros(2 * max_lag_samples + 1)
            lags = np.arange(-max_lag_samples, max_lag_samples + 1)
            return corr_values, lags

        full_corr = signal.correlate(
            signal_1,
            signal_2,
            mode="full",
            method="auto",
        )

        full_corr = full_corr / denominator

        full_lags = signal.correlation_lags(
            len(signal_1),
            len(signal_2),
            mode="full",
        )

        lag_mask = (
            (full_lags >= -max_lag_samples)
            & (full_lags <= max_lag_samples)
        )

        corr_values = full_corr[lag_mask]
        lags = full_lags[lag_mask]

        return corr_values, lags

    # ----------------------------------
    # Pairwise cross-correlation
    # ----------------------------------
    pair_results = []
    pairwise_correlation_matrix = np.eye(
        tot_mus,
        dtype=np.float64,
    )
    corr_signals_all_pairs = []
    lags_seconds = None
    surrogate_peak_correlations_all = []
    for mu_1, mu_2 in combinations(range(tot_mus), 2):

        segment_correlations = []
        corr_values_all_windows = []
        for window_idx in range(n_windows):

            start_idx = window_idx * overlap_corr_samples
            end_idx = start_idx + segment_samples

            signal_1 = smoothed_mus_firing[start_idx:end_idx, mu_1]
            signal_2 = smoothed_mus_firing[start_idx:end_idx, mu_2]

            corr_values, lags = _normalized_cross_correlation(
                signal_1,
                signal_2,
                max_lag_samples=max_lag_samples,
            )

            corr_values_all_windows.append(corr_values)
            if lags_seconds is None:
                lags_seconds = lags / fsamp
            peak_correlation = np.max(corr_values)
            segment_correlations.append(peak_correlation)

        # Store average correlation values across windows for this pair
        corr_values_all_windows = np.asarray(
            corr_values_all_windows, dtype=np.float64,
        )
        average_corr_values = np.mean(
            corr_values_all_windows, axis=0,
        )
        corr_signals_all_pairs.append(average_corr_values)

        # ----------------------------------
        # Pairwise cross-correlation
        # ----------------------------------
        for surrogate_idx_1 in range(number_of_surrogates):

            for surrogate_idx_2 in range(number_of_surrogates):

                surrogate_segment_correlations = []
                # surrogate_corr_values_all_windows = []
                for window_idx in range(n_windows):

                    start_idx = window_idx * overlap_corr_samples
                    end_idx = start_idx + segment_samples

                    signal_1_surrogate = surrogate_smoothed_mus_firing_list[
                        surrogate_idx_1
                    ][start_idx:end_idx, mu_1]

                    signal_2_surrogate = surrogate_smoothed_mus_firing_list[
                        surrogate_idx_2
                    ][start_idx:end_idx, mu_2]

                    corr_values_surrogate, _ = _normalized_cross_correlation(
                        signal_1_surrogate,
                        signal_2_surrogate,
                        max_lag_samples=max_lag_samples,
                    )

                    surrogate_peak_correlation = np.max(
                        corr_values_surrogate
                    )
                    surrogate_segment_correlations.append(
                        surrogate_peak_correlation
                    )

                surrogate_mean_peak_correlation = np.mean(
                    surrogate_segment_correlations
                )
                surrogate_peak_correlations_all.append(
                    surrogate_mean_peak_correlation
                )

        pair_results.append(
            {
                "mu_1": mu_1,
                "mu_2": mu_2,
                "mean_correlation": np.mean(segment_correlations),
                "std_correlation": np.std(segment_correlations, ddof=1),
            }
        )

        # Fill symmetric matrix
        pairwise_correlation_matrix[mu_1, mu_2] = np.mean(segment_correlations)
        pairwise_correlation_matrix[mu_2, mu_1] = np.mean(segment_correlations)

    # Transpose corr_signals_all_pairs to have shape n_lags x n_pairs
    corr_signals_all_pairs = np.array(corr_signals_all_pairs).T
    lags_seconds = np.asarray(lags_seconds, dtype=np.float64)

    # Calculate the grand average correlation values across all pairs
    grand_average_corr_values = np.mean(corr_signals_all_pairs, axis=1)

    # Convert to dataframe
    pairwise_correlation = pd.DataFrame(pair_results)

    # Calculate confidence level from surrogate data
    surrogate_peak_correlations_all = np.asarray(
        surrogate_peak_correlations_all, dtype=np.float64,
    )
    confidence_level = np.percentile(
        surrogate_peak_correlations_all, confidence_percentile,
    )

    # Add a column in the dataframe indicating whether the mean pair
    # correlation is above the confidence level.
    significant_mask = (
        pairwise_correlation["mean_correlation"] > confidence_level
    )
    pairwise_correlation["significant"] = significant_mask

    # Thresholded square correlation matrix
    pairwise_correlation_matrix_thresholded = pairwise_correlation_matrix.copy()
    pairwise_correlation_matrix_thresholded[
        pairwise_correlation_matrix_thresholded < confidence_level
    ] = 0.0

    # Calculate the common drive index as the average of the mean correlations
    # across all pairs.
    common_drive_index_mean = pairwise_correlation["mean_correlation"].mean()
    common_drive_index_std = pairwise_correlation["mean_correlation"].std(
        ddof=1,
    )

    # Calculate the common drive index considering only pairs above the
    # confidence level.
    n_significant_pairs = int(np.sum(significant_mask))
    if n_significant_pairs > 0:
        common_drive_index_thresholded_mean = (
            pairwise_correlation.loc[
                significant_mask,
                "mean_correlation",
            ].mean()
        )
        common_drive_index_thresholded_std = (
            pairwise_correlation.loc[
                significant_mask,
                "mean_correlation",
            ].std(ddof=1)
        )
    else:
        common_drive_index_thresholded_mean = 0.0
        common_drive_index_thresholded_std = 0.0

    cdi_results = {
        "smoothed_mus_firing": smoothed_mus_firing,

        "pairwise_correlation": pairwise_correlation,
        "pairwise_correlation_matrix": pairwise_correlation_matrix,
        "pairwise_correlation_matrix_thresholded": pairwise_correlation_matrix_thresholded,
        "common_drive_index_mean": common_drive_index_mean,
        "common_drive_index_std": common_drive_index_std,
        "common_drive_index_thresholded_mean": common_drive_index_thresholded_mean,
        "common_drive_index_thresholded_std": common_drive_index_thresholded_std,
        "confidence_level": confidence_level,
        "percentage_significant_pairs": 100 * n_significant_pairs / len(pairwise_correlation),

        "corr_signals_all_pairs": corr_signals_all_pairs,
        "grand_average_corr_values": grand_average_corr_values,
        "lags_seconds": lags_seconds,
    }

    return cdi_results


def pci_index(
    emgfile,
    number_iterations=100,
    window_type="hanning",
    window_duration_seconds=1.0,
    overlap_seconds=0.0,
    nfft=None,
    delta_frequency_range=[1, 5],
    alpha_frequency_range=[5, 15],
    beta_frequency_range=[15, 35],
    random_state=42,
):
    """
    Estimate the proportion of common input index (PCI) from motor unit spike
    trains.

    This implementation follows the logic of Negro et al. (2016), where
    coherence is calculated between two CSTs containing n motor units each.
    The number of motor units per CST is varied from 1 to floor (total number
    of MUs / 2).

    The relationship between average coherence and number of units per CST is
    fitted using Eq. 4:

        C(n) = ((n^2 * A)^2) / ((n * B + n^2 * A)^2)

    PCI is then calculated as:

        PCI = sqrt(A / B)

    References:

    - Negro et al., 2016 (https://doi.org/10.1113/JP271748).

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    number_iterations : int, default 100
        Number of random permutations. If the number of unique splits
        is smaller than number_iterations, all unique splits are used.
    window_type : str, default "hanning"
        Type of window used for spectral estimation.
    window_duration_seconds : float, default 1
        Size of the window for coherence estimation in seconds.
    overlap_seconds : float, default 0
        Number of seconds of overlap between adjoining segments.
    nfft : int, optional
        Number of FFT points.
        If None, defaults to 10 * fsamp.
    delta_frequency_range : list, default [1, 5]
        Delta frequency range in Hz.
    alpha_frequency_range : list, default [5, 15]
        Alpha frequency range in Hz.
    beta_frequency_range : list, default [15, 35]
        Beta frequency range in Hz.
    random_state : int, default 42
        Random seed for reproducible random permutations.

    Returns
    -------
    pci_results : dict
        Dictionary containing coherence-vs-CST-size values and fitted PCI
        values. Keys are:

        - "pci_coherence_df": dataframe containing the number of MUs per CST
        and the corresponding average coherence values for each frequency band
        (dataframe).
        - "fitted_pci_coherence_df": dataframe containing the number of MUs
        per CST and the corresponding fitted coherence values using the fitted
        A and B parameters for each frequency band (dataframe).
        - "pci_fit_df": dataframe containing the fitted A and B parameters,
        and the PCI index for each frequency band (dataframe).

    Notes
    -------
    The PCI index is typically implemented only for the delta band (see Negro
    et al., 2016), but this function also fits the model and estimates the PCI
    for alpha and beta bands.
    """

    # ----------------------------------
    # Validate inputs
    # ----------------------------------
    if not emgfile["MUPULSES"]:
        raise ValueError(
            "There are no motor unit pulses in the emgfile. "
            "Please check that MUPULSES is not empty."
        )

    fsamp = float(emgfile["FSAMP"])
    tot_mus = int(emgfile["NUMBER_OF_MUS"])

    if tot_mus < 4:
        raise ValueError(
            "At least 4 motor units are required to estimate PCI."
        )

    if window_duration_seconds <= 0:
        raise ValueError("window_duration_seconds must be positive.")

    if overlap_seconds < 0:
        raise ValueError("overlap_seconds must be >= 0.")

    binary_mus_firing = emgfile["BINARY_MUS_FIRING"].to_numpy(dtype=np.int64)

    rng = np.random.default_rng(random_state)

    # ----------------------------------
    # Spectral parameters
    # ----------------------------------
    window_samples = int(round(fsamp * window_duration_seconds))

    if window_type == "hanning":
        window = signal.windows.hann(window_samples, sym=True)
    elif window_type == "hamming":
        window = signal.windows.hamming(window_samples, sym=True)
    else:
        raise ValueError(
            "Unsupported window_type. Supported types are 'hanning' and "
            "'hamming'."
        )

    overlap_samples = int(round(fsamp * overlap_seconds))

    if overlap_samples >= window_samples:
        raise ValueError(
            "overlap_seconds must be smaller than window_duration_seconds."
        )

    if nfft is None:
        nfft = int(round(10 * fsamp))

    max_units_per_cst = tot_mus // 2

    n_units_per_cst = np.arange(1, max_units_per_cst + 1, dtype=np.int64)

    pci_rows = []

    # ----------------------------------
    # Internal function to calculate pooled coherence for a fixed number of
    # MUs per CST.
    # ----------------------------------
    def _pooled_coherence_for_fixed_cst_size(
        binary_mus_firing,
        fsamp,
        tot_mus,
        number_of_mus_cst,
        number_iterations,
        window,
        overlap_samples,
        nfft,
        rng,
    ):
        """
        Calculate pooled CST-CST coherence for one fixed number of MUs per CST.

        This is similar to pooled_intramuscular_coherence(), but uses a fixed
        number_of_mus_cst and is intended for PCI estimation.
        """

        unique_split_count = (
            comb(tot_mus, number_of_mus_cst)
            * comb(tot_mus - number_of_mus_cst, number_of_mus_cst)
            // 2
        )

        use_all_unique_splits = unique_split_count < number_iterations

        if use_all_unique_splits:
            msg = (
                f"Only {unique_split_count} unique CST group splits are "
                "possible. number_iterations will be set to "
                f"{unique_split_count}.",
            )
            warnings.warn(msg, UserWarning)

            group_pairs = []
            used_splits = set()

            all_units = np.arange(tot_mus)

            for group_1 in combinations(all_units, number_of_mus_cst):

                remaining_units = np.setdiff1d(all_units, group_1)

                for group_2 in combinations(remaining_units, number_of_mus_cst):

                    group_1_tuple = tuple(sorted(group_1))
                    group_2_tuple = tuple(sorted(group_2))

                    split_key = tuple(sorted([group_1_tuple, group_2_tuple]))

                    if split_key not in used_splits:
                        used_splits.add(split_key)

                        group_pairs.append(
                            (
                                np.asarray(group_1_tuple, dtype=np.int64),
                                np.asarray(group_2_tuple, dtype=np.int64),
                            )
                        )

            number_iterations = len(group_pairs)

        else:
            group_pairs = None

        pooled_auto_spectra_1 = None
        pooled_auto_spectra_2 = None
        pooled_cross_spectra = None
        frequency = None

        for iteration in range(number_iterations):

            if use_all_unique_splits:

                group_1_indices, group_2_indices = group_pairs[iteration]

            else:

                unit_indices = rng.permutation(tot_mus)

                group_1_indices = unit_indices[:number_of_mus_cst]
                group_2_indices = unit_indices[-number_of_mus_cst:]

            cst_1 = np.sum(binary_mus_firing[:, group_1_indices], axis=1)
            cst_2 = np.sum(binary_mus_firing[:, group_2_indices], axis=1)

            cst_1 = signal.detrend(cst_1, type="constant")
            cst_2 = signal.detrend(cst_2, type="constant")

            frequency, auto_spectra_1 = signal.csd(
                cst_1,
                cst_1,
                fs=fsamp,
                window=window,
                noverlap=overlap_samples,
                nfft=nfft,
                detrend=False,
                return_onesided=True,
                scaling="density",
            )

            _, auto_spectra_2 = signal.csd(
                cst_2,
                cst_2,
                fs=fsamp,
                window=window,
                noverlap=overlap_samples,
                nfft=nfft,
                detrend=False,
                return_onesided=True,
                scaling="density",
            )

            _, cross_spectra = signal.csd(
                cst_1,
                cst_2,
                fs=fsamp,
                window=window,
                noverlap=overlap_samples,
                nfft=nfft,
                detrend=False,
                return_onesided=True,
                scaling="density",
            )

            if pooled_auto_spectra_1 is None:
                pooled_auto_spectra_1 = np.zeros_like(
                    auto_spectra_1,
                    dtype=np.float64,
                )
                pooled_auto_spectra_2 = np.zeros_like(
                    auto_spectra_2,
                    dtype=np.float64,
                )
                pooled_cross_spectra = np.zeros_like(
                    cross_spectra,
                    dtype=np.complex128,
                )

            pooled_auto_spectra_1 += auto_spectra_1
            pooled_auto_spectra_2 += auto_spectra_2
            pooled_cross_spectra += cross_spectra

        pooled_auto_spectra_1 /= number_iterations
        pooled_auto_spectra_2 /= number_iterations
        pooled_cross_spectra /= number_iterations

        coherence = np.abs(pooled_cross_spectra) ** 2 / (
            pooled_auto_spectra_1 * pooled_auto_spectra_2
        )

        coherence = np.asarray(coherence, dtype=np.float64)
        frequency = np.asarray(frequency, dtype=np.float64)

        return {
            "coherence": coherence,
            "frequency": frequency,
        }

    # ----------------------------------
    # Internal function to average coherence within a frequency band
    # ----------------------------------
    def _average_coherence_in_band(
        coherence,
        frequency,
        frequency_range,
    ):
        """
        Average raw coherence within a frequency band.

        For PCI, this is not thresholded by significance, following
        the original method.
        """

        lower_freq, upper_freq = frequency_range

        band_mask = (
            (frequency >= lower_freq)
            & (frequency < upper_freq)
        )

        if not np.any(band_mask):
            return np.nan

        return float(np.mean(coherence[band_mask]))

    # ----------------------------------
    # Loop over number of units per CST
    # ----------------------------------
    for number_of_mus_cst in n_units_per_cst:

        print(
            f"Calculating coherence for {number_of_mus_cst} "
            f"motor unit(s) per CST..."
        )

        coherence_results_n = _pooled_coherence_for_fixed_cst_size(
            binary_mus_firing=binary_mus_firing,
            fsamp=fsamp,
            tot_mus=tot_mus,
            number_of_mus_cst=number_of_mus_cst,
            number_iterations=number_iterations,
            window=window,
            overlap_samples=overlap_samples,
            nfft=nfft,
            rng=rng,
        )

        coherence = coherence_results_n["coherence"]
        frequency = coherence_results_n["frequency"]

        average_delta = _average_coherence_in_band(
            coherence,
            frequency,
            delta_frequency_range,
        )

        average_alpha = _average_coherence_in_band(
            coherence,
            frequency,
            alpha_frequency_range,
        )

        average_beta = _average_coherence_in_band(
            coherence,
            frequency,
            beta_frequency_range,
        )

        pci_rows.append(
            {
                "number_of_mus_cst": number_of_mus_cst,
                "average_delta": average_delta,
                "average_alpha": average_alpha,
                "average_beta": average_beta,
            }
        )

    average_coherence_df = pd.DataFrame(pci_rows)

    # ----------------------------------
    # Internal function to calculate the PCI model values for a given n, A, B.
    # ----------------------------------
    def _pci_model(
        n,
        A,
        B,
    ):
        """
        Eq. 4 from Negro et al., 2016.

        C(n) = ((n^2 * A)^2) / ((n * B + n^2 * A)^2)
        """

        numerator = (n ** 2 * A) ** 2
        denominator = (n * B + n ** 2 * A) ** 2

        return numerator / denominator

    # ----------------------------------
    # Internal function to fit the PCI model
    # ----------------------------------
    def _fit_pci_model(
        n_units,
        average_coherence,
        params0=(1e-3, 1e-1),
    ):
        """
        Fit PCI model and calculate PCI = sqrt(A / B).
        """

        valid_mask = (
            np.isfinite(n_units)
            & np.isfinite(average_coherence)
        )

        n_units_valid = n_units[valid_mask]
        coherence_valid = average_coherence[valid_mask]

        try:
            params_fit, _ = curve_fit(
                _pci_model,
                n_units_valid,
                coherence_valid,
                p0=params0,
                bounds=([0.0, 0.0], [np.inf, np.inf]),
                maxfev=100000,
            )

            A, B = params_fit

            fitted_coherence = _pci_model(n_units, A, B)

            if B > 0:
                PCI = np.sqrt(A / B)
            else:
                PCI = np.nan

            return {
                "A": float(A),
                "B": float(B),
                "PCI": float(PCI),
                "fitted_coherence": fitted_coherence,
            }

        except Exception as error:

            warnings.warn(
                f"PCI model fitting failed: {error}",
                UserWarning,
            )

            return {
                "A": np.nan,
                "B": np.nan,
                "PCI": np.nan,
                "fitted_coherence": np.full_like(n_units, np.nan, dtype=float),
            }

    # ----------------------------------
    # Fit Eq. 4 for each frequency band
    # ----------------------------------
    fit_results = {}
    for band_name, column_name in {
        "delta": "average_delta",
        "alpha": "average_alpha",
        "beta": "average_beta",
    }.items():

        fit_results[band_name] = _fit_pci_model(
            n_units=average_coherence_df["number_of_mus_cst"],
            average_coherence=average_coherence_df[column_name],
        )

    pci_fit_df = pd.DataFrame(
        [
            {
                "band": band_name,
                "A": fit["A"],
                "B": fit["B"],
                "PCI": fit["PCI"],
            }
            for band_name, fit in fit_results.items()
        ]
    )

    fitted_average_coherence_df = pd.DataFrame(
        {
            "number_of_mus_cst": average_coherence_df["number_of_mus_cst"],
            "fitted_delta": fit_results["delta"]["fitted_coherence"],
            "fitted_alpha": fit_results["alpha"]["fitted_coherence"],
            "fitted_beta": fit_results["beta"]["fitted_coherence"],
        }
    )

    pci_results = {
        "pci_fit_df": pci_fit_df,
        "average_coherence_df": average_coherence_df,
        "fitted_average_coherence_df": fitted_average_coherence_df,
    }

    return pci_results


def network_information_framework(
    emgfile,
    window_type="hanning",
    window_duration_seconds=0.4,
    filter_highcut=0.75,
    filter_order=3,
    remove_edge_seconds=1.0,
    type_clustering="single",
):
    """
    Estimate non-linear dependencies between MUs using pairwise mutual
    information.

    This method:

    1. Smooths binary motor unit spike trains.
    2. High-pass filters the smoothed discharge rates.
    3. Copula-normalizes each motor unit discharge-rate profile.
    4. Estimates pairwise Gaussian mutual information between motor units.
    5. Constructs a symmetric mutual-information network.
    6. Applies modified percolation analysis to identify a network threshold.
    7. Applies link-community detection to identify overlapping modules.

    References:

    - O'Reilly & Delis, 2022 (https://doi.org/10.1088/1741-2552/ac5150)
    - O'Reilly & Delis, 2024 (https://doi.org/10.7554/eLife.87651.4)
    - Cabral et al., 2025 (https://doi.org/10.1016/j.isci.2025.113483)

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    window_duration_seconds : float, default 0.4
        Duration of the Hann window used to smooth binary spike trains.
    filter_highcut : float, default 0.75
        High-pass cutoff frequency used to remove offsets and slow trends.
    filter_order : int, default 3
        Butterworth filter order.
    remove_edge_seconds : float, default 1
        Number of seconds to remove from the beginning and end of the smoothed
        discharge profiles to avoid edge artifacts from convolution and
        filtering.
    type_clustering : str {"single", "complete"}, default "single"
        Link-community clustering type.

        ``single``

        ``complete``

    Returns
    -------
    network_results : dict
        Dictionary containing keys:

        - smoothed_mus_firing: the smoothed binary spike trains calculated by
        window convolution (numpy array). smoothed_mus_firing has the same
        shape as the input binary_mus_firing (samples x motor units).
        - pairwise_mi: dataframe of average pairwise mutual information and if
        it is significant for each motor unit pair (dataframe).
        - pairwise_mi_matrix: square matrix of average pairwise mutual
        information between all motor unit pairs (numpy array).
        pairwise_mi_matrix[i,j] contains the average pairwise mutual
        information between motor unit i and j.
        - pairwise_mi_matrix_thresholded : thresholded mutual-information
        matrix (numpy array). Mutual-information values that are not
        significant are set to zero.
        - network_density : network density after thresholding (float)
        - confidence_level : the confidence level calculated using the
        percolation analysis to determine if a mutual-information value is
        significant (float).
        - percentage_significant_pairs: percentage of motor unit pairs with
        significant mutual information (float).
        - module_affiliation_matrix: binary matrix indicating the module
        affiliation of each motor unit (numpy array).
        module_affiliation_matrix[i,j] is 1 if motor unit j belongs to
        component (or community) i, and 0 otherwise.
        - number_of_components: number of low-dimensional components
        (communities) of the mutual-information network (int).
        - percentage_mus_first_component: percentage of motor units that
        belong to the first component (float).
    """

    # ----------------------------------
    # Validate inputs
    # ----------------------------------
    if not emgfile["MUPULSES"]:
        raise ValueError(
            "There are no motor unit pulses in the emgfile. "
            "Please check that MUPULSES is not empty."
        )

    fsamp = float(emgfile["FSAMP"])
    tot_mus = int(emgfile["NUMBER_OF_MUS"])

    if tot_mus < 2:
        raise ValueError(
            "At least 2 MUs are required for network-information analysis."
        )

    if window_duration_seconds <= 0:
        raise ValueError("window_duration_seconds must be positive.")

    if filter_highcut <= 0:
        raise ValueError("filter_highcut must be positive.")

    if filter_highcut >= fsamp / 2:
        raise ValueError(
            "filter_highcut must be lower than Nyquist frequency."
        )

    if type_clustering not in ["single", "complete"]:
        raise ValueError("type_clustering must be 'single' or 'complete'.")

    binary_mus_firing = emgfile["BINARY_MUS_FIRING"].to_numpy(dtype=np.int64)

    warnings.warn(
        "Important! emgfile['BINARY_MUS_FIRING'] was converted to int64 "
        "to avoid overflow errors.",
        UserWarning,
    )

    # ----------------------------------
    # Smooth binary spike trains
    # ----------------------------------
    smoothed_mus_firing = smooth_spiketrains_convolution(
        binary_mus_firing,
        fsamp,
        window_type=window_type,
        window_duration_seconds=window_duration_seconds,
    )

    # ----------------------------------
    # Remove edge samples affected by convolution/filtering
    # ----------------------------------
    remove_edge_samples = int(round(fsamp * remove_edge_seconds))

    if remove_edge_samples > 0:
        if 2 * remove_edge_samples >= smoothed_mus_firing.shape[0]:
            raise ValueError(
                "remove_edge_seconds is too large for the signal duration."
            )

        smoothed_mus_firing = smoothed_mus_firing[
            remove_edge_samples:-remove_edge_samples,
            :
        ]

    # ----------------------------------
    # High-pass filter smoothed discharge rates
    # ----------------------------------
    sos = signal.butter(
        N=filter_order,
        Wn=filter_highcut,
        btype="highpass",
        output="sos",
        fs=fsamp,
    )

    smoothed_mus_firing = signal.sosfiltfilt(
        sos,
        smoothed_mus_firing,
        axis=0,
    )

    # ----------------------------------
    # Network-information analysis
    # ----------------------------------

    # -----------------------------------
    # Step 1: Copula normalization
    # -----------------------------------

    # ----------------------------------
    # Internal function to perform copula normalization
    # ----------------------------------
    def _copnorm(x):
        """
        Copula normalization.

        Parameters
        ----------
        x : np.ndarray
            Matrix with shape samples x variables.

        Returns
        -------
        x_norm : np.ndarray
            Copula-normalized matrix.
        """

        n_samples, n_variables = x.shape

        ranks = np.empty_like(x, dtype=np.float64)

        for col in range(n_variables):
            order = np.argsort(x[:, col], kind="mergesort")
            rank = np.empty(n_samples, dtype=np.float64)
            rank[order] = np.arange(1, n_samples + 1)
            ranks[:, col] = rank

        x_cdf = ranks / (n_samples + 1)

        x_norm = -np.sqrt(2) * erfcinv(2 * x_cdf)

        return x_norm

    X = smoothed_mus_firing
    X_norm = _copnorm(X)

    # -----------------------------------
    # Step 2: Pairwise mutual information
    # -----------------------------------

    # -----------------------------------
    # Internal function to calculate mutual information between two Gaussian
    # variables.
    # -----------------------------------
    def _mi_gg(
        x,
        y,
        biascorrect=True,
        demeaned=False,
    ):
        """
        Mutual information between two Gaussian variables in bits.

        Parameters
        ----------
        x : np.ndarray
            Samples x variables.
        y : np.ndarray
            Samples x variables.
        biascorrect : bool, default True
            Apply bias correction.
        demeaned : bool, default False
            Whether data are already zero-mean.

        Returns
        -------
        I : float
            Mutual information in bits.
        """

        if x.ndim == 1:
            x = x.reshape(-1, 1)
        if y.ndim == 1:
            y = y.reshape(-1, 1)

        if x.ndim != 2 or y.ndim != 2:
            raise ValueError("_mi_gg: input arrays should be 2D.")

        n_trials = x.shape[0]
        n_var_x = x.shape[1]
        n_var_y = y.shape[1]

        if not demeaned:
            x = x - np.sum(x, axis=0) / n_trials
            y = y - np.sum(y, axis=0) / n_trials

        xy = np.concatenate((x, y), axis=1)

        Cxy = (xy.T @ xy) / (n_trials - 1)

        Cx = Cxy[:n_var_x, :n_var_x]

        y_start = n_var_x
        n_var_xy = n_var_x + n_var_y

        Cy = Cxy[y_start:n_var_xy, y_start:n_var_xy]

        # Cholesky decomposition
        ch_Cx = np.linalg.cholesky(Cx)
        ch_Cy = np.linalg.cholesky(Cy)
        ch_Cxy = np.linalg.cholesky(Cxy)

        HX = np.sum(np.log(np.diag(ch_Cx)))
        HY = np.sum(np.log(np.diag(ch_Cy)))
        HXY = np.sum(np.log(np.diag(ch_Cxy)))

        ln2 = np.log(2)

        if biascorrect:

            psi_terms = digamma(
                (n_trials - np.arange(1, n_var_xy + 1)) / 2
            ) / 2

            dterm = (ln2 - np.log(n_trials - 1)) / 2

            HX = HX - n_var_x * dterm - np.sum(psi_terms[:n_var_x])
            HY = HY - n_var_y * dterm - np.sum(
                psi_terms[n_var_x:n_var_xy]
            )
            HXY = HXY - n_var_xy * dterm - np.sum(psi_terms)

        I = (HX + HY - HXY) / ln2

        return float(I)  # TODO ambiguous variable name 'I' Flake8(E741), do not use I or O as variable names

    pairwise_mi_matrix = np.zeros((tot_mus, tot_mus), dtype=np.float64)
    mi_rows = []
    for mu_1, mu_2 in combinations(range(tot_mus), 2):

        I = _mi_gg(
            X_norm[:, mu_1],
            X_norm[:, mu_2],
            biascorrect=True,
            demeaned=True,
        )

        pairwise_mi_matrix[mu_1, mu_2] = I
        pairwise_mi_matrix[mu_2, mu_1] = I

        mi_rows.append(
            {
                "mu_1": mu_1,
                "mu_2": mu_2,
                "mutual_information": I,
            }
        )

    pairwise_mi = pd.DataFrame(mi_rows)

    # -----------------------------------
    # Step 3: Modified percolation threshold
    # -----------------------------------

    # -----------------------------------
    # Internal function to calculate the number of connected components
    # -----------------------------------
    def _number_connected_components(A):
        """
        Return the number of connected components in an undirected adjacency
        matrix.
        """

        A = np.asarray(A)

        adjacency = (A != 0)

        # Symmetrize
        adjacency = adjacency | adjacency.T

        n_components, labels = connected_components(
            adjacency,
            directed=False,
            return_labels=True,
        )

        return int(n_components), labels

    # -----------------------------------
    # Internal function to apply absolute thresholding
    # -----------------------------------
    def _threshold_absolute(W, threshold):
        """
        Absolute thresholding.
        """

        W = np.asarray(W, dtype=np.float64).copy()

        np.fill_diagonal(W, 0.0)

        W[W < threshold] = 0.0

        return W

    # -----------------------------------
    # Internal function to apply modified percolation analysis
    # -----------------------------------
    def _modified_percolation_analysis(A):
        """
        Modified percolation analysis.

        Parameters
        ----------
        A : np.ndarray
            Weighted adjacency matrix.

        Returns
        -------
        threshold : float
            Absolute threshold value to apply to A.
        """

        threshold = np.finfo(float).tiny

        n_components, _ = _number_connected_components(A)

        if n_components > 1:
            warnings.warn(
                "Network already has more than one connected component.",
                UserWarning,
            )
            threshold = np.min(A)
            return float(threshold)

        a = np.max(A)
        b = np.min(A)

        tolerance = 1e-12
        i = 1
        imax = 10000

        condition_iterations = True
        condition_tolerance = True

        while condition_iterations and condition_tolerance:

            condition_iterations = i < imax
            condition_tolerance = abs(b - a) / 2 > tolerance

            c = (a + b) / 2

            n_components_c, _ = _number_connected_components(
                _threshold_absolute(A, c) != 0
            )

            if (n_components_c - 1 == 0) or ((b - a) / 2 < tolerance):
                threshold = c

            n_components_a, _ = _number_connected_components(
                _threshold_absolute(A, a) != 0
            )

            if np.sign(n_components_c - 1) == np.sign(n_components_a - 1):
                a = c
            else:
                b = c

            i += 1

        return float(threshold)

    confidence_level = _modified_percolation_analysis(pairwise_mi_matrix)

    # Add a column in the dataframe indicating whether the mean pair
    # correlation is above the confidence level.
    significant_mask = (pairwise_mi["mutual_information"] > confidence_level)
    pairwise_mi["significant"] = significant_mask
    n_significant_pairs = int(np.sum(significant_mask))

    # Thresholded network
    pairwise_mi_matrix_thresholded = pairwise_mi_matrix.copy()
    pairwise_mi_matrix_thresholded[
        pairwise_mi_matrix_thresholded < confidence_level
    ] = 0.0
    pairwise_mi_matrix_thresholded[pairwise_mi_matrix_thresholded < 0] = 0.0

    # ------------------------------------
    # Step 4: Link-community detection
    # ------------------------------------

    def _link_communities(
        W,
        type_clustering="single",
    ):
        """
        Link-community detection.

        Parameters
        ----------
        W : np.ndarray
            Weighted adjacency matrix.
        type_clustering : str, default "single"
            "single" or "complete".

        Returns
        -------
        M : np.ndarray
            Binary module affiliation matrix, shape components x nodes.
        """

        W = np.asarray(W, dtype=np.float64).copy()

        n = W.shape[0]

        np.fill_diagonal(W, 0.0)

        max_weight = np.max(W)

        if max_weight <= 0:
            return np.zeros((0, n), dtype=int)

        W = W / max_weight

        # ------------------------------------------------------------
        # Set diagonal to mean connection weight
        # ------------------------------------------------------------
        out_counts = np.sum(W != 0, axis=0)
        in_counts = np.sum(W.T != 0, axis=0)

        col_sum = np.sum(W, axis=0)
        row_sum = np.sum(W.T, axis=0)

        with np.errstate(divide="ignore", invalid="ignore"):
            diagonal_values = (
                (col_sum / out_counts)
                + (row_sum / in_counts)
            ) / 2

        diagonal_values[~np.isfinite(diagonal_values)] = 0.0

        np.fill_diagonal(W, diagonal_values)

        # ------------------------------------------------------------
        # Node similarity
        # ------------------------------------------------------------
        No = np.sum(W ** 2, axis=1)
        Ni = np.sum(W ** 2, axis=0)

        Jo = np.zeros((n, n), dtype=np.float64)
        Ji = np.zeros((n, n), dtype=np.float64)

        for b in range(n):
            for c in range(n):

                Do = W[b, :] @ W[c, :].T
                denom_o = No[b] + No[c] - Do

                if denom_o != 0:
                    Jo[b, c] = Do / denom_o

                Di = W[:, b].T @ W[:, c]
                denom_i = Ni[b] + Ni[c] - Di

                if denom_i != 0:
                    Ji[b, c] = Di / denom_i

        # ------------------------------------------------------------
        # Link list
        # ------------------------------------------------------------
        edge_mask = ((W != 0) | (W.T != 0)) & np.triu(
            np.ones((n, n), dtype=bool),
            k=1,
        )

        A_idx, B_idx = np.where(edge_mask)

        m = len(A_idx)

        if m == 0:
            return np.zeros((0, n), dtype=int)

        Ln = np.zeros((m, 2), dtype=int)
        Lw = np.zeros(m, dtype=np.float64)

        for i in range(m):
            Ln[i, :] = [A_idx[i], B_idx[i]]
            Lw[i] = (W[A_idx[i], B_idx[i]] + W[B_idx[i], A_idx[i]]) / 2

        if m == 1:
            M = np.zeros((1, n), dtype=int)
            M[0, np.unique(Ln[0, :])] = 1
            M = M[np.sum(M, axis=1) > 2, :]
            return M

        # ------------------------------------------------------------
        # Link similarity
        # ------------------------------------------------------------
        ES = np.zeros((m, m), dtype=np.float32)

        for i in range(m):
            for j in range(m):

                if Ln[i, 0] == Ln[j, 0]:
                    a = Ln[i, 0]
                    b = Ln[i, 1]
                    c = Ln[j, 1]

                elif Ln[i, 0] == Ln[j, 1]:
                    a = Ln[i, 0]
                    b = Ln[i, 1]
                    c = Ln[j, 0]

                elif Ln[i, 1] == Ln[j, 0]:
                    a = Ln[i, 1]
                    b = Ln[i, 0]
                    c = Ln[j, 1]

                elif Ln[i, 1] == Ln[j, 1]:
                    a = Ln[i, 1]
                    b = Ln[i, 0]
                    c = Ln[j, 0]

                else:
                    continue

                ES[i, j] = (
                    W[a, b] * W[a, c] * Ji[b, c]
                    + W[b, a] * W[c, a] * Jo[b, c]
                ) / 2

        np.fill_diagonal(ES, 0.0)

        # ------------------------------------------------------------
        # Hierarchical clustering of links
        # ------------------------------------------------------------
        C = np.zeros((m, m), dtype=int)
        Nc = np.zeros((m, m), dtype=np.float64)
        Mc = np.zeros((m, m), dtype=np.float64)
        Dc = np.zeros((m, m), dtype=np.float64)

        U = np.arange(m, dtype=int)

        C[0, :] = U

        last_level = 0

        for level in range(m - 1):

            last_level = level

            # Compute community density
            for j, community_id in enumerate(U):

                idx = C[level, :] == community_id

                links = np.sort(Lw[idx])

                nodes = np.unique(Ln[idx, :].reshape(-1))

                nc = len(nodes)
                mc = np.sum(links)

                if nc > 1:
                    min_mc = np.sum(links[: max(nc - 1, 0)])
                    denominator = (nc * (nc - 1) / 2) - min_mc

                    if denominator != 0:
                        dc = (mc - min_mc) / denominator
                    else:
                        dc = 0.0
                else:
                    dc = 0.0

                Nc[level, j] = nc
                Mc[level, j] = mc
                Dc[level, j] = dc

            # Copy current partition
            C[level + 1, :] = C[level, :]

            if len(U) <= 1:
                break

            ES_sub = ES[np.ix_(U, U)].copy()

            np.fill_diagonal(ES_sub, -np.inf)

            max_similarity = np.max(ES_sub)

            if not np.isfinite(max_similarity):
                break

            merge_positions = np.argwhere(ES_sub == max_similarity)

            if merge_positions.size == 0:
                break

            # Merge the first maximal pair.
            # This is simpler than MATLAB's all-ties merge but follows the
            # same principle.  # TODO do we need this comment?
            u1_pos, u2_pos = merge_positions[0]

            link_1 = U[u1_pos]
            link_2 = U[u2_pos]

            if type_clustering == "single":
                x = np.maximum(ES[link_1, :], ES[link_2, :])
            elif type_clustering == "complete":
                x = np.minimum(ES[link_1, :], ES[link_2, :])

            ES[link_1, :] = x
            ES[link_2, :] = x
            ES[:, link_1] = x
            ES[:, link_2] = x

            ES[link_1, link_1] = 0.0
            ES[link_2, link_2] = 0.0

            C[level + 1, C[level + 1, :] == link_2] = link_1

            U = np.unique(C[level + 1, :])

            if len(U) == 1:
                last_level = level + 1
                break

        Dc[np.isnan(Dc)] = 0.0

        density_score = np.sum(Dc * Mc, axis=1)

        if np.all(density_score == 0):
            best_level = last_level
        else:
            best_level = int(np.argmax(density_score))

        U_best = np.unique(C[best_level, :])

        module_affiliation_matrix = np.zeros((len(U_best), n), dtype=int)

        for j, community_id in enumerate(U_best):

            idx = C[best_level, :] == community_id

            nodes = np.unique(Ln[idx, :].reshape(-1))

            module_affiliation_matrix[j, nodes] = 1

        # Remove modules with <=2 nodes:
        module_affiliation_matrix = module_affiliation_matrix[
            np.sum(module_affiliation_matrix, axis=1) > 2, :
        ]

        return module_affiliation_matrix

    module_affiliation_matrix = _link_communities(
        pairwise_mi_matrix_thresholded, type_clustering=type_clustering,
    )

    number_of_components = int(module_affiliation_matrix.shape[0])

    if number_of_components > 0:
        percentage_mus_first_component = (
            np.sum(module_affiliation_matrix[0, :]) / tot_mus
        ) * 100
    else:
        percentage_mus_first_component = 0.0

    if tot_mus > 1:
        network_density = np.mean(
            np.sum(pairwise_mi_matrix_thresholded > 0, axis=1) / (tot_mus - 1)
        )
    else:
        network_density = np.nan

    network_results = {
        "smoothed_mus_firing": smoothed_mus_firing,

        "pairwise_mi": pairwise_mi,
        "pairwise_mi_matrix": pairwise_mi_matrix,
        "pairwise_mi_matrix_thresholded": pairwise_mi_matrix_thresholded,
        "network_density": network_density,
        "confidence_level": confidence_level,
        "percentage_significant_pairs": 100 * n_significant_pairs / len(pairwise_mi),

        "module_affiliation_matrix": module_affiliation_matrix,
        "number_of_components": number_of_components,
        "percentage_mus_first_component": percentage_mus_first_component,
    }

    return network_results

# TODO in the docstrings, use MU and MUs instead of motor units. Not urgent.
