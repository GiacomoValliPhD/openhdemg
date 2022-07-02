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
		left = ttk.Frame(self, padding="10 10 12 12")
		left.grid(column=0, row=0, sticky=(N, S, W))
		left.columnconfigure(0, weight=1)
		left.columnconfigure(1, weight=1)
		left.columnconfigure(2, weight=1)

		# Left side GUI layout
		# Load file 
		load = ttk.Button(left, 
						  text="Load file",
						  command=self.get_file_input)
		load.grid(column=0, row=1, sticky=W)

		# Save File 
		save = ttk.Button(left,
						  text="Save file")
		save.grid(column=0, row=2, sticky=W)
		separator2 = ttk.Separator(left, orient="horizontal")
		separator2.grid(column=0, columnspan=3, row=3, sticky=(W,E), padx=5, pady=5)

		#View Motor Unit Firings
		firings = ttk.Button(left, 
							 text="View MU firing", 
							 command=self.in_gui_plotting)
		firings.grid(column=0, row=4, sticky=W)
		separator2 = ttk.Separator(left, orient="horizontal")
		separator2.grid(column=0, columnspan=3, row=5, sticky=(W,E), padx=5, pady=5)

		# Select Single Motor Unit
		mu_button = ttk.Button(left, 
							   text="View single MU") 
		mu_button.grid(column=1, row=4, sticky=(W,E))

		self.single_mu = StringVar()
		single_mu = (1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20)
		mu_entry = ttk.Combobox(left, width=5, textvariable=self.single_mu)
		mu_entry["values"] = single_mu
		mu_entry.grid(column=2, row=4, sticky=E)

		# Remove Motor Units
		remove_mus = ttk.Button(left,
							  text="Remove MUs")
		remove_mus.grid(column=0, row=6, sticky=W)

		# Edit Motor Units
		edit_mus = ttk.Button(left,
							  text="Edit MUs")
		edit_mus.grid(column=1, row=6, sticky=W)
		separator3 = ttk.Separator(left, orient="horizontal")
		separator3.grid(column=0, columnspan=3, row=7, sticky=(W,E), padx=5, pady=5)

		# Motor Unit properties
		mus = ttk.Button(left,
						 text="MU properties",
						 )
		mus.grid(column=0, row=8, sticky=W)
		separator4 = ttk.Separator(left, orient="horizontal")
		separator4.grid(column=0, columnspan=3, row=9, sticky=(W,E), padx=5, pady=5)

		# Plots
		plots = ttk.Button(left,
						   text="Plots")
		plots.grid(column=0, row=10, sticky=W)
		separator5 = ttk.Separator(left, orient="horizontal")
		separator5.grid(column=0, columnspan=3, row=11, sticky=(W,E), padx=5, pady=5)

		# Force Analysis
		force = ttk.Button(left, 
						   text="Analyse force", 
						   command = self.analyze_force)
		force.grid(column=0, row=12, sticky=W)

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

		file_path = filedialog.askdirectory()
		return file_path

	def analyze_force(self):

		force_window = ForceAnalysis(self)
		force_window.grab_set() # prevents main window interaction

	def in_gui_plotting(self):

		plot_mu_firing = InGUIPlotting.plot_mu_firing(self)


class InGUIPlotting(GUI):

	def __init__(self, parent):

		super().__init__(parent)

		self.file = file_path
		self.mu_number = mu_number
		self.channels = channels

	def plot_mu_firing(self):

		house_prices = np.random.normal(200000, 25000, 5000)
		fig = Figure(figsize=(3,3))
		a = fig.add_subplot(111)
		a.hist(house_prices)
		a.set_title("Test Plot")

		canvas = FigureCanvasTkAgg(fig, master=self.right)
		canvas_plot = canvas.get_tk_widget()
		canvas_plot.grid(column=0, row=1, rowspan=6, sticky=(W,E))
	

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


