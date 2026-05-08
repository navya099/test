from infrastructure.csvmanager import CSVManager


class CurveOutputService:
    @staticmethod
    def copy_and_export(source_directory, work_directory, openfile_name, img_f_name, curvetype, radius):
        return CSVManager.copy_and_export_csv(
            openfile_name,
            img_f_name,
            source_directory,
            work_directory,
            replacements={
                f"LoadTexture, {curvetype}.png,": f"LoadTexture, {img_f_name}.png,",
                f"LoadTexture, R.png,": f"LoadTexture, {img_f_name}_{int(radius)}.png,"
            })
