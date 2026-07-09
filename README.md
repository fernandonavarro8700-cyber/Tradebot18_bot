# 📊 Bot de Cotizaciones para Telegram

Bot de Telegram que muestra cotizaciones en tiempo real de Acciones locales,
CEDEARs/Wall Street, Bonos, Dólar y Criptomonedas, con alertas de precio,
gráfico histórico y sugerencias inteligentes cuando el ticker está mal escrito.

## Funcionalidades

- **Menú por categoría**: Acciones, CEDEARs, Bonos, Dólar, Cripto.
- **Botones directos** para Dólar y Bonos (los instrumentos más operados a un clic).
- **Búsqueda por ticker** para Acciones/CEDEARs, con botón "Ver las 5 más operadas hoy".
- **Cotización en tiempo real**: precio, variación % diaria y volumen.
- **Alertas de precio**: avisa cuando un activo llega al valor objetivo.
- **Gráfico histórico** de los últimos 7 días.
- **Corrección de errores**: si el ticker está mal escrito (ej. "Galicia"),
  sugiere la opción correcta (GGAL) antes de mostrar la cotización.

## Estructura del proyecto

```
bot.py            # Lógica principal: menús, conversación, handlers
data_sources.py   # Conexión a las APIs de cotizaciones (dólar, mercado local, cripto)
tickers_db.py     # Diccionarios de tickers conocidos (para botones y matching)
alerts.py         # Alertas de precio (guardadas en alerts.json)
charts.py         # Generación del gráfico histórico (PNG)
requirements.txt
```

## Fuentes de datos (todas gratis, sin API key)

| Categoría | Fuente |
|---|---|
| Dólar (oficial/blue/MEP/CCL/etc) | [dolarapi.com](https://dolarapi.com) |
| Acciones / CEDEARs / Bonos (mercado local) | [data912.com](https://data912.com) |
| Criptomonedas | [api.coingecko.com](https://api.coingecko.com) |
| Gráfico histórico | Yahoo Finance (vía librería `yfinance`) |

> Son APIs públicas no oficiales. Si en el futuro cambian su formato,
> hay que ajustar `data_sources.py`.

## Deploy

El bot corre 24/7 en [Railway](https://railway.app) a partir de este repositorio,
con la variable de entorno `TELEGRAM_BOT_TOKEN` configurada ahí.

Instrucciones detalladas de instalación local y deploy en [`SETUP.md`](./SETUP.md).
