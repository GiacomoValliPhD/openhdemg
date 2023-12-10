"""Module that contains all helper functions for the GUI"""

from tkinter import W, E
import customtkinter as ctk
from CTkMessagebox import CTkMessagebox

import openhdemg.library as openhdemg

class GUIHelpers:
    """
    """
    def __init__(self, parent):
        self.parent=parent

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

        except AttributeError:
            CTkMessagebox(title="Info", message="Make sure a file is loaded.", icon="info",
                          bg_color="#fdbc00", fg_color="LightBlue4", title_color="#000000",
                          button_color="#E5E4E2", button_text_color="#000000", button_hover_color="#1e52fe",
                          font=('Segoe UI',15, 'bold'), text_color="#FFFFFF")
