""" 
This file contains the gui functionalities of openhdemg.
"""

import os
import matplotlib
matplotlib.use('TkAgg')
import tkinter as tk
import tkinter.messagebox
import pandas as pd
import numpy as np
from tkinter import ttk, filedialog
from tkinter import StringVar, Tk, N, S, W, E, Canvas
from threading import Thread, Lock
from pandastable import Table, TableModel, config
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import openhdemg 


class GUI(): 

	def __init__(self, root):

		# Set up GUI
		root.title("OpenHDemg")
		#self.iconbitmap()

		# Create left side framing for functionalities 
		self.left = ttk.Frame(root, padding="10 10 12 12")
		self.left.grid(column=0, row=0, sticky=(N, S, W))
		self.left.columnconfigure(0, weight=1)
		self.left.columnconfigure(1, weight=1)
		self.left.columnconfigure(2, weight=1)
		
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
		specs = ttk.Label(self.left,
						  text="File specifications:").grid(column=1, row=1, sticky=(W,E))

		n_channels = ttk.Label(self.left,
						  text="N Channels:").grid(column=1, row=2, sticky=(W,E))

		n_mus = ttk.Label(self.left, 
						  text="N° of MUs:").grid(column=1, row=3, sticky=(W,E))

		file_length = ttk.Label(self.left,
						  text="File length:").grid(column=1, row=4, sticky=(W,E))

		# Save File 
		save = ttk.Button(self.left,
						  text="Save file")
		save.grid(column=0, row=5, sticky=W)
		separator2 = ttk.Separator(self.left, orient="horizontal")
		separator2.grid(column=0, columnspan=3, row=6, sticky=(W,E))

		# View Motor Unit Firings
		firings = ttk.Button(self.left, 
							 text="View MU firing", 
							 command=self.in_gui_plotting)
		firings.grid(column=0, row=7, sticky=W)
		separator2 = ttk.Separator(self.left, orient="horizontal")
		separator2.grid(column=0, columnspan=3, row=8, sticky=(W,E))

		# Remove Motor Units
		remove_mus = ttk.Button(self.left,
							  text="Remove MUs",
							  command=self.remove_mus)
		remove_mus.grid(column=0, row=9, sticky=W)

		# Edit Motor Units
		edit_mus = ttk.Button(self.left,
							  text="Edit MUs",
							  command=self.editing_mus)
		edit_mus.grid(column=1, row=9, sticky=W)
		separator3 = ttk.Separator(self.left, orient="horizontal")
		separator3.grid(column=0, columnspan=3, row=10, sticky=(W,E))

		# Filter Reference Signal
		reference = ttk.Button(self.left, 
							   text="RefSig Editing",
							   command=self.edit_refsig)
		reference.grid(column=0, row=11, sticky=W)

		# Resize File
		resize = ttk.Button(self.left,
							text="Resize File",
							command=self.resize_file)
		resize.grid(column=1, row=11, sticky=(W,E))
		separator4 = ttk.Separator(self.left, orient="horizontal")
		separator4.grid(column=0, columnspan=3, row=12, sticky=(W,E))

		# Force Analysis
		force = ttk.Button(self.left, 
						   text="Analyse force", 
						   command=self.analyze_force)
		force.grid(column=0, row=13, sticky=W)
		separator5 = ttk.Separator(self.left, orient="horizontal")
		separator5.grid(column=0, columnspan=3, row=14, sticky=(W,E))

		# Motor Unit properties
		mus = ttk.Button(self.left,
						 text="MU properties",
						 command=self.mu_analysis)
		mus.grid(column=0, row=15, sticky=W)
		separator6 = ttk.Separator(self.left, orient="horizontal")
		separator6.grid(column=0, columnspan=3, row=16, sticky=(W,E))

		# Plots
		plots = ttk.Button(self.left,
						   text="Plots", command=self.plot_emg)
		plots.grid(column=0, row=17, sticky=W)
		separator5 = ttk.Separator(self.left, orient="horizontal")
		separator5.grid(column=0, columnspan=3, row=18, sticky=(W,E))

		# Export to Excel
		export = ttk.Button(self.left,
							text="Save Results", command=self.export_to_excel)
		export.grid(column=1, row=20, sticky=(W,E))


		# Create right side framing for functionalities 
		self.right = ttk.Frame(root, padding="10 10 12 12")
		self.right.grid(column=1, row=0, sticky=(N, S, E))
		self.right.columnconfigure(0, weight=1)

		# Right side GUI layout
		# Canvas for Plots
		plot_canvas = Canvas(self.right, width=1, height=1)
		plot_canvas.grid(column=0, row=1, rowspan=6, sticky=(W,E))

		for child in self.left.winfo_children():
			child.grid_configure(padx=5, pady=5)

	## Define functionalities for buttons used in GUI

	def get_file_input(self):

		file_path = filedialog.askopenfilename()
		self.file_path = file_path

		# Check filetype for processing
		if self.filetype.get() == "OTB":
			self.resdict = openhdemg.emg_from_otb(self.file_path)
		else:
			self.resdict = openhdemg.emg_from_demuse(self.file_path)
		
		# Add filespecs
		n_channels_value = ttk.Label(self.left,
						  text="").grid(column=2, row=2, sticky=(W,E))

		n_mus_value = ttk.Label(self.left, 
						  text=str(self.resdict["NUMBER_OF_MUS"])).grid(column=2, row=3, sticky=(W,E))

		file_length_value = ttk.Label(self.left,
						  text=str(self.resdict["EMG_LENGTH"])).grid(column=2, row=4, sticky=(W,E))

		if self.filetype.get() == "REFSIG":
			self.resdict = refsig_from_otb(self.file_path)
			# Recondifgure labels
			n_channels.config(text="FSAMP")
			n_mus.config(text="")
			file_length.config(text="")
 
	def export_to_excel(self):

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

#-----------------------------------------------------------------------------------------------
# Plotting inside of GUI 

	def in_gui_plotting(self):

		self.fig = openhdemg.plot_idr(self.resdict, [*range(0, int(self.resdict["NUMBER_OF_MUS"]))], showimmediately=False)
		canvas = FigureCanvasTkAgg(self.fig, master=self.right)
		canvas_plot = canvas.get_tk_widget()
		canvas_plot.grid(column=0, row=1, rowspan=6, sticky=(W,E))

#-----------------------------------------------------------------------------------------------
# Removal of single motor Units 

	def remove_mus(self):

		self.head = tk.Toplevel()
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

		remove = ttk.Button(self.head, 
							text="Remove MU", 
							command=self.remove)
		remove.grid(column=1, row=1, sticky=(W,E), padx=5, pady=5)


	def remove(self):

		self.resdict = openhdemg.delete_mus(self.resdict,
											int(self.mu_to_remove.get()))
		n_mus_value = ttk.Label(self.left, 
						  text=str(self.resdict["NUMBER_OF_MUS"])).grid(column=2, row=3, sticky=(W,E), padx=5, pady=5)

		self.mu_to_remove = StringVar()
		removed_mu_value = [*range(0, self.resdict["NUMBER_OF_MUS"])]
		removed_mu = ttk.Combobox(self.head, width=10, textvariable=self.mu_to_remove)
		removed_mu["values"] = removed_mu_value
		removed_mu["state"] = "readonly"
		removed_mu.grid(column=0, row=0, sticky=(W,E), padx=5, pady=5)

		# Check whether attribute fig is already present and update
		if hasattr(self, "fig"):
			self.in_gui_plotting()

#-----------------------------------------------------------------------------------------------
# Editing of single motor Units 

	def editing_mus(self):

		self.head = tk.Toplevel()
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

		single_mu = ttk.Button(self.head, 
							  text="View single MU", 
							  command=self.view_single_mu)
		single_mu.grid(column=1, row=1, sticky=(W,E), padx=5, pady=5)
		
	def view_single_mu(self):

		fig = openhdemg.plot_idr(self.resdict, 
								 int(self.mu_to_edit.get()),
								 showimmediately=False)

		canvas = FigureCanvasTkAgg(fig, master=self.head)
		canvas_plot = canvas.get_tk_widget()
		canvas_plot.grid(column=1, row=2, sticky=(W,E))


#-----------------------------------------------------------------------------------------------
# Editing of Reference EMG Signal 

	def edit_refsig(self):

		self.head = tk.Toplevel()
		self.head.title("Reference Signal Eiditing Window")
		self.head.grab_set()

		# Filter EMG reference signal
		ttk.Label(self.head, text="Filter Order").grid(column=1, row=0, sticky=(W,E))
		ttk.Label(self.head, text="Cutoff Freq").grid(column=2, row=0, sticky=(W,E))

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

		ttk.Label(self.head, text="Filter Order").grid(column=1, row=3, sticky=(W,E))
		ttk.Label(self.head, text="Automatic Offset").grid(column=2, row=3, sticky=(W,E))

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

		for child in self.head.winfo_children():
			child.grid_configure(padx=5, pady=5)

	### Define functions for Refsig editing

	def filter_refsig(self):

		##### is it here always the inputted EMG file or a seperate file that needs to be loaded??
		
		self.filtrefsig = openhdemg.filter_refsig(self.resdict,
												  int(self.filter_order.get()),
												  int(self.cutoff_freq.get()))
		print(self.filtrefsig)

	def remove_offset(self):

		#### auto eval variable coding could be improved.

		self.offs_emgfile = openhdemg.remove_offset(self.resdict, 
													int(self.offsetval.get()),
													int(self.auto_eval.get()))
		print(self.offs_emgfile)

#-----------------------------------------------------------------------------------------------
# Resize EMG File

	def resize_file(self):

		self.head = tk.Toplevel()
		self.head.title("Resize EMG File Window")
		self.head.grab_set()

		# Enter start point of resizing area
		ttk.Label(self.head,
				  text="Enter Startpoint:").grid(column=0, row=0, sticky=W, padx=5, pady=5)

		self.start_area = StringVar()
		start = ttk.Entry(self.head, 
							 width=10,
							 textvariable=self.start_area)
		start.grid(column=1, row=0,padx=5, pady=5)
		self.start_area.set(120)

		# Enter end point of resizing area
		ttk.Label(self.head,
				  text="Enter Endpoint:").grid(column=0, row=1, sticky=W, padx=5, pady=5)

		self.end_area = StringVar()
		end = ttk.Entry(self.head, 
							 width=10,
							 textvariable=self.end_area)
		end.grid(column=1, row=1, padx=5, pady=5)
		self.end_area.set(2560)

		# Resize Button
		resize = ttk.Button(self.head,
							text="Resize File", command=self.resize_emgfile)
		resize.grid(column=1, row=2, sticky=(W,E), padx=5, pady=5)

	### Define function for resizing

	def resize_emgfile(self):

		self.rs_emgfile, start_, end_ = openhdemg.resize_emgfile(self.resdict, 
																 [int(self.start_area.get()),
																 int(self.end_area.get())])
		# Define dictionary for pandas
		mvf_dic = {"Length": [self.rs_emgfile["EMG_LENGTH"]],
				   "Start": [start_], 
				   "End": [end_]}
		df = pd.DataFrame(data=mvf_dic)
		
		if hasattr(self, "tv1"):
			self.display_results(df)
		else:
			self.call_treeview(df)

#-----------------------------------------------------------------------------------------------
# Analysis of Force

	def analyze_force(self):

		self.head = tk.Toplevel()
		self.head.title("Force Analysis Window")
		
		# Get MVIF
		get_mvf = ttk.Button(self.head,
							 text="Get MVIF", command=self.get_mvif)
		get_mvf.grid(column=0, row=1, sticky=(W,E), padx=5, pady=5)

		# Get RFD
		separator1 = ttk.Separator(self.head, orient="horizontal")
		separator1.grid(column=0, columnspan=3, row=2, sticky=(W,E), padx=5, pady=5)

		ttk.Label(self.head, text="RFD miliseconds").grid(column=1, row=3, sticky=(W,E), padx=5, pady=5)
		ttk.Label(self.head, text="Startpoint").grid(column=2, row=3, sticky=(W,E), padx=5, pady=5)

		get_rfd =  ttk.Button(self.head,
							 text="Get RFD", command=self.get_rfd)
		get_rfd.grid(column=0, row=4, sticky=(W,E), padx=5, pady=5)

		self.rfdms = StringVar()
		milisecond = ttk.Entry(self.head,
							   width=10, textvariable=self.rfdms)
		milisecond.grid(column=1, row=4, sticky=(W,E), padx=5, pady=5)
		self.rfdms.set(250)

		# Define list for RFD computation
		self.ms_list = [50, 100, 150, 200]
		self.ms_list.append(int(self.rfdms.get()))

		self.startpoint = StringVar()
		point = ttk.Entry(self.head,
							   width=10, textvariable=self.startpoint)
		point.grid(column=2, row=4, sticky=(W,E), padx=5, pady=5)
		
	### Define functions for force analysis

	def get_mvif(self):

		self.mvif = openhdemg.get_mvif(self.resdict)
		# Define dictionary for pandas
		mvf_dic = {"MVIF": [self.mvif]}
		self.mvif_df = pd.DataFrame(data=mvf_dic)
		
		if hasattr(self, "tv1"):
			self.display_results(self.mvif_df)
		else:
			self.call_treeview(self.mvif_df)

	def get_rfd(self):

		self.rfd = openhdemg.compute_rfd(self.resdict, 
										 self.ms_list,
										 self.startpoint.get())
		if hasattr(self, "tv1"):
			self.display_results(self.rfd)
		else:
			self.call_treeview(self.rfd)

#-----------------------------------------------------------------------------------------------
# Analysis of motor unit properties 

	def mu_analysis(self):

		self.head = tk.Toplevel()
		self.head.title("Motor Unit Properties Window")
		
		# MVIF Entry
		mvf = ttk.Label(self.head, text="Enter MVIF:").grid(column=0, row=0, sticky=(W))
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
		ttk.Label(self.head, text="Firings Steady").grid(column=2, row=5, sticky=(W,E))

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
		ttk.Label(self.head, text="Firings Steady").grid(column=2, row=8, sticky=(W,E))

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

		try:
			self.mu_thresholds = openhdemg.compute_thresholds(self.resdict,
															  self.ct_event.get(),
															  self.ct_type.get(),
															  int(self.mvif_value.get()))
			if hasattr(self,"tv1"):
				self.display_results(self.mu_thresholds)
			else:
				self.call_treeview(self.mu_thresholds)

		except AttributeError:
			tk.messagebox.showerror("Information", "Load file prior to computation.")

		except ValueError: 
			tk.messagebox.showerror("Information", "Enter valid MVIF.")

		except AssertionError: 
			tk.messagebox.showerror("Information", "Specify Event and/or Type.")

	def compute_mu_dr(self):

		try:
			self.mus_dr = openhdemg.compute_dr(self.resdict,
											   int(self.firings_rec.get()),
											   int(self.firings_ste.get()),
											   self.dr_event.get())
			if hasattr(self, "tv1"):
				self.display_results(self.mus_dr)
			else:
				self.call_treeview(self.mus_dr)

		except AttributeError: 
			tk.messagebox.showerror("Information", "Load file prior to computation.")

		except ValueError: 
			tk.messagebox.showerror("Information", "Enter valid Firings value.")

		except AssertionError: 
			tk.messagebox.showerror("Information", "Specify Event and/or Type.")

	def basic_mus_properties(self):

		try:
			self.exportable_df = openhdemg.basic_mus_properties(self.resdict,
																int(self.b_firings_rec.get()),
																int(self.b_firings_ste.get()),
																int(self.mvif_value.get()))
			if hasattr(self, "tv1"):
				self.display_results(self.exportable_df)
			else:
				self.call_treeview(self.exportable_df)

		except AttributeError: 
			tk.messagebox.showerror("Information", "Load file prior to computation.")

		except ValueError: 
			tk.messagebox.showerror("Information", "Enter valid MVIF.")

		except AssertionError: 
			tk.messagebox.showerror("Information", "Specify Event and/or Type.")
	
#-----------------------------------------------------------------------------------------------
# Plot EMG

	def plot_emg(self):

		openhdemg.plot_emgsig(self.resdict, 4) # Add channel number
		openhdemg.plot_refsig(self.resdict)
		openhdemg.plot_mupulses(self.resdict)
		openhdemg.plot_ipts(self.resdict, 2) # Add MU number selection
		openhdemg.plot_idr(self.resdict, 2) # Add MU number selection

#-----------------------------------------------------------------------------------------------
# Analysis results display

	def call_treeview(self, input_df):

		self.head = tk.Toplevel()
		self.head.geometry("400x400")
		self.head.title("Result Window")
				
		# Set treeview frame
		twframe = ttk.LabelFrame(self.head, text="Result Output")
		twframe.place(relheight=1, relwidth=1)

		# Create treeview
		self.tv1 = ttk.Treeview(twframe)
		self.tv1.place(relheight=1, relwidth=1)

		# Add scrollbars
		treescrolly = tk.Scrollbar(twframe, orient="vertical", command=self.tv1.yview)
		treescrollx = tk.Scrollbar(twframe, orient="horizontal", command=self.tv1.xview)

		# Assign scrollbars to tv1
		self.tv1.config(xscrollcommand=treescrollx.set, yscrollcommand=treescrolly.set)
		treescrolly.pack(side="right", fill="y")
		treescrollx.pack(side="bottom", fill="x")

		# Display Results
		self.display_results(input_df)


	def display_results(self, input_df):
			
			df = input_df
			
			self.clear_tw()
			self.tv1["column"] = list(df.columns)
			self.tv1["show"] = "headings"

			for column in self.tv1["columns"]:
				self.tv1.heading(column, text=column)

			df_rows = df.to_numpy().tolist()
			for row in df_rows:
				self.tv1.insert("", "end", values=row)

			return None

	def clear_tw(self):

		self.tv1.delete(*self.tv1.get_children())

#-----------------------------------------------------------------------------------------------


if __name__ == "__main__":
	root = Tk()
	GUI(root)
	root.mainloop()


