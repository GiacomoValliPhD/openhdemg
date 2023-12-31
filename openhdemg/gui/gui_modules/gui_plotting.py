"""This modules contains all plotting functionalities for the GUI"""

import os
import webbrowser
from tkinter import ttk, W, E, StringVar, PhotoImage
from PIL import Image

import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
import openhdemg.library as openhdemg

class PlotEmg:
    """
    Instance method to open "Plot Window". Options to create
    several plots from the emgfile are displayed.

    Executed when button "Plot EMG" in master GUI window is pressed.
    The plots are displayed in seperate windows.
    """
    def __init__(self, parent):

        try:
            self.parent = parent
            self.head = ctk.CTkToplevel(fg_color="LightBlue4")
            self.head.title("Plot Window")
            self.head.wm_iconbitmap()
            self.head.grab_set()

            # define tk variables for later use
            self.matrix_rc = StringVar() # Matrix rows columns
            self.mat_label = ttk.Label() # Label for matriy rows columns
            self.row_cols_entry = ttk.Entry() # Entry for matrix rows columns

            # Reference signal
            ctk.CTkLabel(self.head, text="Reference signal", font=('Segoe UI',15, 'bold')).grid(
                column=0, row=0, sticky=W
            )
            self.ref_but = StringVar()
            ref_button = ctk.CTkCheckBox(
                self.head,
                variable=self.ref_but,
                bg_color="LightBlue4",
                onvalue="True",
                offvalue="False",
                text=""
            )
            ref_button.grid(column=1, row=0, sticky=(W))
            self.ref_but.set(False)

            # Time
            ctk.CTkLabel(self.head, text="Time in seconds", font=('Segoe UI',15, 'bold')).grid(column=0, row=1, sticky=W)
            self.time_sec = StringVar()
            time_button = ctk.CTkCheckBox(
                self.head,
                variable=self.time_sec,
                bg_color="LightBlue4",
                onvalue="True",
                offvalue="False",
                text=""
            )
            time_button.grid(column=1, row=1, sticky=W)
            self.time_sec.set(False)

            # Figure Size
            ctk.CTkLabel(self.head, text="Figure size in cm (h,w)", font=('Segoe UI',15, 'bold')).grid(column=0, row=2)
            self.size_fig = StringVar()
            fig_entry = ctk.CTkEntry(self.head, width=100, textvariable=self.size_fig)
            self.size_fig.set("20,15")
            fig_entry.grid(column=1, row=2, sticky=W)

            # Plot emgsig
            plt_emgsig = ctk.CTkButton(
                self.head, text="Plot EMGsig", command=self.plt_emgsignal,
                fg_color="#E5E4E2", text_color="black", border_color="black", border_width=1)
            plt_emgsig.grid(column=0, row=3, sticky=W)

            self.channels = StringVar()
            channel_entry_values = ("0", "0,1,2", "0,1,2,3")
            channel_entry = ctk.CTkComboBox(
                self.head, width=150, variable=self.channels,
                values=channel_entry_values
            )
            channel_entry.grid(column=1, row=3, sticky=(W, E))
            self.channels.set("Channel Numbers")

            # Plot refsig
            plt_refsig = ctk.CTkButton(
                self.head, text="Plot RefSig", command=self.plt_refsignal,
                fg_color="#E5E4E2", text_color="black", border_color="black", border_width=1)
            plt_refsig.grid(column=0, row=4, sticky=W)

            # Plot motor unit pulses
            plt_pulses = ctk.CTkButton(
                self.head, text="Plot MUpulses", command=self.plt_mupulses,
                fg_color="#E5E4E2", text_color="black", border_color="black", border_width=1)
            plt_pulses.grid(column=0, row=5, sticky=W)

            # Define Linewidth for plot
            self.linewidth = StringVar()
            linewidth_entry_values = ("0.25", "0.5", "0.75", "1")
            linewidth_entry = ctk.CTkComboBox(
                self.head, width=15, variable=self.linewidth,
                values=linewidth_entry_values
            )
            linewidth_entry.grid(column=1, row=5, sticky=(W, E))
            self.linewidth.set("Linewidth")

            # Plot impulse train
            plt_ipts_but = ctk.CTkButton(self.head, text="Plot Source", command=self.plt_ipts,
                                        fg_color="#E5E4E2", text_color="black", border_color="black", border_width=1)
            plt_ipts_but.grid(column=0, row=6, sticky=W)

            self.mu_numb = StringVar()
            munumb_entry_values = ("0", "0,1,2", "0,1,2,3", "all")
            munumb_entry = ctk.CTkComboBox(self.head, width=15, variable=self.mu_numb,
                                            values=munumb_entry_values)
            munumb_entry.grid(column=1, row=6, sticky=(W, E))
            self.mu_numb.set("MU Number")

            # Plot instantaneous discharge rate
            plt_idr_but = ctk.CTkButton(self.head, text="Plot IDR", command=self.plt_idr,
                                    fg_color="#E5E4E2", text_color="black", border_color="black", border_width=1)
            plt_idr_but.grid(column=0, row=7, sticky=W)

            self.mu_numb_idr = StringVar()
            munumb_entry_idr_values = ("0", "0,1,2", "0,1,2,3", "all")
            munumb_entry_idr = ctk.CTkComboBox(
                self.head, width=15, variable=self.mu_numb_idr,
                values=munumb_entry_idr_values
            )
            munumb_entry_idr.grid(column=1, row=7, sticky=(W, E))
            self.mu_numb_idr.set("MU Number")

            # This section containes the code for column 3++
            # Separator
            ttk.Separator(self.head, orient="vertical").grid(
                row=3, column=2, rowspan=6, ipady=120
            )

            # Matrix code
            ctk.CTkLabel(self.head, text="Matrix Code", font=('Segoe UI',15, 'bold')).grid(row=0, column=3, sticky=(W))

            self.mat_code = StringVar()
            matrix_code_values = ("GR08MM1305", "GR04MM1305", "GR10MM0808", "Trigno Galileo Sensor", "None")
            matrix_code = ctk.CTkComboBox(self.head, width=100, variable=self.mat_code,
                                            values=matrix_code_values, state="readonly")
            matrix_code.grid(row=0, column=4, sticky=(W, E))
            self.mat_code.set("GR08MM1305")

            # Trace matrix code value
            self.mat_code.trace_add("write", self.on_matrix_none)

            # Matrix Orientation
            ctk.CTkLabel(self.head, text="Orientation", font=('Segoe UI',15, 'bold')).grid(row=1, column=3, sticky=(W))
            self.mat_orientation = StringVar()
            orientation_values = ("0", "180")
            orientation = ctk.CTkComboBox(
                self.head, width=15, variable=self.mat_orientation,
                values=orientation_values, state="readonly"
            )
            orientation.grid(row=1, column=4, sticky=(W, E))
            self.mat_orientation.set("180")
            # Disable the orientation setting for DELSYS files
            if self.parent.resdict["SOURCE"] == "DELSYS":
                orientation.config(state="disabled")

            # Plot derivation
            # Button
            deriv_button = ctk.CTkButton(
                self.head, text="Plot Derivation", command=self.plot_derivation,
                fg_color="#E5E4E2", text_color="black", border_color="black", border_width=1)
            deriv_button.grid(row=3, column=3, sticky=W)

            # Combobox Config
            self.deriv_config = StringVar()
            configuration_values = ("Single differential", "Double differential")
            configuration = ctk.CTkComboBox(
                self.head, width=15, variable=self.deriv_config,
                values=configuration_values, state="readonly"
            )
            configuration.grid(row=3, column=4, sticky=(W, E))
            self.deriv_config.set("Configuration")

            # Combobox Matrix
            self.deriv_matrix = StringVar()
            mat_column_values = ("col0", "col1", "col2", "col3", "col4")
            mat_column = ctk.CTkComboBox(
                self.head, width=100, variable=self.deriv_matrix,
                values=mat_column_values, state="readonly"
            )
            mat_column.grid(row=3, column=5, sticky=(W, E))
            self.deriv_matrix.set("Matrix Column")

            # Motor unit action potential
            # Button
            muap_button = ctk.CTkButton(
                self.head, text="Plot MUAPs", command=self.plot_muaps,
                fg_color="#E5E4E2", text_color="black", border_color="black", border_width=1)
            muap_button.grid(row=4, column=3, sticky=W)

            # Combobox Config
            self.muap_config = StringVar()
            config_muap_values = (
                "Monopolar",
                "Single differential",
                "Double differential",
            )
            config_muap = ctk.CTkComboBox(
                self.head, width=15, variable=self.muap_config,
                values=config_muap_values, state="readonly"
            )
            config_muap.grid(row=4, column=4, sticky=(W, E))
            self.muap_config.set("Configuration")
            # Disable config for DELSYS files
            if self.parent.resdict["SOURCE"] == "DELSYS":
                config_muap.config(state="disabled")

            # Combobox MU Number
            self.muap_munum = StringVar()
            mu_numbers = tuple(str(number) for number in range(0, self.parent.resdict["NUMBER_OF_MUS"]))
            muap_munum = ctk.CTkComboBox(self.head, width=15, variable=self.muap_munum,
                                        values=mu_numbers, state="readonly")
            muap_munum.grid(row=4, column=5, sticky=(W, E))
            self.muap_munum.set("MU Number")

            # Combobox Timewindow
            self.muap_time = StringVar()
            timewindow_values = ("25", "50", "100", "200")
            timewindow = ctk.CTkComboBox(self.head, width=120, variable=self.muap_time,
                                            values=timewindow_values)
            timewindow.grid(row=4, column=6, sticky=(W, E))
            self.muap_time.set("Timewindow (ms)")
            # Disable Timewindow for DELSYS files 
            if self.parent.resdict["SOURCE"] == "DELSYS":
                timewindow.config(state="disabled")

            # Matrix Illustration Graphic
            matrix_canvas = ctk.CTkCanvas(self.head, height=150, width=600, bg="white")
            matrix_canvas.grid(row=5, column=3, rowspan=5, columnspan=5)
            parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.matrix = PhotoImage(
                file= parent_dir + "/gui_files/Matrix.png"
            )
            matrix_canvas.create_image(0, 0, anchor="nw", image=self.matrix)
            # Information Button
            self.info = ctk.CTkImage(
                light_image=Image.open(parent_dir + "/gui_files/Info.png"),
                size = (30, 30)
            )
            info_button = ctk.CTkButton(
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
            CTkMessagebox(title="Info", message="Make sure a file is loaded.", icon="info",
                          bg_color="#fdbc00", fg_color="LightBlue4", title_color="#000000",
                          button_color="#E5E4E2", button_text_color="#000000", button_hover_color="#1e52fe",
                          font=('Segoe UI',15, 'bold'), text_color="#FFFFFF")
            self.head.destroy()

    ### Define functions for motor unit plotting
    def on_matrix_none(self, *args):
        """
        This function is called when the value of the mat_code variable is changed.

        When the variable is set to "None" it will create an Entrybox on the grid at column 1 and row 6,
        and when the mat_code is set to something else it will remove the entrybox from the grid.
        """
        if self.mat_code.get() == "None":
            # Place label defined in init
            self.mat_label = ttk.Label(self.head, text="Rows, Columns:") # Label for matriy rows columns
            self.mat_label.grid(row=0, column=5, sticky=E)

            # Column entry only when specified matrix code
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
                    emgfile=self.parent.resdict,
                    channels=chan_list,
                    addrefsig=eval(self.ref_but.get()),
                    timeinseconds=eval(self.time_sec.get()),
                    figsize=figsize,
                )

            else:
                # Plot raw emg signal
                openhdemg.plot_emgsig(
                    emgfile=self.parent.resdict,
                    channels=int(channels),
                    addrefsig=eval(self.ref_but.get()),
                    timeinseconds=eval(self.time_sec.get()),
                    figsize=figsize,
                )

        except ValueError:
            CTkMessagebox(title="Info", message="Enter valid channel number or non-negative figure size.", icon="info",
                          bg_color="#fdbc00", fg_color="LightBlue4", title_color="#000000",
                          button_color="#E5E4E2", button_text_color="#000000", button_hover_color="#1e52fe",
                          font=('Segoe UI',15, 'bold'), text_color="#FFFFFF")
        except KeyError:
            CTkMessagebox(title="Info", message="Enter valid channel number.", icon="info",
                          bg_color="#fdbc00", fg_color="LightBlue4", title_color="#000000",
                          button_color="#E5E4E2", button_text_color="#000000", button_hover_color="#1e52fe",
                          font=('Segoe UI',15, 'bold'), text_color="#FFFFFF")
        except IndexError:
            CTkMessagebox(title="Info", message="Enter valid figure size. Must be non negative and tuple of (heigth, width).",
                          icon="info", bg_color="#fdbc00", fg_color="LightBlue4", title_color="#000000",
                          button_color="#E5E4E2", button_text_color="#000000", button_hover_color="#1e52fe",
                          font=('Segoe UI',15, 'bold'), text_color="#FFFFFF")

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
            emgfile=self.parent.resdict,
            timeinseconds=eval(self.time_sec.get()),
            figsize=figsize,
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

            # Plot motor unit pulses
            openhdemg.plot_mupulses(
                emgfile=self.parent.resdict,
                linewidths=float(self.linewidth.get()),
                addrefsig=eval(self.ref_but.get()),
                timeinseconds=eval(self.time_sec.get()),
                figsize=figsize,
            )

        except ValueError:
            CTkMessagebox(title="Info", message="Enter valid linewidth number.", icon="info",
                          bg_color="#fdbc00", fg_color="LightBlue4", title_color="#000000",
                          button_color="#E5E4E2", button_text_color="#000000", button_hover_color="#1e52fe",
                          font=('Segoe UI',15, 'bold'), text_color="#FFFFFF")

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
                    emgfile=self.parent.resdict,
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
                    emgfile=self.parent.resdict,
                    munumber=mu_list,
                    addrefsig=eval(self.ref_but.get()),
                    timeinseconds=eval(self.time_sec.get()),
                    figsize=figsize,
                )

            else:
                # Plot motor unit puls train in default
                openhdemg.plot_ipts(
                    emgfile=self.parent.resdict,
                    munumber=int(mu_numb),
                    addrefsig=eval(self.ref_but.get()),
                    timeinseconds=eval(self.time_sec.get()),
                    figsize=figsize,
                )

        except ValueError:
            CTkMessagebox(title="Info", message="Enter valid motor unit number.", icon="info",
                          bg_color="#fdbc00", fg_color="LightBlue4", title_color="#000000",
                          button_color="#E5E4E2", button_text_color="#000000", button_hover_color="#1e52fe",
                          font=('Segoe UI',15, 'bold'), text_color="#FFFFFF")

        except KeyError:
            CTkMessagebox(title="Info", message="Enter valid motor unit number.", icon="info",
                          bg_color="#fdbc00", fg_color="LightBlue4", title_color="#000000",
                          button_color="#E5E4E2", button_text_color="#000000", button_hover_color="#1e52fe",
                          font=('Segoe UI',15, 'bold'), text_color="#FFFFFF")

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
                    emgfile=self.parent.resdict,
                    addrefsig=eval(self.ref_but.get()),
                    timeinseconds=eval(self.time_sec.get()),
                    figsize=figsize,
                )

            elif len(mu_idr) > 2:
                mu_list_idr = mu_idr.split(",")
                mu_list_idr = [int(mu) for mu in mu_list_idr]
                # Plot instanteous discharge rate
                openhdemg.plot_idr(
                    emgfile=self.parent.resdict,
                    munumber=mu_list_idr,
                    addrefsig=eval(self.ref_but.get()),
                    timeinseconds=eval(self.time_sec.get()),
                    figsize=figsize,
                )

            else:
                # Plot instanteous discharge rate
                openhdemg.plot_idr(
                    emgfile=self.parent.resdict,
                    munumber=int(mu_idr),
                    addrefsig=eval(self.ref_but.get()),
                    timeinseconds=eval(self.time_sec.get()),
                    figsize=figsize,
                )

        except ValueError:
            CTkMessagebox(title="Info", message="Enter valid motor unit number.", icon="info",
                          bg_color="#fdbc00", fg_color="LightBlue4", title_color="#000000",
                          button_color="#E5E4E2", button_text_color="#000000", button_hover_color="#1e52fe",
                          font=('Segoe UI',15, 'bold'), text_color="#FFFFFF")

        except KeyError:
            CTkMessagebox(title="Info", message="Enter valid motor unit number.", icon="info",
                          bg_color="#fdbc00", fg_color="LightBlue4", title_color="#000000",
                          button_color="#E5E4E2", button_text_color="#000000", button_hover_color="#1e52fe",
                          font=('Segoe UI',15, 'bold'), text_color="#FFFFFF")

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
                        emgfile=self.parent.resdict,
                        code=self.mat_code.get(),
                        orientation=int(self.mat_orientation.get()),
                        n_rows=list_rcs[0],
                        n_cols=list_rcs[1]
                    )

                except ValueError:
                    CTkMessagebox(title="Info", message="Number of specified rows and columns must match" +
                        "\nnumber of channels.", icon="info",
                          bg_color="#fdbc00", fg_color="LightBlue4", title_color="#000000",
                          button_color="#E5E4E2", button_text_color="#000000", button_hover_color="#1e52fe",
                          font=('Segoe UI',15, 'bold'), text_color="#FFFFFF")

                    return

            else:
                # Sort emg file
                sorted_file = openhdemg.sort_rawemg(
                    emgfile=self.parent.resdict,
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
                emgfile=self.parent.resdict,
                differential=diff_file,
                column=self.deriv_matrix.get(),
                addrefsig=eval(self.ref_but.get()),
                timeinseconds=eval(self.time_sec.get()),
                figsize=figsize,
            )
        except ValueError:
            CTkMessagebox(title="Info", message="Enter valid input parameters."
                + "\nPotenital error sources:"
                + "\n - Matrix Code"
                + "\n - Matrix Orientation"
                + "\n - Figure size arguments"
                + "\n - Rows, Columns arguments", icon="info",
                bg_color="#fdbc00", fg_color="LightBlue4", title_color="#000000",
                button_color="#E5E4E2", button_text_color="#000000", button_hover_color="#1e52fe",
                font=('Segoe UI',15, 'bold'), text_color="#FFFFFF")
        except UnboundLocalError:
            CTkMessagebox(title="Info", message="Enter valid Configuration and Matrix Column.", icon="info",
                          bg_color="#fdbc00", fg_color="LightBlue4", title_color="#000000",
                          button_color="#E5E4E2", button_text_color="#000000", button_hover_color="#1e52fe",
                          font=('Segoe UI',15, 'bold'), text_color="#FFFFFF")
        except KeyError:
            CTkMessagebox(title="Info", message="Enter valid Matrix Column.", icon="info",
                          bg_color="#fdbc00", fg_color="LightBlue4", title_color="#000000",
                          button_color="#E5E4E2", button_text_color="#000000", button_hover_color="#1e52fe",
                          font=('Segoe UI',15, 'bold'), text_color="#FFFFFF")

    def plot_muaps(self):
        """
        Instance methos to plot motor unit action potenital obtained from STA from one or
        multiple MUs. Except for DELSYS files, where the STA is not comupted.

        There is no limit to the number of MUs and STA files that can be overplotted.
        ``Remember: the different STAs should be matched`` with same number of electrode,
        processing (i.e., differential) and computed on the same timewindow.
        """
        try:
            # DELSYS requires different MUAPS plot
            if self.parent.resdict["SOURCE"] == "DELSYS":
                figsize = [int(i) for i in self.size_fig.get().split(",")]
                muaps_dict = openhdemg.extract_delsys_muaps(self.parent.resdict)
                openhdemg.plot_muaps(muaps_dict[int(self.muap_munum.get())], figsize=figsize)

            else:
                if self.mat_code.get() == "None":
                    # Get rows and columns and turn into list
                    list_rcs = [int(i) for i in self.matrix_rc.get().split(",")]

                    try:
                        # Sort emg file
                        sorted_file = openhdemg.sort_rawemg(
                            emgfile=self.parent.resdict,
                            code=self.mat_code.get(),
                            orientation=int(self.mat_orientation.get()),
                            n_rows=list_rcs[0],
                            n_cols=list_rcs[1]
                        )

                    except ValueError:
                        CTkMessagebox(title="Info", message="Number of specified rows and columns must match"
                          + "\nnumber of channels.", icon="info",
                          bg_color="#fdbc00", fg_color="LightBlue4", title_color="#000000",
                          button_color="#E5E4E2", button_text_color="#000000", button_hover_color="#1e52fe",
                          font=('Segoe UI',15, 'bold'), text_color="#FFFFFF")
                        return

                else:
                    # Sort emg file
                    sorted_file = openhdemg.sort_rawemg(
                        emgfile=self.parent.resdict,
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
                    emgfile=self.parent.resdict,
                    sorted_rawemg=diff_file,
                    firings="all",
                    timewindow=int(self.muap_time.get()),
                )

                # Create list of figsize
                figsize = [int(i) for i in self.size_fig.get().split(",")]

                # Plot MUAPS
                openhdemg.plot_muaps(sta_dict[int(self.muap_munum.get())], figsize=figsize)

        except ValueError:
            CTkMessagebox(title="Info", message="Enter valid input parameters."
                + "\nPotenital error sources:"
                + "\n - Matrix Code"
                + "\n - Matrix Orientation"
                + "\n - Figure size arguments"
                + "\n - Timewindow"
                + "\n - MU Number"
                + "\n - Rows, Columns arguments", icon="info",
                bg_color="#fdbc00", fg_color="LightBlue4", title_color="#000000",
                button_color="#E5E4E2", button_text_color="#000000", button_hover_color="#1e52fe",
                font=('Segoe UI',15, 'bold'), text_color="#FFFFFF")

        except UnboundLocalError:
            CTkMessagebox(title="Info", message="Enter valid Configuration.", icon="info",
                          bg_color="#fdbc00", fg_color="LightBlue4", title_color="#000000",
                          button_color="#E5E4E2", button_text_color="#000000", button_hover_color="#1e52fe",
                          font=('Segoe UI',15, 'bold'), text_color="#FFFFFF")
        except KeyError:
            CTkMessagebox(title="Info", message="Enter valid Matrix Column.", icon="info",
                          bg_color="#fdbc00", fg_color="LightBlue4", title_color="#000000",
                          button_color="#E5E4E2", button_text_color="#000000", button_hover_color="#1e52fe",
                          font=('Segoe UI',15, 'bold'), text_color="#FFFFFF")
            