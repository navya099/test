import numpy as np
import pyvista as pv
import os
import tkinter as tk
from tkinterdnd2 import TkinterDnD, DND_FILES
from tkinter import messagebox

def parse_txt_file(filename):
    base_dir = os.path.dirname(filename)
    
    with open(filename, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    meshes = []
    current_vertices = []
    current_faces = []
    texture_coords = {}
    texture_file = None
    
    for line_number, line in enumerate(lines, start=1):
        line = line.strip()
        if not line or line.startswith(';'):
            continue
        
        if ';' in line:
            line = line.split(';')[0].strip()
        
        parts = [part.strip() for part in line.split(',') if part.strip()]
        
        if not parts:
            continue
        
        command = parts[0]
        
        try:
            if command.lower() == "createmeshbuilder":
                if current_vertices:
                    if current_faces:
                        meshes.append((np.array(current_vertices), current_faces, texture_coords, texture_file))
                    else:
                        print(f"Warning: No faces found for mesh starting at line {line_number}")
                    current_vertices = []
                    current_faces = []
                    texture_coords = {}
                    texture_file = None
            
            elif command.lower() == "addvertex":
                vX, vY, vZ = map(float, parts[1:4])
                nX, nY, nZ = map(float, parts[4:7]) if len(parts) > 4 else (0, 0, 0)
                current_vertices.append([vX, vY, vZ])
            
            elif command.lower() == "addface":
                indices = list(map(int, parts[1:]))
                if indices:
                    current_faces.append(indices)
                else:
                    print(f"Warning: Empty face found at line {line_number}")
            
            elif command.lower() == "settexturecoordinates":
                vertex_index = int(parts[1])
                u, v = map(float, parts[2:])
                texture_coords[vertex_index] = [u, v]
            
            elif command.lower() == "loadtexture":
                texture_file = os.path.join(base_dir, parts[1])
        
        except ValueError as e:
            print(f"Error parsing line {line_number}: {line}")
            print(f"Details: {e}")
    
    if current_vertices:
        if current_faces:
            meshes.append((np.array(current_vertices), current_faces, texture_coords, texture_file))
        else:
            print(f"Warning: No faces found for final mesh starting at line {line_number}")

    return meshes

def create_mesh(vertices, faces, texture_coords):
    if len(vertices) == 0:
        raise ValueError("No vertices found. Check the input data.")
    
    if len(faces) == 0:
        raise ValueError("No faces found. Check the input data.")
    
    flat_faces = []
    for face in faces:
        if len(face) > 0:
            flat_faces.append(len(face))
            flat_faces.extend(face)
    
    flat_faces = np.array(flat_faces, dtype=int)
    
    mesh = pv.PolyData(vertices, flat_faces)
    
    if texture_coords:
        texture_coords = normalize_texture_coords(texture_coords)
        coords = np.zeros((len(vertices), 2))
        for idx, coord in texture_coords.items():
            coords[idx] = coord
        mesh.point_data['Texture Coordinates'] = coords
    
    return mesh

def visualize_meshes(meshes):
    plotter = pv.Plotter()
    
    for vertices, faces, texture_coords, texture_file in meshes:
        try:
            mesh = create_mesh(vertices, faces, texture_coords)
            '''
            if texture_file:
                absolute_texture_path = os.path.abspath(texture_file)
                print(f'현재 텍스쳐 파일: {absolute_texture_path}')
                
                if os.path.isfile(absolute_texture_path):
                    texture = pv.read_texture(absolute_texture_path)
                    plotter.add_mesh(mesh, style='surface', texture=texture, scalars=None, show_edges=True)
                else:
                    print('텍스쳐 파일을 찾을 수 없습니다. 텍스쳐를 로드하지 않습니다.')
                    plotter.add_mesh(mesh, style='surface', show_edges=True)
            else:
                print('텍스쳐 파일이 제공되지 않았습니다. 텍스쳐를 로드하지 않습니다.')
                plotter.add_mesh(mesh, style='surface', show_edges=True)
            '''
            plotter.add_mesh(mesh, style='surface', show_edges=True)
        except ValueError as e:
            print(f"Error creating mesh: {e}")
    
    plotter.show()

def normalize_texture_coords(texture_coords):
    if not texture_coords:
        return {}
    
    min_u = min(coord[0] for coord in texture_coords.values())
    max_u = max(coord[0] for coord in texture_coords.values())
    min_v = min(coord[1] for coord in texture_coords.values())
    max_v = max(coord[1] for coord in texture_coords.values())
    
    range_u = max_u - min_u
    range_v = max_v - min_v
    
    normalized_coords = {}
    for idx, coord in texture_coords.items():
        norm_u = (coord[0] - min_u) / range_u if range_u > 0 else 0
        norm_v = (coord[1] - min_v) / range_v if range_v > 0 else 0
        normalized_coords[idx] = [norm_u, norm_v]
    
    return normalized_coords

def on_drop(event):
    filename = event.data.strip()
    if filename and os.path.isfile(filename):
        try:
            meshes = parse_txt_file(filename)
            visualize_meshes(meshes)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
    else:
        messagebox.showerror("Error", "The dropped file is not valid or does not exist.")

def main():
    root = TkinterDnD.Tk()
    root.title("Mesh Visualizer")
    
    # Set up drag-and-drop
    root.drop_target_register(DND_FILES)
    root.dnd_bind('<<Drop>>', on_drop)
    
    label = tk.Label(root, text="Drag and drop your .txt file here", padx=20, pady=20)
    label.pack(expand=True, fill=tk.BOTH)
    
    root.geometry('400x200')
    root.mainloop()

if __name__ == "__main__":
    main()
