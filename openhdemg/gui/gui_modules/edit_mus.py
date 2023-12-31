"""Module containing the MU Removal GUI class"""

from tkinter import StringVar, W, E
import os
import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
import openhdemg.library as openhdemg

class MURemovalWindow:
    """
    A class for managing the removal of motor units (MUs) in a GUI application.

    This class creates a window that offers options to select and remove specific MUs. 
    It is activated from the main GUI window and is intended to provide functionalities 
    for manipulating motor unit data. The class raises an AttributeError if it is instantiated 
    without a loaded file for analysis.

    Attributes
    ----------
    parent : object
        The parent widget, typically the main application window, to which this MURemovalWindow 
        instance belongs.
    resdict : dict
        A dictionary containing relevant data and settings, including the number of MUs.
    head : CTkToplevel
        The top-level widget for the Motor Unit Removal window.
    mu_to_remove : StringVar
        Tkinter StringVar to store the ID of the motor unit selected for removal.

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
    The class is designed to interact with the data structure provided by the `resdict` 
    attribute, which is expected to contain specific keys and values relevant to the MU analysis.

    """
    def __init__(self, parent, resdict):
        """
        Initialize a new instance of the MURemovalWindow class.

        This method sets up the GUI components for the Motor Unit Removal Window. It includes 
        a dropdown menu to select a motor unit (MU) for removal and buttons to remove either 
        the selected MU or all empty MUs. The method configures and places various widgets such 
        as labels, comboboxes, and buttons in a grid layout for user interaction.

        Parameters
        ----------
        parent : object
            The parent widget, typically the main application window, to which this MURemovalWindow 
            instance belongs. The parent is used for accessing shared resources and data.
        resdict : dict
            A dictionary containing relevant data and settings for the motor unit analysis, 
            including the number of MUs.

        Raises
        ------
        AttributeError
            If certain widgets or properties are not properly instantiated due to missing 
            parent configurations or resources.
        """
        self.parent = parent
        self.resdict = resdict
        # Create new window
        self.head = ctk.CTkToplevel(fg_color="LightBlue4")
        # Set the background color of the top-level window
        self.head.title("Motor Unit Removal Window")
        self.head.wm_iconbitmap()
        self.head.grab_set()

        # Select Motor Unit
        ctk.CTkLabel(self.head, text="Select MU:", font=('Segoe UI',15, 'bold')).grid(
            column=1, row=0, padx=5, pady=5, sticky=W
        )

        self.mu_to_remove = StringVar()
        removed_mu_value = [*range(0, self.parent.resdict["NUMBER_OF_MUS"])]
        removed_mu_value = list(map(str, removed_mu_value))
        removed_mu = ctk.CTkComboBox(
            self.head, width=10, variable=self.mu_to_remove, values=removed_mu_value, state="readonly"
        )
        removed_mu.grid(column=1, row=1, columnspan=2, sticky=(W, E), padx=5, pady=5)

        # Remove Motor unit
        remove = ctk.CTkButton(self.head, text="Remove MU", command=self.remove,
                                fg_color="#E5E4E2", text_color="black", border_color="black", border_width=1)
        remove.grid(column=1, row=2, sticky=(W, E), padx=5, pady=5)

        # Remove empty MUs
        remove_empty = ctk.CTkButton(self.head, text="Remove empty MUs", command=self.remove_empty,
                                      fg_color="#E5E4E2", text_color="black", border_color="black", border_width=1)
        remove_empty.grid(column=2, row=2, padx=5, pady=5)

    def remove(self):
        """
        Instance method that actually removes a selected motor unit based on user specification.

        Executed when button "Remove MU" in Motor Unit Removal Window is pressed.
        The emgfile and the plot are subsequently updated.

        See Also
        --------
        delete_mus in library.
        """
        try:
            # Get resdict with MU removed
            self.parent.resdict = openhdemg.delete_mus(
                emgfile=self.parent.resdict, munumber=int(self.mu_to_remove.get())
            )
            # Upate MU number
            ctk.CTkLabel(self.parent.left, text=str(self.parent.resdict["NUMBER_OF_MUS"]), font=('Segoe UI',15, 'bold')).grid(
                column=2, row=3, sticky=(W, E)
            )

            # Update selection field
            self.mu_to_remove = StringVar()
            removed_mu_value = [*range(0, self.parent.resdict["NUMBER_OF_MUS"])]
            removed_mu_value = list(map(str, removed_mu_value))
            removed_mu = ctk.CTkComboBox(
                self.head, width=10, variable=self.mu_to_remove, values=removed_mu_value
            )
            removed_mu.configure(state="readonly")
            removed_mu.grid(column=1, row=1, columnspan=2, sticky=(W, E), padx=5, pady=5)

            # Update plot
            if hasattr(self.parent, "fig"):
                self.parent.in_gui_plotting(resdict=self.parent.resdict)

        except AttributeError:
            CTkMessagebox(title="Info", message="Make sure a file is loaded.", icon="info",
                          bg_color="#fdbc00", fg_color="LightBlue4", title_color="#000000",
                          button_color="#E5E4E2", button_text_color="#000000", button_hover_color="#1e52fe",
                          font=('Segoe UI',15, 'bold'), text_color="#FFFFFF")
            
    def remove_empty(self):
        """
        Instance method that removes all empty MUs.

        Executed when button "Remove empty MUs" in Motor Unit Removal Window is pressed.
        The emgfile and the plot are subsequently updated.

        See Also
        --------
        delete_empty_mus in library.
        """
        try:
            # Get resdict with MU removed
            self.parent.resdict = openhdemg.delete_empty_mus(self.parent.resdict)

            # Upate MU number
            ctk.Label(self.parent.left, text=str(self.parent.resdict["NUMBER_OF_MUS"]), font=('Segoe UI',15, 'bold')).grid(
                column=2, row=3, sticky=(W, E)
            )

            # Update selection field
            self.mu_to_remove = StringVar()
            removed_mu_value = [*range(0, self.parent.resdict["NUMBER_OF_MUS"])]
            removed_mu_value = list(map(str, removed_mu_value))
            removed_mu = ctk.CTkComboBox(
                self.head, width=10, variable=self.mu_to_remove, values=removed_mu_value
            )
            removed_mu.configure(state="readonly")
            removed_mu.grid(column=1, row=1, columnspan=2, sticky=(W, E), padx=5, pady=5)

            # Update plot
            if hasattr(self.parent, "fig"):
                self.parent.in_gui_plotting(resdict=self.parent.resdict)

        except AttributeError:
            CTkMessagebox(title="Info", message="Make sure a file is loaded.", icon="info",
                          bg_color="#fdbc00", fg_color="LightBlue4", title_color="#000000",
                          button_color="#E5E4E2", button_text_color="#000000", button_hover_color="#1e52fe",
                          font=('Segoe UI',15, 'bold'), text_color="#FFFFFF")