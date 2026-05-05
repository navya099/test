class FaceBuilder:
    @staticmethod
    def build_edges_from_faces(faces):
        edge_set = set()

        for a, b, c in faces:
            edge_set.add(tuple(sorted((a, b))))
            edge_set.add(tuple(sorted((b, c))))
            edge_set.add(tuple(sorted((c, a))))

        return list(edge_set)
