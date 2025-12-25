class CSVManager:
    def __init__(self):
        pass

    def copy_and_export_csv(open_filename='km표-토공용', output_filename='13460', ptype='km표', source_directory='',
                            work_directory='', offset=0.0):
        # Define the input and output file paths
        open_file = source_directory + open_filename + '.csv'
        output_file = work_directory + output_filename + '.csv'

        # List to store modified lines
        new_lines = []

        # Open the input file for reading
        with open(open_file, 'r', encoding='utf-8') as file:
            # Iterate over each line in the input file
            for line in file:
                # Replace 'LoadTexture, SP.png,' with 'LoadTexture, output_filename.png,' if found
                if f'LoadTexture, {ptype}.png,' in line:
                    line = line.replace(f'LoadTexture, {ptype}.png,', f'LoadTexture, {output_filename}.png,')

                # Append the modified line to the new_lines list
                new_lines.append(line)
        new_lines.append(f'\nTranslateAll, {offset}, 0, 0\n')

        # Open the output file for writing the modified lines
        with open(output_file, 'w', encoding='utf-8') as file:
            # Write the modified lines to the output file
            file.writelines(new_lines)