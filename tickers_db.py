"""
Base de datos local de tickers conocidos.
Se usa para:
 - Mostrar botones de "más operados" en Dólar y Bonos.
 - Hacer matching difuso cuando el usuario escribe mal un ticker
   (ej: "Galicia" -> sugerir "GGAL").
"""

# --- DÓLAR ---
# clave = tipo que espera dolarapi.com, valor = etiqueta linda para el botón
DOLARES = {
    "oficial": "Dólar Oficial",
    "blue": "Dólar Blue",
    "bolsa": "Dólar MEP",
    "contadoconliqui": "Dólar CCL",
    "cripto": "Dólar Cripto",
    "mayorista": "Dólar Mayorista",
    "tarjeta": "Dólar Tarjeta",
}

# --- BONOS más operados (soberanos en dólares/pesos) ---
BONOS_TOP = {
    "AL30": "Bonar 2030",
    "GD30": "Global 2030",
    "AL29": "Bonar 2029",
    "GD29": "Global 2029",
    "AL35": "Bonar 2035",
    "GD35": "Global 2035",
    "AE38": "Bonar 2038",
}

# --- ACCIONES LÍDER (Panel Líder / General) para matching y sugerencias ---
ACCIONES = {
    "GGAL": "Grupo Financiero Galicia",
    "YPFD": "YPF",
    "PAMP": "Pampa Energía",
    "ALUA": "Aluar",
    "TXAR": "Ternium Argentina",
    "CEPU": "Central Puerto",
    "BMA": "Banco Macro",
    "SUPV": "Grupo Supervielle",
    "BBAR": "BBVA Argentina",
    "TGSU2": "Transportadora Gas del Sur",
    "COME": "Sociedad Comercial del Plata",
    "CRES": "Cresud",
    "EDN": "Edenor",
    "TRAN": "Transener",
    "LOMA": "Loma Negra",
    "MIRG": "Mirgor",
}

# --- CEDEARs más comunes (representan acciones de EEUU) ---
CEDEARS = {
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "KO": "Coca-Cola",
    "TSLA": "Tesla",
    "AMZN": "Amazon",
    "GOOGL": "Alphabet (Google)",
    "META": "Meta",
    "NVDA": "Nvidia",
    "DISN": "Disney",
    "MELI": "Mercado Libre",
    "VIST": "Vista Energy",
    "NFLX": "Netflix",
}

# --- CRIPTOMONEDAS (id de CoinGecko : etiqueta) ---
CRIPTO = {
    "bitcoin": "Bitcoin (BTC)",
    "ethereum": "Ethereum (ETH)",
    "tether": "Tether (USDT)",
    "solana": "Solana (SOL)",
    "ripple": "XRP",
    "dogecoin": "Dogecoin (DOGE)",
}

CATEGORIAS = {
    "acciones": "📈 Acciones Locales",
    "cedears": "🌎 CEDEARs y Wall Street",
    "bonos": "💵 Bonos",
    "dolar": "💲 Dólar",
    "cripto": "🪙 Criptomonedas",
}


def universo_para_matching(categoria: str) -> dict:
    """Devuelve el diccionario ticker->nombre relevante para sugerir coincidencias."""
    return {
        "acciones": ACCIONES,
        "cedears": CEDEARS,
        "bonos": BONOS_TOP,
        "cripto": CRIPTO,
    }.get(categoria, {})
