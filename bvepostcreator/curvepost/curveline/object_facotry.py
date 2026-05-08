from model.curve.curve_object_data import CurveObjectDATA


class CurveObjectFactory:
    def __init__(self, offset):
        self.offset = offset

    def create(self, ip, curvetype, structure, station, object_index, img_f_name, object_folder, speed):
        return CurveObjectDATA(
            no=ip.IPNO,
            curvetype=curvetype,
            structure=structure,
            station=station,
            object_index=object_index,
            filename=img_f_name,
            object_path=object_folder,
            speed=speed,
            offset=(self.offset[structure][0], self.offset[structure][1]),
            rotation=0
        )
