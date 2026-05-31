import math
import matplotlib.pyplot as plt

class Vector2:
    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y

    def rotate(self, cosine_of_angle, sine_of_angle):
        x_new = cosine_of_angle * self.x - sine_of_angle * self.y
        y_new = sine_of_angle * self.x + cosine_of_angle * self.y
        self.x, self.y = x_new, y_new

    def __str__(self):
        return f"({self.x}, {self.y})"

class Vector3:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = x
        self.y = y
        self.z = z

    def __str__(self):
        return f"({self.x}, {self.y}, {self.z})"

class Transformation:
    def __init__(self, yaw, pitch, roll):
        self.yaw = yaw
        self.pitch = pitch
        self.roll = roll

    def rotate_vector(self, vector):
        """Rotate a 2D vector by the yaw angle."""
        cos_yaw = math.cos(self.yaw)
        sin_yaw = math.sin(self.yaw)
        vector.rotate(cos_yaw, sin_yaw)
        return vector

class Block:
    def __init__(self, station, position, direction, curve_radius, pitch):
        self.station = station
        self.Position = position
        self.Direction = direction
        self.CurveRadius = curve_radius
        self.Pitch = pitch

def calculate_block(data):

    # Initialize values
    a = 0.0
    c = BlockInterval
    h = 0.0
    Position = Vector3(0, 0, 0)
    Direction = Vector2(0, 1)
    
    for i in range(len(data['Blocks'])):
        block = data['Blocks'][i]
        a = 0.0
        h = 0.0
        current_sta = i * BlockInterval
        block.Position.x = Position.x
        block.Position.y = Position.y
        block.Position.z = Position.z
        
        if block.CurveRadius != 0.0 and block.Pitch != 0.0:
            d = BlockInterval
            p = block.Pitch
            r = block.CurveRadius
            s = d / math.sqrt(1.0 + p * p)
            h = s * p
            b = s / abs(r)
            c = math.sqrt(2.0 * r * r * (1.0 - math.cos(b)))
            a = 0.5 * math.copysign(1, r) * b

            direction_transformation = Transformation(-a, 0.0, 0.0)
            Direction = direction_transformation.rotate_vector(Direction)
        
        elif block.CurveRadius != 0.0:
            d = BlockInterval
            r = block.CurveRadius
            b = d / abs(r)
            c = math.sqrt(2.0 * r * r * (1.0 - math.cos(b)))
            a = 0.5 * math.copysign(1, r) * b

            direction_transformation = Transformation(-a, 0.0, 0.0)
            Direction = direction_transformation.rotate_vector(Direction)
        
        elif block.Pitch != 0.0:
            p = block.Pitch
            d = BlockInterval
            c = d / math.sqrt(1.0 + p * p)
            h = c * p

        # Calculate TrackYaw and TrackPitch
        TrackYaw = math.atan2(Direction.x, Direction.y)
        TrackPitch = math.atan(block.Pitch)

        # Update Position
        Position.x += Direction.x * c
        Position.y += h
        Position.z += Direction.y * c

        if a != 0.0:
            direction_transformation = Transformation(-a, 0.0, 0.0)
            Direction = direction_transformation.rotate_vector(Direction)

def read_blocks_from_file(filename):
    blocks = []
    with open(filename, 'r') as file:
        for line in file:
            if line.strip():  # Skip empty lines
                station = float(line.split(',')[0])
                curve_radius = float(line.split(',')[1])
                Position = Vector3(0, 0, 0)
                Direction = Vector2(0, 1)
                Pitch = 0
                blocks.append(Block(station, Position, Direction, curve_radius, Pitch))  # Assuming pitch is 0
    return blocks

# Variables
BlockInterval = 25

# File path
file_path = 'C:/temp/curve_info.txt'

# Initialize the data dictionary
data = {
    'Blocks': read_blocks_from_file(file_path)  # Provide the correct path to your text file
}

# Execute the function
calculate_block(data)

# Plotting the block positions using Matplotlib
fig = plt.figure()
ax = fig.add_subplot()

x_coords = [block.Position.x for block in data['Blocks']]
y_coords = [block.Position.y for block in data['Blocks']]
z_coords = [block.Position.z for block in data['Blocks']]

ax.plot(x_coords,z_coords, marker='o')

ax.set_xlabel('X Coordinate')
ax.set_ylabel('Y Coordinate')
ax.set_title('Block Positions')

plt.show()

while True:
    try:
        # Get the index from user input
        a = int(input('Enter block index (s): '))

        # Ensure index is within range
        if a >= len(data['Blocks']) or a < 0:
            print(f"Error: Index {a} is out of range. Please enter a valid index.")
            continue  # Skip to the next iteration of the loop

        # Print the position of the selected block
        block = data['Blocks'][a]
        print(f"Block {a}: station = {block.station}, Position = {block.Position}")
    
    except ValueError as e:
        print(f"Invalid input. Please enter a valid integer. Error: {e}")
    except IndexError as e:
        print(f"Error: {e}")

    


