import eel

# Initialize eel with the directory containing the HTML files
eel.init('web')

# Optionnel : Expose a Python function to be callable from JavaScript if needed
@eel.expose
def update_spar_from_js(x, y, z):
    print("New spar position from JS:", x, y, z)

def start_eel(params, dynParams):
    # Launch the eel application without blocking to allow updates
    eel.start("index.html", size=(800, 600), block=False)

    # Send the static parameters once before the loop
    eel.upload_params(params)

    # Boucle while True pour la mise à jour en temps réel de dynParams
    while True:
        # Envoi continu des nouveaux dynParams vers la partie JS
        eel.update_dynParams(dynParams)
        
        # Petite pause pour ne pas saturer la boucle
        eel.sleep(0.01)