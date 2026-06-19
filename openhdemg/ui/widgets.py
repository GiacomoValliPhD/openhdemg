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

from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QSettings
from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QMessageBox, QFileDialog,
    QLabel, QPushButton, QDialogButtonBox, QSizePolicy, QWidget, QCheckBox
)

import numpy as np
import matplotlib
import matplotlib.ticker as ticker
from matplotlib.figure import Figure
from matplotlib.widgets import RectangleSelector
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


class _CustomRectangleSelector:
    """
    RectangleSelector wrapper used by BSS_MU_Editor.
    """

    def __init__(self, ax, canvas, on_select):
        self.ax = ax
        self.canvas = canvas
        self.on_select = on_select

        properties = {
            "edgecolor": "black",
            "linewidth": 1,
            "alpha": 1,
            "fill": False,
        }

        self.selector = RectangleSelector(
            ax,
            self._callback,
            useblit=True,
            props=properties,
            button=1,
            minspanx=0.1,
            minspany=0,
            spancoords="data",
            interactive=False,
            use_data_coordinates=True,
        )

    def _callback(self, eclick, erelease):
        if None in (eclick.xdata, eclick.ydata, erelease.xdata, erelease.ydata):
            return

        x1, x2 = sorted((eclick.xdata, erelease.xdata))
        y1, y2 = sorted((eclick.ydata, erelease.ydata))
        self.on_select([(x1, y1), (x2, y2)])

    def deactivate(self):
        if self.selector.visible:
            self.selector.set_visible(False)

        self.selector.set_active(False)
        self.canvas.draw_idle()

    def disconnect(self):
        self.selector.disconnect_events()


class BSS_MU_Editor(QDialog):
    """
    Portable modal UI for cleaning MU discharge selections obtained via
    convolutive blind source separation.

    Prefer calling this widget through ``run_bss_mu_editor()``
    instead of instantiating it directly. The runner handles the Qt application
    setup and returns the edited EMG file together with the MU indexes marked
    for deletion.

    !!! note "Advanced MU cleaning"
        Please note that the most advanced MU cleaning tools are available in
        the openhdemg software. You can find it at:

            https://www.giacomovalli.com/openhdemg_software/

    This UI allows to:

    - visually inspect the blind source separation discharge time selection.
    - visually inspect the source separation.
    - to add and delete firings.
    - mark MUs to delete.
    - update the separation filter based on the manually selected discharge
    times.

    All the actions can be performed using the following shortcuts:

    - A: Toggle rectangular add mode. Samples of the selected IPTS trace inside
        the rectangle are added to the current MU discharge times.
    - D: Toggle rectangular delete mode. Current MU discharge times inside the
        rectangle are removed.
    - W: Recompute the current MU filter and IPTS from the current discharge
        times.
    - E: Reset the current plot view.
    - Shift+Right or Shift+Left: Move to the next or previous MU.
    - Mouse wheel: Zoom in or out on the time axis around the cursor.

    !!! note "Updated variables"
        This UI updates only the manually edited discharge information. In
        particular, it can update ``MUPULSES`` when firings are added or
        removed, and ``IPTS`` when the W command recomputes the current MU
        source. It does not delete MUs marked with the checkbox, and it does
        not finalise derived fields such as SIL/ACCURACY or
        ``BINARY_MUS_FIRING`` after MU deletion. Those operations should be
        handled by the calling script, for example with the openhdemg library
        functions. For examples, see ``run_bss_mu_editor()``.

    Parameters
    ----------
    emgfile : dict
        Decomposed openhdemg file.
    e_w_sig : array-like
        Already filtered, extended, and whitened EMG signal with shape
        ``(features, samples)``. It is used directly by the W command.
    refsig_channel : int or str
        Reference signal channel to plot behind the discharge rate trace.
    ipts_transform : {"None", "s*abs(s)"}, default "s*abs(s)"
        Non-linear transformation applied to the source recomputed with W.
    path_to_icon : str or None, default None
        Optional window icon path.
    parent : QWidget or None, default None
        Parent widget.
    """

    def __init__(
        self,
        emgfile,
        e_w_sig,
        refsig_channel,
        ipts_transform="s*abs(s)",
        path_to_icon=None,
        parent=None,
    ):
        super().__init__(parent)

        self.setWindowTitle("MU Discharge Cleaner")
        self.setWindowFlags(
            Qt.Window |
            Qt.WindowMinimizeButtonHint |
            Qt.WindowMaximizeButtonHint |
            Qt.WindowCloseButtonHint
        )
        self.resize(1200, 800)

        if path_to_icon is not None:
            self.setWindowIcon(QIcon(path_to_icon))

        self.edited_emgfile = copy.deepcopy(emgfile)
        self.e_w_sig = np.asarray(e_w_sig, dtype=np.float64)
        self.refsig_channel = refsig_channel
        self.ipts_transform = ipts_transform
        self.emg_length = int(self.edited_emgfile["EMG_LENGTH"])
        self.n_mus = int(self.edited_emgfile["NUMBER_OF_MUS"])

        self.figure = None
        self.canvas = None
        self.ax_idr = None
        self.ax_ipts = None
        self.refsig_line = None
        self.idr_line = None
        self.ipts_line = None
        self.ipts_mrkr_line = None
        self.label_mu = None
        self.checkbox_delete = None
        self.status_label = None
        self.rect_selector = None
        self.active_mode = None
        self.connected_mpl_events = {}
        self.current_mu = 0
        self.mus_to_delete = set()

        self.x_samples = np.arange(self.emg_length, dtype=np.float64)
        self.np_refs = self.edited_emgfile["REF_SIGNAL"][
            self.refsig_channel
        ].to_numpy(dtype=np.float64)

        self._create_central_figure()
        command_bar = self._create_command_bar()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(command_bar)
        layout.addWidget(self.canvas)
        layout.addWidget(self.status_label)

        self._connect_mpl_events()
        self._set_current_mu(0)

    # -----------------------
    # Setup helpers
    # -----------------------
    def _create_central_figure(self):
        self.figure = Figure(figsize=(16, 9), constrained_layout=True)
        self.ax_ipts = self.figure.add_subplot(2, 1, 2, sharex=None)
        self.ax_idr = self.figure.add_subplot(2, 1, 1, sharex=self.ax_ipts)

        self.refsig_line, = self.ax_idr.plot(
            [],
            [],
            color="#8C8C8C",
            linewidth=0.8,
        )
        self.idr_line, = self.ax_idr.plot(
            [],
            [],
            "o",
            color="tab:orange",
            markersize=4,
        )
        self.ax_idr.set_ylabel("Discharge Rate (pps)")
        self.ax_idr.tick_params(
            axis="x", which="both", bottom=False, labelbottom=False
        )

        self.ipts_line, = self.ax_ipts.plot(
            [],
            [],
            color="tab:blue",
            linewidth=0.5,
        )
        self.ipts_mrkr_line, = self.ax_ipts.plot(
            [],
            [],
            "o",
            color="tab:orange",
            markersize=4,
        )
        self.ax_ipts.set_ylabel("Pulse Train (au)")
        self.ax_ipts.set_xlabel("Time (s)")
        self.ax_ipts.xaxis.set_major_formatter(
            ticker.FuncFormatter(self._format_seconds)
        )

        self.ax_idr.set_ylim((0, 1))
        self.ax_ipts.set_ylim((0, 1))
        self.x_limits = (0, max(1, self.emg_length))
        self.ipts_limits = (0, 1)
        self.ax_ipts.set_xlim(self.x_limits)

        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setFocusPolicy(Qt.StrongFocus)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def _create_command_bar(self):
        container = QWidget(self)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        self.label_mu = QLabel()
        self.label_mu.setTextFormat(Qt.PlainText)
        self.checkbox_delete = QCheckBox("Mark MU for deletion")
        self.checkbox_delete.toggled.connect(
            self._on_delete_checkbox_toggled
        )
        software_label = QLabel(
            '<b>Need faster, advanced MU cleaning?</b> '
            'The openhdemg software includes the most advanced cleaning UI: '
            '<a href="https://www.giacomovalli.com/openhdemg_software/">'
            'get the openhdemg software</a> '
        )
        software_label.setTextFormat(Qt.RichText)
        software_label.setOpenExternalLinks(True)
        software_label.setStyleSheet(
            "QLabel {"
            "font-weight: 500;"
            "color: #3A2A12;"
            "}"
        )
        self.status_label = QLabel("Active command: none")
        self.status_label.setTextFormat(Qt.PlainText)
        self.status_label.setStyleSheet(
            "padding: 6px; border-top: 1px solid #D0D0D0; color: #333333;"
        )

        layout.addWidget(self.label_mu)
        layout.addSpacing(16)
        layout.addWidget(self.checkbox_delete)
        layout.addStretch()
        layout.addWidget(software_label)

        return container

    def _connect_mpl_events(self):
        self.connected_mpl_events["scroll_event_id"] = self.canvas.mpl_connect(
            "scroll_event", self._mouse_zoom
        )
        self.connected_mpl_events["key_press_event_id"] = (
            self.canvas.mpl_connect("key_press_event", self._key_event_manager)
        )
        self.canvas.setFocus()

    # -----------------------
    # Data helpers
    # -----------------------
    def _format_seconds(self, x, pos):
        del pos
        return f"{round(x / self.edited_emgfile['FSAMP'], 1)}"

    def _get_ipts(self, mu):
        return self.edited_emgfile["IPTS"][mu].to_numpy()

    def _set_ipts(self, mu, source):
        self.edited_emgfile["IPTS"][mu] = source

    def _get_mupulses(self, mu):
        return self.edited_emgfile["MUPULSES"][mu]

    def _set_mupulses(self, mu, mupulses):
        self.edited_emgfile["MUPULSES"][mu] = mupulses

    def _align_source_length(self, source):
        source = np.asarray(source, dtype=np.float64).ravel()
        if len(source) == self.emg_length:
            return source
        if len(source) > self.emg_length:
            return source[:self.emg_length]

        padded = np.zeros(self.emg_length, dtype=np.float64)
        padded[:len(source)] = source
        return padded

    # -----------------------
    # Plotting
    # -----------------------
    def plot_mu(self, mu, reset_lims="True"):
        if self.n_mus < 1:
            self._reset_empty_figure()
            return

        ipts = self._get_ipts(mu)
        mupulses = self._get_mupulses(mu)

        idr = self._fast_idr(mupulses)
        self.idr_line.set_data(mupulses, idr)

        finite_idr = np.asarray(idr, dtype=np.float64)
        finite_idr = finite_idr[np.isfinite(finite_idr)]
        max_idr = float(np.max(finite_idr)) if finite_idr.size else 1.0
        if max_idr <= 0:
            max_idr = 1.0
        self.refsig_line.set_data(self.x_samples, self._scaled_refsig(max_idr))
        self.ax_idr.set_ylim(-1e-6, max_idr * 1.05 + 1e-6)

        self.ipts_line.set_data(self.x_samples, ipts)
        self.ipts_mrkr_line.set_data(mupulses, ipts[mupulses])

        if reset_lims in ("True", True):
            self.x_limits = (-1, len(ipts) + 1)
            self.ipts_limits = self._ipts_limits(ipts)
            self.ax_ipts.set_xlim(self.x_limits)
            self.ax_ipts.set_ylim(self.ipts_limits)
        elif reset_lims in ("Y", "y"):
            self.ipts_limits = self._ipts_limits(ipts)
            self.ax_ipts.set_ylim(self.ipts_limits)
        elif reset_lims in ("False", False):
            pass
        else:
            raise ValueError("reset_lims can be 'True', 'False' or 'Y'")

        self._apply_deletion_visual_state(mu)
        self.canvas.draw_idle()
        self.canvas.setFocus()

    def _set_current_mu(self, mu):
        if self.n_mus < 1:
            self._reset_empty_figure()
            return

        self.current_mu = min(max(int(mu), 0), self.n_mus - 1)
        self._update_mu_label()
        self.plot_mu(self.current_mu)

    def _update_mu_label(self):
        if self.checkbox_delete is not None:
            signals_blocked = self.checkbox_delete.blockSignals(True)
            self.checkbox_delete.setChecked(
                self.current_mu in self.mus_to_delete
            )
            self.checkbox_delete.blockSignals(signals_blocked)

        if self.current_mu in self.mus_to_delete:
            self.label_mu.setText(f"MU number: {self.current_mu}")
            self.label_mu.setStyleSheet(
                "font-weight: bold; color: #B00020;"
            )
            return

        self.label_mu.setText(f"MU number: {self.current_mu}")
        self.label_mu.setStyleSheet("font-weight: bold; color: black;")

    def _apply_deletion_visual_state(self, mu):
        is_marked = mu in self.mus_to_delete
        facecolor = "#FFF0F0" if is_marked else "white"
        self.ax_idr.set_facecolor(facecolor)
        self.ax_ipts.set_facecolor(facecolor)

    def _reset_empty_figure(self):
        self.refsig_line.set_data([], [])
        self.idr_line.set_data([], [])
        self.ipts_line.set_data([], [])
        self.ipts_mrkr_line.set_data([], [])
        self.ax_idr.set_ylim((0, 1))
        self.ax_ipts.set_ylim((0, 1))
        self.x_limits = (0, max(1, self.emg_length))
        self.ipts_limits = (0, 1)
        self.ax_ipts.set_xlim(self.x_limits)
        if self.label_mu is not None:
            self.label_mu.setText("No MUs available")
        self._set_active_command(None)
        self.canvas.draw_idle()

    def _fast_idr(self, mupulses):
        if len(mupulses) == 0:
            return np.array([], dtype=np.float64)
        if len(mupulses) > 2:
            return self.edited_emgfile["FSAMP"] / np.diff(
                mupulses, prepend=np.nan
            )
        return np.zeros(len(mupulses), dtype=np.float64)

    def _scaled_refsig(self, max_idr):
        refs = np.asarray(self.np_refs, dtype=np.float64)
        ref_min = float(np.nanmin(refs)) if refs.size else 0.0
        ref_max = float(np.nanmax(refs)) if refs.size else 0.0
        if ref_max == ref_min:
            return np.zeros_like(refs)
        return (refs - ref_min) / (ref_max - ref_min) * max_idr

    def _ipts_limits(self, ipts):
        finite_ipts = np.asarray(ipts, dtype=np.float64)
        finite_ipts = finite_ipts[np.isfinite(finite_ipts)]
        if finite_ipts.size == 0:
            return (0, 1)

        max_ipts = float(np.max(finite_ipts))
        min_ipts = -abs(max_ipts) * 0.001

        pad = abs(max_ipts) * 0.05 + 1e-6
        if max_ipts <= min_ipts:
            max_ipts = min_ipts + 1

        return (min_ipts - 1e-6, max_ipts + pad)

    # -----------------------
    # Interaction
    # -----------------------
    def _key_event_manager(self, event):
        if event.key is None:
            return

        key = event.key.lower()

        if key == "a":
            self._toggle_selector("add")
        elif key == "d":
            self._toggle_selector("delete")
        elif key == "w":
            self._set_active_command("update filter")
            self.update_filter()
            self._set_active_command(None)
        elif key == "e":
            self.reset_view()
        elif key == "shift+right":
            self._move_mu(1)
        elif key == "shift+left":
            self._move_mu(-1)

    def _toggle_selector(self, mode):
        if self.active_mode == mode:
            self._clear_selector()
            return

        self._clear_selector()
        self.active_mode = mode

        if mode == "add":
            callback = self._add_firings
            label = "add firings"
        elif mode == "delete":
            callback = self._delete_firings
            label = "delete firings"
        else:
            return

        self.rect_selector = _CustomRectangleSelector(
            ax=self.ax_ipts,
            canvas=self.canvas,
            on_select=callback,
        )
        self._set_active_command(label)

    def _clear_selector(self):
        if self.rect_selector is not None:
            self.rect_selector.deactivate()
            self.rect_selector.disconnect()
            self.rect_selector = None
        self.active_mode = None
        self._set_active_command(None)

    def _set_active_command(self, command):
        if command is None:
            self.status_label.setText("Active command: none")
        else:
            self.status_label.setText(f"Active command: {command}")

    def _mouse_zoom(self, event):
        if event.inaxes not in (self.ax_ipts, self.ax_idr):
            return

        cur_xlim = self.ax_ipts.get_xlim()
        xdata = event.xdata
        if xdata is None:
            xdata = cur_xlim[0] + (cur_xlim[1] - cur_xlim[0]) / 2

        zoom_scale_factor = 1.3
        if event.button == "up":
            x_scale = 1 / zoom_scale_factor
        elif event.button == "down":
            x_scale = zoom_scale_factor
        else:
            return

        new_width = (cur_xlim[1] - cur_xlim[0]) * x_scale
        relx = (cur_xlim[1] - xdata) / (cur_xlim[1] - cur_xlim[0])

        x_min = xdata - new_width * (1 - relx)
        x_max = xdata + new_width * relx
        lim_min, lim_max = self.x_limits

        if x_min < lim_min:
            x_max += lim_min - x_min
            x_min = lim_min
        if x_max > lim_max:
            x_min -= x_max - lim_max
            x_max = lim_max

        x_min = max(x_min, lim_min)
        x_max = min(x_max, lim_max)

        if x_max - x_min > 9:
            self.ax_ipts.set_xlim([x_min, x_max])
            self.canvas.draw_idle()

    def reset_view(self):
        self.plot_mu(self.current_mu, reset_lims="True")

    def _move_mu(self, direction):
        new_mu = self.current_mu + direction
        if 0 <= new_mu < self.n_mus:
            self._set_current_mu(new_mu)

    def _on_delete_checkbox_toggled(self, checked):
        mu = self.current_mu
        if checked:
            self.mus_to_delete.add(mu)
            self._set_active_command(f"marked MU {mu} for deletion")
        else:
            self.mus_to_delete.discard(mu)
            self._set_active_command(f"unmarked MU {mu} for deletion")

        self._update_mu_label()
        self.plot_mu(mu, reset_lims="False")

    def _add_firings(self, selection):
        try:
            mu = self.current_mu
            selected = self._samples_in_selection(mu, selection)
            if selected.size > 0:
                mupulses = self._get_mupulses(mu)
                ipts = self._get_ipts(mu)
                merged = np.union1d(mupulses, selected)
                merged = self._remove_close_firings(merged, ipts)
                self._set_mupulses(mu, merged)
                self.plot_mu(mu, reset_lims="False")
        finally:
            self._clear_selector()

    def _delete_firings(self, selection):
        try:
            mu = self.current_mu
            selected = self._mupulses_in_selection(mu, selection)
            if selected.size > 0:
                mupulses = self._get_mupulses(mu)
                self._set_mupulses(mu, np.setdiff1d(mupulses, selected))
                self.plot_mu(mu, reset_lims="False")
        finally:
            self._clear_selector()

    def _samples_in_selection(self, mu, selection):
        ipts = self._get_ipts(mu)
        (x1, y1), (x2, y2) = selection
        start = max(0, int(np.ceil(x1)))
        stop = min(len(ipts) - 1, int(np.floor(x2)))
        if stop < start:
            return np.array([], dtype=np.int64)

        samples = np.arange(start, stop + 1, dtype=np.int64)
        selected = samples[(ipts[samples] >= y1) & (ipts[samples] <= y2)]
        return selected

    def _remove_close_firings(self, mupulses, ipts):
        mupulses = np.sort(mupulses)
        if len(mupulses) < 2:
            return mupulses

        cleaned = []
        group = [mupulses[0]]
        for pulse in mupulses[1:]:
            if pulse - group[-1] <= 1:
                group.append(pulse)
            else:
                cleaned.append(self._highest_ipts_sample(group, ipts))
                group = [pulse]
        cleaned.append(self._highest_ipts_sample(group, ipts))

        return np.asarray(cleaned)

    def _highest_ipts_sample(self, samples, ipts):
        samples = np.asarray(samples)
        return samples[np.argmax(ipts[samples])]

    def _mupulses_in_selection(self, mu, selection):
        ipts = self._get_ipts(mu)
        mupulses = self._get_mupulses(mu)
        (x1, y1), (x2, y2) = selection
        selected = mupulses[
            (mupulses >= x1) &
            (mupulses <= x2) &
            (ipts[mupulses] >= y1) &
            (ipts[mupulses] <= y2)
        ]
        return selected

    def update_filter(self):
        mu = self.current_mu
        mupulses = self._get_mupulses(mu)
        if len(mupulses) == 0:
            QMessageBox.warning(
                self,
                "Filter update unavailable",
                "The current MU has no discharge times.",
            )
            return

        try:
            mu_filter = self._compute_mu_filter(mupulses)
            source = mu_filter.T @ self.e_w_sig
            source = np.asarray(source, dtype=np.float64).ravel()

            if self.ipts_transform == "s*abs(s)":
                source = source * np.abs(source)

            source = self._align_source_length(source)
            self._set_ipts(mu, source)
            mupulses = mupulses[source[mupulses] >= 0]
            self._set_mupulses(mu, mupulses)
            self.plot_mu(mu, reset_lims="Y")
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Filter update failed",
                f"Error updating MU filter: {exc}",
            )

    def _compute_mu_filter(self, mupulses):
        if np.max(mupulses) >= self.e_w_sig.shape[1]:
            raise ValueError(
                "MUPULSES contain sample indexes outside e_w_sig axis 1."
            )

        return np.mean(self.e_w_sig[:, mupulses], axis=1)

    # -----------------------
    # Output
    # -----------------------
    def get_results(self):
        """
        Return the edited EMG file and original MU indexes marked for deletion.
        """
        return self.edited_emgfile, sorted(self.mus_to_delete)


def run_bss_mu_editor(
    emgfile,
    e_w_sig,
    refsig_channel,
    ipts_transform="s*abs(s)",
):
    """
    Open a portable modal UI for cleaning MU discharge selections obtained via
    convolutive blind source separation.

    Close the window to return the edited EMG file. The caller is responsible
    for finalising and saving the returned object.

    !!! note "Advanced MU cleaning"
        Please note that the most advanced MU cleaning tools are available in
        the openhdemg software. You can find it at:

            https://www.giacomovalli.com/openhdemg_software/

    This UI allows to:

    - visually inspect the blind source separation discharge time selection.
    - visually inspect the source separation.
    - to add and delete firings.
    - mark MUs to delete.
    - update the separation filter based on the manually selected discharge
    times.

    All the actions can be performed using the following shortcuts:

    - A: Toggle rectangular add mode. Samples of the selected IPTS trace inside
        the rectangle are added to the current MU discharge times.
    - D: Toggle rectangular delete mode. Current MU discharge times inside the
        rectangle are removed.
    - W: Recompute the current MU filter and IPTS from the current discharge
        times.
    - E: Reset the current plot view.
    - Shift+Right or Shift+Left: Move to the next or previous MU.
    - Mouse wheel: Zoom in or out on the time axis around the cursor.

    !!! note "Updated variables"
        This UI updates only the manually edited discharge information. In
        particular, it can update ``MUPULSES`` when firings are added or
        removed, and ``IPTS`` when the W command recomputes the current MU
        source. It does not delete MUs marked with the checkbox, and it does
        not finalise derived fields such as SIL/ACCURACY or
        ``BINARY_MUS_FIRING`` after MU deletion. Those operations should be
        handled by the calling script, for example with the openhdemg library
        functions. For examples, see ``run_bss_mu_editor()``.

    Parameters
    ----------
    emgfile : dict
        Decomposed openhdemg file.
    e_w_sig : array-like
        Already filtered, extended, and whitened EMG signal with shape
        ``(features, samples)``. It is used directly by the W command.
    refsig_channel : int or str
        Reference signal channel to plot behind the discharge rate trace.
    ipts_transform : {"None", "s*abs(s)"}, default "s*abs(s)"
        Non-linear transformation applied to the source recomputed with W.

    Returns
    -------
    edited_emgfile : dict
        The cleaned EMG file.
    mus_to_delete : list of int
        Original MU indexes marked for deletion. Delete them using
        ``delete_mus``.

    Examples
    --------
    Prepare the preprocessed, extended, centered, and whitened signal in the
    calling script, then open the cleaning UI.

    Import needed modules

    >>> import numpy as np
    >>> import pandas as pd
    >>> import openhdemg.library as emg
    >>> from openhdemg.ui import run_bss_mu_editor

    Load openhdemg module decomposed using EMGDecomposer

    >>> emgfile = emg.askloadmodule()

    Extract needed decomposition parameters

    >>> decomp_params = emgfile["DECOMPOSITION_PARAMETERS"]
    >>> extension_factor = int(decomp_params["extension_factor"])
    >>> eigenvalue_percentile = float(decomp_params["eigenvalue_percentile"])

    Rebuild the same signal used by the decomposition preprocessing pipeline.
    The prepared signal will only be used for cleaning and will not update the
    original emgfile.

    >>> working_emgfile = emgfile
    >>> bandpass_params = decomp_params["bandpass_filtering"]
    >>> if bandpass_params["enabled"] is True:
    ...     working_emgfile = emg.filter_rawemg(
    ...         emgfile=working_emgfile,
    ...         order=bandpass_params["order"],
    ...         lowcut=bandpass_params["lowcut"],
    ...         highcut=bandpass_params["highcut"],
    ...     )

    Extract the EMG signal and store it as an array with channels as rows,
    samples as columns.

    >>> emg_sig = working_emgfile["RAW_SIGNAL"].to_numpy(dtype=np.float64).T

    Apply power-line harmonics removal when it was used during decomposition.

    >>> powerline_params = decomp_params["powerline_harmonics"]
    >>> if powerline_params["enabled"] is True:
    ...     emg_sig = emg.remove_powerline_harmonics(
    ...         sig=emg_sig,
    ...         fsamp=emgfile["FSAMP"],
    ...         notch_freq=powerline_params["notch_freq"],
    ...         notch_width=powerline_params["notch_width"],
    ...     )

    Remove bad channels when this was used during decomposition.

    >>> if decomp_params["exclude_bad_channels"] is True:
    ...     good_channels = emgfile.get("GOOD_CHANNELS", None)
    ...     if good_channels is not None:
    ...         good_idx = sorted(
    ...             int(ch) for ch, ok in good_channels.items() if ok
    ...         )
    ...         emg_sig = emg_sig[good_idx, :]

    Prepare the extended, centered, and whitened signal.

    >>> e_sig = emg.extend_emg_signal(
    ...     sig=emg_sig,
    ...     ext_fact=extension_factor,
    ... )
    >>> e_sig = e_sig - np.mean(e_sig, axis=1, keepdims=True)
    >>> e_w_sig = emg.svd_whitening(
    ...     e_sig=e_sig,
    ...     eigenvalue_percentile=eigenvalue_percentile,
    ... )

    Align with the original sample indexes used by MUPULSES/IPTS.

    >>> e_w_sig = np.pad(
    ...     e_w_sig,
    ...     ((0, 0), (extension_factor, 0)),
    ...     mode="constant",
    ...     constant_values=0,
    ... )

    Start the editor

    >>> edited_emgfile, mus_to_delete = run_bss_mu_editor(
    ...     emgfile=emgfile,
    ...     e_w_sig=e_w_sig,
    ...     refsig_channel=0,
    ... )

    ![](md_graphics/docstrings/widgets/discharge_editor_ex_1.png)

    Once editing is completed, delete MUs marked in the UI

    >>> if mus_to_delete:
    ...     edited_emgfile = emg.delete_mus(
    ...         edited_emgfile,
    ...         munumber=mus_to_delete,
    ...         if_single_mu="remove",
    ...     )

    Also check for duplicate MUs that might have emerged from manual editing,
    if duplicate removal is enabled in the decomposition metadata.

    >>> duplicate_params = decomp_params["duplicate_removal"]
    >>> if duplicate_params["enabled"] is True:
    ...     edited_emgfile = emg.remove_duplicates_within(
    ...         emgfile=edited_emgfile,
    ...         correlation_max_lag=duplicate_params["correlation_max_lag"],
    ...         peak_window_half_width=duplicate_params["peak_window_half_width"],
    ...         duplicate_threshold=duplicate_params["duplicate_threshold"],
    ...         which=duplicate_params["which"],
    ...     )

    Recalculate SIL for all remaining MUs.

    >>> sil_values = []
    >>> for mu in range(edited_emgfile["NUMBER_OF_MUS"]):
    ...     sil = emg.compute_sil(
    ...         ipts=edited_emgfile["IPTS"][mu],
    ...         mupulses=edited_emgfile["MUPULSES"][mu],
    ...         compute_on_peaks_only=True,
    ...     )
    ...     sil_values.append(sil)
    >>> edited_emgfile["ACCURACY"] = pd.DataFrame(sil_values)

    Recalculate binary MU firings.

    >>> edited_emgfile["BINARY_MUS_FIRING"] = emg.create_binary_firings(
    ...     emg_length=edited_emgfile["EMG_LENGTH"],
    ...     number_of_mus=edited_emgfile["NUMBER_OF_MUS"],
    ...     mupulses=edited_emgfile["MUPULSES"],
    ... )

    Standardise emgfile dtypes

    >>> edited_emgfile = emg.standardise_emgfile_dtypes(emgfile=edited_emgfile)

    Save the cleaned emgfile

    >>> emg.asksavemodule(emgfile=edited_emgfile)
    """

    app, app_created, path_to_icon = check_app()

    dialog = BSS_MU_Editor(
        emgfile=emgfile,
        e_w_sig=e_w_sig,
        refsig_channel=refsig_channel,
        ipts_transform=ipts_transform,
        path_to_icon=path_to_icon,
        parent=None,
    )
    dialog.exec()

    return dialog.get_results()


# TODO How to test this module?
