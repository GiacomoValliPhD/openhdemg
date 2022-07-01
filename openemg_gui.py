""" 
Threading: Operations and plot should be in background thread, independant from GUI -> seperate class??
Frontend: GUI with insertionable parameters. 
Backend: Plots, Excel, Analysis.

Input parameters: filepath, MVC, channels 

Questions: -How scalable should the plots be?
		   -What are other relevant parameters that should be costumizable 


"""

import tkinter as tk
import tkinter.messagebox
from tkinter import ttk, filedialog
from tkinter.tix import *
from threading import Thread, Lock
from tkinter import StringVar, Tk, N, S, W, E

from openhdemg.demo import *

