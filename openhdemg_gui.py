"""
This file contains the gui functionalities of openhdemg.
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, Canvas
from tkinter import StringVar, Tk, N, S, W, E
from pandastable import Table

import matplotlib.pyplot as plt
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import pandas as pd
matplotlib.use('TkAgg')

import openhdemg 


class GUI():
    """GUI class for the openEMG package.
       The included functions can not be used singularily.

       Attributes:
        self.left = Left frame inside of root
        self.filetype = Filetype of import EMG file
        self.right = Right frame insinde of root
        self.first_fig = Figure frame determinining size of all figures
        self.logo = Path to file containing logo of OpenHDemg
        self.logo_canvas = Canvas to display logo
        self.terminal = Terminal to display calculation results
        self.filename = Name of the file to be analysed
        self.filepath = Path to EMG file selected for analysis
        self.resdict = Dictionary derived from input EMG file for further analysis
        self.mvif_df = Dataframe containing MVIF values
        self.rfd_df = Dataframe containing RFD values
        self.exportable_df = Dataframe containing ALL basic motor unit properties
        self.mus_dr = Dataframe containing motor unit discharge rate
        self.mu_thresholds = Dataframe containing motor unit threshold values
        self.fig = Matplotlib figure to be plotted on Canvas
        self.canvas = General canvas for plotting figures
        self.head = NEW tk.toplevel instance created everytime upon opnening a new window
        self.mu_to_remove = Selected number of motor unit to be removed
        self.mu_to_edit = Selected motor unit to be visuallized and edited individually
        self.filter_order = Specified order of Butterworth low pass filter
        self.cutoff_freq = Specified cutt-off frequency used for low pass
        self.offset_val = Specified/Determined offset value for reference signal
        self.auto_eval = Variable that if > 0 leads to automatic determination of offset
        self.start_area = Startpoint fo resizing of EMG file
        self.end_area = Endpoint for resizing of EMG file
        self.rfds = Selection of timepoints to calculate rfd
        self.mvif = Determined MVIF value
        self.mvifvalue = MVIF values used for further analysis
        self.ct_event = Specified event for firing threshold calculation
        self.firings_rec = Number of firings used for discharge rate calculation
        self.firings_ste = Number of firings at start/end of steady state
        self.dr_event = Specified event for discharge rate calculation
        self.b_firings_rec = Number of firings used for discharge rate calculation
                             when assessing basic motor unit properties
        self.b_firings_ste = Number of firings at start/end of steady state
                             when assessing basic motor unit properties
        self.channels = Number of channels used for emg signal plotting
        self.linewidth = width of line used for motor unit pulse plotting
        self.mu_numb = Number of motor units used for IPTS plotting
        self.mu_numb_idr = Number of motor units used for IDR plotting
    """

    def __init__(self, root):

        # Set up GUI
        root.title("openHD-EMG")
        root.iconbitmap("logo.ico")

        # Create left side framing for functionalities
        self.left = ttk.Frame(root, padding="10 10 12 12")
        self.left.grid(column=0, row=0, sticky=(N, S, W))
        self.left.columnconfigure(0, weight=1)
        self.left.columnconfigure(1, weight=1)
        self.left.columnconfigure(2, weight=1)

        # Style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TToplevel', background = 'LightBlue4')
        style.configure('TFrame', background = 'LightBlue4')
        style.configure('TLabel', font=('Lucida Sans', 12),
                        foreground = 'black', background = 'LightBlue4')
        style.configure('TButton',
                        foreground = 'black', font = ('Lucida Sans', 11))
        style.configure('TEntry', font = ('Lucida Sans', 12), foreground = 'black')
        style.configure('TCombobox', background = 'LightBlue4', foreground = 'black')
        style.configure('TLabelFrame', foreground = 'black',
                        font = ('Lucida Sans', 16))

        # Specify Signal
        self.filetype = StringVar()
        signal_value = ("OTB", "DEMUSE", "REFSIG")
        signal_entry = ttk.Combobox(self.left,
                                    text="Signal",
                                    width=10,
                                    textvariable=self.filetype)
        signal_entry["values"] = signal_value
        signal_entry["state"] = "readonly"
        signal_entry.grid(column=0, row=1, sticky=(W,E))
        self.filetype.set("Type of file")

        # Load file
        load = ttk.Button(self.left,
                          text="Load file",
                          command=self.get_file_input)
        load.grid(column=0, row=2, sticky=W)

        # File specifications
        ttk.Label(self.left, text="Filespecs:").grid(column=1, row=1, sticky=(W,E))
        ttk.Label(self.left, text="N Channels:").grid(column=1, row=2, sticky=(W,E))
        ttk.Label(self.left, text="N° of MUs:").grid(column=1, row=3, sticky=(W,E))
        ttk.Label(self.left, text="File length:").grid(column=1, row=4, sticky=(W,E))
        separator0 = ttk.Separator(self.left, orient="horizontal")
        separator0.grid(column=0, columnspan=3, row=5, sticky=(W,E))

        # Save File
        save = ttk.Button(self.left,
                          text="Save file",
                          command=self.save_emgfile)
        save.grid(column=0, row=6, sticky=W)
        separator1 = ttk.Separator(self.left, orient="horizontal")
        separator1.grid(column=0, columnspan=3, row=7, sticky=(W,E))

        # Export to Excel
        export = ttk.Button(self.left,
                            text="Save Results", command=self.export_to_excel)
        export.grid(column=1, row=6, sticky=(W,E))

        # View Motor Unit Firings
        firings = ttk.Button(self.left,
                             text="View MUs",
                             command=self.in_gui_plotting)
        firings.grid(column=0, row=8, sticky=W)

        # Sort Motor Units
        sorting = ttk.Button(self.left,
                             text="Sort MUs",
                             command=self.sort_mus)
        sorting.grid(column=1, row=8, sticky=(W,E))
        separator2 = ttk.Separator(self.left, orient="horizontal")
        separator2.grid(column=0, columnspan=3, row=9, sticky=(W,E))

        # Remove Motor Units
        remove_mus = ttk.Button(self.left,
                              text="Remove MUs",
                              command=self.remove_mus)
        remove_mus.grid(column=0, row=10, sticky=W)

        # Edit Motor Units
        edit_mus = ttk.Button(self.left,
                              text="Edit MUs",
                              command=self.editing_mus)
        edit_mus.grid(column=1, row=10, sticky=W)
        separator3 = ttk.Separator(self.left, orient="horizontal")
        separator3.grid(column=0, columnspan=3, row=11, sticky=(W,E))

        # Filter Reference Signal
        reference = ttk.Button(self.left,
                               text="RefSig Editing",
                               command=self.edit_refsig)
        reference.grid(column=0, row=12, sticky=W)

        # Resize File
        resize = ttk.Button(self.left,
                            text="Resize File",
                            command=self.resize_file)
        resize.grid(column=1, row=12, sticky=(W,E))
        separator4 = ttk.Separator(self.left, orient="horizontal")
        separator4.grid(column=0, columnspan=3, row=13, sticky=(W,E))

        # Force Analysis
        force = ttk.Button(self.left,
                           text="Analyse force",
                           command=self.analyze_force)
        force.grid(column=0, row=14, sticky=W)
        separator5 = ttk.Separator(self.left, orient="horizontal")
        separator5.grid(column=0, columnspan=3, row=15, sticky=(W,E))

        # Motor Unit properties
        mus = ttk.Button(self.left,
                         text="MU properties",
                         command=self.mu_analysis)
        mus.grid(column=0, row=16, sticky=W)
        separator6 = ttk.Separator(self.left, orient="horizontal")
        separator6.grid(column=0, columnspan=3, row=17, sticky=(W,E))

        # Plot EMG
        plots = ttk.Button(self.left,
                           text="Plot EMG",
                           command=self.plot_emg)
        plots.grid(column=0, row=18, sticky=W)
        separator7 = ttk.Separator(self.left, orient="horizontal")
        separator7.grid(column=0, columnspan=3, row=19, sticky=(W,E))

        # Reset Analysis
        reset = ttk.Button(self.left,
                           text="Reset analysis", command=self.reset_analysis)
        reset.grid(column=1, row=20, sticky=(W,E))

        # Create right side framing for functionalities
        self.right = ttk.Frame(root, padding="10 10 12 12")
        self.right.grid(column=1, row=0, sticky=(N, S, E))

        # Create empty figure
        self.first_fig = Figure(figsize=(20/2.54,15/2.54))
        self.canvas = FigureCanvasTkAgg(self.first_fig, master=self.right)
        self.canvas.get_tk_widget().grid(row=0, column=0)

        # Create logo figure
        self.logo_canvas = Canvas(self.right, height=590, width=800, bg="white")
        self.logo_canvas.grid(row=0, column=0)
        self.logo = tk.PhotoImage(file="logo.png")
        self.logo_canvas.create_image(400,300,anchor="center", image=self.logo)

        for child in self.left.winfo_children():
            child.grid_configure(padx=5, pady=5)

    ## Define functionalities for buttons used in GUI

    def get_file_input(self):
        """Funktion to load the file for analysis.
           The user is asked to select the file.
        """
        # Ask user to select the file
        file_path = filedialog.askopenfilename()
        self.file_path = file_path
        # Get filename
        filename = os.path.splitext(os.path.basename(file_path))[0]
        self.filename = filename

        # Add filename to label
        root.title(self.filename)

        # Check filetype for processing
        if self.filetype.get() == "OTB":
            # load OTB
            self.resdict = openhdemg.emg_from_otb(file=self.file_path)

            # Add filespecs
            ttk.Label(self.left, text=str(len(self.resdict["RAW_SIGNAL"].columns))).grid(column=2, row=2, sticky=(W,E))
            ttk.Label(self.left, text=str(self.resdict["NUMBER_OF_MUS"])).grid(column=2, row=3, sticky=(W,E))
            ttk.Label(self.left, text=str(self.resdict["EMG_LENGTH"])).grid(column=2, row=4, sticky=(W,E))

        elif self.filetype.get() == "DEMUSE":
            # load DEMUSE
            self.resdict = openhdemg.emg_from_demuse(file=self.file_path)

            # Add filespecs
            ttk.Label(self.left, text=str(len(self.resdict["RAW_SIGNAL"].columns))).grid(column=2, row=2, sticky=(W,E))
            ttk.Label(self.left, text=str(self.resdict["NUMBER_OF_MUS"])).grid(column=2, row=3, sticky=(W,E))
            ttk.Label(self.left, text=str(self.resdict["EMG_LENGTH"])).grid(column=2, row=4, sticky=(W,E))

        else:
            # load refsig
            self.resdict = openhdemg.refsig_from_otb(file=self.file_path)
            # Recondifgure labels for refsig
            ttk.Label(self.left, text=str(len(self.resdict["REF_SIGNAL"].columns))).grid(column=2, row=2, sticky=(W,E))
            ttk.Label(self.left, text="NA").grid(column=2, row=3, sticky=(W,E))
            ttk.Label(self.left, text="        ").grid(column=2, row=4, sticky=(W,E))

    def save_emgfile(self):
        """Function to save the edited emgfile.
           Results are saves in .json file.
        """
        try:
            # Ask user to select the directory
            save_path = filedialog.askdirectory()
            save_filepath = save_path + "/" + self.filename + "_saved.json"

            # Get emgfile
            save_emg = self.resdict

            # Save json file
            openhdemg.save_json_emgfile(emgfile=save_emg, path=save_filepath)

        except AttributeError:
            tk.messagebox.showerror("Information", "Make sure a file is loaded.")

    def export_to_excel(self):
        """Function to export any prior analysis results.
           Results are saved in an excel sheet.
        """
        try:
            # Get file directory
            path = os.path.split(self.file_path)[0]

            # Define excel writer
            writer = pd.ExcelWriter(path + "/" + "Results.xlsx")

            # Check for attributes and write sheets
            if hasattr(self, "mvif_df"):
                self.mvif_df.to_excel(writer, sheet_name="MVIF")

            if hasattr(self, "rfd"):
                self.rfd.to_excel(writer, sheet_name="RFD")

            if hasattr(self, "exportable_df"):
                self.exportable_df.to_excel(writer, sheet_name="Basic MU Properties")

            if hasattr(self, "mus_dr"):
                self.mus_dr.to_excel(writer, sheet_name="MU Discharge Rate")

            if hasattr(self, "mu_thresholds"):
                self.mu_thresholds.to_excel(writer, sheet_name="MU Thresholds")

            writer.save()

        except IndexError:
            tk.messagebox.showerror("Information", "Please conduct at least one analysis before saving")

        except AttributeError:
            tk.messagebox.showerror("Information", "Make sure a file is loaded.")

    def reset_analysis(self):
        """Funktion to restore the base file.
           Any analysis progress will be deleted by reloading the base file.
        """
        # Get user input and check whether analysis wants to be truly resetted
        if tk.messagebox.askokcancel("Attention", "Do you really want to reset the analysis?"):

            # user decided to rest analysis
            try:

                # reload original file
                if self.filetype.get() == "OTB":
                    self.resdict = openhdemg.emg_from_otb(file=self.file_path)

                    # Update Filespecs
                    ttk.Label(self.left, text=str(len(self.resdict["RAW_SIGNAL"].columns))).grid(column=2, row=2, sticky=(W,E))
                    ttk.Label(self.left, text=str(self.resdict["NUMBER_OF_MUS"])).grid(column=2, row=3, sticky=(W,E))
                    ttk.Label(self.left, text=str(self.resdict["EMG_LENGTH"])).grid(column=2, row=4, sticky=(W,E))

                elif self.filetype.get() == "DEMUSE":
                    self.resdict = openhdemg.emg_from_demuse(file=self.file_path)

                    # Update Filespecs
                    ttk.Label(self.left, text=str(len(self.resdict["RAW_SIGNAL"].columns))).grid(column=2, row=2, sticky=(W,E))
                    ttk.Label(self.left, text=str(self.resdict["NUMBER_OF_MUS"])).grid(column=2, row=3, sticky=(W,E))
                    ttk.Label(self.left, text=str(self.resdict["EMG_LENGTH"])).grid(column=2, row=4, sticky=(W,E))

                else:
                    # load refsig
                    self.resdict = openhdemg.refsig_from_otb(file=self.file_path)
                    # Recondifgure labels for refsig
                    ttk.Label(self.left, text=str(len(self.resdict["REF_SIGNAL"].columns))).grid(column=2, row=2, sticky=(W,E))
                    ttk.Label(self.left, text="NA").grid(column=2, row=3, sticky=(W,E))
                    ttk.Label(self.left, text="        ").grid(column=2, row=4, sticky=(W,E))

                # Update Plot
                if hasattr(self, "fig"):
                    self.in_gui_plotting()

                # Clear frame for output
                if hasattr(self, "terminal"):
                    self.terminal = ttk.LabelFrame(root, text="Result Output",
                                              height=100, relief="ridge")
                    self.terminal.grid(column=0, row=21, columnspan=2, pady=8, padx=10,
                                  sticky=(N,S,W,E))

            except AttributeError:
                tk.messagebox.showerror("Information", "Make sure a file is loaded.")
#-----------------------------------------------------------------------------------------------
# Plotting inside of GUI

    def in_gui_plotting(self, plot="idr"):
        """Function to plot any analysis results in the GUI for inspection.
           Plots are updated during the analysis process.
        """

        try:
            if self.filetype.get() == "REFSIG":
                self.fig = openhdemg.plot_refsig(emgfile=self.resdict, showimmediately=False, tight_layout=False)
            elif plot == "idr":
                self.fig = openhdemg.plot_idr(emgfile=self.resdict, munumber=[*range(0, int(self.resdict["NUMBER_OF_MUS"]))], showimmediately=False, tight_layout=False)
            elif plot == "refsig_fil":
                self.fig = openhdemg.plot_refsig(emgfile=self.resdict, showimmediately=False, tight_layout=False)
            elif plot == "refsig_off":
                self.fig = openhdemg.plot_refsig(emgfile=self.resdict, showimmediately=False, tight_layout=False)

            self.canvas = FigureCanvasTkAgg(self.fig, master=self.right)
            self.canvas.get_tk_widget().grid(row=0, column=0)
            toolbar = NavigationToolbar2Tk(self.canvas, self.right, pack_toolbar=False)
            toolbar.grid(row=1, column=0)
            plt.close()

        except AttributeError:
            tk.messagebox.showerror("Information", "Make sure a file is loaded.")

#-----------------------------------------------------------------------------------------------
# Sorting of motor units

    def sort_mus(self):
        """Function to sort motor units ascending according to recruitement order.
           Return sorted emgfile.
        """
        try:
            # Sort emgfile
            self.resdict = openhdemg.sort_mus(emgfile=self.resdict)

            # Update plot
            if hasattr(self, "fig"):
                self.in_gui_plotting()

        except AttributeError:
            tk.messagebox.showerror("Information", "Make sure a file is loaded.")

#-----------------------------------------------------------------------------------------------
# Removal of single motor units

    def remove_mus(self):
        """Function to remove single motor units from analysis.
           MUs can be recovered by reseting the analysis progress.
        """
        # Create new window
        self.head = tk.Toplevel(bg='LightBlue4')
        self.head.title("Motor Unit Removal Window")
        self.head.grab_set()

        # Select Motor Unit
        ttk.Label(self.head, text="Select MU:").grid(column=0, row=0, padx=5, pady=5)

        self.mu_to_remove = StringVar()
        removed_mu_value = [*range(0, self.resdict["NUMBER_OF_MUS"])]
        removed_mu = ttk.Combobox(self.head, width=10, textvariable=self.mu_to_remove)
        removed_mu["values"] = removed_mu_value
        removed_mu["state"] = "readonly"
        removed_mu.grid(column=1, row=0, sticky=(W,E), padx=5, pady=5)

        # Remove Motor unit
        remove = ttk.Button(self.head,
                            text="Remove MU",
                            command=self.remove)
        remove.grid(column=1, row=1, sticky=(W,E), padx=5, pady=5)

    def remove(self):
        """Function that actually removes the motor unit.
        """
        # Get resdict with MU removed
        self.resdict = openhdemg.delete_mus(emgfile=self.resdict,
                                            munumber=int(self.mu_to_remove.get()))
        # Upate MU number
        ttk.Label(self.left, text=str(self.resdict["NUMBER_OF_MUS"])).grid(column=2, row=3, sticky=(W,E))

        # Update selection field
        self.mu_to_remove = StringVar()
        removed_mu_value = [*range(0, self.resdict["NUMBER_OF_MUS"])]
        removed_mu = ttk.Combobox(self.head, width=10, textvariable=self.mu_to_remove)
        removed_mu["values"] = removed_mu_value
        removed_mu["state"] = "readonly"
        removed_mu.grid(column=1, row=0, sticky=(W,E), padx=5, pady=5)

        # Update plot
        if hasattr(self, "fig"):
            self.in_gui_plotting()

#-----------------------------------------------------------------------------------------------
# Editing of single motor Units

    def editing_mus(self):
        """Function to edit sindle motor units.
           For now, this contains only plotting single MUs.
           More options will be added.
        """

        # Create new window
        self.head = tk.Toplevel(bg='LightBlue4')
        self.head.title("Motor Unit Eiditing Window")
        self.head.grab_set()

        # Select Motor Unit
        ttk.Label(self.head, text="Select MU:").grid(column=0, row=0, sticky=W, padx=5, pady=5)

        self.mu_to_edit = StringVar()
        edit_mu_value = [*range(0, self.resdict["NUMBER_OF_MUS"])]
        edit_mu = ttk.Combobox(self.head, width=10, textvariable=self.mu_to_edit)
        edit_mu["values"] = edit_mu_value
        edit_mu["state"] = "readonly"
        edit_mu.grid(column=1, row=0, sticky=(W,E), padx=5, pady=5)

        # Button to plot MU
        single_mu = ttk.Button(self.head,
                              text="View single MU",
                              command=self.view_single_mu)
        single_mu.grid(column=1, row=1, sticky=(W,E), padx=5, pady=5)

    def view_single_mu(self):
        """Funktion that plots single selected MU.
        """
        # Make figure
        fig = openhdemg.plot_idr(emgfile=self.resdict,
                                 munumber=int(self.mu_to_edit.get()),
                                 showimmediately=False)
        # Create canvas and plot
        canvas = FigureCanvasTkAgg(fig, master=self.head)
        canvas_plot = canvas.get_tk_widget()
        canvas_plot.grid(column=1, row=2, sticky=(W,E))
        # Place matplotlib toolbar
        toolbar = NavigationToolbar2Tk(canvas, self.head, pack_toolbar=False)
        toolbar.grid(row=3, column=1)
        # terminate matplotlib to ensure GUI shutdown when closed
        plt.close()

#-----------------------------------------------------------------------------------------------
# Editing of Reference EMG Signal

    def edit_refsig(self):
        """Function to edit the emg reference signal. A new window is openend.
           This funtion provides two options, refsig filtering and offset removal.
        """
        # Create new window
        self.head = tk.Toplevel(bg='LightBlue4')
        self.head.title("Reference Signal Eiditing Window")
        self.head.grab_set()

        # Filter Refsig
        # Define Labels
        ttk.Label(self.head, text="Filter Order").grid(column=1, row=0, sticky=(W,E))
        ttk.Label(self.head, text="Cutoff Freq").grid(column=2, row=0, sticky=(W,E))
        # Fiter button
        basic = ttk.Button(self.head,
                           text="Filter Refsig",
                           command=self.filter_refsig)
        basic.grid(column=0, row=1, sticky=W)

        self.filter_order = StringVar()
        order = ttk.Entry(self.head,
                             width=10,
                             textvariable=self.filter_order)
        order.grid(column=1, row=1)
        self.filter_order.set(4)

        self.cutoff_freq = StringVar()
        cutoff = ttk.Entry(self.head,
                             width=10,
                             textvariable=self.cutoff_freq)
        cutoff.grid(column=2, row=1)
        self.cutoff_freq.set(20)

        # Remove offset of reference signal
        separator2 = ttk.Separator(self.head, orient="horizontal")
        separator2.grid(column=0, columnspan=3, row=2, sticky=(W,E), padx=5, pady=5)

        ttk.Label(self.head, text="Offset Value").grid(column=1, row=3, sticky=(W,E))
        ttk.Label(self.head, text="Automatic Offset").grid(column=2, row=3, sticky=(W,E))
        # Offset removal button
        basic2 = ttk.Button(self.head,
                           text="Remove Offset",
                           command=self.remove_offset)
        basic2.grid(column=0, row=4, sticky=W)

        self.offsetval = StringVar()
        offset = ttk.Entry(self.head,
                             width=10,
                             textvariable=self.offsetval)
        offset.grid(column=1, row=4)
        self.offsetval.set(4)

        self.auto_eval = StringVar()
        auto = ttk.Entry(self.head,
                             width=10,
                             textvariable=self.auto_eval)
        auto.grid(column=2, row=4)
        self.auto_eval.set(0)

        # Add padding to all children widgets of head
        for child in self.head.winfo_children():
            child.grid_configure(padx=5, pady=5)

    ### Define functions for Refsig editing

    def filter_refsig(self):
        """Function that filters the refig based on specs.
        """
        try:
            # Filter refsig
            self.resdict = openhdemg.filter_refsig(emgfile=self.resdict,
                                                   order=int(self.filter_order.get()),
                                                   cutoff=int(self.cutoff_freq.get()))
            # Plot filtered Refsig
            self.in_gui_plotting(plot="refsig_fil")

        except TypeError:
            tk.messagebox.showerror("Information", "Make sure a Refsig file is loaded.")


    def remove_offset(self):
        """Function that removes Refsig offset.
        """
        try:
            # Remove offset
            self.resdict = openhdemg.remove_offset(emgfile=self.resdict,
                                                   offsetval=int(self.offsetval.get()),
                                                   auto=int(self.auto_eval.get()))
            # Update Plot
            self.in_gui_plotting(plot="refsig_off")

        except TypeError:
            tk.messagebox.showerror("Information", "Make sure a Refsig file is loaded.")

#-----------------------------------------------------------------------------------------------
# Resize EMG File

    def resize_file(self):
        """Function to resize the EMG. A new window is openend.
        """
        # Create new window
        self.head = tk.Toplevel(bg='LightBlue4')
        self.head.title("Resize EMG File Window")
        self.head.grab_set()

        # Enter start point of resizing area
        select_res = ttk.Button(self.head,
                                text="Select Resize", command=self.select_resize)
        select_res.grid(column=0, row=0)

        ttk.Label(self.head,
                  text="Enter Startpoint:").grid(column=0, row=1, sticky=W, padx=5, pady=5)

        self.start_area = StringVar()
        start = ttk.Entry(self.head,
                             width=10,
                             textvariable=self.start_area)
        start.grid(column=1, row=1,padx=5, pady=5)
        self.start_area.set(120)

        # Enter end point of resizing area
        ttk.Label(self.head,
                  text="Enter Endpoint:").grid(column=0, row=2, sticky=W, padx=5, pady=5)

        self.end_area = StringVar()
        end = ttk.Entry(self.head,
                             width=10,
                             textvariable=self.end_area)
        end.grid(column=1, row=2, padx=5, pady=5)
        self.end_area.set(2560)

        # Resize Button
        resize = ttk.Button(self.head,
                            text="Resize File", command=self.resize_emgfile)
        resize.grid(column=1, row=3, sticky=(W,E), padx=5, pady=5)

    ### Define function for resizing

    def select_resize(self):
        """ Function to get resize selection from user.
        """
        # Open selection window for user
        start, end = openhdemg.showselect(emgfile=self.resdict, title="Select the start/end area to consider then press enter")
        self.resdict, start_, end_ = openhdemg.resize_emgfile(emgfile=self.resdict,
                                                              area=[start, end])
        # Update Plot
        self.in_gui_plotting()

    def resize_emgfile(self):
        """Function that actually resizes the file.
        """
        # Resize the file.
        self.resdict, start_, end_ = openhdemg.resize_emgfile(emgfile=self.resdict,
                                                              area=[int(self.start_area.get()),
                                                                   int(self.end_area.get())])
        # Define dictionary for pandas
        mvf_dic = {"Length": [self.resdict["EMG_LENGTH"]],
                   "Start": [start_],
                   "End": [end_]}
        df = pd.DataFrame(data=mvf_dic)

        # Display resizing specs
        self.display_results(df)

        # Update file length value
        ttk.Label(self.left, text=str(self.resdict["EMG_LENGTH"])).grid(column=2, row=4, sticky=(W,E))

        # Update plot
        self.in_gui_plotting()

#-----------------------------------------------------------------------------------------------
# Analysis of Force

    def analyze_force(self):
        """Function to analyse force singal. A new window is opened.
           The user can calculate the MVC of the steady state and the RFD.
        """
        # Create new window
        self.head = tk.Toplevel(bg='LightBlue4')
        self.head.title("Force Analysis Window")
        self.head.grab_set()

        # Get MVIF
        get_mvf = ttk.Button(self.head,
                             text="Get MVIF", command=self.get_mvif)
        get_mvf.grid(column=0, row=1, sticky=(W,E), padx=5, pady=5)

        # Get RFD
        separator1 = ttk.Separator(self.head, orient="horizontal")
        separator1.grid(column=0, columnspan=3, row=2, sticky=(W,E), padx=5, pady=5)

        ttk.Label(self.head, text="RFD miliseconds").grid(column=1, row=3, sticky=(W,E), padx=5, pady=5)

        get_rfd =  ttk.Button(self.head,
                             text="Get RFD", command=self.get_rfd)
        get_rfd.grid(column=0, row=4, sticky=(W,E), padx=5, pady=5)

        self.rfdms = StringVar()
        milisecond = ttk.Entry(self.head,
                               width=10, textvariable=self.rfdms)
        milisecond.grid(column=1, row=4, sticky=(W,E), padx=5, pady=5)
        self.rfdms.set("50,100,150,200")

    ### Define functions for force analysis

    def get_mvif(self):
        """Function that retrieves calculated MVIF.
        """
        self.mvif = openhdemg.get_mvif(emgfile=self.resdict)
        # Define dictionary for pandas
        mvf_dic = {"MVIF": [self.mvif]}
        self.mvif_df = pd.DataFrame(data=mvf_dic)
        # Display results
        self.display_results(self.mvif_df)

    def get_rfd(self):
        """Function that retrieves calculated RFD.
        """
        # Define list for RFD computation
        ms = str(self.rfdms.get())
        ms_list = ms.split(",")
        ms_list = [int(i) for i in ms_list]
        # Calculate rfd
        self.rfd = openhdemg.compute_rfd(emgfile=self.resdict,
                                         ms=ms_list)
        # Display results
        self.display_results(self.rfd)
#-----------------------------------------------------------------------------------------------
# Analysis of motor unit properties

    def mu_analysis(self):
        """Function to analyse motor unit properties.
           The user can select between recruitement threshold,
           discharge rate or basic properties computing.
        """
        # Create new window
        self.head = tk.Toplevel(bg='LightBlue4')
        self.head.title("Motor Unit Properties Window")
        self.head.grab_set()

        # MVIF Entry
        ttk.Label(self.head, text="Enter MVIF[n]:").grid(column=0, row=0, sticky=(W))
        self.mvif_value = StringVar()
        enter_mvif = ttk.Entry(self.head, width=20, textvariable=self.mvif_value)
        enter_mvif.grid(column=1, row=0, sticky=(W,E))

        # Compute MU re-/derecruitement threshold
        separator = ttk.Separator(self.head, orient="horizontal")
        separator.grid(column=0, columnspan=4, row=2, sticky=(W,E), padx=5, pady=5)

        thresh = ttk.Button(self.head,
                            text="Compute threshold",
                            command=self.compute_mu_threshold)
        thresh.grid(column=0, row=3, sticky=W)

        self.ct_event = StringVar()
        ct_events_entry = ttk.Combobox(self.head,
                                 width=10,
                                 textvariable=self.ct_event)
        ct_events_entry["values"] = ("rt", "dert", "rt_dert")
        ct_events_entry["state"] = "readonly"
        ct_events_entry.grid(column=1, row=3, sticky=(W,E))
        self.ct_event.set("Event")

        self.ct_type = StringVar()
        ct_types_entry = ttk.Combobox(self.head,
                                 width=10,
                                 textvariable=self.ct_type)
        ct_types_entry["values"] = ("abs", "rel", "abs_rel")
        ct_types_entry["state"] = "readonly"
        ct_types_entry.grid(column=2, row=3, sticky=(W,E))
        self.ct_type.set("Type")

        # Compute motor unit discharge rate
        separator1 = ttk.Separator(self.head, orient="horizontal")
        separator1.grid(column=0, columnspan=4, row=4, sticky=(W,E), padx=5, pady=5)

        ttk.Label(self.head, text="Firings at Rec").grid(column=1, row=5, sticky=(W,E))
        ttk.Label(self.head, text="Firings Start/End Steady").grid(column=2, row=5, sticky=(W,E))

        dr_rate = ttk.Button(self.head,
                             text="Compute discharge rate",
                             command=self.compute_mu_dr)
        dr_rate.grid(column=0, row=6, sticky=W)

        self.firings_rec = StringVar()
        firings_1 = ttk.Entry(self.head,
                             width=20,
                             textvariable=self.firings_rec)
        firings_1.grid(column=1, row=6)
        self.firings_rec.set(4)

        self.firings_ste = StringVar()
        firings_2 = ttk.Entry(self.head,
                             width=20,
                             textvariable=self.firings_ste)
        firings_2.grid(column=2, row=6)
        self.firings_ste.set(10)

        self.dr_event = StringVar()
        dr_events_entry = ttk.Combobox(self.head,
                                       width=10,
                                       textvariable=self.dr_event)
        dr_events_entry["values"] = ("rec", "derec", "rec_derec", "steady", "rec_derec_steady")
        dr_events_entry["state"] = "readonly"
        dr_events_entry.grid(column=3, row=6, sticky=E)
        self.dr_event.set("Event")

        # Compute basic motor unit properties
        separator2 = ttk.Separator(self.head, orient="horizontal")
        separator2.grid(column=0, columnspan=4, row=7, sticky=(W,E), padx=5, pady=5)

        ttk.Label(self.head, text="Firings at Rec").grid(column=1, row=8, sticky=(W,E))
        ttk.Label(self.head, text="Firings Start/End Steady").grid(column=2, row=8, sticky=(W,E))

        basic = ttk.Button(self.head,
                           text="Basic MU properties",
                           command=self.basic_mus_properties)
        basic.grid(column=0, row=9, sticky=W)

        self.b_firings_rec = StringVar()
        b_firings_1 = ttk.Entry(self.head,
                             width=20,
                             textvariable=self.b_firings_rec)
        b_firings_1.grid(column=1, row=9)
        self.b_firings_rec.set(4)

        self.b_firings_ste = StringVar()
        b_firings_2 = ttk.Entry(self.head,
                             width=20,
                             textvariable=self.b_firings_ste)
        b_firings_2.grid(column=2, row=9)
        self.b_firings_ste.set(10)

        for child in self.head.winfo_children():
            child.grid_configure(padx=5, pady=5)

    ### Define functions for motor unit property calculation

    def compute_mu_threshold(self):
        """Function that actually computes the motor unit
           recruitement thresholds.
        """
        try:
            # Compute thresholds
            self.mu_thresholds = openhdemg.compute_thresholds(emgfile=self.resdict,
                                                              event_=self.ct_event.get(),
                                                              type_=self.ct_type.get(),
                                                              mvif=int(self.mvif_value.get()))
            # Display results
            self.display_results(self.mu_thresholds)

        except AttributeError:
            tk.messagebox.showerror("Information", "Load file prior to computation.")

        except ValueError:
            tk.messagebox.showerror("Information", "Enter valid MVIF.")

        except AssertionError:
            tk.messagebox.showerror("Information", "Specify Event and/or Type.")

    def compute_mu_dr(self):
        """Function that actually computes the motor unit
           discharge rates.
        """
        try:
            # Compute discharge rates
            self.mus_dr = openhdemg.compute_dr(emgfile=self.resdict,
                                               n_firings_RecDerec=int(self.firings_rec.get()),
                                               n_firings_steady=int(self.firings_ste.get()),
                                               event_=self.dr_event.get())
            # Display results
            self.display_results(self.mus_dr)

        except AttributeError:
            tk.messagebox.showerror("Information", "Load file prior to computation.")

        except ValueError:
            tk.messagebox.showerror("Information", "Enter valid Firings value.")

        except AssertionError:
            tk.messagebox.showerror("Information", "Specify Event and/or Type.")

    def basic_mus_properties(self):
        """Function that actually computes several basic motor unit
           properties.
        """
        try:
            # Calculate properties
            self.exportable_df = openhdemg.basic_mus_properties(emgfile=self.resdict,
                                                                n_firings_RecDerec = int(self.b_firings_rec.get()),
                                                                n_firings_steady = int(self.b_firings_ste.get()),
                                                                mvif = int(self.mvif_value.get()))
            # Display results
            self.display_results(self.exportable_df)

        except AttributeError:
            tk.messagebox.showerror("Information", "Load file prior to computation.")

        except ValueError:
            tk.messagebox.showerror("Information", "Enter valid MVIF.")

        except AssertionError:
            tk.messagebox.showerror("Information", "Specify Event and/or Type.")

#-----------------------------------------------------------------------------------------------
# Plot EMG

    def plot_emg(self):
        """Function that creates several plots from the emg file.
        """
        # Create new window
        self.head = tk.Toplevel(bg='LightBlue4')
        self.head.title("Plot Window")
        self.head.grab_set()

        # Plot emgsig
        plt_emgsig = ttk.Button(self.head,
                                text="Plot EMGsig",
                                command=self.plt_emgsignal)
        plt_emgsig.grid(column=0, row=0, sticky=W)

        self.channels = StringVar()
        channel_entry = ttk.Combobox(self.head,
                                     width=15,
                                     textvariable=self.channels)
        channel_entry["values"] = ("1", "12", "123", "1234")
        channel_entry.grid(column=1, row=0, sticky=(W,E))
        self.channels.set("Channel Numbers")

        separator0 = ttk.Separator(self.head, orient="horizontal")
        separator0.grid(column=0, columnspan=4, row=1, sticky=(W,E))

        # Plot refsig
        plt_refsig = ttk.Button(self.head,
                                text="Plot REFsig",
                                command=self.plt_refsignal)
        plt_refsig.grid(column=0, row=2, sticky=W)

        separator1 = ttk.Separator(self.head, orient="horizontal")
        separator1.grid(column=0, columnspan=4, row=3, sticky=(W,E))

        # Plot motor unit pulses
        plt_pulses = ttk.Button(self.head,
                                text="Plot MUpulses",
                                command=self.plt_mupulses)
        plt_pulses.grid(column=0, row=4, sticky=W)

        self.linewidth = StringVar()
        linewidth_entry = ttk.Combobox(self.head,
                                       width=15,
                                       textvariable=self.linewidth)
        linewidth_entry["values"] = ("0.25", "0.5", "0.75", "1")
        linewidth_entry.grid(column=1, row=4, sticky=(W,E))
        self.linewidth.set("Linewidth")
        separator2 = ttk.Separator(self.head, orient="horizontal")
        separator2.grid(column=0, columnspan=4, row=5, sticky=(W,E))

        # Plot impulse train
        plt_ipts = ttk.Button(self.head,
                              text="Plot IPTS",
                              command=self.plt_ipts)
        plt_ipts.grid(column=0, row=6, sticky=W)

        self.mu_numb = StringVar()
        munumb_entry = ttk.Combobox(self.head,
                                    width=15,
                                    textvariable=self.mu_numb)
        munumb_entry["values"] = ("1", "12", "123", "1234")
        munumb_entry.grid(column=1, row=6, sticky=(W,E))
        self.mu_numb.set("MU Number")
        separator3 = ttk.Separator(self.head, orient="horizontal")
        separator3.grid(column=0, columnspan=4, row=7, sticky=(W,E))

        # Plot instantaneous discharge rate
        plt_idr = ttk.Button(self.head,
                              text="Plot IDR",
                              command=self.plt_idr)
        plt_idr.grid(column=0, row=8, sticky=W)

        self.mu_numb_idr = StringVar()
        munumb_entry_idr = ttk.Combobox(self.head,
                                    width=15,
                                    textvariable=self.mu_numb_idr)
        munumb_entry_idr["values"] = ("1", "12", "123", "1234")
        munumb_entry_idr.grid(column=1, row=8, sticky=(W,E))
        self.mu_numb_idr.set("MU Number")

        for child in self.head.winfo_children():
            child.grid_configure(padx=5, pady=5)

    ### Define functions for motor unit plotting

    def plt_emgsignal(self):
        """Function to plot the raw emg signal in an seperate plot window.
           The plot can be saved and partly edited using the matplotlib options.
        """
        try:
            # Create list of channels to be plotted
            channel_list = [int(chan) for chan in self.channels.get()]
            # Plot raw emg signal
            openhdemg.plot_emgsig(emgfile=self.resdict, channels=channel_list)

        except AttributeError:
            tk.messagebox.showerror("Information", "Load file prior to computation.")

        except ValueError:
            tk.messagebox.showerror("Information", "Enter valid channel number.")

    def plt_refsignal(self):
        """Function to plot the reference signal in an seperate plot window.
           The plot can be saved and partly edited using the matplotlib options.
        """
        try:
            # Plot reference signal
            openhdemg.plot_refsig(emgfile=self.resdict)

        except AttributeError:
            tk.messagebox.showerror("Information", "Load file prior to computation.")

    def plt_mupulses(self):
        """Function to plot the motor unit pulses in an seperate plot window.
           The plot can be saved and partly edited using the matplotlib options.
        """
        try:
            # Plot motor unig pulses
            openhdemg.plot_mupulses(emgfile=self.resdict, linewidths=float(self.linewidth.get()))

        except AttributeError:
            tk.messagebox.showerror("Information", "Load file prior to computation.")

        except ValueError:
            tk.messagebox.showerror("Information", "Enter valid linewidth number.")


    def plt_ipts(self):
        """Function to plot the motor unit puls train (i.e., non-binary firing) in an seperate plot window.
           The plot can be saved and partly edited using the matplotlib options.
        """
        try:
            # Create list contaning motor units to be plotted
            mu_list = [int(mu) for mu in self.mu_numb.get()]
            # Plot motor unit puls train
            openhdemg.plot_ipts(emgfile=self.resdict, munumber=mu_list)

        except AttributeError:
            tk.messagebox.showerror("Information", "Load file prior to computation.")

        except ValueError:
            tk.messagebox.showerror("Information", "Enter valid motor unit number.")


    def plt_idr(self):
        """Function to plot the instanteous discharge rate in an seperate plot window.
           The plot can be saved and partly edited using the matplotlib options.
        """
        try:
            # Create list containing motor units to be plotted
            mu_list_idr = [int(mu) for mu in self.mu_numb_idr.get()]
            # Plot instanteous discharge rate
            openhdemg.plot_idr(emgfile=self.resdict, munumber=mu_list_idr)

        except AttributeError:
            tk.messagebox.showerror("Information", "Load file prior to computation.")

        except ValueError:
            tk.messagebox.showerror("Information", "Enter valid motor unit number.")

#-----------------------------------------------------------------------------------------------
# Analysis results display

    def display_results(self, input_df):
        """Functions that displays all analysis results in the
           output labelframe using Pandastable. Input must be a
           Pandas dataframe.
        """
        # Create frame for output
        self.terminal = ttk.LabelFrame(root, text="Result Output",
                                       height=100, relief="ridge")
        self.terminal.grid(column=0, row=21, columnspan=2, pady=8, padx=10,
                           sticky=(N,S,W,E))

        # Display results
        table = Table(self.terminal,
                          dataframe=input_df,
                          showtoolbar=False,
                          showstatusbar=False,
                          height=100)

        # Show results
        table.show()
#-----------------------------------------------------------------------------------------------

# Run GUI upon calling
if __name__ == "__main__":
    root = Tk()
    root['bg'] = 'LightBlue4'
    GUI(root)
    root.mainloop()
