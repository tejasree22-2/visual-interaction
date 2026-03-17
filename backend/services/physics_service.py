import math


def calculate_trajectory(angle, velocity, gravity):
    angle_rad = math.radians(angle)
    
    vx = velocity * math.cos(angle_rad)
    vy = velocity * math.sin(angle_rad)
    
    time_of_flight = 2 * vy / gravity
    
    max_height = (vy ** 2) / (2 * gravity)
    
    range_distance = velocity ** 2 * math.sin(2 * angle_rad) / gravity
    
    num_points = 100
    trajectory = []
    for i in range(num_points + 1):
        t = (i / num_points) * time_of_flight
        x = vx * t
        y = vy * t - 0.5 * gravity * t ** 2
        if y < 0:
            y = 0
        trajectory.append([round(x, 4), round(y, 4)])
    
    return {
        "trajectory": trajectory,
        "max_height": round(max_height, 4),
        "range": round(range_distance, 4),
        "time_of_flight": round(time_of_flight, 4)
    }


def get_physics_config():
    return {
        "default_gravity": 9.81,
        "angle_unit": "degrees",
        "velocity_unit": "m/s",
        "distance_unit": "meters"
    }
