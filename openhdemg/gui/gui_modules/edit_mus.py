"""Module containing the MU Removal GUI class"""

from tkinter import StringVar, W, E
import os
from sys import platform
import customtkinter as ctk
import openhdemg.library as openhdemg
from openhdemg.gui.gui_modules.error_handler import show_error_dialog


class MURemovalWindow:
    """
    A class for managing the removal of motor units (MUs) in a GUI application.

    This class creates a window that offers options to select and remove
    specific MUs. It is activated from the main GUI window and is intended to
    provide functionalities for manipulating motor unit data. The class raises
    an AttributeError if it is instantiated without a loaded file for analysis.

    Attributes
    ----------
    parent : object
        The parent widget, typically the main application window, to which
        this MURemovalWindow instance belongs.
    resdict : dict
        A dictionary containing relevant data and settings, including the
        number of MUs.
    head : CTkToplevel
        The top-level widget for the Motor Unit Removal window.
    mu_to_remove : StringVar
        Tkinter StringVar to store the ID of the motor unit selected for
        removal.

    Methods
    -------
    __init__(self, parent, resdict)
        Initialize a new instance of the MURemovalWindow class.
    remove(self)
        Remove the selected motor unit from the analysis.
    remove_empty(self)
        Remove all motor units that are empty or have no data.

    Examples
    --------
    >>> main_window = Tk()
    >>> resdict = {"NUMBER_OF_MUS": 10}  # Example resdict
    >>> mu_removal_window = MURemovalWindow(main_window, resdict)
    >>> mu_removal_window.head.mainloop()

    Raises
    ------
    AttributeError
        When no file is loaded prior to analysis.

    Notes
    -----
    The class is designed to interact with the data structure provided by the
    `resdict` attribute, which is expected to contain specific keys and values
    relevant to the MU analysis.
    """

    def __init__(self, parent):
        """
        Initialize a new instance of the MURemovalWindow class.

        This method sets up the GUI components for the Motor Unit Removal
        Window. It includes a dropdown menu to select a motor unit (MU) for
        removal and buttons to remove either the selected MU or all empty MUs.
        The method configures and places various widgets such as labels,
        comboboxes, and buttons in a grid layout for user interaction.

        Parameters
        ----------
        parent : object
            The parent widget, typically the main application window, to which
            this MURemovalWindow instance belongs. The parent is used for
            accessing shared resources and data.

        Raises
        ------
        AttributeError
            If certain widgets or properties are not properly instantiated due
            to missing parent configurations or resources.
        """

        try:
            # Initialize parent and load parent settings
            self.parent = parent
            self.parent.load_settings()

            # Create new window
            self.head = ctk.CTkToplevel()
            # Set the background color of the top-level window
            self.head.title("Motor Unit Removal Window")

            # Set the icon for the window
            head_path = os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            )
            iconpath = head_path + "/gui_files/Icon_transp.ico"
            self.head.iconbitmap(default=iconpath)
            if platform.startswith("win"):
                self.head.after(200, lambda: self.head.iconbitmap(iconpath))

            self.head.grab_set()

            # Set resizable window
            # Configure columns with a loop
            for col in range(3):
                self.head.columnconfigure(col, weight=1)

            # Configure rows with a loop
            for row in range(10):
                self.head.rowconfigure(row, weight=1)

            # Select Motor Unit
            ctk.CTkLabel(
                self.head, text="Select MU:", font=("Segoe UI", 15, "bold")
            ).grid(column=1, row=0, padx=5, pady=5, sticky=W)

            self.mu_to_remove = StringVar()
            removed_mu_value = [*range(0, self.parent.resdict["NUMBER_OF_MUS"])]
            removed_mu_value = list(map(str, removed_mu_value))
            removed_mu = ctk.CTkComboBox(
                self.head,
                width=10,
                variable=self.mu_to_remove,
                values=removed_mu_value,
                state="readonly",
            )
            removed_mu.grid(
                column=1, row=1, columnspan=2, sticky=(W, E), padx=5, pady=5
            )

            # Remove Motor unit
            remove = ctk.CTkButton(
                self.head,
                text="Remove MU",
                command=self.remove,
            )
            remove.grid(column=1, row=2, sticky=(W, E), padx=5, pady=5)

            # Remove empty MUs
            remove_empty = ctk.CTkButton(
                self.head,
                text="Remove empty MUs",
                command=self.remove_empty,
            )
            remove_empty.grid(column=2, row=2, padx=5, pady=5)

        except AttributeError as e:
            self.head.destroy()
            show_error_dialog(
                parent=self, error=e,
                solution=str("Make sure a file is loaded."),
            )

    def remove(self):
        """
        Instance method that actually removes a selected motor unit based on
        user specification.

        Executed when button "Remove MU" in Motor Unit Removal Window is
        pressed. The emgfile and the plot are subsequently updated.

        See Also
        --------
        delete_mus in library.
        """

        try:
            # Get resdict with MU removed
            self.parent.resdict = openhdemg.delete_mus(
                emgfile=self.parent.resdict,
                munumber=int(self.mu_to_remove.get()),
            )
            # Upate MU number
            self.parent.n_of_mus.configure(
                text="N of MUs: " + str(self.parent.resdict["NUMBER_OF_MUS"]),
                font=("Segoe UI", 15, "bold"),
            )

            # Update selection field
            self.mu_to_remove = StringVar()
            removed_mu_value = [*range(0, self.parent.resdict["NUMBER_OF_MUS"])]
            removed_mu_value = list(map(str, removed_mu_value))
            removed_mu = ctk.CTkComboBox(
                self.head, width=10, variable=self.mu_to_remove,
                values=removed_mu_value,
            )
            removed_mu.configure(state="readonly")
            removed_mu.grid(
                column=1, row=1, columnspan=2, sticky=(W, E), padx=5, pady=5
            )

            # Update plot
            if hasattr(self.parent, "fig"):
                self.parent.in_gui_plotting(resdict=self.parent.resdict)

        except AttributeError as e:
            show_error_dialog(
                parent=self, error=e,
                solution=str("Make sure a file is loaded."),
            )

    def remove_empty(self):
        """
        Instance method that removes all empty MUs.

        Executed when button "Remove empty MUs" in Motor Unit Removal Window
        is pressed. The emgfile and the plot are subsequently updated.

        See Also
        --------
        delete_empty_mus in library.
        """

        try:
            # Get resdict with MU removed
            self.parent.resdict = openhdemg.delete_empty_mus(
                self.parent.resdict,
            )

            # Upate MU number
            self.parent.n_of_mus.configure(
                text="N of MUs: " + str(self.parent.resdict["NUMBER_OF_MUS"]),
                font=("Segoe UI", 15, "bold"),
            )
            # Update selection field
            self.mu_to_remove = StringVar()
            removed_mu_value = [*range(0, self.parent.resdict["NUMBER_OF_MUS"])]
            removed_mu_value = list(map(str, removed_mu_value))
            removed_mu = ctk.CTkComboBox(
                self.head, width=10, variable=self.mu_to_remove,
                values=removed_mu_value,
            )
            removed_mu.configure(state="readonly")
            removed_mu.grid(
                column=1, row=1, columnspan=2, sticky=(W, E), padx=5, pady=5
            )

            # Update plot
            if hasattr(self.parent, "fig"):
                self.parent.in_gui_plotting(resdict=self.parent.resdict)

        except AttributeError as e:
            show_error_dialog(
                parent=self, error=e,
                solution=str("Make sure a file is loaded."),
            )
