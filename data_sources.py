"""
Fuentes de datos (todas gratuitas, sin necesidad de API key):

- Dólar:            https://dolarapi.com
- Acciones/Bonos/CEDEARs (mercado local): https://data912.com
- Criptomonedas:    https://api.coingecko.com

Cada función devuelve un dict "normalizado":
    {
        "ticker": str,
        "nombre": str,
        "precio": float,
        "variacion_pct": float,
        "volumen": float | None,
    }
o None si no se encontró / hubo error.

Se cachean las respuestas por un rato corto para no golpear las APIs
de más (y no chocar con rate limits) cuando varios usuarios consultan
casi al mismo tiempo.
"""

import time
import requests

from tickers_db import DOLARES, CRIPTO

CACHE_TTL_SEGUNDOS = 30
_cache: dict[str, tuple[float, object]] = {}


def _cache_get(key):
    item = _cache.get(key)
    if not item:
        return None
    ts, valor = item
    if time.time() - ts > CACHE_TTL_SEGUNDOS:
        return None
    return valor


def _cache_set(key, valor):
    _cache[key] = (time.time(), valor)


def _get_json(url: str, timeout: int = 10):
    resp = requests.get(url, timeout=timeout, headers={"User-Agent": "cotizaciones-bot"})
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# DÓLAR
# ---------------------------------------------------------------------------
def get_dolar(tipo: str):
    """tipo: una de las claves de DOLARES (oficial, blue, bolsa, contadoconliqui, ...)"""
    cache_key = f"dolar:{tipo}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        data = _get_json(f"https://dolarapi.com/v1/dolares/{tipo}")
    except Exception:
        return None

    resultado = {
        "ticker": tipo,
        "nombre": DOLARES.get(tipo, tipo.capitalize()),
        "precio": data.get("venta") or data.get("compra"),
        "variacion_pct": None,  # dolarapi no da variación diaria
        "volumen": None,
        "extra": {
            "compra": data.get("compra"),
            "venta": data.get("venta"),
            "fecha": data.get("fechaActualizacion"),
        },
    }
    _cache_set(cache_key, resultado)
    return resultado


# ---------------------------------------------------------------------------
# MERCADO LOCAL: acciones, cedears, bonos (data912.com)
# ---------------------------------------------------------------------------
def _buscar_en_data912(endpoint: str, ticker: str):
    cache_key = f"data912:{endpoint}"
    lista = _cache_get(cache_key)
    if lista is None:
        try:
            lista = _get_json(f"https://data912.com/live/{endpoint}")
        except Exception:
            return None
        _cache_set(cache_key, lista)

    ticker = ticker.upper()
    for item in lista:
        simbolo = (item.get("symbol") or item.get("ticker") or "").upper()
        if simbolo == ticker:
            return {
                "ticker": simbolo,
                "nombre": item.get("description") or simbolo,
                "precio": item.get("c") or item.get("close") or item.get("px_bid"),
                "variacion_pct": item.get("pct_change") or item.get("change_pct"),
                "volumen": item.get("v") or item.get("volume"),
            }
    return None


def get_accion(ticker: str):
    return _buscar_en_data912("arg_stocks", ticker)


def get_cedear(ticker: str):
    return _buscar_en_data912("arg_cedears", ticker)


def get_bono(ticker: str):
    return _buscar_en_data912("arg_bonds", ticker)


def get_top5(categoria: str):
    """categoria: 'acciones' | 'cedears' | 'bonos'. Devuelve lista de 5 dicts normalizados
    ordenados por volumen operado descendente."""
    endpoint = {
        "acciones": "arg_stocks",
        "cedears": "arg_cedears",
        "bonos": "arg_bonds",
    }.get(categoria)
    if not endpoint:
        return []

    cache_key = f"data912:{endpoint}"
    lista = _cache_get(cache_key)
    if lista is None:
        try:
            lista = _get_json(f"https://data912.com/live/{endpoint}")
        except Exception:
            return []
        _cache_set(cache_key, lista)

    def volumen_de(item):
        return item.get("v") or item.get("volume") or 0

    top = sorted(lista, key=volumen_de, reverse=True)[:5]
    resultado = []
    for item in top:
        simbolo = (item.get("symbol") or item.get("ticker") or "").upper()
        resultado.append({
            "ticker": simbolo,
            "nombre": item.get("description") or simbolo,
            "precio": item.get("c") or item.get("close") or item.get("px_bid"),
            "variacion_pct": item.get("pct_change") or item.get("change_pct"),
            "volumen": volumen_de(item),
        })
    return resultado


# ---------------------------------------------------------------------------
# CRIPTO (CoinGecko)
# ---------------------------------------------------------------------------
def get_cripto(coin_id: str):
    coin_id = coin_id.lower()
    cache_key = f"cripto:{coin_id}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    url = (
        "https://api.coingecko.com/api/v3/simple/price"
        f"?ids={coin_id}&vs_currencies=usd&include_24hr_change=true&include_24hr_vol=true"
    )
    try:
        data = _get_json(url)
    except Exception:
        return None

    info = data.get(coin_id)
    if not info:
        return None

    resultado = {
        "ticker": coin_id,
        "nombre": CRIPTO.get(coin_id, coin_id.capitalize()),
        "precio": info.get("usd"),
        "variacion_pct": info.get("usd_24h_change"),
        "volumen": info.get("usd_24h_vol"),
    }
    _cache_set(cache_key, resultado)
    return resultado
