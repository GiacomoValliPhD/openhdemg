"""Module containing the error message designs"""

import os
import traceback
from sys import platform

import customtkinter as ctk
from PIL import Image


class ErrorDialog:
    """
    A dialog window for displaying error messages and solutions to the user.

    This class creates a custom dialog window using customtkinter (ctk)
    components to show an error message and a potential solution. The dialog
    includes an information icon, labels for the error and solution, and is
    styled with specific foreground and background colors.

    Parameters
    ----------
    parent : tk.Tk or ctk.CTk
        The parent window to which this dialog is attached. It can be either a
        Tkinter root window or another customtkinter component.
    error : str
        The error message to be displayed in the dialog. This should describe
        what went wrong.
    solution : str
        A message providing a potential solution or workaround for the error
        described.

    Attributes
    ----------
    parent : tk.Tk or ctk.CTk
        The parent window of the dialog.
    head : ctk.CTkToplevel
        The top-level window component of the dialog.
    content_frame : ctk.CTkFrame
        A frame widget that holds the content of the dialog, including the
        error and solution messages.
    info_photo : ctk.CTkImage
        The photo image of the information icon displayed in the dialog.
    icon : ctk.CTkLabel
        A label widget used to display the information icon.
    icon_info : ctk.CTkLabel
        A label widget displaying the text "INFORMATION" below the icon.
    solution_label : ctk.CTkLabel
        A label widget used to display the solution message.
    error_label : ctk.CTkLabel
        A label widget used to display the error message.

    Methods
    -------
    __init__(self, parent, error, solution)
        Initializes the ErrorDialog with the parent window, error message, and
        solution message.

    Example
    -------
    >>> import tkinter as tk
    >>> import customtkinter as ctk
    >>> root = tk.Tk()
    >>> error = "This is a sample error message."
    >>> solution = "Try restarting the application."
    >>> ErrorDialog(root, error, solution)
    >>> root.mainloop()
    """

    def __init__(self, parent, error, solution):
        self.parent = parent
        self.head = ctk.CTkToplevel(fg_color="#FFBF00")
        self.head.title("Error Dialog")
        self.head.geometry("500x300")  # Adjust the size as needed

        # Set window icon
        head_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        iconpath = head_path + "/gui_files/Icon_transp.ico"
        self.head.iconbitmap(iconpath)
        if platform.startswith("win"):
            self.head.after(200, lambda: self.head.iconbitmap(iconpath))

        path = os.path.dirname(os.path.abspath(__file__))

        # Create a frame for the content with blue background, placed in the
        # middle.
        self.content_frame = ctk.CTkFrame(
            self.head,
            corner_radius=10,
            fg_color="LightBlue4",
            bg_color="#FFBF00",
        )
        self.content_frame.pack(padx=50, expand=True, fill="both")

        # Load an information icon and display it
        self.info_photo = ctk.CTkImage(
            light_image=Image.open(path + "/Error.png"),
            size=(50, 50),
        )
        self.icon = ctk.CTkLabel(
            self.content_frame,
            text="",
            image=self.info_photo,
            bg_color="LightBlue4",
        )
        self.icon.pack(pady=5)
        self.icon_info = ctk.CTkLabel(
            self.content_frame,
            text="INFORMATION",
            font=("Arial", 16, "bold"),
            text_color="#123456",
        )
        self.icon_info.pack(pady=5)

        # Error solution label (larger, bold), placed below the icon
        self.solution_label = ctk.CTkLabel(
            self.content_frame,
            text=solution,
            font=("Arial", 14, "bold"),
            wraplength=400,
            fg_color="LightBlue4",
        )
        self.solution_label.pack(pady=(10, 5))

        # Error traceback label (smaller)
        self.error_label = ctk.CTkLabel(
            self.content_frame,
            text=error,
            font=("Arial", 10),
            wraplength=400,
            fg_color="LightBlue4",
        )
        self.error_label.pack(pady=(5, 10), expand=True, fill="both")

        # Make window modal
        self.head.grab_set()  # Redirect all events to this window


def show_error_dialog(parent, error, solution):
    """
    Displays an ErrorDialog with a formatted error traceback and a solution
    message.

    This function takes an exception as input, formats its traceback, and then
    creates an ErrorDialog to display the formatted traceback along with a
    solution message.

    Parameters
    ----------
    parent : tk.Tk or ctk.CTk
        The parent window to which this dialog will be attached.
    error : Exception
        The exception object from which the error message will be derived.
    solution : str
        A message providing a potential solution or workaround for the error.

    Example
    -------
    >>> import tkinter as tk
    >>> import customtkinter as ctk
    >>> root = tk.Tk()
    >>> try:
    ...     # Some operation that raises an exception
    ...     raise ValueError("A sample error.")
    ... except Exception as e:
    ...     show_error_dialog(root, e, "Check the value and try again.")
    >>> root.mainloop()
    """
    if error is None:
        error_message = "".join(
            traceback.format_exception(type(error), value=error, tb=None)
        )
    else:
        error_message = "".join(
            traceback.format_exception(
                type(error),
                value=error,
                tb=error.__traceback__,
            )
        )

    ErrorDialog(parent, error_message, solution)
