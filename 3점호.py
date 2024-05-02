
import matplotlib.pyplot as plt
import numpy as np
import math

def draw_arc(direction, start_point, end_point, center_point):
    x_start, y_start = start_point
    x_end, y_end = end_point
    x_center, y_center = center_point

    start_angle = np.degrees(np.arctan2(y_start - y_center, x_start - x_center))
    end_angle = np.degrees(np.arctan2(y_end - y_center, x_end - x_center))

    

    # Calculate radius
    radius = np.sqrt((x_center - x_start)**2 + (y_center - y_start)**2)
   
    
    # Adjust start_angle and end_angle if necessary
    if start_angle < 0:
        start_angle +=360
    if end_angle < 0:
        end_angle +=360
    print('start_angle',start_angle)
    print('end_angle',end_angle)
    
       
    fii = end_angle - start_angle #시계방향
    fii2 = 360 - abs(end_angle - start_angle) #반시계방향
    
    print('fii',fii)
    print('fii2',fii2)
    
    num_angles = 100
    
    unit =  fii / (num_angles -1)
    unit2 =  fii2 / (num_angles -1)
    
    print('unit',unit)
    print('unit2',unit2)
    
    array = []
    if direction == 1: #시계방향
        if start_angle > end_angle:
            for i in range(num_angles):
                angle = start_angle + unit * i
                array.append(angle)

        else:
            for i in range(num_angles):
                angle = start_angle - unit2 * i
                array.append(angle)
                
        print('시계방향')
        color = 'red'
        
    else: #반시계방향 덧셈
        if start_angle > end_angle:
            for i in range(num_angles):
                angle = start_angle + unit2 * i
                array.append(angle)
        else:
            for i in range(num_angles):
                angle = start_angle + unit * i
                array.append(angle)
        print('반시계방향')
        color ='blue'
        
    theta = np.radians(array)
    
    # Calculate arc coordinates
    x_arc = x_center + radius * np.cos(theta)
    y_arc = y_center + radius * np.sin(theta)

    print("곡선반경 = ",radius)
    
    a = np.degrees(theta[-1] - theta[0])
    
    print("CL = ",abs(radius * math.radians(a)))
    return x_arc, y_arc , color

direction = 1
start_point = (188519.4946839318, 561137.8952718182)
end_point = (187993.30102521466, 561982.8184635111)
center_point = (190767.65376256465, 563124.2942139143)

x_arc, y_arc , color= draw_arc(direction, start_point, end_point, center_point)
plt.plot(x_arc, y_arc, label='Circular Arc',color= color)

# 그래프생성
# Add legend
plt.legend()

plt.title('a')
plt.xlabel('X-axis')
plt.ylabel('Y-axis')
plt.grid(True)
plt.show()
