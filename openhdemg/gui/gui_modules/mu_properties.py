"""Module containing MU propterty analysis"""

import customtkinter as ctk
import os
from tkinter import ttk, W, E, StringVar
import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
import pandas as pd
import openhdemg.library as openhdemg


class MuAnalysis:
    """
    Instance method to open "Motor Unit Properties Window". Options to analyse motor
    unit properties such as recruitement threshold, discharge rate or
    basic properties computing are displayed.

    Executed when button "MU Properties" button in master GUI window is pressed.
    """
    def __init__(self, parent):
        # Create new window
        self.parent = parent
        self.head = ctk.CTkToplevel(fg_color="LightBlue4")
        self.head.title("Motor Unit Properties Window")
        self.head.iconbitmap(
            os.path.dirname(os.path.abspath(__file__)) + "/gui_files/Icon.ico"
        )
        self.head.grab_set()

        # MVC Entry
        ctk.CTkLabel(self.head, text="Enter MVC[n]:", font=('Segoe UI',15, 'bold')).grid(column=0, row=0, sticky=(W))
        self.mvc_value = StringVar()
        enter_mvc = ctk.CTkEntry(self.head, width=100, textvariable=self.mvc_value)
        enter_mvc.grid(column=1, row=0, sticky=(W, E))

        # Compute MU re-/derecruitement threshold
        separator = ttk.Separator(self.head, orient="horizontal")
        separator.grid(column=0, columnspan=4, row=2, padx=5, pady=5)

        thresh = ctk.CTkButton(
            self.head, text="Compute threshold", command=self.compute_mu_threshold,
            fg_color="#E5E4E2", text_color="black", border_color="black", border_width=1
        )
        thresh.grid(column=0, row=3, sticky=W)

        self.ct_event = StringVar()
        ct_event_values = ("rt", "dert", "rt_dert")
        ct_events_entry = ctk.CTkComboBox(self.head, width=100, variable=self.ct_event,
                                          values=ct_event_values, state="readonly")
        ct_events_entry.grid(column=1, row=3)
        self.ct_event.set("Event")

        self.ct_type = StringVar()
        ct_types_values = ("abs", "rel", "abs_rel")
        ct_types_entry = ctk.CTkComboBox(self.head, width=100, variable=self.ct_type,
                                         values=ct_types_values, state="readonly")
        ct_types_entry.grid(column=2, row=3)
        self.ct_type.set("Type")

        # Compute motor unit discharge rate
        separator1 = ttk.Separator(self.head, orient="horizontal")
        separator1.grid(column=0, columnspan=4, row=4, sticky=(W, E), padx=5, pady=5)

        ctk.CTkLabel(self.head, text="Firings at Rec", font=('Segoe UI',15, 'bold')).grid(column=1, row=5, sticky=(W, E))
        ctk.CTkLabel(self.head, text="Firings Start/End Steady", font=('Segoe UI',15, 'bold')).grid(
            column=2, row=5, sticky=(W, E)
        )

        dr_rate = ctk.CTkButton(
            self.head, text="Compute discharge rate", command=self.compute_mu_dr,
            fg_color="#E5E4E2", text_color="black", border_color="black", border_width=1
        )
        dr_rate.grid(column=0, row=6, sticky=W)

        self.firings_rec = StringVar()
        firings_1 = ctk.CTkEntry(self.head, width=100, textvariable=self.firings_rec)
        firings_1.grid(column=1, row=6)
        self.firings_rec.set(4)

        self.firings_ste = StringVar()
        firings_2 = ctk.CTkEntry(self.head, width=100, textvariable=self.firings_ste)
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
        dr_events_entry = ctk.CTkComboBox(self.head, width=100, variable=self.dr_event,
                                          values=dr_events_values, state="readonly")
        dr_events_entry.grid(column=3, row=6, sticky=E)
        self.dr_event.set("Event")

        # Compute basic motor unit properties
        separator2 = ttk.Separator(self.head, orient="horizontal")
        separator2.grid(column=0, columnspan=4, row=7, sticky=(W, E), padx=5, pady=5)

        ctk.CTkLabel(self.head, text="Firings at Rec", font=('Segoe UI',15, 'bold')).grid(column=1, row=8, sticky=(W, E))
        ctk.CTkLabel(self.head, text="Firings Start/End Steady", font=('Segoe UI',15, 'bold')).grid(
            column=2, row=8, sticky=(W, E)
        )

        basic = ctk.CTkButton(
            self.head, text="Basic MU properties", command=self.basic_mus_properties,
            fg_color="#E5E4E2", text_color="black", border_color="black", border_width=1
        )
        basic.grid(column=0, row=9, sticky=W)

        self.b_firings_rec = StringVar()
        b_firings_1 = ctk.CTkEntry(self.head, width=100, textvariable=self.b_firings_rec)
        b_firings_1.grid(column=1, row=9)
        self.b_firings_rec.set(4)

        self.b_firings_ste = StringVar()
        b_firings_2 = ctk.CTkEntry(self.head, width=100, textvariable=self.b_firings_ste)
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
