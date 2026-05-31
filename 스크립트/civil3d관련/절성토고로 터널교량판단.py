import csv

bcount = 1
tcount = 1

with open('c:/temp/new.csv') as f:
    data = [float(line.strip()) for line in f]

b_groups = []
t_groups = []
current_group = []

for i in range(len(data)):
    if data[i] >= 12:
        current_group.append(data[i])
        if i == len(data) - 1 or data[i + 1] < 12:
            b_groups.append(('b{}'.format(bcount), current_group[0], current_group[-1]))
            current_group = []
            bcount += 1
    elif data[i] <= -12:
        current_group.append(data[i])
        if i == len(data) - 1 or data[i + 1] > -12:
            if min(current_group) <= -40:
                t_groups.append(('t{}'.format(tcount), current_group[0], current_group[-1]))
            current_group = []
            tcount += 1

# print the results
for group in b_groups:
    print(group[0], group[1], group[2])
for group in t_groups:
    print(group[0], group[1], group[2])