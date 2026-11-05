import time
import copy
import warnings
from typing import Callable, Optional
from dataclasses import dataclass, is_dataclass, asdict

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from scipy.signal import find_peaks

from openhdemg.library.mathtools import compute_sil
from openhdemg.library.tools import (
    filter_rawemg, remove_powerline_harmonics, create_binary_firings,
    remove_duplicates_within, standardise_emgfile_dtypes,
)


def extend_emg_signal(sig: np.ndarray, ext_fact: int) -> np.ndarray:
    """
    Extend an HDsEMG signal by interleaving shifted copies of the channels.

    The function generates ``ext_fact`` shifted copies of the
    input signal and interleaves them into a larger channel matrix.

    Parameters
    ----------
    sig : np.ndarray
        The EMG signal to extend of shape (n_channels, n_samples).
    ext_fact : int
        The extension factor. Determines how many shifted copies of the
        signal are created. Must be ≥ 1.

    Returns
    -------
    e_sig : np.ndarray
        The extended signal of shape
        (n_channels * ext_fact, n_samples - ext_fact).
        Each group of ``n_channels`` rows contains a copy of the original
        signal shifted by 0, 1, ..., ext_fact - 1 samples.

    Notes
    -----
    To re-align the extended signal to the original signal, consider adding a
    number of zeros equal to 'ext_fact' a the beginning of the signal, or
    'ext_fact/2' at the start and end depending on use cases.

    Examples
    --------
    >>> import openhdemg.library as emg
    >>> emgfile = emg.emg_from_samplefile()
    >>> sig = np.transpose(emgfile["RAW_SIGNAL"].to_numpy())
    >>> print(f"sig shape: {np.shape(sig)}")
    >>> e_sig = emg.extension(sig, 16)
    >>> print(f"e_sig shape: {np.shape(e_sig)}")
    sig shape: (64, 66560)
    e_sig shape: (1024, 66544)
    """

    shape = sig.shape

    e_sig = np.zeros((shape[0] * ext_fact, shape[1] + ext_fact))

    for ind in range(ext_fact):
        e_sig[ind::ext_fact, ind:ind + shape[1]] = sig

    e_sig = e_sig[:, ext_fact:-ext_fact]

    return e_sig


def svd_whitening(
    e_sig: np.ndarray,
    eigenvalue_percentile: float
) -> np.ndarray:
    """
    Perform SVD-based whitening of the extended signal.

    This function whitens the input signal by:
    1. Computing its covariance matrix.
    2. Performing an eigenvalue decomposition.
    3. Retaining only those eigenvectors whose eigenvalues exceed a specified
       percentile threshold.
    4. Scaling the retained eigenvectors by the inverse square root of their
       eigenvalues.
    5. Projecting the extended signal onto this whitening basis.

    Whitening decorrelates the channels and normalises their variance,
    producing a transformed signal in which:
    - Rows correspond to whitened components.
    - Columns correspond to samples.

    Parameters
    ----------
    e_sig : np.ndarray
        Extended signal of shape (n_channels, n_samples).
        Typically obtained by spatial extension to improve decomposition
        robustness.
    eigenvalue_percentile : float
        Percentile (0-100) used to threshold the eigenvalues of the covariance
        matrix. Only eigenvectors whose eigenvalues exceed this percentile
        are retained for whitening. Higher values keep fewer components.
        If set to 0, all strictly positive eigenvalues are retained.

    Returns
    -------
    e_w_sig : np.ndarray
        Whitened signal array of shape (n_components, n_samples), where
        ``n_components`` equals the number of eigenvalues retained after
        percentile thresholding.
    """

    # Compute covariance matrix
    covariance = (e_sig @ e_sig.T) / e_sig.shape[1]

    # Eigenvalue decomposition (ascending order for eigh)
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)

    # Percentile thresholding
    if eigenvalue_percentile == 0:
        keep_idx = np.where(eigenvalues > 0)[0]
    else:
        threshold = np.percentile(eigenvalues, eigenvalue_percentile)
        keep_idx = np.where(eigenvalues > threshold)[0]

    # Inverse square-root of retained eigenvalues
    inv_sqrt_eig = 1.0 / np.sqrt(eigenvalues[keep_idx])

    # Select eigenvectors to retain
    retained_vectors = eigenvectors[:, keep_idx]

    # Whitening matrix: Λ⁻¹ᐟ² Vᵀ
    whitening_matrix = retained_vectors * inv_sqrt_eig[None, :]

    # Apply whitening (components × samples)
    e_w_sig = whitening_matrix.T @ e_sig

    return e_w_sig


def normc(data: np.ndarray) -> np.ndarray:
    """
    Column-wise L2 normalisation of a matrix.

    Parameters
    ----------
    data : np.ndarray
        Input array of shape (n_rows, n_columns).

    Returns
    -------
    np.ndarray
        Array with the same shape as ``data``, where each column has unit L2
        norm. Columns with zero norm are left unchanged.
    """

    norms = np.linalg.norm(data, axis=0, keepdims=True)
    norms[norms == 0] = np.sqrt(data.shape[0])
    return data / norms


def symdecor(data: np.ndarray) -> np.ndarray:
    """
    Symmetric decorrelation of a square or rectangular matrix.

    This orthogonalises the rows of ``data`` using the polar decomposition
    (via SVD), returning the closest orthogonal matrix.

    Parameters
    ----------
    data : np.ndarray
        Input array of shape (n_rows, n_columns).

    Returns
    -------
    np.ndarray
        Orthogonalised matrix of the same shape as ``data``.
    """

    # symmetric decorrelation via polar decomposition (faster)
    U, _, Vt = np.linalg.svd(data, full_matrices=False)
    return U @ Vt


def get_cost_function(cost_function_id: str):
    """
    Return a FastICA nonlinearity g(x) and its derivative dg(x) based on the
    selected identifier.

    Parameters
    ----------
    cost_function_id : str
        Identifier of the cost function to use:

        ``skew``
            g(x) = x²
            dg(x) = 2x

        ``kurtosis``
            g(x) = x³
            dg(x) = 3x²

        ``log_cosh``
            g(x) = tanh(x)
            dg(x) = 1 - tanh²(x)

    Returns
    -------
    g : callable
        FastICA nonlinearity g(x).

    dg : callable
        First derivative g'(x).

    Raises
    ------
    ValueError
        If an invalid ``cost_function_id`` is provided.

    Notes
    -----
    The functions returned by this function are the FastICA nonlinearities
    `g(x)` and their first derivatives `g'(x)`, rather than the underlying
    contrast functions `G(x)`, where:

    `g(x) = G'(x)`

    The corresponding contrast functions are:

    * `skew`:
    `G(x) = x³ / 3`, `g(x) = x²`, and `g'(x) = 2x`.

    * `kurtosis`:
    `G(x) = x⁴ / 4`, `g(x) = x³`, and `g'(x) = 3x²`.

    * `log_cosh`:
    `G(x) = log(cosh(x))`, `g(x) = tanh(x)`, and
    `g'(x) = 1 - tanh²(x)`.

    The term `cost function` is retained because it is commonly used in
    MU blind source separation to refer to the nonlinearity employed
    in the fixed-point optimisation.
    """

    match cost_function_id:
        case "skew":
            def g(x): return x**2
            def dg(x): return 2 * x
        case "kurtosis":
            def g(x): return x**3
            def dg(x): return 3 * x**2
        case "log_cosh":
            def g(x): return np.tanh(x)
            def dg(x): return 1 - np.tanh(x)**2
        case _:
            raise ValueError(
                f"Invalid cost_function_id: {cost_function_id!r}. "
                "Expected 'skew', 'kurtosis', or 'log_cosh'."
            )

    return g, dg


def source_peaks_classification(
    ipts: np.ndarray,
    fsamp: float,
    init: str = 'k-means++',
    max_drate: float | None = None,
    random_state: int = 42,
):
    """
    Identify MU discharge times from a 1-D source signal.

    The function performs:
    1. Normalisation of the input source.
    2. Peak detection on the normalised signal using a minimum inter-spike
       interval derived from the maximum physiological discharge rate.
    3. K-means clustering (k=2) on the peak amplitudes to separate likely
       MU discharges (high-amplitude cluster) from noise.
    4. Cluster-quality estimation using the silhouette score.

    Parameters
    ----------
    ipts : np.ndarray
        One-dimensional source signal (component extracted by the
        decomposition).
    fsamp : float
        Sampling frequency in Hz.
    init : str {"k-means++", "random"}, default "k-means++"
        Initialisation strategy for k-means.

        ``k-means++``
            selects initial cluster centroids using sampling based on an
            empirical probability distribution of the points' contribution to
            the overall inertia. This technique speeds up convergence. The
            algorithm implemented is "greedy k-means++". It differs from the
            vanilla k-means++ by making several trials at each sampling step
            and choosing the best centroid among them.

        ``random``
            choose n_clusters observations (rows) at random from data for the
            initial centroids.
    max_drate : float or None, default None
        Maximum physiological discharge rate in Hz. Used to compute the
        minimum allowed distance between successive peaks:
        ``min_distance_samples = fsamp / max_drate``.
        If None, no minimum spacing constraint is applied.
    random_state : int, default=42
        Random seed for k-means reproducibility.

    Returns
    -------
    mu_spike_idx : np.ndarray
        Sample indices of the accepted spikes, corresponding to motor unit
        discharge times.
    sil : float
        The silhouette score indicating how well the "high" cluster is
        separated from the "low" cluster. Higher values imply better
        separability.
    """

    # Normalise the source
    norm = np.linalg.norm(ipts)
    ipts_norm = ipts if norm == 0 else ipts / norm

    # Findpeaks with min distance = round(1/max_drate * fsamp)
    min_dist = 1 if max_drate is None else round(fsamp / max_drate)
    all_peaks_index, _ = find_peaks(ipts_norm, distance=min_dist)
    ipts_peak_amplitude = ipts_norm[all_peaks_index]
    peaks = ipts_peak_amplitude.reshape(-1, 1)

    # Initialize return values to safe defaults
    spike_cluster_idx = np.array([])
    mu_spike_idx = np.array([])
    sil = np.nan

    try:
        if peaks.shape[0] >= 2:
            # k-means with 2 clusters
            km = KMeans(
                n_clusters=2,
                init=init,
                n_init='auto',
                random_state=random_state,
            )
            labels = km.fit_predict(peaks)
            centers = km.cluster_centers_.flatten()

            # 4) Choose the “high” cluster
            means = []
            for i in (0, 1):
                mask = (labels == i)
                if mask.any():
                    means.append(ipts_peak_amplitude[mask].mean())
                else:
                    means.append(centers[i])
            k = int(np.argmax(means))
            spike_cluster_idx = np.where(labels == k)[0]

            # Global sample indices of chosen peaks
            mu_spike_idx = all_peaks_index[spike_cluster_idx]

            # Calculate SIL
            sil = compute_sil(ipts=ipts_norm, mupulses=mu_spike_idx)

    finally:
        return mu_spike_idx, sil


def compute_mu_filter(
    e_w_sig: np.ndarray,
    mu_mupulses: np.ndarray
) -> np.ndarray:
    """
    Calculate the MU filter.

    Parameters
    ----------
    e_w_sig : np.ndarray
        Extended and whitened signal array of shape (n_components, n_samples),
        where ``n_components`` equals the number of eigenvalues retained after
        percentile thresholding.
    mu_mupulses : np.ndarray
        The times of firing (in samples) of each MU.

    Returns
    -------
    mu_filter : np.ndarray
        Array of shape (n_components,).
    """

    if len(mu_mupulses) > 0:
        mu_filter = np.mean(e_w_sig[:, mu_mupulses], axis=1)
    else:
        mu_filter = np.zeros((np.shape(e_w_sig)[0]))

    return mu_filter


@dataclass
class ConvolutiveBSSParams:
    """
    Parameters for Convolutive Blind Source Separation (BSS).

    To be used in the ``convolutive_bss`` function.

    Attributes
    ----------
    n_iterations: int, default 100
        Number of decomposition iterations (maximum number of sources to
        attempt to extract).
    silhouette_threshold: float, default 0.9
        Minimum silhouette threshold for classifying a source as a valid MU.
    extension_factor: int, default 16
        Factor to extend the signal by.
    cost_function_id : str, default "skew"
        Cost function used by FastICA. Defaults to a skew cost function.
        See ``emg.get_cost_function`` for possible parameters.
    rem_activity_index : bool, default False
        If True, removes activity around identified spikes from the activity
        index to reduce re-detection of the same source.
    max_discharge_rate : float, default 0
        Maximum allowed discharge rate (in Hz) for spike train classification.
        If 0, no upper bound is enforced.
    min_spike_count : int, default 0
        Minimum number of detected spikes required to accept a motor unit.
    eigenvalue_percentile : float, default 10
        Percentile (0-100) of the smallest eigenvalues discarded during
        whitening. Only eigenvectors whose eigenvalues exceed this percentile
        are retained for whitening. Higher values keep fewer components.
        If set to 0, all strictly positive eigenvalues are retained.
    artifact_win_sec : float, default 10e-3
        Length (in seconds) of the window removed around high-energy peaks in
        the activity index.
    tolerance_fastica : float, default 1e-4
        Convergence tolerance for the FastICA iteration.
    max_iter_fastica : int, default 100
        Maximum number of iterations for FastICA updates for each source.
    cluster_dist_type : str {"k-means++", "k-means", "random"}, default "k-means++"
        Initialisation strategy for spike clustering.
    spike_clip_max : float, default 0
        Maximum value used to clip the projected source before applying the
        contrast function. If 0, no clipping is performed.
    random_state : int, default 42
        Random seed used for clustering reproducibility.

    Examples
    --------
    Use default parameters

    >>> import openhdemg.library as emg
    >>> params = emg.ConvolutiveBSSParams()
    >>> print(params)

    Modify the number of iterations and silhouette threshold at params creation

    >>> import openhdemg.library as emg
    >>> params = emg.ConvolutiveBSSParams(
    ...     n_iterations=200,
    ...     silhouette_threshold=0.95,
    ... )
    >>> print(params.n_iterations)

    Modify the number of iterations after params creation

    >>> import openhdemg.library as emg
    >>> params = emg.ConvolutiveBSSParams()
    >>> params.n_iterations = 500
    """

    n_iterations: int = 250
    silhouette_threshold: float = 0.90
    extension_factor: int = 16

    cost_function_id: str = "skew"

    rem_activity_index: bool = False
    max_discharge_rate: float = 0
    min_spike_count: int = 0

    eigenvalue_percentile: float = 10
    artifact_win_sec: float = 10e-3

    tolerance_fastica: float = 1e-4
    max_iter_fastica: int = 100

    cluster_dist_type: str = "k-means++"
    spike_clip_max: float = 0
    random_state: int = 42


def convolutive_bss(
    emgsig: np.ndarray,
    fsamp: float,
    decomposition_params: Optional[ConvolutiveBSSParams] = None,
    **plotting_kwargs,
):
    """
    Decompose HDsEMG signals into motor unit spike trains using convolutive
    blind source separation (Negro et al., 2016).

    Parameters
    ----------
    emgsig: np.ndarray
        Multi-channel EMG signal to decompose of shape (n_channels, n_samples).
    fsamp: float
        Sampling frequency of the EMG recording, in Hz.
    decomposition_params : dataclass
        Parameters for Convolutive Blind Source Separation (BSS). Please see
        ``emg.ConvolutiveBSSParams`` and the examples for more details and
        default values.

    Plotting Parameters
    -------------------
    signals : class, optional
        A class providing Qt Signals for external plotting and progress
        monitoring obtained from DecompositionSignals.
    send_only_process : Bool, optional
        If true, only the signal marking the iteration is sent.
        This can save data transfer and plotting time.
    stop_object : class, optional
        A class providing a stop flag obtained from
        StopDecompositionObject.

    Returns:
    ----------
    mupulses : list of np.ndarray
        List of arrays, each containing the sample indices (spike times)
        of one decomposed motor unit.
    ipts : list of np.ndarray
        List of arrays, each containing the innervation pulse train of
        one motor unit.
    sil : list of float
        List of silhouette scores for each motor unit.
    """

    # Get decomposition parameters and restore None when needed
    if decomposition_params is None:
        decomposition_params = ConvolutiveBSSParams()

    n_iterations = decomposition_params.n_iterations
    silhouette_threshold = decomposition_params.silhouette_threshold
    extension_factor = decomposition_params.extension_factor
    cost_function_id = decomposition_params.cost_function_id
    rem_activity_index = decomposition_params.rem_activity_index
    max_discharge_rate = decomposition_params.max_discharge_rate
    if max_discharge_rate == 0:
        max_discharge_rate = None
    min_spike_count = decomposition_params.min_spike_count
    eigenvalue_percentile = decomposition_params.eigenvalue_percentile
    artifact_win_sec = decomposition_params.artifact_win_sec
    tolerance_fastica = decomposition_params.tolerance_fastica
    max_iter_fastica = decomposition_params.max_iter_fastica
    cluster_dist_type = decomposition_params.cluster_dist_type
    spike_clip_max = decomposition_params.spike_clip_max
    if spike_clip_max == 0:
        spike_clip_max = None
    random_state = decomposition_params.random_state

    # Get plotting parameters
    signals = plotting_kwargs.get("signals", None)
    send_only_process = plotting_kwargs.get("send_only_process", False)
    stop_object = plotting_kwargs.get("stop_object", None)

    # Extend and center
    eYT = extend_emg_signal(sig=emgsig, ext_fact=extension_factor)
    eYT = eYT - np.mean(eYT, axis=1, keepdims=True)

    # Whitening with percentile threshold
    eYW = svd_whitening(e_sig=eYT, eigenvalue_percentile=eigenvalue_percentile)

    # Define a transposed version of eYW
    eYW_T = eYW.T

    # Activity index without samples at the beginning and end
    activity_index = np.sum(np.abs(eYW)**2, axis=0)
    win = int(round(artifact_win_sec * fsamp))
    activity_index[:win] = activity_index[-win:] = 0

    # Define required storage variables
    mupulses_v = []
    ipts_v = []
    silhouette_v = []

    # Initialize vector containing all sources found across iterations.
    all_filters: list[np.ndarray] = []

    # Get cost functions
    G, DG = get_cost_function(cost_function_id=cost_function_id)

    # Main loop for decomposition
    for iteration in range(n_iterations):
        # Check stop flag. If true, interrupt decomposition
        if stop_object is not None:
            if stop_object.stop_requested is True:
                break

        # Check if plotting signals are required
        if signals is not None:
            signals.progress.emit(iteration)
            if send_only_process is False:
                signals.ai_data.emit(activity_index)

        # initialize W with max-energy sample (1D vector)
        idx = activity_index.argmax()
        max_val = activity_index[idx]
        # If the maximum value is zero, break the loop
        if max_val == 0:
            break
        # Store the corresponding column in W and normalize
        W = eYW[:, idx].copy()
        W = W / np.linalg.norm(W)
        # Zero out the activity index around this peak
        lo = max(0, idx - win)
        hi = min(len(activity_index), idx + win + 1)
        activity_index[lo:hi] = 0

        eYW_TEMP = eYW.copy()

        n_samp_temp = eYW_TEMP.shape[1]

        # Initialize the stopping criteria
        crit = 0.0
        counter = 0

        # FastICA update
        # This loop iteratively updates W until convergence or maximum
        # iterations.
        while (1 - crit > tolerance_fastica) and (counter < max_iter_fastica):
            # Reference previous W
            W_old = W.copy()

            # Estimate the source signal
            # (1D: W is n_ch, eYW_TEMP is n_ch x n_samp).
            temp = np.clip(W @ eYW_TEMP, None, spike_clip_max)
            # FastICA update rule
            W = (eYW_TEMP @ G(temp) - DG(temp).sum() * W) / n_samp_temp

            # Deflation with all previously found sources
            if len(all_filters) > 0:
                W_prev = np.column_stack(all_filters)
                W = W - W_prev @ (W_prev.T @ W)

            W = W / np.linalg.norm(W)

            counter += 1
            crit = np.abs(W @ W_old)

        # W is already 1D and normalized; store it for deflation
        all_filters.append(W.copy())

        # Estimate the source signal
        source = eYW_T @ W

        # Classify peaks
        source_energy = source * np.abs(source)
        mu_spike_idx, silhouette = source_peaks_classification(
            ipts=source_energy,
            fsamp=fsamp,
            init=cluster_dist_type,
            max_drate=max_discharge_rate,
            random_state=random_state,
        )

        # Improve SIL
        silhouette_old = np.finfo(float).eps
        silhouette_new = silhouette
        while silhouette_new > silhouette_old:
            silhouette_old = silhouette_new
            Pindex_loop = mu_spike_idx.copy()  # spike indices
            Psource_loop = source.copy()  # source signal
            Psource_energy_loop = source_energy.copy()  # source_energy signal
            wT_loop = np.mean(eYW[:, mu_spike_idx], axis=1)
            wT_loop = wT_loop / np.linalg.norm(wT_loop)
            source = eYW_T @ wT_loop

            # Classify peaks
            source_energy = source * np.abs(source)
            mu_spike_idx, silhouette_new = source_peaks_classification(
                ipts=source_energy,
                fsamp=fsamp,
                init=cluster_dist_type,
                max_drate=max_discharge_rate,
                random_state=random_state,
            )

        # Prepare for the next iteration
        index = Pindex_loop
        source = Psource_loop
        source_energy = Psource_energy_loop
        silhouette = silhouette_old
        if rem_activity_index:
            # Remove activity around identified spikes
            offsets_half = np.arange(
                start=-(extension_factor // 2),
                stop=extension_factor // 2 + 1,
            )
            indices_to_zero = (index[:, None] + offsets_half).ravel()
            indices_to_zero = np.unique(
                np.clip(indices_to_zero, 0, len(activity_index) - 1)
            )
            activity_index[indices_to_zero] = 0

        # Store new MU
        if (silhouette > silhouette_threshold) and (len(index) > min_spike_count):
            mupulses_v.append(index + extension_factor)
            ipts_v.append(np.pad(source, (extension_factor, 0)))
            silhouette_v.append(silhouette)

            # Check if plotting signals are required
            if signals is not None:
                if send_only_process is False:
                    signals.ipts_mupulses_data.emit(
                        fsamp, ipts_v[-1], mupulses_v[-1]
                    )

    # Mark last iteration completed
    if signals is not None:
        signals.progress.emit(n_iterations)

    # Return results
    if len(mupulses_v) == 0:
        return None, None, None
    else:
        return mupulses_v, ipts_v, silhouette_v
    # TODO make sure that mupulses_v is a list of 1d arrays?


class EMGDecomposer:
    def __init__(self):
        """
        High-level HDsEMG decomposition pipeline.

        This class provides a convenient interface to run a full decomposition
        pipeline on an emgfile structure, including optional preprocessing
        (bandpass and power-line removal), optional removal of bad channels,
        decomposition using a selected algorithm, and optional post-processing
        (duplicate MU removal).

        Defaults
        --------
        Decomposition
            - method: `emg.convolutive_bss`
            - parameters: `emg.ConvolutiveBSSParams()`

        Filtering
            - bandpass: enabled by default (order=2, 20-500 Hz)
            - power-line removal: disabled by default

        Channels
            - bad-channel exclusion: enabled by default
            (`exclude_bad_channels=True`)

        Duplicate removal
            - enabled by default

        Examples
        --------
        Common part

        >>> import openhdemg.library as emg
        >>> emgfile = emg.emg_from_samplefile()

        Minimal usage (defaults: bandpass enabled, notch disabled, duplicate
        removal enabled)

        >>> decomposer = emg.EMGDecomposer()
        >>> decomposed_emgfile = decomposer.run_decomposition(emgfile)

        Full customisation of decomposition parameters

        >>> decomposer = emg.EMGDecomposer()
        >>> params = emg.ConvolutiveBSSParams()
        >>> params.n_iterations = 5
        >>> params.silhouette_threshold = 0.88
        >>> decomposer.set_decomposition_parameters(params=params)
        >>> decomposed_emgfile = decomposer.run_decomposition(emgfile)

        Quick customisation of decomposition parameters

        >>> decomposer = emg.EMGDecomposer()
        >>> decomposer.decomposition_parameters.n_iterations = 5
        >>> decomposed_emgfile = decomposer.run_decomposition(emgfile)

        Disable filtering entirely

        >>> decomposer = emg.EMGDecomposer()
        >>> decomposer.change_filtering_parameters(
        ...     bandpass_enabled=False,
        ...     notch_enabled=False,
        ... )
        >>> decomposed_emgfile = decomposer.run_decomposition(emgfile)

        Disable duplicate removal

        >>> decomposer = emg.EMGDecomposer()
        >>> decomposer.change_duplicate_removal_parameters(
        ...     duplicate_removal_enabled=False,
        ... )
        >>> decomposed_emgfile = decomposer.run_decomposition(emgfile)
        """

        # Set defaults
        self.decomposition_function_name = "convolutive_bss"
        self.decomposition_function = convolutive_bss
        self.decomposition_parameters = ConvolutiveBSSParams()

        self.bandpass_enabled = True
        self.bandpass_order = 2
        self.bandpass_lowcut = 20
        self.bandpass_highcut = 500

        self.notch_enabled = False
        self.notch_freq = 50.0
        self.notch_width = 5.0

        self.exclude_bad_channels = True

        self.dup_removal_enabled = True
        self.dup_correlation_max_lag = 50e-3
        self.dup_peak_window_half_width = 2.5e-3
        self.dup_duplicate_threshold = 30
        self.dup_which = "accuracy"

    def set_decomposition_function(self, func: Callable):
        """
        Set the decomposition function to be used by the pipeline.

        Parameters
        ----------
        func : callable
            Decomposition callable. See `emg.convolutive_bss` for the expected
            function signature.

        Notes
        -----
        The function name is stored internally (via `func.__name__`) and
        written into the output metadata under
        `emgfile["DECOMPOSITION_PARAMETERS"]`.
        """

        self.decomposition_function = func
        self.decomposition_function_name = func.__name__

    def set_decomposition_parameters(self, params):
        """
        Set decomposition parameters.

        Parameters
        ----------
        params : dataclass instance
            Dataclass instance containing method-specific parameters.

        Notes
        -----
        Parameters are stored and later serialised (via `dataclasses.asdict`)
        into `emgfile["DECOMPOSITION_PARAMETERS"]`. Ensure parameters are
        JSON-serialisable if you intend to save them to disk.
        """

        if not is_dataclass(params):
            raise TypeError("params must be a dataclass instance")
        self.decomposition_parameters = params

    def change_filtering_parameters(
        self,
        bandpass_enabled=True,
        bandpass_order=2,
        bandpass_lowcut=20,
        bandpass_highcut=500,
        notch_enabled=False,
        notch_freq=50.0,
        notch_width=5.0,
    ):
        """
        Configure preprocessing filters.

        Parameters
        ----------
        bandpass_enabled : bool, default True
            Whether to bandpass filter the signal.
        bandpass_order : int, default 2
            The filter order. Note that a band-pass transformation doubles the
            order, so `order=2` produces a 4th-order band-pass filter.
        bandpass_lowcut : float, default 20
            The lower cut-off frequency in Hz.
        bandpass_highcut : float, default 500
             The higher cut-off frequency in Hz.
        notch_enabled : bool, default False
            Whether to apply notch filtering.
        notch_freq : float, default 50.0
            Fundamental power-line frequency (e.g., 50 or 60 Hz).
        notch_width : float, default 5.0
            Width of each notch (± notch_width/2), in Hz.
        """

        self.bandpass_enabled = bandpass_enabled
        self.bandpass_order = bandpass_order
        self.bandpass_lowcut = bandpass_lowcut
        self.bandpass_highcut = bandpass_highcut

        self.notch_enabled = notch_enabled
        self.notch_freq = notch_freq
        self.notch_width = notch_width

    def get_filtering_parameters(self):
        """
        Return the current filtering parameters.

        Returns
        -------
        params : dict
            Dictionary with keys:
            - "bandpass_enabled"
            - "bandpass_order"
            - "bandpass_lowcut"
            - "bandpass_highcut"
            - "notch_enabled"
            - "notch_freq"
            - "notch_width"

        Notes
        -----
        This method is intended for inspection.
        To modify filtering parameters, use `change_filtering_parameters()`.
        """

        return {
            "bandpass_enabled": self.bandpass_enabled,
            "bandpass_order": self.bandpass_order,
            "bandpass_lowcut": self.bandpass_lowcut,
            "bandpass_highcut": self.bandpass_highcut,

            "notch_enabled": self.notch_enabled,
            "notch_freq": self.notch_freq,
            "notch_width": self.notch_width
        }

    def use_good_channels_only(self, ans: bool = True):
        """
        Enable or disable exclusion of bad channels.

        Parameters
        ----------
        ans : bool, default=True
            If True, channels marked as False in `emgfile["GOOD_CHANNELS"]` are
            excluded prior to decomposition.

        Notes
        -----
        If enabled but `emgfile["GOOD_CHANNELS"]` is missing, a warning is
        issued and no channels are removed.
        """

        self.exclude_bad_channels = ans

    def change_duplicate_removal_parameters(
        self,
        duplicate_removal_enabled=True,
        correlation_max_lag=50e-3,
        peak_window_half_width=2.5e-3,
        duplicate_threshold=30,
        which="accuracy",
    ):
        """
        Configure post-processing removal of duplicate MUs.

        Parameters
        ----------
        duplicate_removal_enabled : bool, default True
            Whether to remove duplicate units.
        correlation_max_lag : float, default 50e-3
            Maximum lag (in seconds) used when computing the cross-correlation
            between MU spike trains. Defines the full search range for possible
            synchronisation peaks. Larger values allow detection of synchrony
            over wider time shifts. This must be < 1.
        peak_window_half_width : float, default 2.5e-3
            Half-width (in seconds) of the window used around the
            cross-correlation peak to compute the duplication sensitivity
            metric. This window should capture the narrow temporal jitter
            expected for duplicate MUs. This must be < 1 and <
            `correlation_max_lag`.
        duplicate_threshold : float, default 30
            Threshold (in percent) for classifying two MUs as duplicates.
            The sensitivity metric is computed as the sum of the
            cross-correlation values within a ±`peak_window_half_width` window
            around the correlation peak, normalised by the size of the larger
            spike train.
        which : str {"accuracy", "covisi"}, default "accuracy"
            How to remove the duplicated MUs.

            ``accuracy``
                The MU with the lowest accuracy is removed. The emgfile must
                already contain the 'ACCURACY' dataframe.

            ``covisi``
                The MU with the highest CoV of interspike interval is removed.
        """

        self.dup_removal_enabled = duplicate_removal_enabled
        self.dup_correlation_max_lag = correlation_max_lag
        self.dup_peak_window_half_width = peak_window_half_width
        self.dup_duplicate_threshold = duplicate_threshold
        self.dup_which = which

    def get_duplicate_removal_parameters(self):
        """
        Return the current duplicate-removal parameters.

        Returns
        -------
        params : dict
            Dictionary with keys:
            - "duplicate_removal_enabled"
            - "correlation_max_lag"
            - "peak_window_half_width"
            - "duplicate_threshold"
            - "which"

        Notes
        -----
        This method is intended for inspection.
        To modify duplicate-removal parameters, use
        `change_duplicate_removal_parameters()`.
        """

        return {
            "duplicate_removal_enabled": self.dup_removal_enabled,
            "correlation_max_lag": self.dup_correlation_max_lag,
            "peak_window_half_width": self.dup_peak_window_half_width,
            "duplicate_threshold": self.dup_duplicate_threshold,
            "which": self.dup_which
        }

    def run_decomposition(self, emgfile, **plotting_kwargs):
        """
        Run the full decomposition pipeline on an emgfile.

        The pipeline performs:
        1) Optional bandpass filtering.
        2) Optional power-line harmonics removal.
        3) Optional exclusion of bad channels (if `GOOD_CHANNELS` is present).
        4) Decomposition using the configured method.
        5) Reconstruction of the EMG file with decomposition outputs.
        6) Optional removal of duplicate MUs.

        Parameters
        ----------
        emgfile : dict-like
            emgfile structure. Must provide at least:
            - "RAW_SIGNAL": pd.DataFrame of shape (n_samples, n_channels)
            - "FSAMP": sampling frequency (Hz)
            Optionally:
            - "GOOD_CHANNELS": dict mapping channel identifiers to booleans
            - "EMG_LENGTH": expected number of samples (validated if present)

        Plotting Parameters
        -------------------
        signals : class, optional
            A class providing Qt Signals for external plotting and progress
            monitoring obtained from DecompositionSignals.
        send_only_process : bool, optional
            If true, only the signal marking the iteration is sent.
            This can save data transfer and plotting time.
        stop_object : class, optional
            A class providing a stop flag obtained from
            StopDecompositionObject.

        Returns
        -------
        decomposed_emgfile : dict-like
            A deep copy of the input EMG file, updated with decomposition
            results. Keys added/updated include:
            - "DECOMPOSITION_PARAMETERS"
            - "NUMBER_OF_MUS"
            - "MUPULSES" (when MUs are found)
            - "IPTS" (when MUs are found)
            - "ACCURACY" (silhouette scores, when MUs are found)
            - "BINARY_MUS_FIRING" (when MUs are found)

        Raises
        ------
        ValueError
            If `EMG_LENGTH` is present and inconsistent with the length of
            "RAW_SIGNAL".
        """

        # Work on safe copy
        emgfile = copy.deepcopy(emgfile)

        # Preprocess signal
        if self.bandpass_enabled:
            _filtered_emgfile = filter_rawemg(
                emgfile=emgfile,
                order=self.bandpass_order,
                lowcut=self.bandpass_lowcut,
                highcut=self.bandpass_highcut,
            )
            emgsig = np.transpose(
                _filtered_emgfile["RAW_SIGNAL"].to_numpy().astype(np.float64)
            )
        else:
            emgsig = np.transpose(
                emgfile["RAW_SIGNAL"].to_numpy().astype(np.float64)
            )
        bandpass_filtering_dict = {
            "enabled": self.bandpass_enabled,
            "order": self.bandpass_order,
            "lowcut": self.bandpass_lowcut,
            "highcut": self.bandpass_highcut
        }

        if self.notch_enabled:
            emgsig = remove_powerline_harmonics(
                sig=emgsig,
                fsamp=emgfile["FSAMP"],
                notch_freq=self.notch_freq,
                notch_width=self.notch_width,
            )
        powerline_harm_dict = {
            "enabled": self.notch_enabled,
            "notch_freq": self.notch_freq,
            "notch_width": self.notch_width
        }

        # Remove bad channels
        if self.exclude_bad_channels is True:
            good_channels_dict = emgfile.get("GOOD_CHANNELS", None)
            if good_channels_dict is not None:
                good_idx = sorted(
                    [int(ch) for ch, ok in good_channels_dict.items() if ok]
                )
                emgsig = emgsig[good_idx, :]
            else:
                warnings.warn(
                    "'exclude_bad_channels' is True but "
                    "emgfile['GOOD_CHANNELS'] is not present."
                )

        # --- Run the decomposition
        # TODO in the future, this might require a default behaviour plus
        # optional behaviours based on self.decomposition_function_name.
        print(
            "\n\u25B6  "
            "Decomposition started. Running for {} iterations".format(
                self.decomposition_parameters.n_iterations
            )
        )
        t0 = time.time()
        decomposition_results = self.decomposition_function(
            emgsig=emgsig,
            fsamp=emgfile["FSAMP"],
            decomposition_params=self.decomposition_parameters,
            **plotting_kwargs,
        )
        decomposition_time = time.time() - t0

        # Get decomposition parameters to save. These must be json
        # serialisable! The user should verify this before saving the file.
        decomposition_parameters = {
            "method_name": self.decomposition_function_name,
            **asdict(self.decomposition_parameters),
            "bandpass_filtering": bandpass_filtering_dict,
            "powerline_harmonics": powerline_harm_dict,
            "exclude_bad_channels": self.exclude_bad_channels,
        }
        emgfile["DECOMPOSITION_PARAMETERS"] = decomposition_parameters

        # Update also decomposition parameters with duplicate removal
        # parameters here because if no MUs are detected, it will not be stored
        # later on.
        remove_duplicates_dict = {
            "enabled": self.dup_removal_enabled,
            "correlation_max_lag": self.dup_correlation_max_lag,
            "peak_window_half_width": self.dup_peak_window_half_width,
            "duplicate_threshold": self.dup_duplicate_threshold,
            "which": self.dup_which,
        }
        emgfile["DECOMPOSITION_PARAMETERS"][
            "duplicate_removal"
        ] = remove_duplicates_dict

        # Extract decomposition parameters here, for future compatibility, as
        # Different decomposition functions might return a different number of
        # parameters. In future, this can be checked using
        # self.decomposition_function_name.

        mupulses, ipts, silhouette = decomposition_results

        # Reconstruct the emgfile depending on whether MUs have been found

        # - No MUs
        c1 = mupulses is None
        c2 = ipts is None
        c3 = silhouette is None
        if any((c1, c2, c3)):
            # No MUs found
            emgfile["NUMBER_OF_MUS"] = 0
            print(
                "\u2718  "
                "Decomposition finished. "
                f"0 MUs detected in {round(decomposition_time)} sec\n"
            )
            # Standardise emgfile
            emgfile = standardise_emgfile_dtypes(emgfile=emgfile)
            return emgfile

        # - Yes MUs
        emgfile["NUMBER_OF_MUS"] = len(mupulses)

        emgfile["MUPULSES"] = mupulses

        columns = list(range(emgfile["NUMBER_OF_MUS"]))
        emgfile["IPTS"] = pd.DataFrame(
            np.transpose(ipts),
            columns=columns,
            dtype=np.float64,
        )

        emgfile["ACCURACY"] = pd.DataFrame(
            silhouette,
            columns=[0],
            dtype=np.float64,
        )

        _raw_len = emgfile["RAW_SIGNAL"].shape[0]
        if "EMG_LENGTH" in emgfile:
            if emgfile["EMG_LENGTH"] != _raw_len:
                raise ValueError(
                    f"EMG_LENGTH ({emgfile['EMG_LENGTH']}) != RAW_SIGNAL "
                    f"length ({_raw_len})"
                )
        else:
            emgfile["EMG_LENGTH"] = _raw_len
        emgfile["BINARY_MUS_FIRING"] = create_binary_firings(
            emg_length=emgfile["EMG_LENGTH"],
            number_of_mus=emgfile["NUMBER_OF_MUS"],
            mupulses=emgfile["MUPULSES"],
        )

        # Remove duplicates
        if self.dup_removal_enabled:
            print("\u25B6  Removing duplicate MUs")
            emgfile = remove_duplicates_within(
                emgfile=emgfile,
                correlation_max_lag=self.dup_correlation_max_lag,
                peak_window_half_width=self.dup_peak_window_half_width,
                duplicate_threshold=self.dup_duplicate_threshold,
                which=self.dup_which,
            )

        # Standardise emgfile
        emgfile = standardise_emgfile_dtypes(emgfile=emgfile)

        # Print summary
        print(
            "\u2714  "
            "Decomposition finished. "
            f"{emgfile['NUMBER_OF_MUS']} MUs detected in "
            f"{round(decomposition_time)} sec\n"
        )

        # Return decomposed file
        return emgfile
