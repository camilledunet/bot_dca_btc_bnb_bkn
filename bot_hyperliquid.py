import os
from dotenv import load_dotenv
from hyperliquid.info import Info
from hyperliquid.exchange import Exchange
from hyperliquid.utils import constants
from eth_account.account import Account

load_dotenv()

# ================= CONFIGURATION =================
# On investit 20 USDC
MONTANT_A_ACHETER_USDC = 20.0 
NOM_CRYPTO = "HYPE"
# =================================================

def run_bot():
    print(f"--- 🚀 Démarrage Achat MARKET pour {NOM_CRYPTO} ---")

    private_key = os.getenv("PRIVATE_KEY")
    public_address = os.getenv("PUBLIC_ADDRESS")

    if not private_key:
        print("❌ ERREUR : Clé privée manquante.")
        return

    try:
        # 1. Connexion
        account = Account.from_key(private_key)
        info = Info(constants.MAINNET_API_URL, skip_ws=True)
        exchange = Exchange(account, constants.MAINNET_API_URL, account_address=public_address)
        print("✅ Connecté.")

        # 2. Récupérer le prix du marché
        all_mids = info.all_mids()
        prix_actuel = float(all_mids.get(NOM_CRYPTO, 25.0))
        print(f"ℹ️ Prix actuel du marché : {prix_actuel} $")

        # 3. Préparer l'ordre "MARKET"
        # Pour simuler un ordre Market qui passe à tous les coups, on met une marge de sécurité (+5%)
        # C'est ce qui garantit l'exécution immédiate.
        # IMPORTANT : On arrondit à 3 chiffres (ex: 26.855) pour éviter l'erreur "Tick Size".
        prix_execution = round(prix_actuel * 1.05, 3)
        
        # Calcul de la quantité (arrondi à 2 chiffres)
        quantite = round(MONTANT_A_ACHETER_USDC / prix_execution, 2)

        print(f"🛒 Envoi ordre MARKET : {quantite} {NOM_CRYPTO} (Cap: {prix_execution} $)")

        # 4. Envoyer l'ordre
        # "Ioc" (Immediate or Cancel) assure que ça s'exécute tout de suite ou pas du tout.
        result = exchange.order(
            name=NOM_CRYPTO,
            is_buy=True,
            sz=quantite,
            limit_px=prix_execution,
            order_type={"limit": {"tif": "Ioc"}}
        )

        # 5. Vérification
        status_type = result["response"]["type"]
        if status_type == "order":
            status_detail = result["response"]["data"]["statuses"][0]
            if "filled" in status_detail:
                print(f"🎉 SUCCÈS ! Ordre exécuté immédiatement au prix du marché.")
                print(f"👉 {status_detail}")
            else:
                print(f"⚠️ Rejeté par le marché : {status_detail}")
        else:
            print(f"❌ Erreur technique : {result}")

    except Exception as e:
        print(f"💥 Erreur : {e}")

if __name__ == "__main__":
    run_bot()
