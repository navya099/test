import os
import shutil

direction = str(input("방향 입력: "))
# define the input file path
input_file_path = f"c:\\temp\\{direction}7000.csv"

# define the output directory
output_dir = "c:\\temp\\output"

# make sure the output directory exists
if not os.path.exists(output_dir):
    os.mkdir(output_dir)

# get the number of multiples of 2 to repeat from user input
num_repeats = int(input("END RAIDUS "))

# iterate over the multiples of 2
for i in range(1, num_repeats // 100 + 1):

    # construct the new file name by multiplying the multiple of 2 by 100
    new_file_name = f"{direction}{i*100}.csv"

    # read the contents of the input file
    with open(input_file_path, 'r') as input_file:
        contents = input_file.read()

    # find and replace the string "02.png" with the current multiple of 2
    new_contents = contents.replace("7000.png", f"{i*100}.png")

    # create the new file with the updated contents
    new_file_path = os.path.join(output_dir, new_file_name)
    with open(new_file_path, 'w') as new_file:
        new_file.write(new_contents)

    # print a message indicating success for each file created
    print(f"{new_file_name} created successfully")

print(f"Total {num_repeats//100} files created successfully")
