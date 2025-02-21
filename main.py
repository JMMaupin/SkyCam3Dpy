import threading
import time
import math
from GamePadXBox import controller_thread, get_controls
import eel_app

# Define the static parameters (sent once)
params = {
    "masts": [
        {"height": 5, "x": -5, "z": -3},
        {"height": 5, "x": 5, "z": -3},
        {"height": 5, "x": 5, "z": 3},
        {"height": 5, "x": -5, "z": 3}
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

# Start the controller thread
thread = threading.Thread(target=controller_thread)
thread.start()

# Start the eel application in a separate thread
eel_thread = threading.Thread(target=eel_app.start_eel, args=(params, dynParams))
eel_thread.start()

# Main loop for handling gamepad controls and updating dynamic parameters
while True:
    # Exemple de mise à jour : ici, on peut définir la position du spar en fonction du temps
    t = time.time()
    dynParams["sparPosition"] = {
        "x": 4 * math.sin(t),
        "y": 2.2 +  2* math.sin(t/2),  # altitude fixe par exemple
        "z": 2.5 * math.cos(t)
    }
    
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
        print(f"Main Loop - Axes: [{axes_str}], Buttons: [{buttons_str}], Hats: [{hats_str}] , Ropes: [{ropes_str}] ",  end='\r')
    
    # Petite pause pour ne pas saturer la boucle
    time.sleep(0.02)