"""Module containing the advanced analysis options"""

from tkinter import ttk, W, E, N, S, StringVar, BooleanVar
import customtkinter as ctk
import os
from sys import platform
from pandastable import Table
import openhdemg.library as openhdemg
from openhdemg.gui.gui_modules.error_handler import show_error_dialog


class AdvancedAnalysis:
    """
    A class to manage advanced analysis tools in an openhdemg GUI application.

    This class provides a window for conducting advanced analyses on EMG data.
    It allows users to select and utilize different analysis tools and set
    parameters for these tools. The class supports functionalities like motor
    unit tracking, duplicate removal, and conduction velocity analysis.

    Attributes
    ----------
    parent : object
        The parent widget, typically the main application window, to which this
        AdvancedAnalysis instance belongs.
    matrix_rc_adv : StringVar
        Tkinter StringVar for storing matrix rows and columns information.
    filetype_adv : StringVar
        Tkinter StringVar for storing the file type information.
    threshold_adv : StringVar
        Tkinter StringVar for storing the threshold value for analysis.
    time_window : StringVar
        Tkinter StringVar for storing the time window for analysis.
    exclude_thres : BooleanVar
        Tkinter BooleanVar to indicate if a threshold is to be excluded.
    filter_adv : BooleanVar
        Tkinter BooleanVar to indicate if filtering is applied.
    show_adv : BooleanVar
        Tkinter BooleanVar to indicate if advanced results are to be shown.
    which_adv : StringVar
        Tkinter StringVar for specifying which advanced analysis to perform.
    emgfile1 : dict
        Dictionary to store the first EMG file's data.
    emgfile2 : dict
        Dictionary to store the second EMG file's data.
    extension_factor_adv : StringVar
        Tkinter StringVar for storing the extension factor for analysis.

    Methods
    -------
    __init__(self, parent)
        Initialize a new instance of the AdvancedAnalysis class.
    advanced_analysis(self)
        Perform the selected advanced analysis based on user-defined
        parameters.
    on_matrix_none_adv(self, *args)
        Callback function for handling changes in matrix code selection.

    Examples
    --------
    >>> main_window = Tk()
    >>> advanced_analysis = AdvancedAnalysis(main_window)
    # Usage of advanced_analysis methods as required

    Notes
    -----
    The class is designed to be a part of a larger GUI application and
    interacts with EMG data and analysis tools. It depends on the state and
    data of the `parent` widget.
    """

    def __init__(self, parent):
        """
        Initialize a new instance of the AdvancedAnalysis class.

        Sets up a window with various controls for performing advanced EMG
        data analyses. The method configures and places widgets for tool
        selection, matrix orientation, matrix code, and an analysis button in
        a grid layout. It also initializes several Tkinter StringVars and
        BooleanVars for user inputs and settings.

        Parameters
        ----------
        parent : object
            The parent widget, usually the main application window, which
            provides necessary context and data for the analysis functions.

        Raises
        ------
        AttributeError
            If certain operations are attempted without a loaded file or
            necessary data.
        """

        # Define attributes for later usage not defined in init
        self.matrix_rc_adv = StringVar()
        self.filetype_adv = StringVar()
        self.threshold_adv = StringVar()
        self.time_window = StringVar()
        self.exclude_thres = BooleanVar()
        self.filter_adv = BooleanVar()
        self.show_adv = BooleanVar()
        self.which_adv = StringVar()
        self.emgfile1 = {}
        self.emgfile2 = {}
        self.extension_factor_adv = StringVar()

        # Initialize parent and load parent settings
        self.parent = parent
        self.parent.load_settings()

        # Disable config for DELSYS files
        try:
            if self.parent.resdict["SOURCE"] == "DELSYS":
                show_error_dialog(
                    parent=self,
                    error=None,
                    solution=str(
                        "Advanced Tools for Delsys are only accessible from "
                        + "the library."
                    ),
                )
                return
        except AttributeError:
            pass  # Allow to open advanced tools even if no file is loaded
        except Exception as e:
            show_error_dialog(
                parent=self, error=e,
                solution=str("An unexpected error occurred."),
            )
            return

        # Open window
        self.a_window = ctk.CTkToplevel(fg_color="LightBlue4")
        self.a_window.title("Advanced Tools Window")

        # Set window icon
        head_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        iconpath = head_path + "/gui_files/Icon_transp.ico"
        self.a_window.iconbitmap(iconpath)

        if platform.startswith("win"):
            self.a_window.after(200, lambda: self.a_window.iconbitmap(iconpath))

        self.a_window.grab_set()

        # Set resizable window
        # Configure columns with a loop
        for col in range(3):
            self.a_window.columnconfigure(col, weight=1)

        # Configure rows with a loop
        for row in range(8):
            self.a_window.rowconfigure(row, weight=1)

        # Add Label
        ctk.CTkLabel(
            self.a_window,
            text="Select tool and matrix:",
            font=("Segoe UI", 20, "underline"),
            anchor="w",
        ).grid(row=0, column=0)

        # Analysis Tool
        ctk.CTkLabel(
            self.a_window, text="Analysis Tool", font=("Segoe UI", 18, "bold")
        ).grid(row=2, column=0, sticky=(W, E))

        # Add Selection Combobox
        adv_box_values = (
            "Motor Unit Tracking",
            "Duplicate Removal",
            "Conduction Velocity",
        )
        self.advanced_method = StringVar()
        adv_box = ctk.CTkComboBox(
            self.a_window,
            width=200,
            variable=self.advanced_method,
            values=adv_box_values,
            state="readonly",
        )
        adv_box.grid(row=2, column=1, sticky=(W, E))
        self.advanced_method.set("Motor Unit Tracking")

        # Matrix Orientation
        ctk.CTkLabel(
            self.a_window, text="Matrix Orientation",
            font=("Segoe UI", 18, "bold"),
        ).grid(row=3, column=0, sticky=(W, E))
        self.mat_orientation_adv = StringVar()
        orientation = ctk.CTkComboBox(
            self.a_window,
            width=100,
            variable=self.mat_orientation_adv,
            values=("0", "180"),
            state="readonly",
        )
        orientation.grid(row=3, column=1, sticky=(W, E))
        self.mat_orientation_adv.set("180")

        # Matrix code
        ctk.CTkLabel(
            self.a_window, text="Matrix Code", font=("Segoe UI", 18, "bold")
        ).grid(row=4, column=0, sticky=(W, E))
        self.mat_code_adv = StringVar()
        matrix_code_vals = (
            "Custom order",
            "None",
            "GR08MM1305",
            "GR04MM1305",
            "GR10MM0808",
        )
        matrix_code = ctk.CTkComboBox(
            self.a_window,
            width=150,
            variable=self.mat_code_adv,
            values=matrix_code_vals,
            state="readonly",
        )
        matrix_code.grid(row=4, column=1, sticky=(W, E))
        self.mat_code_adv.set("GR08MM1305")

        # Trace variable for updating window
        self.mat_code_adv.trace_add("write", self.on_matrix_none_adv)

        # Analysis Button
        adv_button = ctk.CTkButton(
            self.a_window,
            text="Advanced Analysis",
            command=self.advanced_analysis,
            fg_color="#000000",
            text_color="white",
            border_color="white",
            border_width=1,
            hover_color="#FFBF00",
        )
        adv_button.grid(column=0, row=7)

        # Add padding to widgets
        for child in self.a_window.winfo_children():
            child.grid_configure(padx=5, pady=5)

    # -----------------------------------------------------------------------------------------------
    # Advanced Analysis functionalities

    def on_matrix_none_adv(self, *args):
        """
        Handle changes in the matrix code selection in the AdvancedAnalysis
        GUI.

        This callback function is triggered when the `mat_code_adv` variable
        changes. It dynamically updates the GUI to add or remove an entry box
        for specifying matrix rows and columns. When 'None' is selected for
        the matrix code, it creates an entry box for the user to input the
        rows and columns. Otherwise, it removes this entry box.

        Parameters
        ----------
        *args : tuple
            The arguments passed to the callback function. Not used in the
            function but required for compatibility with Tkinter's trace
            mechanism.

        Notes
        -----
        The method is part of the AdvancedAnalysis class and interacts with
        the GUI elements specific to advanced analysis options. It ensures
        that the GUI is responsive to user selections and updates the
        interface accordingly.
        """

        # Necessary to distinguish between None and other
        if self.mat_code_adv.get() == "None":

            # Set label for matrix rows and columns
            self.mat_label_adv = ctk.CTkLabel(
                self.a_window, text="Rows,Columns:",
                font=("Segoe UI", 18, "bold"),
            )
            self.mat_label_adv.grid(row=5, column=1, sticky=W)

            self.row_cols_entry_adv = ctk.CTkEntry(
                self.a_window, width=80, textvariable=self.matrix_rc_adv
            )
            self.row_cols_entry_adv.grid(
                row=6, column=1, sticky=W, padx=5, pady=2,
            )
            self.matrix_rc_adv.set("13,5")
        else:
            # Remove the elements
            if hasattr(self, "row_cols_entry_adv"):
                self.row_cols_entry_adv.grid_forget()
                self.mat_label_adv.grid_forget()

        # Update main advanced window based on selection
        self.a_window.update_idletasks()

    def advanced_analysis(self):
        """
        Open a top-level window based on the selected advanced analysis method.

        This method is responsible for generating different GUI windows
        depending on the advanced analysis option chosen by the user. It
        dynamically creates GUI elements like dropdowns, buttons, and
        checkboxes specific to the selected analysis tool, such as 'Motor Unit
        Tracking', 'Conduction Velocity', or 'Duplicate Removal'.

        Raises
        ------
        AttributeError
            If a required file is not loaded prior to performing the analysis
            or if invalid rows and columns arguments are entered for the
            'Conduction Velocity' analysis.

        Notes
        -----
        The method is part of the AdvancedAnalysis class and interacts with
        other GUI elements and functionalities of the application. It ensures
        that the GUI adapts to the user's choice of analysis, providing
        relevant options and settings for each analysis type.
        """

        # Set head window
        self.head = ctk.CTkToplevel(fg_color="LightBlue4")
        self.head.title(self.advanced_method.get())

        # Set window icon
        head_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        iconpath = head_path + "/gui_files/Icon_transp.ico"
        self.head.iconbitmap(iconpath)
        if platform.startswith("win"):
            self.head.after(200, lambda: self.head.iconbitmap(iconpath))

        self.head.grab_set()

        # Set resizable window
        # Configure columns with a loop
        for col in range(3):
            self.head.columnconfigure(col, weight=1)

        # Configure rows with a loop
        for row in range(17):
            self.head.rowconfigure(row, weight=1)

        # Specify Signal
        signal_value = ("OPENHDEMG", "DEMUSE", "OTB", "CUSTOMCSV")
        signal_entry = ctk.CTkComboBox(
            self.head,
            width=150,
            variable=self.filetype_adv,
            values=signal_value,
            state="readonly",
        )
        signal_entry.grid(column=0, row=1, sticky=(W, E))
        self.filetype_adv.set("Type of file")
        self.filetype_adv.trace_add("write", self.on_filetype_change_adv)

        # Load file
        load1 = ctk.CTkButton(
            self.head,
            text="Load File 1",
            command=self.open_emgfile1,
        )
        load1.grid(column=0, row=2, sticky=(W, E))

        # Load file
        load2 = ctk.CTkButton(
            self.head,
            text="Load File 2",
            command=self.open_emgfile2,
        )
        load2.grid(column=0, row=3, sticky=(W, E))

        # Threshold label
        threshold_label = ctk.CTkLabel(
            self.head, text="Threshold:", font=("Segoe UI", 18, "bold")
        )
        threshold_label.grid(column=0, row=9)

        # Combobox for threshold
        threshold_combobox = ctk.CTkComboBox(
            self.head,
            values=("0.6", "0.7", "0.8", "0.9"),
            variable=self.threshold_adv,
            state="readonly",
            width=100,
        )
        threshold_combobox.grid(column=1, row=9)
        self.threshold_adv.set("0.8")

        # Time Label
        time_window_label = ctk.CTkLabel(
            self.head, text="Time window (ms):", font=("Segoe UI", 18, "bold")
        )
        time_window_label.grid(column=0, row=10)

        # Time Combobox
        time_combobox = ctk.CTkComboBox(
            self.head,
            values=("25", "30", "40", "50", "75", "100"),
            variable=self.time_window,
            state="readonly",
            width=100,
        )
        time_combobox.grid(column=1, row=10)
        self.time_window.set("50")

        # Exclude below threshold
        exclude_label = ctk.CTkLabel(
            self.head, text="Exclude below threshold",
            font=("Segoe UI", 18, "bold"),
        )
        exclude_label.grid(column=0, row=11)

        # Add exclude checkbox
        exclude_checkbox = ctk.CTkCheckBox(
            self.head,
            variable=self.exclude_thres,
            bg_color="LightBlue4",
            onvalue=True,
            offvalue=False,
            text="",
        )
        exclude_checkbox.grid(column=1, row=11)
        self.exclude_thres.set(True)

        # Filter
        filter_label = ctk.CTkLabel(
            self.head, text="Filter", font=("Segoe UI", 18, "bold")
        )
        filter_label.grid(column=0, row=12)

        # Add filter checkbox
        filter_checkbox = ctk.CTkCheckBox(
            self.head,
            variable=self.filter_adv,
            bg_color="LightBlue4",
            onvalue=True,
            offvalue=False,
            text="",
        )
        filter_checkbox.grid(column=1, row=12)
        self.filter_adv.set(True)

        # Show
        show_label = ctk.CTkLabel(
            self.head, text="Show", font=("Segoe UI", 18, "bold"),
        )
        show_label.grid(column=0, row=13)

        # Add show checkbox
        show_checkbox = ctk.CTkCheckBox(
            self.head,
            variable=self.show_adv,
            bg_color="LightBlue4",
            onvalue=True,
            offvalue=False,
            text="",
        )
        show_checkbox.grid(column=1, row=13)

        # Add button to execute MU tracking
        track_button = ctk.CTkButton(
            self.head,
            text="Track",
            command=self.track_mus,
        )
        track_button.grid(column=0, row=15, columnspan=2, sticky=(W, E))

        # Add padding
        for child in self.head.winfo_children():
            child.grid_configure(padx=5, pady=5)

        # Add description for the show_checkbox for Motor Unit Tracking
        if self.advanced_method.get() == "Motor Unit Tracking":
            description_label = ctk.CTkLabel(
                self.head,
                text="Leave Show off if using \n the tracking GUI",
                font=("Segoe UI", 10.5),
            )
            description_label.grid(column=0, row=14, pady=(0, 4))

        # Add Which widget and update the track button
        # to match functionalities required for duplicate removal
        if self.advanced_method.get() == "Duplicate Removal":

            # Add Which label
            ctk.CTkLabel(
                self.head, text="Which", font=("Segoe UI", 18, "bold")
            ).grid(column=0, row=14)

            # Combobox for Which option
            which_combobox = ctk.CTkComboBox(
                self.head,
                values=["munumber", "accuracy"],
                variable=self.which_adv,
                state="readonly",
                width=150,
            )
            which_combobox.grid(row=14, column=1, padx=5, pady=5)
            self.which_adv.set("munumber")

            # Add button to execute MU tracking
            track_button.configure(
                text="Remove Duplicates",
                command=self.remove_duplicates_between,
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
                            self.parent.resdict,
                            code="None",
                            n_rows=list_rcs[0],
                            n_cols=list_rcs[1],
                        )
                    except ValueError as e:
                        show_error_dialog(
                            parent=self,
                            error=e,
                            solution=str(
                                "Number of specified rows and columns must "
                                + "match the number of channels."
                            ),
                        )
                        return

                elif self.mat_code_adv.get() == "Custom order":
                    try:
                        # Sort emg file
                        sorted_rawemg = openhdemg.sort_rawemg(
                            self.parent.resdict,
                            code="Custom order",
                            custom_sorting_order=self.parent.settings.custom_sorting_order,
                        )
                    except ValueError as e:
                        show_error_dialog(
                            parent=self,
                            error=e,
                            solution=str(
                                "Number of rows * columns must match the "
                                + "number of channels. Verify "
                                + "custom_sorting_order in settings."
                            ),
                        )
                        return

                else:
                    # Sort emg file
                    sorted_rawemg = openhdemg.sort_rawemg(
                        self.parent.resdict,
                        code=self.mat_code_adv.get(),
                        orientation=int(self.mat_orientation_adv.get()),
                    )

                openhdemg.MUcv_gui(
                    emgfile=self.parent.resdict,
                    sorted_rawemg=sorted_rawemg,
                    n_firings=self.parent.settings.MUcv_gui__n_firings,
                    muaps_timewindow=self.parent.settings.MUcv_gui__muaps_timewindow,
                    figsize=self.parent.settings.MUcv_gui__figsize,
                    csv_separator=self.parent.settings.MUcv_gui__csv_separator,
                )

            except AttributeError as e:
                show_error_dialog(
                    parent=self,
                    error=e,
                    solution=str(
                        "Please make sure to load a file  in the main window "
                        + "for Conduction velocity calculation."
                    ),
                )
                self.head.destroy()

            except ValueError as e:
                show_error_dialog(
                    parent=self,
                    error=e,
                    solution=str(
                        "Please make sure to enter valid Rows,Columns arguments."
                        + " Arguments must be non-negative and seperated by `,`."
                    ),
                )
                self.head.destroy()

        # Destroy first window to avoid too many pop-ups
        self.a_window.withdraw()  # TODO check for reference as destroy will evoke tcl error upon continuing, whereas withdraw creates issue when closing.

    ### Define function for advanced analysis tools
    def open_emgfile1(self):
        """
        Open EMG file based on the selected file type.

        This function is used to open and store the first emgfile that is
        required for the MU tracking. As both files required are loaded by
        different buttons, two functions storing the two files were created.

        See Also
        --------
        open_emgfile1(), openhdemg.askopenfile()
        """

        try:
            if self.filetype_adv.get() == "OTB":
                self.emgfile1 = openhdemg.askopenfile(
                    filesource=self.filetype_adv.get(),
                    ignore_negative_ipts=self.parent.settings.emg_from_otb__ignore_negative_ipts,
                    otb_ext_factor=self.parent.settings.emg_from_otb__ext_factor,
                    otb_refsig_type=self.parent.settings.emg_from_otb__refsig,
                    otb_extras=self.parent.settings.emg_from_otb__extras,
                )
            elif self.filetype_adv.get() == "DEMUSE":
                self.emgfile1 = openhdemg.askopenfile(
                    filesource=self.filetype_adv.get(),
                    ignore_negative_ipts=self.parent.settings.emg_from_demuse__ignore_negative_ipts,
                )
            elif self.filetype_adv.get() == "CUSTOMCSV":
                self.emgfile1 = openhdemg.askopenfile(
                    filesource=self.filetype_adv.get(),
                    custom_ref_signal=self.parent.settings.emg_from_customcsv__ref_signal,
                    custom_raw_signal=self.parent.settings.emg_from_customcsv__raw_signal,
                    custom_ipts=self.parent.settings.emg_from_customcsv__ipts,
                    custom_mupulses=self.parent.settings.emg_from_customcsv__mupulses,
                    custom_binary_mus_firing=self.parent.settings.emg_from_customcsv__binary_mus_firing,
                    custom_accuracy=self.parent.settings.emg_from_customcsv__accuracy,
                    custom_extras=self.parent.settings.emg_from_customcsv__extras,
                    custom_fsamp=self.parent.settings.emg_from_customcsv__fsamp,
                    custom_ied=self.parent.settings.emg_from_customcsv__ied,
                )
            else:  # OPENHDEMG
                self.emgfile1 = openhdemg.askopenfile(
                    filesource=self.filetype_adv.get(),
                )

            # Add filename to GUI
            ctk.CTkLabel(
                self.head, text="File 1 loaded", font=("Segoe UI", 15, "bold")
            ).grid(column=1, row=2)

        except Exception as e:
            show_error_dialog(
                parent=self,
                error=e,
                solution=str(
                    "Make sure to specify a valid filetype or correct settings"
                ),
            )

    def open_emgfile2(self):
        """
        Open EMG file based on the selected file type.

        This function is used to open and store the first emgfile that is
        required for the MU tracking. As both files required are loaded by
        different buttons, two functions storing the two files were created.

        See Also
        --------
        open_emgfile1(), openhdemg.askopenfile()
        """

        try:
            if self.filetype_adv.get() == "OTB":
                self.emgfile2 = openhdemg.askopenfile(
                    filesource=self.filetype_adv.get(),
                    ignore_negative_ipts=self.parent.settings.emg_from_otb__ignore_negative_ipts,
                    otb_ext_factor=self.parent.settings.emg_from_otb__ext_factor,
                    otb_refsig_type=self.parent.settings.emg_from_otb__refsig,
                    otb_extras=self.parent.settings.emg_from_otb__extras,
                )
            elif self.filetype_adv.get() == "DEMUSE":
                self.emgfile2 = openhdemg.askopenfile(
                    filesource=self.filetype_adv.get(),
                    ignore_negative_ipts=self.parent.settings.emg_from_demuse__ignore_negative_ipts,
                )
            elif self.filetype_adv.get() == "CUSTOMCSV":
                self.emgfile2 = openhdemg.askopenfile(
                    filesource=self.filetype_adv.get(),
                    custom_ref_signal=self.parent.settings.emg_from_customcsv__ref_signal,
                    custom_raw_signal=self.parent.settings.emg_from_customcsv__raw_signal,
                    custom_ipts=self.parent.settings.emg_from_customcsv__ipts,
                    custom_mupulses=self.parent.settings.emg_from_customcsv__mupulses,
                    custom_binary_mus_firing=self.parent.settings.emg_from_customcsv__binary_mus_firing,
                    custom_accuracy=self.parent.settings.emg_from_customcsv__accuracy,
                    custom_extras=self.parent.settings.emg_from_customcsv__extras,
                    custom_fsamp=self.parent.settings.emg_from_customcsv__fsamp,
                    custom_ied=self.parent.settings.emg_from_customcsv__ied,
                )
            else:  # OPENHDEMG
                self.emgfile2 = openhdemg.askopenfile(
                    filesource=self.filetype_adv.get(),
                )

            # Add filename to GUI
            ctk.CTkLabel(
                self.head, text="File 2 loaded", font=("Segoe UI", 15, "bold")
            ).grid(column=1, row=3)

        except Exception as e:
            show_error_dialog(
                parent=self,
                error=e,
                solution=str(
                    "Make sure to specify a valid filetype or correct settings"
                ),
            )

    def on_filetype_change_adv(self, *args):
        """
        Handle changes in the file type selection in the AdvancedAnalysis GUI.

        This callback function is triggered when the `filetype_adv` variable
        changes. If filetype is set to != "OPENHDEMG", it will create a second
        combobox on the grid at column 0 and row 2 and when the filetype is
        set to "OPENHDEMG" it will remove the second combobox from the grid.

        Parameters
        ----------
        *args : tuple
            The arguments passed to the callback function. Not used in the
            function but required for compatibility with Tkinter's trace
            mechanism.

        Notes
        -----
        The method is part of the AdvancedAnalysis class and interacts with
        the GUI elements specific to file type selection. It ensures that the
        GUI is responsive to user selections and updates the interface
        accordingly.
        """

        # Make sure to forget all the previous labels
        if hasattr(self, "adv_verify_settings_text"):
            self.adv_verify_settings_text.grid_forget()

        if self.filetype_adv.get() != "OPENHDEMG":
            # Display the text: Verify openfiles settings!
            self.adv_verify_settings_text = ctk.CTkLabel(
                self.head,
                text="Verify openfiles settings!",
                font=("Segoe UI", 12, "bold"),
                text_color="black",
            )
            self.adv_verify_settings_text.grid(
                column=1, row=1, sticky=(W, E), padx=5,
            )

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

        # Reload settings for tracking
        self.parent.load_settings()

        try:
            if self.mat_code_adv.get() == "None":
                # Get rows and columns and turn into list
                list_rcs = [int(i) for i in self.matrix_rc_adv.get().split(",")]
                n_rows = list_rcs[0]
                n_cols = list_rcs[1]
            else:
                n_rows = None
                n_cols = None
        except ValueError as e:
            show_error_dialog(
                parent=self,
                error=e,
                solution=str("Verify that Rows and Columns are separated by ','"),
            )

        try:
            # Track motor units
            tracking_res = openhdemg.tracking(
                emgfile1=self.emgfile1,
                emgfile2=self.emgfile2,
                firings=self.parent.settings.tracking__firings,
                derivation=self.parent.settings.tracking__derivation,
                threshold=float(self.threshold_adv.get()),
                timewindow=int(self.time_window.get()),
                matrixcode=self.mat_code_adv.get(),
                orientation=int(self.mat_orientation_adv.get()),
                n_rows=n_rows,
                n_cols=n_cols,
                custom_sorting_order=self.parent.settings.custom_sorting_order,
                exclude_belowthreshold=self.exclude_thres.get(),
                filter=self.filter_adv.get(),
                show=self.show_adv.get(),
                gui=self.parent.settings.tracking__gui,
                gui_addrefsig=self.parent.settings.tracking__gui_addrefsig,
                gui_csv_separator=self.parent.settings.tracking__gui_csv_separator,
            )

            # Add result terminal, only if tracking__gui=False to avoid
            # uninterrupted processes.
            if not self.parent.settings.tracking__gui:
                track_terminal = ttk.LabelFrame(
                    self.head, text="MUs Tracking Result", height=100,
                    relief="ridge",
                )
                track_terminal.grid(
                    column=2,
                    row=0,
                    columnspan=2,
                    rowspan=14,
                    pady=8,
                    padx=10,
                    sticky=(N, S, W, E),
                )

                # Add table containing results to the label frame
                track_table = Table(track_terminal, dataframe=tracking_res)
                track_table.show()

        except AttributeError as e:
            show_error_dialog(
                parent=self,
                error=e,
                solution=str(
                    "Make sure to load all required EMG files prior to tracking."
                ),
            )

        except ValueError as e:
            show_error_dialog(
                parent=self,
                error=e,
                solution=str(
                    "Enter valid input parameters."
                    + "\nPotenital error sources:"
                    + "\n - Extension Factor (in case of OTB file)"
                    + "\n - Matrix Code"
                    + "\n - Matrix Orientation"
                    + "\n - Threshold"
                    + "\n - Rows,Columns"
                    + "\n - custom_sorting_order in settings"
                ),
            )

    def remove_duplicates_between(self):
        """
        Perform duplicate removal between two EMG files.

        Notes
        -----
        The function uses the openhdemg.remove_duplicates_between function to
        remove duplicates between two EMG files. If the required parameters
        are not provided, the function will raise an AttributeError or
        ValueError.

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
        except ValueError as e:
            show_error_dialog(
                parent=self,
                error=e,
                solution=str("Verify that Rows and Columns are separated by ','"),
            )

        try:
            # Remove motor unit duplicates
            emg_file1, emg_file2, _ = openhdemg.remove_duplicates_between(
                emgfile1=self.emgfile1,
                emgfile2=self.emgfile2,
                firings=self.parent.settings.remove_duplicates_between__firings,
                derivation=self.parent.settings.remove_duplicates_between__derivation,
                timewindow=int(self.time_window.get()),
                threshold=float(self.threshold_adv.get()),
                matrixcode=self.mat_code_adv.get(),
                orientation=int(self.mat_orientation_adv.get()),
                n_rows=n_rows,
                n_cols=n_cols,
                custom_sorting_order=self.parent.settings.custom_sorting_order,
                filter=self.filter_adv.get(),
                show=self.show_adv.get(),
                which=self.which_adv.get(),
            )

            # Save files
            openhdemg.asksavefile(
                emg_file1,
                compresslevel=self.parent.settings.save_json_emgfile__compresslevel,
            )
            openhdemg.asksavefile(
                emg_file2,
                compresslevel=self.parent.settings.save_json_emgfile__compresslevel,
            )

        except AttributeError as e:
            show_error_dialog(
                parent=self,
                error=e,
                solution=str(
                    "Make sure to load all required EMG files prior to tracking."
                ),
            )

        except ValueError as e:
            show_error_dialog(
                parent=self,
                error=e,
                solution=str(
                    "Enter valid input parameters."
                    + "\nPotenital error sources:"
                    + "\n - Extension Factor (in case of OTB file)"
                    + "\n - Matrix Code"
                    + "\n - Matrix Orientation"
                    + "\n - Threshold"
                    + "\n - Which"
                    + "\n - Rows,Columns"
                    + "\n - custom_sorting_order in settings"
                ),
            )
