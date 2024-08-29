import numpy as np
import pyvista as pv
import os
from PIL import Image

def convert_bmp_to_png(bmp_file):
    """Convert BMP file to PNG format and return the path to the new file."""
    if bmp_file.lower().endswith('.bmp'):
        png_file = bmp_file.rsplit('.', 1)[0] + '.png'
        with Image.open(bmp_file) as img:
            img.save(png_file, format='PNG')
        return png_file
    return bmp_file

def parse_txt_file(filename):
    """Parse a text file with mesh data and return a list of meshes."""
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
            if command == "CreateMeshBuilder":
                if current_vertices:
                    if current_faces:
                        meshes.append((np.array(current_vertices), current_faces, texture_coords, texture_file))
                    else:
                        print(f"Warning: No faces found for mesh starting at line {line_number}")
                    current_vertices = []
                    current_faces = []
                    texture_coords = {}
                    texture_file = None
            
            elif command == "AddVertex":
                vX, vY, vZ = map(float, parts[1:4])
                nX, nY, nZ = map(float, parts[4:7]) if len(parts) > 4 else (0, 0, 0)
                current_vertices.append([vX, vY, vZ])
            
            elif command == "AddFace":
                indices = list(map(int, parts[1:]))
                if indices:
                    current_faces.append(indices)
                else:
                    print(f"Warning: Empty face found at line {line_number}")
            
            elif command == "SetTextureCoordinates":
                vertex_index = int(parts[1])
                u, v = map(float, parts[2:])
                texture_coords[vertex_index] = [u, v]
            
            elif command == "LoadTexture":
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
    """Create a PyVista mesh from vertices, faces, and texture coordinates."""
    if len(vertices) == 0:
        raise ValueError("No vertices found. Check the input data.")
    
    if len(faces) == 0:
        raise ValueError("No faces found. Check the input data.")
    
    # Convert faces to the format expected by PyVista
    flat_faces = []
    for face in faces:
        if len(face) > 0:
            flat_faces.append(len(face))
            flat_faces.extend(face)
    
    flat_faces = np.array(flat_faces, dtype=int)
    
    mesh = pv.PolyData(vertices, flat_faces)
    
    # Apply texture coordinates
    if texture_coords:
        texture_coords_array = np.full((len(vertices), 2), [0, 0])  # Default UV coordinates
        for idx, uv in texture_coords.items():
            if 0 <= idx < len(vertices):
                texture_coords_array[idx] = uv
        
        mesh.point_data['Texture Coordinates'] = texture_coords_array
    
    return mesh

def visualize_meshes(meshes):
    """Visualize the list of meshes with optional textures."""
    plotter = pv.Plotter()
    
    for vertices, faces, texture_coords, texture_file in meshes:
        try:
            mesh = create_mesh(vertices, faces, texture_coords)
            
            if texture_file:
                base, ext = os.path.splitext(texture_file)
            
            if texture_file and os.path.isfile(texture_file):
                texture = pv.read_texture(texture_file)
                
                # Ensure texture is correctly loaded
                print(f"Loaded texture from file: {texture_file}")
                
                if 'Texture Coordinates' in mesh.point_data:
                    print("Texture coordinates found in mesh.")
                else:
                    print("No texture coordinates found in mesh. Ensure they are set correctly.")
                
                # Add the mesh with the texture
                plotter.add_mesh(mesh, texture=texture, show_edges=True)
            else:
                print('Texture file not found or not applicable. Not applying texture.')
                plotter.add_mesh(mesh, show_edges=True)
        except ValueError as e:
            print(f"Error creating mesh: {e}")
    
    plotter.show()

# Replace with your file path
filename = "c:/temp/BridgeL.csv"
meshes = parse_txt_file(filename)

try:
    visualize_meshes(meshes)
except ValueError as e:
    print(e)
