import os
from dotenv import load_dotenv
from hyperliquid.info import Info
from hyperliquid.utils import constants

load_dotenv()

def run_bot():
    print(f"--- 🕵️‍♂️ Lancement du Scanner Spot ---")
    
    # On se connecte juste pour lire les infos (pas besoin de clé privée ici)
    info = Info(constants.MAINNET_API_URL, skip_ws=True)

    print("🔍 Téléchargement du catalogue Spot...")
    try:
        spot_meta = info.spot_meta()
        universe = spot_meta["universe"]
        
        print(f"📚 J'ai trouvé {len(universe)} jetons Spot disponibles :")
        print("---------------------------------------------------")
        
        # On affiche la liste des jetons trouvés
        for idx, token in enumerate(universe):
            nom = token.get("name", "Inconnu")
            index = token.get("index", idx)
            print(f"🔹 Index {index} : {nom}")
            
        print("---------------------------------------------------")

    except Exception as e:
        print(f"💥 Erreur lors du scan : {e}")

if __name__ == "__main__":
    run_bot()
