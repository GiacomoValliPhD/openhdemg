"""
This module contains classes (QtWidgets) and functions managing the user
interfaces used by openhdemg.library. These classes or functions can be used
directly or integrated in larger UIs (e.g., MU tracking and conduction
velocity estimation).
"""

import os
import gc
import sys
import copy
import warnings

from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QSettings
from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QMessageBox, QFileDialog,
    QLabel, QPushButton, QDialogButtonBox, QSizePolicy, QWidget
)

import numpy as np
import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import (
    FigureCanvasQTAgg, NavigationToolbar2QT,
)

matplotlib.use("QtAgg")


def check_app():
    """
    Check if a QApplication instance already exists and return needed objects.

    Ensures that a `QApplication` is available before launching any Qt-based
    GUI. If no instance exists, a new one is created with the 'Fusion' style
    applied. This is useful for ensuring compatibility in environments where a
    QApplication may already be running (e.g., Qt apps).

    Check the implementation of ``run_point_selector()`` to see how it can be
    used.

    Returns
    -------
    app : QApplication
        The active or newly created QApplication instance.
    app_created : bool
        True if a new QApplication was created, False if one already existed.
    path_to_icon : str
        Path to the openhdemg icon.
    """

    master_path = os.path.dirname(os.path.abspath(__file__))
    path_to_icon = os.path.normpath(
            os.path.join(
                master_path,
                "icons",
                "Icon_transp.ico",
            )
        )

    app = QApplication.instance()

    if app is None:
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        app_created = True
    else:
        app_created = False

    return app, app_created, path_to_icon


class PointSelectorDialog(QDialog):
    """
    Interactive dialog for selecting points on a 1D signal.

    It shows a Matplotlib figure in a Qt dialog. The dialog ensures the number
    of selected points matches the required count (if specified) before
    closing.

    Users can move the mouse to track coordinates and press:

        - "A" or "a" to add a point at the current cursor location
        - "D" or "d" to delete the last selected point
        - "Enter" to confirm the selection and close the window

    Check the implementation of ``run_point_selector()`` to see how it can be
    used. It is always suggested to call the ``PointSelectorDialog`` from
    ``run_point_selector()`` instead of directly running its instance, as
    this is also managing the ``QApplication``.

    Parameters
    ----------
    data : array-like
        1D signal to display for point selection.
        This can be anything suitable for matplotlib.axes.Axes.plot.
    nclic : int, default -1
        Number of points to enforce selection before confirming.
        Default is -1, which means no limit.
    y_label : str, default "Data"
        Label for the y-axis.
    title : str, default "A to select, D to delete, Enter to continue"
        Title shown above the plot.
    title_fontsize : int or float, default 10
        Font size of the title.
    title_fontweight : str, default "bold"
        Font weight of the title text. This will be passed to
        matplotlib.text.Text.set_fontweight.
    path_to_icon : None or str, default None
        The path to the window icon. Use none if this widget inherits from a
        parent.

    Attributes
    ----------
    points : list of lists
        A list of Lists containing the [x, y] coordinates of the selected
        points.

    See also
    --------
    - run_point_selector : Run the point selector dialog and return the
        selected points.
    """

    def __init__(
        self,
        data,
        nclic=-1,
        y_label="Data",
        title="A to select, D to delete, Enter to continue",
        title_fontsize=10,
        title_fontweight="bold",
        path_to_icon=None,
    ):

        super().__init__()

        # Enable maximise and close buttons
        self.setWindowFlags(
            Qt.Window | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint
        )

        # Set window name and icon
        self.setWindowTitle("Point Selector")
        if path_to_icon is not None:
            icon = QIcon(path_to_icon)
            self.setWindowIcon(icon)

        # Define required variables
        self.data = data
        self.nclic = nclic
        self.points = []
        self.last_mouse_pos = None

        # Matplotlib Figure + Canvas + Toolbar
        self.fig = Figure(tight_layout=True)
        self.canvas = FigureCanvasQTAgg(self.fig)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)

        # Plot data
        self.ax = self.fig.add_subplot(111)
        self.signal_line, = self.ax.plot(self.data)
        self.markers = []  # store marker references
        self.ax.set_ylabel(y_label)
        self.ax.set_title(
            title,
            fontdict={
                "fontsize": title_fontsize,
                "fontweight": title_fontweight,
            }
        )

        # Add figure and canvas to the layout
        self.v_layout = QVBoxLayout()
        self.v_layout.addWidget(self.toolbar)
        self.v_layout.addWidget(self.canvas)
        self.setLayout(self.v_layout)

        # Give focus to collect clicks
        self.canvas.setFocusPolicy(Qt.StrongFocus)
        self.canvas.setFocus()

        # Event connections
        self.canvas.mpl_connect("motion_notify_event", self.on_mouse_move)
        self.canvas.mpl_connect("key_press_event", self.on_key_press)

    def on_mouse_move(self, event):
        """
        Record mouse position on the figure coordinates.
        """

        if event.inaxes:
            self.last_mouse_pos = [event.xdata, event.ydata]

    def on_key_press(self, event):
        """
        React to pressed buttons.
        """

        if event.key in ["A", "a"] and self.last_mouse_pos is not None:
            self.points.append(self.last_mouse_pos)
            self.redraw_points()
        elif event.key in ["D", "d"] and self.points:
            self.points.pop()
            self.redraw_points()
        elif event.key == "enter":
            self.close()

    def redraw_points(self):
        """
        Update the figure with the selected points.
        """

        # Remove old markers from plot
        for marker in self.markers:
            marker.remove()
        self.markers.clear()
        # Add new markers
        for pt in self.points:
            marker, = self.ax.plot(pt[0], pt[1], "r+")
            self.markers.append(marker)
        self.canvas.draw_idle()

    def closeEvent(self, event):
        # Ask user whether to exit if the number of selected points is
        # not correct.
        if self.nclic > 0 and self.nclic != len(self.points):
            reply = QMessageBox.question(
                self,
                "Incomplete Selection",
                (
                    f"You selected {len(self.points)} point(s), "
                    f"but {self.nclic} were expected.\n"
                    "Do you want to exit anyway?"
                ),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                event.ignore()
                return

        # Before exit, clear memory
        # Iteratively clean the 2 levels of the central widget
        layout = self.v_layout
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            widget.setParent(None)
            widget.close()
            widget.deleteLater()
            del widget
            del item
        self.fig = None
        self.data = None

        # Force garbage collection to fasten memory cleanup
        gc.collect()

        # Always call the base method to ensure normal closing behavior
        super().closeEvent(event)


def run_point_selector(
    data,
    nclic=-1,
    y_label="Data",
    title="A to select, D to delete, Enter to continue",
    title_fontsize=10,
    title_fontweight="bold",
):
    """
    Run the point selector dialog and return the selected points.

    Opens a blocking Qt dialog where the user can select points on a 1D signal
    using keyboard and mouse interactions. The dialog ensures the number of
    selected points matches the required count (if specified) before closing.

    Compared to directly creating a PointSelectorDialog instance, this function
    automatically manages the app integration for the user.

    Users can move the mouse to track coordinates and press:

        - "A" or "a" to add a point at the current cursor location
        - "D" or "d" to delete the last selected point
        - "Enter" to confirm the selection and close the window

    Parameters
    ----------
    data : array-like
        1D signal to display for point selection.
        This can be anything suitable for matplotlib.axes.Axes.plot.
    nclic : int, default -1
        Number of points to enforce selection before confirming.
        Default is -1, which means no limit.
    y_label : str, default "Data"
        Label for the y-axis.
    title : str, default "A to select, D to delete, Enter to continue"
        Title shown above the plot.
    title_fontsize : int or float, default 10
        Font size of the title.
    title_fontweight : str, default "bold"
        Font weight of the title text. This will be passed to
        matplotlib.text.Text.set_fontweight.

    Returns
    -------
    points : list of lists
        A list of Lists containing the [x, y] coordinates of the selected
        points.

    Examples
    --------
    Free selection of points (no limit)

    >>> import numpy as np
    >>> from openhdemg.ui import run_point_selector
    >>> signal = np.sin(np.linspace(0, 10, 500))
    >>> selected_points = run_point_selector(signal, nclic=-1)
    >>> print(selected_points)
    [[70.22, 0.96], [222.14, -0.95], [314.93, 0.04]]

    Select exactly 2 points and print the X coordinates.

    >>> import numpy as np
    >>> from openhdemg.ui import run_point_selector
    >>> signal = np.random.randn(1000)
    >>> selected = run_point_selector(signal, nclic=2)
    >>> print(f"Start: {selected[0][0]}, End: {selected[1][0]}")
    Start: 168.21717572391907, End: 713.5261404204681

    """

    # Check if the PointSelectorDialog is called from an existing application.
    # If not, create an app and retrieve an icon path for it.
    app, app_created, path_to_icon = check_app()

    # Execute PointSelectorDialog in blocking mode
    dialog = PointSelectorDialog(
        data=data,
        nclic=nclic,
        y_label=y_label,
        title=title,
        title_fontsize=title_fontsize,
        title_fontweight=title_fontweight,
        path_to_icon=path_to_icon,
    )
    dialog.exec()
    points = dialog.points

    return points


class CustomFileDialog():
    """
    Custom file dialog for opening or saving a file.

    It uses QSettings to remember the last accessed directory.

    Check the implementation of ``run_custom_file_dialog()`` to see how it can
    be used. It is always suggested to call the ``CustomFileDialog`` from
    ``run_custom_file_dialog()`` instead of directly running its instance, as
    this is also managing the ``QApplication``.

    Parameters
    ----------
    mode : str {"open", "save"}, default "open"
        Operation mode for the dialog.

        ``open``
            Get the file path to load the selected file.

        ``save``
            Get the file path where to save the selected file.
    filesource : str, default "file"
        Description of the file type being handled. This is shown in the dialog
        title.
    filetypes : list of tuples, default [("openhdemg files", "*.json"), ("All files", "*.*")]
        A list of (description, extension) tuples specifying acceptable file
        types.

    Methods
    -------
    get_filepath()
        Get the path to the file or None if the operation is cancelled.

    See also
    --------
    - run_custom_file_dialog : Opens a custom file dialog for opening or
        saving a file.
    """

    def __init__(
        self,
        mode="open",
        filesource="file",
        filetypes=[("All files", "*.*")],
    ):

        # Class variables
        self.mode = mode
        self.filesource = filesource
        self.filetypes = filetypes

        # Setup settings to remember the last directory.
        # On Windows, settings registry can be accessed from:
        # HKEY_CURRENT_USER\Software\openhdemg\library_ui
        self.settings = QSettings("openhdemg", "library_ui")
        self.last_dir_key = "LastDirectory"  # Same as in CustomDirectoryDialog

    def get_filepath(self):
        """
        Get the path to the file.

        If the operation is completed, the directory is memorised for following
        uses.

        Returns
        -------
        str or None
            The selected file path if confirmed, or None if the dialog was
            canceled.
        """

        last_dir = self.settings.value(self.last_dir_key, os.getcwd())
        caption = f"Select an {self.filesource} file to {self.mode}"

        if self.mode == "open":
            file_path, _ = QFileDialog.getOpenFileName(
                caption=caption, dir=last_dir, filter=self._build_filter()
            )
        elif self.mode == "save":
            file_path, _ = QFileDialog.getSaveFileName(
                caption=caption, dir=last_dir, filter=self._build_filter()
            )
        else:
            raise ValueError("CustomFileDialog mode must be 'open' or 'save'")

        if file_path:
            # Save the directory for next time
            self.settings.setValue(
                self.last_dir_key, os.path.dirname(file_path),
            )
            return file_path
        else:
            return None

    def _build_filter(self):
        return ";;".join([f"{desc} ({ext})" for desc, ext in self.filetypes])


def run_custom_file_dialog(
    mode="open",
    filesource="openhdemg",
    filetypes=[("openhdemg files", "*.json"), ("All files", "*.*")],
):
    """
    Opens a custom file dialog for opening or saving a file, remembering the
    last accessed directory.

    Compared to directly creating a CustomFileDialog instance, this function
    automatically manages the app integration for the user.

    Parameters
    ----------
    mode : str {"open", "save"}, default "open"
        Operation mode for the dialog.

        ``open``
            Get the file path to load the selected file.

        ``save``
            Get the file path where to save the selected file.
    filesource : str, default "openhdemg"
        Description of the file type being handled. This is shown in the dialog
        title.
    filetypes : list of tuples, default [("openhdemg files", "*.json"), ("All files", "*.*")]
        A list of (description, extension) tuples specifying acceptable file
        types.

    Returns
    -------
    str or None
        The selected file path if confirmed, or None if the dialog was
        canceled.

    Examples
    --------
    Get the path to a MATLAB file and visualise the full path, the file name
    and its directory.

    >>> from openhdemg.ui import run_custom_file_dialog
    >>> import os
    >>> filepath = run_custom_file_dialog(
    ...     mode="open",
    ...     filesource="MATLAB",
    ...     filetypes=[("MATLAB files", "*.mat"), ("All files", "*.*")]
    ... )
    >>> if filepath:
    ...     filename = os.path.basename(filepath)
    ...     directory = os.path.dirname(filepath)
    ...     print("Full path:", filepath)
    ...     print("File name:", filename)
    ...     print("Directory:", directory)
    ... else:
    ...     print("No file was selected.")
    """

    # Check if the CustomFileDialog is called from an existing application.
    # If not, create the app (the icon cannot be set in QFileDialog).
    app, app_created, path_to_icon = check_app()

    # Execute the CustomFileDialog in open or save mode
    dialog = CustomFileDialog(
        mode=mode,
        filesource=filesource,
        filetypes=filetypes,
    )
    filepath = dialog.get_filepath()

    return filepath


class CustomDirectoryDialog():
    """
    Custom dialog for selecting a directory.

    It uses QSettings to remember the last accessed directory.

    Check the implementation of ``run_custom_directory_dialog()`` to see how it
    can be used. It is always suggested to call the ``CustomDirectoryDialog``
    from ``run_custom_directory_dialog()`` instead of directly running its
    instance, as this is also managing the ``QApplication``.

    Parameters
    ----------
    window_title : str, default "Select a folder"
        Title of the dialog window. This should guide the user.

    Methods
    -------
    get_directory()
        Get the directory path.

    See also
    --------
    - run_custom_directory_dialog : Opens a custom dialog for selecting a
        directory.
    """

    def __init__(self, window_title="Select a folder"):

        # Class variables
        self.window_title = window_title

        # Setup settings to remember the last directory Same as in CustomFileDialog
        self.settings = QSettings("openhdemg", "library_ui")
        self.last_dir_key = "LastDirectory"

    def get_directory(self, mode="open"):
        """
        Get the directory path.

        Allows selecting an existing directory or typing a new one.
        The new directory is created automatically if needed.

        Parameters
        ----------
        mode : str {"open", "save"}, default "open"
            Determines how the dialog behaves:

            ``open``
                The dialog is used to select an existing directory. The user
                must choose a folder that already exists on the filesystem.

            ``save``
                The dialog additionally allows the user to type a new directory
                name into the text bar. If the typed directory does not exist,
                it will be created automatically after the user confirms.

        Returns
        -------
        str or None
            The selected or created directory path.
        """

        last_dir = self.settings.value(self.last_dir_key, os.getcwd())

        dialog = QFileDialog()
        dialog.setWindowTitle(self.window_title)
        dialog.setFileMode(QFileDialog.Directory)
        dialog.setOption(QFileDialog.ShowDirsOnly, True)

        # If saving, allow to type the new folder name
        if mode == "save":
            dialog.setAcceptMode(QFileDialog.AcceptSave)

        # Set last directory
        dialog.setDirectory(last_dir)

        if dialog.exec():
            dir_path = dialog.selectedFiles()[0]

            # Create directory if it doesn't exist
            if dir_path and not os.path.exists(dir_path):
                try:
                    os.makedirs(dir_path)
                except Exception as e:
                    QMessageBox.critical(
                        None,
                        "Error",
                        f"Could not create directory:\n{dir_path}\n\n{str(e)}",
                    )
                    return None

            # Save for next time
            self.settings.setValue(self.last_dir_key, dir_path)
            return dir_path

        return None


def run_custom_directory_dialog(window_title="Select a folder", mode="open"):
    """
    Opens a custom dialog for selecting a directory, remembering the last
    accessed directory.

    Compared to directly creating a CustomDirectoryDialog instance, this
    function automatically manages the app integration for the user.

    Parameters
    ----------
    window_title : str, default "Select a folder"
        Title of the dialog window. This should guide the user.
    mode : str {"open", "save"}, default "open"
        Determines how the dialog behaves:

        ``open``
            The dialog is used to select an existing directory. The user must
            choose a folder that already exists on the filesystem.

        ``save``
            The dialog additionally allows the user to type a new directory
            name into the text bar. If the typed directory does not exist, it
            will be created automatically after the user confirms.

    Returns
    -------
    str or None
        The selected directory path if confirmed, or None if the dialog was
        canceled.

    Examples
    --------
    Select a directory and print the path:

    >>> from openhdemg.ui import run_custom_directory_dialog
    >>> dirpath = run_custom_directory_dialog(
    ...     window_title="Select the output folder"
    ... )
    >>> if dirpath:
    ...     print("Selected directory:", dirpath)
    ... else:
    ...     print("No directory was selected.")
    """

    # Check if the CustomDirectoryDialog is called from an existing
    # application. If not, create the app (the icon cannot be set in
    # QFileDialog).
    app, app_created, path_to_icon = check_app()

    # Execute the CustomDirectoryDialog in open or save mode
    dialog = CustomDirectoryDialog(window_title=window_title)
    dirpath = dialog.get_directory(mode=mode)

    return dirpath


class VerticalNavigationToolbar2QT(NavigationToolbar2QT):
    """
    A vertical version of the Matplotlib NavigationToolbar2QT.

    Parameters
    ----------
    canvas : matplotlib.backends.backend_qtagg.FigureCanvasQTAgg
        The Matplotlib canvas associated with the toolbar.
    parent : QWidget, optional
        The parent widget for the toolbar. Defaults to None.
    """

    def __init__(self, canvas, parent=None):
        super().__init__(canvas, parent)

        # Create a vertical layout for the toolbar
        self.setOrientation(Qt.Vertical)

    def set_message(self, s):
        """
        Disable the mouse position display in the toolbar.
        """
        pass


class Manual_EMGChannels_Selection_Dialog(QDialog):
    """
    Modal dialog for manual selection of noisy EMG channels.

    The dialog displays stacked EMG channels for visual inspection and
    allows the user to mark channels as valid or invalid using the
    keyboard (keys 1-8). Selected channels are stored in the
    ``GOOD_CHANNELS`` field of the EMG file upon confirmation.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    manual_offset : float, default 0
        Vertical spacing between channels. If 0, an automatic offset is
        computed from signal amplitude.
    path_to_icon : str or None, optional
        Path to a window icon file.
    parent : QWidget or None, optional
        Parent widget.
    """

    def __init__(
        self,
        emgfile,
        manual_offset=0,
        path_to_icon=None,
        parent=None,
    ):
        super().__init__(parent)

        # Setup window
        self.setWindowTitle("Select EMG Channels")
        self.setWindowFlags(
            Qt.Window |
            Qt.WindowMaximizeButtonHint |
            Qt.WindowCloseButtonHint
        )
        self.resize(1200, 800)

        # Manually set icon if requested
        if path_to_icon is not None:
            icon = QIcon(path_to_icon)
            self.setWindowIcon(icon)

        # Make needed variables available
        self.emgfile = copy.deepcopy(emgfile)

        # Additional required variables
        self.visible_count = 8
        self.current_start = 0
        self.n_channels = int(self.emgfile["RAW_SIGNAL"].shape[1])
        self.good_channels = self.emgfile.get("GOOD_CHANNELS", None)
        if self.good_channels is None:
            self.good_channels = {
                int(ch): True for ch in range(self.n_channels)
            }
        else:
            # Convert loaded ch strings to int, then opposite on return
            self.good_channels = {
                int(k): bool(v) for k, v in self.good_channels.items()
            }
        self.raw_emg = None
        self.figure = None
        self.ax = None
        self.lines = None
        self.canvas = None
        self.toolbar = None
        self.plot_layout = None
        self.plot_widget = None
        self.keep_colour = "#1f77b4"
        self.reject_colour = "red"
        self.manual_offset = None
        self.half_offset = None

        # Calculate auto offset if 0 and generate emg array to plot
        self.raw_emg = self.emgfile["RAW_SIGNAL"].to_numpy(
            dtype=np.float64
        )

        if manual_offset == 0:
            self.manual_offset = self._compute_offset(emg_arr=self.raw_emg)
        else:
            self.manual_offset = manual_offset
        self.half_offset = manual_offset / 2

        # X axis (Seconds)
        self.x = np.arange(self.raw_emg.shape[0], dtype=np.float64)
        self.x /= self.emgfile["FSAMP"]

        # Build UI elements
        # --- Plot widget ---
        self.setup_plot_widget()

        # --- Info labels ---
        self.label_channels = QLabel()
        self.label_channels.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: black;"
        )
        self.label_instructions = QLabel(
            f"Press keys 1-{self.visible_count} to toggle channels "
            "(blue = keep, red = remove)"
        )
        self.label_instructions.setStyleSheet(
            "font-size: 12px; color: gray;"
        )

        # Navigation buttons
        btn_prev = QPushButton("← Previous")
        btn_next = QPushButton("Next →")
        btn_prev.clicked.connect(self.show_previous)
        btn_next.clicked.connect(self.show_next)

        nav_layout = QHBoxLayout()
        nav_layout.addWidget(btn_prev)
        nav_layout.addStretch()
        nav_layout.addWidget(btn_next)

        # OK/Cancel
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        # Layout
        layout = QVBoxLayout(self)
        layout.addWidget(self.label_channels)
        layout.addWidget(self.label_instructions)
        layout.addWidget(self.plot_widget)
        layout.addLayout(nav_layout)
        layout.addWidget(button_box)

        # Initial plot
        self.update_chart()

    # -----------------------
    # Plotting / refreshing
    # -----------------------
    def setup_plot_widget(self):
        self.plot_widget = QWidget(self)
        self.plot_layout = QHBoxLayout(self.plot_widget)
        self.plot_layout.setContentsMargins(0, 0, 0, 0)

        # ---- Matplotlib figure / axis ----
        self.figure = Figure(constrained_layout=True)
        self.ax = self.figure.add_subplot(111)

        # Optional: basic cosmetics (safe defaults)
        self.ax.set_xlabel("Time (s)", fontsize=14, labelpad=10)
        self.ax.set_ylabel("Original channels (progressive)", fontsize=14)

        # ---- Pre-allocate placeholder lines ----
        self.lines = []

        for i in range(self.visible_count):
            (line,) = self.ax.plot(
                [], [],
                linewidth=0.5,
                color=self.keep_colour,
                animated=False,
                visible=False,  # hidden until data is assigned
            )
            self.lines.append(line)

        # Set reasonable x/y limits so empty plot doesn't look broken
        self.ax.set_xlim(0, 1)
        self.ax.set_ylim(0, 1)

        # Store the figure in a canvas
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Toolbar
        self.toolbar = VerticalNavigationToolbar2QT(self.canvas)

        # Add to layout
        self.plot_layout.addWidget(self.canvas)
        self.plot_layout.addWidget(self.toolbar, alignment=Qt.AlignHCenter)

    def _current_channels(self):
        # Return the list of channel indices currently displayed.
        end = min(self.current_start + self.visible_count, self.n_channels)
        return list(range(self.current_start, end))

    def update_chart(self):
        # Update line data, colours, and axis labels for the current page.
        channels = self._current_channels()
        n_vis = len(channels)

        # Update each placeholder line
        for i, line in enumerate(self.lines):
            if i < n_vis:
                ch = channels[i]
                y = self.raw_emg[:, ch] + (
                    self.half_offset + self.manual_offset * i
                )

                line.set_data(self.x, y)
                line.set_color(
                    self.keep_colour if self.good_channels[ch] else self.reject_colour
                )
                line.set_visible(True)
            else:
                line.set_visible(False)
                line.set_data([], [])

        # Update axes limits safely
        if n_vis > 0:
            self.ax.set_xlim(float(self.x[0]), float(self.x[-1]))

            # compute y-lims from the *locally stacked* visible signals
            y_visible = np.column_stack([
                self.raw_emg[:, ch] + (
                    self.half_offset + self.manual_offset * i
                )
                for i, ch in enumerate(channels)
            ])
            y_min = float(np.min(y_visible))
            y_max = float(np.max(y_visible))
            pad = 0.05 * (y_max - y_min) if y_max > y_min else 1.0
            self.ax.set_ylim(y_min - pad, y_max + pad)

            # y ticks at local baselines
            yticks = [
                self.half_offset + self.manual_offset * i for i in range(n_vis)
            ]
            yticklabels = [f"{ch} ({i+1})" for i, ch in enumerate(channels)]
            self.ax.set_yticks(yticks)
            self.ax.set_yticklabels(yticklabels)

        else:
            self.ax.set_xlim(0, 1)
            self.ax.set_ylim(0, 1)
            self.ax.set_yticks([])

        # Update label (1-based indices for humans)
        self.label_channels.setText(
            f"Showing channels {self.current_start + 1}-"
            f"{min(self.current_start + self.visible_count, self.n_channels)} "
            f"of {self.n_channels}"
        )

        self.canvas.draw_idle()

    def _update_line_colours(self):
        # Update line colours to reflect the current channel selection.
        channels = self._current_channels()
        for pos, ch in enumerate(channels):
            self.lines[pos].set_color(
                self.keep_colour if self.good_channels[ch] else self.reject_colour
            )

        self.canvas.draw_idle()

    # -----------------------
    # Helpers
    # -----------------------
    def _compute_offset(self, emg_arr):
        # Return a scalar offset used to vertically stack channels.
        ptp = np.ptp(emg_arr, axis=0)
        ptp = ptp[np.isfinite(ptp)]
        ptp = ptp[ptp > 0]

        if ptp.size == 0:
            return 1.0

        offset = float(np.percentile(ptp, 90))  # robust-ish
        if not np.isfinite(offset) or offset <= 0:
            offset = float(np.max(ptp)) if ptp.size else 1.0

        return offset * 1.05  # +5% headroom

    # -----------------------
    # Navigation
    # -----------------------
    def show_next(self):
        if self.current_start + self.visible_count < self.n_channels:
            self.current_start += self.visible_count
            self.update_chart()

    def show_previous(self):
        if self.current_start - self.visible_count >= 0:
            self.current_start -= self.visible_count
            self.update_chart()

    # -----------------------
    # Interaction
    # -----------------------
    def keyPressEvent(self, event):
        key = event.key()

        # Toggle only for keys 1.self.visible_count
        if Qt.Key_1 <= key <= (Qt.Key_1 + self.visible_count - 1):
            idx = key - Qt.Key_1
            channels = self._current_channels()
            # Important for last page with fewer channels
            if idx < len(channels):
                ch = channels[idx]
                self.good_channels[ch] = not self.good_channels[ch]
                self._update_line_colours()
            return

        super().keyPressEvent(event)

    # -----------------------
    # Output
    # -----------------------
    def get_emgfile_with_good_channels(self):
        """
        Return a deepcopy the EMG file with updated GOOD_CHANNELS metadata.

        Channel indices are stored as strings for saving compatibility.
        """
        str_good_chs = {
            str(k): bool(v) for k, v in self.good_channels.items()
        }
        self.emgfile["GOOD_CHANNELS"] = str_good_chs

        return self.emgfile

    # -----------------------
    # Cleanup
    # -----------------------
    def closeEvent(self, event):
        try:
            if self.canvas is not None:
                self.canvas.setParent(None)
                self.canvas.close()
                self.canvas.deleteLater()
                del self.canvas

            if self.toolbar is not None:
                self.toolbar.setParent(None)
                self.toolbar.close()
                self.toolbar.deleteLater()
                del self.toolbar

            if self.figure is not None:
                self.figure.clear()

            del self.plot_layout
            del self.plot_widget

            # Drop refs
            self.lines = None
            self.ax = None
            self.figure = None
            self.canvas = None
            self.toolbar = None
            self.good_channels = None
            self.raw_emg = None
        finally:
            gc.collect()
            super().closeEvent(event)


def run_manual_emgchannels_selection_dialog(emgfile, manual_offset=0):
    """
    Select noisy channels via visual inspection.

    This function opens a modal graphical dialog that allows the user to
    visually inspect stacked EMG channels and mark noisy or unwanted
    channels. Channel selection is performed interactively; the calling
    code is blocked until the dialog is closed.

    Compared to directly creating a Manual_EMGChannels_Selection_Dialog
    instance, this function automatically manages the app integration for
    the user.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    manual_offset : int or float, default 0
        This parameter sets the scaling of the channels. If 0 (default), the
        channels' amplitude is scaled automatically to fit the plotting window.
        If > 0, the channels will be scaled based on the specified value.

    Returns
    -------
    edited_emgfile : dict or None
        The EMG file dictionary with an updated ``"GOOD_CHANNELS"`` entry
        (mapping channel indices as strings to booleans) if the user
        confirms the selection.  
        Returns ``None`` if the dialog is cancelled.

    Examples
    --------
    See emg.select_bad_channels()
    """

    # Check if the Dialog is called from an existing application.
    # If not, create an app and retrieve an icon path for it.
    app, app_created, path_to_icon = check_app()

    dlg = Manual_EMGChannels_Selection_Dialog(
        emgfile=emgfile,
        manual_offset=manual_offset,
        path_to_icon=path_to_icon,
        parent=None,
    )
    if dlg.exec() == QDialog.Accepted:
        emgfile = dlg.get_emgfile_with_good_channels()
        return emgfile
    else:
        return None



# TODO How to test this module?
