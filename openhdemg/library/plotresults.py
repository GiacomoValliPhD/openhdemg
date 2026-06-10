"""
This module contains all the functions used to visualise the results of
computations.

Result plots are usually provided with a plot title because small variations in
the analyses parameters might change the interpretation of the plot.
"""

import numpy as np

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

from openhdemg.library.plotemg import _create_figure

matplotlib.use("QtAgg")


# TODO consider having the layout manager working also for this module

def plot_coherence(
    coherence_results,
    coherence_band_results=None,
    show_confidence_level=True,
    delta_frequency_range=(1, 5, "tab:blue"),
    alpha_frequency_range=(5, 15, "tab:green"),
    beta_frequency_range=(15, 35, "tab:orange"),
    gamma_frequency_range=(35, 60, "tab:red"),
    show_frequency_bands=True,
    show_legend=True,
    legend_location="inside",
    max_frequency=80,
    figsize=[20, 15],
    tight_layout=True,
    showimmediately=True,
    use_plt=True,
):
    """
    Plot the raw coherence curve or a z-scored coherence curve.

    Parameters
    ----------
    coherence_results : dict
        Dictionary containing the coherence results from
        `pooled_intramuscular_coherence` or `z_score_coherence`.
    coherence_band_results : pd.DataFrame or None, default None
        Output DataFrame from `calculate_coherence_bands`.
    show_confidence_level : bool, default True
        When True and `coherence_band_results` is provided, the confidence
        level value will be shown in the figure.
    show_confidence_level : bool, default True
        When True and `coherence_band_results` is provided, the confidence
        level value will be shown in the figure.
    delta_frequency_range : tuple, default (1, 5, "tab:blue")
        Frequency range and colour used to highlight the delta band.
        The tuple must contain the lower frequency, upper frequency, and
        matplotlib-compatible colour.
    alpha_frequency_range : tuple, default (5, 15, "tab:green")
        Frequency range and colour used to highlight the alpha band.
        The tuple must contain the lower frequency, upper frequency, and
        matplotlib-compatible colour.
    beta_frequency_range : tuple, default (15, 35, "tab:orange")
        Frequency range and colour used to highlight the beta band.
        The tuple must contain the lower frequency, upper frequency, and
        matplotlib-compatible colour.
    gamma_frequency_range : tuple, default (35, 60, "tab:red")
        Frequency range and colour used to highlight the gamma band.
        The tuple must contain the lower frequency, upper frequency, and
        matplotlib-compatible colour.
    show_frequency_bands : bool, default True
        If True, shaded frequency bands are plotted in the background of the
        coherence figure.
    show_legend : bool, default True
        If True and `show_frequency_bands` is True, the legend describing the
        frequency bands is shown.
    legend_location : str {"inside", "outside"}, default "inside"
        Location of the legend.

        ``inside``
            The legend is placed inside the figure.

        ``outside``
            The legend is placed outside the figure.
    max_frequency : int or float, default 80
        Maximum frequency shown on the x-axis.
    figsize : list, default [20, 15]
        Size of the figure in centimeters [width, height].
    tight_layout : bool, default True
        If True (default), fig.tight_layout() is called and the figure's
        layout is improved.
        It is useful to set it to False when calling the function from a GUI.
    showimmediately : bool, default True
        If True (default), `plt.show()` is called to display the figure to the
        user. This has an effect only if `use_plt` is True. Set to False when
        using the function within a GUI or when managing figure display
        manually.
    use_plt : bool, default True
        Whether to use the `pyplot` interface (`plt.subplots`) or the
        object-oriented `matplotlib.figure.Figure` API to create the figure.
        Set to False in GUI applications or headless environments to avoid the
        persistent pyplot's global state.

    Returns
    -------
    fig : pyplot `~.figure.Figure`

    Examples
    --------
    Plot pooled intramuscular coherence from a resized steady-state signal.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askloadmodule()
    >>> steady_emgfile, _, _ = emg.resize_emgfile(
    ...     emgfile,
    ...     area=[15400, 50770],
    ... )
    >>> coherence_results = emg.pooled_intramuscular_coherence(
    ...     emgfile=steady_emgfile,
    ... )
    >>> fig = emg.plot_coherence(
    ...     coherence_results=coherence_results,
    ... )

    ![](md_graphics/docstrings/plotresults/plot_coherence_ex_1.png)

    Plot z-scored pooled intramuscular coherence and show the confidence level,
    but not the frequency bands.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askloadmodule()
    >>> steady_emgfile, _, _ = emg.resize_emgfile(
    ...     emgfile,
    ...     area=[15400, 50770],
    ... )
    >>> coherence_results = emg.pooled_intramuscular_coherence(
    ...     emgfile=steady_emgfile,
    ... )
    >>> z_coherence_results = emg.z_score_coherence(
    ...     coherence_results,
    ... )
    >>> coherence_band_results = emg.calculate_coherence_bands(
    ...     z_coherence_results,
    ... )
    >>> emg.plot_coherence(
    ...     coherence_results=z_coherence_results,
    ...     coherence_band_results=coherence_band_results,
    ...     show_confidence_level=True,
    ...     show_frequency_bands=False,
    ... )

    ![](md_graphics/docstrings/plotresults/plot_coherence_ex_2.png)
    """

    # Check if we have to plot coherence or Z coherence
    if "z_score" in coherence_results:
        plotting_z = True
        figname = "Z Coherence"
    else:
        plotting_z = False
        figname = "Coherence"

    # Create figure and axis
    fig, ax1 = _create_figure(
        figsize=(figsize[0] / 2.54, figsize[1] / 2.54),
        use_plt=use_plt, figname=figname,
    )

    # Plot frequency bands
    if show_frequency_bands is True:
        bands = {
            "Delta": delta_frequency_range,
            "Alpha": alpha_frequency_range,
            "Beta": beta_frequency_range,
            "Gamma": gamma_frequency_range,
        }
        for name, (lo, hi, color) in bands.items():
            ax1.axvspan(lo, hi, color=color, alpha=0.12, label=name)

    # Plot coherence
    if plotting_z is True:
        ax1.plot(coherence_results["frequency"], coherence_results["z_score"])
        _max = coherence_results["z_score"].max()
        max_y_lim = _max + _max * 0.1
    else:
        ax1.plot(
            coherence_results["frequency"], coherence_results["coherence"],
        )
        max_y_lim = 1

    # Plot confidence level
    if show_confidence_level is True:
        if coherence_band_results is not None:
            confidence_level = float(
                coherence_band_results["confidence_level"].iat[0]
            )
            ax1.axhline(y=confidence_level, color='red', linestyle='--')

    ax1.set_ylabel(
        "Z coherence (score)" if plotting_z is True else "Coherence (score)",
        fontsize=12,
        labelpad=6,
    )
    ax1.set_xlabel("Frequency (Hz)", fontsize=12, labelpad=6)

    if plotting_z is True:
        title = "Z-scored pooled intramuscular coherence"
    else:
        title = "Pooled intramuscular coherence"
    ax1.set_title(title, fontsize=12, pad=14)

    ax1.set_xlim(0, max_frequency)
    ax1.set_ylim(0, max_y_lim)

    # Manage legend
    if show_legend is True and show_frequency_bands is True:
        if legend_location == "inside":
            ax1.legend(loc="upper right")
        elif legend_location == "outside":
            ax1.legend(
                loc="upper left",
                bbox_to_anchor=(1.02, 1),
                borderaxespad=0,
            )
        else:
            raise ValueError(
                "legend_location must be 'inside' or 'outside'."
            )

    # Manage layout  # TODO replace with layout manager (also for labels and title)
    if tight_layout is True:
        fig.tight_layout()
    ax1.spines["top"].set_visible(False)
    ax1.spines["bottom"].set_visible(True)
    ax1.spines["left"].set_visible(True)
    ax1.spines["right"].set_visible(False)

    # Show the figure
    if showimmediately is True and use_plt is True:
        plt.show()

    return fig


def plot_smoothed_dr_pca_selection(
    pca_results,
    components_to_plot=-1,
    component_numbering_base=0,
    show_legend=True,
    legend_location="inside",
    figsize=[20, 15],
    tight_layout=True,
    showimmediately=True,
    use_plt=True,
):
    """
    Plot the PCA component-selection criterion.

    Parameters
    ----------
    pca_results : dict
        Dictionary containing the PCA results from `smoothed_dr_pca`.
    components_to_plot : int, default -1
        Number of components to plot. If -1, all components are plotted.
    component_numbering_base : int, default 0
        Base used to number components on the x-axis. If 0, components are
        numbered from 0. If 1, components are numbered from 1.
    show_legend : bool, default True
        If True, the legend describing the plotted component-selection
        quantities is shown.
    legend_location : str {"inside", "outside"}, default "inside"
        Location of the legend.

        ``inside``
            The legend is placed inside the figure.

        ``outside``
            The legend is placed outside the figure.
    figsize : list, default [20, 15]
        Size of the figure in centimeters [width, height].
    tight_layout : bool, default True
        If True (default), fig.tight_layout() is called and the figure's
        layout is improved.
        It is useful to set it to False when calling the function from a GUI.
    showimmediately : bool, default True
        If True (default), `plt.show()` is called to display the figure to the
        user. This has an effect only if `use_plt` is True. Set to False when
        using the function within a GUI or when managing figure display
        manually.
    use_plt : bool, default True
        Whether to use the `pyplot` interface (`plt.subplots`) or the
        object-oriented `matplotlib.figure.Figure` API to create the figure.
        Set to False in GUI applications or headless environments to avoid the
        persistent pyplot's global state.

    Returns
    -------
    fig : pyplot `~.figure.Figure`
        The generated PCA component-selection figure.

    Examples
    --------
    Plot the number of PCA components retained using parallel analysis.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askloadmodule()
    >>> steady_emgfile, _, _ = emg.resize_emgfile(
    ...     emgfile,
    ...     area=[15400, 50770],
    ... )
    >>> pca_results = emg.smoothed_dr_pca(
    ...     emgfile=steady_emgfile,
    ...     method_n_components="parallel_analysis",
    ... )
    >>> emg.plot_smoothed_dr_pca_selection(pca_results=pca_results)

    ![](md_graphics/docstrings/plotresults/plot_smoothed_dr_pca_selection_ex_1.png)

    Plot the number of PCA components retained using a cumulative explained
    variance threshold.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askloadmodule()
    >>> steady_emgfile, _, _ = emg.resize_emgfile(
    ...     emgfile,
    ...     area=[15400, 50770],
    ... )
    >>> pca_results = emg.smoothed_dr_pca(
    ...     emgfile=steady_emgfile,
    ...     method_n_components="variance_greater_than_threshold",
    ...     variance_threshold=85.0,
    ... )
    >>> emg.plot_smoothed_dr_pca_selection(pca_results=pca_results)

    ![](md_graphics/docstrings/plotresults/plot_smoothed_dr_pca_selection_ex_2.png)

    Plot the number of PCA components retained using Kaiser's criterion.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askloadmodule()
    >>> steady_emgfile, _, _ = emg.resize_emgfile(
    ...     emgfile,
    ...     area=[15400, 50770],
    ... )
    >>> pca_results = emg.smoothed_dr_pca(
    ...     emgfile=steady_emgfile,
    ...     method_n_components="eigenvalue_greater_than_one",
    ... )
    >>> emg.plot_smoothed_dr_pca_selection(pca_results=pca_results)

    ![](md_graphics/docstrings/plotresults/plot_smoothed_dr_pca_selection_ex_3.png)
    """

    # Validate component numbering base
    if component_numbering_base not in [0, 1]:
        raise ValueError(
            "component_numbering_base must be 0 or 1."
        )

    # Determine number of components to plot
    n_available_components = len(pca_results["eigenvalues"])

    if components_to_plot == -1:
        n_components_to_plot = n_available_components
    elif isinstance(components_to_plot, int) and components_to_plot > 0:
        n_components_to_plot = min(components_to_plot, n_available_components)
    else:
        raise ValueError(
            "components_to_plot must be a positive integer or -1."
        )

    # Component numbers shown on the x-axis
    component_numbers = np.arange(
        component_numbering_base,
        n_components_to_plot + component_numbering_base,
    )

    # Create figure and axis
    fig, ax1 = _create_figure(
        figsize=(figsize[0] / 2.54, figsize[1] / 2.54),
        use_plt=use_plt,
        figname="PCA Component Selection",
    )

    # Plot based on method_n_components
    if pca_results["method_n_components"] == "parallel_analysis":
        ax1.plot(
            component_numbers,
            pca_results["eigenvalues"][:n_components_to_plot],
            "o-",
            label="Observed eigenvalues",
        )

        ax1.plot(
            component_numbers,
            pca_results["percentile_eigenvalues_pa"][
                :n_components_to_plot
            ],
            "s-",
            label="95th percentile simulated eigenvalues",
        )

        ax1.set_ylabel("Eigenvalue (n)", fontsize=12, labelpad=6)
        ax1.set_title("Parallel analysis", fontsize=12, pad=14)

    elif pca_results["method_n_components"] in [
        "variance_greater_than_threshold"
    ]:
        ax1.plot(
            component_numbers,
            pca_results["cumulative_explained_variance"][
                :n_components_to_plot
            ],
            "o-",
            label="Cumulative explained variance",
        )

        ax1.axhline(
            y=pca_results["variance_threshold"],
            color="red",
            linestyle="--",
            label=(
                "Variance threshold "
                f"({pca_results['variance_threshold']}%)"
            ),
        )

        ax1.set_ylabel(
            "Cumulative explained variance (%)",
            fontsize=12,
            labelpad=6,
        )
        ax1.set_title(
            "Variance-based component selection",
            fontsize=12,
            pad=14,
        )

    elif pca_results["method_n_components"] == "eigenvalue_greater_than_one":
        ax1.plot(
            component_numbers,
            pca_results["eigenvalues"][:n_components_to_plot],
            "o-",
            label="Observed eigenvalues",
        )

        ax1.axhline(
            y=1.0,
            color="red",
            linestyle="--",
            label="Kaiser's criterion (λ > 1)",
        )

        ax1.set_ylabel("Eigenvalue (n)", fontsize=12, labelpad=6)
        ax1.set_title(
            "Eigenvalue-based component selection",
            fontsize=12,
            pad=14,
        )

    else:
        raise ValueError(
            "method_n_components must be one of "
            "'parallel_analysis', "
            "'variance_greater_than_threshold', or "
            "'eigenvalue_greater_than_one'."
        )

    ax1.set_xlabel("Component (n)", fontsize=12, labelpad=6)

    # Manage legend  # TODO build a common legend manager, maybe inside figure manager
    if show_legend is True:
        if legend_location == "inside":
            if pca_results["method_n_components"] in [
                "variance_greater_than_threshold"
            ]:
                ax1.legend(loc="lower right")
            else:
                ax1.legend(loc="upper right")
        elif legend_location == "outside":
            ax1.legend(
                loc="upper left",
                bbox_to_anchor=(1.02, 1),
                borderaxespad=0,
            )
        else:
            raise ValueError(
                "legend_location must be 'inside' or 'outside'."
            )

    # Manage layout  # TODO replace with layout manager (also for labels and title)
    if tight_layout is True:
        fig.tight_layout()
    ax1.spines["top"].set_visible(False)
    ax1.spines["bottom"].set_visible(True)
    ax1.spines["left"].set_visible(True)
    ax1.spines["right"].set_visible(False)

    # Force integer ticks on the x-axis
    ax1.xaxis.set_major_locator(MaxNLocator(integer=True))

    # Force integer ticks on the y-axis only for eigenvalue plots
    if pca_results["method_n_components"] in [
        "parallel_analysis",
        "eigenvalue_greater_than_one",
    ]:
        ax1.yaxis.set_major_locator(MaxNLocator(integer=True))

    # Show the figure
    if showimmediately is True and use_plt is True:
        plt.show()

    return fig


def plot_smoothed_dr_pca_low_dimensional_comp(
    emgfile,
    pca_results,
    components_to_plot=-1,
    component_numbering_base=0,
    show_legend=True,
    legend_location="outside",
    figsize=[20, 15],
    tight_layout=True,
    showimmediately=True,
    use_plt=True,
):
    """
    Plot the retained low-dimensional PCA components.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    pca_results : dict
        Dictionary containing the PCA results from `smoothed_dr_pca`.
    components_to_plot : int, default -1
        Number of low-dimensional components to plot. If -1, all retained
        components are plotted.
    component_numbering_base : int, default 0
        Base used to number components in the legend. If 0, components are
        numbered from 0. If 1, components are numbered from 1.
    show_legend : bool, default True
        If True, the legend describing the retained low-dimensional
        components is shown.
    legend_location : str {"inside", "outside"}, default "outside"
        Location of the legend.

        ``inside``
            The legend is placed inside the figure.

        ``outside``
            The legend is placed outside the figure.
    figsize : list, default [20, 15]
        Size of the figure in centimeters [width, height].
    tight_layout : bool, default True
        If True (default), fig.tight_layout() is called and the figure's
        layout is improved.
        It is useful to set it to False when calling the function from a GUI.
    showimmediately : bool, default True
        If True (default), `plt.show()` is called to display the figure to the
        user. This has an effect only if `use_plt` is True. Set to False when
        using the function within a GUI or when managing figure display
        manually.
    use_plt : bool, default True
        Whether to use the `pyplot` interface (`plt.subplots`) or the
        object-oriented `matplotlib.figure.Figure` API to create the figure.
        Set to False in GUI applications or headless environments to avoid the
        persistent pyplot's global state.

    Returns
    -------
    fig : pyplot `~.figure.Figure`
        The generated low-dimensional PCA components figure.

    Examples
    --------
    Plot the retained low-dimensional PCA components.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askloadmodule()
    >>> steady_emgfile, _, _ = emg.resize_emgfile(
    ...     emgfile,
    ...     area=[15400, 50770],
    ... )
    >>> pca_results = emg.smoothed_dr_pca(emgfile=steady_emgfile)
    >>> emg.plot_smoothed_dr_pca_low_dimensional_comp(
    ...     emgfile=steady_emgfile,
    ...     pca_results=pca_results,
    ...     show_legend=False,
    ... )

    ![](md_graphics/docstrings/plotresults/plot_smoothed_dr_pca_low_dimensional_comp_ex_1.png)
    """

    # Validate component numbering base
    if component_numbering_base not in [0, 1]:
        raise ValueError(
            "component_numbering_base must be 0 or 1."
        )

    # Determine number of components to plot
    n_available_components = pca_results["low_dimensional_components"].shape[1]

    if components_to_plot == -1:
        n_components_to_plot = n_available_components
    elif isinstance(components_to_plot, int) and components_to_plot > 0:
        n_components_to_plot = min(components_to_plot, n_available_components)
    else:
        raise ValueError(
            "components_to_plot must be a positive integer or -1."
        )

    # Component numbers shown in the legend
    component_numbers = np.arange(
        component_numbering_base,
        n_components_to_plot + component_numbering_base,
    )

    # Create figure and axis
    fig, ax1 = _create_figure(
        figsize=(figsize[0] / 2.54, figsize[1] / 2.54),
        use_plt=use_plt,
        figname="Smoothed DR PCA Low-Dimensional Components",
    )

    # Calculate time axis
    time = (
        np.arange(pca_results["low_dimensional_components"].shape[0])
        / emgfile["FSAMP"]
    )

    # Plot low-dimensional components
    for component_idx, component_number in enumerate(component_numbers):
        ax1.plot(
            time,
            pca_results["low_dimensional_components"][:, component_idx],
            label=f"Component {component_number}",
        )

    ax1.set_xlabel("Time (s)", fontsize=12, labelpad=6)
    ax1.set_ylabel("Component score", fontsize=12, labelpad=6)
    ax1.set_title("Low-dimensional components", fontsize=12, pad=14)

    # Manage legend
    if show_legend is True:
        if legend_location == "inside":
            ax1.legend(loc="upper right")
        elif legend_location == "outside":
            ax1.legend(
                loc="upper left",
                bbox_to_anchor=(1.02, 1),
                borderaxespad=0,
            )
        else:
            raise ValueError(
                "legend_location must be 'inside' or 'outside'."
            )

    # Manage layout
    if tight_layout is True:
        fig.tight_layout()
    ax1.spines["top"].set_visible(False)
    ax1.spines["bottom"].set_visible(True)
    ax1.spines["left"].set_visible(True)
    ax1.spines["right"].set_visible(False)

    # Show the figure
    if showimmediately is True and use_plt is True:
        plt.show()

    return fig


def plot_common_drive_index(
    cdi_results,
    show_individual_pairs=True,
    show_confidence_level=True,
    show_legend=True,
    legend_location="inside",
    show_values_in_title=True,
    figsize=[20, 15],
    tight_layout=True,
    showimmediately=True,
    use_plt=True,
):
    """
    Plot the common drive index cross-correlation signals.

    Parameters
    ----------
    cdi_results : dict
        Dictionary containing the common drive index results from
        `common_drive_index`.
    show_individual_pairs : bool, default True
        If True, the cross-correlation signals from all individual MU pairs
        are shown in the background.
    show_confidence_level : bool, default True
        If True, the confidence level used to determine significant pairwise
        correlations is shown.
    show_legend : bool, default True
        If True, the legend describing the plotted cross-correlation signals
        is shown.
    legend_location : str {"inside", "outside"}, default "inside"
        Location of the legend.

        ``inside``
            The legend is placed inside the figure.

        ``outside``
            The legend is placed outside the figure.
    show_values_in_title : bool, default True
        If True, common drive index values and the percentage of significant
        pairs are shown in the title.
    figsize : list, default [20, 15]
        Size of the figure in centimeters [width, height].
    tight_layout : bool, default True
        If True (default), fig.tight_layout() is called and the figure's
        layout is improved.
        It is useful to set it to False when calling the function from a GUI.
    showimmediately : bool, default True
        If True (default), `plt.show()` is called to display the figure to the
        user. This has an effect only if `use_plt` is True. Set to False when
        using the function within a GUI or when managing figure display
        manually.
    use_plt : bool, default True
        Whether to use the `pyplot` interface (`plt.subplots`) or the
        object-oriented `matplotlib.figure.Figure` API to create the figure.
        Set to False in GUI applications or headless environments to avoid the
        persistent pyplot's global state.

    Returns
    -------
    fig : pyplot `~.figure.Figure`
        The generated common drive index figure.

    Examples
    --------
    Plot the common drive index cross-correlation signals.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askloadmodule()
    >>> steady_emgfile, _, _ = emg.resize_emgfile(
    ...     emgfile,
    ...     area=[15400, 50770],
    ... )
    >>> cdi_results = emg.common_drive_index(emgfile=steady_emgfile)
    >>> emg.plot_common_drive_index(cdi_results=cdi_results)

    ![](md_graphics/docstrings/plotresults/plot_common_drive_index_ex_1.png)
    """

    # Create figure and axis
    fig, ax1 = _create_figure(
        figsize=(figsize[0] / 2.54, figsize[1] / 2.54),
        use_plt=use_plt,
        figname="Common Drive Index",
    )

    # Plot individual pairwise cross-correlation signals
    lags_seconds = np.asarray(cdi_results["lags_seconds"])
    corr_signals_all_pairs = np.asarray(cdi_results["corr_signals_all_pairs"])

    if show_individual_pairs is True:
        ax1.plot(
            lags_seconds,
            corr_signals_all_pairs,
            color="gray",
            alpha=0.7,
            linewidth=0.5,
        )

    # Plot grand-average cross-correlation signal
    ax1.plot(
        lags_seconds,
        cdi_results["grand_average_corr_values"],
        color="k",
        linewidth=2.5,
        label="Grand average across MU pairs",
    )

    # Plot confidence level
    if show_confidence_level is True:
        ax1.axhline(
            y=cdi_results["confidence_level"],
            color="red",
            linestyle="--",
            label="Confidence level",
        )

        ax1.axhline(
            y=-cdi_results["confidence_level"],
            color="red",
            linestyle="--",
        )

    # Set y-axis limits
    values_for_ylim = [
        np.nanmin(cdi_results["grand_average_corr_values"]),
    ]

    if show_individual_pairs is True:
        values_for_ylim.append(
            np.nanmin(corr_signals_all_pairs)
        )

    if show_confidence_level is True:
        confidence_level = cdi_results["confidence_level"]
        values_for_ylim.extend([
            -confidence_level,
            confidence_level,
        ])

    min_y_value = min(values_for_ylim)

    if min_y_value < 0:
        ax1.set_ylim(min_y_value, 1)
    else:
        ax1.set_ylim(0, 1)

    ax1.set_xlabel("Lag (s)", fontsize=12, labelpad=6)
    ax1.set_ylabel("Mean cross-correlation", fontsize=12, labelpad=6)

    # Set title
    title = "Common drive index"
    if show_values_in_title is True:
        title += (
            "\nCommon drive index: {:.3f} ± {:.3f}, "
            "Significant pairs: {:.1f}%".format(
                cdi_results["common_drive_index_thresholded_mean"],
                cdi_results["common_drive_index_thresholded_std"],
                cdi_results["percentage_significant_pairs"],
            )
        )
    ax1.set_title(title, fontsize=12, pad=14)

    # Manage legend
    if show_legend is True:
        if legend_location == "inside":
            ax1.legend(loc="upper right")
        elif legend_location == "outside":
            ax1.legend(
                loc="upper left",
                bbox_to_anchor=(1.02, 1),
                borderaxespad=0,
            )
        else:
            raise ValueError(
                "legend_location must be 'inside' or 'outside'."
            )

    # Manage layout  # TODO replace with layout manager (also for labels and title)
    if tight_layout is True:
        fig.tight_layout()
    ax1.spines["top"].set_visible(False)
    ax1.spines["bottom"].set_visible(True)
    ax1.spines["left"].set_visible(True)
    ax1.spines["right"].set_visible(False)

    # Show the figure
    if showimmediately is True and use_plt is True:
        plt.show()

    return fig


def plot_common_drive_matrix(
    cdi_results,
    thresholded=True,
    mu_numbering_base=0,
    cmap="coolwarm",
    vmin=0,
    vmax=1,
    show_colorbar=True,
    show_values_in_title=True,
    figsize=[20, 15],
    tight_layout=True,
    showimmediately=True,
    use_plt=True,
):
    """
    Plot the pairwise common drive matrix.

    Parameters
    ----------
    cdi_results : dict
        Dictionary containing the common drive index results from
        `common_drive_index`.
    thresholded : bool, default True
        If True, the thresholded pairwise common drive matrix is plotted.
        If False, the non-thresholded pairwise common drive matrix is plotted.
    mu_numbering_base : int, default 0
        Base used to number MUs on the x- and y-axes. If 0, MUs are numbered
        from 0. If 1, MUs are numbered from 1.
    cmap : str, default "coolwarm"
        Matplotlib colormap used to plot the pairwise common drive matrix.
    vmin : int or float, default 0
        Minimum value used to scale the colormap.
    vmax : int or float, default 1
        Maximum value used to scale the colormap.
    show_colorbar : bool, default True
        If True, the colorbar describing the matrix values is shown.
    show_values_in_title : bool, default True
        If True, common drive index values and the percentage of significant
        pairs are shown in the title.
    figsize : list, default [20, 15]
        Size of the figure in centimeters [width, height].
    tight_layout : bool, default True
        If True (default), fig.tight_layout() is called and the figure's
        layout is improved.
        It is useful to set it to False when calling the function from a GUI.
    showimmediately : bool, default True
        If True (default), `plt.show()` is called to display the figure to the
        user. This has an effect only if `use_plt` is True. Set to False when
        using the function within a GUI or when managing figure display
        manually.
    use_plt : bool, default True
        Whether to use the `pyplot` interface (`plt.subplots`) or the
        object-oriented `matplotlib.figure.Figure` API to create the figure.
        Set to False in GUI applications or headless environments to avoid the
        persistent pyplot's global state.

    Returns
    -------
    fig : pyplot `~.figure.Figure`
        The generated pairwise common drive matrix figure.

    Examples
    --------
    Plot the thresholded pairwise common drive matrix.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askloadmodule()
    >>> steady_emgfile, _, _ = emg.resize_emgfile(
    ...     emgfile,
    ...     area=[15400, 50770],
    ... )
    >>> cdi_results = emg.common_drive_index(emgfile=steady_emgfile)
    >>> emg.plot_common_drive_matrix(cdi_results=cdi_results)

    ![](md_graphics/docstrings/plotresults/plot_common_drive_matrix_ex_1.png)
    """

    # Validate MU numbering base
    if mu_numbering_base not in [0, 1]:
        raise ValueError(
            "mu_numbering_base must be 0 or 1."
        )

    # Select matrix to plot
    if thresholded is True:
        correlation_matrix_plot = cdi_results[
            "pairwise_correlation_matrix_thresholded"
        ]
    else:
        correlation_matrix_plot = cdi_results[
            "pairwise_correlation_matrix"
        ]

    # Create figure and axis
    fig, ax1 = _create_figure(
        figsize=(figsize[0] / 2.54, figsize[1] / 2.54),
        use_plt=use_plt,
        figname="Common Drive Matrix",
    )

    # Plot pairwise common drive matrix
    im = ax1.imshow(
        correlation_matrix_plot,
        cmap=cmap,
        aspect="auto",
        origin="upper",
        vmin=vmin,
        vmax=vmax,
    )

    # Manage colorbar
    if show_colorbar is True:
        cbar = fig.colorbar(im, ax=ax1)
        cbar.set_label("Mean cross-correlation", fontsize=12, labelpad=6)

    # MU numbers shown on the x- and y-axes
    n_motor_units = correlation_matrix_plot.shape[0]
    motor_unit_numbers = np.arange(
        mu_numbering_base,
        n_motor_units + mu_numbering_base,
    )

    ax1.set_xticks(np.arange(n_motor_units))
    ax1.set_yticks(np.arange(n_motor_units))
    ax1.set_xticklabels(motor_unit_numbers)
    ax1.set_yticklabels(motor_unit_numbers)

    ax1.set_xlabel("Motor unit (n)", fontsize=12, labelpad=6)
    ax1.set_ylabel("Motor unit (n)", fontsize=12, labelpad=6)

    # Set title
    if thresholded is True:
        title = "Thresholded pairwise common drive matrix"
        if show_values_in_title is True:
            title += (
                "\nCommon drive index: {:.3f} ± {:.3f}, "
                "Significant pairs: {:.1f}%".format(
                    cdi_results["common_drive_index_thresholded_mean"],
                    cdi_results["common_drive_index_thresholded_std"],
                    cdi_results["percentage_significant_pairs"],
                )
            )
    else:
        title = "Pairwise common drive matrix"
        if show_values_in_title is True:
            title += (
                "\nCommon drive index: {:.3f} ± {:.3f}, "
                "Significant pairs: {:.1f}%".format(
                    cdi_results["common_drive_index_mean"],
                    cdi_results["common_drive_index_std"],
                    cdi_results["percentage_significant_pairs"],
                )
            )
    ax1.set_title(title, fontsize=12, pad=14)

    # Force integer ticks on the x- and y-axes
    ax1.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax1.yaxis.set_major_locator(MaxNLocator(integer=True))

    # Manage layout  # TODO replace with layout manager (also for labels and title)
    if tight_layout is True:
        fig.tight_layout()

    # Show the figure
    if showimmediately is True and use_plt is True:
        plt.show()

    return fig


def plot_pci_index(
    pci_results,
    show_legend=True,
    legend_location="inside",
    figsize=[20, 15],
    tight_layout=True,
    showimmediately=True,
    use_plt=True,
):
    """
    Plot observed and fitted PCI coherence values.

    Parameters
    ----------
    pci_results : dict
        Dictionary containing the proportion of common input index results from
        `pci_index`.
    show_legend : bool, default True
        If True, the legend describing the observed and fitted coherence
        values for each frequency band is shown.
    legend_location : str {"inside", "outside"}, default "inside"
        Location of the legend.

        ``inside``
            The legend is placed inside the figure.

        ``outside``
            The legend is placed outside the figure.
    figsize : list, default [20, 15]
        Size of the figure in centimeters [width, height].
    tight_layout : bool, default True
        If True (default), fig.tight_layout() is called and the figure's
        layout is improved.
        It is useful to set it to False when calling the function from a GUI.
    showimmediately : bool, default True
        If True (default), `plt.show()` is called to display the figure to the
        user. This has an effect only if `use_plt` is True. Set to False when
        using the function within a GUI or when managing figure display
        manually.
    use_plt : bool, default True
        Whether to use the `pyplot` interface (`plt.subplots`) or the
        object-oriented `matplotlib.figure.Figure` API to create the figure.
        Set to False in GUI applications or headless environments to avoid the
        persistent pyplot's global state.

    Returns
    -------
    fig : pyplot `~.figure.Figure`
        The generated PCI figure.

    Examples
    --------
    Plot observed and fitted coherence values used to estimate the PCI index.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askloadmodule()
    >>> steady_emgfile, _, _ = emg.resize_emgfile(
    ...     emgfile,
    ...     area=[15400, 50770],
    ... )
    >>> pci_results = emg.pci_index(emgfile=steady_emgfile)
    >>> emg.plot_pci_index(pci_results=pci_results)

    ![](md_graphics/docstrings/plotresults/plot_pci_index_ex_1.png)
    """

    # Get PCI dataframes
    average_coherence_df = pci_results["average_coherence_df"]
    fitted_average_coherence_df = pci_results[
        "fitted_average_coherence_df"
    ]

    # Create figure and axis
    fig, ax1 = _create_figure(
        figsize=(figsize[0] / 2.54, figsize[1] / 2.54),
        use_plt=use_plt,
        figname="Proportion of Common Input Index",
    )

    # Plot observed coherence values
    for band_name, col_name in {
        "Delta": "average_delta",
        "Alpha": "average_alpha",
        "Beta": "average_beta",
    }.items():
        ax1.plot(
            average_coherence_df["number_of_mus_cst"],
            average_coherence_df[col_name],
            "o",
            label=f"{band_name} observed",
        )

    # Plot fitted coherence values
    for band_name, col_name in {
        "Delta": "fitted_delta",
        "Alpha": "fitted_alpha",
        "Beta": "fitted_beta",
    }.items():
        ax1.plot(
            fitted_average_coherence_df["number_of_mus_cst"],
            fitted_average_coherence_df[col_name],
            "-",
            label=f"{band_name} fit",
        )

    ax1.set_xlabel(
        "MUs per cumulative spike train (n)",
        fontsize=12,
        labelpad=6,
    )
    ax1.set_ylabel("Average coherence", fontsize=12, labelpad=6)
    ax1.set_title("Proportion of common input index", fontsize=12, pad=14)
    ax1.set_ylim(0, 1)

    # Force integer ticks on the x-axis
    ax1.xaxis.set_major_locator(MaxNLocator(integer=True))

    # Manage legend
    if show_legend is True:
        if legend_location == "inside":
            ax1.legend(loc="upper right")
        elif legend_location == "outside":
            ax1.legend(
                loc="upper left",
                bbox_to_anchor=(1.02, 1),
                borderaxespad=0,
            )
        else:
            raise ValueError(
                "legend_location must be 'inside' or 'outside'."
            )

    # Manage layout
    if tight_layout is True:
        fig.tight_layout()
    ax1.spines["top"].set_visible(False)
    ax1.spines["bottom"].set_visible(True)
    ax1.spines["left"].set_visible(True)
    ax1.spines["right"].set_visible(False)

    # Show the figure
    if showimmediately is True and use_plt is True:
        plt.show()

    return fig


def plot_smoothed_dr_mutualinformation_matrix(
    network_results,
    thresholded=True,
    mu_numbering_base=0,
    cmap="coolwarm",
    vmin=0,
    vmax=1,
    show_colorbar=True,
    show_values_in_title=True,
    figsize=[20, 15],
    tight_layout=True,
    showimmediately=True,
    use_plt=True,
):
    """
    Plot the pairwise mutual-information matrix.

    Parameters
    ----------
    network_results : dict
        Dictionary containing the network information framework results from
        `smoothed_dr_mutualinformation`.
    thresholded : bool, default True
        If True, the thresholded pairwise mutual-information matrix is plotted.
        If False, the non-thresholded pairwise mutual-information matrix is
        plotted.
    mu_numbering_base : int, default 0
        Base used to number MUs on the x- and y-axes. If 0, MUs are numbered
        from 0. If 1, MUs are numbered from 1.
    cmap : str, default "coolwarm"
        Matplotlib colormap used to plot the pairwise mutual-information
        matrix.
    vmin : int or float, default 0
        Minimum value used to scale the colormap.
    vmax : int or float, default 1
        Maximum value used to scale the colormap.
    show_colorbar : bool, default True
        If True, the colorbar describing the matrix values is shown.
    show_values_in_title : bool, default True
        If True, common drive index values and the percentage of significant
        pairs are shown in the title.
    figsize : list, default [20, 15]
        Size of the figure in centimeters [width, height].
    tight_layout : bool, default True
        If True (default), fig.tight_layout() is called and the figure's
        layout is improved.
        It is useful to set it to False when calling the function from a GUI.
    showimmediately : bool, default True
        If True (default), `plt.show()` is called to display the figure to the
        user. This has an effect only if `use_plt` is True. Set to False when
        using the function within a GUI or when managing figure display
        manually.
    use_plt : bool, default True
        Whether to use the `pyplot` interface (`plt.subplots`) or the
        object-oriented `matplotlib.figure.Figure` API to create the figure.
        Set to False in GUI applications or headless environments to avoid the
        persistent pyplot's global state.

    Returns
    -------
    fig : pyplot `~.figure.Figure`
        The generated mutual-information matrix figure.

    Examples
    --------
    Examples
    --------
    Plot the thresholded pairwise mutual-information matrix.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askloadmodule()
    >>> steady_emgfile, _, _ = emg.resize_emgfile(
    ...     emgfile,
    ...     area=[15400, 50770],
    ... )
    >>> network_results = emg.smoothed_dr_mutualinformation(
    ...     emgfile=steady_emgfile,
    ... )
    >>> emg.plot_smoothed_dr_mutualinformation_matrix(
    ...     network_results=network_results
    ... )

    ![](md_graphics/docstrings/plotresults/plot_smoothed_dr_mutualinformation_matrix_ex_1.png)

    Plot the non-thresholded pairwise mutual-information matrix using
    automatic colour scaling.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askloadmodule()
    >>> steady_emgfile, _, _ = emg.resize_emgfile(
    ...     emgfile,
    ...     area=[15400, 50770],
    ... )
    >>> network_results = emg.smoothed_dr_mutualinformation(
    ...     emgfile=steady_emgfile,
    ... )
    >>> emg.plot_smoothed_dr_mutualinformation_matrix(
    ...     network_results=network_results,
    ...     thresholded=False,
    ...     vmax=0.5,
    ... )

    ![](md_graphics/docstrings/plotresults/plot_smoothed_dr_mutualinformation_matrix_ex_2.png)
    """

    # Validate MU numbering base
    if mu_numbering_base not in [0, 1]:
        raise ValueError(
            "mu_numbering_base must be 0 or 1."
        )

    # Select matrix to plot
    if thresholded is True:
        mutual_information_matrix = network_results[
            "pairwise_mi_matrix_thresholded"
        ].copy()
    else:
        mutual_information_matrix = network_results[
            "pairwise_mi_matrix"
        ].copy()

    # Create figure and axis
    fig, ax1 = _create_figure(
        figsize=(figsize[0] / 2.54, figsize[1] / 2.54),
        use_plt=use_plt,
        figname="Smoothed DR mutual Information Matrix",
    )

    # Plot matrix
    im = ax1.imshow(
        mutual_information_matrix,
        cmap=cmap,
        aspect="auto",
        origin="upper",
        vmin=vmin,
        vmax=vmax,
    )

    # Manage colorbar
    if show_colorbar is True:
        cbar = fig.colorbar(im, ax=ax1)
        cbar.set_label("Mutual information", fontsize=12, labelpad=6)

    # MU numbers shown on the x- and y-axes
    n_motor_units = mutual_information_matrix.shape[0]
    motor_unit_numbers = np.arange(
        mu_numbering_base,
        n_motor_units + mu_numbering_base,
    )

    ax1.set_xticks(np.arange(n_motor_units))
    ax1.set_yticks(np.arange(n_motor_units))
    ax1.set_xticklabels(motor_unit_numbers)
    ax1.set_yticklabels(motor_unit_numbers)

    ax1.set_xlabel("Motor unit (n)", fontsize=12, labelpad=6)
    ax1.set_ylabel("Motor unit (n)", fontsize=12, labelpad=6)

    # Set title
    if thresholded is True:
        title = "Thresholded mutual-information matrix"
        if show_values_in_title is True:
            title += (
                "\nNetwork density: {:.2f}, "
                "Significant pairs: {:.1f}%".format(
                    network_results["network_density"],
                    network_results["percentage_significant_pairs"],
                )
            )
    else:
        title = "Pairwise mutual-information matrix"
    ax1.set_title(title, fontsize=12, pad=14)

    # Force integer ticks on the x- and y-axes
    ax1.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax1.yaxis.set_major_locator(MaxNLocator(integer=True))

    # Manage layout
    if tight_layout is True:
        fig.tight_layout()

    # Show the figure
    if showimmediately is True and use_plt is True:
        plt.show()

    return fig


def plot_smoothed_dr_mu_network(
    network_results,
    mu_numbering_base=0,
    node_size=800,
    show_labels=True,
    show_values_in_title=True,
    figsize=[20, 15],
    tight_layout=True,
    showimmediately=True,
    use_plt=True,
):
    """
    Plot the MU mutual-information network.

    Parameters
    ----------
    network_results : dict
        Dictionary containing the network information framework results from
        `smoothed_dr_mutualinformation`.
    mu_numbering_base : int, default 0
        Base used to number MUs on the x- and y-axes. If 0, MUs are numbered
        from 0. If 1, MUs are numbered from 1.
    node_size : int or float, default 800
        Size of the network nodes.
    show_labels : bool, default True
        If True, MU labels are shown inside the network nodes.
    show_values_in_title : bool, default True
        If True, common drive index values and the percentage of significant
        pairs are shown in the title.
    figsize : list, default [20, 15]
        Size of the figure in centimeters [width, height].
    tight_layout : bool, default True
        If True (default), fig.tight_layout() is called and the figure's
        layout is improved.
        It is useful to set it to False when calling the function from a GUI.
    showimmediately : bool, default True
        If True (default), `plt.show()` is called to display the figure to the
        user. This has an effect only if `use_plt` is True. Set to False when
        using the function within a GUI or when managing figure display
        manually.
    use_plt : bool, default True
        Whether to use the `pyplot` interface (`plt.subplots`) or the
        object-oriented `matplotlib.figure.Figure` API to create the figure.
        Set to False in GUI applications or headless environments to avoid the
        persistent pyplot's global state.

    Returns
    -------
    fig : pyplot `~.figure.Figure`
        The generated MU network figure.

    Examples
    --------
    Plot the MU mutual-information network.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askloadmodule()
    >>> steady_emgfile, _, _ = emg.resize_emgfile(
    ...     emgfile,
    ...     area=[15400, 50770],
    ... )
    >>> network_results = emg.smoothed_dr_mutualinformation(
    ...     emgfile=steady_emgfile,
    ... )
    >>> emg.plot_smoothed_dr_mu_network(network_results=network_results)

    ![](md_graphics/docstrings/plotresults/plot_smoothed_dr_mu_network_ex_1.png)
    """

    # Validate motor unit numbering base
    if mu_numbering_base not in [0, 1]:
        raise ValueError(
            "mu_numbering_base must be 0 or 1."
        )

    # Get network data
    pairwise_mi_thresholded = network_results[
        "pairwise_mi_matrix_thresholded"
    ].copy()
    module_affiliation_matrix = network_results[
        "module_affiliation_matrix"
    ]

    n_nodes = pairwise_mi_thresholded.shape[0]

    # Create figure and axis
    fig, ax1 = _create_figure(
        figsize=(figsize[0] / 2.54, figsize[1] / 2.54),
        use_plt=use_plt,
        figname="Smoothed DR MU Network",
    )

    # Calculate circular node positions
    theta = np.linspace(
        0,
        2 * np.pi,
        n_nodes,
        endpoint=False,
    )

    pos = np.column_stack(
        (
            np.cos(theta),
            np.sin(theta),
        )
    )

    # Get edge list and weights
    edge_indices = np.argwhere(np.triu(pairwise_mi_thresholded, k=1) > 0)

    if edge_indices.size > 0:
        edge_weights = pairwise_mi_thresholded[
            edge_indices[:, 0],
            edge_indices[:, 1],
        ]
        max_edge_weight = np.max(edge_weights)
    else:
        edge_weights = np.array([])
        max_edge_weight = 0.0

    # Draw edges
    for edge_idx, (i, j) in enumerate(edge_indices):

        if max_edge_weight > 0:
            edge_width = 2 * edge_weights[edge_idx] / max_edge_weight
        else:
            edge_width = 1.0

        ax1.plot(
            [pos[i, 0], pos[j, 0]],
            [pos[i, 1], pos[j, 1]],
            color=[0.957, 0.839, 0.855],
            linewidth=edge_width,
            zorder=1,
        )

    # Define node colours
    node_colors = np.tile(
        np.array([0.816, 0.285, 0.355]),
        (n_nodes, 1),
    )

    if (
        module_affiliation_matrix.size > 0
        and module_affiliation_matrix.shape[0] >= 1
    ):
        nodes_not_in_first_component = np.where(
            module_affiliation_matrix[0, :] == 0
        )[0]

        node_colors[nodes_not_in_first_component, :] = np.array(
            [0.6, 0.6, 0.6]
        )

    # Draw nodes
    ax1.scatter(
        pos[:, 0],
        pos[:, 1],
        s=node_size,
        c=node_colors,
        edgecolors="black",
        linewidths=0.6,
        zorder=2,
    )

    # Draw node labels
    if show_labels is True:
        for node_idx in range(n_nodes):

            motor_unit_number = node_idx + mu_numbering_base

            ax1.text(
                pos[node_idx, 0],
                pos[node_idx, 1],
                f"MU{motor_unit_number}",
                ha="center",
                va="center",
                fontsize=8,
                color="black",
                zorder=3,
            )

    # Set title
    title = "Motor unit network"
    if show_values_in_title is True:
        title += (
            "\nNumber of components: {}\n"
            "Motor units in first component: {:.1f}%".format(
                network_results["number_of_components"],
                network_results["percentage_mus_first_component"],
            )
        )
    ax1.set_title(title, fontsize=12, pad=14)

    ax1.set_axis_off()
    ax1.set_aspect("equal")

    # Manage layout
    if tight_layout is True:
        fig.tight_layout()

    # Show the figure
    if showimmediately is True and use_plt is True:
        plt.show()

    return fig
