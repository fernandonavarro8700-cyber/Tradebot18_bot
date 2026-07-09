import difflib
import logging
import os

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

import alerts
import data_sources as ds
from charts import generar_grafico
from tickers_db import ACCIONES, BONOS_TOP, CATEGORIAS, CEDEARS, CRIPTO, DOLARES, universo_para_matching

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Estados de la conversación
ESPERANDO_TICKER, ESPERANDO_PRECIO_ALERTA, CONFIRMANDO_SUGERENCIA = range(3)


# ---------------------------------------------------------------------------
# HELPERS DE UI
# ---------------------------------------------------------------------------
def menu_principal():
    botones = [[InlineKeyboardButton(nombre, callback_data=f"cat:{clave}")]
               for clave, nombre in CATEGORIAS.items()]
    return InlineKeyboardMarkup(botones)


def menu_dolar():
    botones = [[InlineKeyboardButton(nombre, callback_data=f"quote:dolar:{clave}")]
               for clave, nombre in DOLARES.items()]
    botones.append([InlineKeyboardButton("⬅️ Volver al inicio", callback_data="home")])
    return InlineKeyboardMarkup(botones)


def menu_bonos():
    botones = [[InlineKeyboardButton(f"{t} - {n}", callback_data=f"quote:bonos:{t}")]
               for t, n in BONOS_TOP.items()]
    botones.append([InlineKeyboardButton("⬅️ Volver al inicio", callback_data="home")])
    return InlineKeyboardMarkup(botones)


def menu_cripto():
    botones = [[InlineKeyboardButton(nombre, callback_data=f"quote:cripto:{clave}")]
               for clave, nombre in CRIPTO.items()]
    botones.append([InlineKeyboardButton("⬅️ Volver al inicio", callback_data="home")])
    return InlineKeyboardMarkup(botones)


def menu_pedir_ticker(categoria):
    botones = [
        [InlineKeyboardButton("🔥 Ver las 5 más operadas hoy", callback_data=f"top5:{categoria}")],
        [InlineKeyboardButton("⬅️ Volver al inicio", callback_data="home")],
    ]
    return InlineKeyboardMarkup(botones)


def menu_post_cotizacion(categoria, ticker):
    botones = [
        [InlineKeyboardButton("🔔 Crear Alerta", callback_data=f"alerta:{categoria}:{ticker}")],
        [InlineKeyboardButton("📊 Ver Gráfico Histórico", callback_data=f"grafico:{categoria}:{ticker}")],
        [InlineKeyboardButton("🔎 Nueva Consulta", callback_data=f"cat:{categoria}")],
        [InlineKeyboardButton("🏠 Volver al Inicio", callback_data="home")],
    ]
    return InlineKeyboardMarkup(botones)


def formatear_cotizacion(data, categoria):
    lineas = [f"*{data['nombre']}* ({data['ticker'].upper()})"]
    if data.get("precio") is not None:
        lineas.append(f"💰 Precio: {data['precio']:.2f}")
    if data.get("variacion_pct") is not None:
        signo = "🟢" if data["variacion_pct"] >= 0 else "🔴"
        lineas.append(f"{signo} Variación diaria: {data['variacion_pct']:.2f}%")
    if data.get("volumen"):
        lineas.append(f"📦 Volumen: {data['volumen']:,.0f}")
    if categoria == "dolar" and data.get("extra"):
        lineas.append(f"Compra: {data['extra']['compra']} / Venta: {data['extra']['venta']}")
    return "\n".join(lineas)


def buscar_dato(categoria: str, ticker: str):
    if categoria == "dolar":
        return ds.get_dolar(ticker)
    if categoria == "acciones":
        return ds.get_accion(ticker)
    if categoria == "cedears":
        return ds.get_cedear(ticker)
    if categoria == "bonos":
        return ds.get_bono(ticker)
    if categoria == "cripto":
        return ds.get_cripto(ticker)
    return None


# ---------------------------------------------------------------------------
# HANDLERS
# ---------------------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        "👋 ¡Hola! Soy tu bot de cotizaciones.\n\n"
        "Elegí una categoría para empezar:"
    )
    if update.message:
        await update.message.reply_text(texto, reply_markup=menu_principal())
    else:
        await update.callback_query.edit_message_text(texto, reply_markup=menu_principal())
    return ConversationHandler.END


async def manejar_botones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "home":
        await start(update, context)
        return ConversationHandler.END

    if data.startswith("cat:"):
        categoria = data.split(":", 1)[1]
        context.user_data["categoria"] = categoria

        if categoria == "dolar":
            await query.edit_message_text("💲 Elegí la cotización del dólar:", reply_markup=menu_dolar())
            return ConversationHandler.END
        if categoria == "bonos":
            await query.edit_message_text("💵 Elegí un bono soberano:", reply_markup=menu_bonos())
            return ConversationHandler.END
        if categoria == "cripto":
            await query.edit_message_text("🪙 Elegí una criptomoneda:", reply_markup=menu_cripto())
            return ConversationHandler.END
        if categoria in ("acciones", "cedears"):
            nombre_cat = "acción" if categoria == "acciones" else "CEDEAR"
            await query.edit_message_text(
                f"✏️ Escribí el ticker de la {nombre_cat} que querés consultar "
                f"(ej: {'YPFD, GGAL' if categoria == 'acciones' else 'AAPL, KO'}):",
                reply_markup=menu_pedir_ticker(categoria),
            )
            return ESPERANDO_TICKER

    if data.startswith("top5:"):
        categoria = data.split(":", 1)[1]
        await query.edit_message_text("🔎 Buscando las más operadas...")
        top = ds.get_top5(categoria)
        if not top:
            await query.edit_message_text(
                "No pude obtener el ranking en este momento. Probá de nuevo en un rato.",
                reply_markup=menu_principal(),
            )
            return ConversationHandler.END
        texto = "🔥 *Las 5 más operadas hoy:*\n\n" + "\n\n".join(
            formatear_cotizacion(item, categoria) for item in top
        )
        await query.edit_message_text(texto, parse_mode=ParseMode.MARKDOWN, reply_markup=menu_principal())
        return ConversationHandler.END

    if data.startswith("quote:"):
        _, categoria, ticker = data.split(":", 2)
        await mostrar_cotizacion(update, context, categoria, ticker, via_callback=True)
        return ConversationHandler.END

    if data.startswith("grafico:"):
        _, categoria, ticker = data.split(":", 2)
        info = buscar_dato(categoria, ticker)
        nombre = info["nombre"] if info else ticker.upper()
        await query.edit_message_text("📊 Generando el gráfico...")
        buffer, error = generar_grafico(categoria, ticker, nombre)
        if error:
            await context.bot.send_message(chat_id=query.message.chat_id, text=error)
        else:
            await context.bot.send_photo(chat_id=query.message.chat_id, photo=buffer)
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="¿Qué querés hacer ahora?",
            reply_markup=menu_post_cotizacion(categoria, ticker),
        )
        return ConversationHandler.END

    if data.startswith("alerta:"):
        _, categoria, ticker = data.split(":", 2)
        context.user_data["alerta_categoria"] = categoria
        context.user_data["alerta_ticker"] = ticker
        await query.edit_message_text(f"🔔 ¿A qué precio querés que te avise sobre {ticker.upper()}?")
        return ESPERANDO_PRECIO_ALERTA

    if data.startswith("confirmar_sugerencia:si:"):
        _, _, categoria, ticker = data.split(":", 3)
        await mostrar_cotizacion(update, context, categoria, ticker, via_callback=True)
        return ConversationHandler.END

    if data.startswith("confirmar_sugerencia:no:"):
        categoria = data.split(":", 2)[2]
        await query.edit_message_text(
            "Ok, probá escribir el ticker de nuevo (ej: usá las siglas oficiales del activo):",
            reply_markup=menu_pedir_ticker(categoria),
        )
        return ESPERANDO_TICKER

    return ConversationHandler.END


async def mostrar_cotizacion(update, context, categoria, ticker, via_callback=False):
    data = buscar_dato(categoria, ticker)
    chat_id = update.callback_query.message.chat_id if via_callback else update.message.chat_id

    if not data or data.get("precio") is None:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"No pude obtener la cotización de {ticker.upper()} en este momento.",
            reply_markup=menu_principal(),
        )
        return

    texto = formatear_cotizacion(data, categoria)
    context.user_data["ultimo_ticker"] = data["ticker"]
    context.user_data["ultimo_precio"] = data["precio"]

    if via_callback:
        await update.callback_query.edit_message_text(
            texto, parse_mode=ParseMode.MARKDOWN, reply_markup=menu_post_cotizacion(categoria, data["ticker"])
        )
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text=texto,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=menu_post_cotizacion(categoria, data["ticker"]),
        )


async def recibir_ticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    categoria = context.user_data.get("categoria")
    ticker_ingresado = update.message.text.strip()
    ticker_upper = ticker_ingresado.upper()

    universo = universo_para_matching(categoria)

    # 1) Coincidencia exacta con un ticker conocido
    if ticker_upper in universo:
        await mostrar_cotizacion(update, context, categoria, ticker_upper)
        return ConversationHandler.END

    # 2) Intentar directamente contra la fuente de datos (puede haber tickers
    #    que no estén en nuestro diccionario local pero sí existan en la API)
    data = buscar_dato(categoria, ticker_upper)
    if data and data.get("precio") is not None:
        await mostrar_cotizacion(update, context, categoria, ticker_upper)
        return ConversationHandler.END

    # 3) No se encontró: buscar la sugerencia más parecida, tanto por ticker
    #    como por nombre de la empresa (ej: "Galicia" -> GGAL)
    candidatos = list(universo.keys()) + list(universo.values())
    parecidos = difflib.get_close_matches(ticker_ingresado, candidatos, n=1, cutoff=0.5)

    if parecidos:
        sugerido = parecidos[0]
        # si el match fue por nombre, convertirlo al ticker correspondiente
        ticker_sugerido = sugerido
        if sugerido not in universo:
            for t, n in universo.items():
                if n == sugerido:
                    ticker_sugerido = t
                    break
        nombre_sugerido = universo.get(ticker_sugerido, ticker_sugerido)

        botones = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Sí", callback_data=f"confirmar_sugerencia:si:{categoria}:{ticker_sugerido}")],
            [InlineKeyboardButton("❌ No", callback_data=f"confirmar_sugerencia:no:{categoria}")],
        ])
        await update.message.reply_text(
            f"No encontré el ticker '{ticker_ingresado}'. "
            f"¿Quisiste decir *{ticker_sugerido}* ({nombre_sugerido})?",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=botones,
        )
        return CONFIRMANDO_SUGERENCIA

    await update.message.reply_text(
        f"No encontré el ticker '{ticker_ingresado}' y no se me ocurre a qué te referís. "
        "Fijate que esté bien escrito e intentá de nuevo, o volvé al inicio.",
        reply_markup=menu_pedir_ticker(categoria),
    )
    return ESPERANDO_TICKER


async def recibir_precio_alerta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip().replace(",", ".")
    try:
        precio_objetivo = float(texto)
    except ValueError:
        await update.message.reply_text("Ingresá solo un número, ej: 1250.50")
        return ESPERANDO_PRECIO_ALERTA

    categoria = context.user_data["alerta_categoria"]
    ticker = context.user_data["alerta_ticker"]
    data = buscar_dato(categoria, ticker)

    if not data or data.get("precio") is None:
        await update.message.reply_text("No pude confirmar el precio actual, intentá crear la alerta de nuevo.")
        return ConversationHandler.END

    direccion = alerts.crear_alerta(
        chat_id=update.message.chat_id,
        categoria=categoria,
        ticker=ticker,
        nombre=data["nombre"],
        precio_actual=data["precio"],
        precio_objetivo=precio_objetivo,
    )
    palabra = "suba" if direccion == "sube" else "baje"
    await update.message.reply_text(
        f"🔔 ¡Listo! Te voy a avisar cuando {data['nombre']} ({ticker.upper()}) {palabra} a {precio_objetivo:.2f}.",
        reply_markup=menu_principal(),
    )
    return ConversationHandler.END


async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Operación cancelada.", reply_markup=menu_principal())
    return ConversationHandler.END


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    if not TOKEN:
        raise RuntimeError(
            "Falta la variable de entorno TELEGRAM_BOT_TOKEN. "
            "Creá un archivo .env basado en .env.example."
        )

    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start), CallbackQueryHandler(manejar_botones)],
        states={
            ESPERANDO_TICKER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_ticker),
                CallbackQueryHandler(manejar_botones),
            ],
            ESPERANDO_PRECIO_ALERTA: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_precio_alerta),
            ],
            CONFIRMANDO_SUGERENCIA: [
                CallbackQueryHandler(manejar_botones),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancelar), CommandHandler("start", start)],
    )

    app.add_handler(conv_handler)

    # Chequeo de alertas cada 3 minutos
    app.job_queue.run_repeating(alerts.revisar_alertas, interval=180, first=30)

    logger.info("Bot iniciado. Esperando mensajes...")
    app.run_polling()


if __name__ == "__main__":
    main()
