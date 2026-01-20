# core/parser/sketchup_csv.py

def parse_sketchup_csv_lines(lines):
    meshes = []

    cur_vertices = []
    cur_faces = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        parts = [p.strip() for p in line.split(",") if p.strip()]
        cmd = parts[0]

        if cmd == "CreateMeshBuilder":
            if cur_vertices:
                meshes.append((cur_vertices, cur_faces))
            cur_vertices = []
            cur_faces = []

        elif cmd == "AddVertex":
            cur_vertices.append(tuple(map(float, parts[1:4])))

        elif cmd == "AddFace":
            cur_faces.append(tuple(map(int, parts[1:4])))

    # 마지막 mesh
    if cur_vertices:
        meshes.append((cur_vertices, cur_faces))

    return meshes

