""" 
This file contains the gui functionalities of openhdemg.
"""

import matplotlib
matplotlib.use('TkAgg')
import tkinter as tk
import tkinter.messagebox
import numpy as np
from tkinter import ttk, filedialog
from tkinter import StringVar, Tk, N, S, W, E, Canvas
from threading import Thread, Lock
from pandastable import Table, TableModel, config
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import openhdemg 


class GUI(Tk): 

	def __init__(self):

		super().__init__()

		# Set up GUI
		self.title("OpenHDemg")
		#self.iconbitmap()

		# Create left side framing for functionalities 
		self.left = ttk.Frame(self, padding="10 10 12 12")
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
						  text="File length (s):").grid(column=1, row=4, sticky=(W,E))

		# Save File 
		save = ttk.Button(self.left,
						  text="Save file")
		save.grid(column=0, row=5, sticky=W)
		separator2 = ttk.Separator(self.left, orient="horizontal")
		separator2.grid(column=0, columnspan=3, row=6, sticky=(W,E), padx=5, pady=5)

		# View Motor Unit Firings
		firings = ttk.Button(self.left, 
							 text="View MU firing", 
							 command=self.in_gui_plotting)
		firings.grid(column=0, row=7, sticky=W)
		separator2 = ttk.Separator(self.left, orient="horizontal")
		separator2.grid(column=0, columnspan=3, row=8, sticky=(W,E), padx=5, pady=5)

		# Remove Motor Units
		remove_mus = ttk.Button(self.left,
							  text="Remove MUs",
							  command=self.remove_mus)
		remove_mus.grid(column=0, row=9, sticky=W)

		# Edit Motor Units
		edit_mus = ttk.Button(self.left,
							  text="Edit MUs")
		edit_mus.grid(column=1, row=9, sticky=W)
		separator3 = ttk.Separator(self.left, orient="horizontal")
		separator3.grid(column=0, columnspan=3, row=10, sticky=(W,E), padx=5, pady=5)

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
		separator4.grid(column=0, columnspan=3, row=12, sticky=(W,E), padx=5, pady=5)

		# Force Analysis
		force = ttk.Button(self.left, 
						   text="Analyse force", 
						   command=self.analyze_force)
		force.grid(column=0, row=13, sticky=W)
		separator5 = ttk.Separator(self.left, orient="horizontal")
		separator5.grid(column=0, columnspan=3, row=14, sticky=(W,E), padx=5, pady=5)

		# Motor Unit properties
		mus = ttk.Button(self.left,
						 text="MU properties",
						 command=self.analyse_mus)
		mus.grid(column=0, row=15, sticky=W)
		separator6 = ttk.Separator(self.left, orient="horizontal")
		separator6.grid(column=0, columnspan=3, row=16, sticky=(W,E), padx=5, pady=5)

		# Plots
		plots = ttk.Button(self.left,
						   text="Plots")
		plots.grid(column=0, row=17, sticky=W)
		separator5 = ttk.Separator(self.left, orient="horizontal")
		separator5.grid(column=0, columnspan=3, row=18, sticky=(W,E), padx=5, pady=5)

		# Create left side framing for functionalities 
		self.right = ttk.Frame(self, padding="10 10 12 12")
		self.right.grid(column=1, row=0, sticky=(N, S, E))
		self.right.columnconfigure(0, weight=1)

		# Right side GUI layout

		# Canvas for Plots
		plot_canvas = Canvas(self.right, width=400, height=400)
		plot_canvas.grid(column=0, row=1, rowspan=6, sticky=(W,E))

	## Define functionalities for buttons used in GUI

	def get_file_input(self):

		file_path = filedialog.askopenfilename()
		self.file_path = file_path

		# Check filetype for processing
		if self.filetype == "OTB":
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

		if self.filetype == "REFSIG":
			self.resdict = refsig_from_otb(self.file_path)
			# Recondifgure labels
			n_channels.config(text="FSAMP")
			n_mus.config(text="")
			file_length.config(text="")
		
	def in_gui_plotting(self):

		InGUIPlotting.plot_mu_firing(self)

	def remove_mus(self):

		remove_window = EditMus(self, 
								self.file_path,
								50)
		remove_window.grab_set()
		#path = RemoveMus.remove_mu(self)
		#self.file_path = path

	def edit_refsig(self):

		refsig_window = RefSig(self, 
							   self.file_path)
		refsig_window.grab_set()

	def resize_file(self):

		pass

	def analyze_force(self):

		force_window = ForceAnalysis(self)
		force_window.grab_set() # prevents main window interaction

	def analyse_mus(self):

		mus_window = MuAnalysis(self, self.file_path)
		mus_window.grab_set()

	

	


class InGUIPlotting(GUI):

	def __init__(self, parent):

		super().__init__(parent)

		self.file = file_path
		self.mu_number = mu_number
		self.channels = channels

	def plot_mu_firing(self):

		#Test

		house_prices = np.random.normal(200000, 25000, 5000)
		fig = Figure(figsize=(5,5))
		a = fig.add_subplot(111)
		a.hist(house_prices)
		a.set_title("Test Plot")

		canvas = FigureCanvasTkAgg(fig, master=self.right)
		canvas_plot = canvas.get_tk_widget()
		canvas_plot.grid(column=0, row=1, rowspan=6, sticky=(W,E))


class EditMus(tk.Toplevel):

	def __init__(self, parent, file, number):

		super().__init__(parent)

		self.title("Motor Unit Removal Or Editing Window")
		self.geometry("400x400")
		self.file_path = file 
		self.n_channels = number 

		
		self.mu_to_remove = StringVar()
		removed_mu = ttk.Entry(self, width=10, textvariable=self.mu_to_remove)
		removed_mu.pack()

		remove = ttk.Button(self, 
							text="Remove MU", 
							command=self.remove_mu)
		remove.pack()

	def remove_mu(self):

		#update emgfile with removed MU

		del_emgfile = openhdemg.delete_mus(self.file_path,
										   self.mu_to_remove.get())
		print(del_emgfile)
		return del_emgfile

class RefSig(tk.Toplevel):

	def __init__(self, parent, file):

		super().__init__(parent)

		self.title("Reference signal editing window")
		head = tk.Frame(self, padding="10 10 12 12")
		head.grid(column=0, row=0, sticky=(S,W,E,N))

		self.file_path = file



class MuAnalysis(tk.Toplevel):

	def __init__(self, parent, file):

		super().__init__(parent)

		# Define gird and class attributes
		self.title("Motor Unit Properties Window")
		head = ttk.Frame(self, padding="10 10 12 12")
		head.grid(column=0, row=0, sticky=(N,S,W,E))

		self.file_path = file

		# MVIF Entry
		mvf = ttk.Label(head, text="Enter MVIF:").grid(column=0, row=0, sticky=(W))
		self.mvif_value = StringVar()
		enter_mvif = ttk.Entry(head, width=20, textvariable=self.mvif_value)
		enter_mvif.grid(column=1, row=0, sticky=(W,E))
		
		# Select MVIF on Plot
		select_mvif = ttk.Button(head,
								 text="Select MVIF")
		select_mvif.grid(column=0, row=1, sticky=W)

		# Compute MU re-/derecruitement threshold
		thresh = ttk.Button(head,
							text="Compute threshold",
							command=self.compute_mu_threshold)
		thresh.grid(column=0, row=2, sticky=W)

		self.ct_event = StringVar()
		ct_events_entry = ttk.Combobox(head,
								 width=10,
								 textvariable=self.ct_event)
		ct_events_entry["values"] = ("rt", "dert", "rt_dert")
		ct_events_entry["state"] = "readonly"
		ct_events_entry.grid(column=1, row=2, sticky=(W,E))
		self.ct_event.set("Event")

		self.ct_type = StringVar()
		ct_types_entry = ttk.Combobox(head,
								 width=10,
								 textvariable=self.ct_type)
		ct_types_entry["values"] = ("abs", "rel", "abs_rel")
		ct_types_entry["state"] = "readonly"
		ct_types_entry.grid(column=2, row=2, sticky=(W,E))
		self.ct_type.set("Type")

		# Compute motor unit discharge rate
		dr_rate = ttk.Button(head,
							 text="Compute discharge rate",
							 command=self.compute_mu_dr)
		dr_rate.grid(column=0, row=3, sticky=W)

		self.firings_rec = StringVar()
		firings_1 = ttk.Entry(head, 
							 width=20,
							 textvariable=self.firings_rec)
		firings_1.grid(column=1, row=3)
		self.firings_rec.set(4)

		self.firings_ste = StringVar()
		firings_2 = ttk.Entry(head, 
							 width=20,
							 textvariable=self.firings_ste)
		firings_2.grid(column=2, row=3)
		self.firings_ste.set(10)

		self.dr_event = StringVar()
		dr_events_entry = ttk.Combobox(head,
									   width=10,
									   textvariable=self.dr_event)
		dr_events_entry["values"] = ("rec", "derec", "rec_derec", "steady", "rec_derec_steady")
		dr_events_entry["state"] = "readonly"
		dr_events_entry.grid(column=3, row=3, sticky=E)
		self.dr_event.set("Event")

		# Compute basic motor unit properties
		basic = ttk.Button(head,
						   text="Basic MU properties",
						   command=self.basic_mus_properties)
		basic.grid(column=0, row=4, sticky=W)

		self.b_firings_rec = StringVar()
		b_firings_1 = ttk.Entry(head, 
							 width=20,
							 textvariable=self.b_firings_rec)
		b_firings_1.grid(column=1, row=4)
		self.b_firings_rec.set(4)

		self.b_firings_ste = StringVar()
		b_firings_2 = ttk.Entry(head, 
							 width=20,
							 textvariable=self.b_firings_ste)
		b_firings_2.grid(column=2, row=4)
		self.b_firings_ste.set(10)

	def compute_mu_threshold(self):

		self.mu_thresholds = openhdemg.compute_thresholds(self.file_path,
														  self.ct_event,
														  self.ct_type,
														  self.mvif_value)
		print(self.mu_thresholds)

	def compute_mu_dr(self):

		self.mus_dr = openhdemg.compute_dr(self.file_path,
										   self.firings_rec,
										   self.firings_ste,
										   self.dr_event)
		print(self.mus_dr)

	def basic_mus_properties(self):

		self.exportable_df = openhdemg.basic_mus_properties(self.file_path,
															self.b_firings_rec,
															self.b_firings_ste,
															self.mvif_value)
		print(self.exportable_df)


class ForceAnalysis(tk.Toplevel): 

	def __init__(self, parent):

		super().__init__(parent)

		self.title("Force Ananlysis Window")
		self.geometry("400x400")

		close_button = ttk.Button(self, 
				   				  text="Click me!",
				   				  command=self.destroy)
		close_button.pack()


if __name__ == "__main__":
	gui = GUI()
	gui.mainloop()


