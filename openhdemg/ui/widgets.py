"""
This module contains classes (QtWidgets) and functions managing the user
interfaces used by openhdemg.library. These classes or functions can be used
directly or integrated in larger UIs (e.g., MU tracking and conduction
velocity estimation).
"""

import os
import gc
import sys

from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QSettings
from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QMessageBox, QFileDialog,
)

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
        self.v_layout.addWidget(self.canvas)
        self.v_layout.addWidget(self.toolbar)
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

    def get_directory(self):
        """
        Get the directory path.

        If the operation is completed, the directory is memorised for following
        uses.

        Returns
        -------
        str or None
            The selected directory path if confirmed, or None if the dialog was
            canceled.
        """

        last_dir = self.settings.value(self.last_dir_key, os.getcwd())

        dir_path = QFileDialog.getExistingDirectory(
            caption=self.window_title, dir=last_dir,
        )

        if dir_path:
            # Save the directory for next time
            self.settings.setValue(
                self.last_dir_key, dir_path,
            )
            return dir_path
        else:
            return None


def run_custom_directory_dialog(window_title="Select a folder"):
    """
    Opens a custom dialog for selecting a directory, remembering the last
    accessed directory.

    Compared to directly creating a CustomDirectoryDialog instance, this
    function automatically manages the app integration for the user.

    Parameters
    ----------
    window_title : str, default "Select a folder"
        Title of the dialog window. This should guide the user.

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
    dirpath = dialog.get_directory()

    return dirpath

# TODO How to test this module?
