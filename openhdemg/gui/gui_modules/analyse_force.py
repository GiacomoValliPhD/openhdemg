"""Module containing the force analysis GUI"""

from tkinter import ttk, W, E, StringVar
import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
import pandas as pd
import openhdemg.library as openhdemg

class AnalyseForce:
    """
    Class containing the force analysis window for openhdemg
    
    Instance method to open "Force analysis Window".
        Options to analyse force singal are displayed.

        Executed when "Analyse Force" button in master GUI window is pressed.
    """

    def __init__(self, parent):
        self.parent = parent

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
            mvc_df = pd.DataFrame(data=mvc_dic)
            # Display results
            self.parent.display_results(input_df=mvc_df)

        except AttributeError:
            CTkMessagebox(title="Info", message="Make sure a file is loaded.", icon="info",
                          bg_color="#fdbc00", fg_color="LightBlue4", title_color="#000000",
                          button_color="#E5E4E2", button_text_color="#000000", button_hover_color="#1e52fe",
                          font=('Segoe UI',15, 'bold'), text_color="#FFFFFF")

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
            rfd = openhdemg.compute_rfd(emgfile=self.parent.resdict, ms=ms_list)
            # Display results
            self.parent.display_results(input_df=rfd)

        except AttributeError:
            CTkMessagebox(title="Info", message="Make sure a file is loaded.", icon="info",
                          bg_color="#fdbc00", fg_color="LightBlue4", title_color="#000000",
                          button_color="#E5E4E2", button_text_color="#000000", button_hover_color="#1e52fe",
                          font=('Segoe UI',15, 'bold'), text_color="#FFFFFF")