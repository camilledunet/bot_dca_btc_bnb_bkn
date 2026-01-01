import os
import time
from dotenv import load_dotenv
from hyperliquid.info import Info
from hyperliquid.exchange import Exchange
from hyperliquid.utils import constants
from eth_account.account import Account

load_dotenv()

# ================= CONFIGURATION =================
# On tente avec 20 USDC pour être large (tu as 27 dispo)
MONTANT_A_ACHETER_USDC = 20.0 
NOM_CRYPTO = "HYPE"
# =================================================

def run_bot():
    print(f"--- 🔍 Démarrage du Robot Diagnostic pour {NOM_CRYPTO} ---")

    private_key = os.getenv("PRIVATE_KEY")
    public_address = os.getenv("PUBLIC_ADDRESS")

    if not private_key or not public_address:
        print("❌ ERREUR : Clés manquantes.")
        return

    try:
        # Connexion
        account = Account.from_key(private_key)
        info = Info(constants.MAINNET_API_URL, skip_ws=True)
        exchange = Exchange(account, constants.MAINNET_API_URL, account_address=public_address)
        print("✅ Connecté.")

        # Vérif Solde
        user_state = info.spot_user_state(public_address)
        balances = user_state.get("balances", [])
        mon_solde_usdc = 0.0
        for b in balances:
            if b["coin"] == "USDC":
                mon_solde_usdc = float(b["total"])
        
        print(f"💰 Ton solde : {mon_solde_usdc} USDC")

        if mon_solde_usdc < MONTANT_A_ACHETER_USDC:
            print(f"❌ Pas assez d'argent ! Tu as {mon_solde_usdc}, il faut {MONTANT_A_ACHETER_USDC}.")
            return

        # Prix
        all_mids = info.all_mids()
        prix_actuel = float(all_mids.get(NOM_CRYPTO, 25.0)) # Prix par défaut 25 si introuvable
        print(f"🏷️ Prix du HYPE estimé : {prix_actuel} $")

        # Calcul Quantité
        prix_limite = prix_actuel * 1.05 # +5% pour être sûr
        # On arrondit à 2 chiffres (ex: 0.45)
        quantite = round(MONTANT_A_ACHETER_USDC / prix_limite, 2)
        
        print(f"🛒 Tentative d'achat de {quantite} {NOM_CRYPTO} (Prix max: {round(prix_limite, 2)} $)")

        # Ordre
        result = exchange.order(
            name=NOM_CRYPTO,
            is_buy=True,
            sz=quantite,
            limit_px=prix_limite,
            order_type={"limit": {"tif": "Ioc"}}
        )

        # ANALYSE DU RÉSULTAT (La partie importante !)
        status_type = result["response"]["type"]
        
        if status_type == "order":
            # On regarde ce qu'il y a DANS la réponse
            status_detail = result["response"]["data"]["statuses"][0]
            
            if "filled" in status_detail:
                print(f"🎉 VRAIE VICTOIRE ! Ordre rempli complet : {status_detail}")
            else:
                # Si c'est "canceled" ou autre chose
                print(f"⚠️ PROBLÈME : L'ordre a été envoyé mais rejeté par Hyperliquid.")
                print(f"👉 Raison du rejet : {status_detail}")
        else:
            print(f"❌ Erreur technique bizarre : {result}")

    except Exception as e:
        print(f"💥 Crash : {e}")

if __name__ == "__main__":
    run_bot()
