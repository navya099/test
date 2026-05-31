import pandas as pd
import networkx as nx
import math
import time
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import ttk

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# Define Euclidean distance function
def euclidean_distance(lon1, lat1, lon2, lat2):
    """
    Calculate the Euclidean distance between two points given their latitude and longitude.
    """
    dx = lon2 - lon1
    dy = lat2 - lat1
    return math.sqrt(dx**2 + dy**2)

def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points
    on the Earth's surface using Haversine formula.
    """
    # Convert latitude and longitude from degrees to radians
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    # Radius of the Earth in kilometers
    R = 6371.0
    
    # Calculate the distance
    distance = R * c
    
    return distance

# Read data from Excel file
file_path = 'C:/Users/Administrator/Documents/korea_administrative_division_latitude_longitude.xlsx'
xl = pd.ExcelFile(file_path)

# Create an empty graph
G = nx.Graph()

# Dictionary to store nodes with attributes (position: (longitude, latitude))
nodes = {}

# Start time for performance measurement
start_time = time.time()

# Process data from each sheet
for sheet_name in xl.sheet_names:
    data = xl.parse(sheet_name)
    
    # Add nodes to the graph
    for index, row in data.iterrows():
        try:
            node_name = row[0]  # Assuming 'docity' column contains the node name
            longitude = row[3]  # Longitude
            latitude = row[4]  # Latitude
            
            # Add node to dictionary with attributes
            nodes[node_name] = {'pos': (longitude, latitude)}
            
            # Add node to graph
            G.add_node(node_name, pos=(longitude, latitude))  # Store position as node attribute
        
        except KeyError:
            print(f"Column names not found in sheet '{sheet_name}'. Check your data and column names.")
            continue

    # Add edges to the graph with weights (distance)
    for i in range(len(data)):
        row_i = data.iloc[i]
        node_i = row_i[0]  # Node name
        
        for j in range(i + 1, len(data)):
            row_j = data.iloc[j]
            node_j = row_j[0]  # Node name
            
            # Calculate Euclidean distance between nodes
            lon1, lat1 = nodes[node_i]['pos']
            lon2, lat2 = nodes[node_j]['pos']
            distance = haversine(lon1, lat1, lon2, lat2)
            
            # Add edge to the graph with weight
            G.add_edge(node_i, node_j, weight=distance)
        
        print(f'Calculating edges for node {i + 1}/{len(data)} in sheet {sheet_name}')

# Print elapsed time for creating graph
elapsed_time = time.time() - start_time
print(f"Elapsed time for creating graph: {elapsed_time:.2f} seconds")

# Initialize variables for selected nodes
start_node = None
end_node = None

# Example usage: Compute shortest path and distance
def compute_shortest_path():
    global start_node, end_node
    if start_node is None or end_node is None:
        return
    
    shortest_distance, shortest_path = nx.single_source_dijkstra(G, start_node, target=end_node)
    print(f"Shortest distance from {start_node} to {end_node}: {shortest_distance:.2f} km")
    print(f"Shortest path: {' -> '.join(shortest_path)}")
    print(shortest_path)
    # Clear previous plot
    plt.clf()
    
    # Plotting code
    plt.figure(figsize=(10, 8))
    
    # Draw nodes with labels
    for node, attrs in G.nodes(data=True):
        lon, lat = attrs['pos']
        plt.plot(lon, lat, 'bo', markersize=8)  # Blue circles for nodes
        plt.text(lon, lat, node, fontsize=8, ha='center', va='bottom')  # Display node name

    '''
    # Draw edges
    for u, v, attrs in G.edges(data=True):
        lon1, lat1 = nodes[u]['pos']
        lon2, lat2 = nodes[v]['pos']
        plt.plot([lon1, lon2], [lat1, lat2], 'k-', alpha=0.5)  # Gray lines for edges
    '''
    
    # Highlight shortest path
    for i in range(len(shortest_path) - 1):
        u = shortest_path[i]
        v = shortest_path[i + 1]
        lon1, lat1 = nodes[u]['pos']
        lon2, lat2 = nodes[v]['pos']
        plt.plot([lon1, lon2], [lat1, lat2], 'r-', linewidth=2)  # Red lines for shortest path
    
    plt.title(f"Shortest path from {start_node} to {end_node}")
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.grid(True)
    plt.axis('equal')  # Set equal aspect ratio
    plt.tight_layout()
    plt.show()

# Visualization using Matplotlib within Tkinter
root = tk.Tk()
root.title("Graph Visualization")

# Frame for Matplotlib plot
frame = ttk.Frame(root)
frame.pack(padx=20, pady=10)


# Combo box for selecting start node
start_label = ttk.Label(frame, text="Select start node:")
start_label.grid(row=0, column=0, padx=5, pady=5, sticky='w')

start_combo = ttk.Combobox(frame, state='readonly', width=30)
start_combo.grid(row=0, column=1, padx=5, pady=5)

# Combo box for selecting end node
end_label = ttk.Label(frame, text="Select end node:")
end_label.grid(row=1, column=0, padx=5, pady=5, sticky='w')

end_combo = ttk.Combobox(frame, state='readonly', width=30)
end_combo.grid(row=1, column=1, padx=5, pady=5)

# Function to update start and end nodes
def update_nodes(event):
    global start_node, end_node
    start_node = start_combo.get()
    end_node = end_combo.get()
    compute_shortest_path()

# Bind combo box selection to update function
start_combo.bind("<<ComboboxSelected>>", update_nodes)
end_combo.bind("<<ComboboxSelected>>", update_nodes)

# Populate combo boxes with node names
node_names = list(G.nodes())
start_combo['values'] = node_names
end_combo['values'] = node_names

# Start the Tkinter main loop
root.mainloop()
