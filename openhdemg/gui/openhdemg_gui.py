"""
This file contains the gui functionalities of openhdemg.
"""

import os
import tkinter as tk
import customtkinter
import webbrowser
from tkinter import ttk, filedialog, Canvas
from tkinter import StringVar, Tk, N, S, W, E, DoubleVar
from pandastable import Table, config

from PIL import Image

import matplotlib.pyplot as plt
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import pandas as pd

matplotlib.use("TkAgg")

import openhdemg.library as openhdemg


class emgGUI:
    """
    A class representing a Tkinter TK instance.

    This class is used to create a graphical user interface for
    the openhdemg library.

    Attributes
    ----------
    self.auto_eval : int, default 0
        If auto > 0, the script automatically removes the offset based on the number
        of samples passed in input.
    self.b_firings_rec : int, default 4
        The number of firings at recruitment and derecruitment to consider for the
        calculation of the DR.
    self.b_firings_ste : int, default 10
        The number of firings to consider for the calculation of the DR at the start and at the end
        of the steady-state phase.
    self.canvas : matplotlib.backends.backend_tkagg
        Canvas for plotting figures inside the GUI.
    self.channels : int or list
        The channel (int) or channels (list of int) to plot.
        The list can be passed as a manually-written with: "0,1,2,3,4,5...,n",
        channels is expected to be with base 0.
    self.convert : str, default Multiply
        The kind of conversion applied to the Refsig during Refsig conversion. Can be "Multiply" or "Divide".
    self.convert_factor : float, default 2.5
        Factore used during Refsig converison when multiplication or division is applied.
    self.cutoff_freq : int, default 20
        The cut-off frequency in Hz.
    self.ct_event : str, default "rt_dert"
        When to calculate the thresholds. Input parameters for event_ are:
            "rt_dert" means that both recruitment and derecruitment tresholds will be calculated.
            "rt" means that only recruitment tresholds will be calculated.
            "dert" means that only derecruitment tresholds will be calculated.
    self.dr_event : str, default "rec_derec_steady"
        When to calculate the DR. Input parameters for event_ are:
            "rec_derec_steady" means that the DR is calculated at recruitment, derecruitment and
            during the steady-state phase.
            "rec" means that the DR is calculated at recruitment.
            "derec" means that the DR is calculated at derecruitment.
            "rec_derec" means that the DR is calculated at recruitment and derecruitment.
            "steady" means that the DR is calculated during the steady-state phase.
    self.end_area, self.start_area : int
        The start and end of the selection for file resizing (can be used for code automation).
    self.exportable_df : pd.DataFrame
        A pd.DataFrame containing the results of the analysis.
    self.fig : matplotlib.figure
        Figure to be plotted on Canvas.
    self.filename : str
        String and name of the file to be analysed.
    self.filepath : str
        String containing the path to EMG file selected for analysis.
    self.filetype : str
        String containing the filetype of import EMG file.
        Filetype can be "OPENHDEMG", "OTB", "DEMUSE", "OTB_REFSIG", "CUSTOMCSV", "CUSTOMCSV_REFSIG".
    self.filter_order : int, default 4
        The filter order.
    self.firings_rec : int, default 4
        The number of firings at recruitment and derecruitment to consider for the calculation
        of the DR.
    self.firings_ste : int, default 10
        The number of firings to consider for the calculation of the DR at the start and at the end
        of the steady-state phase.
    self.first_fig : matplotlib.figure
        Figure frame determinining size of all figures that are plotted on canvas.
    self.head : tk.toplevel
        New tk.toplevel instance created everytime upon opnening a new window. This is needed
        for having a seperate window open.
    self.left : tk.frame
        Left frame inside of master that contains all buttons and filespecs.
    self.linewidth : float, default 0.5
        The width of the vertical lines representing the MU firing.
    self.logo :
        String containing the path to image file containing logo of openhdemg.
    self.logo_canvas : tk.canvas
        Canvas to display logo of Open_HG-EMG when openend.
    self.master: tk
        TK master window containing all widget children for this GUI.
    self.mus_dr: pd.DataFrame
        A pd.DataFrame containing the requested DR.
    self.mu_numb : int or list, default "all"
        By default, IPTS of all the MUs is plotted.
        Otherwise, a single MU (int) or multiple MUs (list of int) can be specified.
        The list can be passed as a manually-written list: "0,1,2,3,4,5,...,n",
        self.m_numb is expected to be with base 0 (i.e., the first MU in the file is the number 0).
    self.mu_numb_idr : int or list, default "all"
        By default, IDR of all the MUs is plotted.
        Otherwise, a single MU (int) or multiple MUs (list of int) can be specified.
        The list can be passed as a manually-written list: "0,1,2,3,4,5,...,n",
        self.m_numb_idr is expected to be with base 0 (i.e., the first MU in the
        file is the number 0).
    self.mu_to_remove : int
        The MUs to remove. If a single MU has to be removed, this should be an
        int (number of the MU).
        self.mu_to_remove is expected to be with base 0
        (i.e., the first MU in the file is the number 0).
    self.mu_to_edit : int
        The MUs to edit singularly. If a single MU has to be edited, this should be an
        int (number of the MU).
        self.mu_to_edit is expected to be with base 0
        (i.e., the first MU in the file is the number 0).
    self.mu_thresholds : pd.DataFrame
        A DataFrame containing the requested thresholds.
    self.mvc : float
        The MVC value in the original unit of measurement.
    self.mvc_df : pd.DataFrame
        A Dataframe containing the detected MVC value.
    self.mvc_value : float
        The MVC value specified during Refsig conversion.
    self.offsetval: float, default 0
        Value of the offset. If offsetval is 0 (default), the user will be asked to manually
        select an aerea to compute the offset value.
        Otherwise, the value passed to offsetval will be used. Negative offsetval can be passed.
    self.resdict : dict
        Dictionary derived from input EMG file for further analysis.
    self.rfd_df : pd.DataFrame
        A Dataframe containing the calculated RFD values.
    self.rfdms : list, default [50, 100, 150, 200]
        Milliseconds (ms). A list containing the ranges in ms to calculate the RFD.
    self.right : tk.frame
        Left frame inside of master that contains plotting canvas.
    self.terminal : ttk.Labelframe
        Tkinter labelframe that is used to display the results table in the GUI.
    self.mat_code : str
        The code containing the matrix identification number.
    self.mat_orientation : int
        The orientation of the matrix in degrees. Can be 0, 180.
    self.deriv_config : str
        The Method used to calculate the MUs deviation.
    self.muap_config : str
        The Method used to calculate the MUs deviation.
    self.deriv_matrix : str
        Column of the matrix to be plotted.
    self.size_fig : str, default [20,15]
        Size of the figure to be plotted in centimeter.
    self.ref_but : str, default "False"
        String value used to determine if reference signal should be
        added to the plot.
    self.time_but : str, default "False"
        String value used to determine if time in seconds should be used
        in x-axis of plotting.
    muap_munum : int
        Number of motor unit to be plotted.
    muap_time : int
        Time window to be plotted.
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
    self.advanced_method : tk.Stringvar()
        Stringvariable containing the selected method of advanced
        analysis.
    self.matrix_rc : tk.StringVar()
        String containing the channel number of emgfile when
        matri codes are bypassed. Used in plot window.
    self.matrix_rc_adv : tk.StringVar()
        String containing the channel number of emgfile when
        matri codes are bypassed. Used in advanced window.
    self.emgfile1 : pd.Dataframe
        Dataframe object containing the loaded first emgfile used
        for MU tracking.
    self.emgfile2 : pd.Dataframe
        Dataframe object containing the loaded first emgfile used
        for MU tracking.
    self.thresh_adv : tk.Stringvar()
        Stringvariable containing the selected threshold for MU tracking.
    self.filter_adv : tk.Boolenvar()
        Boolean determining whether filtering should be applied during MU
        tracking.
    self.show_adv : tk.Boolenvar()
        Boolean determining whether results of MU tracking should be plotted.
    self.exclude_thres : tk.Boolenvar()
        Boolean determining whether values below treshold should be excluded
        during MU tracking.
    self.which_adv : tk.Stringvar()
        Stringvariable determining how MU duplicates are removed.
    self.time_window : tk.Stringvar()
        Stringvariable determining the time window for duplicate removal
        and tracking.

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
    export_to_excel()
        Saves the analysis results to a .xlsx file.
        Executed when button "Save Results" in master GUI window pressed.
    reset_analysis()
        Resets the whole analysis, restores the original input file and the graph.
        Executed when button "Reset analysis" in master GUI window pressed.
    in_gui_plotting()
        Method used for creating plot inside the GUI (on the GUI canvas).
        Executed when button "View MUs" in master GUI window pressed.
    sort_mus()
        Method used to sort motor units in Plot according to recruitement order.
        Executed when button "Sort MUs" in master GUI window pressed.
    remove_mus()
        Opens seperate window to select motor units to be removed.
        Executed when button "Remove MUs" in master GUI window pressed.
    remove()
        Method used to remove single motor units.
    edit_refsig()
        Opens seperate window to edit emg reference signal.
        Executed when button "RefSig Editing" in master GUI window pressed.
    filter_refsig()
        Method used to filter the emg reference signal.
    remove_offset()
        Method used to remove offset of emg reference signal.
    resize_file()
        Opens seperate window to resize emg file / reference signal.
        Executed when button "Resize File" in master GUI window pressed.
    analyze_force()
        Opens seperate window to analyze force signal/values.
        Executed when button "Analyze force" in master GUI window pressed.
    get_mvc()
        Method used to calculate/select MVC.
    det_rfd()
        Method used to calculated RFD based on selected startpoint.
    mu_analysis()
        Opens seperate window to calculated specific motor unit properties.
        Executed when button "MU properties" in master GUI window pressed.
    compute_mu_threshold()
        Method used to calculate motor unit recruitement thresholds.
    compute_mu_dr()
       Method used to calculate motor unit discharge rate.
    basic_mus_analysis()
        Method used to calculate basic motor unit properties.
    plot_emg()
        Opens seperate window to plot emgsignal/motor unit properties.
        Executed when button "Plot EMG" in master GUI window pressed.
    plt_emgsignal()
        Method used to plot emgsignal.
    plt_idr()
        Method used to plot instanteous discharge rate.
    plt_ipts()
        Method used to plot the motor unit puls train (i.e., non-binary firing)
    plt_refsignal()
        Method used to plot the motor unit reference signal.
    plt_mupulses()
        Method used to plot the motor unit pulses.
    plot_derivation()
        Method to plot the differential derivation of the RAW_SIGNAL
        by matrix column.
    plot_muaps()
        Method to plot motor unit action potenital obtained from STA
        from one or multiple MUs.
    advanced_analysis()
        Method to open top-level windows based on the selected advanced method.
    on_filetype_change()
        Method do display extension factor combobx when filetype loaded is
        OTB.
    open_emgfile1()
        Method to open EMG file based on the selected file type and extension factor.
    open_emgfile2()
        Method to open EMG file based on the selected file type and extension factor.
    track_mus()
        Method to perform MUs tracking on the loaded EMG files.
    display_results()
        Method used to display result table containing analysis results.
    to_percent()
        Method that converts Refsig to a percentag value. Should only be used when the Refsig is in absolute values.
    convert_refsig()
        Method that converts Refsig by multiplication or division.

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
        # Set up GUI
        self.master = master
        self.master.title("openhdemg")
        master_path = os.path.dirname(os.path.abspath(__file__))
        iconpath = master_path + "/gui_files/Icon.ico"
        self.master.iconbitmap(iconpath)
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)

        # Create left side framing for functionalities
        self.left = ttk.Frame(self.master, padding="10 10 12 12")
        self.left.grid(column=0, row=0, sticky="nsew")
        self.left.columnconfigure(0, weight=1)
        self.left.columnconfigure(1, weight=1)
        self.left.columnconfigure(2, weight=1)
        self.left.columnconfigure(3, weight=1)
        self.left.rowconfigure(0, weight=1)
        self.left.rowconfigure(1, weight=1)
        self.left.rowconfigure(2, weight=1)
        self.left.rowconfigure(3, weight=1)
        self.left.rowconfigure(4, weight=1)
        self.left.rowconfigure(5, weight=1)
        self.left.rowconfigure(6, weight=1)
        self.left.rowconfigure(7, weight=1)
        self.left.rowconfigure(8, weight=1)
        self.left.rowconfigure(9, weight=1)
        self.left.rowconfigure(10, weight=1)
        self.left.rowconfigure(11, weight=1)
        self.left.rowconfigure(12, weight=1)
        self.left.rowconfigure(13, weight=1)
        self.left.rowconfigure(14, weight=1)
        self.left.rowconfigure(15, weight=1)
        self.left.rowconfigure(16, weight=1)
        self.left.rowconfigure(17, weight=1)
        self.left.rowconfigure(18, weight=1)

        # Style
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TToplevel", background="LightBlue4")
        style.configure("TFrame", background="LightBlue4")
        style.configure(
            "TLabel",
            font=("Lucida Sans", 12),
            foreground="black",
            background="LightBlue4",
        )
        style.configure("TButton", foreground="black", font=("Lucida Sans", 11))
        style.configure("TEntry", font=("Lucida Sans", 12), foreground="black")
        style.configure("TCombobox", background="LightBlue4", foreground="black")
        style.configure("TLabelFrame", foreground="black", font=("Lucida Sans", 16))

        # Specify Signal
        self.filetype = StringVar()
        signal_value = ("OPENHDEMG", "OTB", "DEMUSE", "OTB_REFSIG", "CUSTOMCSV", "CUSTOMCSV_REFSIG")
        signal_entry = ttk.Combobox(
            self.left, text="Signal", width=10, textvariable=self.filetype
        )
        signal_entry["values"] = signal_value
        signal_entry["state"] = "readonly"
        signal_entry.grid(column=0, row=1, sticky=(W, E))
        self.filetype.set("Type of file")
        # Trace filetype to apply function when changeing
        self.filetype.trace("w", self.on_filetype_change)

        # Load file
        load = ttk.Button(self.left, text="Load File", command=self.get_file_input)
        load.grid(column=0, row=3, sticky=W)

        # File specifications
        ttk.Label(self.left, text="Filespecs:").grid(column=1, row=1, sticky=(W, E))
        ttk.Label(self.left, text="N Channels:").grid(column=1, row=2, sticky=(W, E))
        ttk.Label(self.left, text="N of MUs:").grid(column=1, row=3, sticky=(W, E))
        ttk.Label(self.left, text="File length:").grid(column=1, row=4, sticky=(W, E))
        separator0 = ttk.Separator(self.left, orient="horizontal")
        separator0.grid(column=0, columnspan=3, row=5, sticky=(W, E))

        # COMMENT: This is commented out because it is not yet functional.
        # Decompose file
        # decompose = ttk.Button(self.left,
        #                        text="Decompose",
        #                        command=self.decompose_file)
        # decompose.grid(row=3, column=0, sticky=W)

        # Save File
        save = ttk.Button(self.left, text="Save File", command=self.save_emgfile)
        save.grid(column=0, row=6, sticky=W)
        separator1 = ttk.Separator(self.left, orient="horizontal")
        separator1.grid(column=0, columnspan=3, row=7, sticky=(W, E))

        # Export to Excel
        export = ttk.Button(
            self.left, text="Save Results", command=self.export_to_excel
        )
        export.grid(column=1, row=6, sticky=(W, E))

        # View Motor Unit Firings
        firings = ttk.Button(self.left, text="View MUs", command=self.in_gui_plotting)
        firings.grid(column=0, row=8, sticky=W)

        # Sort Motor Units
        sorting = ttk.Button(self.left, text="Sort MUs", command=self.sort_mus)
        sorting.grid(column=1, row=8, sticky=(W, E))
        separator2 = ttk.Separator(self.left, orient="horizontal")
        separator2.grid(column=0, columnspan=3, row=9, sticky=(W, E))

        # Remove Motor Units
        remove_mus = ttk.Button(self.left, text="Remove MUs", command=self.remove_mus)
        remove_mus.grid(column=0, row=10, sticky=W)

        # COMMENT: This is commented because it is not fully functional
        # Edit Motor Units
        # edit_mus = ttk.Button(self.left,
        #                      text="Edit MUs",
        #                      command=self.editing_mus)
        # edit_mus.grid(column=1, row=10, sticky=W)

        separator3 = ttk.Separator(self.left, orient="horizontal")
        separator3.grid(column=0, columnspan=3, row=11, sticky=(W, E))

        # Filter Reference Signal
        reference = ttk.Button(
            self.left, text="RefSig Editing", command=self.edit_refsig
        )
        reference.grid(column=0, row=12, sticky=W)

        # Resize File
        resize = ttk.Button(self.left, text="Resize File", command=self.resize_file)
        resize.grid(column=1, row=12, sticky=(W, E))
        separator4 = ttk.Separator(self.left, orient="horizontal")
        separator4.grid(column=0, columnspan=3, row=13, sticky=(W, E))

        # Force Analysis
        force = ttk.Button(self.left, text="Analyse Force", command=self.analyze_force)
        force.grid(column=0, row=14, sticky=W)
        separator5 = ttk.Separator(self.left, orient="horizontal")
        separator5.grid(column=0, columnspan=3, row=15, sticky=(W, E))

        # Motor Unit properties
        mus = ttk.Button(self.left, text="MU Properties", command=self.mu_analysis)
        mus.grid(column=1, row=14, sticky=W)
        separator6 = ttk.Separator(self.left, orient="horizontal")
        separator6.grid(column=0, columnspan=3, row=17, sticky=(W, E))

        # Plot EMG
        plots = ttk.Button(self.left, text="Plot EMG", command=self.plot_emg)
        plots.grid(column=0, row=16, sticky=W)
        separator7 = ttk.Separator(self.left, orient="horizontal")
        separator7.grid(column=0, columnspan=3, row=19, sticky=(W, E))

        # Reset Analysis
        reset = ttk.Button(
            self.left, text="Reset Analysis", command=self.reset_analysis
        )
        reset.grid(column=1, row=18, sticky=(W, E))

        # Advanced tools
        # Create seperate style for this button
        advanced_button_style = ttk.Style()
        advanced_button_style.theme_use("clam")
        advanced_button_style.configure(
            "B.TButton",
            foreground="white",
            background="black",
            font=("Lucida Sans", 11),
        )

        advanced = ttk.Button(
            self.left,
            command=self.open_advanced_tools,
            text="Advanced Tools",
            style="B.TButton",
        )
        advanced.grid(row=20, column=0, columnspan=2, sticky=(W, E))

        # Create right side framing for functionalities
        self.right = ttk.Frame(self.master, padding="10 10 12 12")
        self.right.grid(column=1, row=0, sticky=(N, S, E, W))
        self.right.columnconfigure(0, weight=1)
        self.right.columnconfigure(1, weight=1)

        # Create empty figure
        self.first_fig = Figure(figsize=(20 / 2.54, 15 / 2.54))
        self.canvas = FigureCanvasTkAgg(self.first_fig, master=self.right)
        self.canvas.get_tk_widget().grid(row=0, column=0, rowspan=5)

        # Create logo figure
        self.logo_canvas = Canvas(self.right, height=590, width=800, bg="white")
        self.logo_canvas.grid(row=0, column=0, rowspan=5)

        logo_path = master_path + "/gui_files/logo.png"  # Get logo path
        self.logo = tk.PhotoImage(file=logo_path)

        # self.matrix = tk.PhotoImage(file="Matrix_illustration.png")
        self.logo_canvas.create_image(400, 300, anchor="center", image=self.logo)

        # Create info button
        # Information Button
        info_path = master_path + "/gui_files/Info.png"  # Get infor button path
        self.info = customtkinter.CTkImage(light_image=Image.open(info_path),
                                             size=(30,30))
        info_button = customtkinter.CTkButton(
            self.right,
            image=self.info,
            text="",
            width=30,
            height=30,
            bg_color="LightBlue4",
            fg_color="LightBlue4",
            command=lambda: (
                (
                    webbrowser.open("https://www.giacomovalli.com/openhdemg/gui_intro/")
                ),
            ),
        )
        info_button.grid(row=0, column=1, sticky=E)

        # Button for online tutorials
        online_path = master_path + "/gui_files/Online.png"
        self.online = customtkinter.CTkImage(light_image=Image.open(online_path),
                                             size=(30,30))
        online_button = customtkinter.CTkButton(
            self.right,
            image=self.online,
            text="",
            width=30,
            height=30,
            bg_color="LightBlue4",
            fg_color="LightBlue4",
            command=lambda: (
                (
                    webbrowser.open("https://www.giacomovalli.com/openhdemg/tutorials/setup_working_env/")
                ),
            ),
        )
        online_button.grid(row=1, column=1, sticky=E)

        # Button for dev information
        redirect_path = master_path + "/gui_files/Redirect.png"
        self.redirect = customtkinter.CTkImage(light_image=Image.open(redirect_path),
                                             size=(30,30))
        redirect_button = customtkinter.CTkButton(
            self.right,
            image=self.redirect,
            text="",
            width=30,
            height=30,
            bg_color="LightBlue4",
            fg_color="LightBlue4",
            command=lambda: (
                (
                    webbrowser.open("https://www.giacomovalli.com/openhdemg/about-us/#meet-the-developers")
                ),
            ),
        )
        redirect_button.grid(row=2, column=1, sticky=E)

        # Button for contact information
        contact_path = master_path + "/gui_files/Contact.png"
        self.contact = customtkinter.CTkImage(light_image=Image.open(contact_path),
                                             size=(30,30))
        contact_button = customtkinter.CTkButton(
            self.right,
            image=self.contact,
            text="",
            width=30,
            height=30,
            bg_color="LightBlue4",
            fg_color="LightBlue4",
            command=lambda: (
                (
                    webbrowser.open("https://www.giacomovalli.com/openhdemg/contacts/")
                ),
            ),
        )
        contact_button.grid(row=3, column=1, sticky=E)

        # Button for citatoin information
        cite_path = master_path + "/gui_files/Cite.png"
        self.cite = customtkinter.CTkImage(light_image=Image.open(cite_path),
                                             size=(30,30))
        cite_button = customtkinter.CTkButton(
            self.right,
            image=self.cite,
            text="",
            width=30,
            height=30,
            bg_color="LightBlue4",
            fg_color="LightBlue4",
            command=lambda: (
                # Check user OS for pdf opening
                (
                    webbrowser.open("https://www.giacomovalli.com/openhdemg/cite-us/")
                ),
            ),
        )
        cite_button.grid(row=4, column=1, sticky=E)

        for child in self.left.winfo_children():
            child.grid_configure(padx=5, pady=5)

    ## Define functionalities for buttons used in GUI master window

    def get_file_input(self):
        """
        Instance Method to load the file for analysis. The user is asked to select the file.

        Executed when the button "Load File" in master GUI window is pressed.

        See Also
        --------
        emg_from_demuse, emg_from_otb, refsig_from_otb and emg_from_json in library.
        """
        try:
            if self.filetype.get() in ["OTB", "DEMUSE", "OPENHDEMG", "CUSTOMCSV"]:
                # Check filetype for processing
                if self.filetype.get() == "OTB":
                    # Ask user to select the decomposed file
                    file_path = filedialog.askopenfilename(
                        title="Open OTB file", filetypes=[("MATLAB files", "*.mat")]
                    )
                    self.file_path = file_path
                    # Load file
                    self.resdict = openhdemg.emg_from_otb(
                        filepath=self.file_path,
                        ext_factor=int(self.extension_factor.get()),
                    )

                elif self.filetype.get() == "DEMUSE":
                    # Ask user to select the file
                    file_path = filedialog.askopenfilename(
                        title="Open DEMUSE file", filetypes=[("MATLAB files", "*.mat")]
                    )
                    self.file_path = file_path

                    # load file
                    self.resdict = openhdemg.emg_from_demuse(filepath=self.file_path)

                elif self.filetype.get() == "OPENHDEMG":
                    # Ask user to select the file
                    file_path = filedialog.askopenfilename(
                        title="Open JSON file", filetypes=[("JSON files", "*.json")]
                    )
                    self.file_path = file_path

                    # load OPENHDEMG (.json)
                    self.resdict = openhdemg.emg_from_json(filepath=self.file_path)

                else:
                    # Ask user to select the file
                    file_path = filedialog.askopenfilename(
                        title="Open CUSTOMCSV file",
                        filetypes=[("CSV files", "*.csv")],
                    )
                    self.file_path = file_path

                    # load file
                    self.resdict = openhdemg.emg_from_customcsv(filepath=self.file_path)

                # Get filename
                filename = os.path.splitext(os.path.basename(file_path))[0]
                self.filename = filename

                # Add filename to label
                self.master.title(self.filename)

                # Add filespecs
                ttk.Label(
                    self.left, text=str(len(self.resdict["RAW_SIGNAL"].columns))
                ).grid(column=2, row=2, sticky=(W, E))
                ttk.Label(self.left, text=str(self.resdict["NUMBER_OF_MUS"])).grid(
                    column=2, row=3, sticky=(W, E)
                )
                ttk.Label(self.left, text=str(self.resdict["EMG_LENGTH"])).grid(
                    column=2, row=4, sticky=(W, E)
                )   
                """
                # BUG with "OPENHDEMG" type we identify all files saved from openhdemg,
                regardless of the content. This will result in an error for ttk.Label
                self.resdict["NUMBER_OF_MUS"] and self.resdict["EMG_LENGTH"].
                """

            else:
                # Ask user to select the refsig file
                if self.filetype.get() == "OTB_REFSIG":
                    file_path = filedialog.askopenfilename(
                        title="Open OTB_REFSIG file",
                        filetypes=[("MATLAB files", "*.mat")],
                    )
                    self.file_path = file_path
                    # load refsig
                    self.resdict = openhdemg.refsig_from_otb(filepath=self.file_path)

                else:  # CUSTOMCSV_REFSIG
                    file_path = filedialog.askopenfilename(
                        title="Open CUSTOMCSV_REFSIG file",
                        filetypes=[("CSV files", "*.csv")],
                    )
                    self.file_path = file_path
                    # load refsig
                    self.resdict = openhdemg.refsig_from_customcsv(filepath=self.file_path)

                # Get filename
                filename = os.path.splitext(os.path.basename(file_path))[0]
                self.filename = filename

                # Add filename to label
                self.master.title(self.filename)

                # Reconfigure labels for refsig
                ttk.Label(
                    self.left, text=str(len(self.resdict["REF_SIGNAL"].columns))
                ).grid(column=2, row=2, sticky=(W, E))
                ttk.Label(self.left, text="NA").grid(column=2, row=3, sticky=(W, E))
                ttk.Label(self.left, text="        ").grid(
                    column=2, row=4, sticky=(W, E)
                )

        except ValueError:
            tk.messagebox.showerror(
                "Information",
                "When an OTB file is loaded, make sure to "
                + "\nspecify an extension factor (number) first.",
            )

    def on_filetype_change(self, *args):
        """
        This function is called when the value of the filetype variable is changed.
        When the filetype is set to "OTB" it will create a second combobox on the grid at column 0 and row 2,
        and when the filetype is set to something else it will remove the second combobox from the grid.
        """
        # Add a combobox containing the OTB extension factors
        # in case an OTB file is loaded
        if self.filetype.get() == "OTB":
            self.extension_factor = StringVar()
            self.otb_combobox = ttk.Combobox(
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
                textvariable=self.extension_factor,
                state="readonly",
            )
            self.otb_combobox.grid(column=0, row=2, sticky=(W, E), padx=5)
            self.otb_combobox.set("Extension Factor")

        # Forget widget when filetype is changes
        else:
            if hasattr(self, "otb_combobox"):
                self.otb_combobox.grid_forget()

    def decompose_file(self):
        pass

    def save_emgfile(self):
        """
        Instance method to save the edited emgfile. Results are saves in .json file.

        Executed when the button "Save File" in master GUI window is pressed.

        Raises
        ------
        AttributeError
            When file was not loaded in the GUI.

        See Also
        --------
        save_json_emgfile in library.
        """
        try:
            # Ask user to select the directory and file name
            save_filepath = filedialog.asksaveasfilename(
                defaultextension=".*",
                filetypes=(("JSON files", "*.json"), ("all files", "*.*")),
            )

            # Get emgfile
            save_emg = self.resdict

            # Save json file
            openhdemg.save_json_emgfile(emgfile=save_emg, filepath=save_filepath)

        except AttributeError:
            tk.messagebox.showerror("Information", "Make sure a file is loaded.")

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
            writer = pd.ExcelWriter(path + "/Results_" + self.filename + ".xlsx")

            # Check for attributes and write sheets
            if hasattr(self, "mvc_df"):
                self.mvc_df.to_excel(writer, sheet_name="MVC")

            if hasattr(self, "rfd"):
                self.rfd.to_excel(writer, sheet_name="RFD")

            if hasattr(self, "exportable_df"):
                self.exportable_df.to_excel(writer, sheet_name="Basic MU Properties")

            if hasattr(self, "mus_dr"):
                self.mus_dr.to_excel(writer, sheet_name="MU Discharge Rate")

            if hasattr(self, "mu_thresholds"):
                self.mu_thresholds.to_excel(writer, sheet_name="MU Thresholds")

            writer.close()

        except IndexError:
            tk.messagebox.showerror(
                "Information", "Please conduct at least one analysis before saving"
            )

        except AttributeError:
            tk.messagebox.showerror("Information", "Make sure a file is loaded.")

        except PermissionError:
            tk.messagebox.showerror(
                "Information",
                "If /Results.xlsx already opened, please close."
                + "\nOtherwise ignore as you propably canceled the saving progress.",
            )

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
        if tk.messagebox.askokcancel(
            "Attention", "Do you really want to reset the analysis?"
        ):
            # user decided to rest analysis
            try:
                # reload original file
                if self.filetype.get() in ["OTB", "DEMUSE", "OPENHDEMG", "CUSTOMCSV"]:
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

                    # Update Filespecs
                    ttk.Label(
                        self.left, text=str(len(self.resdict["RAW_SIGNAL"].columns))
                    ).grid(column=2, row=2, sticky=(W, E))
                    ttk.Label(self.left, text=str(self.resdict["NUMBER_OF_MUS"])).grid(
                        column=2, row=3, sticky=(W, E)
                    )
                    ttk.Label(self.left, text=str(self.resdict["EMG_LENGTH"])).grid(
                        column=2, row=4, sticky=(W, E)
                    )

                else:
                    # load refsig
                    if self.filetype.get() == "OTB_REFSIG":
                        self.resdict = openhdemg.refsig_from_otb(filepath=self.file_path)
                    else:  # CUSTOMCSV_REFSIG
                        self.resdict = openhdemg.refsig_from_customcsv(filepath=self.file_path)

                    # Recondifgure labels for refsig
                    ttk.Label(
                        self.left, text=str(len(self.resdict["REF_SIGNAL"].columns))
                    ).grid(column=2, row=2, sticky=(W, E))
                    ttk.Label(self.left, text="NA").grid(column=2, row=3, sticky=(W, E))
                    ttk.Label(self.left, text="        ").grid(
                        column=2, row=4, sticky=(W, E)
                    )

                # Update Plot
                if hasattr(self, "fig"):
                    self.in_gui_plotting()

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

            except AttributeError:
                tk.messagebox.showerror("Information", "Make sure a file is loaded.")

            except FileNotFoundError:
                tk.messagebox.showerror("Information", "Make sure a file is loaded.")

    def open_advanced_tools(self):
        """
        Open a window for advanced analysis tools.
        """
        # Open window
        self.a_window = tk.Toplevel(bg="LightBlue4", height=200)
        self.a_window.title("Advanced Tools Window")
        self.a_window.iconbitmap(
            os.path.dirname(os.path.abspath(__file__)) + "/gui_files/Icon.ico"
        )
        self.a_window.grab_set()

        # Add Label
        ttk.Label(
            self.a_window, text="Select tool and matrix:", font=("Verdana", 14, "bold")
        ).grid(row=0, column=0)

        # Analysis Tool
        ttk.Label(self.a_window, text="Analysis Tool").grid(
            row=2, column=0, sticky=(W, E)
        )
        # Add Selection Combobox
        self.advanced_method = StringVar()
        adv_box = ttk.Combobox(
            self.a_window, width=15, textvariable=self.advanced_method
        )
        adv_box["values"] = (
            "Motor Unit Tracking",
            "Duplicate Removal",
            "Conduction Velocity",
        )
        adv_box["state"] = "readonly"
        adv_box.grid(row=2, column=1, sticky=(W, E))
        adv_box.set("Motor Unit Tracking")

        # Matrix Orientation
        ttk.Label(self.a_window, text="Matrix Orientation").grid(
            row=3, column=0, sticky=(W, E)
        )
        self.mat_orientation_adv = StringVar()
        orientation = ttk.Combobox(
            self.a_window, width=8, textvariable=self.mat_orientation_adv
        )
        orientation["values"] = ("0", "180")
        orientation["state"] = "readonly"
        orientation.grid(row=3, column=1, sticky=(W, E))
        self.mat_orientation_adv.set("180")

        # Matrix code
        ttk.Label(self.a_window, text="Matrix Code").grid(
            row=4, column=0, sticky=(W, E)
        )
        self.mat_code_adv = StringVar()
        matrix_code = ttk.Combobox(
            self.a_window, width=10, textvariable=self.mat_code_adv
        )
        matrix_code["values"] = ("GR08MM1305", "GR04MM1305", "GR10MM0808", "None")
        matrix_code["state"] = "readonly"
        matrix_code.grid(row=4, column=1, sticky=(W, E))
        self.mat_code_adv.set("GR08MM1305")
        
        # Trace variabel for updating window
        self.mat_code_adv.trace("w", self.on_matrix_none_adv)

        # Analysis Button
        adv_button = ttk.Button(
            self.a_window,
            text="Advanced Analysis",
            command=self.advanced_analysis,
            style="B.TButton",
        )
        adv_button.grid(column=0, row=7)

        # Add padding to widgets
        for child in self.a_window.winfo_children():
            child.grid_configure(padx=5, pady=5)

    def on_matrix_none_adv(self, *args):
        """
        This function is called when the value of the mat_code_adv variable is changed.

        When the variable is set to "None" it will create an Entrybox on the grid at column 1 and row 6,
        and when the mat_code_adv is set to something else it will remove the entrybox from the grid.
        """
        if self.mat_code_adv.get() == "None":
        
            self.mat_label_adv = ttk.Label(self.a_window, text="Rows, Columns:")
            self.mat_label_adv.grid(row=5, column=1, sticky = W)
            
            self.matrix_rc_adv = StringVar()
            self.row_cols_entry_adv = ttk.Entry(self.a_window, width=8, textvariable= self.matrix_rc_adv)
            self.row_cols_entry_adv.grid(row=6, column=1, sticky = W, padx=5, pady=2)
            self.matrix_rc_adv.set("13,5")
        
        else:
            if hasattr(self, "row_cols_entry_adv"):
                self.row_cols_entry_adv.grid_forget()
                self.mat_label_adv.grid_forget()
        
        self.a_window.update_idletasks()

    # -----------------------------------------------------------------------------------------------
    # Plotting inside of GUI

    def in_gui_plotting(self, plot="idr"):
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
            if self.filetype.get() in ["OTB_REFSIG", "CUSTOMCSV_REFSIG"]:
                self.fig = openhdemg.plot_refsig(
                    emgfile=self.resdict, showimmediately=False, tight_layout=True
                )
            elif plot == "idr":
                self.fig = openhdemg.plot_idr(
                    emgfile=self.resdict, showimmediately=False, tight_layout=True
                )
            elif plot == "refsig_fil":
                self.fig = openhdemg.plot_refsig(
                    emgfile=self.resdict, showimmediately=False, tight_layout=True
                )
            elif plot == "refsig_off":
                self.fig = openhdemg.plot_refsig(
                    emgfile=self.resdict, showimmediately=False, tight_layout=True
                )

            self.canvas = FigureCanvasTkAgg(self.fig, master=self.right)
            self.canvas.get_tk_widget().grid(row=0, column=0, rowspan=5)
            toolbar = NavigationToolbar2Tk(self.canvas, self.right, pack_toolbar=False)
            toolbar.grid(row=5, column=0)
            plt.close()

        except AttributeError:
            tk.messagebox.showerror("Information", "Make sure a file is loaded.")

    # -----------------------------------------------------------------------------------------------
    # Sorting of motor units

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
            self.resdict = openhdemg.sort_mus(emgfile=self.resdict)

            # Update plot
            if hasattr(self, "fig"):
                self.in_gui_plotting()

        except AttributeError:
            tk.messagebox.showerror("Information", "Make sure a file is loaded.")

    # -----------------------------------------------------------------------------------------------
    # Removal of single motor units

    def remove_mus(self):
        """
        Instance method to open "Motor Unit Removal Window". Further option to select and
        remove MUs are displayed.

        Executed when button "Remove MUs" in master GUI window is pressed.

        Raises
        ------
        AttributeError
            When no file is loaded prior to analysis.
        """
        if hasattr(self, "resdict"):
            # Create new window
            self.head = tk.Toplevel(bg="LightBlue4")
            self.head.title("Motor Unit Removal Window")
            self.head.iconbitmap(
                os.path.dirname(os.path.abspath(__file__)) + "/gui_files/Icon.ico"
            )
            self.head.grab_set()

            # Select Motor Unit
            ttk.Label(self.head, text="Select MU:").grid(
                column=0, row=0, padx=5, pady=5
            )

            self.mu_to_remove = StringVar()
            removed_mu_value = [*range(0, self.resdict["NUMBER_OF_MUS"])]
            removed_mu = ttk.Combobox(
                self.head, width=10, textvariable=self.mu_to_remove
            )
            removed_mu["values"] = removed_mu_value
            removed_mu["state"] = "readonly"
            removed_mu.grid(column=1, row=0, sticky=(W, E), padx=5, pady=5)

            # Remove Motor unit
            remove = ttk.Button(self.head, text="Remove MU", command=self.remove)
            remove.grid(column=1, row=1, sticky=(W, E), padx=5, pady=5)

        else:
            tk.messagebox.showerror("Information", "Make sure a file is loaded.")

    def remove(self):
        """
        Instance methof that actually removes a selected motor unit based on user specification.

        Executed when button "Remove MU" in Motor Unit Removal Window is pressed.
        The emgfile and the plot are subsequently updated.

        See Also
        --------
        delete_mus in library.
        """
        try:
            # Get resdict with MU removed
            self.resdict = openhdemg.delete_mus(
                emgfile=self.resdict, munumber=int(self.mu_to_remove.get())
            )
            # Upate MU number
            ttk.Label(self.left, text=str(self.resdict["NUMBER_OF_MUS"])).grid(
                column=2, row=3, sticky=(W, E)
            )

            # Update selection field
            self.mu_to_remove = StringVar()
            removed_mu_value = [*range(0, self.resdict["NUMBER_OF_MUS"])]
            removed_mu = ttk.Combobox(
                self.head, width=10, textvariable=self.mu_to_remove
            )
            removed_mu["values"] = removed_mu_value
            removed_mu["state"] = "readonly"
            removed_mu.grid(column=1, row=0, sticky=(W, E), padx=5, pady=5)

            # Update plot
            if hasattr(self, "fig"):
                self.in_gui_plotting()

        except AttributeError:
            tk.messagebox.showerror("Information", "Make sure a file is loaded.")

    # -----------------------------------------------------------------------------------------------
    # Editing of single motor Units

    # def editing_mus(self):
    #     """
    #     Instance method to edit sindle motor units. For now, this contains only plotting single MUs.
    #     More options will be added.

    #     THIS PART IS NOT YET INTEGRATED IN THE GUI.
    #     """

    #     # Create new window
    #     self.head = tk.Toplevel(bg='LightBlue4')
    #     self.head.title("Motor Unit Eiditing Window")
    #     self.head.grab_set()

    #     # Select Motor Unit
    #     ttk.Label(self.head, text="Select MU:").grid(column=0, row=0, sticky=W, padx=5, pady=5)

    #     self.mu_to_edit = StringVar()
    #     edit_mu_value = [*range(0, self.resdict["NUMBER_OF_MUS"])]
    #     edit_mu = ttk.Combobox(self.head, width=10, textvariable=self.mu_to_edit)
    #     edit_mu["values"] = edit_mu_value
    #     edit_mu["state"] = "readonly"
    #     edit_mu.grid(column=1, row=0, sticky=(W,E), padx=5, pady=5)

    #     # Button to plot MU
    #     single_mu = ttk.Button(self.head,
    #                           text="View single MU",
    #                           command=self.view_single_mu)
    #     single_mu.grid(column=1, row=1, sticky=(W,E), padx=5, pady=5)

    # def view_single_mu(self):
    #     """
    #     Instance method that plots single selected MU.

    #     THIS PART IS NOT YET INTEGRATED IN THE GUI.
    #     """
    #     # Make figure
    #     fig = openhdemg.plot_idr(emgfile=self.resdict,
    #                              munumber=int(self.mu_to_edit.get()),
    #                              showimmediately=False)
    #     # Create canvas and plot
    #     canvas = FigureCanvasTkAgg(fig, master=self.head)
    #     canvas_plot = canvas.get_tk_widget()
    #     canvas_plot.grid(column=1, row=2, sticky=(W,E))
    #     # Place matplotlib toolbar
    #     toolbar = NavigationToolbar2Tk(canvas, self.head, pack_toolbar=False)
    #     toolbar.grid(row=3, column=1)
    #     # terminate matplotlib to ensure GUI shutdown when closed
    #     plt.close()

    # -----------------------------------------------------------------------------------------------
    # Editing of Reference EMG Signal

    def edit_refsig(self):
        """
        Instance method to open "Reference Signal Editing Window". Options for
        refsig filtering and offset removal are displayed.

        Executed when button "RefSig Editing" in master GUI window is pressed.
        """
        # Create new window
        self.head = tk.Toplevel(bg="LightBlue4")
        self.head.title("Reference Signal Editing Window")
        self.head.iconbitmap(
            os.path.dirname(os.path.abspath(__file__)) + "/gui_files/Icon.ico"
        )
        self.head.grab_set()

        # Filter Refsig
        # Define Labels
        ttk.Label(self.head, text="Filter Order").grid(column=1, row=0, sticky=(W, E))
        ttk.Label(self.head, text="Cutoff Freq").grid(column=2, row=0, sticky=(W, E))
        # Fiter button
        basic = ttk.Button(self.head, text="Filter Refsig", command=self.filter_refsig)
        basic.grid(column=0, row=1, sticky=W)

        self.filter_order = StringVar()
        order = ttk.Entry(self.head, width=10, textvariable=self.filter_order)
        order.grid(column=1, row=1)
        self.filter_order.set(4)

        self.cutoff_freq = StringVar()
        cutoff = ttk.Entry(self.head, width=10, textvariable=self.cutoff_freq)
        cutoff.grid(column=2, row=1)
        self.cutoff_freq.set(15)

        # Remove offset of reference signal
        separator2 = ttk.Separator(self.head, orient="horizontal")
        separator2.grid(column=0, columnspan=3, row=2, sticky=(W, E), padx=5, pady=5)

        ttk.Label(self.head, text="Offset Value").grid(column=1, row=3, sticky=(W, E))
        ttk.Label(self.head, text="Automatic Offset").grid(
            column=2, row=3, sticky=(W, E)
        )

        # Offset removal button
        basic2 = ttk.Button(self.head, text="Remove Offset", command=self.remove_offset)
        basic2.grid(column=0, row=4, sticky=W)

        self.offsetval = StringVar()
        offset = ttk.Entry(self.head, width=10, textvariable=self.offsetval)
        offset.grid(column=1, row=4)
        self.offsetval.set(4)

        self.auto_eval = StringVar()
        auto = ttk.Entry(self.head, width=10, textvariable=self.auto_eval)
        auto.grid(column=2, row=4)
        self.auto_eval.set(0)

        separator3 = ttk.Separator(self.head, orient="horizontal")
        separator3.grid(column=0, columnspan=3, row=5, sticky=(W, E), padx=5, pady=5)

        # Convert Reference signal
        ttk.Label(self.head, text="Operator").grid(column=1, row=6, sticky=(W, E))
        ttk.Label(self.head, text="Factor").grid(
            column=2, row=6, sticky=(W, E)
        )

        self.convert = StringVar()
        convert = ttk.Combobox(self.head, width=10, textvariable=self.convert)
        convert["values"] = ("Multiply", "Divide")
        convert["state"] = "readonly"
        convert.grid(column=1, row=7)
        self.convert.set("Multiply")

        self.convert_factor = DoubleVar()
        factor = ttk.Entry(self.head, width=10, textvariable=self.convert_factor)
        factor.grid(column=2, row=7)
        self.convert_factor.set(2.5)
        
        convert_button = ttk.Button(self.head, text="Convert", command=self.convert_refsig)
        convert_button.grid(column=0, row=7, sticky=W)

        separator3 = ttk.Separator(self.head, orient="horizontal")
        separator3.grid(column=0, columnspan=3, row=8, sticky=(W, E), padx=5, pady=5)

        # Convert to percentage
        ttk.Label(self.head, text="MVC Value").grid(column=1, row=9, sticky=(W, E))
        
        percent_button = ttk.Button(self.head, text="To Percent*", command=self.to_percent)
        percent_button.grid(column=0, row=10, sticky=W)

        self.mvc_value = DoubleVar()
        mvc = ttk.Entry(self.head, width=10, textvariable=self.mvc_value)
        mvc.grid(column=1, row=10)


        ttk.Label(self.head,
                  text= "*Use this button \nonly if your Refsig \nis in absolute values!",
                  font=("Arial", 8)).grid(
            column=2, row=9, rowspan=2
        )

        # Add padding to all children widgets of head
        for child in self.head.winfo_children():
            child.grid_configure(padx=5, pady=5)

    ### Define functions for Refsig editing

    def filter_refsig(self):
        """
        Instance method that filters the refig based on user selected specs.

        Executed when button "Filter Refsig" in Reference Signal Editing Window is pressed.
        The emgfile and the GUI plot are updated.

        Raises
        ------
        AttributeError
            When no reference signal file is available.

        See Also
        --------
        filter_refsig in library.
        """
        try:
            # Filter refsig
            self.resdict = openhdemg.filter_refsig(
                emgfile=self.resdict,
                order=int(self.filter_order.get()),
                cutoff=int(self.cutoff_freq.get()),
            )
            # Plot filtered Refsig
            self.in_gui_plotting(plot="refsig_fil")

        except AttributeError:
            tk.messagebox.showerror("Information", "Make sure a Refsig file is loaded.")

    def remove_offset(self):
        """
        Instance Method that removes user specified/selected Refsig offset.

        Executed when button "Remove offset" in Reference Signal Editing Window is pressed.
        The emgfile and the GUI plot are updated.

        Raises
        ------
        AttributeError
            When no reference signal file is available

        See Also
        --------
        remove_offset in library.
        """
        try:
            # Remove offset
            self.resdict = openhdemg.remove_offset(
                emgfile=self.resdict,
                offsetval=int(self.offsetval.get()),
                auto=int(self.auto_eval.get()),
            )
            # Update Plot
            self.in_gui_plotting(plot="refsig_off")

        except AttributeError:
            tk.messagebox.showerror("Information", "Make sure a Refsig file is loaded.")

        except ValueError:
            tk.messagebox.showerror("Information", "Make sure to specify valid filtering or offset values.")

    def convert_refsig(self):
        """
        Instance Method that converts Refsig by multiplication or division.

        Executed when button "Convert" in Reference Signal Editing Window is pressed.
        The emgfile and the GUI plot are updated.

        Raises
        ------
        AttributeError
            When no reference signal file is available
        ValueError
            When invalid conversion factor is specified
        
        """
        try:
            if self.convert.get() == "Multiply":
                self.resdict["REF_SIGNAL"] = self.resdict["REF_SIGNAL"] * self.convert_factor.get()
            elif self.convert.get() == "Divide":
                self.resdict["REF_SIGNAL"] = self.resdict["REF_SIGNAL"] / self.convert_factor.get()
        
            # Update Plot
            self.in_gui_plotting(plot="refsig_off")

        except AttributeError:
            tk.messagebox.showerror("Information", "Make sure a Refsig file is loaded.")

        except ValueError:
            tk.messagebox.showerror("Information", "Make sure to specify a valid conversion factor.")

    def to_percent(self):
        """
        Instance Method that converts Refsig to a percentag value. Should only be used when the Refsig is in absolute values.

        Executed when button "To Percen" in Reference Signal Editing Window is pressed.
        The emgfile and the GUI plot are updated.

        Raises
        ------
        AttributeError
            When no reference signal file is available
        ValueError
            When invalid conversion factor is specified
        """
        try:
            self.resdict["REF_SIGNAL"] = (self.resdict["REF_SIGNAL"] * 100) / self.mvc_value.get()
        
            # Update Plot
            self.in_gui_plotting()

        except AttributeError:
            tk.messagebox.showerror("Information", "Make sure a Refsig file is loaded.")

        except ValueError:
            tk.messagebox.showerror("Information", "Make sure to specify a valid conversion factor.")
    # -----------------------------------------------------------------------------------------------
    # Resize EMG File

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
                emgfile=self.resdict,
                title="Select the start/end area to resize by hovering the mouse\nand pressing the 'a'-key. Wrong points can be removed with right click.\nWhen ready, press enter.",
                titlesize=10,
            )
            start, end = points[0], points[1]
            self.resdict, _, _ = openhdemg.resize_emgfile(
                emgfile=self.resdict, area=[start, end]
            )
            # Update Plot
            self.in_gui_plotting()

        except AttributeError:
            tk.messagebox.showerror("Information", "Make sure a file is loaded.")

    # -----------------------------------------------------------------------------------------------
    # Analysis of Force

    def analyze_force(self):
        """
        Instance method to open "Force analysis Window".
        Options to analyse force singal are displayed.

        Executed when "Analyse Force" button in master GUI window is pressed.
        """
        # Create new window
        self.head = tk.Toplevel(bg="LightBlue4")
        self.head.title("Force Analysis Window")
        self.head.iconbitmap(
            os.path.dirname(os.path.abspath(__file__)) + "/gui_files/Icon.ico"
        )
        self.head.grab_set()

        # Get MVC
        get_mvf = ttk.Button(self.head, text="Get MVC", command=self.get_mvc)
        get_mvf.grid(column=0, row=1, sticky=(W, E), padx=5, pady=5)

        # Get RFD
        separator1 = ttk.Separator(self.head, orient="horizontal")
        separator1.grid(column=0, columnspan=3, row=2, sticky=(W, E), padx=5, pady=5)

        ttk.Label(self.head, text="RFD miliseconds").grid(
            column=1, row=3, sticky=(W, E), padx=5, pady=5
        )

        get_rfd = ttk.Button(self.head, text="Get RFD", command=self.get_rfd)
        get_rfd.grid(column=0, row=4, sticky=(W, E), padx=5, pady=5)

        self.rfdms = StringVar()
        milisecond = ttk.Entry(self.head, width=10, textvariable=self.rfdms)
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
            self.mvc = openhdemg.get_mvc(emgfile=self.resdict)
            # Define dictionary for pandas
            mvc_dic = {"MVC": [self.mvc]}
            self.mvc_df = pd.DataFrame(data=mvc_dic)
            # Display results
            self.display_results(self.mvc_df)

        except AttributeError:
            tk.messagebox.showerror("Information", "Make sure a file is loaded.")

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
            self.rfd = openhdemg.compute_rfd(emgfile=self.resdict, ms=ms_list)
            # Display results
            self.display_results(self.rfd)

        except AttributeError:
            tk.messagebox.showerror("Information", "Make sure a file is loaded.")

    # -----------------------------------------------------------------------------------------------
    # Analysis of motor unit properties

    def mu_analysis(self):
        """
        Instance method to open "Motor Unit Properties Window". Options to analyse motor
        unit properties such as recruitement threshold, discharge rate or
        basic properties computing are displayed.

        Executed when button "MU Properties" button in master GUI window is pressed.
        """
        # Create new window
        self.head = tk.Toplevel(bg="LightBlue4")
        self.head.title("Motor Unit Properties Window")
        self.head.iconbitmap(
            os.path.dirname(os.path.abspath(__file__)) + "/gui_files/Icon.ico"
        )
        self.head.grab_set()

        # MVC Entry
        ttk.Label(self.head, text="Enter MVC[n]:").grid(column=0, row=0, sticky=(W))
        self.mvc_value = StringVar()
        enter_mvc = ttk.Entry(self.head, width=20, textvariable=self.mvc_value)
        enter_mvc.grid(column=1, row=0, sticky=(W, E))

        # Compute MU re-/derecruitement threshold
        separator = ttk.Separator(self.head, orient="horizontal")
        separator.grid(column=0, columnspan=4, row=2, sticky=(W, E), padx=5, pady=5)

        thresh = ttk.Button(
            self.head, text="Compute threshold", command=self.compute_mu_threshold
        )
        thresh.grid(column=0, row=3, sticky=W)

        self.ct_event = StringVar()
        ct_events_entry = ttk.Combobox(self.head, width=10, textvariable=self.ct_event)
        ct_events_entry["values"] = ("rt", "dert", "rt_dert")
        ct_events_entry["state"] = "readonly"
        ct_events_entry.grid(column=1, row=3, sticky=(W, E))
        self.ct_event.set("Event")

        self.ct_type = StringVar()
        ct_types_entry = ttk.Combobox(self.head, width=10, textvariable=self.ct_type)
        ct_types_entry["values"] = ("abs", "rel", "abs_rel")
        ct_types_entry["state"] = "readonly"
        ct_types_entry.grid(column=2, row=3, sticky=(W, E))
        self.ct_type.set("Type")

        # Compute motor unit discharge rate
        separator1 = ttk.Separator(self.head, orient="horizontal")
        separator1.grid(column=0, columnspan=4, row=4, sticky=(W, E), padx=5, pady=5)

        ttk.Label(self.head, text="Firings at Rec").grid(column=1, row=5, sticky=(W, E))
        ttk.Label(self.head, text="Firings Start/End Steady").grid(
            column=2, row=5, sticky=(W, E)
        )

        dr_rate = ttk.Button(
            self.head, text="Compute discharge rate", command=self.compute_mu_dr
        )
        dr_rate.grid(column=0, row=6, sticky=W)

        self.firings_rec = StringVar()
        firings_1 = ttk.Entry(self.head, width=20, textvariable=self.firings_rec)
        firings_1.grid(column=1, row=6)
        self.firings_rec.set(4)

        self.firings_ste = StringVar()
        firings_2 = ttk.Entry(self.head, width=20, textvariable=self.firings_ste)
        firings_2.grid(column=2, row=6)
        self.firings_ste.set(10)

        self.dr_event = StringVar()
        dr_events_entry = ttk.Combobox(self.head, width=10, textvariable=self.dr_event)
        dr_events_entry["values"] = (
            "rec",
            "derec",
            "rec_derec",
            "steady",
            "rec_derec_steady",
        )
        dr_events_entry["state"] = "readonly"
        dr_events_entry.grid(column=3, row=6, sticky=E)
        self.dr_event.set("Event")

        # Compute basic motor unit properties
        separator2 = ttk.Separator(self.head, orient="horizontal")
        separator2.grid(column=0, columnspan=4, row=7, sticky=(W, E), padx=5, pady=5)

        ttk.Label(self.head, text="Firings at Rec").grid(column=1, row=8, sticky=(W, E))
        ttk.Label(self.head, text="Firings Start/End Steady").grid(
            column=2, row=8, sticky=(W, E)
        )

        basic = ttk.Button(
            self.head, text="Basic MU properties", command=self.basic_mus_properties
        )
        basic.grid(column=0, row=9, sticky=W)

        self.b_firings_rec = StringVar()
        b_firings_1 = ttk.Entry(self.head, width=20, textvariable=self.b_firings_rec)
        b_firings_1.grid(column=1, row=9)
        self.b_firings_rec.set(4)

        self.b_firings_ste = StringVar()
        b_firings_2 = ttk.Entry(self.head, width=20, textvariable=self.b_firings_ste)
        b_firings_2.grid(column=2, row=9)
        self.b_firings_ste.set(10)

        for child in self.head.winfo_children():
            child.grid_configure(padx=5, pady=5)

    ### Define functions for motor unit property calculation

    def compute_mu_threshold(self):
        """
        Instance method to compute the motor unit recruitement thresholds
        based on user selection of events and types.

        Executed when button "Compute threshold" in Motor Unit Properties Window
        is pressed. The analysis results are displayed in the result terminal.

        Raises
        ------
        AttributeError
            When no file is loaded prior to calculation.
        ValueError
            When entered MVC is not valid (inexistent).
        AssertionError
            When types/events are not specified.

        See Also
        --------
        compute_thresholds in library.
        """
        try:
            # Compute thresholds
            self.mu_thresholds = openhdemg.compute_thresholds(
                emgfile=self.resdict,
                event_=self.ct_event.get(),
                type_=self.ct_type.get(),
                mvc=float(self.mvc_value.get()),
            )
            # Display results
            self.display_results(self.mu_thresholds)

        except AttributeError:
            tk.messagebox.showerror("Information", "Load file prior to computation.")

        except ValueError:
            tk.messagebox.showerror("Information", "Enter valid MVC.")

        except AssertionError:
            tk.messagebox.showerror("Information", "Specify Event and/or Type.")

    def compute_mu_dr(self):
        """
        Instance method to compute the motor unit discharge rate
        based on user selection of Firings and Events.

        Executed when button "Compute discharge rate" in Motor Unit Properties Window
        is pressed. The analysis results are displayed in the result terminal.

        Raises
        ------
        AttributeError
            When no file is loaded prior to calculation.
        ValueError
            When entered Firings values are not valid (inexistent).
        AssertionError
            When types/events are not specified.

        See Also
        --------
        compute_dr in library.
        """
        try:
            # Compute discharge rates
            self.mus_dr = openhdemg.compute_dr(
                emgfile=self.resdict,
                n_firings_RecDerec=int(self.firings_rec.get()),
                n_firings_steady=int(self.firings_ste.get()),
                event_=self.dr_event.get(),
            )
            # Display results
            self.display_results(self.mus_dr)

        except AttributeError:
            tk.messagebox.showerror("Information", "Load file prior to computation.")

        except ValueError:
            tk.messagebox.showerror(
                "Information",
                "Enter valid Firings value or select a correct number of points."
            )

        except AssertionError:
            tk.messagebox.showerror("Information", "Specify Event and/or Type.")

    def basic_mus_properties(self):
        """
        Instance method to compute basic motor unit properties based in user
        selection in plot.

        Executed when button "Basic MU properties" in Motor Unit Properties Window
        is pressed. The analysis results are displayed in the result terminal.

        Raises
        ------
        AttributeError
            When no file is loaded prior to calculation.
        ValueError
            When entered Firings values are not valid (inexistent).
        AssertionError
            When types/events are not specified.
        UnboundLocalError
            When start/end area for calculations are specified wrongly.

        See Also
        --------
        basic_mus_properties in library.
        """
        try:
            # Calculate properties
            self.exportable_df = openhdemg.basic_mus_properties(
                emgfile=self.resdict,
                n_firings_RecDerec=int(self.b_firings_rec.get()),
                n_firings_steady=int(self.b_firings_ste.get()),
                mvc=float(self.mvc_value.get()),
            )
            # Display results
            self.display_results(self.exportable_df)

        except AttributeError:
            tk.messagebox.showerror("Information", "Load file prior to computation.")

        except ValueError:
            tk.messagebox.showerror(
                "Information",
                "Enter valid MVC or select a correct number of points."
            )

        except AssertionError:
            tk.messagebox.showerror("Information", "Specify Event and/or Type.")

        except UnboundLocalError:
            tk.messagebox.showerror("Information", "Select start/end area again.")

    # -----------------------------------------------------------------------------------------------
    # Plot EMG

    def plot_emg(self):
        """
        Instance method to open "Plot Window". Options to create
        several plots from the emgfile are displayed.

        Executed when button "Plot EMG" in master GUI window is pressed.
        The plots are displayed in seperate windows.
        """
        try:
    
            # Create new window
            self.head = tk.Toplevel(bg="LightBlue4")
            self.head.title("Plot Window")
            self.head.iconbitmap(
                os.path.dirname(os.path.abspath(__file__)) + "/gui_files/Icon.ico"
            )
            self.head.grab_set()

            # Reference signal
            ttk.Label(self.head, text="Reference signal").grid(
                column=0, row=0, sticky=W
            )
            self.ref_but = StringVar()
            ref_button = tk.Checkbutton(
                self.head,
                variable=self.ref_but,
                bg="LightBlue4",
                onvalue="True",
                offvalue="False",
            )
            ref_button.grid(column=1, row=0, sticky=(W))
            self.ref_but.set(False)

            # Time
            ttk.Label(self.head, text="Time in seconds").grid(column=0, row=1, sticky=W)
            self.time_sec = StringVar()
            time_button = tk.Checkbutton(
                self.head,
                variable=self.time_sec,
                bg="LightBlue4",
                onvalue="True",
                offvalue="False",
            )
            time_button.grid(column=1, row=1, sticky=W)
            self.time_sec.set(False)

            # Figure Size
            ttk.Label(self.head, text="Figure size in cm (h,w)").grid(column=0, row=2)
            self.size_fig = StringVar()
            fig_entry = ttk.Entry(self.head, width=7, textvariable=self.size_fig)
            self.size_fig.set("20,15")
            fig_entry.grid(column=1, row=2, sticky=W)

            # Plot emgsig
            plt_emgsig = ttk.Button(
                self.head, text="Plot EMGsig", command=self.plt_emgsignal
            )
            plt_emgsig.grid(column=0, row=3, sticky=W)

            self.channels = StringVar()
            channel_entry = ttk.Combobox(
                self.head, width=15, textvariable=self.channels
            )
            channel_entry["values"] = ("0", "0,1,2", "0,1,2,3")
            channel_entry.grid(column=1, row=3, sticky=(W, E))
            self.channels.set("Channel Numbers")

            # Plot refsig
            plt_refsig = ttk.Button(
                self.head, text="Plot RefSig", command=self.plt_refsignal
            )
            plt_refsig.grid(column=0, row=4, sticky=W)

            # Plot motor unit pulses
            plt_pulses = ttk.Button(
                self.head, text="Plot MUpulses", command=self.plt_mupulses
            )
            plt_pulses.grid(column=0, row=5, sticky=W)

            self.linewidth = StringVar()
            linewidth_entry = ttk.Combobox(
                self.head, width=15, textvariable=self.linewidth
            )
            linewidth_entry["values"] = ("0.25", "0.5", "0.75", "1")
            linewidth_entry.grid(column=1, row=5, sticky=(W, E))
            self.linewidth.set("Linewidth")

            # Plot impulse train
            plt_ipts = ttk.Button(self.head, text="Plot Source", command=self.plt_ipts)
            plt_ipts.grid(column=0, row=6, sticky=W)

            self.mu_numb = StringVar()
            munumb_entry = ttk.Combobox(self.head, width=15, textvariable=self.mu_numb)
            munumb_entry["values"] = ("0", "0,1,2", "0,1,2,3", "all")
            munumb_entry.grid(column=1, row=6, sticky=(W, E))
            self.mu_numb.set("MU Number")

            # Plot instantaneous discharge rate
            plt_idr = ttk.Button(self.head, text="Plot IDR", command=self.plt_idr)
            plt_idr.grid(column=0, row=7, sticky=W)

            self.mu_numb_idr = StringVar()
            munumb_entry_idr = ttk.Combobox(
                self.head, width=15, textvariable=self.mu_numb_idr
            )
            munumb_entry_idr["values"] = ("0", "0,1,2", "0,1,2,3", "all")
            munumb_entry_idr.grid(column=1, row=7, sticky=(W, E))
            self.mu_numb_idr.set("MU Number")

            # This section containes the code for column 3++

            # Separator
            ttk.Separator(self.head, orient="vertical").grid(
                row=3, column=2, rowspan=6, ipady=120
            )

            # Matrix code
            ttk.Label(self.head, text="Matrix Code").grid(row=0, column=3, sticky=(W))
            self.mat_code = StringVar()
            matrix_code = ttk.Combobox(self.head, width=15, textvariable=self.mat_code)
            matrix_code["values"] = ("GR08MM1305", "GR04MM1305", "GR10MM0808", "None")
            matrix_code["state"] = "readonly"
            matrix_code.grid(row=0, column=4, sticky=(W, E))
            self.mat_code.set("GR08MM1305")

            # Trace matrix code value
            self.mat_code.trace("w", self.on_matrix_none)

            # Matrix Orientation
            ttk.Label(self.head, text="Orientation").grid(row=1, column=3, sticky=(W))
            self.mat_orientation = StringVar()
            orientation = ttk.Combobox(
                self.head, width=15, textvariable=self.mat_orientation
            )
            orientation["values"] = ("0", "180")
            orientation["state"] = "readonly"
            orientation.grid(row=1, column=4, sticky=(W, E))
            self.mat_orientation.set("180")

            # Plot derivation
            # Button
            deriv_button = ttk.Button(
                self.head, text="Plot Derivation", command=self.plot_derivation
            )
            deriv_button.grid(row=3, column=3)

            # Combobox Config
            self.deriv_config = StringVar()
            configuration = ttk.Combobox(
                self.head, width=15, textvariable=self.deriv_config
            )
            configuration["values"] = ("Single differential", "Double differential")
            configuration["state"] = "readonly"
            configuration.grid(row=3, column=4, sticky=(W, E))
            self.deriv_config.set("Configuration")

            # Combobox Matrix
            self.deriv_matrix = StringVar()
            mat_column = ttk.Combobox(
                self.head, width=15, textvariable=self.deriv_matrix
            )
            mat_column["values"] = ("col0", "col1", "col2", "col3", "col4")
            mat_column["state"] = "readonly"
            mat_column.grid(row=3, column=5, sticky=(W, E))
            self.deriv_matrix.set("Matrix column")

            # Motor unit action potential
            # Button
            muap_button = ttk.Button(
                self.head, text="Plot MUAPs", command=self.plot_muaps
            )
            muap_button.grid(row=4, column=3)

            # Combobox Config
            self.muap_config = StringVar()
            config_muap = ttk.Combobox(
                self.head, width=15, textvariable=self.muap_config
            )
            config_muap["values"] = (
                "Monopolar",
                "Single differential",
                "Double differential",
            )
            config_muap["state"] = "readonly"
            config_muap.grid(row=4, column=4, sticky=(W, E))
            self.muap_config.set("Configuration")

            # Combobox MU Number
            self.muap_munum = StringVar()
            muap_munum = ttk.Combobox(self.head, width=15, textvariable=self.muap_munum)
            mu_numbers = [*range(0, self.resdict["NUMBER_OF_MUS"])]
            muap_munum["values"] = mu_numbers
            muap_munum["state"] = "readonly"
            muap_munum.grid(row=4, column=5, sticky=(W, E))
            self.muap_munum.set("MU Number")

            # Combobox Timewindow
            self.muap_time = StringVar()
            timewindow = ttk.Combobox(self.head, width=15, textvariable=self.muap_time)
            timewindow["values"] = ("25", "50", "100", "200")
            timewindow.grid(row=4, column=6, sticky=(W, E))
            self.muap_time.set("Timewindow (ms)")

            # Matrix Illustration Graphic
            matrix_canvas = Canvas(self.head, height=150, width=600, bg="white")
            matrix_canvas.grid(row=5, column=3, rowspan=5, columnspan=5)
            self.matrix = tk.PhotoImage(
                file=os.path.dirname(os.path.abspath(__file__))
                + "/gui_files/Matrix.png"
            )
            matrix_canvas.create_image(0, 0, anchor="nw", image=self.matrix)

            # Information Button
            self.info = customtkinter.CTkImage(
                light_image=Image.open(os.path.dirname(os.path.abspath(__file__)) + "/gui_files/Info.png"),
                size = (30, 30)
            )
            info_button = customtkinter.CTkButton(
                self.head,
                image=self.info,
                text="",
                width=30,
                height=30,
                bg_color="LightBlue4",
                fg_color="LightBlue4",
                command=lambda: (
                    (
                        webbrowser.open("https://www.giacomovalli.com/openhdemg/gui_basics/#plot-motor-units")
                    ),
                ),
            )
            info_button.grid(row=0, column=6, sticky=E)

            for child in self.head.winfo_children():
                child.grid_configure(padx=5, pady=5)

        except AttributeError:
            tk.messagebox.showerror("Information", "Load file prior to computation.")
            self.head.destroy()

    ### Define functions for motor unit plotting

    def on_matrix_none(self, *args):
        """
        This function is called when the value of the mat_code variable is changed.

        When the variable is set to "None" it will create an Entrybox on the grid at column 1 and row 6,
        and when the mat_code is set to something else it will remove the entrybox from the grid.
        """
        if self.mat_code.get() == "None":
        
            self.mat_label = ttk.Label(self.head, text="Rows, Columns:")
            self.mat_label.grid(row=0, column=5, sticky=E)
            
            self.matrix_rc = StringVar()
            self.row_cols_entry = ttk.Entry(self.head, width=8, textvariable= self.matrix_rc)
            self.row_cols_entry.grid(row=0, column=6, sticky = W, padx=5)
            self.matrix_rc.set("13,5")
        
        else:
            if hasattr(self, "row_cols_entry"):
                self.row_cols_entry.grid_forget()
                self.mat_label.grid_forget()
                
        
        self.head.update_idletasks()


    def plt_emgsignal(self):
        """
        Instance method to plot the raw emg signal in an seperate plot window.
        The channels selected by the user are plotted. The plot can be saved and
        partly edited using the matplotlib options.

        Executed when button "Plot EMGsig" in Plot Window is pressed.

        Raises
        ------
        AttributeError
            When no file is loaded prior to calculation.
        ValueError
            When entered channel number is not valid (inexistent).
        KeyError
            When entered channel number is out of bounds.

        See Also
        --------
        plot_emgsignal in library.
        """
        try:
            # Create list of channels to be plotted
            channels = self.channels.get()
            # Create list of figsize
            figsize = [int(i) for i in self.size_fig.get().split(",")]

            if len(channels) > 1:
                chan_list = channels.split(",")
                chan_list = [int(i) for i in chan_list]

                # Plot raw emg signal
                openhdemg.plot_emgsig(
                    emgfile=self.resdict,
                    channels=chan_list,
                    addrefsig=eval(self.ref_but.get()),
                    timeinseconds=eval(self.time_sec.get()),
                    figsize=figsize,
                )

            else:
                # Plot raw emg signal
                openhdemg.plot_emgsig(
                    emgfile=self.resdict,
                    channels=int(channels),
                    addrefsig=eval(self.ref_but.get()),
                    timeinseconds=eval(self.time_sec.get()),
                    figsize=figsize,
                )

        except ValueError:
            tk.messagebox.showerror("Information", "Enter valid channel number.")

        except KeyError:
            tk.messagebox.showerror("Information", "Enter valid channel number.")

    def plt_refsignal(self):
        """
        Instance method to plot the reference signal in an seperate plot window.
        The plot can be saved and partly edited using the matplotlib options.

        Executed when button "Plot REFsig" in Plot Window is pressed.

        Raises
        ------
        AttributeError
            When no file is loaded prior to calculation.

        See Also
        --------
        plot_refsig in library.
        """
        # Create list of figsize
        figsize = [int(i) for i in self.size_fig.get().split(",")]

        # Plot reference signal
        openhdemg.plot_refsig(
            emgfile=self.resdict, timeinseconds=self.time_sec.get(), figsize=figsize
        )

    def plt_mupulses(self):
        """
        Instance method to plot the mu pulses in an seperate plot window.
        The linewidth selected by the user is used. The plot can be saved and
        partly edited using the matplotlib options.

        Executed when button "Plot MUpulses" in Plot Window is pressed.

        Raises
        ------
        AttributeError
            When no file is loaded prior to calculation.
        ValueError
            When entered channel number is not valid (inexistent).

        See Also
        --------
        plot_mupulses in library.
        """
        try:
            # Create list of figsize
            figsize = [int(i) for i in self.size_fig.get().split(",")]

            # Plot motor unig pulses
            openhdemg.plot_mupulses(
                emgfile=self.resdict,
                linewidths=float(self.linewidth.get()),
                addrefsig=eval(self.ref_but.get()),
                timeinseconds=eval(self.time_sec.get()),
                figsize=figsize,
            )

        except ValueError:
            tk.messagebox.showerror("Information", "Enter valid linewidth number.")

    def plt_ipts(self):
        """
        Instance method to plot the motor unit pulse train in an seperate plot window.
        The motor units selected by the user are plotted. The plot can be saved and
        partly edited using the matplotlib options.

        Executed when button "Plot Source" in Plot Window is pressed.

        Raises
        ------
        AttributeError
            When no file is loaded prior to calculation.
        ValueError
            When entered motor unit number is not valid (inexistent).
        KeyError
            When entered motor number is out of bounds.

        See Also
        --------
        plot_ipts in library.
        """
        try:
            # Create list contaning motor units to be plotted
            mu_numb = self.mu_numb.get()
            # Create list of figsize
            figsize = [int(i) for i in self.size_fig.get().split(",")]

            if mu_numb == "all":
                # Plot motor unit puls train in default
                openhdemg.plot_ipts(
                    emgfile=self.resdict,
                    addrefsig=eval(self.ref_but.get()),
                    timeinseconds=eval(self.time_sec.get()),
                    figsize=figsize,
                )

            elif len(mu_numb) > 2:
                # Split at ,
                mu_list = mu_numb.split(",")
                # Use comprehension to loop troug mu_list
                mu_list = [int(i) for i in mu_list]
                # Plot motor unit puls train in default
                openhdemg.plot_ipts(
                    emgfile=self.resdict,
                    munumber=mu_list,
                    addrefsig=eval(self.ref_but.get()),
                    timeinseconds=eval(self.time_sec.get()),
                    figsize=figsize,
                )

            else:
                # Plot motor unit puls train in default
                openhdemg.plot_ipts(
                    emgfile=self.resdict,
                    munumber=int(mu_numb),
                    addrefsig=eval(self.ref_but.get()),
                    timeinseconds=eval(self.time_sec.get()),
                    figsize=figsize,
                )

        except ValueError:
            tk.messagebox.showerror("Information", "Enter valid motor unit number.")

        except KeyError:
            tk.messagebox.showerror("Information", "Enter valid motor unit number.")

    def plt_idr(self):
        """
        Instance method to plot the instanteous discharge rate in an seperate plot window.
        The motor units selected by the user are plotted. The plot can be saved and
        partly edited using the matplotlib options.

        Executed when button "Plot IDR" in Plot Window is pressed.

        Raises
        ------
        AttributeError
            When no file is loaded prior to calculation.
        ValueError
            When entered channel number is not valid (inexistent).
        KeyError
            When entered channel number is out of bounds.

        See Also
        --------
        plot_idr in library.
        """
        try:
            mu_idr = self.mu_numb_idr.get()
            # Create list of figsize
            figsize = [int(i) for i in self.size_fig.get().split(",")]

            if mu_idr == "all":
                # Plot instanteous discharge rate
                openhdemg.plot_idr(
                    emgfile=self.resdict,
                    addrefsig=eval(self.ref_but.get()),
                    timeinseconds=eval(self.time_sec.get()),
                    figsize=figsize,
                )

            elif len(mu_idr) > 2:
                mu_list_idr = mu_idr.split(",")
                mu_list_idr = [int(mu) for mu in mu_list_idr]
                # Plot instanteous discharge rate
                openhdemg.plot_idr(
                    emgfile=self.resdict,
                    munumber=mu_list_idr,
                    addrefsig=eval(self.ref_but.get()),
                    timeinseconds=eval(self.time_sec.get()),
                    figsize=figsize,
                )

            else:
                # Plot instanteous discharge rate
                openhdemg.plot_idr(
                    emgfile=self.resdict,
                    munumber=int(mu_idr),
                    addrefsig=eval(self.ref_but.get()),
                    timeinseconds=eval(self.time_sec.get()),
                    figsize=figsize,
                )

        except ValueError:
            tk.messagebox.showerror("Information", "Enter valid motor unit number.")

        except KeyError:
            tk.messagebox.showerror("Information", "Enter valid motor unit number.")

    def plot_derivation(self):
        """
        Instance method to plot the differential derivation of the RAW_SIGNAL by matrix column.

        Both the single and the double differencials can be plotted.
        This function is used to plot also the sorted RAW_SIGNAL.
        """
        try:
            if self.mat_code.get() == "None":
                # Get rows and columns and turn into list
                list_rcs = [int(i) for i in self.matrix_rc.get().split(",")]

                try:
                    # Sort emg file
                    sorted_file = openhdemg.sort_rawemg(
                        emgfile=self.resdict,
                        code=self.mat_code.get(),
                        orientation=int(self.mat_orientation.get()),
                        n_rows=list_rcs[0],
                        n_cols=list_rcs[1]
                    )

                except ValueError:
                    tk.messagebox.showerror(
                        "Information",
                        "Number of specified rows and columns must match" +
                        "\nnumber of channels."
                    )
                    return

            else:
                # Sort emg file
                sorted_file = openhdemg.sort_rawemg(
                    emgfile=self.resdict,
                    code=self.mat_code.get(),
                    orientation=int(self.mat_orientation.get()),
                )

            # calcualte derivation
            if self.deriv_config.get() == "Single differential":
                diff_file = openhdemg.diff(sorted_rawemg=sorted_file)

            elif self.deriv_config.get() == "Double differential":
                diff_file = openhdemg.double_diff(sorted_rawemg=sorted_file)

            # Create list of figsize
            figsize = [int(i) for i in self.size_fig.get().split(",")]

            # Plot derivation
            openhdemg.plot_differentials(
                emgfile=self.resdict,
                differential=diff_file,
                column=self.deriv_matrix.get(),
                addrefsig=eval(self.ref_but.get()),
                timeinseconds=eval(self.time_sec.get()),
                figsize=figsize,
            )
        except ValueError:
            tk.messagebox.showerror(
                "Information",
                "Enter valid input parameters."
                + "\nPotenital error sources:"
                + "\n - Matrix Code"
                + "\n - Matrix Orientation"
                + "\n - Figure size arguments"
                + "\n - Rows, Columns arguments",
            )
        except UnboundLocalError:
            tk.messagebox.showerror(
                "Information", "Enter valid Configuration and Matrx Column."
            )

        except KeyError:
            tk.messagebox.showerror("Information", "Enter valid Matrx Column.")

    def plot_muaps(self):
        """
        Instance methos to plot motor unit action potenital obtained from STA from one or
        multiple MUs.

        There is no limit to the number of MUs and STA files that can be overplotted.
        ``Remember: the different STAs should be matched`` with same number of electrode,
        processing (i.e., differential) and computed on the same timewindow.
        """
        try:
            if self.mat_code.get() == "None":
                # Get rows and columns and turn into list
                list_rcs = [int(i) for i in self.matrix_rc.get().split(",")]

                try:
                    # Sort emg file
                    sorted_file = openhdemg.sort_rawemg(
                        emgfile=self.resdict,
                        code=self.mat_code.get(),
                        orientation=int(self.mat_orientation.get()),
                        n_rows=list_rcs[0],
                        n_cols=list_rcs[1]
                    )

                except ValueError:
                    tk.messagebox.showerror(
                            "Information",
                            "Number of specified rows and columns must match"
                            + "\nnumber of channels."
                    )
                    return
                
            else:
                # Sort emg file
                sorted_file = openhdemg.sort_rawemg(
                    emgfile=self.resdict,
                    code=self.mat_code.get(),
                    orientation=int(self.mat_orientation.get()),
                )

            # calcualte derivation
            if self.muap_config.get() == "Single differential":
                diff_file = openhdemg.diff(sorted_rawemg=sorted_file)

            elif self.muap_config.get() == "Double differential":
                diff_file = openhdemg.double_diff(sorted_rawemg=sorted_file)

            elif self.muap_config.get() == "Monopolar":
                diff_file = sorted_file

            # Calculate STA dictionary
            # Plot deviation
            sta_dict = openhdemg.sta(
                emgfile=self.resdict,
                sorted_rawemg=diff_file,
                firings="all",
                timewindow=int(self.muap_time.get()),
            )

            # Create list of figsize
            figsize = [int(i) for i in self.size_fig.get().split(",")]

            # Plot MUAPS
            openhdemg.plot_muaps(sta_dict[int(self.muap_munum.get())], figsize=figsize)

        except ValueError:
            tk.messagebox.showerror(
                "Information",
                "Enter valid input parameters."
                + "\nPotenital error sources:"
                + "\n - Matrix Code"
                + "\n - Matrix Orientation"
                + "\n - Figure size arguments"
                + "\n - Timewindow"
                + "\n - MU Number"
                + "\n - Rows, Columns arguments",
            )

        except UnboundLocalError:
            tk.messagebox.showerror("Information", "Enter valid Configuration.")

        except KeyError:
            tk.messagebox.showerror("Information", "Enter valid Matrx Column.")

    # -----------------------------------------------------------------------------------------------
    # Advanced Analysis

    def advanced_analysis(self):
        """
        Open top-level windows based on the selected advanced method.
        """

        if self.advanced_method.get() == "Motor Unit Tracking":
            head_title = "MUs Tracking Window"
        elif self.advanced_method.get() == "Duplicate Removal":
            head_title = "Duplicate Removal Window"
        else:
            head_title = "Conduction Velocity Window"

        self.head = tk.Toplevel(bg="LightBlue4")
        self.head.title(head_title)
        self.head.iconbitmap(
            os.path.dirname(os.path.abspath(__file__)) + "/gui_files/Icon.ico"
        )
        self.head.grab_set()

        # Specify Signal
        self.filetype_adv = StringVar()
        signal_value = ("OTB", "DEMUSE", "OPENHDEMG", "CUSTOMCSV")
        signal_entry = ttk.Combobox(
            self.head, text="Signal", width=8, textvariable=self.filetype_adv
        )
        signal_entry["values"] = signal_value
        signal_entry["state"] = "readonly"
        signal_entry.grid(column=0, row=1, sticky=(W, E))
        self.filetype_adv.set("Type of file")
        self.filetype_adv.trace("w", self.on_filetype_change_adv)

        # Load file
        load1 = ttk.Button(self.head, text="Load File 1", command=self.open_emgfile1)
        load1.grid(column=0, row=2, sticky=(W, E))

        # Load file
        load2 = ttk.Button(self.head, text="Load File 2", command=self.open_emgfile2)
        load2.grid(column=0, row=3, sticky=(W, E))

        # Threshold label
        threshold_label = ttk.Label(self.head, text="Threshold:")
        threshold_label.grid(column=0, row=9)

        # Combobox for threshold
        self.threshold_adv = StringVar()
        threshold_combobox = ttk.Combobox(
            self.head,
            values=[0.6, 0.7, 0.8, 0.9],
            textvariable=self.threshold_adv,
            state="readonly",
            width=8,
        )
        threshold_combobox.grid(column=1, row=9)
        self.threshold_adv.set(0.8)

        # Time Label
        time_window_label = ttk.Label(self.head, text="Time window:")
        time_window_label.grid(column=0, row=10)

        # Time Combobox
        self.time_window = StringVar()
        time_combobox = ttk.Combobox(
            self.head,
            values=[25, 50],
            textvariable=self.time_window,
            state="readonly",
            width=8,
        )
        time_combobox.grid(column=1, row=10)
        self.time_window.set(25)

        # Exclude below threshold
        exclude_label = ttk.Label(self.head, text="Exclude below threshold")
        exclude_label.grid(column=0, row=11)

        # Add exclude checkbox
        self.exclude_thres = tk.BooleanVar()
        exclude_checkbox = tk.Checkbutton(
            self.head, variable=self.exclude_thres, bg="LightBlue4"
        )
        exclude_checkbox.grid(column=1, row=11)
        self.exclude_thres.set(True)

        # Filter
        filter_label = ttk.Label(self.head, text="Filter")
        filter_label.grid(column=0, row=12)

        # Add filter checkbox
        self.filter_adv = tk.BooleanVar()
        filter_checkbox = tk.Checkbutton(
            self.head, variable=self.filter_adv, bg="LightBlue4"
        )
        filter_checkbox.grid(column=1, row=12)
        self.filter_adv.set(True)

        # Exclude below threshold
        show_label = ttk.Label(self.head, text="Show")
        show_label.grid(column=0, row=13)

        # Add exclude checkbox
        self.show_adv = tk.BooleanVar()
        show_checkbox = tk.Checkbutton(
            self.head, variable=self.show_adv, bg="LightBlue4"
        )
        show_checkbox.grid(column=1, row=13)

        # Add button to execute MU tracking
        track_button = ttk.Button(self.head, text="Track", command=self.track_mus)
        track_button.grid(column=0, row=15, columnspan=2, sticky=(W, E))

        # Add padding
        for child in self.head.winfo_children():
            child.grid_configure(padx=5, pady=5)

        # Add Which widget and update the track button
        # to match functionalities required for duplicate removal
        if self.advanced_method.get() == "Duplicate Removal":
            
            # Update title
            
            # Add Which label
            ttk.Label(self.head, text="Which").grid(column=0, row=14)
            # Combobox for Which option
            self.which_adv = StringVar()
            which_combobox = ttk.Combobox(
                self.head,
                values=["munumber", "accuracy"],
                textvariable=self.which_adv,
                state="readonly",
                width=8,
            )
            which_combobox.grid(row=14, column=1, padx=5, pady=5)
            self.which_adv.set("munumber")

            # Add button to execute MU tracking
            track_button.config(
                text="Remove Duplicates", command=self.remove_duplicates_between
            )

        if self.advanced_method.get() == "Conduction Velocity":
            try:
                # Destroy unnecessary pop-ups
                self.head.destroy()
                self.a_window.destroy()

                if self.mat_code_adv.get() == "None":

                    # Get rows and columns and turn into list
                    list_rcs = [int(i) for i in self.matrix_rc_adv.get().split(",")]

                    try:
                        # Sort emg file
                        sorted_rawemg = openhdemg.sort_rawemg(
                            self.resdict,
                            code=self.mat_code_adv.get(),
                            orientation=int(self.mat_orientation_adv.get()),
                            n_rows=list_rcs[0],
                            n_cols=list_rcs[1]
                        )
                    except ValueError:
                        tk.messagebox.showerror(
                            "Information",
                            "Number of specified rows and columns must match"
                            + "\nnumber of channels."
                        )
                        return

                else:
                    # Sort emg file
                    sorted_rawemg = openhdemg.sort_rawemg(
                        self.resdict,
                        code=self.mat_code_adv.get(),
                        orientation=int(self.mat_orientation_adv.get()),
                    )

                openhdemg.MUcv_gui(
                    emgfile=self.resdict,
                    sorted_rawemg=sorted_rawemg,
                )

            except AttributeError:
                tk.messagebox.showerror(
                    "Information",
                    "Please make sure to load a file"
                    + "prior to Conduction velocity calculation.",
                )
                self.head.destroy()
            
            except ValueError:
                tk.messagebox.showerror(
                    "Information",
                    "Please make sure to enter valid Rows, Columns arguments."
                    + "\nArguments must be non-negative and seperated by `,`.",
                )
                self.head.destroy()


        # Destroy first window to avoid too many pop-ups
        self.a_window.destroy()

    ### Define function for advanced analysis tools
    def open_emgfile1(self):
        """
        Open EMG file based on the selected file type and extension factor.

        This function is used to open and store the first emgfile that is
        required for the MU tracking. As both files required are loaded by
        different buttons, two functions storing the two files were created.

        See Also
        --------
        open_emgfile1(), openhdemg.askopenfile()
        """
        try: 
            # Open OTB file
            if self.filetype_adv.get() == "OTB":
                self.emgfile1 = openhdemg.askopenfile(
                    filesource=self.filetype_adv.get(),
                    otb_ext_factor=int(self.extension_factor_adv.get()),
                )
            # Open all other filetypes
            else:
                self.emgfile1 = openhdemg.askopenfile(
                    filesource=self.filetype_adv.get(),
                )

            # Add filename to GUI
            ttk.Label(self.head, text="File 1 loaded").grid(column=1, row=2)

        except ValueError:
            tk.messagebox.showerror(
                "Information",
                "Make sure to specify a valid extension factor.",
            )
            
    def open_emgfile2(self):
        """
        Open EMG file based on the selected file type and extension factor.

        This function is used to open and store the first emgfile that is
        required for the MU tracking. As both files required are loaded by
        different buttons, two functions storing the two files were created.

        See Also
        --------
        open_emgfile1(), openhdemg.askopenfile()
        """
        # Open OTB file
        if self.filetype_adv.get() == "OTB":
            self.emgfile2 = openhdemg.askopenfile(
                filesource=self.filetype_adv.get(),
                otb_ext_factor=int(self.extension_factor_adv.get()),
            )
        # Open all other filetypes
        else:
            self.emgfile2 = openhdemg.askopenfile(
                filesource=self.filetype_adv.get(),
            )

        # Add filename to GUI
        ttk.Label(self.head, text="File 2 loaded").grid(column=1, row=3)

    def on_filetype_change_adv(self, *args):
        """
        This function is called when the value of the filetype variable is changed.
        When the filetype is set to "OTB" it will create a second combobox on the grid at column 0 and row 2,
        and when the filetype is set to something else it will remove the second combobox from the grid.
        """
        # Add a combobox containing the OTB extension factors
        # in case an OTB file is loaded
        if self.filetype_adv.get() == "OTB":
            self.extension_factor_adv = StringVar()
            self.otb_combobox = ttk.Combobox(
                self.head,
                values=["8", "9", "10", "11", "12", "13", "14", "15", "16"],
                width=8,
                textvariable=self.extension_factor_adv,
                state="readonly",
            )
            self.otb_combobox.grid(column=1, row=1, sticky=(W, E), padx=5)
            self.otb_combobox.set("Extension Factor")

        # Forget the widget in case the filetype is changed
        else:
            if hasattr(self, "otb_combobox"):
                self.otb_combobox.grid_forget()

    def track_mus(self):
        """
        Perform MUs tracking on the loaded EMG files.

        Notes
        -----
        The function uses the openhdemg.tracking
        function to perform the tracking of MUs.

        Raises
        ------
        AttributeError
            If the required EMG files have not been loaded.
        ValueError
            If the input parameters are not valid.

        See Also
        --------
        openhdemg.tracking()
        """
        try:
            if self.mat_code_adv.get() == "None":
                # Get rows and columns and turn into list
                list_rcs = [int(i) for i in self.matrix_rc_adv.get().split(",")]
                n_rows = list_rcs[0]
                n_cols = list_rcs[1]
            else:
                n_rows = None
                n_cols = None
        except ValueError:
            tk.messagebox.showerror(
                "Information",
                "Verify that Rows and Columns are separated by ','",
            )

        try:
            # Track motor units
            tracking_res = openhdemg.tracking(
                emgfile1=self.emgfile1,
                emgfile2=self.emgfile2,
                threshold=float(self.threshold_adv.get()),
                timewindow=int(self.time_window.get()),
                matrixcode=self.mat_code_adv.get(),
                orientation=int(self.mat_orientation_adv.get()),
                n_rows=n_rows,
                n_cols=n_cols,
                exclude_belowthreshold=self.exclude_thres.get(),
                filter=self.filter_adv.get(),
                show=self.show_adv.get(),
            )

            # Add result terminal
            track_terminal = ttk.LabelFrame(
                self.head, text="MUs Tracking Result", height=100, relief="ridge"
            )
            track_terminal.grid(
                column=2,
                row=0,
                columnspan=2,
                rowspan=12,
                pady=8,
                padx=10,
                sticky=(N, S, W, E),
            )

            # Add table containing results to the label frame
            track_table = Table(track_terminal, dataframe=tracking_res)
            track_table.show()

        except AttributeError:
            tk.messagebox.showerror(
                "Information",
                "Make sure to load all required EMG files prior to tracking.",
            )

        except ValueError:
            tk.messagebox.showerror(
                "Information",
                "Enter valid input parameters."
                + "\nPotenital error sources:"
                + "\n - Extension Factor (in case of OTB file)"
                + "\n - Matrix Code"
                + "\n - Matrix Orientation"
                + "\n - Threshold"
                + "\n - Rows, Columns",
            )

    def remove_duplicates_between(self):
        """
        Perform duplicate removal between two EMG files.

        Notes
        -----
        The function uses the openhdemg.remove_duplicates_between function to remove duplicates between two EMG files.
        If the required parameters are not provided, the function will raise an AttributeError or ValueError.

        Raises
        ------
        AttributeError
            If the required EMG files have not been loaded.
        ValueError
            If the input parameters are not valid.

        See Also
        --------
        openhdemg.remove_duplicates_between(), openhdemg.asksavefile()
        """
        try:
            if self.mat_code_adv.get() == "None":
                # Get rows and columns and turn into list
                list_rcs = [int(i) for i in self.matrix_rc_adv.get().split(",")]
                n_rows = list_rcs[0]
                n_cols = list_rcs[1]
            else:
                n_rows = None
                n_cols = None
        except ValueError:
            tk.messagebox.showerror(
                "Information",
                "Verify that Rows and Columns are separated by ','",
            )

        try:
            # Remove motor unit duplicates
            emg_file1, emg_file2, _ = openhdemg.remove_duplicates_between(
                emgfile1=self.emgfile1,
                emgfile2=self.emgfile2,
                threshold=float(self.threshold_adv.get()),
                timewindow=int(self.time_window.get()),
                matrixcode=self.mat_code_adv.get(),
                orientation=int(self.mat_orientation_adv.get()),
                n_rows=n_rows,
                n_cols=n_cols,
                filter=self.filter_adv.get(),
                show=self.show_adv.get(),
                which=self.which_adv.get(),
            )

            # Save files
            openhdemg.asksavefile(emg_file1)
            openhdemg.asksavefile(emg_file2)

        except AttributeError:
            tk.messagebox.showerror(
                "Information",
                "Make sure to load all required EMG files prior to tracking.",
            )

        except ValueError:
            tk.messagebox.showerror(
                "Information",
                "Enter valid input parameters."
                + "\nPotenital error sources:"
                + "\n - Extension Factor (in case of OTB file)"
                + "\n - Matrix Code"
                + "\n - Matrix Orientation"
                + "\n - Threshold"
                + "\n - Which"
                + "\n - Rows, Columns",
            )

    def calculate_conduct_vel(self):
        # Add result terminal
        track_terminal = ttk.LabelFrame(
            self.head, text="Conduction Velocity", height=100, relief="ridge"
        )
        track_terminal.grid(
            column=2,
            row=0,
            columnspan=2,
            rowspan=12,
            pady=8,
            padx=10,
            sticky=(N, S, W, E),
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
            root, text="Result Output", height=100, relief="ridge"
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
