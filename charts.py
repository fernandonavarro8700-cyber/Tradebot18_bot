"""
Genera un gráfico histórico (últimos 7 días) para el activo consultado,
usando Yahoo Finance como fuente unificada de históricos.

Mapeo de tickers -> símbolo de Yahoo Finance:
 - Acciones / Bonos locales: se les agrega el sufijo ".BA" (Bolsa de Buenos Aires)
 - CEDEARs / Wall Street:    se usa el ticker tal cual (mercado de EEUU)
 - Cripto:                   se usa "<SIMBOLO>-USD" (ej: BTC-USD)
"""

import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import yfinance as yf

_CRIPTO_YAHOO = {
    "bitcoin": "BTC-USD",
    "ethereum": "ETH-USD",
    "tether": "USDT-USD",
    "solana": "SOL-USD",
    "ripple": "XRP-USD",
    "dogecoin": "DOGE-USD",
}


def _simbolo_yahoo(categoria: str, ticker: str) -> str:
    if categoria in ("acciones", "bonos"):
        return f"{ticker.upper()}.BA"
    if categoria == "cedears":
        return ticker.upper()
    if categoria == "cripto":
        return _CRIPTO_YAHOO.get(ticker.lower(), f"{ticker.upper()}-USD")
    if categoria == "dolar":
        return None  # no hay histórico de Yahoo para el dólar argentino
    return ticker.upper()


def generar_grafico(categoria: str, ticker: str, nombre: str):
    """Devuelve (BytesIO con PNG, None) o (None, mensaje_error)."""
    simbolo = _simbolo_yahoo(categoria, ticker)
    if simbolo is None:
        return None, "No tengo histórico disponible para cotizaciones de dólar todavía."

    try:
        hist = yf.Ticker(simbolo).history(period="7d")
    except Exception:
        return None, "No pude descargar el histórico en este momento. Probá de nuevo más tarde."

    if hist.empty:
        return None, f"No encontré datos históricos para {simbolo}."

    fig, ax = plt.subplots(figsize=(6, 3.5))
    ax.plot(hist.index, hist["Close"], color="#2563eb", linewidth=2)
    ax.fill_between(hist.index, hist["Close"], color="#2563eb", alpha=0.08)
    ax.set_title(f"{nombre} ({ticker.upper()}) - últimos 7 días")
    ax.set_ylabel("Precio")
    ax.grid(alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()

    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=140)
    plt.close(fig)
    buffer.seek(0)
    return buffer, None
