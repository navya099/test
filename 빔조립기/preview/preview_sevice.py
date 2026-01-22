from controller.filefinder import FileLocator
from controller.path_resolver import PathResolver
from preview.previe_assembler import PreviewAssembler


class PreviewService:
    @staticmethod
    def build_from_install(install):
        names = []
        names.append(install.beam.name)
        names.extend(br.type for br in install.brackets)
        names.extend(col.name for col in install.columns)

        locator = FileLocator(PathResolver.BASE_PATH)

        fullpaths = []
        for name in names:
            path = locator.find(name)
            if path:
                fullpaths.append(path)
            else:
                raise FileNotFoundError(name)
        return PreviewAssembler.load_objects(fullpaths)
