import pandas as pd

# read input csv file
df = pd.read_csv('c:/temp/temp.csv', header=None, names=['station', 'elevation'])

# initialize variables for bridge and tunnel sections
bridge_start, tunnel_start = None, None

# create a list to hold the extracted data
extracted_data = []

# loop through the rows in the dataframe
for index, row in df.iterrows():

    # check for tunnel section
    if row['elevation'] < -10 and tunnel_start is None:
        tunnel_start = row['station']

    elif row['elevation'] >= -10 and tunnel_start is not None:
        # check if continuous section is long enough to be a tunnel
        if row['station'] - tunnel_start >= 200:
            extracted_data.append(['Tunnel', tunnel_start, row['station']])
        tunnel_start = None

    # check for bridge section
    if row['elevation'] > 15 and bridge_start is None:
        bridge_start = row['station']

    elif row['elevation'] <= 15 and bridge_start is not None:
        # check if continuous section is long enough to be a bridge
        if row['station'] - bridge_start >= 100:
            extracted_data.append(['Bridge', bridge_start, row['station']])
        bridge_start = None

# write the extracted data to a new csv file
pd.DataFrame(extracted_data, columns=['Type', 'Start', 'End']).to_csv('c:/temp/out.csv', index=False)
