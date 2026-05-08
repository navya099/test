from infrastructure.dxftoimg import DXF2IMG


class ImageConverter:
    def __init__(self):
        self.converter = DXF2IMG()

    def convert_and_resize(self, dxf_path, output_path, size):
        output_paths = self.converter.convert_dxf2img([dxf_path], img_format='.png')
        if output_paths:
            self.converter.trim_and_resize_image(output_paths[0], output_path, size)
