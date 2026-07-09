> 📌 Este documento tiene el paso a paso completo de instalación y deploy. Para la descripción general del proyecto, ver [README.md](./README.md).

# 📊 Bot de Cotizaciones para Telegram

Bot que muestra cotizaciones en tiempo real de Acciones locales, CEDEARs/Wall Street,
Bonos, Dólar y Criptomonedas, con alertas de precio, gráfico histórico y sugerencias
inteligentes cuando el ticker está mal escrito.

## Estructura del proyecto

```
telegram-cotizaciones-bot/
├── bot.py            # Lógica principal: menús, conversación, handlers
├── data_sources.py   # Conexión a las APIs de cotizaciones (dólar, mercado local, cripto)
├── tickers_db.py      # Diccionarios de tickers conocidos (para botones y matching)
├── alerts.py          # Alertas de precio (guardadas en alerts.json)
├── charts.py           # Generación del gráfico histórico (PNG)
├── requirements.txt
├── .env.example
└── .gitignore
```

## Fuentes de datos (todas gratis, sin API key)

| Categoría              | Fuente                                    |
|------------------------|--------------------------------------------|
| Dólar (oficial/blue/MEP/CCL/etc) | https://dolarapi.com               |
| Acciones / CEDEARs / Bonos (mercado local) | https://data912.com    |
| Criptomonedas          | https://api.coingecko.com                  |
| Gráfico histórico      | Yahoo Finance (vía librería `yfinance`)    |

> ⚠️ Estas son APIs públicas no oficiales. Si en el futuro cambian su formato o
> caen, tendrás que ajustar `data_sources.py`. Si tu proyecto crece, considerá
> pasar a una fuente paga/oficial (ej. Invertir Online, Bull Market, etc.).

---

## Paso 1 — Crear el bot en Telegram

1. Abrí Telegram y buscá **@BotFather**.
2. Enviale `/newbot` y seguí los pasos (nombre y username del bot).
3. Te va a dar un **token** con este formato: `123456789:ABCdefGhIJKlmNoPQRstuVwxYZ`.
   Guardalo, lo vas a necesitar en el Paso 3.

## Paso 2 — Crear el repositorio en GitHub

1. Entrá a [github.com/new](https://github.com/new).
2. Nombre sugerido: `telegram-cotizaciones-bot`. Dejalo **privado** si vas a
   subir el token por error alguna vez (igual nunca lo subas, ver `.gitignore`).
3. No marques "Add README" porque ya vas a subir el tuyo.
4. Copiá la URL del repo (ej: `https://github.com/tu-usuario/telegram-cotizaciones-bot.git`).

## Paso 3 — Preparar el proyecto localmente

```bash
# 1. Descomprimí/copiá esta carpeta en tu máquina y entrá en ella
cd telegram-cotizaciones-bot

# 2. Creá un entorno virtual
python3 -m venv venv
source venv/bin/activate        # En Windows: venv\Scripts\activate

# 3. Instalá las dependencias
pip install -r requirements.txt

# 4. Copiá el archivo de ejemplo y pegá tu token
cp .env.example .env
# Editá .env y poné: TELEGRAM_BOT_TOKEN=el_token_que_te_dio_botfather

# 5. Probalo localmente
python bot.py
```

Si todo salió bien, en la consola vas a ver `Bot iniciado. Esperando mensajes...`
y podés hablarle al bot desde Telegram con `/start`.

## Paso 4 — Subirlo a GitHub

```bash
git init
git add .
git commit -m "Bot de cotizaciones inicial"
git branch -M main
git remote add origin https://github.com/tu-usuario/telegram-cotizaciones-bot.git
git push -u origin main
```

El `.gitignore` ya excluye tu `.env` y `alerts.json`, así que el token **nunca**
se sube al repositorio.

## Paso 5 — Dejarlo corriendo 24/7 (deploy gratuito)

Tu compu no puede quedar prendida siempre, así que conviene desplegarlo en un
servicio gratuito/económico. Dos opciones simples:

### Opción A: Railway
1. Entrá a [railway.app](https://railway.app) y logueate con GitHub.
2. "New Project" → "Deploy from GitHub repo" → elegí tu repo.
3. En "Variables" agregá `TELEGRAM_BOT_TOKEN` con tu token.
4. En "Settings" → "Start Command" poné: `python bot.py`.
5. Deploy. Listo, el bot queda corriendo solo.

### Opción B: Render (Background Worker)
1. Entrá a [render.com](https://render.com) → "New" → "Background Worker".
2. Conectá tu repo de GitHub.
3. Build command: `pip install -r requirements.txt`
4. Start command: `python bot.py`
5. Agregá la variable de entorno `TELEGRAM_BOT_TOKEN`.

> Usá "Background Worker", no "Web Service": este bot usa `run_polling()`
> (no abre un puerto HTTP), así que no necesita un servicio web.

---

## Cómo funciona el flujo del bot

1. **`/start`** → Menú principal con las 5 categorías.
2. **Dólar / Bonos** → Botones directos con los más operados → 1 clic = respuesta.
3. **Acciones / CEDEARs** → Pide escribir el ticker (universo muy grande para
   botones) + botón "Ver las 5 más operadas hoy".
4. **Criptomonedas** → Botones con las más comunes (BTC, ETH, USDT, SOL, XRP, DOGE).
5. Al mostrar la cotización (precio, variación % y volumen) ofrece:
   - 🔔 **Crear Alerta** → pide el precio objetivo y monitorea cada 3 minutos.
   - 📊 **Ver Gráfico Histórico** → imagen de los últimos 7 días.
   - 🔎 **Nueva Consulta** / 🏠 **Volver al Inicio**.
6. **Manejo de errores**: si el ticker no existe, usa `difflib` para comparar
   contra los tickers y nombres conocidos (ej. "Galicia" → sugiere "GGAL") y
   pregunta con botones **Sí/No** antes de mostrar la cotización.

## Ideas para seguir mejorando

- Migrar `alerts.json` a SQLite/Postgres si crece la cantidad de usuarios.
- Agregar más ONs (obligaciones negociables) al listado de bonos.
- Cachear el histórico de `yfinance` para no pedirlo de nuevo en pocos minutos.
- Agregar `/misalertas` para listar y cancelar alertas activas.
