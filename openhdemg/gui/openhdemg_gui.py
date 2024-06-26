"""
This file contains the gui functionalities of openhdemg.
"""

import importlib
import os
import copy
import subprocess
import sys
import tkinter as tk
import webbrowser
from tkinter import Canvas, E, N, S, StringVar, Tk, W, filedialog, messagebox, ttk

import customtkinter as ctk
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from pandastable import Table
from PIL import Image

import openhdemg.gui.settings as settings
import openhdemg.library as openhdemg
from openhdemg.gui.gui_modules import (
    AdvancedAnalysis,
    AnalyseForce,
    EditSig,
    GUIHelpers,
    MuAnalysis,
    MURemovalWindow,
    PlotEmg,
    show_error_dialog,
)

matplotlib.use("TkAgg")
ctk.set_default_color_theme(
    os.path.dirname(os.path.abspath(__file__)) + "/gui_files/gui_color_theme.json"
)


class emgGUI(ctk.CTk):
    """
    This class is used to create a graphical user interface for the openhdemg
    library.

    Within this class and corresponding childs, most functionalities of the
    openhdemg library are packed in a GUI. However, the library is more
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
        Filetype can be "OPENHDEMG", "OTB", "DEMUSE", "OTB_REFSIG",
        "CUSTOMCSV", "CUSTOMCSV_REFSIG".
    self.left : tk.frame
        Left frame inside of self that contains all buttons and filespecs.
    self.logo :
        String containing the path to image file containing logo of openhdemg.
    self.logo_canvas : tk.canvas
        Canvas to display logo of Open_HG-EMG when openend.
    self.self: tk
        TK self window containing all widget children for this GUI.
    self.resdict : dict
        Dictionary derived from input EMG file for further analysis.
    self.resdict_copy_of_original : dict
        A deepcopy of self.resdict stored for resetting the analyses.
    self.right : tk.frame
        Left frame inside of self that contains plotting canvas.
    self.terminal : ttk.Labelframe
        Tkinter labelframe that is used to display the results table in the
        GUI.
    self.processing_indicator : ctk.CTkButton
        Button used to indicate that the file is loading/saving.
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

    Methods
    -------
    __init__(self)
        Initializes GUI class and main GUI window (self).
    get_file_input()
        Gets emgfile location and respective file is loaded.
        Executed when button "Load File" in self GUI window pressed.
    save_emgfile()
        Saves the edited emgfile dictionary to a .json file.
        Executed when button "Save File" in self GUI window pressed.
    reset_analysis()
        Resets the whole analysis, restores the original input file and the
        graph.
        Executed when button "Reset analysis" in self GUI window pressed.
    in_gui_plotting()
        Method used for creating plot inside the GUI (on the GUI canvas).
        Executed when button "View MUs" in self GUI window pressed.
    mu_analysis()
        Opens seperate window to calculated specific motor unit properties.
        Executed when button "MU properties" in self GUI window pressed.
    display_results()
        Method used to display result table containing analysis results.

    Notes
    -----
    Please note that altough we created a GUI class, the included methods/
    instances are highly specific. We did not conceptualize the
    methods/instances to be used seperately. Similar functionalities are
    available in the library and were specifically coded to be used
    seperately/singularly.

    Most instance methods of this class heavily rely on the functions provided
    in the library. In the section "See Also" at each instance method, the
    reader is referred to the corresponding function and extensive
    documentation in the library.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialization of  GUI window upon calling.

        Parameters
        ----------
        : tk
            tk class object
        """

        super().__init__(*args, **kwargs)

        # Load settings
        self.load_settings()

        # Set up GUI
        self.title("openhdemg")
        master_path = os.path.dirname(os.path.abspath(__file__))
        ctk.set_default_color_theme(master_path + "/gui_files/gui_color_theme.json")

        iconpath = master_path + "/gui_files/Icon_transp.ico"
        self.iconbitmap(iconpath)

        # Necessary for resizing
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=5)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)  # Output
        self.minsize(width=600, height=400)

        # Create left side framing for functionalities
        self.left = ctk.CTkFrame(
            self,
        )
        self.left.grid(column=0, row=0, sticky=(N, S, E, W))

        # Configure columns with a loop
        self.left.columnconfigure(0, weight=1)
        self.left.columnconfigure(1, weight=1)

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
            width=8,
            variable=self.filetype,
            values=signal_value,
            state="readonly",
        )
        signal_entry.grid(column=0, row=1, sticky=(W, E))
        self.filetype.set("Type of file")
        # Trace filetype to apply function when changing
        self.filetype.trace_add("write", self.on_filetype_change)

        # Load file
        load = ctk.CTkButton(
            self.left,
            text="Load File",
            command=self.get_file_input,
        )
        load.grid(column=0, row=3, sticky=(N, S, E, W))

        # Button to indicate that the file is loading
        self.processing_indicator = ctk.CTkButton(
            self.left,
            text="Processing!",
            fg_color="#FFA500",  # Orange
        )
        self.processing_indicator.grid(column=0, row=4, sticky=(N, S, E, W))
        # Hide, don't forget to preserve rowconfigure settings
        self.processing_indicator.lower()

        # File specifications
        ctk.CTkLabel(
            self.left,
            text="Filespecs",
            font=("Segoe UI", 18, "underline"),
        ).grid(column=1, row=1, sticky=W)
        self.n_channels = ctk.CTkLabel(
            self.left,
            text="N Channels:",
            font=("Segoe UI", 15, "bold"),
        )
        self.n_channels.grid(column=1, row=2, sticky=W)
        self.n_of_mus = ctk.CTkLabel(
            self.left,
            text="N of MUs:",
            font=("Segoe UI", 15, "bold"),
        )
        self.n_of_mus.grid(column=1, row=3, sticky=W)
        self.file_length = ctk.CTkLabel(
            self.left,
            text="File Length:",
            font=("Segoe UI", 15, "bold"),
        )
        self.file_length.grid(column=1, row=4, sticky=W)
        separator0 = ttk.Separator(self.left, orient="horizontal")
        separator0.grid(column=0, columnspan=2, row=5, sticky=(E, W))

        # Save File
        save = ctk.CTkButton(
            self.left,
            text="Save File",
            command=self.save_emgfile,
        )
        save.grid(column=0, row=6, sticky=(N, S, E, W))
        separator1 = ttk.Separator(self.left, orient="horizontal")
        separator1.grid(column=0, columnspan=2, row=7, sticky=(E, W))

        # Export to Excel
        export = ctk.CTkButton(
            self.left,
            text="Save Results",
            command=lambda: (GUIHelpers(parent=self).export_to_excel()),
        )
        export.grid(column=1, row=6, sticky=(N, S, E, W))

        # View Motor Unit Firings
        firings = ctk.CTkButton(
            self.left,
            text="View MUs",
            command=lambda: (self.in_gui_plotting(resdict=self.resdict)),
        )
        firings.grid(column=0, row=8, sticky=(N, S, E, W))

        # Sort Motor Units
        sorting = ctk.CTkButton(
            self.left,
            text="Sort MUs",
            command=lambda: (GUIHelpers(parent=self).sort_mus()),
        )
        sorting.grid(column=1, row=8, sticky=(N, S, E, W))
        separator2 = ttk.Separator(self.left, orient="horizontal")
        separator2.grid(column=0, columnspan=2, row=9, sticky=(E, W))

        # Remove Motor Units
        remove_mus = ctk.CTkButton(
            self.left,
            text="Remove MUs",
            command=lambda: (MURemovalWindow(parent=self)),
        )
        remove_mus.grid(column=0, row=10, sticky=(N, S, E, W))

        separator3 = ttk.Separator(self.left, orient="horizontal")
        separator3.grid(column=0, columnspan=2, row=11, sticky=(E, W))

        # Filter Reference Signal
        reference = ctk.CTkButton(
            self.left,
            text="Signal Editing",
            command=lambda: (EditSig(parent=self)),
        )
        reference.grid(column=0, row=12, sticky=(N, S, E, W))

        # Resize File
        resize = ctk.CTkButton(
            self.left,
            text="Resize File",
            command=lambda: (GUIHelpers(parent=self).resize_file()),
        )
        resize.grid(column=1, row=12, sticky=(N, S, E, W))
        separator4 = ttk.Separator(self.left, orient="horizontal")
        separator4.grid(column=0, columnspan=2, row=13, sticky=(E, W))

        # Force Analysis
        force = ctk.CTkButton(
            self.left,
            text="Analyse Force",
            command=lambda: (AnalyseForce(parent=self)),
        )
        force.grid(column=0, row=14, sticky=(N, S, E, W))
        separator5 = ttk.Separator(self.left, orient="horizontal")
        separator5.grid(column=0, columnspan=2, row=15, sticky=(E, W))

        # Motor Unit properties
        mus = ctk.CTkButton(
            self.left,
            text="MU Properties",
            command=lambda: (MuAnalysis(parent=self)),
        )
        mus.grid(column=1, row=14, sticky=(N, S, E, W))
        separator6 = ttk.Separator(self.left, orient="horizontal")
        separator6.grid(column=0, columnspan=2, row=17, sticky=(E, W))

        # Plot EMG
        plots = ctk.CTkButton(
            self.left,
            text="Plot EMG",
            command=lambda: (PlotEmg(parent=self)),
        )
        plots.grid(column=0, row=16, sticky=(N, S, E, W))
        separator7 = ttk.Separator(self.left, orient="horizontal")
        separator7.grid(column=0, columnspan=2, row=19, sticky=(E, W))

        # Reset Analysis
        reset = ctk.CTkButton(
            self.left,
            text="Reset Analysis",
            command=self.reset_analysis,
        )
        reset.grid(column=1, row=18, sticky=(N, S, E, W))

        # Advanced tools
        advanced = ctk.CTkButton(
            self.left,
            text="Advanced Tools",
            command=lambda: (AdvancedAnalysis(self)),
            hover_color="#FFBF00",
            fg_color="#000000",
            text_color="#FFFFFF",
            border_color="#FFFFFF",
        )
        advanced.grid(row=20, column=0, columnspan=2, sticky=(N, S, E, W))

        # Create right side framing for functionalities
        self.right = ctk.CTkFrame(
            self,
        )
        self.right.grid(column=1, row=0, sticky=(N, S, E, W))

        # Configure columns, plot is weighted more icons are not configured
        self.right.columnconfigure(0, weight=10)
        self.right.columnconfigure(1, weight=0)
        # Configure rows with a loop
        for row in range(5):
            self.right.rowconfigure(row, weight=1)

        # Create logo canvas figure
        self.logo_canvas = Canvas(
            self.right,
            width=800,
            height=600,
            bg="white",
        )
        self.logo_canvas.grid(
            row=0, column=0, rowspan=6, sticky=(N, S, E, W), pady=(5, 0),
        )

        # Load the logo as a resizable matplotlib figure
        logo_path = master_path + "/gui_files/Logo_high_res.png"
        logo = plt.imread(logo_path)
        logo_fig, ax = plt.subplots()
        ax.imshow(logo)
        ax.axis('off')  # Turn off axis
        logo_fig.tight_layout()  # Adjust layout padding

        # Plot the figure in the in_gui_plotting canvas
        self.canvas = FigureCanvasTkAgg(logo_fig, master=self.logo_canvas)
        self.canvas.get_tk_widget().pack(
            expand=True, fill="both", padx=5, pady=5,
        )
        plt.close()
        # This solution is more flexible and memory efficient than previously.

        # Create info buttons
        # Settings button
        gear_path = master_path + "/gui_files/Gear.png"
        self.gear = ctk.CTkImage(
            light_image=Image.open(gear_path),
            size=(30, 30),
        )

        settings_b = ctk.CTkButton(
            self.right,
            text="",
            image=self.gear,
            command=self.open_settings,
            width=30,
            height=30,
            bg_color="LightBlue4",
            fg_color="LightBlue4",
            border_width=0,
        )
        settings_b.grid(column=1, row=0, sticky=W, pady=(0, 20))

        # Information Button
        info_path = master_path + "/gui_files/Info.png"  # Get info button path
        self.info = ctk.CTkImage(
            light_image=Image.open(info_path),
            size=(30, 30),
        )
        info_button = ctk.CTkButton(
            self.right,
            image=self.info,
            text="",
            width=30,
            height=30,
            bg_color="LightBlue4",
            fg_color="LightBlue4",
            border_width=0,
            command=lambda: (
                (webbrowser.open("https://www.giacomovalli.com/openhdemg/gui_intro/"))
            ),
        )
        info_button.grid(row=1, column=1, sticky=W, pady=(0, 20))

        # Button for online tutorials
        online_path = master_path + "/gui_files/Online.png"
        self.online = ctk.CTkImage(
            light_image=Image.open(online_path),
            size=(30, 30),
        )
        online_button = ctk.CTkButton(
            self.right,
            image=self.online,
            text="",
            width=30,
            height=30,
            bg_color="LightBlue4",
            fg_color="LightBlue4",
            border_width=0,
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
            light_image=Image.open(redirect_path),
            size=(30, 30),
        )
        redirect_button = ctk.CTkButton(
            self.right,
            image=self.redirect,
            text="",
            width=30,
            height=30,
            bg_color="LightBlue4",
            fg_color="LightBlue4",
            border_width=0,
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
        self.contact = ctk.CTkImage(
            light_image=Image.open(contact_path),
            size=(30, 30),
        )
        contact_button = ctk.CTkButton(
            self.right,
            image=self.contact,
            text="",
            width=30,
            height=30,
            bg_color="LightBlue4",
            fg_color="LightBlue4",
            border_width=0,
            command=lambda: (
                (webbrowser.open("https://www.giacomovalli.com/openhdemg/contacts/"))
            ),
        )
        contact_button.grid(row=4, column=1, sticky=W, pady=(0, 20))

        # Button for citatoin information
        cite_path = master_path + "/gui_files/Cite.png"
        self.cite = ctk.CTkImage(
            light_image=Image.open(cite_path),
            size=(30, 30),
        )
        cite_button = ctk.CTkButton(
            self.right,
            image=self.cite,
            text="",
            width=30,
            height=30,
            bg_color="LightBlue4",
            fg_color="LightBlue4",
            border_width=0,
            command=lambda: (
                (webbrowser.open("https://www.giacomovalli.com/openhdemg/cite-us/"))
            ),
        )
        cite_button.grid(row=5, column=1, sticky=W, pady=(0, 20))

        # Create frame for output
        self.terminal = ttk.LabelFrame(
            self, text="Result Output", height=150, relief="ridge",
        )
        self.terminal.grid(
            column=0,
            row=1,
            columnspan=2,
            pady=5,
            padx=5,
            sticky=(N, S, W, E),
        )

        for child in self.left.winfo_children():
            child.grid_configure(padx=5, pady=5)

    # Define functionalities for buttons used in GUI master window
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

    def open_settings(self):
        """
        Instance Method to open the setting file for.

        Executed when the button "Settings" in master GUI window is pressed.
        A python file is openend containing a dictionary with relevant
        variables that users should be able to customize.
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

    def get_file_input(self):
        """
        Instance Method to load the file for analysis. The user is asked to
        select the file.

        Executed when the button "Load File" in master GUI window is pressed.

        This creates both an object containing the file to use and an object
        to reset to the original file.

        See Also
        --------
        emg_from_otb, emg_from_demuse, emg_from_delsys, emg_from_customcsv,
        refsig_from_otb, refsig_from_delsys, refsig_from_customcsv in library.
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
                            title="Open decomposed OTB file to load",
                            filetypes=[("MATLAB files", "*.mat")],
                        )
                        self.file_path = file_path
                        # Load file
                        self.resdict = openhdemg.emg_from_otb(
                            filepath=self.file_path,
                            ext_factor=self.settings.emg_from_otb__ext_factor,
                            refsig=self.settings.emg_from_otb__refsig,
                            extras=self.settings.emg_from_otb__extras,
                            ignore_negative_ipts=self.settings.emg_from_otb__ignore_negative_ipts,
                        )
                        # Add filespecs
                        self.n_channels.configure(
                            text="N Channels: "
                            + str(len(self.resdict["RAW_SIGNAL"].columns)),
                            font=("Segoe UI", 15, ("bold")),
                        )
                        self.n_of_mus.configure(
                            text="N of MUs: " + str(self.resdict["NUMBER_OF_MUS"]),
                            font=("Segoe UI", 15, "bold"),
                        )
                        self.file_length.configure(
                            text="File Length: " + str(self.resdict["EMG_LENGTH"]),
                            font=("Segoe UI", 15, "bold"),
                        )

                    elif self.filetype.get() == "DEMUSE":
                        # Ask user to select the file
                        file_path = filedialog.askopenfilename(
                            title="Open DEMUSE file to load",
                            filetypes=[("MATLAB files", "*.mat")],
                        )
                        self.file_path = file_path
                        # load file
                        self.resdict = openhdemg.emg_from_demuse(
                            filepath=self.file_path,
                            ignore_negative_ipts=self.settings.emg_from_demuse__ignore_negative_ipts,
                        )
                        # Add filespecs
                        self.n_channels.configure(
                            text="N Channels: "
                            + str(len(self.resdict["RAW_SIGNAL"].columns)),
                            font=("Segoe UI", 15, ("bold")),
                        )
                        self.n_of_mus.configure(
                            text="N of MUs: " + str(self.resdict["NUMBER_OF_MUS"]),
                            font=("Segoe UI", 15, "bold"),
                        )
                        self.file_length.configure(
                            text="File Length: " + str(self.resdict["EMG_LENGTH"]),
                            font=("Segoe UI", 15, "bold"),
                        )

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
                            rawemg_filepath=self.file_path,
                            mus_directory=self.mus_path,
                            emg_sensor_name=self.settings.emg_from_delsys__emg_sensor_name,
                            refsig_sensor_name=self.settings.emg_from_delsys__refsig_sensor_name,
                            filename_from=self.settings.emg_from_delsys__filename_from,
                        )
                        # Add filespecs
                        self.n_channels.configure(
                            text="N Channels: "
                            + str(len(self.resdict["RAW_SIGNAL"].columns)),
                            font=("Segoe UI", 15, ("bold")),
                        )
                        self.n_of_mus.configure(
                            text="N of MUs: " + str(self.resdict["NUMBER_OF_MUS"]),
                            font=("Segoe UI", 15, "bold"),
                        )
                        self.file_length.configure(
                            text="File Length: " + str(self.resdict["EMG_LENGTH"]),
                            font=("Segoe UI", 15, "bold"),
                        )

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
                            # Add filespecs
                            self.n_channels.configure(
                                text="N Channels: "
                                + str(len(self.resdict["RAW_SIGNAL"].columns)),
                                font=("Segoe UI", 15, ("bold")),
                            )
                            self.n_of_mus.configure(
                                text="N of MUs: " + str(self.resdict["NUMBER_OF_MUS"]),
                                font=("Segoe UI", 15, "bold"),
                            )
                            self.file_length.configure(
                                text="File Length: " + str(self.resdict["EMG_LENGTH"]),
                                font=("Segoe UI", 15, "bold"),
                            )
                        else:
                            # Add filespecs
                            self.n_channels.configure(
                                text="N Channels: "
                                + str(len(self.resdict["REF_SIGNAL"].columns)),
                                font=("Segoe UI", 15, ("bold")),
                            )
                            self.n_of_mus.configure(
                                text="N of MUs: N/A",
                                font=("Segoe UI", 15, "bold"),
                            )
                            self.file_length.configure(
                                text="File Length: "
                                + str(len(self.resdict["REF_SIGNAL"].iloc[:, 0])),
                                font=("Segoe UI", 15, "bold"),
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
                            ref_signal=self.settings.emg_from_customcsv__ref_signal,
                            raw_signal=self.settings.emg_from_customcsv__raw_signal,
                            ipts=self.settings.emg_from_customcsv__ipts,
                            mupulses=self.settings.emg_from_customcsv__mupulses,
                            binary_mus_firing=self.settings.emg_from_customcsv__binary_mus_firing,
                            accuracy=self.settings.emg_from_customcsv__accuracy,
                            extras=self.settings.emg_from_customcsv__extras,
                            fsamp=self.settings.emg_from_customcsv__fsamp,
                            ied=self.settings.emg_from_customcsv__ied,
                        )
                        # Add filespecs
                        self.n_channels.configure(
                            text="N Channels: "
                            + str(len(self.resdict["RAW_SIGNAL"].columns)),
                            font=("Segoe UI", 15, ("bold")),
                        )
                        self.n_of_mus.configure(
                            text="N of MUs: " + str(self.resdict["NUMBER_OF_MUS"]),
                            font=("Segoe UI", 15, "bold"),
                        )
                        self.file_length.configure(
                            text="File Length: " + str(self.resdict["EMG_LENGTH"]),
                            font=("Segoe UI", 15, "bold"),
                        )

                    # Get filename
                    filename = os.path.splitext(os.path.basename(file_path))[0]
                    self.filename = filename

                    # Add filename to label
                    self.title(self.filename)

                    # Lower processing_indicator
                    if hasattr(self, "processing_indicator"):
                        self.processing_indicator.lower()

                # This sections is used for refsig loading as they do not
                # require the filespecs to be loaded.
                else:
                    if self.filetype.get() == "OTB_REFSIG":
                        file_path = filedialog.askopenfilename(
                            title="Open OTB_REFSIG file to load",
                            filetypes=[("MATLAB files", "*.mat")],
                        )
                        self.file_path = file_path
                        # load refsig
                        self.resdict = openhdemg.refsig_from_otb(
                            filepath=self.file_path,
                            refsig=self.settings.refsig_from_otb__refsig,
                            extras=self.settings.refsig_from_otb__extras,
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
                            filepath=self.file_path,
                            refsig_sensor_name=self.settings.refsig_from_delsys__refsig_sensor_name,
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
                            ref_signal=self.settings.refsig_from_customcsv__ref_signal,
                            extras=self.settings.refsig_from_customcsv__extras,
                            fsamp=self.settings.refsig_from_customcsv__fsamp,
                        )

                    # Get filename
                    filename = os.path.splitext(os.path.basename(file_path))[0]
                    self.filename = filename

                    # Add filename to label
                    self.title(self.filename)

                    # Add filespecs
                    self.n_channels.configure(
                        text="N Channels: "
                        + str(len(self.resdict["REF_SIGNAL"].columns)),
                        font=("Segoe UI", 15, ("bold")),
                    )
                    self.n_of_mus.configure(
                        text="N of MUs: N/A",
                        font=("Segoe UI", 15, "bold"),
                    )
                    self.file_length.configure(
                        text="File Length: "
                        + str(len(self.resdict["REF_SIGNAL"].iloc[:, 0])),
                        font=("Segoe UI", 15, "bold"),
                    )

                # Lower processing_indicator
                if hasattr(self, "processing_indicator"):
                    self.processing_indicator.lower()

                # If file succesfully loaded, delete previous analyses results
                self.delete_previous_analyses_results()

                # Make a copy of the loaded file
                self.resdict_copy_of_original = copy.deepcopy(self.resdict)

                # Display the loaded file
                if self.resdict["SOURCE"] in ["DEMUSE", "OTB", "CUSTOMCSV", "DELSYS"]:
                    self.in_gui_plotting(self.resdict)
                else:
                    self.in_gui_plotting(self.resdict, plot="refsig_off")

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
                # Lower processing_indicator
                if hasattr(self, "processing_indicator"):
                    self.processing_indicator.lower()

            except FileNotFoundError as e:
                show_error_dialog(
                    parent=self,
                    error=e,
                    solution=str(
                        "Make sure to load correct file"
                        + "according to your specification."
                    ),
                )
                # Lower processing_indicator
                if hasattr(self, "processing_indicator"):
                    self.processing_indicator.lower()

            except TypeError as e:
                show_error_dialog(
                    parent=self,
                    error=e,
                    solution=str(
                        "Make sure to load correct file"
                        + "according to your specification."
                    ),
                )
                # Lower processing_indicator
                if hasattr(self, "processing_indicator"):
                    self.processing_indicator.lower()

            except KeyError as e:
                show_error_dialog(
                    parent=self,
                    error=e,
                    solution=str(
                        "Make sure to load correct file"
                        + "according to your specification."
                    ),
                )
                # Lower processing_indicator
                if hasattr(self, "processing_indicator"):
                    self.processing_indicator.lower()

            except:
                # Lower processing_indicator
                if hasattr(self, "processing_indicator"):
                    self.processing_indicator.lower()

        # Re-Load settings
        self.load_settings()

        # Display the processing indicator
        self.processing_indicator.lift()

        # Call the function to load the file
        load_file()

        # Remove file loading indicator
        if hasattr(self, "processing_indicator"):
            self.processing_indicator.lower()

    def on_filetype_change(self, *args):
        """
        This function is called when the value of the filetype variable is
        changed. If filetype is set to != "OPENHDEMG", it will create a second
        combobox on the grid at column 0 and row 2 and when the filetype is
        set to "OPENHDEMG" it will remove the second combobox from the grid.
        """

        # Make sure to forget all the previous labels
        if hasattr(self, "verify_settings_text"):
            self.verify_settings_text.grid_forget()

        if self.filetype.get() != "OPENHDEMG":
            # Display the text: Verify openfiles settings!
            self.verify_settings_text = ctk.CTkLabel(
                self.left,
                text="Verify openfiles settings!",
                font=("Segoe UI", 12, "bold"),
                text_color="black",
            )
            self.verify_settings_text.grid(
                column=0,
                row=2,
                sticky=(W, E),
                padx=5,
            )

    def save_emgfile(self):
        """
        Instance method to save the edited emgfile. Results are saved in a
        .json file.

        Executed when the "Save File" button in the master GUI window is
        pressed.

        Raises
        ------
        AttributeError
            When a file was not loaded in the GUI.

        See Also
        --------
        save_json_emgfile in library.
        """

        # Re-Load settings
        self.load_settings()

        # Display the processing indicator
        self.processing_indicator.lift()

        # Save the file
        try:
            openhdemg.asksavefile(
                emgfile=self.resdict,
                compresslevel=self.settings.save_json_emgfile__compresslevel,
            )
        except AttributeError as e:
            # Remove file saving indicator
            if hasattr(self, "processing_indicator"):
                self.processing_indicator.lower()
            # Show error
            show_error_dialog(
                parent=self,
                error=e,
                solution=str("Make sure a file is loaded."),
            )
        except Exception:
            # Remove file saving indicator
            if hasattr(self, "processing_indicator"):
                self.processing_indicator.lower()

        # Remove file saving indicator
        if hasattr(self, "processing_indicator"):
            self.processing_indicator.lower()

    def reset_analysis(self):
        """
        Instance method to restore the GUI to base data. Any analysis progress
        will be deleted by reloading the original file.

        Executed when button "Reset Analysis" in master GUI window is pressed.
        The emgfile is updated to its original state.

        Raises
        ------
        AttributeError
            When no file was loaded in the GUI.
        FileNotFoundError
            When no file was loaded in the GUI.
        """

        # Get user input and check whether analysis wants to be truly resetted
        if not messagebox.askokcancel(
            title="Attention",
            message="Do you really want to reset the analysis?",
            icon="warning",
        ):
            # user decided to not rest analysis
            return

        # user decided to rest analysis
        try:
            # Revert to original file
            if self.resdict["SOURCE"] in [
                "OTB", "DEMUSE", "CUSTOMCSV", "DELSYS",
            ]:
                # Use the resdict copy
                self.resdict = self.resdict_copy_of_original

                # Update Filespecs
                self.n_channels.configure(
                    text="N Channels: " + str(len(self.resdict["RAW_SIGNAL"].columns)),
                    font=("Segoe UI", 15, ("bold")),
                )
                self.n_of_mus.configure(
                    text="N of MUs: " + str(self.resdict["NUMBER_OF_MUS"]),
                    font=("Segoe UI", 15, "bold"),
                )
                self.file_length.configure(
                    text="File Length: " + str(self.resdict["EMG_LENGTH"]),
                    font=("Segoe UI", 15, "bold"),
                )

                # Update Plot
                self.in_gui_plotting(resdict=self.resdict)

            elif self.resdict["SOURCE"] in [
                "OTB_REFSIG", "CUSTOMCSV_REFSIG", "DELSYS_REFSIG"
            ]:
                # Use the resdict copy
                self.resdict = self.resdict_copy_of_original

                # Reconfigure labels for refsig
                self.n_channels.configure(
                    text="N Channels: " + str(len(self.resdict["REF_SIGNAL"].columns)),
                    font=("Segoe UI", 15, ("bold")),
                )
                self.n_of_mus.configure(
                    text="N of MUs: N/A",
                    font=("Segoe UI", 15, "bold"),
                )
                self.file_length.configure(
                    text="File Length: "
                    + str(len(self.resdict["REF_SIGNAL"].iloc[:, 0])),
                    font=("Segoe UI", 15, "bold"),
                )

                # Update Plot
                self.in_gui_plotting(resdict=self.resdict, plot="refsig_off")

            # Clear frame for output
            if hasattr(self, "terminal"):
                self.terminal = ttk.LabelFrame(
                    self, text="Result Output", height=150, relief="ridge"
                )
                self.terminal.grid(
                    column=0,
                    row=1,
                    columnspan=2,
                    pady=5,
                    padx=5,
                    sticky=(N, S, W, E),
                )  # Repeat original settings in init

            # Delete previous analyses results
            self.delete_previous_analyses_results()

        except AttributeError as e:
            show_error_dialog(
                parent=self,
                error=e,
                solution=str("Make sure a file is loaded."),
            )

        except FileNotFoundError as e:
            show_error_dialog(
                parent=self,
                error=e,
                solution=str("Make sure a file is loaded."),
            )

    def delete_previous_analyses_results(self):
        """
        Instance method to delete the objects storing the analyses results.
        """

        # Check for attributes and delete them if present
        if hasattr(self, "mvc_df"):
            del self.mvc_df
        if hasattr(self, "rfd"):
            del self.rfd
        if hasattr(self, "mu_prop_df"):
            del self.mu_prop_df
        if hasattr(self, "mus_dr"):
            del self.mus_dr
        if hasattr(self, "mu_thresholds"):
            del self.mu_thresholds

    # ----------------------------------------------------------------------------------------------
    # Plotting inside of GUI

    def in_gui_plotting(self, resdict, plot="idr"):
        """
        Instance method to plot any analysis results in the GUI for inspection.
        Plots are updated during the analysis process.

        Executed when button "View MUs" in master GUI window is pressed or
        when the original input file is changed.

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
                    emgfile=resdict,
                    showimmediately=False,
                )
            elif plot == "idr":
                self.fig = openhdemg.plot_idr(
                    emgfile=resdict,
                    showimmediately=False,
                )
            elif plot == "refsig_fil":
                self.fig = openhdemg.plot_refsig(
                    emgfile=resdict,
                    showimmediately=False,
                )
            elif plot == "refsig_off":
                self.fig = openhdemg.plot_refsig(
                    emgfile=resdict,
                    showimmediately=False,
                )

            # Remove previous figure
            if hasattr(self, 'canvas'):
                self.canvas.get_tk_widget().destroy()

            # Pack figure inside logo_canvas. This is more reliable and should
            # be more efficient.
            self.canvas = FigureCanvasTkAgg(self.fig, master=self.logo_canvas)
            self.canvas.get_tk_widget().pack(
                expand=True, fill="both", padx=5, pady=5,
            )

            # Add toolbar
            toolbar = NavigationToolbar2Tk(
                self.canvas,
                self.right,
                pack_toolbar=False,
            )
            toolbar.grid(row=5, column=0, sticky=(S, E), padx=5, pady=5)
            plt.close()

        except AttributeError as e:
            show_error_dialog(
                parent=self,
                error=e,
                solution=str("Make sure a file is loaded."),
            )

    # ----------------------------------------------------------------------------------------------
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

        # Display results
        # Clear/recreate frame for output
        if hasattr(self, "terminal"):
            self.terminal = ttk.LabelFrame(
                self, text="Result Output", height=150, relief="ridge",
            )
            self.terminal.grid(
                column=0,
                row=1,
                columnspan=2,
                pady=5,
                padx=5,
                sticky=(N, S, W, E),
            )  # Repeat original settings in init

        table = Table(
            self.terminal,
            dataframe=input_df,
            showtoolbar=False,
            showstatusbar=False,
            height=100,
            width=100,
        )

        # Resize column width
        """ options = {"cellwidth": 10}
        config.apply_options(options, table) """

        # Show results
        table.show()


# ----------------------------------------------------------------------------------------------
def run_main():
    # Run GUI upon calling
    if __name__ == "__main__":
        app = emgGUI()
        app._state_before_windows_set_titlebar_color = "zoomed"
        app.mainloop()


if __name__ == "__main__":
    app = emgGUI()
    app._state_before_windows_set_titlebar_color = "zoomed"
    app.mainloop()
