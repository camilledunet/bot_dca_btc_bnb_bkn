import os
import time
from dotenv import load_dotenv
from hyperliquid.info import Info
from hyperliquid.exchange import Exchange
from hyperliquid.utils import constants
from eth_account.account import Account

load_dotenv()

# ================= CONFIGURATION =================
MONTANT_A_ACHETER_USDC = 20.0 
NOM_CRYPTO = "HYPE"
# =================================================

def run_bot():
    print(f"--- 💎 Démarrage Achat SPOT (Vrai Jeton) pour {NOM_CRYPTO} ---")

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

        # 2. Trouver le "Code Secret" du Spot HYPE
        # Sur Hyperliquid, le Spot n'a pas le même nom. Il faut trouver son index (ex: @4).
        print("🔍 Recherche du marché Spot...")
        spot_meta = info.spot_meta()
        universe = spot_meta["universe"]
        
        spot_name_code = None
        spot_decimals = 8 # Par défaut

        for idx, token in enumerate(universe):
            if token["name"] == NOM_CRYPTO:
                spot_name_code = f"@{idx}" # C'est ça le secret ! (ex: @4)
                spot_decimals = token["szDecimals"]
                print(f"✅ Trouvé ! Le code Spot de {NOM_CRYPTO} est : {spot_name_code}")
                break
        
        if not spot_name_code:
            print(f"❌ Impossible de trouver {NOM_CRYPTO} dans la liste Spot !")
            return

        # 3. Vérifier le solde SPOT
        user_state = info.spot_user_state(public_address)
        mon_solde_usdc = 0.0
        for b in user_state.get("balances", []):
            if b["coin"] == "USDC":
                mon_solde_usdc = float(b["total"])
        
        print(f"💰 Ton solde SPOT : {mon_solde_usdc} USDC")

        if mon_solde_usdc < MONTANT_A_ACHETER_USDC:
            print(f"❌ Pas assez d'argent en SPOT ! (Tu as {mon_solde_usdc}, il faut {MONTANT_A_ACHETER_USDC})")
            print("👉 Transfère tes USDC de 'Perps' vers 'Spot' sur le site.")
            return

        # 4. Préparer l'ordre
        # On récupère le prix du Spot (qui peut être légèrement différent du Perp)
        all_mids = info.all_mids()
        # Le prix spot est souvent stocké sous le code (ex: @4) ou le nom
        prix_actuel = float(all_mids.get(spot_name_code, all_mids.get(NOM_CRYPTO, 25.0)))
        print(f"ℹ️ Prix Spot actuel : {prix_actuel} $")

        # Prix limite (+5% pour achat immédiat) arrondi à 4 décimales pour le Spot
        prix_execution = round(prix_actuel * 1.05, 4)
        
        # Quantité arrondie selon les règles du Spot (szDecimals)
        quantite = round(MONTANT_A_ACHETER_USDC / prix_execution, spot_decimals)

        print(f"🛒 Achat de {quantite} {NOM_CRYPTO} (Spot: {spot_name_code})")

        # 5. Envoyer l'ordre SPOT
        result = exchange.order(
            name=spot_name_code,  # On utilise le code @...
            is_buy=True,
            sz=quantite,
            limit_px=prix_execution,
            order_type={"limit": {"tif": "Ioc"}}
        )

        # 6. Vérification
        status_type = result["response"]["type"]
        if status_type == "order":
            status_detail = result["response"]["data"]["statuses"][0]
            if "filled" in status_detail:
                print(f"🎉 SUCCÈS TOTAL ! Tu as acheté du vrai {NOM_CRYPTO} (Spot).")
                print(f"👉 Vérifie ton 'Portfolio' > 'Spot'.")
            else:
                print(f"⚠️ Rejeté : {status_detail}")
        else:
            print(f"❌ Erreur technique : {result}")

    except Exception as e:
        print(f"💥 Erreur : {e}")

if __name__ == "__main__":
    run_bot()
