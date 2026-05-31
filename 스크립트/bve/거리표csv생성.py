import os
import shutil

# define the input file path
input_file_path = "c:\\temp\\02.csv"

# define the output directory
output_dir = "c:\\temp\\output"

# make sure the output directory exists
if not os.path.exists(output_dir):
    os.mkdir(output_dir)

# get the number of multiples of 2 to repeat from user input
num_repeats = int(input("Enter the number of multiples of 2 to repeat: "))

# iterate over the multiples of 2
for i in range(1, num_repeats+1):

    # construct the new file name by multiplying the multiple of 2 by 100
    new_file_name = f"{i*200}.csv"

    # read the contents of the input file
    with open(input_file_path, 'r') as input_file:
        contents = input_file.read()

    # find and replace the string "02.png" with the current multiple of 2
    new_contents = contents.replace("02.png", f"{i*2}.png")

    # create the new file with the updated contents
    new_file_path = os.path.join(output_dir, new_file_name)
    with open(new_file_path, 'w') as new_file:
        new_file.write(new_contents)

    # print a message indicating success for each file created
    print(f"{new_file_name} created successfully")

print(f"Total {num_repeats} files created successfully")
