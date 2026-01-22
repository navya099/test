from controller.filefinder import FileLocator
from controller.path_resolver import PathResolver
from preview.previe_assembler import PreviewAssembler
from preview.preview_result import PreviewBuildResult


class PreviewService:
    @staticmethod
    def build_from_install(install):
        names = []
        names.append(install.beam.name)
        names.extend(br.type for br in install.brackets)
        names.extend(col.name for col in install.columns)

        locator = FileLocator(PathResolver.BASE_PATH)

        found_paths = []
        missing = []

        for name in names:
            path = locator.find(name)
            if path:
                found_paths.append(path)
            else:
                missing.append(name)

        objects = PreviewAssembler.load_objects(found_paths) if found_paths else []

        return PreviewBuildResult(objects=objects, missing=missing)
