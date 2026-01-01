import os
import time
from dotenv import load_dotenv
from hyperliquid.info import Info
from hyperliquid.exchange import Exchange
from hyperliquid.utils import constants
from eth_account.account import Account

load_dotenv()

# ================= CONFIGURATION =================
# On garde 20 USDC pour être large
MONTANT_A_ACHETER_USDC = 20.0 
NOM_CRYPTO = "HYPE"
# =================================================

def run_bot():
    print(f"--- 🔧 Démarrage Robot HYPE (Correction Précision) ---")

    private_key = os.getenv("PRIVATE_KEY")
    public_address = os.getenv("PUBLIC_ADDRESS")

    if not private_key:
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
        mon_solde_usdc = 0.0
        for b in user_state.get("balances", []):
            if b["coin"] == "USDC":
                mon_solde_usdc = float(b["total"])
        
        print(f"💰 Ton solde : {mon_solde_usdc} USDC")

        if mon_solde_usdc < MONTANT_A_ACHETER_USDC:
            print(f"❌ Pas assez d'argent (Min {MONTANT_A_ACHETER_USDC}).")
            return

        # Prix
        all_mids = info.all_mids()
        prix_actuel = float(all_mids.get(NOM_CRYPTO, 25.0))
        
        # --- C'EST ICI QUE CA CHANGE ---
        # Le marché veut souvent 3 ou 4 décimales pour le prix du HYPE.
        # On tente avec 4 décimales pour être sûr d'être précis (le système coupera si trop long).
        # On arrondit la quantité à 2 décimales.
        
        prix_limite = round(prix_actuel * 1.05, 4)  # 4 chiffres après la virgule (Ex: 26.1234)
        quantite = round(MONTANT_A_ACHETER_USDC / prix_limite, 2) # 2 chiffres pour la quantité (Ex: 0.75)

        print(f"🏷️ Prix actuel : {prix_actuel}")
        print(f"🛒 Commande : Acheter {quantite} {NOM_CRYPTO} à max {prix_limite} $")

        # Ordre
        result = exchange.order(
            name=NOM_CRYPTO,
            is_buy=True,
            sz=quantite,
            limit_px=prix_limite,
            order_type={"limit": {"tif": "Ioc"}}
        )

        # Analyse
        status_type = result["response"]["type"]
        if status_type == "order":
            status_detail = result["response"]["data"]["statuses"][0]
            if "filled" in status_detail:
                print(f"🎉 VICTOIRE ! Achat confirmé : {status_detail}")
            else:
                print(f"⚠️ Rejeté : {status_detail}")
        else:
            print(f"❌ Erreur : {result}")

    except Exception as e:
        print(f"💥 Crash : {e}")

if __name__ == "__main__":
    run_bot()
