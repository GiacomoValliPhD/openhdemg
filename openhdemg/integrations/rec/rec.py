"""
Temporary interface for selecting a ReC/MEACs or ReC/BAM *_EMG_raw.sig
or *_SIG_raw.sig file (plus an optional GAM auxiliary file) and loading it with
the correct system-specific loader.

"""

import re

from PySide6.QtWidgets import QInputDialog

from openhdemg.integrations.rec.rec_sig.openfiles_rec import emg_from_rec
from openhdemg.ui.widgets import check_app, run_custom_file_dialog


def _ask_gam_channels():
    """
    Prompt the user to type the GAM channel indices to load.

    Shows a small Qt text-input dialog asking for one or more 0-based
    channel indices (0-13), comma-separated.

    Returns
    -------
    list of int or None
        The parsed channel indices, or None if the dialog was canceled
        or left empty (in which case the GAM file is skipped entirely).

    Raises
    ------
    ValueError
        If no integers at all can be found in the entered text.
   
    """

    check_app()

    text, ok = QInputDialog.getText(
        None,
        "ReC GAM channels",
        "Enter the GAM channel indices to load (0-13), comma-separated "
        "(e.g. '4' or '4,7,10'):",
    )

    if not ok or not text.strip():
        return None


    gam_channels = [int(n) for n in re.findall(r"-?\d+", text)]

    if not gam_channels:
        raise ValueError(
            f"\nCould not find any channel indices in '{text}'. Enter "
            "one or more integers, e.g. '4' or '4,7,10'.\n"
        )

    return gam_channels


def _ask_ied(default=10.0):
    """
    Prompt the user for the interelectrode distance (IED) of the matrix.

    Parameters
    ----------
    default : float, default 10.0
        The value shown when the dialog opens, and returned if the
        dialog is canceled or left empty.

    Returns
    -------
    ied : float
        The entered interelectrode distance, in mm.

    Raises
    ------
    ValueError
        If no number can be found in the entered text.

    """

    check_app()

    text, ok = QInputDialog.getText(
        None,
        "ReC interelectrode distance",
        "Interelectrode distance (IED), in mm:",
        text=str(default),
    )

    if not ok or not text.strip():
        return default

    match = re.search(r"-?\d+(?:[.,]\d+)?", text)
    if not match:
        raise ValueError(
            f"\nCould not find a number in '{text}'. Enter the "
            "interelectrode distance in mm, e.g. '10' or '8.5'.\n"
        )

    return float(match.group().replace(",", "."))


def select_and_load_rec_file(gam_channels=None, ied=None):
    """
    Select a *_EMG_raw.sig file (and optionally a GAM file) with
    file dialogs, then load them.

    A first dialog selects the *_EMG_raw.sig or *_SIG_raw.sig file. 
    If ied was not already provided, a second dialog then asks for the 
    interelectrode distance (IED), pre-filled with the default (10 mm), 
    so accepting it as-is just keeps the default. 
    A third dialog is then shown to optionally select a GAM auxiliary file, 
    which can be located in a different folder: 
    if it is canceled, no GAM file is used and REF_SIGNAL is unaffected. 
    If a GAM file is selected and gam_channels was not already provided, 
    a fourth dialog asks which channel indices to load from it.

    The file is loaded with emg_from_rec(), which automatically detects
    whether it comes from a ReC/MEACs or a ReC/BAM system based on the
    system code embedded in the filename, and loads it with the matching
    loader (emg_from_rec_meacs or emg_from_rec_bam).

    Parameters
    ----------
    gam_channels : int or list of int or None, default None
        Passed to emg_from_rec(). 0-based channel indices to extract
        from the GAM file. If None and a GAM file is selected in the
        third dialog, a fourth dialog asks the user to type them instead
        of raising an error. 
    ied : float or None, default None
        Passed to emg_from_rec(). The interelectrode distance, in mm, of
        the matrix used to acquire the selected file. If None, a second
        dialog asks for it (pre-filled with the default, 10 mm). 

    Returns
    -------
    emgfile : dict or None
        The loaded emgfile, or None if the first dialog (EMG file) was
        canceled.

    See also
    --------
    - emg_from_rec : Generic loader dispatching to emg_from_rec_meacs or
        emg_from_rec_bam based on the filename.

    Examples
    --------
    >>> from openhdemg.integrations.rec.rec import select_and_load_rec_file
    >>> emgfile = select_and_load_rec_file()
    """
    filepath = run_custom_file_dialog(
        mode="open",
        filesource="EMG REC",
        filetypes=[
            ("ReC/MEACS and ReC/BAM EMG files", "*_EMG_raw.sig *_SIG_raw.sig"),
            ("All files", "*.*"),
        ],
    )

    if not filepath:
        return None

    if ied is None:
        ied = _ask_ied()

    gam_filepath = run_custom_file_dialog(
        mode="open",
        filesource="AUX GAM file (optional, cancel to skip)",
        filetypes=[
            ("ReC GAM auxiliary files", "*_AUX_raw.sig"),
            ("All files", "*.*"),
        ],
    )

    if gam_filepath and gam_channels is None:
        gam_channels = _ask_gam_channels()
        if gam_channels is None:
            # Canceled or left empty: skip the GAM file entirely.
            gam_filepath = None

    return emg_from_rec(
        filepath=filepath,
        ied=ied,
        gam_filepath=gam_filepath if gam_filepath else None,
        gam_channels=gam_channels,
    )


if __name__ == "__main__":
    # Quick manual run: select the files and print a short summary.
    emgfile = select_and_load_rec_file()

    if emgfile is not None:
        print("SOURCE:", emgfile["SOURCE"])
        print("FILENAME:", emgfile["FILENAME"])
        print("RAW_SIGNAL shape:", emgfile["RAW_SIGNAL"].shape)
        print("REF_SIGNAL shape:", emgfile["REF_SIGNAL"].shape)
    else:
        print("No file was selected.")
