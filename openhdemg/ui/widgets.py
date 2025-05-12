import os
import gc
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QMessageBox,
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
    path_to_icon : str or None
        Path to the openhdemg icon (if a new app was created), or None.
    """

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        app.setStyle('Fusion')

        app_created = True

        master_path = os.path.dirname(os.path.abspath(__file__))
        path_to_icon = os.path.normpath(
            os.path.join(
                master_path,
                "icons",
                "Icon_transp.ico",
            )
        )
    else:
        app_created = False
        path_to_icon = None

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
    used.

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
        if event.inaxes:
            self.last_mouse_pos = [event.xdata, event.ydata]

    def on_key_press(self, event):
        if event.key in ["A", "a"] and self.last_mouse_pos is not None:
            self.points.append(self.last_mouse_pos)
            self.redraw_points()
        elif event.key in ["D", "d"] and self.points:
            self.points.pop()
            self.redraw_points()
        elif event.key == "enter":
            self.close()

    def redraw_points(self):
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

    Select exactly 2 points and print the X coordinates.  # TODO consider if using __init__ or not for ui

    >>> import numpy as np
    >>> from openhdemg.ui import run_point_selector
    >>> signal = np.random.randn(1000)
    >>> selected = run_point_selector(signal, nclic=2)
    >>> print(f"Start: {selected[0][0]}, End: {selected[1][0]}")
    Start: 168.21717572391907, End: 713.5261404204681

    """

    # Check if the point selector is called frpm an existing application.
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

    if app_created:
        app.quit()

    return points


# TODO Fai documentazione su questo nuovo modulo
# TODO elimina deprecated functions da qui e docs