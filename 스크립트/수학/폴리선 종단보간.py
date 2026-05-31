from shapely.geometry import LineString
from scipy.interpolate import interp1d
import numpy as np
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import filedialog
from tkinter import Scale, Entry, StringVar
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk

# Variables to store the current view
current_xlim = None
current_ylim = None

def is_valid_double(value):
    try:
        np.float64(value)
        return True
    except ValueError:
        return False

def update_graph(value=None):
    if value is not None and is_valid_double(value):
        scale.set(np.float64(value))  # Update the slider to the desired value

    target_x = np.float64(scale.get())  # Get the current value of the slider

    # Find the interpolated y coordinate for the given x coordinate
    target_y = f(target_x)

    # Update the graph
    ax.clear()
    ax.plot(x, y, label='Polyline')
    ax.scatter(target_x, target_y, color='red', label='Target Point')
    ax.legend()

    # Set the axis limits to the current view
    ax.set_xlim(current_xlim)
    ax.set_ylim(current_ylim)

    canvas.draw()

    # Output the target y value
    print("x coordinate:", target_x)
    print("y coordinate:", target_y)

def on_scroll(event):
    # Store the current view
    global current_xlim, current_ylim
    current_xlim = ax.get_xlim()
    current_ylim = ax.get_ylim()

def on_scroll_end(event):
    # Restore the current view after zooming
    ax.set_xlim(current_xlim)
    ax.set_ylim(current_ylim)
    canvas.draw()

# Create a tkinter application
root = tk.Tk()
 # Hide the main window

# Open the file selection dialog
file_path = filedialog.askopenfilename(title="Select a file", filetypes=[("Text files", "*.txt")])

if file_path:
    try:
        # Open the selected file and read the data
        with open(file_path, 'r') as file:
            lines = file.readlines()

        # Extract x and y coordinates from each line
        points = []
        for line in lines:
            x, y = map(float, line.strip().split())
            points.append((x, y))

        # Create a LineString from the points
        line = LineString(points)

        # Extract x and y coordinates
        x, y = line.xy

        # Create an interpolation function
        f = interp1d(x, y, kind='linear')

        # Create a slider
        scale_label = tk.Label(root, text="X coordinate:")
        scale_label.pack()
        scale = Scale(root, from_=min(x), to=max(x), orient='horizontal', resolution=0.01, command=update_graph)
        scale.pack()

        # Create a text entry field
        entry_label = tk.Label(root, text="or enter directly:")
        entry_label.pack()
        entry_value = StringVar()
        entry = Entry(root, textvariable=entry_value)
        entry.pack()
        entry.bind("<Return>", lambda event=None: update_graph(entry_value.get()))

        # Set the focus
        entry.focus_set()

        # Create the graph
        fig, ax = plt.subplots()
        ax.plot(x, y, label='Polyline')

        # Store the initial axis limits
        initial_xlim = ax.get_xlim()
        initial_ylim = ax.get_ylim()

        # Add the graph to the Tkinter window
        canvas = FigureCanvasTkAgg(fig, master=root)
        canvas.get_tk_widget().pack()
        canvas.draw()

        # Create a Matplotlib navigation toolbar
        toolbar = NavigationToolbar2Tk(canvas, root)
        toolbar.update()
        canvas.get_tk_widget().pack()

        # Connect scroll events to handle zoom and pan
        canvas.mpl_connect('scroll_event', on_scroll)
        canvas.mpl_connect('scroll_event', on_scroll_end)

        # Run the tkinter application
        root.mainloop()

    except FileNotFoundError:
        print("File not found.")
    except Exception as e:
        print("An error occurred while reading the file:", e)
else:
    print("File selection was canceled.")
