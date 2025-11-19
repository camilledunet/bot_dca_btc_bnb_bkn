import os
import time
import hmac
import hashlib
import requests
from datetime import datetime
from urllib.parse import urlencode

# Si tu as installé python-dotenv, ça va charger automatiquement le fichier .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Si ce module n'est pas installé, ce n'est pas grave
    pass

# ========================
# CONFIG
# ========================

BASE_URL = "https://api.mexc.com"  # Endpoint de l'API spot MEXC

API_KEY = os.getenv("MEXC_API_KEY")
API_SECRET = os.getenv("MEXC_API_SECRET")

# Montant par coin à chaque DCA (dans la devise de cotation : USDC ou USDT)
MONTANT_PAR_COIN = 1.16   # 1,16$ par crypto

# Paires spot :
# - BTC côté en USDC
# - BNB & BKN côté en USDT
PAIRS = ["BTCUSDC", "BNBUSDT"]



# ========================
# FONCTIONS UTILITAIRES
# ========================

def create_signature(query_string: str, secret: str) -> str:
    """
    Crée la signature HMAC SHA256 à partir d'une chaîne de paramètres.
    """
    return hmac.new(
        secret.encode("utf-8"),
        query_string.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()


def mexc_request(method: str, path: str, params: dict = None, is_signed: bool = False):
    """
    Envoie une requête à l'API MEXC (Spot v3).

    - method : "GET", "POST", ...
    - path   : ex "/api/v3/order"
    - params : dict de paramètres (symbol, side, type, ...)
    - is_signed : True pour les endpoints qui nécessitent une signature (account, order, ...)

    Pour les endpoints SIGNED :
    - on met TOUT dans la query string : symbol=...&side=...&...&timestamp=...&recvWindow=...
    - on calcule la signature sur CETTE chaîne
    - on ajoute &signature=... à la fin de l'URL
    """
    if params is None:
        params = {}

    method = method.upper()
    url = BASE_URL + path

    # Endpoints publics simples (ping, time, etc.)
    if not is_signed:
        if method == "GET":
            response = requests.get(url, params=params, timeout=10)
        else:
            response = requests.post(url, params=params, timeout=10)
    else:
        if not API_KEY or not API_SECRET:
            raise Exception("API_KEY ou API_SECRET manquants. Vérifie ton fichier .env.")

        full_params = dict(params)
        full_params["timestamp"] = int(time.time() * 1000)
        full_params["recvWindow"] = 5000  # 5 secondes

        query_string = urlencode(full_params)
        signature = create_signature(query_string, API_SECRET)

        url = url + "?" + query_string + "&signature=" + signature

        headers = {
            "X-MEXC-APIKEY": API_KEY
        }

        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        else:
            response = requests.post(url, headers=headers, timeout=10)

    try:
        data = response.json()
    except Exception:
        response.raise_for_status()
        raise

    if response.status_code != 200:
        raise Exception(f"Erreur API MEXC ({response.status_code}): {data}")

    return data


def place_market_buy(symbol: str, quote_amount: float):
    """
    Passe un ordre d'achat MARKET sur 'symbol'
    en dépensant 'quote_amount' dans la devise de cotation (USDC ou USDT).
    """
    params = {
        "symbol": symbol,
        "side": "BUY",
        "type": "MARKET",
        "quoteOrderQty": str(quote_amount),
    }

    try:
        result = mexc_request("POST", "/api/v3/order", params=params, is_signed=True)
        print(f"[OK] MARKET BUY {symbol} pour {quote_amount} → ordre {result.get('orderId')}")
        return result
    except Exception as e:
        print(f"[ERREUR] Impossible de passer l'ordre sur {symbol} : {e}")
        return None


def get_all_balances():
    """
    Récupère toutes les balances sous forme de dictionnaire.
    Ex: {'USDT': {'free': 10.0, 'locked': 0.0}, 'USDC': {...}, ...}
    """
    try:
        account = mexc_request("GET", "/api/v3/account", is_signed=True)
        balances = account.get("balances", [])
        result = {}
        for asset in balances:
            asset_name = asset.get("asset")
            free = float(asset.get("free", "0"))
            locked = float(asset.get("locked", "0"))
            result[asset_name] = {"free": free, "locked": locked}
        return result
    except Exception as e:
        print(f"[ERREUR] Impossible de récupérer les balances : {e}")
        return {}


def dca_run():
    """
    Un cycle de DCA :
    - on regarde combien tu as en USDC et USDT
    - on achète pour MONTANT_PAR_COIN sur chaque paire, si le solde de la devise correspondante est suffisant
    """
    print("=" * 60)
    print(f"Lancement du DCA MEXC - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if not API_KEY or not API_SECRET:
        print("[CRITIQUE] API_KEY ou API_SECRET manquants. Vérifie ton fichier .env.")
        return

    balances = get_all_balances()
    if not balances:
        print("[STOP] Impossible de lire les balances, on annule ce cycle.")
        return

    # On sépare les paires par devise de cotation (USDC / USDT)
    quotes = ["USDC", "USDT"]

    for quote in quotes:
        # On sélectionne les paires qui finissent par cette devise
        pairs_for_quote = [p for p in PAIRS if p.endswith(quote)]
        if not pairs_for_quote:
            continue  # aucune paire pour cette devise, on passe

        free = balances.get(quote, {}).get("free", 0.0)
        total_needed = MONTANT_PAR_COIN * len(pairs_for_quote)

        print(f"Solde {quote} disponible : {free:.4f}, nécessaire pour ces paires : {total_needed:.4f}")

        if free < total_needed:
            print(f"[STOP] Solde insuffisant en {quote} pour ces paires : {pairs_for_quote}")
            continue

        # Pour chaque paire avec cette devise de cotation, on passe l'ordre
        for symbol in pairs_for_quote:
            print(f"--> Achat MARKET de {MONTANT_PAR_COIN} {quote} sur {symbol}")
            place_market_buy(symbol, MONTANT_PAR_COIN)
            time.sleep(0.5)  # petite pause


    print("DCA terminé.")
    print("=" * 60)


if __name__ == "__main__":
    dca_run()
