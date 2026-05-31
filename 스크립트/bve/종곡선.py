import matplotlib.pyplot as plt
import numpy as np

def calculate_curve_station(radius, vip, start_grade, end_grade):
    # Convert grades from units per mile to percentage (1% = 10 units per mile)
    start_grade_percentage = start_grade / 1000.0
    end_grade_percentage = end_grade / 1000.0

    # Calculate curve length using the provided formula
    length = abs(radius * (start_grade_percentage - end_grade_percentage))

    # Calculate start and end stations
    start_station = vip - (length / 2)
    end_station = vip + (length / 2)

    return start_station, end_station, length

def calculate_curve_fl(radius, vip, start_grade, end_grade, vip_fl):
    # Convert grades from units per mile to percentage (1% = 10 units per mile)
    start_grade_percentage = start_grade / 1000.0
    end_grade_percentage = end_grade / 1000.0

    # Calculate curve length using the provided formula
    length = abs(radius * (start_grade_percentage - end_grade_percentage))

    # Calculate start and end FLs
    if start_grade > 0:
        start_fl = vip_fl - (start_grade_percentage * (length / 2))
    else:
        start_fl = vip_fl + abs((start_grade_percentage * (length / 2)))

    end_fl = vip_fl + (end_grade_percentage * (length / 2))

    return start_fl, end_fl

def calculate_ordinate(radius, vip, start_grade, end_grade, vip_fl):
    start_grade_percentage = start_grade / 1000.0
    end_grade_percentage = end_grade / 1000.0
    length = abs(radius * (start_grade_percentage - end_grade_percentage))
    
    grade_diff = end_grade_percentage - start_grade_percentage
    
    ordinate = grade_diff * (length/2)**2 / (2*length)
    vip_curve_fl = vip_fl + ordinate

    return vip_curve_fl

def generate_10_multiples(start, end):
    # Ensure start is less than or equal to end
    if start > end:
        start, end = end, start
    
    # Calculate the nearest lower multiple of 10 for start
    start_multiple = ((start - 1) // interval + 1) * interval

    # Generate a list of 10 multiples between start and end
    multiples_list = list(range(start_multiple, end + 1, interval))

    return multiples_list


# Example values
radius_input = input("종곡선 반경을 입력하세요 (기본값 9000): ")
radius_value = int(radius_input) if radius_input else 9000
vip_input = input("vip 측점을 입력하세요 (기본값 0): ")
vip_value = float(vip_input) if vip_input else 0
start_grade_input = input("시점 구배를  입력하세요 (기본값 0): ")
start_grade_value = float(start_grade_input) if start_grade_input else 0
end_grade_input = input("종점 구배를  입력하세요 (기본값 -35): ")
end_grade_value = float(end_grade_input) if end_grade_input else -35
vip_fl_input = input("계획고를  입력하세요 (기본값 0): ")
vip_fl_value = float(vip_fl_input) if vip_fl_input else 0



# Call the functions
start_station_result, end_station_result, curve_length = calculate_curve_station(radius_value, vip_value, start_grade_value, end_grade_value)
start_fl_result, end_fl_result = calculate_curve_fl(radius_value, vip_value, start_grade_value, end_grade_value, vip_fl_value)
vip_curve_fl = calculate_ordinate(radius_value, vip_value, start_grade_value, end_grade_value, vip_fl_value)

# Print the results
print(f"BVC: {start_station_result}")
print(f"EVC: {end_station_result}")
print(f"종곡선길이: {curve_length}")
print(f"BVC FL: {start_fl_result}")
print(f"EVC FL: {end_fl_result}")

# Plot the line connecting start FL, VIP value, and end FL
x_values_line = [start_station_result, vip_value, end_station_result]
y_values_line = [start_fl_result, vip_fl_value, end_fl_result]

plt.plot(x_values_line, y_values_line, marker='o', linestyle='-', color='green', label='Connecting Line')

# Draw the three-point parabola
# Create a range of x values
# Fit a quadratic curve to the three points
y_values_line2 = [start_fl_result, vip_curve_fl, end_fl_result]
coefficients = np.polyfit(x_values_line, y_values_line2, 2)
quadratic_function = np.poly1d(coefficients)

# Generate x values for the curve
x_parabola = np.linspace(start_station_result, end_station_result, 100)

# Calculate y values using the quadratic function
y_parabola = quadratic_function(x_parabola)

#포물선의 (x,y)좌표 출력
# Print the (x, y) coordinates of the parabolic curve
print("Parabolic Curve (x, y) Coordinates:")
for x, y in zip(x_parabola, y_parabola):
    print(f"{x:.2f} fl = {y:.2f}")

# Calculate the slope between two consecutive points
slope_values = np.gradient(y_parabola, x_parabola) * 1000

# Print the slope values between two consecutive points
print("\nSlope values between consecutive points:")
for x, slope in zip(x_parabola[1:], slope_values):
    print(f"{x:.2f},.pitch {slope:.4f}")

    
# Plot the fitted parabolic curve
plt.plot(x_parabola, y_parabola, label='Parabola', color='blue')

# Set labels and title
plt.xlabel('Station')
plt.ylabel('FL (Finish Line) Elevation')
plt.title('Vertical Curve with Connecting Line and Parabola')
plt.legend()

# Show the plot
plt.show()
