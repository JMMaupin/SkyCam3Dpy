import eel
import time
import math

# Initialize eel with the directory containing the HTML files
eel.init('web')

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

# Optionnel : Expose a Python function to be callable from JavaScript if needed
@eel.expose
def update_spar_from_js(x, y, z):
    print("New spar position from JS:", x, y, z)

# Launch the eel application without blocking to allow updates
eel.start("index.html", size=(800, 600), block=False)

# Send the static parameters once before the loop
eel.upload_params(params)

# Boucle while True pour la mise à jour en temps réel de dynParams
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
    spar_width = params["spar"]["width"]
    spar_length = params["spar"]["length"]
    for mast in params["masts"]:
        # Calcul simple de distance entre la position du mast et la position du spar
        dx = mast["x"] - dynParams["sparPosition"]["x"]
        dz = mast["z"] - dynParams["sparPosition"]["z"]
        mast_top_y = mast["height"]  # en supposant que la partie haute du mât est à cette hauteur
        dy = dynParams["sparPosition"]["y"] - mast_top_y
        
        # Ajustement des calculs en fonction de la largeur et de la longueur du spar
        adjusted_dx = dx - spar_width / 2
        adjusted_dz = dz - spar_length / 2
        
        new_length = math.sqrt(adjusted_dx**2 + dy**2 + adjusted_dz**2)
        new_ropes.append({"length": round(new_length, 2)})
    
    dynParams["ropes"] = new_ropes

    # Envoi continu des nouveaux dynParams vers la partie JS
    eel.update_dynParams(dynParams)
    
    # Petite pause pour ne pas saturer la boucle
    eel.sleep(0.01)
