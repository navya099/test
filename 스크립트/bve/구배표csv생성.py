import os
import shutil

direction = str(input("방향 입력: "))
# define the input file path
input_file_path = f"c:\\temp\\{direction}3.csv"

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
    if i*0.5 == int(i*0.5):
        new_file_name = f"{direction}{int(i*0.5)}.csv"
    else:
        new_file_name = f"{direction}{i*0.5}.csv"

    # read the contents of the input file
    with open(input_file_path, 'r', encoding='utf8') as input_file:
        contents = input_file.read()

    # find and replace the string "상3.png" with the current multiple of 2
    if i*0.5 == int(i*0.5):
        new_contents = contents.replace(f"{direction}3.png", f"{direction}{int(i*0.5)}.png")
    else:
        new_contents = contents.replace(f"{direction}3.png", f"{direction}{i*0.5}.png")

    # create the new file with the updated contents
    new_file_path = os.path.join(output_dir, new_file_name)
    with open(new_file_path, 'w', encoding='utf8') as new_file:
        new_file.write(new_contents)

    # print a message indicating success for each file created
    print(f"{new_file_name} created successfully")

print(f"Total {num_repeats} files created successfully")
