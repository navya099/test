import os

class CSVManager:
    @staticmethod
    def copy_and_export_csv(
        open_filename: str,
        output_filename: str,
        ptype: str,
        source_directory: str,
        work_directory: str,
        offset: float = 0.0,
    ):
        open_file = os.path.join(source_directory, f'{open_filename}.csv')
        output_file = os.path.join(work_directory, f'{output_filename}.csv')

        new_lines = []

        with open(open_file, 'r', encoding='utf-8') as f:
            for line in f:
                if f'LoadTexture, {ptype}.png,' in line:
                    line = line.replace(
                        f'LoadTexture, {ptype}.png,',
                        f'LoadTexture, {output_filename}.png,'
                    )
                new_lines.append(line)

        new_lines.append(f'\nTranslateAll, {offset}, 0, 0\n')

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
