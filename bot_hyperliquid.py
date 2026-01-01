import os
import time
from dotenv import load_dotenv
from hyperliquid.info import Info
from hyperliquid.exchange import Exchange
from hyperliquid.utils import constants
from eth_account.account import Account

# 1. On charge les clés secrètes
load_dotenv()

# ================= CONFIGURATION =================
# C'est ici que tu peux changer le montant !
# Mets au moins 5 USDC pour être sûr.
MONTANT_A_ACHETER_USDC = 5.0 
NOM_CRYPTO = "HYPE"
# =================================================

def run_bot():
    print(f"--- Démarrage du Robot Hyperliquid pour {NOM_CRYPTO} ---")

    # On récupère tes secrets (Clé privée et Adresse)
    private_key = os.getenv("PRIVATE_KEY")
    public_address = os.getenv("PUBLIC_ADDRESS")

    if not private_key or not public_address:
        print("ERREUR : Je ne trouve pas ta CLÉ PRIVÉE ou ton ADRESSE dans les réglages Render.")
        return

    try:
        # Connexion à Hyperliquid (Le marché)
        account = Account.from_key(private_key)
        info = Info(constants.MAINNET_API_URL, skip_ws=True)
        exchange = Exchange(account, constants.MAINNET_API_URL, account_address=public_address)
        print("✅ Connecté au marché !")

        # Vérifier si tu as des sous (USDC)
        user_state = info.spot_user_state(public_address)
        balances = user_state.get("balances", [])
        mon_solde_usdc = 0.0
        
        for b in balances:
            if b["coin"] == "USDC":
                mon_solde_usdc = float(b["total"])
        
        print(f"💰 Tu as {mon_solde_usdc} USDC dans ton porte-monnaie.")

        if mon_solde_usdc < MONTANT_A_ACHETER_USDC:
            print(f"❌ Pas assez d'argent ! Il faut {MONTANT_A_ACHETER_USDC} USDC.")
            return

        # Trouver le prix du HYPE
        prix_actuel = 0
        all_mids = info.all_mids()
        
        # On cherche le prix du HYPE
        if NOM_CRYPTO in all_mids:
             prix_actuel = float(all_mids[NOM_CRYPTO])
        else:
             print("⚠️ Je ne trouve pas le prix exact, je vais essayer d'acheter au prix du marché.")
             prix_actuel = 100.0 

        # On calcule combien de pièces on peut acheter
        # On ajoute 5% au prix pour être sûr que l'achat passe tout de suite
        prix_limite = prix_actuel * 1.05
        quantite = round(MONTANT_A_ACHETER_USDC / prix_limite, 2)

        if quantite <= 0:
             print("❌ Quantité trop petite à acheter.")
             return

        print(f"🛒 J'essaie d'acheter {quantite} {NOM_CRYPTO}...")

        # L'ordre d'achat
        result = exchange.order(
            name=NOM_CRYPTO,
            is_buy=True,
            sz=quantite,
            limit_px=prix_limite,
            order_type={"limit": {"tif": "Ioc"}} # "Immédiat ou Annuler"
        )

        # Vérification
        status = result["response"]["type"]
        if status == "order":
            print(f"🎉 SUCCÈS ! J'ai acheté du {NOM_CRYPTO} sur Hyperliquid !")
        else:
            print(f"🤔 Bizarre, voici la réponse : {result}")

    except Exception as e:
        print(f"💥 Oups, une erreur : {e}")

if __name__ == "__main__":
    run_bot()
