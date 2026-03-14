class PoleUpdator:
    @staticmethod
    def update_all(poles):
        for i, pole in enumerate(poles):
            prev_pole = poles[i - 1] if i > 0 else None
            current_pole = pole
            next_pole = poles[i + 1] if i < len(poles) - 1 else None
            if next_pole:
                current_pole.next_pos = next_pole.pos
                current_pole.span = next_pole.pos - current_pole.pos
                current_pole.next_gauge = next_pole.gauge
                current_pole.next_structure = next_pole.structure
                current_pole.next_z = next_pole.z
                current_pole.next_base_type = next_pole.base_type
                current_pole.next_side = next_pole.side