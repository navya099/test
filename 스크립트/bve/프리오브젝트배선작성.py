# Open input file with UTF-8 encoding
with open('C:/TEMP/STATION2.csv', encoding='utf-8') as infile:
     # Read lines from input file
     lines = infile.readlines()

# Get integer input from user
input_int = float(input("Enter an integer: "))

# Open output file with UTF-8 encoding
with open('C:/TEMP/STATION.ANIMATED', mode='w', encoding='utf-8') as outfile:
     # Initialize variables for object name and previous row values
     object_name = ''
     prev_col3, prev_col4 = 0, 0
     delete_lines = 0 # Counter for lines to be deleted
     # Loop through lines in input file
     for i, line in enumerate(lines):
         # Check if line is a comment
         if line.startswith(','):
             # Write comment to output file
             outfile.write(';'+line.strip()+ '\n')
         else:
             # Split line into columns
             cols = line.strip().split(',')
             # Check if object name has changed
             if object_name != cols[1]:
             
                 # Reset previous row values
                 prev_col3, prev_col4 = 0, 0
                 # Set new object name
                 object_name = cols[1]
             # Calculate rotation values
             try:
                 rotate_y = (float(lines[i+1].strip().split(',')[2]) - float(cols[2])) / 25
                 rotate_x = (float(lines[i+1].strip().split(',')[3]) - float(cols[3])) / 25
             except (ValueError, IndexError):
                 rotate_y = 0
                 rotate_x = 0

             # Write object state to output file if rotate_y is not 0
             outfile.write('[object]\n')
             outfile.write('states=25M레일.csv\n')
             outfile.write('position={},{},{}\n'.format(cols[2], cols[3], abs(float(input_int)-(float(cols[0])))))
             outfile.write('RotateYFunction={:.5f}\n'.format(rotate_y))
             outfile.write('RotateXFunction={:.5f}\n'.format(rotate_x))
             # Update previous row values
             prev_col3, prev_col4 = float(cols[2]), float(cols[3])

# Open the output file with UTF-8 encoding
with open('C:/TEMP/STATION.ANIMATED', mode='r+', encoding='utf-8') as outfile:
     # Read the contents of the file
     contents = outfile.read()
     # Replace the text
     contents = contents.replace(';,', ';')
     # Go back to the beginning of the file
     outfile.seek(0)
     # Write the updated contents back to the file
     outfile.write(contents)
     
with open('C:/TEMP/STATION.ANIMATED', mode='r+', encoding='utf-8') as outfile:
    # Delete 5 lines before comment
    lines = outfile.readlines()
    for i, line in enumerate(lines):
        if line.startswith(';'):
            start = max(0, i-5)
            end = i
            del lines[start:end]
    outfile.seek(0)
    outfile.writelines(lines)
    outfile.truncate()
