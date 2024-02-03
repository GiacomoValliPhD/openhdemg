"""Module that contains all helper functions for the GUI"""

from tkinter import W, E, filedialog
import customtkinter as ctk
import pandas as pd

import openhdemg.library as openhdemg
from openhdemg.gui.gui_modules.error_handler import show_error_dialog


class GUIHelpers:
    """
    A utility class to provide additional functionalities in an openhdemg GUI application.

    This class includes helper functions to enhance user interaction with the application, 
    such as resizing files based on user input. It is designed to work in conjunction with 
    the main GUI components and relies on the parent widget for accessing shared data and resources.

    Attributes
    ----------
    parent : object
        The parent widget, typically the main application window, to which this GUIHelpers 
        instance belongs.

    Methods
    -------
    __init__(self, parent)
        Initialize a new instance of the GUIHelpers class.
    resize_file(self)
        Resize the EMG file based on user-defined areas selected in the GUI plot.
    export_to_excel(self)
        Save an analaysis dataframe to a csv file. 
    sort_mus(self)
        Sort motor units according to recriuitement order.
    
    Examples
    --------
    >>> main_window = Tk()
    >>> gui_helpers = GUIHelpers(main_window)
    # Usage of gui_helpers methods as required

    Raises
    ------
    AttributeError
        When no file is loaded prior to analysis or certain operations are attempted 
        without the necessary context or data.

    Notes
    -----
    The class's methods interact with other components of the openhdemg application, 
    such as file handling and plotting utilities, and are dependent on the state of the 
    parent widget.

    """

    def __init__(self, parent):
        """
        Initialize a new instance of the GUIHelpers class.

        Sets up a reference to the parent widget, which is used for accessing shared 
        resources and functionalities within the application.

        Parameters
        ----------
        parent : object
            The parent widget, usually the main application window, which provides 
            necessary context and data for the helper functions.

        """
        self.parent = parent

    def resize_file(self):
        """
        Instance method to get resize area from user specification on plot and
        resize emgfile.

        Executed when button "Select Resize" is pressed in Resize file window.
        The emgfile and the GUI plot are updated.

        Raises
        ------
        AttributeError
            When no file is loaded prior to analysis.

        See Also
        --------
        showselect, resize_emgfile in library.
        """
        try:
            # Open selection window for user
            points = openhdemg.showselect(
                emgfile=self.parent.resdict,
                title="Select the start/end area to resize by hovering the mouse\nand pressing the 'a'-key. Wrong points can be removed with right click.\nWhen ready, press enter.",
                titlesize=10,
            )
            start, end = points[0], points[1]

            # Delsys requires different handling for resize
            if self.parent.resdict["SOURCE"] == "DELSYS":
                self.parent.resdict, _, _ = openhdemg.resize_emgfile(
                emgfile=self.parent.resdict, area=[start, end], accuracy="maintain"
                )
            else:
                self.parent.resdict, _, _ = openhdemg.resize_emgfile(
                    emgfile=self.parent.resdict, area=[start, end]
                )
            # Update Plot
            self.parent.in_gui_plotting(resdict=self.parent.resdict)

            # Update filelength
            ctk.CTkLabel(self.parent.left, text=str(self.parent.resdict["EMG_LENGTH"]), font=('Segoe UI',12)).grid(
                    column=2, row=4, sticky=(W, E)
            )

        except AttributeError as e:
            show_error_dialog(parent=self, error=e, solution=str("Make sure a file is loaded."))

    def export_to_excel(self):
        """
        Instnace method to export any prior analysis results. Results are saved in an excel sheet
        in a directory specified by the user.

        Executed when button "Save Results" in master GUI window is pressed.

        Raises
        ------
        IndexError
            When no analysis has been performed prior to attempted savig.
        AttributeError
            When no file was loaded in the GUI.
        """
        try:
            # Ask user to select the directory
            path = filedialog.askdirectory()

            # Define excel writer
            writer = pd.ExcelWriter(path + "/Results_" + self.parent.filename + ".xlsx")

            # Check for attributes and write sheets
            if hasattr(self.parent, "mvc_df"):
                self.parent.mvc_df.to_excel(writer, sheet_name="MVC")

            if hasattr(self.parent, "rfd"): 
                self.parent.rfd.to_excel(writer, sheet_name="RFD")

            if hasattr(self.parent, "exportable_df"):
                self.parent.mu_prop_df.to_excel(writer, sheet_name="Basic MU Properties")

            if hasattr(self.parent, "mus_dr"):
                self.parent.mus_dr.to_excel(writer, sheet_name="MU Discharge Rate")

            if hasattr(self.parent, "mu_thresholds"):
                self.mu_thresholds.to_excel(writer, sheet_name="MU Thresholds")

            writer.close()

        except IndexError as e:
            show_error_dialog(parent=self, error=e, solution=str("Please conduct at least one analysis before saving."))

        except AttributeError as e:
            show_error_dialog(parent=self, error=e, solution=str("Make sure a file is loaded."))

        except PermissionError as e:
            show_error_dialog(parent=self, error=e, solution=str("If /Results.xlsx already opened, please close."))

    def sort_mus(self):
        """
        Instance method to sort motor units ascending according to recruitement order.

        Executed when button "Sort MUs" in master GUI window is pressed. The plot of the MUs
        and the emgfile are subsequently updated.

        Raises
        ------
        AttributeError
            When no file was loaded in the GUI.

        See Also
        --------
        sort_mus in library.
        """
        try:
            # Sort emgfile
            self.parent.resdict = openhdemg.sort_mus(emgfile=self.parent.resdict)

            # Update plot
            if hasattr(self.parent, "fig"):
                self.parent.in_gui_plotting(resdict=self.parent.resdict)

        except AttributeError as e:
            show_error_dialog(parent=self, error=e, solution=str("Make sure a file is loaded."))

        except KeyError:
            show_error_dialog(parent=self, error=e,
                              solution=str("Sorting not possible when ≤ 1"
                                    + "\nMU is present in the File (i.e. Refsigs)"))
    