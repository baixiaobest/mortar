import numpy as np
import csv

NEAR_MIN = 50
NEAR_MAX = 500
MEDIUM_MIN = NEAR_MAX
MEDIUM_MAX = 2000
FAR_MIN = MEDIUM_MAX
FAR_MAX = 4050
TABLE_DISTANCE_STEP = 50
TABLE_ELEVATION_STEP = 5
TABLE_ELEVATION_MIN = -200
TABLE_ELEVATION_MAX = 200

NEAR_MUZZLE_VELOCITY = 70
MEDIUM_MUZZLE_VELOCITY = 140
FAR_MUZZLE_VELOCITY = 200

def calculate_distance_bearing(start_grid, target_grid):
    dgrid = target_grid - start_grid
    distance = np.linalg.norm(dgrid) * 100

    north = np.array([0, 1])
    dgrid_norm = dgrid / np.linalg.norm(dgrid)

    dot_prod = np.dot(dgrid_norm, north)
    cross_prod = np.cross(north, dgrid_norm)
    bearing = np.arccos(dot_prod) * 180 / np.pi

    if cross_prod > 0:
        bearing = 360 - bearing

    return distance, bearing

def load_table(name):
    table = []
    with open(name, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row in reader:
            table.append(np.array(row).astype(float))
    return np.array(table)

def load_range_tables():
    return load_table("range_table_near.csv"), load_table("range_table_medium.csv"), load_table("range_table_far.csv")

def calculate_elevation(distance, rel_elevation, table_near, table_medium, table_far):
    if (rel_elevation > TABLE_ELEVATION_MAX or rel_elevation < TABLE_ELEVATION_MIN):
        print("relative elevation out of range")
        return 0, "None"

    table = None
    min = 0
    ammo_type = "NONE"
    if distance >= NEAR_MIN and distance < NEAR_MAX:
        table = table_near
        min = NEAR_MIN
        ammo_type = "NEAR"
    elif distance >= MEDIUM_MIN and distance < MEDIUM_MAX:
        table = table_medium
        min = MEDIUM_MIN
        ammo_type = "MEDIUM"
    elif distance >= FAR_MIN and distance < FAR_MAX:
        table = table_far
        min = FAR_MIN
        ammo_type = "FAR"
    else:
        print("Distance out of range table range.")
        return 0, ammo_type

    row = int((distance - min) / TABLE_DISTANCE_STEP)
    col = int((rel_elevation - TABLE_ELEVATION_MIN) / TABLE_ELEVATION_STEP)
    left_top_elev = table[row, col]
    left_bottom_elev = table[row + 1, col]
    right_top_elev = table[row, col + 1]
    right_bottom_elev = table[row + 1, col + 1]
    alpha = (distance - (min + row * TABLE_DISTANCE_STEP)) / TABLE_DISTANCE_STEP
    beta = (rel_elevation - ( TABLE_ELEVATION_MIN + col * TABLE_ELEVATION_STEP)) / TABLE_ELEVATION_STEP

    left_interpolate = (1.0 - alpha) * left_top_elev + alpha * left_bottom_elev
    right_interpolate = (1.0 - alpha) * right_top_elev + alpha * right_bottom_elev
    interpolate = (1.0 - beta) * left_interpolate + beta * right_interpolate

    return interpolate, ammo_type

def calculate_elevation2(distance, rel_elevation, muzzle_velocity):
    return (np.rad2deg(np.arctan(((muzzle_velocity**2)+np.sqrt(((muzzle_velocity**4)-9.81*((9.81*muzzle_velocity**2)
            +(2*rel_elevation*muzzle_velocity**2)))))/(9.81*distance))) - np.rad2deg(np.arctan(((muzzle_velocity**2)
            +np.sqrt(((muzzle_velocity**4)-9.81*((9.81*muzzle_velocity**2)+(2*0*muzzle_velocity**2)))))/(9.81*distance))))\
            +(90-np.rad2deg(np.arctan(((muzzle_velocity**2)/(9.81*distance))-(((((muzzle_velocity**2)*((muzzle_velocity**2)
            -(19.62*0)))/(96.2361*(distance**2)))-1)**0.5))))

def get_ballistic_solution(distance, rel_elevation):
    solutions = []
    ammo_types = []
    muzzle_velocities = [NEAR_MUZZLE_VELOCITY, MEDIUM_MUZZLE_VELOCITY, FAR_MUZZLE_VELOCITY]
    types = ["NEAR", "MEDIUM", "FAR"]

    for idx, muzzle_veolocity in enumerate(muzzle_velocities):
        try:
            elevation = calculate_elevation2(distance, rel_elevation, muzzle_veolocity)
            if not np.isnan(elevation):
                solutions.append(elevation)
                ammo_types.append(types[idx])
        except:
            continue

    return solutions, ammo_types

def print_solution(bearing, distance, adjusted_distance, solutions, ammo_types):
    print("\nbearing: {0} distance: {1} adjusted_distance: {2}".format(bearing, distance, adjusted_distance))

    for idx, solution in enumerate(solutions):
        print("Solution {0}: ammo type: {1} elevation: {2}".format(idx, ammo_types[idx], solution))

if __name__=="__main__":
    start_grid = np.array([81.8, 214.4])
    target_grid = np.array([73, 216])
    rel_elevation = 198-95
    distance_override = None

    distance, bearing = calculate_distance_bearing(start_grid, target_grid)
    if distance_override is not None:
        distance = distance_override

    solutions, ammo_types = get_ballistic_solution(distance, rel_elevation)

    if len(solutions) == 0:
        print("No solution")
        exit()

    print_solution(bearing, distance, distance, solutions, ammo_types)

    adjusted_distance = distance
    user_input = ""
    while user_input != 'q':
        user_input = input("\nHow far off is the artillery? (positive if fall short, q to quit)")
        try:
            adjusted_distance = adjusted_distance + float(user_input)
            solutions, ammo_types = get_ballistic_solution(adjusted_distance, rel_elevation)

            if len(solutions) == 0:
                print("No solution")
            else:
                print_solution(bearing, distance, adjusted_distance, solutions, ammo_types)
        except:
            if user_input != 'q':
                print("invalid input")