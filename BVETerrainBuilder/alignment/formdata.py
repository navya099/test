from .form import Form

class FormData:
    def __init__(self, name: str):
        self.name = name

        self.formdata: list[Form] = []