import streamlit as st
import yfinance as yf
import pandas as pd
from google import genai
from datetime import datetime, timedelta
import numpy as np
import altair as alt
import anthropic
from dotenv import load_dotenv
import os

load_dotenv()
tokenGenAI = os.getenv("api_key_genai")
api_key = os.getenv("api_key_anthropic")

# Configuración API Gemini
tokenGenAI = tokenGenAI
client = genai.Client(api_key=tokenGenAI)


# Configuración general
st.set_page_config(page_title="Análisis de Empresas", layout="centered")
st.markdown("""
    <style>
        .stApp {
            background: linear-gradient(to right, #f8f9fa, #e0f7fa);
            font-family: 'Segoe UI', sans-serif;
        }
        .section-header {
            color: #007B9E;
            font-size: 26px;
            padding-top: 20px;
        }
    </style>
""", unsafe_allow_html=True)


# Sidebar con parámetros
with st.sidebar:
    st.title(" TickerLens 📊🔎")
    st.markdown("TickerLens es una app que sirve para saber información general de la empresa que desees, te brinda datos relevantes que servirán para analizar más a profundidad la empresa, al igual que te dará una recomendación de inversión. \
    \n\n" \
    "A continuación, ingresa el ticker de la empresa que desees saber más información de ella:")
    symbol = st.text_input("Símbolo de la acción", value="AAPL", help="Ejemplo: AAPL, TSLA, MSFT")
    
    st.markdown("---")
    st.markdown("Hecho por👩‍💻: María Fernanda Rodríguez Calderón\n\nID 0242636")

# Si se ingresó un símbolo válido

if symbol:
    try:
        company = yf.Ticker(symbol)
        info = company.info

        if not info or 'longBusinessSummary' not in info:
            st.warning("⚠️ No se encontró información para el símbolo ingresado.")
        else:
            company_name = info.get("longName", "Nombre no disponible").upper()
            sector = info.get("sector", "Sector no disponible")
            description = info.get("longBusinessSummary", "Descripción no disponible")
            logo_url = info.get("logo_url", "")

            

            # === SECCIÓN 1: Información de la empresa ===
            st.markdown(f"<div class='section-header'>📌 Descripción de la Empresa</div>", unsafe_allow_html=True)
            st.subheader(company_name)
            st.markdown(f"<p style='color: #2ca02c; font-size: 16px;'><strong>Sector:</strong> {sector}</p>", unsafe_allow_html=True)

            # Traducir descripción
            prompt = "Traduce el siguiente texto al español dando la información más relevante resumido: " + description
            response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
            translated = response.text

            #Mostrar traducción
            st.markdown(f"""{translated}""")

            if logo_url:
                st.image(logo_url, width=150)

            # === Cargar precios históricos ===
            end_date = datetime.today()
            start_date = end_date - timedelta(days=5*365)
            hist = company.history(start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'))

            if not hist.empty:
                # === SECCIÓN 2: Gráfica ===
                st.markdown(f"<div class='section-header'>📈 Precio Histórico de Cierre (2020–2025)</div>", unsafe_allow_html=True)
                st.markdown(f"La siguiente gráfica muestra el precio histórico de cierre de los últimos 5 años (2020-2025) de **{symbol.upper()}**:")

                df_hist = hist.reset_index()[["Date", "Close"]]
            

                # Gráfica precios históricos
                line_chart = alt.Chart(df_hist).mark_line(
                    color="#007B9E",      # Azul elegante
                    strokeWidth=2.5,
                    opacity=0.85
                ).encode(
                    x=alt.X('Date:T', title='Fecha'),
                    y=alt.Y('Close:Q', title='Precio de Cierre'),
                    tooltip=[alt.Tooltip('Date:T', title='Fecha'), alt.Tooltip('Close:Q', title='Precio')]
                ).properties(
                    title=alt.TitleParams("Precio Histórico de Cierre", fontSize=20, anchor="middle"),
                    height=400,
                    width=700
                ).interactive()

                # Mostrar en Streamlit
                st.altair_chart(line_chart, use_container_width=True)

                # CSS para fondo y estética general
                st.markdown("""
                <style>
                    .stApp {
                        background: linear-gradient(to right, #f7f9fb, #eef9f9);
                    }
                    .vega-embed {
                        background-color: transparent !important;
                    }
                    .section-header {
                        font-size: 26px;
                        font-weight: 600;
                        color: #0a3d62;
                        text-align: center;
                        margin-top: 30px;
                    }
                </style>
                """, unsafe_allow_html=True)


                # === SECCIÓN 3: CAGR ===
                st.markdown(f"<div class='section-header'>📊 Rendimiento Compuesto Anual (CAGR)</div>", unsafe_allow_html=True)

                st.markdown("""
                    <div style='text-align: justify; font-size: 16px;'>
                        El <strong>rendimiento compuesto anual (CAGR)</strong> muestra el crecimiento medio anual de la acción,
                        considerando reinversión de ganancias. Es útil para analizar el comportamiento a largo plazo de una empresa.
                    </div>
                """, unsafe_allow_html=True)

                def calculate_cagr(start_value, end_value, years):
                    return (end_value / start_value) ** (1 / years) - 1

                today = hist.index[-1]
                periods = {
                    "1 año": 252,
                    "3 años": 252 * 3,
                    "5 años": 252 * 5,
                }

                cagr_results = {}
                for label, days in periods.items():
                    try:
                        start_date = today - pd.tseries.offsets.BDay(days)
                        if start_date < hist.index[0]:
                            cagr_results[label] = "No disponible"
                            continue
                        start_price = hist.loc[hist.index >= start_date][0:1]["Close"].values[0]
                        end_price = hist["Close"].iloc[-1]
                        years = days / 252
                        cagr = calculate_cagr(start_price, end_price, years)
                        cagr_results[label] = f"{cagr*100:.2f}%"
                    except Exception:
                        cagr_results[label] = "Error"

                st.table(pd.DataFrame.from_dict(cagr_results, orient="index", columns=["CAGR"]))

                #Fórmula CAGR
                st.latex(r"""
                    \text{CAGR} = \left( \frac{\text{Valor Final}}{\text{Valor Inicial}} \right)^{\frac{1}{\text{número de periodos}}} - 1
                """)

                # === SECCIÓN 4: Volatilidad Anualizada ===
                st.markdown(f"<div class='section-header'>📉 Volatilidad Anualizada (Riesgo)</div>", unsafe_allow_html=True)
                st.markdown("La **volatilidad** es la medida de la desviación de los rendimientos con respecto a la media.")

                st.latex(r"""
                \text{Volatilidad Anualizada} = \text{Desviación estándar de los rendimientos diarios} \times \sqrt{252}
                """)


                vol_results = {}
                for label, days in periods.items():
                    try:
                        start_date = today - pd.tseries.offsets.BDay(days)
                        if start_date < hist.index[0]:
                            vol_results[label] = "No disponible"
                            continue
                        data_range = hist.loc[hist.index >= start_date]["Close"].pct_change().dropna()
                        daily_std = np.std(data_range)
                        annualized_vol = daily_std * np.sqrt(252)
                        vol_results[label] = f" {annualized_vol*100:.2f}%"
                    except Exception:
                        vol_results[label] = "Error"

                st.table(pd.DataFrame.from_dict(vol_results, orient="index", columns=["Volatilidad Anualizada"]))

                # === SECCIÓN 5: Simulador de Inversión ===
                st.markdown(f"<div class='section-header'>💰 Simulador de Inversión</div>", unsafe_allow_html=True)
                st.markdown("Imagina que hubieras invertido en esta acción hace un tiempo. ¿Cuánto tendrías hoy?")

                inversion_inicial = st.number_input("Monto de inversión inicial (USD)", min_value=100.0, value=1000.0, step=100.0)
                periodo_seleccionado = st.selectbox("Selecciona el período de inversión", list(periods.keys()))

                dias = periods[periodo_seleccionado]
                fecha_inicio = today - pd.tseries.offsets.BDay(dias)
                hist_periodo = hist.loc[hist.index >= fecha_inicio]

                if not hist_periodo.empty:
                    precios_normalizados = hist_periodo["Close"] / hist_periodo["Close"].iloc[0]
                    valor_inversion = precios_normalizados * inversion_inicial
                    valor_futuro = valor_inversion.iloc[-1]

                    st.markdown(f"""
                        <div style='background-color:#d4edda; padding: 15px; border-radius: 10px; font-size: 18px; color: #155724;'>
                        💸 Si hubieras invertido <strong>${inversion_inicial:,.2f}</strong> dólares hace <strong>{periodo_seleccionado}</strong>, hoy tendrías aproximadamente <strong>${valor_futuro:,.2f}</strong> dólares.
                        </div>
                    """, unsafe_allow_html=True)

                    #Gráfica

                    # Preparar el DataFrame
                    df_inversion = valor_inversion.reset_index()
                    df_inversion.columns = ["Date", "Valor"]

                    # Gráfico de crecimiento de la inversión
                    chart_inversion = alt.Chart(df_inversion).mark_line(
                        color="#28a745",        # Verde elegante
                        strokeWidth=2.5,
                        opacity=0.85
                    ).encode(
                        x=alt.X('Date:T', title='Fecha'),
                        y=alt.Y('Valor:Q', title='Valor de la Inversión'),
                        tooltip=[
                            alt.Tooltip('Date:T', title='Fecha'),
                            alt.Tooltip('Valor:Q', title='Valor')
                        ]
                    ).properties(
                        title=alt.TitleParams(
                            text="Crecimiento de la Inversión a lo Largo del Tiempo",
                            fontSize=20,
                            anchor="middle"  # Centrar el título
                        ),
                        height=400,
                        width=700
                    ).interactive()

                    # Mostrar el gráfico en Streamlit
                    st.altair_chart(chart_inversion, use_container_width=True)

                # === SECCIÓN 6: Gráfica Comparativa con S&P 500 ===
                st.markdown(f"<div class='section-header'>📊 Comparativa con S&P 500</div>", unsafe_allow_html=True)
                st.markdown(f"""
                    A continuación, se muestra una gráfica comparativa entre el precio de **{symbol.upper()}** y el índice S&P 500.
                    Esto te permitirá ver cómo se ha comportado la acción en relación con el mercado en general.
                """)

                # Obtener datos históricos del S&P 500 (SPY)
                

                spy = yf.Ticker("SPY")
                spy_hist = spy.history(start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'))

                if not spy_hist.empty:
                    # Normalizar precios
                    df_action = hist[["Close"]].reset_index().rename(columns={"Close": f"{symbol.upper()}"}).set_index("Date")
                    df_spy = spy_hist[["Close"]].reset_index().rename(columns={"Close": "S&P 500 (SPY)"}).set_index("Date")
                    df_comparative = df_action.join(df_spy, how="inner")

                    # Preparar DataFrame para Altair
                    df_comparative_reset = df_comparative.reset_index()
                    df_melted = df_comparative_reset.melt(id_vars=["Date"], var_name="variable", value_name="value")

                    # Crear gráfico comparativo 
                    chart_comparative = alt.Chart(df_melted).mark_line(
                        strokeWidth=2.5,
                        opacity=0.85
                    ).encode(
                        x=alt.X('Date:T', title='Fecha'),
                        y=alt.Y('value:Q', title='Precio de Cierre'),
                        color=alt.Color('variable:N', title='Instrumento'),
                        tooltip=[
                            alt.Tooltip('Date:T', title='Fecha'),
                            alt.Tooltip('variable:N', title='Instrumento'),
                            alt.Tooltip('value:Q', title='Precio')
                        ]
                    ).properties(
                        title=alt.TitleParams(
                            text=f"Comparativa de Precios: {symbol.upper()} vs S&P 500",
                            fontSize=20,
                            anchor="middle"  # Centrar el título
                        ),
                        height=400,
                        width=700
                    ).interactive()

                    # Mostrar gráfico en Streamlit
                    st.altair_chart(chart_comparative, use_container_width=True)


                    st.markdown(f"""
                        **Explicación:**
                        - La gráfica muestra la evolución del precio de **{symbol.upper()}** y el índice S&P 500 (ETF SPY) en el mismo periodo.
                        - Al comparar ambos, puedes observar si la acción ha tenido un comportamiento superior o inferior al del mercado en general.
                    """)
                else:
                    st.warning("No se encontraron datos históricos del índice S&P 500 para graficar.")

                # === SECCIÓN 7: Modelo CAPM, Beta y Sharpe Ratio ===
                st.markdown(f"<div class='section-header'>📌 Modelo de Valoración de Activos Financieros (CAPM)</div>", unsafe_allow_html=True)

                st.markdown("""
                <div style='text-align: justify; font-size: 16px;'>
                El modelo <strong>CAPM (Capital Asset Pricing Model)</strong> estima el rendimiento esperado de una acción considerando su riesgo sistémico (beta),
                la tasa libre de riesgo y el rendimiento del mercado. Es útil para evaluar si una acción está sobrevalorada o subvalorada.
                </div>
                """, unsafe_allow_html=True)

                st.latex(r"""
                \text{CAPM} = \text{Tasa Libre de Riesgo} + \text{Beta} \times (\text{Rendimiento del Mercado} - \text{Tasa Libre de Riesgo})
                """)


                # === Ingreso de tasa libre de riesgo (en porcentaje) ===
                st.markdown("**Tasa libre de riesgo sugerida (bono del Tesoro a 10 años):** 4.43%")
                rf_input = st.number_input("Ingresa la tasa libre de riesgo (%)", min_value=0.0, max_value=15.0, value=4.43, step=0.01)  # en porcentaje
                rf = rf_input / 100  # convertir a decimal

                # === Obtener datos del índice S&P 500 (simbolizado como ^GSPC) ===
                sp500 = yf.Ticker("^GSPC")
                hist_sp500 = sp500.history(start=hist.index[0], end=hist.index[-1])
                if not hist_sp500.empty:
                    # Calcular retornos logarítmicos diarios
                    returns_stock = hist["Close"].pct_change().dropna()
                    returns_market = hist_sp500["Close"].pct_change().dropna()
                    df_returns = pd.DataFrame({"stock": returns_stock, "market": returns_market}).dropna()

                    # === Calcular Beta ===
                    cov_matrix = np.cov(df_returns["stock"], df_returns["market"])
                    beta = cov_matrix[0, 1] / cov_matrix[1, 1]

                    # === Calcular retorno del mercado anualizado ===
                    rm_annual = (1 + df_returns["market"].mean()) ** 252 - 1  # retorno del mercado
                    rm = rm_annual

                    # === Retorno esperado por CAPM ===
                    expected_return = rf + beta * (rm - rf)

                    # === Calcular Sharpe Ratio ===
                    stock_annual_return = (1 + df_returns["stock"].mean()) ** 252 - 1
                    stock_annual_std = np.std(df_returns["stock"]) * np.sqrt(252)
                    sharpe_ratio = (stock_annual_return - rf) / stock_annual_std

                   


                   # === Mostrar resultados con explicaciones y fórmulas ===
                    st.markdown(f"""
                    <ul style='font-size:16px;'>
                        <li><strong>Beta:</strong> {beta:.2f} <br>
                            <span style='color: #555;'>Mide la sensibilidad de la acción frente a los movimientos del mercado. Un beta mayor a 1 indica mayor volatilidad que el mercado, mientras que una beta menor a 1 indica menor volatilidad que el mercado.</span>
                        </li>
                    </ul>
                    """, unsafe_allow_html=True)

                

                    st.latex(r"""
                    \text{Beta} = \frac{\text{Covarianza de los rendimientos de la acción y del mercado}}{\text{Varianza de los rendimientos del mercado}}
                    """)

                    st.markdown(f"""
                    <ul style='font-size:16px;'>
                        <li><strong>Retorno del mercado (estimado):</strong> {rm*100:.2f}% <br>
                            <span style='color: #555;'>Es el rendimiento promedio que se espera obtener al invertir en el mercado en general, como el índice S&P 500.</span>
                        </li>
                        <li><strong>Retorno esperado (CAPM):</strong> {expected_return*100:.2f}% <br>
                            <span style='color: #555;'>Es el rendimiento teórico que un inversionista espera recibir por el riesgo asumido al invertir en una acción específica.</span>
                        </li>
                    </ul>
                    """, unsafe_allow_html=True)

                    st.markdown(f"""
                    <ul style='font-size:16px;'>
                        <li><strong>Sharpe Ratio:</strong> {sharpe_ratio:.2f} <br>
                            <span style='color: #555;'>Evalúa si el retorno adicional compensa adecuadamente el riesgo asumido. Cuanto mayor sea, mejor será la relación entre riesgo y retorno.</span>
                        </li>
                    </ul>
                    """, unsafe_allow_html=True)

                    st.latex(r"""
                    \text{Sharpe Ratio} = \frac{\text{Retorno esperado de la acción} - \text{Tasa libre de riesgo}}{\text{Desviación estándar de los rendimientos diarios} \times \sqrt{252}}
                    """)
                    
                else:
                    st.warning("No se pudo obtener datos del índice S&P 500.")
            

                
                # === SECCIÓN 8: Simulación Monte Carlo ===
                st.markdown(f"<div class='section-header'>🎲 Simulación Monte Carlo</div>", unsafe_allow_html=True)

                st.markdown(f"""
                <div style='text-align: justify; font-size: 16px;'>
                La <strong>simulación Monte Carlo</strong> permite estimar múltiples trayectorias posibles del precio futuro de una acción a través de escenarios aleatorios.
                Este método se basa en la <em>volatilidad histórica</em> y un supuesto de crecimiento promedio, generando muchas rutas posibles en el tiempo.

                Es útil para visualizar la incertidumbre y los rangos de precios posibles, ayudando en la toma de decisiones bajo riesgo.
            
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f"A continuación se visualiza la simulación Monte Carlo de **{symbol.upper()}**:")

                # Parámetros para la simulación
                num_simulaciones = 100
                num_dias = 252  # 1 año

                # Usar último precio de cierre
                ultimo_precio = hist["Close"].iloc[-1]

                # Rendimientos logarítmicos diarios
                log_returns = np.log(hist["Close"] / hist["Close"].shift(1)).dropna()
                media = log_returns.mean()
                vol = log_returns.std()

                # Simulación
                simulaciones = np.zeros((num_dias, num_simulaciones))
                for i in range(num_simulaciones):
                    precios = [ultimo_precio]
                    for _ in range(1, num_dias):
                        drift = media - 0.5 * vol**2
                        shock = np.random.normal(loc=0, scale=vol)
                        precio = precios[-1] * np.exp(drift + shock)
                        precios.append(precio)
                    simulaciones[:, i] = precios

                # Preparar DataFrame para Altair
                df_simulacion = pd.DataFrame(simulaciones)
                df_simulacion["Día"] = df_simulacion.index
                df_melted = df_simulacion.melt(id_vars=["Día"], var_name="Simulación", value_name="Precio")

                # Gráfico con Altair
                chart_mc = alt.Chart(df_melted).mark_line(
                    opacity=0.25,
                    strokeWidth=1.5,
                    color="#007B9E"  # color base azul elegante
                ).encode(
                    x=alt.X("Día:Q", title="Día"),
                    y=alt.Y("Precio:Q", title="Precio Simulado"),
                    detail="Simulación:N",
                    tooltip=[
                        alt.Tooltip("Día:Q", title="Día"),
                        alt.Tooltip("Precio:Q", title="Precio Simulado")
                    ]
                ).properties(
                    title=alt.TitleParams(
                        text=" Proyecciones de Precio con Simulación Monte Carlo (1 año)",
                        fontSize=20,
                        anchor="middle"
                    ),
                    height=400,
                    width=700
                ).interactive()

                # Mostrar en Streamlit
                st.altair_chart(chart_mc, use_container_width=True)

                # === RESUMEN DE RESULTADOS ===
                precios_finales = simulaciones[-1, :]
                precio_min = np.min(precios_finales)
                precio_max = np.max(precios_finales)
                percentil_5 = np.percentile(precios_finales, 5)
                percentil_95 = np.percentile(precios_finales, 95)

                st.markdown(f"""
                <div style='background-color:#f1f1f1; padding: 15px; border-radius: 10px; font-size: 16px;'>
                <b>📌 Resumen de resultados al final de 1 año:</b><br>
                - Precio mínimo simulado: <strong>${precio_min:,.2f}</strong><br>
                - Precio máximo simulado: <strong>${precio_max:,.2f}</strong><br>
                - Percentil 5: <strong>${percentil_5:,.2f}</strong><br>
                - Percentil 95: <strong>${percentil_95:,.2f}</strong>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("""
                <div style='text-align: justify; font-size: 15px;'>
                🔍 <strong>¿Qué significan los percentiles?</strong><br>
                El <strong>percentil 5</strong> representa el valor por debajo del cual se espera que caiga el 5% de las simulaciones; es decir, en un escenario pesimista, el precio podría caer por debajo de ese valor. 
                \n El <strong>percentil 95</strong> representa el valor por encima del cual solo el 5% de las simulaciones llegan; en un escenario muy optimista, el precio podría superar ese valor.
                </div>
                """, unsafe_allow_html=True)

                # === Sección 9: ANÁLISIS TÉCNICO ===
                st.markdown(f"<div class='section-header'>📊 Análisis Técnico de {symbol.upper()}</div>", unsafe_allow_html=True)

                # 1. Medias Móviles Simples (SMA)
                st.markdown("""
                ##### 📈 Medias Móviles Simples (SMA)
                Las <strong>medias móviles simples</strong> suavizan los movimientos del precio para identificar tendencias.
                <ul>
                <li><strong>SMA 50:</strong> Promedio de los últimos 50 días (corto plazo)</li>
                <li><strong>SMA 200:</strong> Promedio de los últimos 200 días (largo plazo)</li>
                </ul>
                """, unsafe_allow_html=True)

                hist["SMA_50"] = hist["Close"].rolling(window=50).mean()
                hist["SMA_200"] = hist["Close"].rolling(window=200).mean()

                #Gráfica
                base = alt.Chart(hist.reset_index()).transform_filter(
                    alt.datum["SMA_200"] != None
                )

                # Línea del precio de cierre
                line_price = base.mark_line(
                    color="#007B9E",  # Azul elegante
                    strokeWidth=2.5,
                    opacity=0.85
                ).encode(
                    x=alt.X("Date:T", title="Fecha"),
                    y=alt.Y("Close:Q", title="Precio"),
                    tooltip=[alt.Tooltip("Date:T", title="Fecha"), alt.Tooltip("Close:Q", title="Precio de Cierre")]
                )

                # Línea de SMA 50 (naranja)
                line_sma50 = alt.Chart(hist.reset_index()).mark_line(
                    color="orange",
                    strokeDash=[5, 5],
                    strokeWidth=2
                ).encode(
                    x="Date:T",
                    y="SMA_50:Q"
                )

                # Línea de SMA 200 (verde)
                line_sma200 = alt.Chart(hist.reset_index()).mark_line(
                    color="green",
                    strokeDash=[2, 2],
                    strokeWidth=2
                ).encode(
                    x="Date:T",
                    y="SMA_200:Q"
                )

                # Combinar todas
                sma_chart = (line_price + line_sma50 + line_sma200).properties(
                    title=alt.TitleParams(
                        text="Precio de Cierre con Medias Móviles (SMA 50 y SMA 200)",
                        fontSize=20,
                        anchor="middle"
                    ),
                    height=400,
                    width=700
                ).interactive()

                # Mostrar en Streamlit
                st.altair_chart(sma_chart, use_container_width=True)


                # Interpretación SMA
                st.markdown("Interpretación:")
                sma_50 = hist["SMA_50"].iloc[-1]
                sma_200 = hist["SMA_200"].iloc[-1]
                if sma_50 > sma_200:
                    st.markdown("🟢 La **SMA 50** está por encima de la **SMA 200**, lo que sugiere una <strong>tendencia alcista</strong> (cruce dorado).", unsafe_allow_html=True)
                elif sma_50 < sma_200:
                    st.markdown("🔴 La **SMA 50** está por debajo de la **SMA 200**, indicando una posible <strong>tendencia bajista</strong> (cruce de la muerte).", unsafe_allow_html=True)
                else:
                    st.markdown("⚪ Las SMAs están alineadas, sin una señal clara de tendencia.", unsafe_allow_html=True)

                # 2. Índice de Fuerza Relativa (RSI)
                st.markdown("""
                #### 💪 Índice de Fuerza Relativa (RSI)
                El <strong>RSI</strong> mide la magnitud de los cambios recientes en el precio para identificar condiciones de <em>sobrecompra</em> o <em>sobreventa</em>.
                <ul>
                <li>Valores sobre 70: posible <strong>sobrecompra</strong></li>
                <li>Valores bajo 30: posible <strong>sobreventa</strong></li>
                </ul>
                """, unsafe_allow_html=True)

                delta = hist["Close"].diff()
                ganancia = delta.where(delta > 0, 0.0)
                perdida = -delta.where(delta < 0, 0.0)

                media_ganancia = ganancia.rolling(window=14).mean()
                media_perdida = perdida.rolling(window=14).mean()

                rs = media_ganancia / media_perdida
                hist["RSI"] = 100 - (100 / (1 + rs))

                #Gráfica RSI
                rsi_chart = alt.Chart(hist.reset_index()).transform_filter(
                    alt.datum["RSI"] != None
                ).mark_line(
                    color="purple",
                    strokeWidth=2.5,
                    opacity=0.85
                ).encode(
                    x=alt.X("Date:T", title="Fecha"),
                    y=alt.Y("RSI:Q", title="Índice de Fuerza Relativa (RSI)"),
                    tooltip=[alt.Tooltip("Date:T", title="Fecha"), alt.Tooltip("RSI:Q", title="RSI")]
                ).properties(
                    title=alt.TitleParams(
                        text="Índice de Fuerza Relativa (RSI)",
                        fontSize=20,
                        anchor="middle"
                    ),
                    height=400,
                    width=700
                ).interactive()

                # Mostrar en Streamlit
                st.altair_chart(rsi_chart, use_container_width=True)


                # Interpretación RSI
                st.markdown("Interpretación:")
                rsi_actual = hist["RSI"].iloc[-1]
                if rsi_actual > 70:
                    st.markdown(f"🔴 El RSI actual es {rsi_actual:.2f}, lo que indica una posible <strong>sobrecompra</strong>.", unsafe_allow_html=True)
                elif rsi_actual < 30:
                    st.markdown(f"🟢 El RSI actual es {rsi_actual:.2f}, lo que indica una posible <strong>sobreventa</strong>.", unsafe_allow_html=True)
                else:
                    st.markdown(f"⚪ El RSI actual es {rsi_actual:.2f}, indicando una condición <strong>neutral</strong>.", unsafe_allow_html=True)

                # 3. Bandas de Bollinger
                st.markdown("""
                #### 📉 Bandas de Bollinger
                Las <strong>Bandas de Bollinger</strong> muestran niveles de precio relativos, calculando una media móvil (SMA 20) y sumando/restando dos desviaciones estándar.
                <ul>
                <li>Precio cerca de la banda superior: posible <strong>sobrecompra</strong></li>
                <li>Precio cerca de la banda inferior: posible <strong>sobreventa</strong></li>
                </ul>
                """, unsafe_allow_html=True)

                hist["SMA_20"] = hist["Close"].rolling(window=20).mean()
                hist["STD_20"] = hist["Close"].rolling(window=20).std()
                hist["Banda_Sup"] = hist["SMA_20"] + 2 * hist["STD_20"]
                hist["Banda_Inf"] = hist["SMA_20"] - 2 * hist["STD_20"]

                #Gráfica de Bandas de Bollinger
                base_bollinger = alt.Chart(hist.reset_index()).transform_filter(
                    alt.datum["SMA_20"] != None
                )

                # Precio de cierre
                precio_line = base_bollinger.mark_line(
                    color="#007B9E",
                    strokeWidth=2.5,
                    opacity=0.85
                ).encode(
                    x=alt.X("Date:T", title="Fecha"),
                    y=alt.Y("Close:Q", title="Precio de Cierre"),
                    tooltip=[
                        alt.Tooltip("Date:T", title="Fecha"),
                        alt.Tooltip("Close:Q", title="Precio de Cierre")
                    ]
                )

                # Media móvil 20 días (SMA 20)
                sma_line = alt.Chart(hist.reset_index()).mark_line(color="gray", strokeDash=[5, 5]).encode(
                    x="Date:T",
                    y="SMA_20:Q"
                )

                # Banda superior
                banda_sup = alt.Chart(hist.reset_index()).mark_line(color="green", strokeDash=[2, 2]).encode(
                    x="Date:T",
                    y="Banda_Sup:Q"
                )

                # Banda inferior
                banda_inf = alt.Chart(hist.reset_index()).mark_line(color="red", strokeDash=[2, 2]).encode(
                    x="Date:T",
                    y="Banda_Inf:Q"
                )

                # Composición del gráfico
                bollinger_chart = (precio_line + sma_line + banda_sup + banda_inf).properties(
                    title=alt.TitleParams(
                        text="📉 Bandas de Bollinger",
                        fontSize=20,
                        anchor="middle"
                    ),
                    height=400,
                    width=700
                ).interactive()

                # Mostrar en Streamlit
                st.altair_chart(bollinger_chart, use_container_width=True)


                # Interpretación Bollinger
                st.markdown("Interpretación:")
                precio_actual = hist["Close"].iloc[-1]
                banda_sup = hist["Banda_Sup"].iloc[-1]
                banda_inf = hist["Banda_Inf"].iloc[-1]

                if precio_actual > banda_sup:
                    st.markdown("🔺 El precio actual está por encima de la banda superior, lo que podría indicar <strong>sobrecompra o volatilidad alta</strong>.", unsafe_allow_html=True)
                elif precio_actual < banda_inf:
                    st.markdown("🔻 El precio actual está por debajo de la banda inferior, lo que podría sugerir <strong>sobreventa</strong> o una reversión potencial.", unsafe_allow_html=True)
                else:
                    st.markdown("⚪ El precio se encuentra dentro de las bandas, indicando <strong>comportamiento normal</strong>.", unsafe_allow_html=True)




        

            else:
                st.warning("No se encontraron datos históricos para graficar.")

    except Exception as e:
        st.error("No se pudo obtener información. Verifica el símbolo e intenta nuevamente.")


#Guardar datos en una variable
datos_empresa = {
    "Ticker": symbol,
    "Precio mínimo": precio_min,
    "Precio máximo": precio_max,
    "CAGR 1 año": cagr_results.get("1 año"),
    "CAGR 3 años": cagr_results.get("3 años"),
    "CAGR 5 años": cagr_results.get("5 años"),
    "Volatilidad 1 año": vol_results.get("1 año"),
    "Volatilidad 3 años": vol_results.get("3 años"),
    "Volatilidad 5 años": vol_results.get("5 años"),
    "Beta": beta,
    "Retorno del mercado": rm,
    "CAPM": expected_return,
    "Percentil 5": percentil_5,
    "Percentil 95": percentil_95,
    "SMA 50": sma_50,
    "SMA 200": sma_200,
    "RSI": rsi_actual
}


# Convertir el diccionario a un DataFrame de una sola fila
df_resultado = pd.DataFrame([datos_empresa])


st.markdown(f"<div class='section-header'> 🔍🧠 Recomendación de inversión</div>", unsafe_allow_html=True)


client = anthropic.Anthropic(
    api_key=api_key,
)

message = client.messages.create(
    model="claude-3-7-sonnet-20250219",
    max_tokens=20000,
    temperature=1,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text":f"Eres un agente de análisis financiero fundamental. Tu tarea es analizar los datos financieros proporcionados para una empresa específica y ofrecer una recomendación de inversión basada en tu análisis. Sigue estas instrucciones cuidadosamente:\n\n1. Lee atentamente los siguientes datos financieros:\n\n<financial_data>\n{df_resultado}\n</financial_data>\n\n2. Analiza los datos financieros proporcionados.\n\n3. Basándote en tu análisis, proporciona una recomendación de inversión. Tu recomendación debe ser una de las siguientes:\n   - Comprar\n   - Mantener\n   - Vender\n\n4. Justifica tu recomendación con un análisis detallado de los puntos fuertes y débiles de la empresa, basándote en los datos financieros proporcionados.\n\n5. Presenta tu respuesta en el siguiente formato:\n   \n   <analisis>\n   [Aquí, proporciona un análisis de 500 caracteres de los aspectos financieros clave de la empresa, destacando tanto los puntos fuertes como los débiles]\n   </analisis>\n\n   <recomendacion>\n   [Aquí, indica tu recomendación: Comprar, Mantener o Vender de esta manera: \"La recomendación es:\" con un punto al final]\n   </recomendacion>\n\n   <justificacion>\n   [Aquí, explica en detalle en 500 caracteres por qué has llegado a esta recomendación, basándote en tu análisis]\n   </justificacion>\n\nAl final haz una conclusión general resumida en 400 caracteres.\n\nRecuerda que tu análisis debe ser objetivo y basado únicamente en los datos financieros proporcionados. No hagas suposiciones sobre información que no se te ha proporcionado ni consideres factores externos como condiciones del mercado o noticias recientes."
                }
            ]
        }
    ]
)
# Mostrar recomendación de inversión
# Verifica y muestra el contenido generado por Claude
if message.content:
    try:
        # Si es una lista de bloques (lo más común)
        texto = "\n\n".join([bloque.text for bloque in message.content if bloque.type == "text"])
        st.markdown(texto, unsafe_allow_html=True)  # Permite mejor formato visual
    except Exception as e:
        st.error(f"Error al procesar el contenido: {e}")
        st.write(message.content)
else:
    st.warning("No se recibió contenido del modelo.")


# Guardar en un archivo CSV
df_resultado.to_csv("datos_analisis_empresa.csv", index=False, encoding="utf-8-sig")

st.success("✅ Los datos se ha exportado exitosamente como 'datos_analisis_empresa.csv'")

with open("datos_analisis_empresa.csv", "rb") as file:
    st.download_button(
        label="📥 Descargar datos en CSV",
        data=file,
        file_name="datos_analisis_empresa.csv",
        mime="text/csv"
    )
