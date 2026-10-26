"""Interactive BSS motor-unit editor."""

import gc
import copy

import numpy as np
import matplotlib.ticker as ticker
from matplotlib.figure import Figure
from matplotlib.widgets import RectangleSelector
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QCheckBox, QDialog, QHBoxLayout, QLabel, QMessageBox, QSizePolicy,
    QVBoxLayout, QWidget,
)

from openhdemg.ui.qt_matplotlib import (
    check_app, close_and_delete_widget, release_canvas_figure,
)


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
        self._cleaned_up = False

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
        Return the edited EMG file and MU indexes marked for deletion.
        """

        if self.edited_emgfile is None:
            raise RuntimeError(
                "The editor results are unavailable or were already retrieved."
            )

        edited_emgfile = self.edited_emgfile
        mus_to_delete = sorted(self.mus_to_delete)
        return edited_emgfile, mus_to_delete

    # -----------------------
    # Cleanup
    # -----------------------
    def cleanup(self, preserve_results=False):
        """Release all memory-intensive Matplotlib, Qt, and EMG references."""

        if self._cleaned_up:
            if not preserve_results:
                self.edited_emgfile = None
                self.mus_to_delete = set()
            return
        self._cleaned_up = True

        canvas = getattr(self, "canvas", None)

        selector = getattr(self, "rect_selector", None)
        if selector is not None:
            try:
                selector.disconnect()
            except (AttributeError, RuntimeError):
                pass
        self.rect_selector = None

        if canvas is not None:
            for callback_id in self.connected_mpl_events.values():
                try:
                    canvas.mpl_disconnect(callback_id)
                except (AttributeError, RuntimeError):
                    pass

        checkbox = getattr(self, "checkbox_delete", None)
        if checkbox is not None:
            try:
                checkbox.toggled.disconnect(
                    self._on_delete_checkbox_toggled
                )
            except (RuntimeError, TypeError):
                pass

        for line_name in (
            "refsig_line",
            "idr_line",
            "ipts_line",
            "ipts_mrkr_line",
        ):
            line = getattr(self, line_name, None)
            if line is not None:
                try:
                    line.set_data([], [])
                except (AttributeError, RuntimeError):
                    pass

        release_canvas_figure(canvas)
        close_and_delete_widget(canvas)

        self.connected_mpl_events = {}
        self.figure = None
        self.canvas = None
        self.ax_idr = None
        self.ax_ipts = None
        self.refsig_line = None
        self.idr_line = None
        self.ipts_line = None
        self.ipts_mrkr_line = None
        self.e_w_sig = None
        self.x_samples = None
        self.np_refs = None
        self.label_mu = None
        self.checkbox_delete = None
        self.status_label = None
        self.active_mode = None

        if not preserve_results:
            self.edited_emgfile = None
            self.mus_to_delete = set()

        gc.collect()

    def done(self, result):
        """Release working buffers whenever the modal editor closes."""

        try:
            super().done(result)
        finally:
            self.cleanup(preserve_results=True)


def run_bss_mu_editor(
    emgfile,
    e_w_sig,
    refsig_channel,
    ipts_transform="s*abs(s)",
    parent=None,
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
    parent : QWidget or None, default None
        Optional Qt parent used when embedding the editor.

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

    _app, _, path_to_icon = check_app()

    dialog = BSS_MU_Editor(
        emgfile=emgfile,
        e_w_sig=e_w_sig,
        refsig_channel=refsig_channel,
        ipts_transform=ipts_transform,
        path_to_icon=path_to_icon,
        parent=parent,
    )
    try:
        dialog.exec()
        return dialog.get_results()
    finally:
        dialog.cleanup()
        dialog.setParent(None)
        dialog.deleteLater()
        gc.collect()
