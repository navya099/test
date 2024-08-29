import numpy as np
import pyvista as pv
import os

def parse_txt_file(filename):
    # CSV 파일의 디렉토리 경로
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
                    # Finalize current mesh
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
    if len(vertices) == 0:
        raise ValueError("No vertices found. Check the input data.")
    
    if len(faces) == 0:
        raise ValueError("No faces found. Check the input data.")
    
    # Convert faces to the format expected by PyVista: [n0, v0, v1, ..., vn] where n0 is the number of vertices in the face
    flat_faces = []
    for face in faces:
        if len(face) > 0:
            flat_faces.append(len(face))  # number of vertices in the face
            flat_faces.extend(face)        # the indices of the vertices
    
    flat_faces = np.array(flat_faces, dtype=int)
    
    mesh = pv.PolyData(vertices, flat_faces)
    
    # Apply texture coordinates
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
            
            # 텍스쳐 파일의 절대 경로 생성
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

# txt 파일 파싱 및 메쉬 생성
filename = "c:/temp/DikeL.csv"  # CSV 파일 경로
meshes = parse_txt_file(filename)

try:
    visualize_meshes(meshes)
except ValueError as e:
    print(e)
