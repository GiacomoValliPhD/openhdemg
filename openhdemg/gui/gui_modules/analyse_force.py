"""Module containing the force analysis GUI"""

from tkinter import ttk, W, E, StringVar
import customtkinter as ctk
import pandas as pd
import openhdemg.library as openhdemg
from openhdemg.gui.gui_modules.error_handler import show_error_dialog


class AnalyseForce:
    """
    A class for conducting force analysis in an openhdemg GUI application.

    This class provides a window for analyzing force signals. It includes functionalities 
    for calculating Maximum Voluntary Contraction (MVC) and Rate of Force Development (RFD). 
    The class is activated through the "Analyse Force" button in the main GUI window.

    Attributes
    ----------
    parent : object
        The parent widget, typically the main application window, to which this AnalyseForce 
        instance belongs.
    head : CTkToplevel
        The top-level widget for the Force Analysis window.
    rfdms : StringVar
        Tkinter StringVar to store the milliseconds value for Rate of Force Development (RFD) analysis.

    Methods
    -------
    __init__(self, parent)
        Initialize a new instance of the AnalyseForce class.
    get_mvc(self)
        Calculate and display the Maximum Voluntary Contraction (MVC).
    get_rfd(self)
        Calculate and display the Rate of Force Development (RFD) over specified milliseconds.
    
    Examples
    --------
    >>> main_window = Tk()
    >>> force_analysis = AnalyseForce(main_window)
    >>> force_analysis.head.mainloop()

    Notes
    -----
    The class is designed to be a part of a larger GUI application and interacts with force 
    signal data accessible via the `parent` widget.
    """

    def __init__(self, parent):
        """
        Initialize a new instance of the AnalyseForce class.

        This method sets up the GUI components for the Force Analysis Window. It includes buttons 
        for calculating MVC and RFD, and an entry field for specifying RFD milliseconds. The method 
        configures and places various widgets such as labels, buttons, and entry fields in a grid 
        layout for user interaction.

        Parameters
        ----------
        parent : object
            The parent widget, typically the main application window, to which this AnalyseForce 
            instance belongs. The parent is used for accessing shared resources and data.

        Raises
        ------
        AttributeError
            If certain widgets or properties are not properly instantiated due to missing 
            parent configurations or resources.

        """
        # Initialize parent and load parent settings 
        
        self.parent = parent
        self.parent.load_settings()
        
        # Create new window
        self.head = ctk.CTkToplevel(fg_color="LightBlue4")
        self.head.title("Force Analysis Window")
        self.head.wm_iconbitmap()
        self.head.grab_set()

        # Get MVC
        get_mvf = ctk.CTkButton(self.head, text="Get MVC", command=self.get_mvc,
                                fg_color="#E5E4E2", text_color="black", border_color="black", border_width=1)
        get_mvf.grid(column=0, row=1, sticky=(W, E), padx=5, pady=5)

        # Get RFD
        separator1 = ttk.Separator(self.head, orient="horizontal")
        separator1.grid(column=0, columnspan=3, row=2, sticky=(W, E), padx=5, pady=5)

        ctk.CTkLabel(self.head, text="RFD miliseconds", font=('Segoe UI',15, 'bold')).grid(
            column=1, row=3, sticky=(W, E), padx=5, pady=5
        )

        get_rfd = ctk.CTkButton(self.head, text="Get RFD", command=self.get_rfd,
                                fg_color="#E5E4E2", text_color="black", border_color="black", border_width=1)
        get_rfd.grid(column=0, row=4, sticky=(W, E), padx=5, pady=5)

        self.rfdms = StringVar()
        milisecond = ctk.CTkEntry(self.head, width=100, textvariable=self.rfdms)
        milisecond.grid(column=1, row=4, sticky=(W, E), padx=5, pady=5)
        self.rfdms.set("50,100,150,200")

    ### Define functions for force analysis

    def get_mvc(self):
        """
        Instance methof to retrieve calculated MVC based on user selection.

        Executed when button "Get MVC" in Analyze Force window is pressed.
        The Results of the analysis are displayed in the results terminal.

        Raises
        ------
        AttributeError
            When no file is loaded prior to analysis.

        See Also
        --------
        get_mvc in the library
        """
        try:
            # get MVC
            mvc = openhdemg.get_mvc(emgfile=self.parent.resdict)
            # Define dictionary for pandas
            mvc_dic = {"MVC": [mvc]}
            self.parent.mvc_df = pd.DataFrame(data=mvc_dic)
            # Display results
            self.parent.display_results(input_df=self.parent.mvc_df)

        except AttributeError as e:
            show_error_dialog(parent=self, error=e, solution=str("Make sure a file is loaded."))

    def get_rfd(self):
        """
        Instance method to calculate RFD at specified timepoints based on user selection.

        Executed when button "Get RFD" in Analyze Force window is pressed.
        The Results of the analysis are displayed in the results terminal.

        Raises
        ------
        AttributeError
            When no file is loaded prior to analysis.

        See Also
        --------
        get_rfd in library
        """
        try:
            # Define list for RFD computation
            ms = str(self.rfdms.get())
            # Split the string at ,
            ms_list = ms.split(",")
            # Use comprehension to iterate through
            ms_list = [int(i) for i in ms_list]
            # Calculate rfd
            self.parent.rfd = openhdemg.compute_rfd(emgfile=self.parent.resdict, ms=ms_list)
            # Display results
            self.parent.display_results(input_df=self.parent.rfd)

        except AttributeError as e:
            show_error_dialog(parent=self, error=e, solution=str("Make sure a file is loaded."))
