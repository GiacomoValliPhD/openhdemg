"""
This module contains all the functions used to visualise the content of the
imported EMG file, the MUs properties or to save figures.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import warnings
from openhdemg.library.tools import compute_idr
from openhdemg.library.mathtools import min_max_scaling


def showgoodlayout(tight_layout=True, despined=False):
    """
    **WARNING!** This function is deprecated since v0.1.1 and will be removed
    in v0.2.0. Please use Figure_Layout_Manager(figure).set_layout() instead.

    Despine and show plots with a good layout.

    This function is called by the various plot functions contained in the
    library but can also be used by the user to quickly adjust the layout of
    custom plots.

    Parameters
    ----------
    tight_layout : bool, default True
        If true (default), plt.tight_layout() is applied to the figure.
    despined : bool or str {"2yaxes"}, default False

        False: left and bottom is not despined (standard plotting).

        True: all the sides are despined.

        ``2yaxes``
            Only the top is despined.
            This is used to show y axes both on the right and left side at the
            same time.
    """

    # Warn for the use of a deprecated function
    msg = (
        "This function is deprecated since v0.1.1 and will be removed after " +
        "v0.2.0. Please use Figure_Layout_Manager(figure).set_layout()."
    )
    warnings.warn(msg, DeprecationWarning, stacklevel=2)

    if despined is False:
        sns.despine()
    elif despined is True:
        sns.despine(top=True, bottom=True, left=True, right=True)
    elif despined == "2yaxes":
        sns.despine(top=True, bottom=False, left=False, right=False)
    else:
        raise ValueError(
            f"despined can be True, False or 2yaxes. {despined} was passed instead"
        )

    if tight_layout is True:
        plt.tight_layout()


class Figure_Layout_Manager():
    """
    Class managing custom layout and custom settings for 2D plots.

    Parameters
    ----------
    figure : pyplot `~.figure.Figure`
        The matplotlib.pyplot figure to manage.

    Attributes
    ----------
    figure : pyplot `~.figure.Figure`
        The managed matplotlib.pyplot figure.
    default_line2d_kwargs_ax1 : dict
        Default kwargs for matplotlib.lines.Line2D relative to figure's axis 1.
    default_line2d_kwargs_ax2 : dict
        Default kwargs for matplotlib.lines.Line2D relative to figure's axis 2.
    default_axes_kwargs : dict
        Default kwargs for figure's axes.

    Methods
    -------
    get_final_kwargs()
        Combine default and user specified kwargs and return the final kwargs.
    set_layout()
        Set the figure's layout regarding spines and tight layout.
    set_style_from_kwargs()
        Set line2d, labels, title, ticks and grid.
        If custom styles are needed, this method should be used after calling
        the get_final_kwargs() method. Otherwise, the standard openhdemg
        style will be used.

    Examples
    --------
    Initialise the Figure_Layout_Manager.

    >>> import openhdemg.library as emg
    >>> import matplotlib.pyplot as plt
    >>> fig, ax1 = plt.subplots()
    >>> fig_manager = emg.Figure_Layout_Manager(figure=fig)

    Access the default_axes_kwargs and print them in an easy-to-read way.

    >>> import pprint
    >>> default_axes_kwargs = fig_manager.default_axes_kwargs
    >>> pp = pprint.PrettyPrinter(indent=4, width=80)
    >>> pp.pprint(default_axes_kwargs)
    {   'grid': {  'alpha': 0.7,
                   'axis': 'both',
                   'color': 'gray',
                   'linestyle': '--',
                   'linewidth': 0.5,
                   'visible': False},
        'labels': {  'labelpad': 6,
                     'title': None,
                     'title_color': 'black',
                     'title_pad': 14,
                     'title_size': 12,
                     'xlabel': None,
                     'xlabel_color': 'black',
                     'xlabel_size': 12,
                     'ylabel_dx': None,
                     'ylabel_dx_color': 'black',
                     'ylabel_dx_size': 12,
                     'ylabel_sx': None,
                     'ylabel_sx_color': 'black',
                     'ylabel_sx_size': 12},
        'ticks_ax1': {  'axis': 'both',
                        'colors': 'black',
                        'direction': 'out',
                        'labelrotation': 0,
                        'labelsize': 10},
        'ticks_ax2': {  'axis': 'y',
                        'colors': 'black',
                        'direction': 'out',
                        'labelrotation': 0,
                        'labelsize': 10}}

    Access the default line2d kwargs and print them in an easy-to-read way.

    >>> default_line2d_kwargs_ax1 = fig_manager.default_line2d_kwargs_ax1
    >>> pp.pprint(default_line2d_kwargs_ax1)
    {'linewidth': 1}

    >>> default_line2d_kwargs_ax2 = fig_manager.default_line2d_kwargs_ax2
    >>> pp.pprint(default_line2d_kwargs_ax2)
    {'color': '0.4', 'linewidth': 2}
    """

    def __init__(self, figure):
        # Init method that sets default kwargs.

        self.figure = figure

        self.default_line2d_kwargs_ax1 = {
            "linewidth": 1,
        }

        self.default_line2d_kwargs_ax2 = {
            "linewidth": 2,
            "color": '0.4',
        }

        self.default_axes_kwargs = {
            "grid": {
                "visible": False,
                "axis": "both",
                "color": "gray",
                "linestyle": "--",
                "linewidth": 0.5,
                "alpha": 0.7
            },
            "labels": {
                "xlabel": None,
                "ylabel_sx": None,
                "ylabel_dx": None,
                "title": None,
                "xlabel_size": 12,
                "xlabel_color": "black",
                "ylabel_sx_size": 12,
                "ylabel_sx_color": "black",
                "ylabel_dx_size": 12,
                "ylabel_dx_color": "black",
                "labelpad": 6,
                "title_size": 12,
                "title_color": "black",
                "title_pad": 14,
            },
            "ticks_ax1": {
                "axis": "both",
                "labelsize": 10,
                "labelrotation": 0,
                "direction": "out",
                "colors": "black",
            },
            "ticks_ax2": {
                "axis": "y",
                "labelsize": 10,
                "labelrotation": 0,
                "direction": "out",
                "colors": "black",
            }
        }

        # Define the final kwargs that will be used to set figures' stile
        # unless updated with get_final_kwargs().
        self.final_kwargs = (
            self.default_line2d_kwargs_ax1,
            self.default_line2d_kwargs_ax2,
            self.default_axes_kwargs,
        )

    def get_final_kwargs(
        self,
        line2d_kwargs_ax1=None,
        line2d_kwargs_ax2=None,
        axes_kwargs=None,
    ):
        """
        Update default kwarg values with user-specified kwargs.

        This method merges default keyword arguments for line plots and axes
        with user-specified arguments, allowing customization of plot
        aesthetics.

        The use of the kwargs is clarified below in the Notes section.

        Parameters
        ----------
        line2d_kwargs_ax1 : dict, optional
            User-specified keyword arguments for the first set of Line2D
            objects. If None, the default values will be used.
        line2d_kwargs_ax2 : dict, optional
            User-specified keyword arguments for the second set of Line2D
            objects (when twinx is used and a second Y axis is generated).
            If None, the default values will be used.
        axes_kwargs : dict, optional
            User-specified keyword arguments for the axes' styling.
            If None, the default values will be used.

        Returns
        -------
        final_kwargs : tuple
            A tuple containing three dictionaries:

            1. Updated line2d kwargs for the first axis.
            2. Updated line2d kwargs for the second axis.
            3. Updated axes kwargs.

        Notes
        -----
        The method ensures that any user-specified kwargs will override the
        corresponding default values. If no user kwargs are provided for a
        particular category, the defaults will be retained.

        ``line2d_kwargs_ax1`` and ``line2d_kwargs_ax2`` can contain any of the
        matplotlib.lines.Line2D parameters as described at:
        (https://matplotlib.org/stable/api/_as_gen/matplotlib.lines.Line2D.html).

        ``axes_kwargs`` can contain up to 4 dictionaries ("grid", "labels",
        "ticks_ax1", "ticks_ax2") which regulate specific styles.

        - ``grid`` can contain any of the matplotlib.axes.Axes.grid parameters
        as described at:
        (https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.grid.html).
        - ``labels`` can contain only specific parameters (with default values
        below):

            - "xlabel": None,
            - "ylabel_sx": None,
            - "ylabel_dx": None,
            - "title": None,
            - "xlabel_size": 12,
            - "xlabel_color": "black",
            - "ylabel_sx_size": 12,
            - "ylabel_sx_color": "black",
            - "ylabel_dx_size": 12,
            - "ylabel_dx_color": "black",
            - "labelpad": 6,
            - "title_size": 12,
            - "title_color": "black",
            - "title_pad": 14,

        - ``ticks_ax1`` and ``ticks_ax2`` can contain any of the
        matplotlib.pyplot.tick_params as described at:
        (https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.tick_params.html).

        Examples
        --------
        Plot data in 2 Y axes.

        >>> import openhdemg.library as emg
        >>> import matplotlib.pyplot as plt
        >>> fig, ax1 = plt.subplots()
        >>> ax1.plot([1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1])
        >>> ax2 = ax1.twinx()
        >>> ax2.plot([6, 5, 4, 3, 2, 1, 2, 3, 4, 5, 6])

        Declare custom user plotting kwargs.

        >>> line2d_kwargs_ax1 = {
        ...     "linewidth": 3,
        ...     "alpha": 0.2,
        ... }
        >>> line2d_kwargs_ax2 = {
        ...     "linewidth": 1,
        ...     "alpha": 0.2,
        ...     "color": "red",
        ... }
        >>> axes_kwargs = {
        ...     "grid": {
        ...         "visible": True,
        ...         "axis": "both",
        ...         "color": "gray",
        ...     },
        ... }

        Merge default and user kwargs.

        >>> fig_manager = emg.Figure_Layout_Manager(figure=fig)
        >>> final_kwargs = fig_manager.get_final_kwargs(
        ...     line2d_kwargs_ax1=line2d_kwargs_ax1,
        ...     line2d_kwargs_ax2=line2d_kwargs_ax2,
        ...     axes_kwargs=axes_kwargs,
        ... )

        Print them in an easy-to-read way.

        >>> import pprint
        >>> pp = pprint.PrettyPrinter(indent=4, width=40)
        >>> pp.pprint(final_kwargs[0])
        {   'alpha': 0.2,
            'linewidth': 3}

        >>> pp.pprint(final_kwargs[1])
        {   'alpha': 0.2,
            'color': 'red',
            'linewidth': 1}

        >>> pp.pprint(final_kwargs[2])
        {   'grid': {   'alpha': 0.7,
                        'axis': 'both',
                        'color': 'gray',
                        'linestyle': '--',
                        'linewidth': 0.5,
                        'visible': True},
            'labels': {   'labelpad': 6,
                        'title': None,
                        'title_color': 'black',
                        'title_pad': 14,
                        'title_size': 12,
                        'xlabel': None,
                        'xlabel_color': 'black',
                        'xlabel_size': 12,
                        'ylabel_dx': None,
                        'ylabel_dx_color': 'black',
                        'ylabel_dx_size': 12,
                        'ylabel_sx': None,
                        'ylabel_sx_color': 'black',
                        'ylabel_sx_size': 12},
            'ticks_ax1': {   'axis': 'both',
                            'colors': 'black',
                            'direction': 'out',
                            'labelrotation': 0,
                            'labelsize': 10},
            'ticks_ax2': {   'axis': 'y',
                            'colors': 'black',
                            'direction': 'out',
                            'labelrotation': 0,
                            'labelsize': 10}}
        """

        # Update default kwarg values with user-specified kwargs and return
        # them.
        if line2d_kwargs_ax1 is None:
            line2d_kwargs_ax1 = {}
        if line2d_kwargs_ax2 is None:
            line2d_kwargs_ax2 = {}
        if axes_kwargs is None:
            axes_kwargs = {}

        # Dictionaries
        self.line2d_kwargs_ax1 = {
            **self.default_line2d_kwargs_ax1, **line2d_kwargs_ax1
        }
        self.line2d_kwargs_ax2 = {
            **self.default_line2d_kwargs_ax2, **line2d_kwargs_ax2
        }
        # Nested dictionary
        self.axes_kwargs = {}
        for key in self.default_axes_kwargs.keys():
            if key in axes_kwargs.keys():
                self.axes_kwargs[key] = {
                    **self.default_axes_kwargs[key], **axes_kwargs[key]
                }
            else:
                self.axes_kwargs[key] = self.default_axes_kwargs[key]

        self.final_kwargs = (
            self.line2d_kwargs_ax1, self.line2d_kwargs_ax2, self.axes_kwargs,
        )

        return self.final_kwargs

    def set_layout(self, tight_layout=True, despine="box"):
        """
        Despine and show plots with a tight layout.

        This method is called by the various plot functions contained in the
        library but can also be used by the user to quickly adjust the layout
        of custom plots.

        Parameters
        ----------
        tight_layout : bool, default True
            If true, plt.tight_layout() is applied to the figure.
        despined : str {"box", "all", "1yaxis", "2yaxes"}, default "box"

            ``box``
                No side is despined.

            ``all``
                All the sides are despined.

            ``1yaxis``
                Right and top are despined.
                This is used to show the Y axis on the left side.

            ``2yaxes``
                Only the top is despined.
                This is used to show Y axes both on the left and right side at
                the same time.

        Examples
        --------
        Plot data in 2 Y axes.

        >>> import openhdemg.library as emg
        >>> import matplotlib.pyplot as plt
        >>> fig, ax1 = plt.subplots()
        >>> ax1.plot([1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1])
        >>> ax2 = ax1.twinx()
        >>> ax2.plot([6, 5, 4, 3, 2, 1, 2, 3, 4, 5, 6])

        Show the figure with 2 Y axes.

        >>> fig_manager = emg.Figure_Layout_Manager(figure=fig)
        >>> fig_manager.set_layout(tight_layout=True, despine="2yaxes")
        >>> plt.show()

        ![](md_graphics/docstrings/plotemg/FLM_set_layout_ex_1.png)
        """

        if despine == "box":
            sns.despine(
                self.figure, top=False, bottom=False, left=False, right=False,
            )
        elif despine == "all":
            sns.despine(
                self.figure, top=True, bottom=True, left=True, right=True,
            )
        elif despine == "2yaxes":
            sns.despine(
                self.figure, top=True, bottom=False, left=False, right=False,
            )
        elif despine == "1yaxis":
            sns.despine(
                self.figure, top=True, bottom=False, left=False, right=True,
            )
        else:
            raise ValueError(
                "despine can be 'box', 'all', '2yaxes' or '1yaxes'. " +
                f"{despine} was passed instead."
            )

        if tight_layout is True:
            self.figure.tight_layout()

    def set_style_from_kwargs(self):
        """
        Set the style of the figure.

        This method updates the main figure with the user-specified custom
        style, or with the standard openhdemg style if no style kwargs have
        been set with emg.Figure_Layout_Manager(figure).get_final_kwargs().

        Examples
        --------
        Plot data in 2 Y axes.

        >>> import openhdemg.library as emg
        >>> import matplotlib.pyplot as plt
        >>> fig, ax1 = plt.subplots()
        >>> ax1.plot([1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1])
        >>> ax2 = ax1.twinx()
        >>> ax2.plot([6, 5, 4, 3, 2, 1, 2, 3, 4, 5, 6])

        Declare custom user plotting kwargs.

        >>> line2d_kwargs_ax1 = {
        ...     "linewidth": 3,
        ...     "alpha": 0.2,
        ...     "marker": "d",
        ...     "markersize": 15,
        ... }
        >>> line2d_kwargs_ax2 = {
        ...     "linewidth": 1,
        ...     "alpha": 0.2,
        ...     "color": "red",
        ... }
        >>> axes_kwargs = {
        ...     "grid": {
        ...         "visible": True,
        ...         "axis": "both",
        ...         "color": "gray",
        ...     },
        ... }

        Merge default and user kwargs.

        >>> fig_manager = emg.Figure_Layout_Manager(figure=fig)
        >>> final_kwargs = fig_manager.get_final_kwargs(
        ...     line2d_kwargs_ax1=line2d_kwargs_ax1,
        ...     line2d_kwargs_ax2=line2d_kwargs_ax2,
        ...     axes_kwargs=axes_kwargs,
        ... )

        Apply the custom style.

        >>> fig_manager.set_style_from_kwargs()

        Show the figure.

        >>> plt.show()

        ![](md_graphics/docstrings/plotemg/FLM_set_style_from_kwargs_ex_1.png)
        """

        # Retrieve axes
        axes = self.figure.get_axes()
        if len(axes) == 0:
            raise ValueError("No figure axes available.")
        elif len(axes) == 1:
            ax1 = axes[0]
            ax2 = None
        elif len(axes) == 2:
            ax1 = axes[0]
            ax2 = axes[1]
        else:
            ax1 = axes[0]
            ax2 = axes[1]
            warnings.warn(
                "The Figure_Layout_Manager can set only the first 2 axes. " +
                f"{len(axes)} axes are present."
            )

        # Set matplotlib.lines.Line2D
        lines1 = ax1.get_lines()
        for key, value in self.final_kwargs[0].items():
            for line in lines1:
                getattr(line, f"set_{key}")(value)
        if ax2 is not None:
            lines2 = ax2.get_lines()
            for key, value in self.final_kwargs[1].items():
                for line in lines2:
                    getattr(line, f"set_{key}")(value)

        # Adjust labels
        ax1.xaxis.labelpad = self.final_kwargs[2]["labels"]["labelpad"]
        xl = ax1.xaxis.get_label()
        if self.final_kwargs[2]["labels"]["xlabel"] is not None:
            xl.set_text(self.final_kwargs[2]["labels"]["xlabel"])
        xl.set_size(self.final_kwargs[2]["labels"]["xlabel_size"])
        xl.set_color(self.final_kwargs[2]["labels"]["xlabel_color"])

        ax1.yaxis.labelpad = self.final_kwargs[2]["labels"]["labelpad"]
        ylsx = ax1.yaxis.get_label()
        if self.final_kwargs[2]["labels"]["ylabel_sx"] is not None:
            ylsx.set_text(self.final_kwargs[2]["labels"]["ylabel_sx"])
        ylsx.set_size(self.final_kwargs[2]["labels"]["ylabel_sx_size"])
        ylsx.set_color(self.final_kwargs[2]["labels"]["ylabel_sx_color"])

        if ax2 is not None:
            ax2.yaxis.labelpad = self.final_kwargs[2]["labels"]["labelpad"]
            yldx = ax2.yaxis.get_label()
            if self.final_kwargs[2]["labels"]["ylabel_dx"] is not None:
                yldx.set_text(self.final_kwargs[2]["labels"]["ylabel_dx"])
            yldx.set_size(self.final_kwargs[2]["labels"]["ylabel_dx_size"])
            yldx.set_color(self.final_kwargs[2]["labels"]["ylabel_dx_color"])

        # Set title
        ax1.set_title(
            self.final_kwargs[2]["labels"]["title"],
            fontsize=self.final_kwargs[2]["labels"]["title_size"],
            color=self.final_kwargs[2]["labels"]["title_color"],
            pad=self.final_kwargs[2]["labels"]["title_pad"],
        )

        # Adjust ticks
        ax1.tick_params(**self.final_kwargs[2]["ticks_ax1"])
        if ax2 is not None:
            ax2.tick_params(**self.final_kwargs[2]["ticks_ax2"])

        # Set grid
        if self.final_kwargs[2]["grid"]["visible"]:
            ax1.grid(**self.final_kwargs[2]["grid"])


class Figure_Subplots_Layout_Manager():
    """
    Class managing custom layout and custom settings for figures with multiple
    2D subplots.

    Parameters
    ----------
    figure : pyplot `~.figure.Figure`
        The matplotlib.pyplot figure to manage.

    Attributes
    ----------
    figure : pyplot `~.figure.Figure`
        The managed matplotlib.pyplot figure.

    Methods
    -------
    set_layout()
        Despine and show plots with a tight layout.
    set_line2d_from_kwargs()
        Set line2d parameters from user kwargs.

    Examples
    --------
    Initialise the Figure_Layout_Manager.

    >>> import openhdemg.library as emg
    >>> import matplotlib.pyplot as plt
    >>> fig, axes = plt.subplots(nrows=5, ncols=5)
    >>> fig_manager = emg.Figure_Subplots_Layout_Manager(figure=fig)
    """

    def __init__(self, figure):
        # Init method that sets default kwargs.

        self.figure = figure

    def set_layout(self, tight_layout=True, despine="box"):
        """
        Despine and show plots with a tight layout.

        This method is called by the various plot functions contained in the
        library but can also be used by the user to quickly adjust the layout
        of custom plots.

        Parameters
        ----------
        tight_layout : bool, default True
            If true, plt.tight_layout() is applied to the figure.
        despined : str {"box", "all", "1yaxis", "2yaxes"}, default "box"

            ``box``
                No side is despined.

            ``all``
                All the sides are despined.

            ``1yaxis``
                Right and top are despined.
                This is used to show the Y axis on the left side.

            ``2yaxes``
                Only the top is despined.
                This is used to show Y axes both on the left and right side at
                the same time.

        Examples
        --------
        Plot sine waves in a 3x3 grid of subplots.

        >>> import openhdemg.library as emg
        >>> import matplotlib.pyplot as plt
        >>> import numpy as np
        >>> fig, axes = plt.subplots(nrows=3, ncols=3)
        >>> x = np.linspace(0, 4 * np.pi, 500)
        >>> base_signal = np.sin(x)
        >>> for row in axes:
        >>>     for ax in row:
        >>>         ax.plot(x, base_signal)
        >>>         ax.set_xticks([])
        >>>         ax.set_yticks([])

        Despine the figure and apply a tight layout.

        >>> fig_manager = emg.Figure_Subplots_Layout_Manager(figure=fig)
        >>> fig_manager.set_layout(tight_layout=True, despine="all")
        >>> plt.show()

        ![](md_graphics/docstrings/plotemg/FSLM_set_layout_ex_1.png)
        """

        if despine == "box":
            sns.despine(
                self.figure, top=False, bottom=False, left=False, right=False,
            )
        elif despine == "all":
            sns.despine(
                self.figure, top=True, bottom=True, left=True, right=True,
            )
        elif despine == "2yaxes":
            sns.despine(
                self.figure, top=True, bottom=False, left=False, right=False,
            )
        elif despine == "1yaxis":
            sns.despine(
                self.figure, top=True, bottom=False, left=False, right=True,
            )
        else:
            raise ValueError(
                "despine can be 'box', 'all', '2yaxes' or '1yaxes'. " +
                f"{despine} was passed instead."
            )

        if tight_layout is True:
            self.figure.tight_layout()

    def set_line2d_from_kwargs(self, line2d_kwargs_ax1=None):
        """
        Set the line2d style of the figure.

        This method updates the main figure with the user-specified custom
        line2d style.

        Parameters
        ----------
        line2d_kwargs_ax1 : dict or list, optional
            User-specified keyword arguments for sets of Line2D objects.
            This can be a list of dictionaries containing the kwargs for each
            Line2D, or a single dictionary. If a single dictionary is passed,
            the same style will be applied to all the lines.

        Notes
        -----
        ``line2d_kwargs_ax1`` can contain any of the matplotlib.lines.Line2D
        parameters as described at:
        (https://matplotlib.org/stable/api/_as_gen/matplotlib.lines.Line2D.html).

        Examples
        --------
        Plot sine waves in a 3x3 grid of subplots with and without noise.

        >>> import openhdemg.library as emg
        >>> import matplotlib.pyplot as plt
        >>> import numpy as np
        >>> fig, axes = plt.subplots(nrows=3, ncols=3)
        >>> x = np.linspace(0, 4 * np.pi, 500)
        >>> base_signal = np.sin(x)
        >>> for row in axes:
        >>>     for ax in row:
        >>>         noisy_signal = base_signal + np.random.normal(
        ...             scale=0.4, size=base_signal.shape,
        ...         )
        >>>         ax.plot(x, noisy_signal)
        >>>         ax.plot(x, base_signal)
        >>>         ax.set_xticks([])
        >>>         ax.set_yticks([])

        Set up the layout manager with custom styling for the 2 line2D
        (relative to the signal with and without noise, respectively).

        >>> line2d_kwargs_ax1 = [
        ...     {
        ...         "color": "tab:red",
        ...         "alpha": 1,
        ...         "linewidth": 0.2,
        ...     },
        ...     {
        ...         "color": "tab:blue",
        ...         "linewidth": 3,
        ...         "alpha": 0.6,
        ...     },
        ... ]
        >>> fig_manager = emg.Figure_Subplots_Layout_Manager(figure=fig)
        >>> fig_manager.set_layout(despine="all")
        >>> fig_manager.set_line2d_from_kwargs(
        ...     line2d_kwargs_ax1=line2d_kwargs_ax1,
        ... )
        >>> plt.show()

        ![](md_graphics/docstrings/plotemg/FSLM_set_line2d_from_kwargs_ex_1.png)
        """

        # Retrieve axes
        axes = self.figure.get_axes()
        if len(axes) == 0:
            raise ValueError("No figure axes available.")

        # Set matplotlib.lines.Line2D
        if isinstance(line2d_kwargs_ax1, list):
            for ax in axes:
                lines1 = ax.get_lines()
                # Check if the number of line kwargs corresponds to the number
                # of lines.
                if len(line2d_kwargs_ax1) != len(lines1):
                    raise ValueError(
                        "The number of line2d_kwargs_ax1 is different from " +
                        "the number of Line2D"
                    )
                else:
                    # Set kwargs
                    for pos, line in enumerate(lines1):
                        for key, value in line2d_kwargs_ax1[pos].items():
                            getattr(line, f"set_{key}")(value)
        else:
            for ax in axes:
                lines1 = ax.get_lines()
                for key, value in line2d_kwargs_ax1.items():
                    for line in lines1:
                        getattr(line, f"set_{key}")(value)


def get_unique_fig_name(base_name):
    """
    Generate a unique figure name if base_name is already in use.

    This allows to plot multiple figures in the background, with the same name,
    before calling plt.show().

    Parameters
    ----------
    base_name : str
        The name to use in the figure.

    Returns
    -------
    new_name : str
        The new, unique name. If base_name is not used in other figures,
        new_name == base_name.
    """

    existing_titles = [
        plt.figure(num).canvas.manager.get_window_title(
        ) for num in plt.get_fignums()
    ]

    if base_name not in existing_titles:
        return base_name  # Name is unique

    # If the name exists, append a number to make it unique
    counter = 1
    new_name = f"{base_name} ({counter})"
    while new_name in existing_titles:
        counter += 1
        new_name = f"{base_name} ({counter})"

    return new_name


def plot_emgsig(
    emgfile,
    channels,
    manual_offset=0,
    addrefsig=False,
    timeinseconds=True,
    figsize=[20, 15],
    tight_layout=True,
    line2d_kwargs_ax1=None,
    line2d_kwargs_ax2=None,
    axes_kwargs=None,
    showimmediately=True,
):
    """
    Plot the RAW_SIGNAL. Single or multiple channels.

    Up to 12 channels (a common matrix row) can be easily observed togheter,
    but more can be plotted.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    channels : int or list
        The channel (int) or channels (list of int) to plot.
        The list can be passed as a manually-written list or with:
        channels=[*range(0, 13)].
        We need the " * " operator to unpack the results of range into a list.
        channels is expected to be with base 0 (i.e., the first channel
        in the file is the number 0).
    manual_offset : int or float, default 0
        This parameter sets the scaling of the channels. If 0 (default), the
        channels' amplitude is scaled automatically to fit the plotting window.
        If > 0, the channels will be scaled based on the specified value.
    addrefsig : bool, default True
        If True, the REF_SIGNAL is plotted in front of the signal with a
        separated y-axes.
    timeinseconds : bool, default True
        Whether to show the time on the x-axes in seconds (True)
        or in samples (False).
    figsize : list, default [20, 15]
        Size of the figure in centimeters [width, height].
    tight_layout : bool, default True
        If True (default), the plt.tight_layout() is called and the figure's
        layout is improved.
        It is useful to set it to False when calling the function from a GUI.
    line2d_kwargs_ax1 : dict, optional
        Kwargs for matplotlib.lines.Line2D relative to figure's axis 1 (the
        EMG signal).
    line2d_kwargs_ax2 : dict, optional
        Kwargs for matplotlib.lines.Line2D relative to figure's axis 2 (the
        reference signal).
    axes_kwargs : dict, optional
        Kwargs for figure's axes.
    showimmediately : bool, default True
        If True (default), plt.show() is called and the figure showed to the
        user.
        It is useful to set it to False when calling the function from a GUI.

    Returns
    -------
    fig : pyplot `~.figure.Figure`

    See also
    --------
    - plot_differentials : plot the differential derivation of the RAW_SIGNAL
        by matrix column.

    Examples
    --------
    Plot channels 0 to 12 and overlay the reference signal.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.emg_from_samplefile()
    >>> emg.plot_emgsig(
    ...     emgfile=emgfile,
    ...     channels=[*range(0,13)],
    ...     addrefsig=True,
    ...     timeinseconds=True,
    ...     figsize=[20, 15],
    ... )

    ![](md_graphics/docstrings/plotemg/plot_emgsig_ex_1.png)

    Plot channels and the reference signal with a custom look.

    >>> import openhdemg.library as emg
    >>> line2d_kwargs_ax1 = {
    ...     "linewidth": 0.2,
    ...     "alpha": 1,
    ... }
    >>> line2d_kwargs_ax2 = {
    ...     "linewidth": 2,
    ...     "color": '0.4',
    ...     "alpha": 1,
    ... }
    >>> axes_kwargs = {
    ...     "grid": {
    ...         "visible": True,
    ...         "axis": "both",
    ...         "color": "gray",
    ...         "linestyle": "--",
    ...         "linewidth": 0.5,
    ...         "alpha": 0.7
    ...     },
    ...     "labels": {
    ...         "xlabel": None,
    ...         "ylabel_sx": "Channels (N°)",
    ...         "ylabel_dx": "MVC (%)",
    ...         "title": "Custom figure title",
    ...         "xlabel_size": 12,
    ...         "xlabel_color": "black",
    ...         "ylabel_sx_size": 12,
    ...         "ylabel_sx_color": "black",
    ...         "ylabel_dx_size": 12,
    ...         "ylabel_dx_color": "black",
    ...         "labelpad": 6,
    ...         "title_size": 12,
    ...         "title_color": "black",
    ...         "title_pad": 14,
    ...     },
    ...     "ticks_ax1": {
    ...         "axis": "both",
    ...         "labelsize": 10,
    ...         "labelrotation": 0,
    ...         "direction": "in",
    ...         "colors": "black",
    ...     },
    ...     "ticks_ax2": {
    ...         "axis": "y",
    ...         "labelsize": 10,
    ...         "labelrotation": 0,
    ...         "direction": "in",
    ...         "colors": "black",
    ...     }
    ... }
    >>> emgfile = emg.emg_from_samplefile()
    >>> fig = emg.plot_emgsig(
    ...     emgfile,
    ...     channels=[*range(0, 3)],
    ...     manual_offset=0,
    ...     addrefsig=True,
    ...     timeinseconds=True,
    ...     tight_layout=True,
    ...     line2d_kwargs_ax1=line2d_kwargs_ax1,
    ...     line2d_kwargs_ax2=line2d_kwargs_ax2,
    ...     axes_kwargs=axes_kwargs,
    ...     showimmediately=True,
    ... )

    ![](md_graphics/docstrings/plotemg/plot_emgsig_ex_2.png)
    """

    # Check to have the RAW_SIGNAL in a pandas dataframe
    if isinstance(emgfile["RAW_SIGNAL"], pd.DataFrame):
        emgsig = emgfile["RAW_SIGNAL"]
    else:
        raise TypeError(
            "RAW_SIGNAL is probably absent or it is not contained in a " +
            "dataframe"
        )

    # Here we produce an x axis in seconds or samples
    if timeinseconds:
        x_axis = emgsig.index / emgfile["FSAMP"]
    else:
        x_axis = emgsig.index

    # Create figure and axis
    figname = get_unique_fig_name("Channels n.{}".format(channels))
    fig, ax1 = plt.subplots(
        figsize=(figsize[0] / 2.54, figsize[1] / 2.54),
        num=figname,
    )

    # Check if we have a single channel or a list of channels to plot
    if isinstance(channels, list) and len(channels) == 1:
        channels = channels[0]

    if isinstance(channels, int):
        ax1.plot(x_axis, emgsig[channels])

        ax1.set_ylabel("Ch {}".format(channels))
        # set_ylabel is useful because if the channel is empty it won't
        # show the channel number
        ax1.set_xlabel("Time (Sec)" if timeinseconds else "Samples")

    # Plot all the channels
    elif isinstance(channels, list) and manual_offset == 0:
        # Normalise the df
        norm_raw_all = min_max_scaling(
                data=emgfile["RAW_SIGNAL"][channels],
                col_by_col=False,
            )

        for count, thisChannel in enumerate(channels):
            norm_raw = norm_raw_all[thisChannel]

            # Add value to the previous channel to avoid overlapping
            norm_raw = norm_raw + (0.5 - norm_raw.mean()) + count
            ax1.plot(x_axis, norm_raw)

        # Ensure correct and complete ticks on the left y axis
        ax1.set_yticks(np.arange(0.5, len(channels) + 0.5, 1))
        ax1.set_yticklabels([str(x) for x in channels])

        # Set axes labels
        ax1.set_ylabel("Channels")
        ax1.set_xlabel("Time (Sec)" if timeinseconds else "Samples")

    elif isinstance(channels, list) and manual_offset > 0:
        # Plot all the channels
        half_offset = manual_offset / 2
        for count, thisChannel in enumerate(channels):
            data = emgfile["RAW_SIGNAL"][thisChannel]

            # Add offset to the previous channel to avoid overlapping
            if count == 0:
                data = data + half_offset
                ax1.plot(x_axis, data)
            else:
                data = data + half_offset + manual_offset * count
                ax1.plot(x_axis, data)

        # Ensure correct and complete ticks on the left y axis
        ax1.set_yticks(
            np.linspace(
                start=half_offset,
                stop=len(channels) * manual_offset + half_offset - manual_offset,
                num=len(channels),
            )
        )
        ax1.set_yticklabels([str(x) for x in channels])

        # Set axes labels
        ax1.set_ylabel("Channels")
        ax1.set_xlabel("Time (Sec)" if timeinseconds else "Samples")

    elif isinstance(channels, list) and manual_offset < 0:
        raise ValueError(
            "When calling the plot_emgsig function, manual_offset must be >= 0"
        )

    else:
        raise TypeError(
            "When calling the plot_emgsig function, you should pass an "
            + "integer or a list to channels"
        )

    # Plot the ref signal
    if addrefsig:
        if not isinstance(emgfile["REF_SIGNAL"], pd.DataFrame):
            raise TypeError(
                "REF_SIGNAL is probably absent or it is not contained in a " +
                "dataframe"
            )

        ax2 = ax1.twinx()
        ax2.plot(x_axis, emgfile["REF_SIGNAL"][0])
        ax2.set_ylabel("MVC")

        # Set z-order so that ax2 is in the background
        ax2.set_zorder(0)
        ax1.set_zorder(1)
        ax1.patch.set_alpha(0)

    # Initialise Figure_Layout_Manager and update default kwarg values with
    # user-specified kwargs.
    fig_manager = Figure_Layout_Manager(figure=fig)
    fig_manager.get_final_kwargs(
        line2d_kwargs_ax1, line2d_kwargs_ax2, axes_kwargs,
    )
    # Adjust labels' size and color, title, ticks and grid
    fig_manager.set_style_from_kwargs()
    # Set appropriate layout
    fig_manager.set_layout(
        tight_layout=tight_layout,
        despine="2yaxes" if addrefsig else "1yaxis",
    )

    # Show the figure
    if showimmediately:
        plt.show()

    return fig


def plot_differentials(
    emgfile,
    differential,
    column="col0",
    manual_offset=0,
    addrefsig=False,
    timeinseconds=True,
    figsize=[20, 15],
    tight_layout=True,
    line2d_kwargs_ax1=None,
    line2d_kwargs_ax2=None,
    axes_kwargs=None,
    showimmediately=True,
):
    """
    Plot the differential derivation of the RAW_SIGNAL by matrix column.

    Both the single and the double differentials can be plotted.
    This function is used to plot also the sorted RAW_SIGNAL.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the original emgfile.
    differential : dict
        The dictionary containing the differential derivation of the
        RAW_SIGNAL.
    column : str {"col0", "col1", "col2", "col3", "col4", ...}, default "col0"
        The matrix column to plot.
        Options are usyally "col0", "col1", "col2", "col3", "col4".
        but might change based on the size of the matrix used.
    manual_offset : int or float, default 0
        This parameter sets the scaling of the channels. If 0 (default), the
        channels' amplitude is scaled automatically to fit the plotting window.
        If > 0, the channels will be scaled based on the specified value.
    addrefsig : bool, default True
        If True, the REF_SIGNAL is plotted in front of the signal with a
        separated y-axes.
    timeinseconds : bool, default True
        Whether to show the time on the x-axes in seconds (True)
        or in samples (False).
    figsize : list, default [20, 15]
        Size of the figure in centimeters [width, height].
    tight_layout : bool, default True
        If True (default), the plt.tight_layout() is called and the figure's
        layout is improved.
        It is useful to set it to False when calling the function from a GUI.
    line2d_kwargs_ax1 : dict, optional
        Kwargs for matplotlib.lines.Line2D relative to figure's axis 1 (the
        EMG signal).
    line2d_kwargs_ax2 : dict, optional
        Kwargs for matplotlib.lines.Line2D relative to figure's axis 2 (the
        reference signal).
    axes_kwargs : dict, optional
        Kwargs for figure's axes.
    showimmediately : bool, default True
        If True (default), plt.show() is called and the figure showed to the
        user.
        It is useful to set it to False when calling the function from a GUI.

    Returns
    -------
    fig : pyplot `~.figure.Figure`

    See also
    --------
    - diff : calculate single differential of RAW_SIGNAL on matrix rows.
    - double_diff : calculate double differential of RAW_SIGNAL on matrix rows.
    - plot_emgsig : pot the RAW_SIGNAL. Single or multiple channels.

    Examples
    --------
    Plot the differential derivation of the second matrix column (col1).

    >>> import openhdemg.library as emg
    >>> emgfile = emg.emg_from_samplefile()
    >>> sorted_rawemg = emg.sort_rawemg(
    ...     emgfile=emgfile,
    ...     code="GR08MM1305",
    ...     orientation=180,
    ... )
    >>> sd=emg.diff(sorted_rawemg=sorted_rawemg)
    >>> emg.plot_differentials(
    ...     emgfile=emgfile,
    ...     differential=sd,
    ...     column="col1",
    ...     addrefsig=False,
    ...     timeinseconds=True,
    ...     figsize=[20, 15],
    ...     showimmediately=True,
    ... )

    ![](md_graphics/docstrings/plotemg/plot_differentials_ex_1.png)

    Plot the double differential derivation of the second matrix column (col1)
    with custom styles (the graph shows a zoomed section).

    >>> import openhdemg.library as emg
    >>> emgfile = emg.emg_from_samplefile()
    >>> sorted_rawemg = emg.sort_rawemg(
    ...     emgfile=emgfile,
    ...     code="GR08MM1305",
    ...     orientation=180,
    ... )
    >>> sd=emg.double_diff(sorted_rawemg=sorted_rawemg)
    >>> line2d_kwargs_ax1 = {"linewidth": 0.5}
    >>> axes_kwargs = {
    ...     "grid": {
    ...         "visible": True,
    ...         "axis": "both",
    ...         "color": "gray",
    ...         "linestyle": "--",
    ...         "linewidth": 0.5,
    ...         "alpha": 0.7
    ...     },
    ... }
    >>> fig = emg.plot_differentials(
    ...     emgfile,
    ...     differential=sd,
    ...     column="col1",
    ...     manual_offset=1000,
    ...     addrefsig=True,
    ...     timeinseconds=True,
    ...     tight_layout=True,
    ...     line2d_kwargs_ax1=line2d_kwargs_ax1,
    ...     axes_kwargs=axes_kwargs,
    ...     showimmediately=True,
    ... )

    ![](md_graphics/docstrings/plotemg/plot_differentials_ex_2.png)

    For further examples on how to customise the figure's layout, refer to
    plot_emgsig().
    """

    # Check to have the signal in a pandas dataframe
    if isinstance(differential[column], pd.DataFrame):
        emgsig = differential[column]
    else:
        raise TypeError(
            "The signal differential[column] is probably absent or it is " +
            "not contained in a dataframe"
        )

    # Here we produce an x axis in seconds or samples
    if timeinseconds:
        x_axis = emgsig.index / emgfile["FSAMP"]
    else:
        x_axis = emgsig.index

    # Create figure and axis
    figname = get_unique_fig_name("Column n.{}".format(column))
    fig, ax1 = plt.subplots(
        figsize=(figsize[0] / 2.54, figsize[1] / 2.54),
        num=figname,
    )

    # Plot all the channels
    if manual_offset == 0:
        # Normalise the df
        norm_raw_all = min_max_scaling(emgsig, col_by_col=False)

        for count, thisChannel in enumerate(emgsig.columns):
            norm_raw = norm_raw_all[thisChannel]

            # Add value to the previous channel to avoid overlapping
            norm_raw = norm_raw + (0.5 - norm_raw.mean()) + count
            ax1.plot(x_axis, norm_raw)

        # Ensure correct and complete ticks on the left y axis
        ax1.set_yticks(np.arange(0.5, len(emgsig.columns) + 0.5, 1))
        ax1.set_yticklabels([str(x) for x in emgsig.columns])

        # Set axes labels
        ax1.set_ylabel("Channels")
        ax1.set_xlabel("Time (Sec)" if timeinseconds else "Samples")

    elif manual_offset > 0:
        half_offset = manual_offset / 2
        for count, thisChannel in enumerate(emgsig.columns):
            data = emgsig[thisChannel]

            # Add offset to the previous channel to avoid overlapping
            if count == 0:
                data = data + half_offset
                ax1.plot(x_axis, data)
            else:
                data = data + half_offset + manual_offset * count
                ax1.plot(x_axis, data)

        # Ensure correct and complete ticks on the left y axis
        """ ax1.set_yticks(
            np.arange(
                half_offset,
                len(emgsig.columns) * manual_offset + half_offset,
                manual_offset,
            )
        ) """
        ax1.set_yticks(
            np.linspace(
                start=half_offset,
                stop=len(emgsig.columns) * manual_offset + half_offset - manual_offset,
                num=len(emgsig.columns),
            )
        )
        ax1.set_yticklabels([str(x) for x in emgsig.columns])

        # Set axes labels
        ax1.set_ylabel("Channels")
        ax1.set_xlabel("Time (Sec)" if timeinseconds else "Samples")

    else:
        raise ValueError(
            "When calling the plot_differentials function, manual_offset " +
            "must be >= 0"
        )

    # Plot the ref signal
    if addrefsig:
        if not isinstance(emgfile["REF_SIGNAL"], pd.DataFrame):
            raise TypeError(
                "REF_SIGNAL is probably absent or it is not contained in a " +
                "dataframe"
            )

        ax2 = ax1.twinx()
        ax2.plot(x_axis, emgfile["REF_SIGNAL"][0])
        ax2.set_ylabel("MVC")

        # Set z-order so that ax2 is in the background
        ax2.set_zorder(0)
        ax1.set_zorder(1)
        ax1.patch.set_alpha(0)

    # Initialise Figure_Layout_Manager and update default kwarg values with
    # user-specified kwargs.
    fig_manager = Figure_Layout_Manager(figure=fig)
    fig_manager.get_final_kwargs(
        line2d_kwargs_ax1, line2d_kwargs_ax2, axes_kwargs,
    )
    # Adjust labels' size and color, title, ticks and grid
    fig_manager.set_style_from_kwargs()
    # Set appropriate layout
    fig_manager.set_layout(
        tight_layout=tight_layout,
        despine="2yaxes" if addrefsig else "1yaxis",
    )

    if showimmediately:
        plt.show()

    return fig


def plot_refsig(
    emgfile,
    ylabel="",
    timeinseconds=True,
    figsize=[20, 15],
    tight_layout=True,
    line2d_kwargs_ax1=None,
    axes_kwargs=None,
    showimmediately=True,
):
    """
    Plot the REF_SIGNAL.

    The REF_SIGNAL is usually expressed as % MVC for submaximal contractions
    or as Kilograms (Kg) or Newtons (N) for maximal contractions, but any
    value can be plotted.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    ylabel : str
        WARNING! This parameter is deprecated since v0.1.1 and will be removed
        after v0.2.0. Please use axes_kwargs instead. See examples in the
        plot_refsig documentation.
    timeinseconds : bool, default True
        Whether to show the time on the x-axes in seconds (True)
        or in samples (False).
    figsize : list, default [20, 15]
        Size of the figure in centimeters [width, height].
    tight_layout : bool, default True
        If True (default), the plt.tight_layout() is called and the figure's
        layout is improved.
        It is useful to set it to False when calling the function from a GUI.
    line2d_kwargs_ax1 : dict, optional
        Kwargs for matplotlib.lines.Line2D relative to figure's axis 1 (the
        reference signal).
    axes_kwargs : dict, optional
        Kwargs for figure's axes.
    showimmediately : bool, default True
        If True (default), plt.show() is called and the figure showed to the
        user.
        It is useful to set it to False when calling the function from a GUI.

    Returns
    -------
    fig : pyplot `~.figure.Figure`

    Examples
    --------
    Plot the reference signal.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.emg_from_samplefile()
    >>> emg.plot_refsig(emgfile=emgfile)

    ![](md_graphics/docstrings/plotemg/plot_refsig_ex_1.png)

    Plot the reference signal with custom labels and style.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.emg_from_samplefile()
    >>> line2d_kwargs_ax1 = {"linewidth": 1}
    >>> axes_kwargs = {
    ...     "grid": {
    ...         "visible": True,
    ...         "axis": "both",
    ...         "color": "red",
    ...         "linestyle": "--",
    ...         "linewidth": 0.3,
    ...         "alpha": 0.7
    ...     },
    ...     "labels": {
    ...         "ylabel_sx": "MVC (%)",
    ...         "title": "Custom figure title",
    ...     },
    ... }
    >>> fig = emg.plot_refsig(
    ...     emgfile,
    ...     timeinseconds=True,
    ...     tight_layout=True,
    ...     line2d_kwargs_ax1=line2d_kwargs_ax1,
    ...     axes_kwargs=axes_kwargs,
    ...     showimmediately=True,
    ... )

    ![](md_graphics/docstrings/plotemg/plot_refsig_ex_2.png)
    """

    # Warn for the use of a deprecated parameter
    if len(ylabel) > 0:
        msg = (
            "The ylabel parameter is deprecated since v0.1.1 and will be " +
            "removed after v0.2.0. Please use axes_kwargs instead. " +
            "See examples in the plot_refsig documentation."
        )
        warnings.warn(msg, DeprecationWarning, stacklevel=2)

    # Check to have the REF_SIGNAL in a pandas dataframe
    if isinstance(emgfile["REF_SIGNAL"], pd.DataFrame):
        refsig = emgfile["REF_SIGNAL"]
    else:
        raise TypeError(
            "REF_SIGNAL is probably absent or it is not contained in a " +
            "dataframe"
        )

    # Here we produce an x axis in seconds or samples
    if timeinseconds:
        x_axis = refsig.index / emgfile["FSAMP"]
    else:
        x_axis = refsig.index

    figname = get_unique_fig_name("Reference signal")
    fig, ax1 = plt.subplots(
        figsize=(figsize[0] / 2.54, figsize[1] / 2.54),
        num=figname,
    )

    ax1.plot(x_axis, refsig[0])

    ax1.set_ylabel("MVC")
    ax1.set_xlabel("Time (Sec)" if timeinseconds else "Samples")

    # Initialise Figure_Layout_Manager and update default kwarg values with
    # user-specified kwargs.
    fig_manager = Figure_Layout_Manager(figure=fig)
    fig_manager.get_final_kwargs(
        line2d_kwargs_ax1, {}, axes_kwargs,
    )
    # Adjust labels' size and color, title, ticks and grid
    fig_manager.set_style_from_kwargs()
    # Set appropriate layout
    fig_manager.set_layout(tight_layout=tight_layout, despine="1yaxis")

    if showimmediately:
        plt.show()

    return fig


def plot_mupulses(
    emgfile,
    munumber="all",
    linewidths=0,
    linelengths=0.9,
    addrefsig=True,
    timeinseconds=True,
    figsize=[20, 15],
    tight_layout=True,
    line2d_kwargs_ax1=None,
    line2d_kwargs_ax2=None,
    axes_kwargs=None,
    showimmediately=True,
):
    """
    Plot the MUPULSES (binary representation of the firings time).

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    munumber : str, int or list, default "all"

        ``all``
            IPTS of all the MUs is plotted.

        Otherwise, a single MU (int) or multiple MUs (list of int) can be
        specified.
        The list can be passed as a manually-written list or with:
        munumber=[*range(0, n)].
        We need the " * " operator to unpack the results of range into a list.
        munumber is expected to be with base 0 (i.e., the first MU in the file
        is the number 0).
    linewidths : float
        WARNING! This parameter is deprecated since v0.1.1 and will be removed
        after v0.2.0. Please use line2d_kwargs_ax1 instead. See examples in the
        plot_mupulses documentation.
    linelengths : float, default 0.9
        The vertical length of each line. This must be a value between 0 and 1.
    addrefsig : bool, default True
        If True, the REF_SIGNAL is plotted in front of the MUs pulses with a
        separated y-axes.
    timeinseconds : bool, default True
        Whether to show the time on the x-axes in seconds (True)
        or in samples (False).
    figsize : list, default [20, 15]
        Size of the figure in centimeters [width, height].
    tight_layout : bool, default True
        If True (default), the plt.tight_layout() is called and the figure's
        layout is improved.
        It is useful to set it to False when calling the function from a GUI.
    line2d_kwargs_ax1 : dict, optional
        Kwargs for matplotlib.lines.Line2D relative to figure's axis 1 (the
        MUPULSES).
    line2d_kwargs_ax2 : dict, optional
        Kwargs for matplotlib.lines.Line2D relative to figure's axis 2 (the
        reference signal).
    axes_kwargs : dict, optional
        Kwargs for figure's axes.
    showimmediately : bool, default True
        If True (default), plt.show() is called and the figure showed to the
        user.
        It is useful to set it to False when calling the function from a GUI.

    Returns
    -------
    fig : pyplot `~.figure.Figure`

    See also
    --------
    - plot_ipts : plot the MUs impulse train per second (IPTS).
    - plot_idr : plot the instantaneous discharge rate.

    Examples
    --------
    Plot MUs pulses based on recruitment order and overlay the reference
    signal.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.emg_from_samplefile()
    >>> emgfile = emg.sort_mus(emgfile)
    >>> emg.plot_mupulses(
    ...     emgfile=emgfile,
    ...     addrefsig=True,
    ...     timeinseconds=True,
    ...     figsize=[20, 15],
    ...     showimmediately=True,
    ... )

    ![](md_graphics/docstrings/plotemg/plot_mupulses_ex_1.png)

    Plot MUs pulses based on recruitment order and adjust lines width, color
    and length.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.emg_from_samplefile()
    >>> emgfile = emg.sort_mus(emgfile)
    >>> line2d_kwargs_ax1 = {
    ...     "linewidth": 0.7,
    ...     "color": "0.1",
    ...     "alpha": 0.4,
    ... }
    >>> fig = emg.plot_mupulses(
    ...     emgfile,
    ...     munumber="all",
    ...     linelengths=0.7,
    ...     addrefsig=True,
    ...     timeinseconds=True,
    ...     tight_layout=True,
    ...     line2d_kwargs_ax1=line2d_kwargs_ax1,
    ...     showimmediately=True,
    ... )

    ![](md_graphics/docstrings/plotemg/plot_mupulses_ex_2.png)

    For further examples on how to customise the figure's layout, refer to
    plot_emgsig().
    """

    # Warn for the use of a deprecated parameter
    if linewidths > 0:
        msg = (
            "The linewidths parameter is deprecated since v0.1.1 and will " +
            "be removed after v0.2.0. Please use line2d_kwargs_ax1 instead. " +
            "See examples in the plot_mupulses documentation."
        )
        warnings.warn(msg, DeprecationWarning, stacklevel=2)

    # Check to have the correct input
    if isinstance(emgfile["MUPULSES"], list):
        mupulses = emgfile["MUPULSES"]
    else:
        raise TypeError(
            "MUPULSES is probably absent or it is not contained in a np.array"
        )

    # Check linelengths value
    if linelengths < 0 or linelengths > 1:
        raise ValueError(
            "linelengths must be a number between 0 and 1."
        )

    # Check if all the MUs have to be plotted and create the y labels
    if isinstance(munumber, str):
        # Manage exception of single MU
        if emgfile["NUMBER_OF_MUS"] > 1:
            y_tick_lab = [*range(0, emgfile["NUMBER_OF_MUS"])]
            ylab = "Motor units"
        else:
            munumber = 0

    elif isinstance(munumber, int):
        mupulses = [mupulses[munumber]]
        y_tick_lab = []
        ylab = f"MU n. {munumber}"
    elif isinstance(munumber, list):
        if len(munumber) > 1:
            mupulses = [mupulses[mu] for mu in munumber]
            y_tick_lab = munumber
            ylab = "Motor units"
        else:
            mupulses = [mupulses[munumber[0]]]
            y_tick_lab = []
            ylab = f"MU n. {munumber[0]}"
    else:
        raise TypeError(
            "While calling the plot_mupulses function, you should pass an " +
            "integer, a list or 'all' to munumber"
        )

    # Convert x axes in seconds if timeinseconds==True.
    # This has to be done both for the REF_SIGNAL and the mupulses, for the
    # MUPULSES we need to convert the point of firing from samples to seconds.
    if timeinseconds:
        mupulses = [n / emgfile["FSAMP"] for n in mupulses]
        x_axis = emgfile["RAW_SIGNAL"].index / emgfile["FSAMP"]
    else:
        x_axis = emgfile["RAW_SIGNAL"].index

    # Create colors list for the firings and plot them
    colors1 = ["C{}".format(i) for i in range(len(mupulses))]

    # Use the subplot to allow the use of twinx
    figname = get_unique_fig_name("MUs pulses")
    fig, ax1 = plt.subplots(
        figsize=(figsize[0] / 2.54, figsize[1] / 2.54), num=figname,
    )

    # Plot the MUPULSES.
    # Iterate over each row and plot events manually to allow the use of
    # the Figure_Layout_Manager.
    for i, (events, color) in enumerate(zip(mupulses, colors1)):
        # The `y` position for this row (increasing by 1 for each new row)
        delta = (1-linelengths) / 2
        y_pos = i
        # Draw each event as a vertical line
        for event in events:
            ax1.plot(
                [event, event],
                [y_pos + delta, y_pos + delta + linelengths],
                color=color, linewidth=0.5,
            )

    # Ensure correct and complete ticks on the left y axis
    ax1.set_yticks(np.arange(0.5, len(mupulses) + 0.5, 1))
    ax1.set_yticklabels([str(mu) for mu in y_tick_lab])
    # Set axes labels
    ax1.set_ylabel(ylab)
    ax1.set_xlabel("Time (Sec)" if timeinseconds else "Samples")

    if addrefsig:
        if not isinstance(emgfile["REF_SIGNAL"], pd.DataFrame):
            raise TypeError(
                "REF_SIGNAL is probably absent or it is not contained in a " +
                "dataframe"
            )
        ax2 = ax1.twinx()
        ax2.plot(x_axis, emgfile["REF_SIGNAL"][0])
        ax2.set_ylabel("MVC")

        # Set z-order so that ax2 is in the background
        ax2.set_zorder(0)
        ax1.set_zorder(1)
        ax1.patch.set_alpha(0)

    # Initialise Figure_Layout_Manager and update default kwarg values with
    # user-specified kwargs.
    fig_manager = Figure_Layout_Manager(figure=fig)
    fig_manager.get_final_kwargs(
        line2d_kwargs_ax1, line2d_kwargs_ax2, axes_kwargs,
    )
    # Adjust labels' size and color, title, ticks and grid
    fig_manager.set_style_from_kwargs()
    # Set appropriate layout
    fig_manager.set_layout(
        tight_layout=tight_layout,
        despine="2yaxes" if addrefsig else "1yaxis",
    )

    if showimmediately:
        plt.show()

    return fig


def plot_ipts(
    emgfile,
    munumber="all",
    addrefsig=False,
    timeinseconds=True,
    figsize=[20, 15],
    tight_layout=True,
    line2d_kwargs_ax1=None,
    line2d_kwargs_ax2=None,
    axes_kwargs=None,
    showimmediately=True,
):
    """
    Plot the IPTS (decomposed source).

    IPTS is the non-binary representation of the MUs firing times.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    munumber : str, int or list, default "all"

        ``all``
            IPTS of all the MUs is plotted.

        Otherwise, a single MU (int) or multiple MUs (list of int) can be
        specified.
        The list can be passed as a manually-written list or with:
        munumber=[*range(0, 12)].
        We need the " * " operator to unpack the results of range into a list.
        munumber is expected to be with base 0 (i.e., the first MU in the file
        is the number 0).
    addrefsig : bool, default True
        If True, the REF_SIGNAL is plotted in front of the signal with a
        separated y-axes.
    timeinseconds : bool, default True
        Whether to show the time on the x-axes in seconds (True) or in
        samples (False).
    figsize : list, default [20, 15]
        Size of the figure in centimeters [width, height].
    tight_layout : bool, default True
        If True (default), the plt.tight_layout() is called and the figure's
        layout is improved.
        It is useful to set it to False when calling the function from a GUI.
    line2d_kwargs_ax1 : dict, optional
        Kwargs for matplotlib.lines.Line2D relative to figure's axis 1 (the
        IPTS).
    line2d_kwargs_ax2 : dict, optional
        Kwargs for matplotlib.lines.Line2D relative to figure's axis 2 (the
        reference signal).
    axes_kwargs : dict, optional
        Kwargs for figure's axes.
    showimmediately : bool, default True
        If True (default), plt.show() is called and the figure showed to the
        user.
        It is useful to set it to False when calling the function from a GUI.

    Returns
    -------
    fig : pyplot `~.figure.Figure`

    See also
    --------
    - plot_mupulses : plot the binary representation of the firings.
    - plot_idr : plot the instantaneous discharge rate.

    Notes
    -----
    munumber = "all" corresponds to:
    munumber = [*range(0, emgfile["NUMBER_OF_MUS"])]

    Examples
    --------
    Plot IPTS of all the MUs and overlay the reference signal.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.emg_from_samplefile()
    >>> emg.plot_ipts(
    ...     emgfile=emgfile,
    ...     munumber="all",
    ...     addrefsig=True,
    ...     timeinseconds=True,
    ...     figsize=[20, 15],
    ...     showimmediately=True,
    ... )

    ![](md_graphics/docstrings/plotemg/plot_ipts_ex_1.png)

    Plot IPTS of two MUs.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.emg_from_samplefile()
    >>> emg.plot_ipts(
    ...     emgfile=emgfile,
    ...     munumber=[1, 3],
    ...     addrefsig=False,
    ...     timeinseconds=True,
    ...     figsize=[20, 15],
    ...     showimmediately=True,
    ... )

    ![](md_graphics/docstrings/plotemg/plot_ipts_ex_2.png)

    Plot IPTS of all the MUs, the reference signal, smaller lines and a
    background grid.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.emg_from_samplefile()
    >>> line2d_kwargs_ax1 = {"linewidth": 0.5}
    >>> axes_kwargs = {
    ...     "grid": {
    ...         "visible": True,
    ...         "axis": "both",
    ...         "color": "gray",
    ...         "linestyle": "--",
    ...         "linewidth": 1,
    ...         "alpha": 0.7
    ...     },
    ... }
    >>> fig = emg.plot_ipts(
    ...     emgfile,
    ...     munumber="all",
    ...     addrefsig=True,
    ...     timeinseconds=True,
    ...     tight_layout=True,
    ...     axes_kwargs=axes_kwargs,
    ...     showimmediately=True,
    ... )

    ![](md_graphics/docstrings/plotemg/plot_ipts_ex_3.png)

    For additional examples on how to customise the figure's layout, refer to
    plot_emgsig().
    """

    # Check if all the MUs have to be plotted
    if isinstance(munumber, str):
        if emgfile["NUMBER_OF_MUS"] == 1:  # Manage exception of single MU
            munumber = 0
        else:
            munumber = [*range(0, emgfile["NUMBER_OF_MUS"])]

    # Check if we have a single mu or a list of mus to plot
    if isinstance(munumber, list) and len(munumber) == 1:
        munumber = munumber[0]

    # Check to have the IPTS in a pandas dataframe
    if isinstance(emgfile["IPTS"], pd.DataFrame):
        ipts = emgfile["IPTS"]
    else:
        raise TypeError(
            "IPTS is probably absent or it is not contained in a dataframe"
        )

    # Here we produce an x axis in seconds or samples
    if timeinseconds:
        x_axis = ipts.index / emgfile["FSAMP"]
    else:
        x_axis = ipts.index

    # Use the subplot function to allow for the use of twinx()
    figname = get_unique_fig_name("IPTS")
    fig, ax1 = plt.subplots(
        figsize=(figsize[0] / 2.54, figsize[1] / 2.54), num=figname,
    )

    # Check if we have a single MU or a list of MUs to plot
    if isinstance(munumber, int):
        ax1.plot(x_axis, ipts[munumber])

        ax1.set_ylabel("MU {}".format(munumber))
        # Use set_ylabel because if the MU is empty,
        # the channel number won't show.
        ax1.set_xlabel("Time (Sec)" if timeinseconds else "Samples")

    elif isinstance(munumber, list):
        # Plot all the MUs.
        for count, thisMU in enumerate(munumber):
            norm_ipts = min_max_scaling(
                ipts[thisMU], col_by_col=False,
            )

            # Add value to the previous channel to avoid overlapping
            norm_ipts = norm_ipts + (0.5 - norm_ipts.mean()) + count
            ax1.plot(x_axis, norm_ipts)

        # Ensure correct and complete ticks on the left y axis
        ax1.set_yticks(np.arange(0.5, len(munumber) + 0.5, 1))
        ax1.set_yticklabels([str(x) for x in munumber])

        # Set axes labels
        ax1.set_ylabel("Motor units")
        ax1.set_xlabel("Time (Sec)" if timeinseconds else "Samples")

    else:
        raise TypeError(
            "While calling the plot_ipts function, you should pass an " +
            "integer, a list or 'all' to munumber"
        )

    # Plot the ref signal
    if addrefsig:
        if not isinstance(emgfile["REF_SIGNAL"], pd.DataFrame):
            raise TypeError(
                "REF_SIGNAL is probably absent or it is not contained in a " +
                "dataframe"
            )

        ax2 = ax1.twinx()
        ax2.plot(x_axis, emgfile["REF_SIGNAL"][0])
        ax2.set_ylabel("MVC")

        # Set z-order so that ax2 is in the background
        ax2.set_zorder(0)
        ax1.set_zorder(1)
        ax1.patch.set_alpha(0)

    # Initialise Figure_Layout_Manager and update default kwarg values with
    # user-specified kwargs.
    fig_manager = Figure_Layout_Manager(figure=fig)
    fig_manager.get_final_kwargs(
        line2d_kwargs_ax1, line2d_kwargs_ax2, axes_kwargs,
    )
    # Adjust labels' size and color, title, ticks and grid
    fig_manager.set_style_from_kwargs()
    # Set appropriate layout
    fig_manager.set_layout(
        tight_layout=tight_layout,
        despine="2yaxes" if addrefsig else "1yaxis",
    )

    # Show the figure
    if showimmediately:
        plt.show()

    return fig


def plot_idr(
    emgfile,
    munumber="all",
    addrefsig=True,
    timeinseconds=True,
    figsize=[20, 15],
    tight_layout=True,
    line2d_kwargs_ax1=None,
    line2d_kwargs_ax2=None,
    axes_kwargs=None,
    showimmediately=True,
):
    """
    Plot the instantaneous discharge rate (IDR).

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    munumber : str, int or list, default "all"

        ``all``
            IDR of all the MUs is plotted.

        Otherwise, a single MU (int) or multiple MUs (list of int) can be
        specified.
        The list can be passed as a manually-written list or with:
        munumber=[*range(0, 12)].
        We need the " * " operator to unpack the results of range into a list.
        munumber is expected to be with base 0 (i.e., the first MU in the file
        is the number 0).
    addrefsig : bool, default True
        If True, the REF_SIGNAL is plotted in front of the MUs IDR with a
        separated y-axes.
    timeinseconds : bool, default True
        Whether to show the time on the x-axes in seconds (True)
        or in samples (False).
    figsize : list, default [20, 15]
        Size of the figure in centimeters [width, height].
    tight_layout : bool, default True
        If True (default), the plt.tight_layout() is called and the figure's
        layout is improved.
        It is useful to set it to False when calling the function from a GUI.
    line2d_kwargs_ax1 : dict, optional
        Kwargs for matplotlib.lines.Line2D relative to figure's axis 1 (the
        IDR).
    line2d_kwargs_ax2 : dict, optional
        Kwargs for matplotlib.lines.Line2D relative to figure's axis 2 (the
        reference signal).
    axes_kwargs : dict, optional
        Kwargs for figure's axes.
    showimmediately : bool, default True
        If True (default), plt.show() is called and the figure showed to the
        user.
        It is useful to set it to False when calling the function from a GUI.

    Returns
    -------
    fig : pyplot `~.figure.Figure`

    See also
    --------
    - plot_mupulses : plot the binary representation of the firings.
    - plot_ipts : plot the impulse train per second (IPTS).

    Notes
    -----
    munumber = "all" corresponds to
    munumber = [*range(0, emgfile["NUMBER_OF_MUS"])]

    Examples
    --------
    Plot IDR of all the MUs and overlay the reference signal.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.emg_from_samplefile()
    >>> emg.plot_idr(
    ...     emgfile=emgfile,
    ...     munumber="all",
    ...     addrefsig=True,
    ...     timeinseconds=True,
    ...     figsize=[20, 15],
    ...     showimmediately=True,
    ... )

    ![](md_graphics/docstrings/plotemg/plot_idr_ex_1.png)

    Plot IDR of two MUs.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.emg_from_samplefile()
    >>> emg.plot_idr(
    ...     emgfile=emgfile,
    ...     munumber=[1, 3],
    ...     addrefsig=False,
    ...     timeinseconds=True,
    ...     figsize=[20, 15],
    ...     showimmediately=True,
    ... )

    ![](md_graphics/docstrings/plotemg/plot_idr_ex_2.png)

    Plot IDR and use custom markers.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.emg_from_samplefile()
    >>> line2d_kwargs_ax1 = {
    ...     "marker": "D",
    ...     "markersize": 6,
    ...     "markeredgecolor": "tab:blue",
    ...     "markeredgewidth": "2",
    ...     "fillstyle": "none",
    ...     "alpha": 0.6,
    ... }
    >>> fig = emg.plot_idr(
    ...     emgfile,
    ...     munumber=[1, 3, 4],
    ...     addrefsig=True,
    ...     timeinseconds=False,
    ...     tight_layout=True,
    ...     line2d_kwargs_ax1=line2d_kwargs_ax1,
    ...     showimmediately=True,
    ... )

    ![](md_graphics/docstrings/plotemg/plot_idr_ex_3.png)

    For additional examples on how to customise the figure's layout, refer to
    plot_emgsig().
    """

    # Compute the IDR
    idr = compute_idr(emgfile=emgfile)

    # Check if all the MUs have to be plotted
    if isinstance(munumber, str):
        if emgfile["NUMBER_OF_MUS"] == 1:  # Manage exception of single MU
            munumber = 0
        else:
            munumber = [*range(0, emgfile["NUMBER_OF_MUS"])]

    # Check if we have a single mu or a list of mus to plot
    if isinstance(munumber, list) and len(munumber) == 1:
        munumber = munumber[0]

    # Use the subplot function to allow for the use of twinx()
    figname = get_unique_fig_name("IDR")
    fig, ax1 = plt.subplots(
        figsize=(figsize[0] / 2.54, figsize[1] / 2.54), num=figname,
    )

    # Check if we have a single MU or a list of MUs to plot.
    if isinstance(munumber, int):
        ax1.plot(
            idr[munumber]["timesec" if timeinseconds else "mupulses"],
            idr[munumber]["idr"],
            ".", markersize=12,
        )

        ax1.set_ylabel("MU {} (pps)".format(munumber))
        # Useful because if the MU is empty it won't show the channel number
        ax1.set_xlabel("Time (Sec)" if timeinseconds else "Samples")

    elif isinstance(munumber, list):
        # Extract the 'idr' column from each df and create a new df of idrs
        idr_all = pd.DataFrame({key: df['idr'] for key, df in idr.items()})
        idr_all = idr_all[munumber]
        # Normalise the df
        norm_idr_all = min_max_scaling(data=idr_all, col_by_col=False)

        for count, thisMU in enumerate(munumber):
            norm_idr = norm_idr_all[thisMU]

            # Add value to the previous mu to avoid overlapping
            if norm_idr.mean() <= 0.5:
                norm_idr = norm_idr + (0.5 - norm_idr.mean()) + count
            else:
                norm_idr = norm_idr - (norm_idr.mean() - 0.5) + count

            ax1.plot(
                # Ignore first nan with [1:]
                idr[thisMU]["timesec" if timeinseconds else "mupulses"][1:],
                norm_idr.dropna(),
                ".", markersize=8,
            )

        # Ensure correct and complete ticks on the left y axis
        ax1.set_yticks(np.arange(0.5, len(munumber) + 0.5, 1))
        ax1.set_yticklabels([str(mu) for mu in munumber])

        # Set axes labels
        ax1.set_ylabel("Motor units")
        ax1.set_xlabel("Time (Sec)" if timeinseconds else "Samples")

    else:
        raise TypeError(
            "While calling the plot_idr function, you should pass an " +
            "integer, a list or 'all' to munumber"
        )

    # Plot the ref signal
    if addrefsig:
        if not isinstance(emgfile["REF_SIGNAL"], pd.DataFrame):
            raise TypeError(
                "REF_SIGNAL is probably absent or it is not contained in a " +
                "dataframe"
            )

        x_axis = (
            emgfile["REF_SIGNAL"].index / emgfile["FSAMP"]
            if timeinseconds
            else emgfile["REF_SIGNAL"].index
        )
        ax2 = ax1.twinx()
        ax2.plot(x_axis, emgfile["REF_SIGNAL"][0])
        ax2.set_ylabel("MVC")

        # Set z-order so that ax2 is in the background
        ax2.set_zorder(0)
        ax1.set_zorder(1)
        ax1.patch.set_alpha(0)

    # Initialise Figure_Layout_Manager and update default kwarg values with
    # user-specified kwargs.
    fig_manager = Figure_Layout_Manager(figure=fig)
    fig_manager.get_final_kwargs(
        line2d_kwargs_ax1, line2d_kwargs_ax2, axes_kwargs,
    )
    # Adjust labels' size and color, title, ticks and grid
    fig_manager.set_style_from_kwargs()
    # Set appropriate layout
    fig_manager.set_layout(
        tight_layout=tight_layout,
        despine="2yaxes" if addrefsig else "1yaxis",
    )

    # Show the figure
    if showimmediately:
        plt.show()

    return fig


def plot_smoothed_dr(
    emgfile,
    smoothfits,
    munumber="all",
    addidr=True,
    stack=True,
    addrefsig=True,
    timeinseconds=True,
    figsize=[20, 15],
    tight_layout=True,
    line2d_kwargs_ax1=None,
    line2d_kwargs_ax2=None,
    axes_kwargs=None,
    showimmediately=True,
):
    """
    Plot the smoothed discharge rate.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    smoothfits : pd.DataFrame
        Smoothed discharge rate estimates aligned in time. Columns should
        contain the smoothed discharge rate for each MU.
    munumber : str, int or list, default "all"

        ``all``
            IDR of all the MUs is plotted.

        Otherwise, a single MU (int) or multiple MUs (list of int) can be
        specified.
        The list can be passed as a manually-written list or with:
        munumber=[*range(0, 12)].
        We need the " * " operator to unpack the results of range into a list.
        munumber is expected to be with base 0 (i.e., the first MU in the file
        is the number 0).
    addidr : bool, default True
        Whether to show also the IDR behind the smoothed DR line.
    stack : bool, default True
        Whether to stack multiple MUs. If False, all the MUs smoothed DR will
        be plotted on the same line.
    addrefsig : bool, default True
        If True, the REF_SIGNAL is plotted in front of the MUs IDR with a
        separated y-axes.
    timeinseconds : bool, default True
        Whether to show the time on the x-axes in seconds (True)
        or in samples (False).
    figsize : list, default [20, 15]
        Size of the figure in centimeters [width, height].
    tight_layout : bool, default True
        If True (default), the plt.tight_layout() is called and the figure's
        layout is improved.
        It is useful to set it to False when calling the function from a GUI.
    line2d_kwargs_ax1 : dict, optional
        Kwargs for matplotlib.lines.Line2D relative to figure's axis 1 (in
        this case, smoothfits and idr).
    line2d_kwargs_ax2 : dict, optional
        Kwargs for matplotlib.lines.Line2D relative to figure's axis 2 (the
        reference signal).
    axes_kwargs : dict, optional
        Kwargs for figure's axes.
    showimmediately : bool, default True
        If True (default), plt.show() is called and the figure showed to the
        user.
        It is useful to set it to False when calling the function from a GUI.

    Returns
    -------
    fig : pyplot `~.figure.Figure`

    See also
    --------
    - compute_svr : Fit MU discharge rates with Support Vector Regression,
        nonlinear regression.

    Notes
    -----
    munumber = "all" corresponds to:
    munumber = [*range(0, emgfile["NUMBER_OF_MUS"])]

    Examples
    --------
    Smooth MUs DR using Support Vector Regression. Plot the smoothed DR of
    some MUs and overlay the IDR and the reference signal.

    >>> import openhdemg.library as emg
    >>> import pandas as pd
    >>> emgfile = emg.emg_from_samplefile()
    >>> emgfile = emg.sort_mus(emgfile=emgfile)
    >>> svrfits = emg.compute_svr(emgfile)
    >>> smoothfits = pd.DataFrame(svrfits["gensvr"]).transpose()
    >>> fig = emg.plot_smoothed_dr(
    ...     emgfile,
    ...     smoothfits=smoothfits,
    ...     munumber=[0, 1, 3, 4],
    ...     addidr=True,
    ...     stack=False,
    ...     addrefsig=True,
    ... )

    ![](md_graphics/docstrings/plotemg/plot_smoothed_dr_ex_1.png)

    Stack the MUs and change line width.

    >>> import openhdemg.library as emg
    >>> import pandas as pd
    >>> emgfile = emg.emg_from_samplefile()
    >>> emgfile = emg.sort_mus(emgfile=emgfile)
    >>> svrfits = emg.compute_svr(emgfile)
    >>> smoothfits = pd.DataFrame(svrfits["gensvr"]).transpose()
    >>> line2d_kwargs_ax1 = {
    ...     "linewidth": 3,
    ... }
    >>> fig = emg.plot_smoothed_dr(
    ...     emgfile,
    ...     smoothfits=smoothfits,
    ...     munumber=[0, 1, 3, 4],
    ...     addidr=True,
    ...     stack=True,
    ...     addrefsig=True,
    ...     line2d_kwargs_ax1=line2d_kwargs_ax1,
    ... )

    ![](md_graphics/docstrings/plotemg/plot_smoothed_dr_ex_2.png)

    Plot in black and white.

    >>> import openhdemg.library as emg
    >>> import pandas as pd
    >>> emgfile = emg.emg_from_samplefile()
    >>> emgfile = emg.sort_mus(emgfile=emgfile)
    >>> svrfits = emg.compute_svr(emgfile)
    >>> smoothfits = pd.DataFrame(svrfits["gensvr"]).transpose()
    >>> line2d_kwargs_ax1 = {
    ...     "linewidth": 3,
    ...     "markerfacecolor": "0.8",
    ...     "markeredgecolor": "k",
    ...     "color": "k",
    ... }
    >>> line2d_kwargs_ax2 = {"alpha": 0.2}
    >>> fig = emg.plot_smoothed_dr(
    ...     emgfile,
    ...     smoothfits=smoothfits,
    ...     munumber=[0, 1, 3, 4],
    ...     addidr=True,
    ...     stack=True,
    ...     addrefsig=True,
    ...     line2d_kwargs_ax1=line2d_kwargs_ax1,
    ...     line2d_kwargs_ax2=line2d_kwargs_ax2,
    ... )

    ![](md_graphics/docstrings/plotemg/plot_smoothed_dr_ex_3.png)

    For additional examples on how to customise the figure's layout, refer to
    plot_emgsig().
    """

    # Compute the IDR
    idr = compute_idr(emgfile=emgfile)

    # Check if all the MUs have to be plotted
    if isinstance(munumber, list):
        if len(munumber) == 1:  # Manage exception of single MU
            munumber = munumber[0]
    elif isinstance(munumber, str):
        if emgfile["NUMBER_OF_MUS"] == 1:  # Manage exception of single MU
            munumber = 0
        else:
            munumber = [*range(0, emgfile["NUMBER_OF_MUS"])]

    # Check smoothfits type
    if not isinstance(smoothfits, pd.DataFrame):
        raise TypeError("smoothfits must be a pd.DataFrame")

    # Use the subplot function to allow for the use of twinx()
    figname = get_unique_fig_name("Smoothed DR")
    fig, ax1 = plt.subplots(
        figsize=(figsize[0] / 2.54, figsize[1] / 2.54),
        num=figname,
    )

    # Check if we have a single MU or a list of MUs to plot.
    if isinstance(munumber, int):
        # Plot IDR
        if addidr:
            ax1.plot(
                idr[munumber]["timesec" if timeinseconds else "mupulses"],
                idr[munumber]["idr"],
                ".", markersize=12, alpha=0.4,
                color="C0",  # Set same color as smoothed DR
            )

        # Plot smoothed DR
        if timeinseconds:
            x_smooth = np.arange(len(smoothfits[munumber])) / emgfile["FSAMP"]
        else:
            x_smooth = np.arange(len(smoothfits[munumber]))
        ax1.plot(x_smooth, smoothfits[munumber], linewidth=2, color="C0")

        ax1.set_ylabel("MU {} (pps)".format(munumber))
        # Useful because if the MU is empty it won't show the channel number
        ax1.set_xlabel("Time (Sec)" if timeinseconds else "Samples")

    elif isinstance(munumber, list) and stack:
        # Extract the 'idr' column from each df and create a new df of idrs
        idr_all = pd.DataFrame({key: df['idr'] for key, df in idr.items()})
        idr_all = idr_all[munumber]

        # Normalise 'idr' and 'smoothfits' based on common max and min
        min_ = min(idr_all.min().min(), smoothfits.min().min())
        max_ = max(idr_all.max().max(), smoothfits.max().max())
        norm_idr_all = ((idr_all - min_) / (max_ - min_))
        norm_fit_all = ((smoothfits - min_) / (max_ - min_))

        for count, thisMU in enumerate(munumber):
            # Get norm_fit and mean norm_fit of this MU to align yticks
            norm_fit = norm_fit_all[thisMU]
            norm_fit_mu_mean = norm_fit.mean()

            # Get x axis for smoothed fit
            if timeinseconds:
                x_smooth = np.arange(
                    len(smoothfits[thisMU])
                ) / emgfile["FSAMP"]
            else:
                x_smooth = np.arange(len(smoothfits[thisMU]))

            if addidr:
                # Prepare IDR to plot. Add value to the previous mu to avoid
                # overlapping.
                norm_idr = norm_idr_all[thisMU]
                if norm_fit_mu_mean <= 0.5:
                    norm_idr = norm_idr + (0.5 - norm_fit_mu_mean) + count
                else:
                    norm_idr = norm_idr - (norm_fit_mu_mean - 0.5) + count

                # Prepare smoothed fit to plot. Add value to the previous mu
                # to avoid overlapping
                if norm_fit_mu_mean <= 0.5:
                    norm_fit = norm_fit + (0.5 - norm_fit_mu_mean) + count
                else:
                    norm_fit = norm_fit - (norm_fit_mu_mean - 0.5) + count

                # Plot IDR and smoothed fit
                ax1.plot(
                    idr[thisMU]["timesec" if timeinseconds else "mupulses"][1:],
                    norm_idr.dropna(),
                    ".", markersize=12, alpha=0.4,
                    color=f"C{count}",  # Set same color as smoothed DR
                )
                ax1.plot(x_smooth, norm_fit, linewidth=2, color=f"C{count}")

            else:
                if norm_fit_mu_mean <= 0.5:
                    norm_fit = norm_fit + (0.5 - norm_fit_mu_mean) + count
                else:
                    norm_fit = norm_fit - (norm_fit_mu_mean - 0.5) + count
                ax1.plot(x_smooth, norm_fit, linewidth=2, color=f"C{count}")

        # Ensure correct and complete ticks on the left y axis
        ax1.set_yticks(np.arange(0.5, len(munumber) + 0.5, 1))
        ax1.set_yticklabels([str(mu) for mu in munumber])

        # Set axes labels
        ax1.set_ylabel("Motor units")
        ax1.set_xlabel("Time (Sec)" if timeinseconds else "Samples")

    elif isinstance(munumber, list) and not stack:
        for count, thisMU in enumerate(munumber):
            # Plot IDR
            if addidr:
                ax1.plot(
                    idr[thisMU]["timesec" if timeinseconds else "mupulses"],
                    idr[thisMU]["idr"],
                    ".", markersize=12, alpha=0.4,
                    color=f"C{count}",  # Set same color as smoothed DR
                )

            # Plot smoothed DR
            if timeinseconds:
                x_smooth = np.arange(
                    len(smoothfits[thisMU])
                ) / emgfile["FSAMP"]
            else:
                x_smooth = np.arange(len(smoothfits[thisMU]))
            ax1.plot(
                x_smooth, smoothfits[thisMU], linewidth=2, color=f"C{count}",
            )

        # Set axes labels
        ax1.set_ylabel("Discharge rate (pps)")
        ax1.set_xlabel("Time (Sec)" if timeinseconds else "Samples")

    else:
        raise TypeError(
            "While calling the plot_idr function, you should pass an " +
            "integer, a list or 'all' to munumber"
        )

    # Plot the ref signal
    if addrefsig:
        if not isinstance(emgfile["REF_SIGNAL"], pd.DataFrame):
            raise TypeError(
                "REF_SIGNAL is probably absent or it is not contained in a " +
                "dataframe"
            )

        x_axis = (
            emgfile["REF_SIGNAL"].index / emgfile["FSAMP"]
            if timeinseconds
            else emgfile["REF_SIGNAL"].index
        )

        ax2 = ax1.twinx()
        ax2.plot(x_axis, emgfile["REF_SIGNAL"][0])
        ax2.set_ylabel("MVC")

        # Set z-order so that ax2 is in the background
        ax2.set_zorder(0)
        ax1.set_zorder(1)
        ax1.patch.set_alpha(0)

    # Initialise Figure_Layout_Manager and update default kwarg values with
    # user-specified kwargs.
    fig_manager = Figure_Layout_Manager(figure=fig)
    fig_manager.get_final_kwargs(
        line2d_kwargs_ax1, line2d_kwargs_ax2, axes_kwargs,
    )
    # Adjust labels' size and color, title, ticks and grid
    fig_manager.set_style_from_kwargs()
    # Set appropriate layout
    fig_manager.set_layout(
        tight_layout=tight_layout,
        despine="2yaxes" if addrefsig else "1yaxis",
    )

    # Show the figure
    if showimmediately:
        plt.show()

    return fig


def plot_muaps(
    sta_dict,
    title="MUAPs from STA",
    figsize=[20, 15],
    tight_layout=False,
    line2d_kwargs_ax1=None,
    showimmediately=True,
):
    """
    Plot MUAPs obtained from STA from one or multiple MUs.

    Parameters
    ----------
    sta_dict : dict or list
        dict containing STA of the specified MU or a list of dicts containing
        STA of specified MUs.
        If a list is passed, different MUs are overlayed. This is useful for
        visualisation of MUAPs during tracking or duplicates removal.
    title : str, default "MUAPs from STA"
        Title of the plot canva.
    figsize : list, default [20, 15]
        Size of the figure in centimeters [width, height].
    tight_layout : bool, default False
        If True (default), the plt.tight_layout() is called and the figure's
        layout is improved.
        It is useful to set it to False when calling the function from a GUI
        or if the final layout is not correct.
    line2d_kwargs_ax1 : dict or list, optional
        User-specified keyword arguments for sets of Line2D objects.
        This can be a list of dictionaries containing the kwargs for each
        Line2D, or a single dictionary. If a single dictionary is passed,
        the same style will be applied to all the lines. See examples.
    showimmediately : bool, default True
        If True (default), plt.show() is called and the figure showed to the
        user.
        It is useful to set it to False when calling the function from a GUI.

    Returns
    -------
    fig : pyplot `~.figure.Figure`

    See also
    --------
    - sta : computes the spike-triggered average (STA) of every MUs.
    - plot_muap : for overplotting all the STAs and the average STA of a MU.
    - align_by_xcorr : for alignin the STAs of two different MUs.

    Notes
    -----
    There is no limit to the number of MUs and STA files that can be
    overplotted.

    ``Remember: the different STAs should be matched`` with same number of
        electrode, processing (i.e., differential) and computed on the same
        timewindow.

    Examples
    --------
    Plot MUAPs of a single MU.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.emg_from_samplefile()
    >>> sorted_rawemg = emg.sort_rawemg(
    ...     emgfile=emgfile,
    ...     code="GR08MM1305",
    ...     orientation=180,
    ...     dividebycolumn=True,
    ... )
    >>> sta = emg.sta(
    ...     emgfile=emgfile,
    ...     sorted_rawemg=sorted_rawemg,
    ...     firings="all",
    ...     timewindow=50,
    ... )
    >>> emg.plot_muaps(sta_dict=sta[0])

    ![](md_graphics/docstrings/plotemg/plot_muaps_ex_1.png)

    Plot single differential derivation MUAPs of a single MU.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.emg_from_samplefile()
    >>> sorted_rawemg = emg.sort_rawemg(
    ...     emgfile=emgfile,
    ...     code="GR08MM1305",
    ...     orientation=180,
    ...     dividebycolumn=True,
    ... )
    >>> sorted_rawemg = emg.diff(sorted_rawemg=sorted_rawemg)
    >>> sta = emg.sta(
    ...     emgfile=emgfile,
    ...     sorted_rawemg=sorted_rawemg,
    ...     firings="all",
    ...     timewindow=50,
    ... )
    >>> emg.plot_muaps(sta_dict=sta[1])

    ![](md_graphics/docstrings/plotemg/plot_muaps_ex_2.png)

    Plot single differential derivation MUAPs of two MUs from the same file.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.emg_from_samplefile()
    >>> sorted_rawemg = emg.sort_rawemg(
    ...     emgfile=emgfile,
    ...     code="GR08MM1305",
    ...     orientation=180,
    ...     dividebycolumn=True,
    ... )
    >>> sorted_rawemg = emg.diff(sorted_rawemg=sorted_rawemg)
    >>> sta = emg.sta(
    ...     emgfile=emgfile,
    ...     sorted_rawemg=sorted_rawemg,
    ...     firings="all",
    ...     timewindow=50,
    ... )
    >>> emg.plot_muaps(sta_dict=[sta[2], sta[3]])

    ![](md_graphics/docstrings/plotemg/plot_muaps_ex_3.png)

    Plot double differential derivation MUAPs of two MUs from the same file
    and change their color.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.emg_from_samplefile()
    >>> sorted_rawemg = emg.sort_rawemg(
    ...     emgfile=emgfile,
    ...     code="GR08MM1305",
    ...     orientation=180,
    ...     dividebycolumn=True,
    ... )
    >>> sorted_rawemg = emg.double_diff(sorted_rawemg=sorted_rawemg)
    >>> sta = emg.sta(
    ...     emgfile=emgfile,
    ...     sorted_rawemg=sorted_rawemg,
    ...     firings="all",
    ...     timewindow=50,
    ... )
    >>> line2d_kwargs_ax1 = {
    ...     "color": "tab:red",
    ... }
    >>> emg.plot_muaps(
    ...     sta_dict=[sta[2], sta[3]],
    ...     line2d_kwargs_ax1=line2d_kwargs_ax1,
    ... )

    ![](md_graphics/docstrings/plotemg/plot_muaps_ex_4.png)

    Or change their color and style individually.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.emg_from_samplefile()
    >>> sorted_rawemg = emg.sort_rawemg(
    ...     emgfile=emgfile,
    ...     code="GR08MM1305",
    ...     orientation=180,
    ...     dividebycolumn=True,
    ... )
    >>> sorted_rawemg = emg.double_diff(sorted_rawemg=sorted_rawemg)
    >>> sta = emg.sta(
    ...     emgfile=emgfile,
    ...     sorted_rawemg=sorted_rawemg,
    ...     firings="all",
    ...     timewindow=30,
    ... )
    >>> line2d_kwargs_ax1 = [
    ...     {
    ...         "color": "tab:red",
    ...         "linewidth": 3,
    ...         "alpha": 0.6,
    ...     },
    ...     {
    ...         "color": "tab:blue",
    ...         "linewidth": 3,
    ...         "alpha": 0.6,
    ...     },
    ... ]
    >>> emg.plot_muaps(
    ...     sta_dict=[sta[2], sta[3]],
    ...     line2d_kwargs_ax1=line2d_kwargs_ax1,
    ... )

    ![](md_graphics/docstrings/plotemg/plot_muaps_ex_5.png)
    """

    if isinstance(sta_dict, dict):
        sta_dict = [sta_dict]

    if not isinstance(sta_dict, list):
        raise TypeError("sta_dict must be dict or list")

    # Find the largest and smallest value to define common y axis limits.
    xmax = 0
    xmin = 0
    # Loop each sta_dict and MU, c means matrix columns
    for thisdict in sta_dict:
        for c in thisdict:
            max_ = thisdict[c].max().max()
            min_ = thisdict[c].min().min()
            if max_ > xmax:
                xmax = max_
            if min_ < xmin:
                xmin = min_

    # Obtain number of columns and rows
    cols = len(sta_dict[0])
    rows = len(sta_dict[0][next(iter(sta_dict[0]))].columns)

    figname = get_unique_fig_name(title)
    fig, axs = plt.subplots(
        rows,
        cols,
        figsize=(figsize[0] / 2.54, figsize[1] / 2.54),
        num=figname,
    )

    # Manage exception of arrays instead of matrices and check that they
    # are correctly oriented.
    if cols > 1 and rows > 1:
        # Matrices
        for thisdict in sta_dict:
            # Plot all the MUAPs, c means matrix columns, r rows
            for r in range(rows):
                for pos, c in enumerate(thisdict.keys()):
                    axs[r, pos].plot(thisdict[c].iloc[:, r])

                    axs[r, pos].set_ylim(xmin, xmax)
                    axs[r, pos].xaxis.set_visible(False)
                    axs[r, pos].set(yticklabels=[])
                    axs[r, pos].tick_params(left=False)

    elif cols == 1 and rows > 1:
        # Arrays
        for thisdict in sta_dict:
            # Plot all the MUAPs, c means matrix columns, r rows
            for r in range(rows):
                for pos, c in enumerate(thisdict.keys()):
                    axs[r].plot(thisdict[c].iloc[:, r])

                    axs[r].set_ylim(xmin, xmax)
                    axs[r].xaxis.set_visible(False)
                    axs[r].set(yticklabels=[])
                    axs[r].tick_params(left=False)

    elif cols > 1 and rows == 1:
        raise ValueError(
            "Arrays should be organised as 1 column, multiple rows. " +
            "Not as 1 row, multiple columns."
        )

    else:
        raise ValueError(
            "Unacceptable number of rows and columns to plot"
        )

    # Initialise Figure_Subplots_Layout_Manager and update the figure if
    # needed.
    fig_manager = Figure_Subplots_Layout_Manager(figure=fig)
    if line2d_kwargs_ax1 is not None:
        fig_manager.set_line2d_from_kwargs(
            line2d_kwargs_ax1=line2d_kwargs_ax1,
        )
    # Set appropriate layout
    fig_manager.set_layout(tight_layout=tight_layout, despine="all")

    # Show the figure
    if showimmediately:
        plt.show()

    return fig


def plot_muap(
    emgfile,
    stmuap,
    munumber,
    column,
    channel,
    channelprog=False,
    average=True,
    timeinseconds=True,
    figsize=[20, 15],
    tight_layout=True,
    line2d_kwargs_ax1=None,
    line2d_kwargs_ax2=None,
    axes_kwargs=None,
    showimmediately=True,
):
    """
    Plot the MUAPs of a specific matrix channel.

    Plot the MUs action potential (MUAPs) shapes with or without average.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    stmuap : dict
        dict containing a dict of ST MUAPs (pd.DataFrame) for every MUs.
    munumber : int
        The number of the MU to plot.
    column : str
        The matrix columns.
        Options are usyally "col0", "col1", "col2", ..., last column.
    channel : int
        The channel of the matrix to plot.
        This can be the real channel number if channelprog=False (default),
        or a progressive number (from 0 to the length of the matrix column)
        if channelprog=True.
    channelprog : bool, default False
        Whether to use the real channel number or a progressive number
        (see channel).
    average : bool, default True
        Whether to plot also the MUAPs average obtained by spike triggered
        average.
    timeinseconds : bool, default True
        Whether to show the time on the x-axes in seconds (True)
        or in samples (False).
    figsize : list, default [20, 15]
        Size of the figure in centimeters [width, height].
    tight_layout : bool, default True
        If True (default), the plt.tight_layout() is called and the figure's
        layout is improved.
        It is useful to set it to False when calling the function from a GUI.
    line2d_kwargs_ax1 : dict, optional
        Kwargs for matplotlib.lines.Line2D relative to figure's axis 1 (the
        single MUAPs).
    line2d_kwargs_ax2 : dict, optional
        Kwargs for matplotlib.lines.Line2D relative to figure's axis 2 (the
        average MUAP).
    axes_kwargs : dict, optional
        Kwargs for figure's axes.
    showimmediately : bool, default True
        If True (default), plt.show() is called and the figure showed to the
        user.
        It is useful to set it to False when calling the function from a GUI.

    Returns
    -------
    fig : pyplot `~.figure.Figure`

    See also
    --------
    - plot_muaps : Plot MUAPs obtained from STA from one or multiple MUs.
    - st_muap : Generate spike triggered MUAPs of every MUs
        (as input to this function).

    Examples
    --------
    Plot all the consecutive MUAPs of a single MU.
    In this case we are plotting the matrix channel 35 which is placed in
    column 3 ("col2" as Python numbering is base 0).

    >>> import openhdemg.library as emg
    >>> emgfile = emg.emg_from_samplefile()
    >>> sorted_rawemg = emg.sort_rawemg(
    ...     emgfile,
    ...     code="GR08MM1305",
    ...     orientation=180,
    ...     dividebycolumn=True,
    ... )
    >>> stmuap = emg.st_muap(
    ...     emgfile=emgfile,
    ...     sorted_rawemg=sorted_rawemg,
    ...     timewindow=50,
    ... )
    >>> emg.plot_muap(
    ...     emgfile=emgfile,
    ...     stmuap=stmuap,
    ...     munumber=3,
    ...     column="col2",
    ...     channel=35,
    ...     channelprog=False,
    ...     average=False,
    ...     timeinseconds=True,
    ...     figsize=[20, 15],
    ...     showimmediately=True,
    ... )

    To avoid the problem of remebering which channel number is present in
    which matrix column, we can set channelprog=True and locate the channel
    with a value ranging from 0 to the length of each column.

    >>> emg.plot_muap(
    ...     emgfile=emgfile,
    ...     stmuap=stmuap,
    ...     munumber=3,
    ...     column="col2",
    ...     channel=9,
    ...     channelprog=True,
    ...     average=False,
    ...     timeinseconds=True,
    ...     figsize=[20, 15],
    ...     showimmediately=True,
    ... )

    ![](md_graphics/docstrings/plotemg/plot_muap_ex_2.png)

    It is also possible to visualise the spike triggered average
    of the MU with average=True.
    In this example the single differential derivation is used.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.emg_from_samplefile()
    >>> sorted_rawemg = emg.sort_rawemg(
    ...     emgfile=emgfile,
    ...     code="GR08MM1305",
    ...     orientation=180,
    ...     dividebycolumn=True,
    ... )
    >>> sorted_rawemg = emg.diff(sorted_rawemg=sorted_rawemg)
    >>> stmuap = emg.st_muap(
    ...     emgfile=emgfile,
    ...     sorted_rawemg=sorted_rawemg,
    ...     timewindow=50,
    ... )
    >>> emg.plot_muap(
    ...     emgfile=emgfile,
    ...     stmuap=stmuap,
    ...     munumber=3,
    ...     column="col2",
    ...     channel=8,
    ...     channelprog=True,
    ...     average=True,
    ...     timeinseconds=True,
    ...     figsize=[20, 15],
    ...     showimmediately=True,
    ... )

    ![](md_graphics/docstrings/plotemg/plot_muap_ex_3.png)

    We can also customise the look of the plot.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.emg_from_samplefile()
    >>> sorted_rawemg = emg.sort_rawemg(
    ...     emgfile=emgfile,
    ...     code="GR08MM1305",
    ...     orientation=180,
    ...     dividebycolumn=True,
    ... )
    >>> sorted_rawemg = emg.diff(sorted_rawemg=sorted_rawemg)
    >>> stmuap = emg.st_muap(
    ...     emgfile=emgfile,
    ...     sorted_rawemg=sorted_rawemg,
    ...     timewindow=30,
    ... )
    >>> line2d_kwargs_ax1 = {"linewidth": 0.5}
    >>> line2d_kwargs_ax2 = {"linewidth": 3, "color": '0.4'}
    >>> axes_kwargs = {
    ...     "grid": {
    ...         "visible": True,
    ...         "axis": "both",
    ...         "color": "gray",
    ...         "linestyle": "--",
    ...         "linewidth": 0.5,
    ...         "alpha": 0.7
    ...     },
    ...     "labels": {
    ...         "xlabel_size": 16,
    ...         "ylabel_sx_size": 16,
    ...     },
    ... }
    >>> fig = emg.plot_muap(
    ...     emgfile=emgfile,
    ...     stmuap=stmuap,
    ...     munumber=3,
    ...     column="col2",
    ...     channel=35,
    ...     channelprog=False,
    ...     average=True,
    ...     timeinseconds=True,
    ...     figsize=[20, 15],
    ...     line2d_kwargs_ax1=line2d_kwargs_ax1,
    ...     line2d_kwargs_ax2=line2d_kwargs_ax2,
    ...     axes_kwargs=axes_kwargs,
    ...     showimmediately=True,
    ... )

    ![](md_graphics/docstrings/plotemg/plot_muap_ex_4.png)

    For further examples on how to customise the figure's layout, refer to
    plot_emgsig().
    """

    # Check if munumber is within the number of MUs
    if munumber >= emgfile["NUMBER_OF_MUS"]:
        raise ValueError(
            "munumber exceeds the the number of MUs in the emgfile " +
            f"({emgfile['NUMBER_OF_MUS']})"
        )

    # Get the MUAPs to plot
    if channelprog:
        keys = list(stmuap[munumber][column].keys())

        # Check that the specified channel is within the matrix column range
        if channel >= len(keys):
            raise ValueError(
                "Channel exceeds the the length of the matrix column, " +
                "verify the use of channelprog"
            )

        my_muap = stmuap[munumber][column][keys[channel]]
        channelnumb = keys[channel]

    else:
        keys = list(stmuap[munumber][column].keys())

        # Check that the specified channel is within the matrix channels
        if channel not in keys:
            raise ValueError(
                "Channel is not included in this matrix column"
            )

        my_muap = stmuap[munumber][column][channel]
        channelnumb = channel

    # Here we produce an x axis in milliseconds or samples
    if timeinseconds:
        x_axis = (my_muap.index / emgfile["FSAMP"]) * 1000
    else:
        x_axis = my_muap.index

    # Set figure and name based on original channel number
    figname = "ST MUAPs of MU {}, column {}, channel {}".format(
        munumber, column, channelnumb
    )
    figname = get_unique_fig_name(figname)
    fig, ax1 = plt.subplots(
        figsize=(figsize[0] / 2.54, figsize[1] / 2.54),
        num=figname,
    )

    # Plot all the MUAPs
    if average:
        # Create a second axis for custom look
        ax2 = ax1.twiny()
        ax2.xaxis.set_visible(False)
        ax2.yaxis.set_visible(False)

        ax1.plot(x_axis, my_muap)
        ax2.plot(x_axis, my_muap.mean(axis="columns"))
    else:
        ax1.plot(x_axis, my_muap, linewidth=0.2)

    ax1.set_ylabel("Amplitude")
    ax1.set_xlabel("Time (ms)" if timeinseconds else "Samples")

    # Initialise Figure_Layout_Manager and update default kwarg values with
    # user-specified kwargs.
    fig_manager = Figure_Layout_Manager(figure=fig)
    # If not specified, set default line kwargs for decent plotting
    if average:
        def_line2d_kwargs_ax1 = {"color": "0.6", "linewidth": 0.2}
        def_line2d_kwargs_ax2 = {"color": "red"}
    else:
        def_line2d_kwargs_ax1 = {"linewidth": 0.2}
        def_line2d_kwargs_ax2 = {}

    if line2d_kwargs_ax1 is not None:
        line2d_kwargs_ax1 = {
            **def_line2d_kwargs_ax1, **line2d_kwargs_ax1
        }
    else:
        line2d_kwargs_ax1 = def_line2d_kwargs_ax1

    if line2d_kwargs_ax2 is not None:
        line2d_kwargs_ax2 = {
            **def_line2d_kwargs_ax2, **line2d_kwargs_ax2
        }
    else:
        line2d_kwargs_ax2 = def_line2d_kwargs_ax2

    fig_manager.get_final_kwargs(
        line2d_kwargs_ax1, line2d_kwargs_ax2, axes_kwargs,
    )

    # Adjust labels' size and color, title, ticks and grid
    fig_manager.set_style_from_kwargs()
    # Set appropriate layout
    fig_manager.set_layout(
        tight_layout=tight_layout,
        despine="1yaxis",
    )

    # Show the figure
    if showimmediately:
        plt.show()

    return fig


def plot_muaps_for_cv(
    sta_dict,
    xcc_sta_dict,
    title="MUAPs for CV",
    figsize=[20, 15],
    tight_layout=False,
    line2d_kwargs_ax1=None,
    showimmediately=True,
):
    """
    Visualise MUAPs on which to calculate MUs CV.

    Plot MUAPs obtained from the STA of the double differential signal and
    their paired cross-correlation value.

    Parameters
    ----------
    sta_dict : dict
        dict containing the STA of the double-differential derivation of a
        specific MU.
    xcc_sta_dict : dict
        dict containing the normalised cross-correlation coefficient of the
        double-differential derivation of a specific MU.
    title : str, default "MUAPs from STA"
        Title of the plot.
    figsize : list, default [20, 15]
        Size of the figure in centimeters [width, height].
    tight_layout : bool, default False
        If True (default), the plt.tight_layout() is called and the figure's
        layout is improved.
        It is useful to set it to False when calling the function from a GUI
        or if the final layout is not correct.
    line2d_kwargs_ax1 : dict or list, optional
        User-specified keyword arguments for sets of Line2D objects.
        This can be a list of dictionaries containing the kwargs for each
        Line2D, or a single dictionary. If a single dictionary is passed,
        the same style will be applied to all the lines. See examples.
    showimmediately : bool, default True
        If True (default), plt.show() is called and the figure showed to the
        user.
        It is useful to set it to False when calling the function from a GUI.

    Returns
    -------
    fig : pyplot `~.figure.Figure`

    Examples
    --------
    Plot the double differential derivation and the XCC of adjacent channels
    for the first MU (0).

    >>> import openhdemg.library as emg
    >>> emgfile = emg.emg_from_samplefile()
    >>> emgfile = emg.filter_rawemg(emgfile)
    >>> sorted_rawemg = emg.sort_rawemg(
    ...     emgfile,
    ...     code="GR08MM1305",
    ...     orientation=180,
    ...     dividebycolumn=True
    ... )
    >>> dd = emg.double_diff(sorted_rawemg)
    >>> sta = emg.sta(
    ...     emgfile=emgfile,
    ...     sorted_rawemg=dd,
    ...     firings=[0, 50],
    ...     timewindow=50,
    ... )
    >>> xcc_sta = emg.xcc_sta(sta)
    >>> fig = emg.plot_muaps_for_cv(
    ...     sta_dict=sta[0],
    ...     xcc_sta_dict=xcc_sta[0],
    ...     showimmediately=True,
    ... )

    ![](md_graphics/docstrings/plotemg/plot_muaps_for_cv_ex_1.png)

    Customise the look of the plot.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.emg_from_samplefile()
    >>> emgfile = emg.filter_rawemg(emgfile)
    >>> sorted_rawemg = emg.sort_rawemg(
    ...     emgfile,
    ...     code="GR08MM1305",
    ...     orientation=180,
    ...     dividebycolumn=True
    ... )
    >>> dd = emg.double_diff(sorted_rawemg)
    >>> sta = emg.sta(
    ...     emgfile=emgfile,
    ...     sorted_rawemg=dd,
    ...     firings="all",
    ...     timewindow=50,
    ... )
    >>> xcc_sta = emg.xcc_sta(sta)
    >>> line2d_kwargs_ax1 = {
    ...     "color": "k",
    ...     "linewidth": 1,
    ... }
    >>> fig = emg.plot_muaps_for_cv(
    ...     sta_dict=sta[0],
    ...     xcc_sta_dict=xcc_sta[0],
    ...     line2d_kwargs_ax1=line2d_kwargs_ax1,
    ...     showimmediately=True,
    ... )

    ![](md_graphics/docstrings/plotemg/plot_muaps_for_cv_ex_2.png)

    For further examples on how to customise the figure's layout, refer to
    plot_muaps().
    """

    if not isinstance(sta_dict, dict):
        raise TypeError("sta_dict must be a dict")

    # Find the largest and smallest value to define common y axis limits.
    # This is much faster than using sharey.
    ymax = 0
    ymin = 0
    # Loop each column (c)
    for c in sta_dict:
        max_ = sta_dict[c].max().max()
        min_ = sta_dict[c].min().min()
        if max_ > ymax:
            ymax = max_
        if min_ < ymin:
            ymin = min_

    # Obtain number of columns and rows, this changes if we use different
    # matrices.
    cols = len(sta_dict)
    rows = len(sta_dict["col0"].columns)
    figname = get_unique_fig_name(title)
    fig, axs = plt.subplots(
        rows,
        cols,
        figsize=(figsize[0] / 2.54, figsize[1] / 2.54),
        num=figname,
    )

    # Manage exception of arrays instead of matrices and check that they
    # are correctly oriented.
    if cols > 1 and rows > 1:
        for r in range(rows):
            for pos, c in enumerate(sta_dict.keys()):
                axs[r, pos].plot(sta_dict[c].iloc[:, r])

                axs[r, pos].set_ylim(ymin, ymax)
                axs[r, pos].xaxis.set_visible(False)
                axs[r, pos].set(yticklabels=[])
                axs[r, pos].tick_params(left=False)

                if r != 0:
                    xcc = round(xcc_sta_dict[c].iloc[:, r].iloc[0], 2)
                    color = "k" if xcc >= 0.8 else "r"
                    axs[r, pos].set_title(
                        xcc, fontsize=8, color=color, loc="left", pad=3,
                    )

                else:
                    axs[r, pos].set_title(c, fontsize=12, pad=20)

                axs[r, pos].set_ylabel(r, fontsize=6, rotation=0, labelpad=0)

    elif cols == 1 and rows > 1:
        for r in range(rows):
            for pos, c in enumerate(sta_dict.keys()):
                axs[r].plot(sta_dict[c].iloc[:, r])

                axs[r].set_ylim(ymin, ymax)
                axs[r].xaxis.set_visible(False)
                axs[r].set(yticklabels=[])
                axs[r].tick_params(left=False)

                if r != 0:
                    xcc = round(xcc_sta_dict[c].iloc[:, r].iloc[0], 2)
                    color = "k" if xcc >= 0.8 else "r"
                    axs[r].set_title(
                        xcc, fontsize=8, color=color, loc="left", pad=3,
                    )

                else:
                    axs[r].set_title(c, fontsize=12, pad=20)

                axs[r].set_ylabel(r, fontsize=6, rotation=0, labelpad=0)

    elif cols > 1 and rows == 1:
        raise ValueError(
            "Arrays should be organised as 1 column, multiple rows. " +
            "Not as 1 row, multiple columns."
        )

    else:
        raise ValueError(
            "Unacceptable number of rows and columns to plot"
        )

    # Initialise Figure_Subplots_Layout_Manager and update the figure if
    # needed.
    fig_manager = Figure_Subplots_Layout_Manager(figure=fig)
    if line2d_kwargs_ax1 is not None:
        fig_manager.set_line2d_from_kwargs(
            line2d_kwargs_ax1=line2d_kwargs_ax1,
        )
    # Set appropriate layout
    fig_manager.set_layout(tight_layout=tight_layout, despine="all")

    # Show the figure
    if showimmediately:
        plt.show()

    return fig
