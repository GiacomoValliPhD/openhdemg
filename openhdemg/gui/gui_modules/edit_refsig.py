"""Module containing the Resif editing class"""

from tkinter import ttk, W, E, StringVar, DoubleVar
import customtkinter as ctk
import os
from sys import platform
import openhdemg.library as openhdemg
from openhdemg.gui.gui_modules.error_handler import show_error_dialog


class EditRefsig:
    """
    A class to manage editing of the reference signal in a GUI application.

    This class creates a window that offers various options for editing the
    reference signal. It includes functionalities for filtering the signal,
    removing offset, converting the signal, and transforming it to a
    percentage value. The class is instantiated when the "RefSig Editing"
    button in the master GUI window is pressed.

    Attributes
    ----------
    parent : object
        The parent widget, typically the main application window, to which
        this EditRefsig instance belongs.
    head : CTkToplevel
        The top-level widget for the Reference Signal Editing window.
    filter_order : StringVar
        Tkinter StringVar to store the filter order for reference signal
        filtering.
    cutoff_freq : StringVar
        Tkinter StringVar to store the cutoff frequency for reference signal
        filtering.
    offsetval : StringVar
        Tkinter StringVar to store the offset value to be removed from the
        reference signal.
    auto_eval : StringVar
        Tkinter StringVar to store the value for automatic offset evaluation.
    convert : StringVar
        Tkinter StringVar to store the operation (Multiply/Divide) for
        reference signal conversion.
    convert_factor : DoubleVar
        Tkinter DoubleVar to store the factor for reference signal conversion.
    mvc_value : DoubleVar
        Tkinter DoubleVar to store the MVC (Maximum Voluntary Contraction)
        value for percentage conversion.

    Methods
    -------
    __init__(self, parent)
        Initialize a new instance of the EditRefsig class.
    filter_refsig(self)
        Apply filtering to the reference signal based on the specified order
        and cutoff frequency.
    remove_offset(self)
        Remove or adjust the offset of the reference signal based on the
        specified value or automatic evaluation.
    convert_refsig(self)
        Convert the reference signal using the specified operation
        (Multiply/Divide) and factor.
    to_percent(self)
        Convert the reference signal to a percentage value based on the
        specified MVC value.

    Examples
    --------
    >>> main_window = Tk()
    >>> edit_refsig = EditRefsig(main_window)
    >>> edit_refsig.head.mainloop()

    Notes
    -----
    This class relies on the `ctk` and `ttk` modules from the `tkinter`
    library. The class is designed to be instantiated from within a larger GUI
    application and operates on the reference signal data that is accessible
    via the `parent` widget.
    """

    def __init__(self, parent):
        """
        Initialize a new instance of the EditRefsig class.

        This method sets up the GUI components for the Reference Signal
        Editing Window. It includes controls for filtering the reference
        signal, removing its offset, converting it, and transforming it to a
        percentage value. The method configures and places various widgets
        such as labels, entries, buttons, and combo boxes in a grid layout for
        user interaction.

        Parameters
        ----------
        parent : object
            The parent widget, typically the main application window, to which
            this EditRefsig instance belongs. The parent is used for accessing
            shared resources and data.

        Raises
        ------
        AttributeError
            If certain widgets or properties are not properly instantiated due
            to missing parent configurations or resources.
        """

        # Initialize parent and load parent settings
        self.parent = parent
        self.parent.load_settings()

        # Create new window
        self.head = ctk.CTkToplevel()
        self.head.title("Reference Signal Editing Window")

        head_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        iconpath = head_path + "/gui_files/Icon2.ico"
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

        # Filter Refsig
        # Define Labels
        ctk.CTkLabel(
            self.head, text="Filter Order", font=("Segoe UI", 18, "bold"),
        ).grid(column=1, row=0, sticky=(W, E))
        ctk.CTkLabel(
            self.head, text="Cutoff Freq", font=("Segoe UI", 18, "bold"),
        ).grid(column=2, row=0, sticky=(W, E))
        # Fiter button
        basic = ctk.CTkButton(
            self.head,
            text="Filter Refsig",
            command=self.filter_refsig,
        )
        basic.grid(column=0, row=1, sticky=W)
        self.filter_order = StringVar()
        order = ctk.CTkEntry(
            self.head, width=100, textvariable=self.filter_order,
        )
        order.grid(column=1, row=1)
        self.filter_order.set(4)

        self.cutoff_freq = StringVar()
        cutoff = ctk.CTkEntry(
            self.head, width=100, textvariable=self.cutoff_freq,
        )
        cutoff.grid(column=2, row=1)
        self.cutoff_freq.set(15)

        # Remove offset of reference signal
        separator2 = ttk.Separator(self.head, orient="horizontal")
        separator2.grid(
            column=0, columnspan=3, row=2, sticky=(W, E), padx=5, pady=5,
        )

        ctk.CTkLabel(
            self.head, text="Offset Value", font=("Segoe UI", 18, "bold")
        ).grid(column=1, row=3, sticky=(W, E))
        ctk.CTkLabel(
            self.head, text="Automatic Offset", font=("Segoe UI", 18, "bold")
        ).grid(column=2, row=3, sticky=(W, E))

        # Offset removal button
        basic2 = ctk.CTkButton(
            self.head,
            text="Remove Offset",
            command=self.remove_offset,
        )
        basic2.grid(column=0, row=4, sticky=W)

        self.offsetval = StringVar()
        offset = ctk.CTkEntry(
            self.head, width=100, textvariable=self.offsetval,
        )
        offset.grid(column=1, row=4)
        self.offsetval.set(4)

        self.auto_eval = StringVar()
        auto = ctk.CTkEntry(self.head, width=100, textvariable=self.auto_eval)
        auto.grid(column=2, row=4)
        self.auto_eval.set(0)

        separator3 = ttk.Separator(self.head, orient="horizontal")
        separator3.grid(
            column=0, columnspan=3, row=5, sticky=(W, E), padx=5, pady=5,
        )

        # Convert Reference signal
        ctk.CTkLabel(
            self.head, text="Operator", font=("Segoe UI", 18, "bold"),
        ).grid(column=1, row=6, sticky=(W, E))
        ctk.CTkLabel(
            self.head, text="Factor", font=("Segoe UI", 18, "bold"),
        ).grid(column=2, row=6, sticky=(W, E))

        self.convert = StringVar()
        convert = ctk.CTkComboBox(
            self.head, width=100, variable=self.convert,
            values=("Multiply", "Divide"),
        )
        convert.configure(state="readonly")
        convert.grid(column=1, row=7)
        self.convert.set("Multiply")

        self.convert_factor = DoubleVar()
        factor = ctk.CTkEntry(
            self.head, width=100, textvariable=self.convert_factor,
        )
        factor.grid(column=2, row=7)
        self.convert_factor.set(2.5)

        convert_button = ctk.CTkButton(
            self.head,
            text="Convert",
            command=self.convert_refsig,
        )
        convert_button.grid(column=0, row=7, sticky=W)

        separator3 = ttk.Separator(self.head, orient="horizontal")
        separator3.grid(
            column=0, columnspan=3, row=8, sticky=(W, E), padx=5, pady=5,
        )

        # Convert to percentage
        ctk.CTkLabel(
            self.head, text="MVC Value", font=("Segoe UI", 18, "bold"),
        ).grid(column=1, row=9, sticky=(W, E))

        percent_button = ctk.CTkButton(
            self.head,
            text="To Percent*",
            command=self.to_percent,
        )
        percent_button.grid(column=0, row=10, sticky=W)

        self.mvc_value = DoubleVar()
        mvc = ctk.CTkEntry(self.head, width=100, textvariable=self.mvc_value)
        mvc.grid(column=1, row=10)

        ctk.CTkLabel(
            self.head,
            text="*Use this button \nonly if your Refsig \nis in absolute values!",
            font=("Arial", 8),
        ).grid(column=2, row=9, rowspan=2)

        # Add padding to all children widgets of head
        for child in self.head.winfo_children():
            child.grid_configure(padx=5, pady=5)

    ### Define functions for Refsig editing

    def filter_refsig(self):
        """
        Instance method that filters the refig based on user selected specs.

        Executed when button "Filter Refsig" in Reference Signal Editing
        Window is pressed. The emgfile and the GUI plot are updated.

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
            self.parent.resdict = openhdemg.filter_refsig(
                emgfile=self.parent.resdict,
                order=int(self.filter_order.get()),
                cutoff=int(self.cutoff_freq.get()),
            )
            # Plot filtered Refsig
            self.parent.in_gui_plotting(
                resdict=self.parent.resdict, plot="refsig_fil",
            )

        except AttributeError as e:
            show_error_dialog(
                parent=self, error=e,
                solution=str("Make sure a Refsig file is loaded."),
            )

    def remove_offset(self):
        """
        Instance Method that removes user specified/selected Refsig offset.

        Executed when button "Remove offset" in Reference Signal Editing
        Window is pressed. The emgfile and the GUI plot are updated.

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
            self.parent.resdict = openhdemg.remove_offset(
                emgfile=self.parent.resdict,
                offsetval=int(self.offsetval.get()),
                auto=int(self.auto_eval.get()),
            )
            # Update Plot
            self.parent.in_gui_plotting(
                resdict=self.parent.resdict, plot="refsig_off",
            )

        except AttributeError as e:
            show_error_dialog(
                parent=self, error=e,
                solution=str("Make sure a Refsig file is loaded."),
            )

        except ValueError as e:
            show_error_dialog(
                parent=self,
                error=e,
                solution=str("Make sure to specify valid filtering or offset values."),
            )

    def convert_refsig(self):
        """
        Instance Method that converts Refsig by multiplication or division.

        Executed when button "Convert" in Reference Signal Editing Window is
        pressed. The emgfile and the GUI plot are updated.

        Raises
        ------
        AttributeError
            When no reference signal file is available
        ValueError
            When invalid conversion factor is specified
        """

        try:
            if self.convert.get() == "Multiply":
                self.parent.resdict["REF_SIGNAL"] = (
                    self.parent.resdict["REF_SIGNAL"] * self.convert_factor.get()
                )
            elif self.convert.get() == "Divide":
                self.parent.resdict["REF_SIGNAL"] = (
                    self.parent.resdict["REF_SIGNAL"] / self.convert_factor.get()
                )

            # Update Plot
            self.parent.in_gui_plotting(
                resdict=self.parent.resdict, plot="refsig_off",
            )

        except AttributeError as e:
            show_error_dialog(
                parent=self, error=e,
                solution=str("Make sure a Refsig file is loaded."),
            )

        except ValueError as e:
            show_error_dialog(
                parent=self,
                error=e,
                solution=str("Make sure to specify valid conversion factor."),
            )

    def to_percent(self):
        """
        Instance Method that converts Refsig to a percentag value. Should only
        be used when the Refsig is in absolute values.

        Executed when button "To Percen" in Reference Signal Editing Window is
        pressed. The emgfile and the GUI plot are updated.

        Raises
        ------
        AttributeError
            When no reference signal file is available
        ValueError
            When invalid conversion factor is specified
        """

        try:
            self.parent.resdict["REF_SIGNAL"] = (
                self.parent.resdict["REF_SIGNAL"] * 100
            ) / self.mvc_value.get()
            # Update Plot
            self.parent.in_gui_plotting(resdict=self.parent.resdict)

        except AttributeError as e:
            show_error_dialog(
                parent=self, error=e,
                solution=str("Make sure a Refsig file is loaded."),
            )

        except ValueError as e:
            show_error_dialog(
                parent=self,
                error=e,
                solution=str("Make sure to specify valid conversion factor."),
            )
