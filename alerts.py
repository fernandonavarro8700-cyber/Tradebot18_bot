"""
Alertas de precio muy simples, persistidas en un archivo JSON local
(alerts.json). Para un volumen chico/mediano de usuarios esto alcanza;
si el bot crece conviene migrar a SQLite o Postgres.

Cada alerta:
{
    "chat_id": int,
    "categoria": "acciones" | "cedears" | "bonos" | "dolar" | "cripto",
    "ticker": str,
    "nombre": str,
    "precio_objetivo": float,
    "direccion": "sube" | "baja"   # se calcula al crear la alerta
}
"""

import json
import os

import data_sources as ds

ARCHIVO = os.path.join(os.path.dirname(__file__), "alerts.json")


def _cargar():
    if not os.path.exists(ARCHIVO):
        return []
    with open(ARCHIVO, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def _guardar(alertas):
    with open(ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(alertas, f, ensure_ascii=False, indent=2)


def crear_alerta(chat_id, categoria, ticker, nombre, precio_actual, precio_objetivo):
    direccion = "sube" if precio_objetivo > precio_actual else "baja"
    alertas = _cargar()
    alertas.append({
        "chat_id": chat_id,
        "categoria": categoria,
        "ticker": ticker,
        "nombre": nombre,
        "precio_objetivo": precio_objetivo,
        "direccion": direccion,
    })
    _guardar(alertas)
    return direccion


def _precio_actual(categoria, ticker):
    if categoria == "dolar":
        r = ds.get_dolar(ticker)
    elif categoria == "acciones":
        r = ds.get_accion(ticker)
    elif categoria == "cedears":
        r = ds.get_cedear(ticker)
    elif categoria == "bonos":
        r = ds.get_bono(ticker)
    elif categoria == "cripto":
        r = ds.get_cripto(ticker)
    else:
        r = None
    return r["precio"] if r else None


async def revisar_alertas(context):
    """Job periódico: recorre todas las alertas, notifica y elimina las cumplidas."""
    alertas = _cargar()
    if not alertas:
        return

    restantes = []
    for alerta in alertas:
        precio = _precio_actual(alerta["categoria"], alerta["ticker"])
        if precio is None:
            restantes.append(alerta)
            continue

        cumplida = (
            (alerta["direccion"] == "sube" and precio >= alerta["precio_objetivo"])
            or (alerta["direccion"] == "baja" and precio <= alerta["precio_objetivo"])
        )

        if cumplida:
            texto = (
                f"🔔 ¡Alerta cumplida!\n\n"
                f"{alerta['nombre']} ({alerta['ticker'].upper()}) llegó a "
                f"{precio:.2f}, tu objetivo era {alerta['precio_objetivo']:.2f}."
            )
            try:
                await context.bot.send_message(chat_id=alerta["chat_id"], text=texto)
            except Exception:
                pass
        else:
            restantes.append(alerta)

    _guardar(restantes)
