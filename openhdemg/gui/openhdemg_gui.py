"""
This file contains the gui functionalities of openhdemg.
"""

import os
import sys
import subprocess
import importlib

import tkinter as tk
import threading
import webbrowser
from tkinter import messagebox, ttk, filedialog, Canvas, StringVar, Tk, N, S, W, E
import customtkinter as ctk
from pandastable import Table, config

from PIL import Image

import matplotlib.pyplot as plt
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

import openhdemg.library as openhdemg
import openhdemg.gui.settings as settings
from openhdemg.gui.gui_modules import (
    MURemovalWindow,
    EditRefsig,
    GUIHelpers,
    AnalyseForce,
    MuAnalysis,
    PlotEmg,
    AdvancedAnalysis,
    show_error_dialog,
)


matplotlib.use("TkAgg")


class emgGUI:
    """
     This class is used to create a graphical user interface for
     the openhdemg library.

     Within this class and corresponding childs, most functionalities
     of the ophdemg library are packed in a GUI. Howebver, the library is more
     comprehensive and much more adaptable to the users needs.

     Attributes
     ----------
     self.canvas : matplotlib.backends.backend_tkagg
         Canvas for plotting figures inside the GUI.
     self.channels : int or list
         The channel (int) or channels (list of int) to plot.
         The list can be passed as a manually-written with: "0,1,2,3,4,5...,n",
         channels is expected to be with base 0.
     self.fig : matplotlib.figure
         Figure to be plotted on Canvas.
     self.filename : str
         String and name of the file to be analysed.
     self.filepath : str
         String containing the path to EMG file selected for analysis.
     self.filetype : str
         String containing the filetype of import EMG file.
         Filetype can be "OPENHDEMG", "OTB", "DEMUSE", "OTB_REFSIG", "CUSTOMCSV", "CUSTOMCSV_REFSIG".
     self.left : tk.frame
         Left frame inside of master that contains all buttons and filespecs.
    self.logo :
         String containing the path to image file containing logo of openhdemg.
     self.logo_canvas : tk.canvas
         Canvas to display logo of Open_HG-EMG when openend.
     self.master: tk
         TK master window containing all widget children for this GUI.
     self.resdict : dict
         Dictionary derived from input EMG file for further analysis.
     self.right : tk.frame
         Left frame inside of master that contains plotting canvas.
     self.terminal : ttk.Labelframe
         Tkinter labelframe that is used to display the results table in the GUI.
     self.info : tk.PhotoImage
         Information Icon displayed in GUI.
     self.online : tk.Photoimage
         Online Icon displayed in GUI.
     self.redirect : tk.PhotoImage
         Redirection Icon displayed in GUI.
     self.contact : tk.PhotoImage
         Contact Icon displayed in GUI.
     self.cite : tk.PhotoImage
         Citation Icon displayed in GUI.
     self.otb_combobox : ttk.Combobox
         Combobox appearing in main GUI window or advanced
         analysis window when OTB files are loaded. Contains
         the extension factor for OTB files.
         Stringvariable containing the
     self.extension_factor : tk.StringVar()
         Stringvariable containing the OTB extension factor value.

     Methods
     -------
     __init__(master)
         Initializes GUI class and main GUI window (master).
     get_file_input()
         Gets emgfile location and respective file is loaded.
         Executed when button "Load File" in master GUI window pressed.
     save_emgfile()
         Saves the edited emgfile dictionary to a .json file.
         Executed when button "Save File" in master GUI window pressed.
     reset_analysis()
         Resets the whole analysis, restores the original input file and the graph.
         Executed when button "Reset analysis" in master GUI window pressed.
     in_gui_plotting()
         Method used for creating plot inside the GUI (on the GUI canvas).
         Executed when button "View MUs" in master GUI window pressed.
     mu_analysis()
         Opens seperate window to calculated specific motor unit properties.
         Executed when button "MU properties" in master GUI window pressed.
     display_results()
         Method used to display result table containing analysis results.

     Notes
     -----
     Please note that altough we created a GUI class, the included methods/
     instances are highly specific. We did not conceptualize the methods/instances
     to be used seperately. Similar functionalities are available in the library
     and were specifically coded to be used seperately/singularly.

     Most instance methods of this class heavily rely on the functions provided in
     the library. In the section "See Also" at each instance method, the reader is
     referred to the corresponding function and extensive documentation in the library.
    """

    def __init__(self, master):
        """
        Initialization of master GUI window upon calling.

        Parameters
        ----------
        master: tk
            tk class object
        """
        # Load settings
        self.load_settings()

        # Set up GUI
        self.master = master
        self.master.title("openhdemg")
        master_path = os.path.dirname(os.path.abspath(__file__))
        iconpath = master_path + "/gui_files/Icon.ico"
        self.master.iconbitmap(iconpath)

        # Necessary for resizing
        self.master.columnconfigure(0, weight=1)
        self.master.columnconfigure(1, weight=1)
        self.master.rowconfigure(0, weight=1)

        # Create left side framing for functionalities
        self.left = ctk.CTkFrame(
            self.master, fg_color=self.settings.background_color, corner_radius=0
        )
        self.left.grid(column=0, row=0, sticky=(N, S, E, W))

        # Configure columns with a loop
        for col in range(3):
            self.left.columnconfigure(col, weight=1)

        # Configure rows with a loop
        for row in range(21):
            self.left.rowconfigure(row, weight=1)

        # Specify filetype
        self.filetype = StringVar()
        signal_value = [
            "OPENHDEMG",
            "DEMUSE",
            "OTB",
            "OTB_REFSIG",
            "DELSYS",
            "DELSYS_REFSIG",
            "CUSTOMCSV",
            "CUSTOMCSV_REFSIG",
        ]
        signal_entry = ctk.CTkComboBox(
            self.left,
            width=150,
            variable=self.filetype,
            values=signal_value,
            state="readonly",
        )
        signal_entry.grid(column=0, row=1, sticky=(N, S, E, W))
        self.filetype.set("Type of file")
        # Trace filetype to apply function when changeing
        self.filetype.trace_add("write", self.on_filetype_change)

        # Load file
        load = ctk.CTkButton(
            self.left,
            text="Load File",
            command=self.get_file_input,
            fg_color="#E5E4E2",
            text_color="black",
            border_color="black",
            border_width=1,
        )
        load.grid(column=0, row=3, sticky=(N, S, E, W))

        # File specifications
        ctk.CTkLabel(self.left, text="Filespecs:", font=("Segoe UI", 15, "bold")).grid(
            column=1, row=1, sticky=(W)
        )
        ctk.CTkLabel(self.left, text="N Channels:", font=("Segoe UI", 15, "bold")).grid(
            column=1, row=2, sticky=(W)
        )
        ctk.CTkLabel(self.left, text="N of MUs:", font=("Segoe UI", 15, "bold")).grid(
            column=1, row=3, sticky=(W)
        )
        ctk.CTkLabel(
            self.left, text="File length:", font=("Segoe UI", 15, "bold")
        ).grid(column=1, row=4, sticky=(W))
        separator0 = ttk.Separator(self.left, orient="horizontal")
        separator0.grid(column=0, columnspan=3, row=5, sticky=(E, W))

        # Save File
        save = ctk.CTkButton(
            self.left,
            text="Save File",
            command=self.save_emgfile,
            fg_color="#E5E4E2",
            text_color="black",
            border_color="black",
            border_width=1,
        )
        save.grid(column=0, row=6, sticky=(N, S, E, W))
        separator1 = ttk.Separator(self.left, orient="horizontal")
        separator1.grid(column=0, columnspan=3, row=7, sticky=(E, W))

        # Export to Excel
        export = ctk.CTkButton(
            self.left,
            text="Save Results",
            command=lambda: (GUIHelpers(parent=self).export_to_excel()),
            fg_color="#E5E4E2",
            text_color="black",
            border_color="black",
            border_width=1,
        )
        export.grid(column=1, row=6, sticky=(N, S, E, W))

        # View Motor Unit Firings
        firings = ctk.CTkButton(
            self.left,
            text="View MUs",
            command=lambda: (self.in_gui_plotting(resdict=self.resdict)),
            fg_color="#E5E4E2",
            text_color="black",
            border_color="black",
            border_width=1,
        )
        firings.grid(column=0, row=8, sticky=(N, S, E, W))

        # Sort Motor Units
        sorting = ctk.CTkButton(
            self.left,
            text="Sort MUs",
            command=lambda: (GUIHelpers(parent=self).sort_mus()),
            fg_color="#E5E4E2",
            text_color="black",
            border_color="black",
            border_width=1,
        )
        sorting.grid(column=1, row=8, sticky=(N, S, E, W))
        separator2 = ttk.Separator(self.left, orient="horizontal")
        separator2.grid(column=0, columnspan=3, row=9, sticky=(E, W))

        # Remove Motor Units
        remove_mus = ctk.CTkButton(
            self.left,
            text="Remove MUs",
            command=lambda: (MURemovalWindow(parent=self)),
            fg_color="#E5E4E2",
            text_color="black",
            border_color="black",
            border_width=1,
        )
        remove_mus.grid(column=0, row=10, sticky=(N, S, E, W))

        separator3 = ttk.Separator(self.left, orient="horizontal")
        separator3.grid(column=0, columnspan=3, row=11, sticky=(E, W))

        # Filter Reference Signal
        reference = ctk.CTkButton(
            self.left,
            text="RefSig Editing",
            command=lambda: (EditRefsig(parent=self)),
            fg_color="#E5E4E2",
            text_color="black",
            border_color="black",
            border_width=1,
        )
        reference.grid(column=0, row=12, sticky=(N, S, E, W))

        # Resize File
        resize = ctk.CTkButton(
            self.left,
            text="Resize File",
            command=lambda: (GUIHelpers(parent=self).resize_file()),
            fg_color="#E5E4E2",
            text_color="black",
            border_color="black",
            border_width=1,
        )
        resize.grid(column=1, row=12, sticky=(N, S, E, W))
        separator4 = ttk.Separator(self.left, orient="horizontal")
        separator4.grid(column=0, columnspan=3, row=13, sticky=(E, W))

        # Force Analysis
        force = ctk.CTkButton(
            self.left,
            text="Analyse Force",
            command=lambda: (AnalyseForce(parent=self)),
            fg_color="#E5E4E2",
            text_color="black",
            border_color="black",
            border_width=1,
        )
        force.grid(column=0, row=14, sticky=(N, S, E, W))
        separator5 = ttk.Separator(self.left, orient="horizontal")
        separator5.grid(column=0, columnspan=3, row=15, sticky=(E, W))

        # Motor Unit properties
        mus = ctk.CTkButton(
            self.left,
            text="MU Properties",
            command=lambda: (MuAnalysis(parent=self)),
            fg_color="#E5E4E2",
            text_color="black",
            border_color="black",
            border_width=1,
        )
        mus.grid(column=1, row=14, sticky=(N, S, E, W))
        separator6 = ttk.Separator(self.left, orient="horizontal")
        separator6.grid(column=0, columnspan=3, row=17, sticky=(E, W))

        # Plot EMG
        plots = ctk.CTkButton(
            self.left,
            text="Plot EMG",
            command=lambda: (PlotEmg(parent=self)),
            fg_color="#E5E4E2",
            text_color="black",
            border_color="black",
            border_width=1,
        )
        plots.grid(column=0, row=16, sticky=(N, S, E, W))
        separator7 = ttk.Separator(self.left, orient="horizontal")
        separator7.grid(column=0, columnspan=3, row=19, sticky=(E, W))

        # Reset Analysis
        reset = ctk.CTkButton(
            self.left,
            text="Reset Analysis",
            command=self.reset_analysis,
            fg_color="#E5E4E2",
            text_color="black",
            border_color="black",
            border_width=1,
        )
        reset.grid(column=1, row=18, sticky=(N, S, E, W))

        # Advanced tools
        advanced = ctk.CTkButton(
            self.left,
            text="Advanced Tools",
            command=lambda: (AdvancedAnalysis(self)),
            fg_color="#000000",
            text_color="white",
            border_color="white",
            border_width=1,
            hover_color="#FFBF00",
        )
        advanced.grid(row=20, column=0, columnspan=2, sticky=(N, S, E, W))

        # Create right side framing for functionalities
        self.right = ctk.CTkFrame(
            self.master, fg_color="LightBlue4", corner_radius=0, bg_color="LightBlue4"
        )
        self.right.grid(column=1, row=0, sticky=(N, S, E, W))

        # Configure columns, plot is weighted more icons are not configured
        self.right.columnconfigure(0, weight=10)
        self.right.columnconfigure(1, weight=0)
        # Configure rows with a loop
        for row in range(5):
            self.right.rowconfigure(row, weight=1)

        # Create empty figure
        self.first_fig = Figure(figsize=(20 / 2.54, 15 / 2.54), frameon=True)
        self.canvas = FigureCanvasTkAgg(self.first_fig, master=self.right)
        self.canvas.get_tk_widget().grid(
            row=0, column=0, rowspan=6, sticky=(N, S, E, W)
        )

        # Create logo figure
        self.logo_canvas = Canvas(self.right, height=590, width=800, bg="white")
        self.logo_canvas.grid(row=0, column=0, rowspan=6, sticky=(N, S, E, W))

        logo_path = master_path + "/gui_files/logo.png"  # Get logo path
        self.logo = tk.PhotoImage(file=logo_path)

        self.logo_canvas.create_image(400, 300, anchor="center", image=self.logo)

        # Create info buttons
        # Settings button
        gear_path = master_path + "/gui_files/gear.png"
        self.gear = ctk.CTkImage(light_image=Image.open(gear_path), size=(30, 30))

        settings_b = ctk.CTkButton(
            self.right,
            text="",
            image=self.gear,
            command=self.open_settings,
            width=30,
            height=30,
            bg_color="LightBlue4",
            fg_color="LightBlue4",
        )
        settings_b.grid(column=1, row=0, sticky=W, pady=(0, 20))

        # Information Button
        info_path = master_path + "/gui_files/Info.png"  # Get infor button path
        self.info = ctk.CTkImage(light_image=Image.open(info_path), size=(30, 30))
        info_button = ctk.CTkButton(
            self.right,
            image=self.info,
            text="",
            width=30,
            height=30,
            bg_color="LightBlue4",
            fg_color="LightBlue4",
            command=lambda: (
                (webbrowser.open("https://www.giacomovalli.com/openhdemg/gui_intro/"))
            ),
        )
        info_button.grid(row=1, column=1, sticky=W, pady=(0, 20))

        # Button for online tutorials
        online_path = master_path + "/gui_files/Online.png"
        self.online = ctk.CTkImage(light_image=Image.open(online_path), size=(30, 30))
        online_button = ctk.CTkButton(
            self.right,
            image=self.online,
            text="",
            width=30,
            height=30,
            bg_color="LightBlue4",
            fg_color="LightBlue4",
            command=lambda: (
                (
                    webbrowser.open(
                        "https://www.giacomovalli.com/openhdemg/tutorials/setup_working_env/"
                    )
                )
            ),
        )
        online_button.grid(row=2, column=1, sticky=W, pady=(0, 20))

        # Button for dev information
        redirect_path = master_path + "/gui_files/Redirect.png"
        self.redirect = ctk.CTkImage(
            light_image=Image.open(redirect_path), size=(30, 30)
        )
        redirect_button = ctk.CTkButton(
            self.right,
            image=self.redirect,
            text="",
            width=30,
            height=30,
            bg_color="LightBlue4",
            fg_color="LightBlue4",
            command=lambda: (
                (
                    webbrowser.open(
                        "https://www.giacomovalli.com/openhdemg/about-us/#meet-the-developers"
                    )
                )
            ),
        )
        redirect_button.grid(row=3, column=1, sticky=W, pady=(0, 20))

        # Button for contact information
        contact_path = master_path + "/gui_files/Contact.png"
        self.contact = ctk.CTkImage(light_image=Image.open(contact_path), size=(30, 30))
        contact_button = ctk.CTkButton(
            self.right,
            image=self.contact,
            text="",
            width=30,
            height=30,
            bg_color="LightBlue4",
            fg_color="LightBlue4",
            command=lambda: (
                (webbrowser.open("https://www.giacomovalli.com/openhdemg/contacts/"))
            ),
        )
        contact_button.grid(row=4, column=1, sticky=W, pady=(0, 20))

        # Button for citatoin information
        cite_path = master_path + "/gui_files/Cite.png"
        self.cite = ctk.CTkImage(light_image=Image.open(cite_path), size=(30, 30))
        cite_button = ctk.CTkButton(
            self.right,
            image=self.cite,
            text="",
            width=30,
            height=30,
            bg_color="LightBlue4",
            fg_color="LightBlue4",
            command=lambda: (
                (webbrowser.open("https://www.giacomovalli.com/openhdemg/cite-us/"))
            ),
        )
        cite_button.grid(row=5, column=1, sticky=W, pady=(0, 20))

        for child in self.left.winfo_children():
            child.grid_configure(padx=5, pady=5)

    ## Define functionalities for buttons used in GUI master window
    def load_settings(self):
        """
        Instance Method to load the setting file for.

        Executed each time when the GUI or a toplevel is openened.
        The settings specified by the user will then be transferred
        to the code and used.
        """
        # If not previously imported, just import it
        global settings
        self.settings = importlib.reload(settings)
        self.update_gui_variables()

    def open_settings(self):
        """
        Instance Method to open the setting file for.

        Executed when the button "Settings" in master GUI window is pressed.
        A python file is openend containing a dictionary with relevant variables
        that users should be able to customize.
        """
        # Determine relative filepath
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/settings.py"

        # Check for operating system and open in default editor
        if sys.platform.startswith("darwin"):  # macOS
            subprocess.run(["open", file_path])
        elif sys.platform.startswith("win32"):  # Windows
            os.startfile(file_path)
        else:  # Linux or other
            subprocess.run(["xdg-open", file_path])

    # Unused (yet)
    def update_gui_variables(self):
        """
        Method to update variables changes in the settings file
        """
        pass

    def get_file_input(self):
        """
        Instance Method to load the file for analysis. The user is asked to select the file.

        Executed when the button "Load File" in master GUI window is pressed.

        See Also
        --------
        emg_from_demuse, emg_from_otb, refsig_from_otb and emg_from_json in library.
        """

        def load_file():
            try:
                if self.filetype.get() in [
                    "OTB",
                    "DEMUSE",
                    "OPENHDEMG",
                    "CUSTOMCSV",
                    "DELSYS",
                ]:
                    # Check filetype for processing
                    if self.filetype.get() == "OTB":
                        # Ask user to select the decomposed file
                        file_path = filedialog.askopenfilename(
                            title="Open OTB file to load",
                            filetypes=[("MATLAB files", "*.mat")],
                        )
                        self.file_path = file_path
                        # Load file
                        self.resdict = openhdemg.emg_from_otb(
                            filepath=self.file_path,
                            ext_factor=int(self.extension_factor.get()),
                        )
                        # Add filespecs
                        ctk.CTkLabel(
                            self.left, text=str(len(self.resdict["RAW_SIGNAL"].columns))
                        ).grid(column=2, row=2, sticky=(W, E), padx=5, pady=5)
                        ctk.CTkLabel(
                            self.left, text=str(self.resdict["NUMBER_OF_MUS"])
                        ).grid(column=2, row=3, sticky=(W, E), padx=5, pady=5)
                        ctk.CTkLabel(
                            self.left, text=str(self.resdict["EMG_LENGTH"])
                        ).grid(column=2, row=4, sticky=(W, E), padx=5, pady=5)

                    elif self.filetype.get() == "DEMUSE":
                        # Ask user to select the file
                        file_path = filedialog.askopenfilename(
                            title="Open DEMUSE file to load",
                            filetypes=[("MATLAB files", "*.mat")],
                        )
                        self.file_path = file_path
                        # load file
                        self.resdict = openhdemg.emg_from_demuse(
                            filepath=self.file_path
                        )
                        # Add filespecs
                        ctk.CTkLabel(
                            self.left, text=str(len(self.resdict["RAW_SIGNAL"].columns))
                        ).grid(column=2, row=2, sticky=(W, E), padx=5, pady=5)
                        ctk.CTkLabel(
                            self.left, text=str(self.resdict["NUMBER_OF_MUS"])
                        ).grid(column=2, row=3, sticky=(W, E), padx=5, pady=5)
                        ctk.CTkLabel(
                            self.left, text=str(self.resdict["EMG_LENGTH"])
                        ).grid(column=2, row=4, sticky=(W, E), padx=5, pady=5)
                    elif self.filetype.get() == "DELSYS":
                        # Ask user to select the file
                        file_path = filedialog.askopenfilename(
                            title="Select a DELSYS file with raw EMG to load",
                            filetypes=[("MATLAB files", "*.mat")],
                        )
                        # Ask user to open the Delsys decompostition
                        self.mus_path = filedialog.askdirectory(
                            title="Select the folder containing the DELSYS decomposition",
                        )
                        self.file_path = file_path

                        # load DELSYS
                        self.resdict = openhdemg.emg_from_delsys(
                            rawemg_filepath=self.file_path, mus_directory=self.mus_path
                        )
                        # Add filespecs
                        ctk.CTkLabel(
                            self.left, text=str(len(self.resdict["RAW_SIGNAL"].columns))
                        ).grid(column=2, row=2, sticky=(W, E), padx=5, pady=5)
                        ctk.CTkLabel(
                            self.left, text=str(self.resdict["NUMBER_OF_MUS"])
                        ).grid(column=2, row=3, sticky=(W, E), padx=5, pady=5)
                        ctk.CTkLabel(
                            self.left, text=str(self.resdict["EMG_LENGTH"])
                        ).grid(column=2, row=4, sticky=(W, E), padx=5, pady=5)

                    elif self.filetype.get() == "OPENHDEMG":
                        # Ask user to select the file
                        file_path = filedialog.askopenfilename(
                            title="Open JSON file to load",
                            filetypes=[("JSON files", "*.json")],
                        )
                        self.file_path = file_path
                        # load OPENHDEMG (.json)
                        self.resdict = openhdemg.emg_from_json(filepath=self.file_path)
                        # Add filespecs
                        if self.resdict["SOURCE"] in [
                            "DEMUSE",
                            "OTB",
                            "CUSTOMCSV",
                            "DELSYS",
                        ]:
                            ctk.CTkLabel(
                                self.left,
                                text=str(len(self.resdict["RAW_SIGNAL"].columns)),
                            ).grid(column=2, row=2, sticky=(W, E), padx=5, pady=5)
                            ctk.CTkLabel(
                                self.left, text=str(self.resdict["NUMBER_OF_MUS"])
                            ).grid(column=2, row=3, sticky=(W, E), padx=5, pady=5)
                            ctk.CTkLabel(
                                self.left, text=str(self.resdict["EMG_LENGTH"])
                            ).grid(column=2, row=4, sticky=(W, E), padx=5, pady=5)
                        else:
                            # Reconfigure labels for refsig
                            ctk.CTkLabel(
                                self.left,
                                text=str(len(self.resdict["REF_SIGNAL"].columns)),
                            ).grid(column=2, row=2, sticky=(W, E), padx=5, pady=5)
                            ctk.CTkLabel(self.left, text="NA").grid(
                                column=2, row=3, sticky=(W, E), padx=5, pady=5
                            )
                            ctk.CTkLabel(self.left, text="        ").grid(
                                column=2, row=4, sticky=(W, E), padx=5, pady=5
                            )
                    else:
                        # Ask user to select the file
                        file_path = filedialog.askopenfilename(
                            title="Open CUSTOMCSV file to load",
                            filetypes=[("CSV files", "*.csv")],
                        )
                        self.file_path = file_path
                        # load file
                        self.resdict = openhdemg.emg_from_customcsv(
                            filepath=self.file_path,
                            fsamp=float(self.fsamp.get()),
                        )
                        # Add filespecs
                        ctk.CTkLabel(self.left, text="Custom CSV").grid(
                            column=2, row=2, sticky=(W, E), padx=5, pady=5
                        )
                        ctk.CTkLabel(self.left, text="").grid(
                            column=2, row=3, sticky=(W, E), padx=5, pady=5
                        )
                        ctk.CTkLabel(self.left, text="").grid(
                            column=2, row=4, sticky=(W, E), padx=5, pady=5
                        )

                    # Get filename
                    filename = os.path.splitext(os.path.basename(file_path))[0]
                    self.filename = filename

                    # Add filename to label
                    self.master.title(self.filename)

                    # End progress
                    progress.grid_remove()
                    progress.stop()

                # This sections is used for refsig loading as they required not the
                # the filespecs to be loaded.
                else:
                    if self.filetype.get() == "OTB_REFSIG":
                        file_path = filedialog.askopenfilename(
                            title="Open OTB_REFSIG file to load",
                            filetypes=[("MATLAB files", "*.mat")],
                        )
                        self.file_path = file_path
                        # load refsig
                        self.resdict = openhdemg.refsig_from_otb(
                            filepath=self.file_path
                        )

                    elif self.filetype.get() == "DELSYS_REFSIG":

                        # Ask user to select the file
                        file_path = filedialog.askopenfilename(
                            title="Select a DELSYS_REFSIG file with raw EMG to load",
                            filetypes=[("MATLAB files", "*.mat")],
                        )
                        self.file_path = file_path
                        # load DELSYS
                        self.resdict = openhdemg.refsig_from_delsys(
                            filepath=self.file_path
                        )

                    elif self.filetype.get() == "CUSTOMCSV_REFSIG":
                        file_path = filedialog.askopenfilename(
                            title="Open CUSTOMCSV_REFSIG file to load",
                            filetypes=[("CSV files", "*.csv")],
                        )
                        self.file_path = file_path
                        # load refsig
                        self.resdict = openhdemg.refsig_from_customcsv(
                            filepath=self.file_path,
                            fsamp=float(self.fsamp.get()),
                        )

                    # Get filename
                    filename = os.path.splitext(os.path.basename(file_path))[0]
                    self.filename = filename

                    # Add filename to label
                    self.master.title(self.filename)

                    # Reconfigure labels for refsig
                    ctk.CTkLabel(
                        self.left, text=str(len(self.resdict["REF_SIGNAL"].columns))
                    ).grid(column=2, row=2, sticky=(W, E), padx=5, pady=5)
                    ctk.CTkLabel(self.left, text="NA").grid(
                        column=2, row=3, sticky=(W, E), padx=5, pady=5
                    )
                    ctk.CTkLabel(self.left, text="        ").grid(
                        column=2, row=4, sticky=(W, E), padx=5, pady=5
                    )

                # for child in self.left.winfo_children():
                #     child.grid_configure(padx=5, pady=5)

                # End progress
                progress.grid_remove()
                progress.stop()

                return

            except ValueError as e:
                show_error_dialog(
                    parent=self,
                    error=e,
                    solution=str(
                        "When an OTB file is loaded, make sure to "
                        + "specify an extension factor (number) first."
                        + "\nWhen a DELSYS file is loaded, make sure to "
                        + "specify the correct folder."
                    ),
                )
                # End progress
                progress.stop()
                progress.grid_remove()

            except FileNotFoundError as e:
                show_error_dialog(
                    parent=self,
                    error=e,
                    solution=str(
                        "Make sure to load correct file"
                        + "according to your specification."
                    ),
                )
                # End progress
                progress.stop()
                progress.grid_remove()

            except TypeError as e:
                show_error_dialog(
                    parent=self,
                    error=e,
                    solution=str(
                        "Make sure to load correct file"
                        + "according to your specification."
                    ),
                )
                # End progress
                progress.stop()
                progress.grid_remove()

            except KeyError as e:
                show_error_dialog(
                    parent=self,
                    error=e,
                    solution=str(
                        "Make sure to load correct file"
                        + "according to your specification."
                    ),
                )
                # End progress
                progress.stop()
                progress.grid_remove()

            except:
                # End progress
                progress.grid_remove()
                progress.stop()

        # Indicate Progress
        progress = ctk.CTkProgressBar(
            self.left,
            mode="indeterminate",
            fg_color="#585858",
            width=100,
            progress_color="#FFBF00",
        )
        progress.grid(row=4, column=0)
        progress.start()

        # Create a thread to run the load_file function
        save_thread = threading.Thread(target=load_file)
        save_thread.start()

    def on_filetype_change(self, *args):
        """
        This function is called when the value of the filetype variable is changed.
        When the filetype is set to "OTB", "CUSTOMCSV", "CUSTOMCSV_REFSIG" it will
        create a second combobox on the grid at column 0 and row 2 and when the filetype
        is set to something else it will remove the second combobox from the grid.
        """
        if self.filetype.get() not in ["OTB"]:
            if hasattr(self, "otb_combobox"):
                self.otb_combobox.grid_forget()
        if self.filetype.get() not in ["CUSTOMCSV"]:
            if hasattr(self, "csv_entry"):
                self.csv_entry.grid_forget()
        if self.filetype.get() not in ["CUSTOMCSV_REFSIG"]:
            if hasattr(self, "csv_entry"):
                self.csv_entry.grid_forget()

        # Add a combobox containing the OTB extension factors
        # in case an OTB file is loaded
        if self.filetype.get() == "OTB":
            self.extension_factor = StringVar()
            self.otb_combobox = ctk.CTkComboBox(
                self.left,
                values=[
                    "8",
                    "9",
                    "10",
                    "11",
                    "12",
                    "13",
                    "14",
                    "15",
                    "16",
                ],
                width=8,
                variable=self.extension_factor,
                state="readonly",
            )
            self.otb_combobox.grid(column=0, row=2, sticky=(W, E), padx=5)
            self.otb_combobox.set("Extension Factor")

        elif self.filetype.get() in ["CUSTOMCSV", "CUSTOMCSV_REFSIG"]:
            self.fsamp = StringVar(value="Fsamp")
            self.csv_entry = ctk.CTkEntry(
                self.left,
                width=8,
                textvariable=self.fsamp,
            )
            self.csv_entry.grid(column=0, row=2, sticky=(W, E), padx=5)

    def save_emgfile(self):
        """
        Instance method to save the edited emgfile. Results are saved in a .json file.

        Executed when the "Save File" button in the master GUI window is pressed.

        Raises
        ------
        AttributeError
            When a file was not loaded in the GUI.

        See Also
        --------
        save_json_emgfile in library.
        """

        def save_file():
            try:
                # Ask user to select the directory and file name
                save_filepath = filedialog.asksaveasfilename(
                    defaultextension=".json",
                    filetypes=(("JSON files", "*.json"), ("all files", "*.*")),
                )

                if not save_filepath:
                    # End progress
                    progress.stop()
                    progress.grid_remove()
                    return  # User canceled the file dialog

                # Get emgfile
                save_emg = self.resdict

                # Save json file
                openhdemg.save_json_emgfile(emgfile=save_emg, filepath=save_filepath)

                # End progress
                progress.stop()
                progress.grid_remove()

                return

            except AttributeError as e:
                show_error_dialog(
                    parent=self, error=e, solution=str("Make sure a file is loaded.")
                )

        # Indicate Progress
        progress = ctk.CTkProgressBar(self.left, mode="indeterminate")
        progress.grid(row=4, column=0)
        progress.start()

        # Create a thread to run the save_file function
        save_thread = threading.Thread(target=save_file)
        save_thread.start()

    def reset_analysis(self):
        """
        Instance method to restore the GUI to base data. Any analysis progress will be deleted by
        reloading the original file.

        Executed when button "Reset Analysis" in master GUI window is pressed. The emgfile is
        updated to its original state.

        Raises
        ------
        AttributeError
            When no file was loaded in the GUI.
        FileNotFoundError
            When no file was loaded in the GUI.
        """
        # Get user input and check whether analysis wants to be truly resetted
        if messagebox.askokcancel(
            title="Attention",
            message="Do you really want to reset the analysis?",
            icon="warning",
        ):
            # user decided to rest analysis
            try:
                # reload original file
                if self.filetype.get() in [
                    "OTB",
                    "DEMUSE",
                    "OPENHDEMG",
                    "CUSTOMCSV",
                    "DELSYS",
                ]:
                    if self.filetype.get() == "OTB":
                        self.resdict = openhdemg.emg_from_otb(
                            filepath=self.file_path,
                            ext_factor=int(self.extension_factor.get()),
                        )

                    elif self.filetype.get() == "DEMUSE":
                        self.resdict = openhdemg.emg_from_demuse(
                            filepath=self.file_path
                        )

                    elif self.filetype.get() == "OPENHDEMG":
                        self.resdict = openhdemg.emg_from_json(filepath=self.file_path)

                    elif self.filetype.get() == "CUSTOMCSV":
                        self.resdict = openhdemg.emg_from_customcsv(
                            filepath=self.file_path
                        )
                    elif self.filetype.get() == "DELSYS":
                        self.resdict = openhdemg.emg_from_delsys(
                            rawemg_filepath=self.file_path, mus_directory=self.mus_path
                        )
                    # Update Filespecs
                    ctk.CTkLabel(
                        self.left, text=str(len(self.resdict["RAW_SIGNAL"].columns))
                    ).grid(column=2, row=2, sticky=(W, E))
                    ctk.CTkLabel(
                        self.left, text=str(self.resdict["NUMBER_OF_MUS"])
                    ).grid(column=2, row=3, sticky=(W, E))
                    ctk.CTkLabel(self.left, text=str(self.resdict["EMG_LENGTH"])).grid(
                        column=2, row=4, sticky=(W, E)
                    )

                else:
                    # load refsig
                    if self.filetype.get() == "OTB_REFSIG":
                        self.resdict = openhdemg.refsig_from_otb(
                            filepath=self.file_path
                        )
                    else:  # CUSTOMCSV_REFSIG
                        self.resdict = openhdemg.refsig_from_customcsv(
                            filepath=self.file_path
                        )

                    # Recondifgure labels for refsig
                    ctk.CTkLabel(
                        self.left, text=str(len(self.resdict["REF_SIGNAL"].columns))
                    ).grid(column=2, row=2, sticky=(W, E))
                    ctk.CTkLabel(self.left, text="NA").grid(
                        column=2, row=3, sticky=(W, E)
                    )
                    ctk.CTkLabel(self.left, text="        ").grid(
                        column=2, row=4, sticky=(W, E)
                    )

                # Update Plot
                if hasattr(self, "fig"):
                    self.in_gui_plotting(resdict=self.resdict)

                # Clear frame for output
                if hasattr(self, "terminal"):
                    self.terminal = ttk.LabelFrame(
                        self.master, text="Result Output", height=100, relief="ridge"
                    )
                    self.terminal.grid(
                        column=0,
                        row=21,
                        columnspan=2,
                        pady=8,
                        padx=10,
                        sticky=(N, S, W, E),
                    )

            except AttributeError as e:
                show_error_dialog(
                    parent=self, error=e, solution=str("Make sure a file is loaded.")
                )

            except FileNotFoundError as e:
                show_error_dialog(
                    parent=self, error=e, solution=str("Make sure a file is loaded.")
                )

    # -----------------------------------------------------------------------------------------------
    # Plotting inside of GUI

    def in_gui_plotting(self, resdict, plot="idr"):
        """
        Instance method to plot any analysis results in the GUI for inspection. Plots are updated
        during the analysis process.

        Executed when button "View MUs" in master GUI window is pressed or when the original
        input file is changed.

        Raises
        ------
        AttributeError
            When no file was loaded in the GUI.

        See Also
        --------
        plot_refsig, plot_idr in the library.
        """
        try:
            if self.resdict["SOURCE"] in [
                "OTB_REFSIG",
                "CUSTOMCSV_REFSIG",
                "DELSYS_REFSIG",
            ]:
                self.fig = openhdemg.plot_refsig(
                    emgfile=resdict, showimmediately=False, tight_layout=True
                )
            elif plot == "idr":
                self.fig = openhdemg.plot_idr(
                    emgfile=resdict, showimmediately=False, tight_layout=True
                )
            elif plot == "refsig_fil":
                self.fig = openhdemg.plot_refsig(
                    emgfile=resdict, showimmediately=False, tight_layout=True
                )
            elif plot == "refsig_off":
                self.fig = openhdemg.plot_refsig(
                    emgfile=resdict, showimmediately=False, tight_layout=True
                )

            self.canvas = FigureCanvasTkAgg(self.fig, master=self.right)
            self.canvas.get_tk_widget().grid(
                row=0, column=0, rowspan=6, sticky=(N, S, E, W), padx=5
            )
            toolbar = NavigationToolbar2Tk(self.canvas, self.right, pack_toolbar=False)
            toolbar.grid(row=5, column=0, sticky=S)
            plt.close()

        except AttributeError as e:
            show_error_dialog(
                parent=self, error=e, solution=str("Make sure a file is loaded.")
            )

    # -----------------------------------------------------------------------------------------------
    # Analysis results display

    def display_results(self, input_df):
        """
        Instance method that displays all analysis results in the
        output terminal using Pandastable. Input must be a Pandas dataframe.

        Executed trough functions with calculated anylsis results.

        Parameters
        ----------
        input_df : pd.DataFrame
            Dataftame containing the analysis results.
        """
        # Create frame for output
        self.terminal = ttk.LabelFrame(
            self.master,
            text="Result Output",
            height=100,
            relief="ridge",
        )
        self.terminal.grid(
            column=0, row=21, columnspan=2, pady=8, padx=10, sticky=(N, S, W, E)
        )

        # Display results
        table = Table(
            self.terminal,
            dataframe=input_df,
            showtoolbar=False,
            showstatusbar=False,
            height=100,
            width=100,
        )

        # Resize column width
        options = {"cellwidth": 10}
        config.apply_options(options, table)

        # Show results
        table.show()


# -----------------------------------------------------------------------------------------------
def run_main():
    # Run GUI upon calling
    if __name__ == "__main__":
        root = Tk()
        emgGUI(root)
        root.mainloop()


if __name__ == "__main__":
    root = Tk()
    emgGUI(root)
    root.mainloop()
