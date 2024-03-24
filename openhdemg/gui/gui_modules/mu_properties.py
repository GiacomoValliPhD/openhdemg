"""Module containing MU propterty analysis"""

from tkinter import ttk, W, E, StringVar
from sys import platform
import os
import customtkinter as ctk
import openhdemg.library as openhdemg
from openhdemg.gui.gui_modules.error_handler import show_error_dialog


class MuAnalysis:
    """
    A class for analyzing motor unit (MU) properties within a GUI application.

    This class creates a window for analyzing various MU properties such as
    recruitment threshold, discharge rate, and other basic properties. It is
    activated from the main GUI window and allows for input and computation of
    MU-related metrics.

    Attributes
    ----------
    parent : object
        The parent widget, typically the main application window that this
        MuAnalysis instance belongs to.
    head : CTkToplevel
        The top-level widget for the MU properties analysis window.
    mvc_value : StringVar
        Tkinter StringVar for storing the Maximum Voluntary Contraction (MVC)
        value.
    ct_event : StringVar
        Variable to store the chosen event type for computing MU thresholds.
    ct_type : StringVar
        Variable to store the type of computation (absolute, relative, or both)
        for MU thresholds.
    firings_rec : StringVar
        Variable to store the number of firings at recruitment.
    firings_ste : StringVar
        Variable to store the number of firings at the start/end of steady
        phase.
    dr_event : StringVar
        Variable to store the chosen event type for computing MU discharge
        rate.
    b_firings_rec : StringVar
        Variable to store the number of firings at recruitment for basic MU
        properties computation.
    b_firings_ste : StringVar
        Variable to store the number of firings at the start/end of steady
        phase for basic MU properties computation.

    Methods
    -------
    __init__(self, parent)
        Initialize a new instance of the MuAnalysis class.
    compute_mu_threshold(self)
        Compute the motor unit recruitment/derecruitment threshold.
    compute_mu_dr(self)
        Compute the motor unit discharge rate.
    basic_mus_properties(self)
        Compute basic motor unit properties.

    Examples
    --------
    >>> main_window = Tk()
    >>> mu_analysis = MuAnalysis(main_window)
    >>> mu_analysis.head.mainloop()

    Notes
    -----
    This class is dependent on the `ctk` and `ttk` modules from the `tkinter`
    library. Some attributes and methods are conditional based on the
    `parent`'s properties.

    """

    def __init__(self, parent):
        """
        Initialize a new instance of the MuAnalysis class.

        This method sets up the GUI components of the Motor Unit Properties
        window. It includes input fields for MVC (Maximum Voluntary
        Contraction) value, buttons and dropdown menus to compute MU
        thresholds, discharge rates, and basic MU properties. Each component is
        configured and placed in the window grid.

        Parameters
        ----------
        parent : object
            The parent widget, typically the main application window, to which
            this MuAnalysis instance belongs. The parent is used for accessing
            shared resources and data.

        Raises
        ------
        AttributeError
            If certain widgets or properties are not properly instantiated due
            to missing parent configurations or resources.

        Notes
        -----
        The creation of the GUI components involves setting up various Tkinter
        and custom widgets (like CTkLabel, CTkEntry, CTkButton, CTkComboBox).
        Each widget is configured with specific properties like size, color,
        and variable bindings and placed in a grid layout.

        """
        # Initialize parent and load parent settings
        self.parent = parent
        self.parent.load_settings()
        # Create new window
        self.head = ctk.CTkToplevel()
        self.head.title("Motor Unit Properties Window")

        # Set window icon
        head_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        iconpath = head_path + "/gui_files/Icon2.ico"
        self.head.iconbitmap(iconpath)
        if platform.startswith("win"):
            self.head.after(200, lambda: self.head.iconbitmap(iconpath))
        self.head.grab_set()

        # Set resizable window
        # Configure columns with a loop
        for col in range(3):
            self.head.columnconfigure(col, weight=1)

        # Configure rows with a loop
        for row in range(21):
            self.head.rowconfigure(row, weight=1)

        # MVC Entry
        ctk.CTkLabel(
            self.head,
            text="Enter MVC[n]:",
            font=("Segoe UI", 18, "bold"),
        ).grid(column=0, row=0, sticky=(W))
        self.mvc_value = StringVar()
        enter_mvc = ctk.CTkEntry(
            self.head,
            width=100,
            textvariable=self.mvc_value,
        )
        enter_mvc.grid(column=1, row=0, sticky=(W, E))

        # Compute MU re-/derecruitement threshold
        separator = ttk.Separator(self.head, orient="horizontal")
        separator.grid(column=0, columnspan=4, row=2, padx=5, pady=5)

        thresh = ctk.CTkButton(
            self.head,
            text="Compute threshold",
            command=self.compute_mu_threshold,
        )
        thresh.grid(column=0, row=3, sticky=W)

        self.ct_event = StringVar()
        ct_event_values = ("rt", "dert", "rt_dert")
        ct_events_entry = ctk.CTkComboBox(
            self.head,
            width=100,
            variable=self.ct_event,
            values=ct_event_values,
            state="readonly",
        )
        ct_events_entry.grid(column=1, row=3)
        self.ct_event.set("Event")

        self.ct_type = StringVar()
        ct_types_values = ("abs", "rel", "abs_rel")
        ct_types_entry = ctk.CTkComboBox(
            self.head,
            width=100,
            variable=self.ct_type,
            values=ct_types_values,
            state="readonly",
        )
        ct_types_entry.grid(column=2, row=3)
        self.ct_type.set("Type")

        # Compute motor unit discharge rate
        separator1 = ttk.Separator(self.head, orient="horizontal")
        separator1.grid(
            column=0,
            columnspan=4,
            row=4,
            sticky=(W, E),
            padx=5,
            pady=5,
        )

        ctk.CTkLabel(
            self.head,
            text="Firings at Rec",
            font=("Segoe UI", 18, "bold"),
        ).grid(column=1, row=5, sticky=(W, E))
        ctk.CTkLabel(
            self.head,
            text="Firings Start/End Steady",
            font=("Segoe UI", 18, "bold"),
        ).grid(column=2, row=5, sticky=(W, E))

        dr_rate = ctk.CTkButton(
            self.head,
            text="Compute discharge rate",
            command=self.compute_mu_dr,
        )
        dr_rate.grid(column=0, row=6, sticky=W)

        self.firings_rec = StringVar()
        firings_1 = ctk.CTkEntry(
            self.head,
            width=100,
            textvariable=self.firings_rec,
        )
        firings_1.grid(column=1, row=6)
        self.firings_rec.set(4)

        self.firings_ste = StringVar()
        firings_2 = ctk.CTkEntry(
            self.head,
            width=100,
            textvariable=self.firings_ste,
        )
        firings_2.grid(column=2, row=6)
        self.firings_ste.set(10)

        self.dr_event = StringVar()
        dr_events_values = (
            "rec",
            "derec",
            "rec_derec",
            "steady",
            "rec_derec_steady",
        )
        dr_events_entry = ctk.CTkComboBox(
            self.head,
            width=100,
            variable=self.dr_event,
            values=dr_events_values,
            state="readonly",
        )
        dr_events_entry.grid(column=3, row=6, sticky=E)
        self.dr_event.set("Event")

        # Compute basic motor unit properties
        separator2 = ttk.Separator(self.head, orient="horizontal")
        separator2.grid(
            column=0,
            columnspan=4,
            row=7,
            sticky=(W, E),
            padx=5,
            pady=5,
        )

        ctk.CTkLabel(
            self.head,
            text="Firings at Rec",
            font=("Segoe UI", 18, "bold"),
        ).grid(column=1, row=8, sticky=(W, E))
        ctk.CTkLabel(
            self.head,
            text="Firings Start/End Steady",
            font=("Segoe UI", 18, "bold"),
        ).grid(column=2, row=8, sticky=(W, E))

        basic = ctk.CTkButton(
            self.head,
            text="Basic MU properties",
            command=self.basic_mus_properties,
        )
        basic.grid(column=0, row=9, sticky=W)

        self.b_firings_rec = StringVar()
        b_firings_1 = ctk.CTkEntry(
            self.head,
            width=100,
            textvariable=self.b_firings_rec,
        )
        b_firings_1.grid(column=1, row=9)
        self.b_firings_rec.set(4)

        self.b_firings_ste = StringVar()
        b_firings_2 = ctk.CTkEntry(
            self.head,
            width=100,
            textvariable=self.b_firings_ste,
        )
        b_firings_2.grid(column=2, row=9)
        self.b_firings_ste.set(10)

        for child in self.head.winfo_children():
            child.grid_configure(padx=5, pady=5)

    ### Define functions for motor unit property calculation

    def compute_mu_threshold(self):
        """
        Instance method to compute the motor unit recruitement thresholds
        based on user selection of events and types.

        Executed when button "Compute threshold" in Motor Unit Properties
        Window is pressed. The analysis results are displayed in the result
        terminal.

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
            self.parent.mu_thresholds = openhdemg.compute_thresholds(
                emgfile=self.parent.resdict,
                event_=self.ct_event.get(),
                type_=self.ct_type.get(),
                n_firings=self.parent.settings.compute_thresholds__n_firings,
                mvc=float(self.mvc_value.get()),
            )
            # Display results
            self.parent.display_results(self.parent.mu_thresholds)

        except AttributeError as e:
            show_error_dialog(
                parent=self,
                error=e,
                solution=str("Make sure a file is loaded."),
            )

        except ValueError as e:
            show_error_dialog(
                parent=self,
                error=e,
                solution=str("Enter valid MVC, Event or Type."),
            )

        except AssertionError as e:
            show_error_dialog(
                parent=self,
                error=e,
                solution=str("Specify Event and/or Type."),
            )

    def compute_mu_dr(self):
        """
        Instance method to compute the motor unit discharge rate
        based on user selection of Firings and Events.

        Executed when button "Compute discharge rate" in Motor Unit Properties
        Window is pressed. The analysis results are displayed in the result
        terminal.

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
            self.parent.mus_dr = openhdemg.compute_dr(
                emgfile=self.parent.resdict,
                n_firings_RecDerec=int(self.firings_rec.get()),
                n_firings_steady=int(self.firings_ste.get()),
                event_=self.dr_event.get(),
            )
            # Display results
            self.parent.display_results(self.parent.mus_dr)

        except AttributeError as e:
            show_error_dialog(
                parent=self, error=e, solution=str("Make sure a file is loaded.")
            )

        except ValueError as e:
            show_error_dialog(
                parent=self,
                error=e,
                solution=str(
                    "Enter valid Firings value or select a correct number of points."
                ),
            )

        except AssertionError as e:
            show_error_dialog(
                parent=self,
                error=e,
                solution=str("Specify Event and/or Type."),
            )

    def basic_mus_properties(self):
        """
        Instance method to compute basic motor unit properties based in user
        selection in plot.

        Executed when button "Basic MU properties" in Motor Unit Properties
        Window is pressed. The analysis results are displayed in the result
        terminal.

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
            self.parent.mu_prop_df = openhdemg.basic_mus_properties(
                emgfile=self.parent.resdict,
                n_firings_rt_dert=self.parent.settings.basic_mus_properties__n_firings_rt_dert,
                n_firings_RecDerec=int(self.b_firings_rec.get()),
                n_firings_steady=int(self.b_firings_ste.get()),
                accuracy=self.parent.settings.basic_mus_properties__accuracy,
                ignore_negative_ipts=self.parent.settings.basic_mus_properties__ignore_negative_ipts,
                constrain_pulses=self.parent.settings.basic_mus_properties__constrain_pulses,
                mvc=float(self.mvc_value.get()),
            )
            # Display results
            self.parent.display_results(self.parent.mu_prop_df)

        except AttributeError as e:
            show_error_dialog(
                parent=self, error=e, solution=str("Make sure a file is loaded.")
            )

        except ValueError as e:
            show_error_dialog(
                parent=self,
                error=e,
                solution=str(
                    "Enter valid MVC value or select a correct number of points."
                ),
            )

        except AssertionError as e:
            show_error_dialog(
                parent=self, error=e, solution=str("Specify Event and/or Type.")
            )

        except UnboundLocalError as e:
            show_error_dialog(
                parent=self, error=e, solution=str("Select start/end area again.")
            )
