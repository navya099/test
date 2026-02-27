
class FormData:
    def __init__(self, name: str):
        self.name = name
        from alignment_geometry.form import Form
        self.formdata: list[Form] = []