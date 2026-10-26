"""Shared Qt and Matplotlib lifecycle utilities.
"""

import os
import sys

from PySide6.QtCore import QEventLoop
from PySide6.QtWidgets import QApplication


def check_app():
    """
    Return the active QApplication, creation state, and default icon path.
    """

    path_to_icon = os.path.normpath(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "icons",
            "Icon_transp.ico",
        )
    )

    app = QApplication.instance()
    app_created = app is None
    if app_created:
        app = QApplication(sys.argv)
        app.setStyle("Fusion")

    return app, app_created, path_to_icon


def disconnect_navigation_toolbar(toolbar):
    """
    Disconnect Matplotlib callbacks and break toolbar/canvas references.

    Release the canvas widget lock before detaching an active pan or zoom
    toolbar. Otherwise, a replacement toolbar on the same persistent canvas
    cannot acquire the lock and its navigation tools remain unavailable.
    """

    if toolbar is None:
        return

    canvas = getattr(toolbar, "canvas", None)
    figure = getattr(canvas, "figure", None)

    if canvas is not None:
        widgetlock = getattr(canvas, "widgetlock", None)
        if widgetlock is not None:
            try:
                if widgetlock.isowner(toolbar):
                    widgetlock.release(toolbar)
            except (AttributeError, RuntimeError, ValueError):
                pass

    if figure is not None:
        for axes in figure.get_axes():
            try:
                axes.set_navigate_mode(None)
            except (AttributeError, RuntimeError):
                pass

        pan_info = getattr(toolbar, "_pan_info", None)
        if pan_info is not None:
            for axes in getattr(pan_info, "axes", ()):
                try:
                    axes.end_pan()
                except (AttributeError, RuntimeError):
                    pass

        zoom_info = getattr(toolbar, "_zoom_info", None)
        if zoom_info is not None:
            try:
                toolbar.remove_rubberband()
            except (AttributeError, RuntimeError):
                pass

        callback_ids = (
            getattr(toolbar, "_id_press", None),
            getattr(toolbar, "_id_release", None),
            getattr(toolbar, "_id_drag", None),
            getattr(getattr(toolbar, "_pan_info", None), "cid", None),
            getattr(getattr(toolbar, "_zoom_info", None), "cid", None),
        )
        for callback_id in callback_ids:
            if callback_id is not None:
                try:
                    canvas.mpl_disconnect(callback_id)
                except (AttributeError, RuntimeError):
                    pass

    if hasattr(toolbar, "_pan_info"):
        toolbar._pan_info = None
    if hasattr(toolbar, "_zoom_info"):
        toolbar._zoom_info = None

    nav_stack = getattr(toolbar, "_nav_stack", None)
    if nav_stack is not None:
        try:
            nav_stack.clear()
        except (AttributeError, RuntimeError):
            pass

    if canvas is not None and getattr(canvas, "toolbar", None) is toolbar:
        canvas.toolbar = None
    toolbar.canvas = None


def release_canvas_figure(canvas, *, release_toolbar=True):
    """
    Detach and clear the Figure and renderer retained by a QtAgg canvas.

    Set ``release_toolbar`` to ``False`` when the canvas will be reused with
    another Figure. Final widget teardown should keep the default so no
    canvas/toolbar ownership cycle survives.
    """

    if canvas is None:
        return

    figure = getattr(canvas, "figure", None)
    if figure is not None:
        try:
            figure.clear()
        except (AttributeError, RuntimeError):
            pass
        try:
            figure.set_canvas(None)
        except (AttributeError, RuntimeError):
            pass

    canvas.figure = None
    if release_toolbar:
        canvas.toolbar = None

    # A draw_idle() QTimer may run after the widget has been deleted.
    if hasattr(canvas, "_draw_pending"):
        canvas._draw_pending = False

    # FigureCanvasAgg owns its renderer buffer independently of the Figure.
    if hasattr(canvas, "renderer"):
        canvas.renderer = None
        canvas._lastKey = None


def set_canvas_figure(canvas, figure):
    """Attach a Figure to an existing QtAgg canvas and schedule a redraw."""

    release_canvas_figure(canvas, release_toolbar=False)
    canvas.figure = figure
    figure.set_canvas(canvas)
    canvas._draw_pending = False

    # Match Figure dimensions to the persistent widget as a new canvas would.
    try:
        pixel_ratio = canvas.device_pixel_ratio
        width = max(canvas.width() * pixel_ratio, 1)
        height = max(canvas.height() * pixel_ratio, 1)
        figure.set_size_inches(
            width / figure.dpi,
            height / figure.dpi,
            forward=False,
        )
    except (AttributeError, RuntimeError, TypeError, ValueError):
        pass

    canvas.draw_idle()


def close_and_delete_widget(
    widget,
    layout=None,
    *,
    disconnect_toolbar=False,
    release_figure=False,
):
    """Remove, close, and schedule deletion of a Qt widget."""

    if widget is None:
        return

    if disconnect_toolbar:
        disconnect_navigation_toolbar(widget)
    if release_figure:
        release_canvas_figure(widget)

    if layout is not None:
        try:
            layout.removeWidget(widget)
        except RuntimeError:
            pass

    try:
        widget.close()
        widget.setParent(None)
        widget.deleteLater()
    except RuntimeError:
        pass


def run_window_blocking(window, closed_signal):
    """Show a window and block in a local event loop until it closes."""

    event_loop = QEventLoop()
    closed_signal.connect(event_loop.quit)
    window.destroyed.connect(event_loop.quit)

    try:
        window.show()
        event_loop.exec()
    finally:
        try:
            closed_signal.disconnect(event_loop.quit)
        except (RuntimeError, TypeError):
            pass

    return window
