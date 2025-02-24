import threading
import time
import math
from GamePadXBox import controller_thread, get_controls
import eel_app

# Define the static parameters (sent once)
params = {
    "masts": [
        {"height": 8, "x": -6, "z": -4},
        {"height": 7, "x": 8, "z": -3},
        {"height": 5, "x": 10, "z": 2},
        {"height": 6, "x": -5, "z": 3}
    ],
    "spar": {
        "width": 0.5,
        "length": 0.3
    },
    "showAxes": False
}

# Initial dynamic parameters, which seront mises à jour en temps réel
dynParams = {
    "ropes": [
        {"length": 7},
        {"length": 7},
        {"length": 7},
        {"length": 7}
    ],
    # Vous pouvez ajouter ici la position du spar venant du calcul Python
    "sparPosition": {"x": 0, "y": 1, "z": 0}
}

cmdPosition = { "x": 0, "y": 0, "z": 0  }

# Start the controller thread
thread = threading.Thread(target=controller_thread)
thread.start()

# Start the eel application in a separate thread
eel_thread = threading.Thread(target=eel_app.start_eel, args=(params, dynParams))
eel_thread.start()

def limit_spar_position(cmdPosition, params):
    from shapely.geometry import Point, Polygon

    # Static variables for position memory and velocity (using class to store state)
    if not hasattr(limit_spar_position, 'last_pos'):
        limit_spar_position.last_pos = {'x': cmdPosition['x'], 'y': cmdPosition['y'], 'z': cmdPosition['z']}
        limit_spar_position.velocity = {'x': 0, 'y': 0, 'z': 0}

    # Physics parameters - ajustés pour plus de fluidité
    damping = 0.95  # Amortissement plus doux (0-1)
    spring = 0.15   # Force de rappel plus douce
    dt = 0.02      # Intervalle de temps

    # Create a polygon from the mast positions
    mast_positions = [(mast["x"], mast["z"]) for mast in params["masts"]]
    polygon = Polygon(mast_positions)

    # Calculate margins for different zones - marges réduites
    center = polygon.centroid
    min_dist = min(Point(center).distance(Point(x, z)) for x, z in mast_positions)
    margin = min_dist * 0.05  # Réduit à 5% au lieu de 10%
    
    # Create different safety zones for progressive limiting
    safe_zone = polygon.buffer(-margin, join_style=2, cap_style=3)
    danger_zone = polygon.buffer(-margin * 0.3, join_style=2, cap_style=3)  # Zone de danger plus large

    # Get point from command position
    point = Point(cmdPosition["x"], cmdPosition["z"])
    
    # Calculate target position with une transition plus progressive
    if danger_zone.contains(point):
        target_x = cmdPosition["x"]
        target_z = cmdPosition["z"]
    else:
        # Find nearest point on safe zone
        nearest_point = safe_zone.boundary.interpolate(safe_zone.boundary.project(point))
        
        # Calculate push-back force with smoother transition
        dist_to_safe = point.distance(nearest_point)
        # Force progressive avec une courbe plus douce
        force = math.pow(min(1.0, dist_to_safe / (margin * 2)), 2)
        
        # Apply progressive force
        target_x = cmdPosition["x"] * (1 - force) + nearest_point.x * force
        target_z = cmdPosition["z"] * (1 - force) + nearest_point.y * force

    # Height limitations with smooth transitions
    min_height = min(mast["height"] for mast in params["masts"]) - 0.3  # Marge réduite
    min_allowed = 0.2
    target_y = min(max(cmdPosition["y"], min_allowed), min_height)

    # Apply physics simulation for smooth movement
    for axis, target in [('x', target_x), ('y', target_y), ('z', target_z)]:
        # Calculate acceleration with smoother spring effect
        delta = target - limit_spar_position.last_pos[axis]
        acceleration = delta * spring * (1.0 - abs(delta) / (abs(delta) + 1.0))
        
        # Update velocity with acceleration and damping
        limit_spar_position.velocity[axis] = (
            limit_spar_position.velocity[axis] + acceleration * dt
        ) * damping
        
        # Update position
        limit_spar_position.last_pos[axis] += limit_spar_position.velocity[axis]

    # Return smoothed position
    return {
        'x': limit_spar_position.last_pos['x'],
        'y': limit_spar_position.last_pos['y'],
        'z': limit_spar_position.last_pos['z']
    }


# Main loop for handling gamepad controls and updating dynamic parameters
while True:
    # Exemple de mise à jour : ici, on peut définir la position du spar en fonction du temps
    t = time.time()


    if get_controls() != None:
        # ax 2 -> x  ax 3 -> z ax 1 -> y
        gain = 0.05
        deadzone = 0.1
        if abs(get_controls().axes[2]) > deadzone or abs(get_controls().axes[3]) > deadzone or abs(get_controls().axes[1]) > deadzone:
            cmdPosition['x'] += gain * get_controls().axes[2]
            cmdPosition['z'] += gain * get_controls().axes[3]
            cmdPosition['y'] -= gain * get_controls().axes[1]   
    else:
        cmdPosition = {
            "x": 6 * math.sin(t),
            "y": 2.2 +  2* math.sin(t/2),  # altitude fixe par exemple
            "z": 4 * math.cos(t)
        }

    # Limit the spar position within the defined bounds
    dynParams["sparPosition"] = limit_spar_position(cmdPosition, params)
    
    
    # Exemple de recalcul des longueurs de cordes en fonction de la nouvelle position du spar
    # (Vous devez ici réaliser votre propre calcul en fonction de vos besoins)
    new_ropes = []
    spar=type('spar',(),{})
    spar.width = params["spar"]["width"]
    spar.length = params["spar"]["length"]
    for mast in params["masts"]:
        # Calcul simple de distance entre la position du mast et la position du spar
        dx = mast["x"] - dynParams["sparPosition"]["x"]
        dz = mast["z"] - dynParams["sparPosition"]["z"]
        mast_top_y = mast["height"]  # en supposant que la partie haute du mât est à cette hauteur
        dy = dynParams["sparPosition"]["y"] - mast_top_y
        
        # Ajustement des calculs en fonction de la largeur et de la longueur du spar
        adjusted_dx = dx - spar.width / 2
        adjusted_dz = dz - spar.length / 2
        
        new_length = math.sqrt(adjusted_dx**2 + dy**2 + adjusted_dz**2)
        new_ropes.append({"length": round(new_length, 2)})
    
    dynParams["ropes"] = new_ropes
    ropes_str = ', '.join([f"{rope['length']:.2f}" for rope in new_ropes])

    # Exemple de récupération des contrôles de la manette
    ctrl = get_controls()
    if ctrl:
        # Access and update control values here
        axes_str = ', '.join([f"{value:.2f}" for value in ctrl.axes])
        buttons_str = ', '.join([str(int(pressed)) for pressed in ctrl.buttons])
        hats_str = ', '.join([f"({hat[0]}, {hat[1]})" for hat in ctrl.hats])
        print(f"Main Loop - Axes: [{axes_str}], Buttons: [{buttons_str}], Hats: [{hats_str}], Ropes: [{ropes_str}]", end='\r')
    
    # Petite pause pour ne pas saturer la boucle
    time.sleep(0.02)