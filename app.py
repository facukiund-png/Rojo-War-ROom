import streamlit as st
import pandas as pd
import feedparser
import datetime
import numpy as np
import urllib.parse
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import random
import time
import folium
from streamlit_folium import st_folium

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="ROJO WAR ROOM",
    page_icon="👹",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo CSS personalizado
st.markdown("""
<style>
    .big-font { font-size:20px !important; font-weight: bold; }
    .alert { color: #ff4b4b; font-weight: bold; }
    .stButton>button { width: 100%; border-radius: 5px; }
    div[data-testid="stMetricValue"] { font-size: 24px; color: #e63946; }
    
    /* ESTILO DEL TICKER */
    .ticker-wrap {
        width: 100%;
        overflow: hidden;
        background-color: #b71c1c; 
        padding: 12px;
        white-space: nowrap;
        box-sizing: border-box;
        border-radius: 5px;
        margin-bottom: 20px;
        border-left: 10px solid #ffffff;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .ticker {
        display: inline-block;
        white-space: nowrap;
        animation: ticker 90s linear infinite;
    }
    .ticker-item {
        display: inline-block;
        padding: 0 3rem;
        font-size: 22px; 
        font-weight: 800;
        color: #ffffff !important; 
        font-family: 'Arial Black', sans-serif;
        text-transform: uppercase;
    }
    @keyframes ticker {
        0% { transform: translate3d(100%, 0, 0); }
        100% { transform: translate3d(-100%, 0, 0); }
    }
</style>
""", unsafe_allow_html=True)

# --- FUNCIONES AUXILIARES (MOTOR DE BÚSQUEDA CON FILTROS DE CATEGORÍA) ---

@st.cache_data(ttl=300) 
def buscar_noticias_rss(filtro_categoria="Todas"):
    """
    Motor de Búsqueda que acepta CATEGORÍAS específicas.
    """
    
    # 1. DICCIONARIO DE FILTROS (Aquí definimos qué busca cada botón)
    filtros = {
        "Todas": 'Avellaneda OR Fútbol OR Club OR "El Rojo" OR "Rey de Copas" OR Liga OR Copa OR Vaccari OR Grindetti OR Reserva OR Futsal OR Deuda OR Inhibición',
        
        "Fútbol Profesional": 'Vaccari OR "Liga Profesional" OR "Copa Argentina" OR Partido OR Gol OR Formación OR "11 titular" OR "Mercado de Pases" OR Refuerzos OR "Ficha técnica"',
        
        "Institución": 'Sede OR Asamblea OR Socios OR Cuota OR "Campaña de Socios" OR Obras OR "Convocatoria" OR Elecciones OR Estatuto OR Balance',
        
        "Economía/Judicial": 'Inhibición OR Deuda OR Embargo OR FIFA OR TAS OR Dólares OR "Banco Central" OR Pagos OR Juicio OR Acreedores OR Cheques',
        
        "Jugadores": 'Mancuello OR Ávalos OR "Santi López" OR Rey OR Laso OR "Saltita González" OR Loyola OR Sporle OR Canelo OR "Tata Martínez"',
        
        "Dirigentes": 'Grindetti OR Seoane OR Damiani OR "Comisión Directiva" OR "Secretario General" OR Marconi OR "Mesa Chica"',
        
        "Otros Deportes": 'Reserva OR Futsal OR Basquet OR "Fútbol Femenino" OR Inferiores OR Wilde OR "Villa Domínico" OR Hockey'
    }

    # Seleccionamos las palabras clave según lo que eligió el usuario en el sidebar
    contexto_seleccionado = filtros.get(filtro_categoria, filtros["Todas"])

    # 2. EXCLUSIÓN (Anti-Política Nacional)
    exclusion = (
        '-Diputados -Senadores -"Partido Independiente" -"Cine Independiente" '
        '-"Música Independiente" -Santa -Medellin -Rivadavia -Chivilcoy -Neuquen -Petrolero -Jujuy'
    )

    # 3. CONSTRUCCIÓN DE LA QUERY
    # Query: "Independiente" AND (Palabras Clave de la Categoría) AND NOT (Exclusiones)
    base_query = f'"Independiente" AND ({contexto_seleccionado}) {exclusion}'

    # 4. FECHA: Últimos 2 días
    encoded_query = urllib.parse.quote(base_query + " when:2d")
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=es-419&gl=AR&ceid=AR:es-419"
    
    try:
        feed = feedparser.parse(url)
        noticias = []
        if feed.entries:
            for entry in feed.entries:
                noticias.append({
                    'titulo': entry.title,
                    'link': entry.link,
                    'fecha': entry.published,
                    'fecha_obj': entry.published_parsed, 
                    'fuente': entry.source.title if 'source' in entry else 'Google News'
                })
            
            # Ordenar por fecha real
            noticias.sort(key=lambda x: x['fecha_obj'], reverse=True)
            
        return noticias
    except:
        return []

def generar_link_whatsapp(texto):
    """Crea un link para compartir en WhatsApp"""
    base_url = "https://wa.me/?text="
    encoded_text = urllib.parse.quote(texto)
    return base_url + encoded_text

# --- SIDEBAR (Barra Lateral con Filtros) ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/d/db/Club_Atl%C3%A9tico_Independiente_logo_%282008-present%29.png", width=100)
    st.title("COMANDO ROJO")
    
    # --- SECCIÓN DE FILTROS AL COSTADO ---
    st.divider()
    st.header("🔍 Filtros de Noticias")
    categoria_seleccionada = st.radio(
        "Ver noticias sobre:",
        ["Todas", "Fútbol Profesional", "Institución", "Economía/Judicial", "Jugadores", "Dirigentes", "Otros Deportes"]
    )
    st.divider()
    
    if st.button("🔄 ACTUALIZAR DATOS"):
        st.cache_data.clear()
        st.rerun()

    st.subheader("📆 Próximos Partidos")
    partidos = pd.DataFrame({
        "Rival": ["Racing (V)", "River (L)", "Belgrano (V)"],
        "Fecha": ["Dom 15/12", "Dom 22/12", "Mie 25/12"],
        "Torneo": ["Liga", "Liga", "Copa"]
    })
    st.table(partidos)

# --- CUERPO PRINCIPAL (PESTAÑAS) ---
tab_alertas, tab_medios, tab_politica, tab_twitter, tab_clipping, tab_estrategia, tab_territorio, tab_ia, tab_mapa = st.tabs([
    "🚨 ALERTAS", "📰 MEDIOS", "🗳️ POLÍTICA", "🐦 TWITTER", "📝 CLIPPING", "🧠 ESTRATEGIA", "🗺️ TERRITORIO", "🦎 DISCURSO POLIMÓRFICO", "📍 DOMINACIÓN VISUAL"
])

# 1. PESTAÑA ALERTAS URGENTES
with tab_alertas:
    # --- TICKER (SIEMPRE MUESTRA TODO, NO FILTRA PARA NO PERDER ALERTAS) ---
    noticias_ticker = buscar_noticias_rss("Todas") 
    if noticias_ticker:
        textos_ticker = [f"👹 {n['titulo']}" for n in noticias_ticker[:10]]
        string_ticker = "   ----------   ".join(textos_ticker)
    else:
        string_ticker = "🔴 Sin noticias recientes en el radar."
        
    st.markdown(f"""
    <div class="ticker-wrap">
        <div class="ticker">
            <div class="ticker-item">{string_ticker}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- CUERPO DE NOTICIAS (FILTRADO POR EL SIDEBAR) ---
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader(f"🔥 Noticias: {categoria_seleccionada}")
        
        # AQUÍ USAMOS LA CATEGORÍA DEL SIDEBAR
        noticias_filtradas = buscar_noticias_rss(categoria_seleccionada)
        
        if noticias_filtradas:
            for n in noticias_filtradas[:20]: 
                with st.container(border=True):
                    col_ico, col_txt = st.columns([0.1, 0.9])
                    with col_ico:
                        # Iconos visuales según contexto
                        title_lower = n['titulo'].lower()
                        if "inhibi" in title_lower or "deuda" in title_lower or "embargo" in title_lower:
                            st.markdown("### 💸")
                        elif "gol" in title_lower or "ganó" in title_lower or "empate" in title_lower:
                            st.markdown("### ⚽")
                        elif "lesión" in title_lower:
                            st.markdown("### 🚑")
                        elif "grindetti" in title_lower or "seoane" in title_lower:
                            st.markdown("### 👔")
                        else:
                            st.markdown("### 📰")
                            
                    with col_txt:
                        st.markdown(f"**[{n['titulo']}]({n['link']})**")
                        st.caption(f"🕒 {n['fecha']} | 📰 {n['fuente']}")
        else:
            st.info(f"No se encontraron noticias recientes en la categoría '{categoria_seleccionada}'. Intenta con 'Todas'.")
            
    with col2:
        st.warning("⚠️ PANEL DE CONTROL")
        st.metric(label="Noticias Visibles", value=len(noticias_filtradas) if noticias_filtradas else 0)
        st.markdown(f"""
        **Filtro Activo:**
        * 🎯 {categoria_seleccionada}
        """)

# 2. PESTAÑA MEDIOS
with tab_medios:
    st.header("📰 Kiosco Digital")
    filtro_medios = st.radio("Fuente:", ["Nacionales", "Partidarios", "Mercado de Pases"], horizontal=True)
    
    query = ""
    if filtro_medios == "Nacionales":
        query = 'site:ole.com.ar OR site:tycsports.com OR site:infobae.com OR site:lanacion.com.ar OR site:clarin.com'
    elif filtro_medios == "Partidarios":
        query = '(Infierno Rojo OR De la Cuna al Infierno OR Soy del Rojo OR LocoXelRojo OR "Muy Independiente")'
    else:
        query = '(Refuerzos OR Transferencias OR "Mercado de Pases" OR "Altas y Bajas" OR Contrato OR Firma)'
    
    # Aquí buscamos "Independiente" + el medio
    encoded_query = urllib.parse.quote(f'"Independiente" AND {query} when:2d')
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=es-419&gl=AR&ceid=AR:es-419"
    
    feed = feedparser.parse(url)
    noticias = []
    if feed.entries:
         for entry in feed.entries:
             noticias.append(entry)
    
    if noticias:
        for n in noticias[:10]:
            with st.expander(f"{n.title}"):
                st.write(f"Fuente: {n.source.title if 'source' in n else 'Google'}")
                st.markdown(f"**[🔗 LEER NOTA COMPLETA]({n.link})**")
    else:
        st.info("No se encontraron noticias recientes en esta categoría.")

# 3. PESTAÑA POLÍTICA
with tab_politica:
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.subheader("🕵️ Oficialismo")
        # Usamos la funcion general forzando categoria Dirigentes + apellido
        # (Simplificado para este ejemplo, busca especifico)
        pass 
        st.info("Consulta la pestaña ALERTAS > Dirigentes para ver novedades.")

    with col_p2:
        st.subheader("🥊 Oposición")
        st.info("Consulta la pestaña ALERTAS > Dirigentes para ver novedades.")
            
    st.divider()
    st.subheader("📂 Archivos X (Dossier)")
    perfil = st.selectbox("Seleccionar Perfil:", ["Néstor G. (Presidente)", "Hugo M. (Ex-Pres)", "Fabián D. (Ex-Pres)"])
    
    if perfil == "Néstor G. (Presidente)":
        with st.expander("Ver Ficha Técnica", expanded=True):
            st.markdown("""
            - **Cargo:** Presidente (En licencia en Lanús).
            - **Fortaleza:** Vínculos políticos nacionales.
            - **Debilidad:** Ausencia en el día a día.
            - **Amenaza Electoral:** ALTA.
            """)
            st.progress(80, text="Nivel de Influencia")

# 4. PESTAÑA TWITTER
with tab_twitter:
    st.header("🐦 Radar X (En Vivo)")
    st.info("Estos botones abren búsquedas filtradas en tiempo real en X (Twitter).")
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.link_button("🔥 Buscar 'Independiente' (Reciente)", "https://twitter.com/search?q=Independiente&src=typed_query&f=live")
        st.link_button("📈 Buscar '#TodoRojo' (Populares)", "https://twitter.com/search?q=%23TodoRojo%20min_faves%3A50&src=typed_query&f=live")
    with col_t2:
        st.link_button("🗳️ Menciones 'Marchese'", "https://twitter.com/search?q=Gonzalo%20Marchese%20Independiente&src=typed_query&f=live")
        st.link_button("🥊 Menciones 'Grindetti' (Videos)", "https://twitter.com/search?q=Grindetti%20Independiente%20filter%3Avideos&src=typed_query&f=live")

# 5. PESTAÑA CLIPPING
with tab_clipping:
    st.header("📝 Generador de Mensajes")
    texto_clipping = st.text_area("Pega aquí el link o noticia:", height=100)
    analisis = st.selectbox("Etiqueta:", ["⚠️ URGENTE", "✅ BUENA NOTICIA", "❌ FAKE NEWS", "ℹ️ INFO"])
    
    if texto_clipping:
        mensaje_final = f"*{analisis}*\n\n{texto_clipping}\n\n_Reporte Rojo War Room_"
        st.code(mensaje_final, language="markdown")
        
        if st.button("📲 Generar Link de WhatsApp"):
            link = generar_link_whatsapp(mensaje_final)
            st.success("Link generado! Haz clic abajo:")
            st.markdown(f"## [👉 ENVIAR POR WHATSAPP]({link})")

# 6. PESTAÑA ESTRATEGIA
with tab_estrategia:
    subtab_sim, subtab_log = st.tabs(["🧮 SIMULADOR ELECTORAL", "🛡️ LOGÍSTICA DIA D"])
    with subtab_sim:
        st.subheader("Simulador de Votos")
        col_sim1, col_sim2 = st.columns(2)
        with col_sim1:
            votos_vitalicios = st.slider("Votos Vitalicios", 0, 5000, 2500)
            votos_activos = st.slider("Votos Activos", 0, 20000, 12000)
            participacion = st.slider("Participación (%)", 0, 100, 65)
        with col_sim2:
            total_votos = (votos_vitalicios + votos_activos) * (participacion/100)
            data_votos = pd.DataFrame({
                "Agrupación": ["Oficialismo", "Revolución (Nosotros)", "Otras"],
                "Votos": [total_votos * 0.35, total_votos * 0.45, total_votos * 0.20]
            })
            st.bar_chart(data_votos.set_index("Agrupación"))
            st.metric("Votos Totales Estimados", int(total_votos))
    with subtab_log:
        st.subheader("Calculadora Operativa")
        mesas = st.number_input("Mesas Habilitadas", value=150)
        fiscales = st.number_input("Fiscales por mesa", value=2)
        st.metric("Total Fiscales Necesarios", mesas * fiscales)

# 7. PESTAÑA TERRITORIO
with tab_territorio:
    col_terr1, col_terr2 = st.columns([2, 1])
    with col_terr1:
        st.subheader("🗺️ Mapa de Socios (Simulado)")
        data_mapa = pd.DataFrame({
            'lat': np.random.normal(-34.6702, 0.01, 100),
            'lon': np.random.normal(-58.3709, 0.01, 100)
        })
        st.map(data_mapa)
    with col_terr2:
        st.subheader("☁️ Temas del Día")
        text = "Independiente Rojo Avellaneda Vaccari Ganar Copa Sudamericana Bochini Deuda Aguero Maratea Socios"
        wordcloud = WordCloud(width=400, height=400, background_color='black', colormap='Reds').generate(text)
        fig, ax = plt.subplots()
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis("off")
        st.pyplot(fig)

# 8. PESTAÑA DISCURSO POLIMÓRFICO
with tab_ia:
    st.header("🦎 Discurso Polimórfico")
    st.info("Herramienta de adaptación de tono estratégico.")
    col_ia1, col_ia2 = st.columns([1, 1])
    with col_ia1:
        st.subheader("1. Configuración")
        idea_base = st.text_area("Escribe la idea central (cruda):", "Tenemos que sacar a los que le hacen mal al club y arreglar la cancha", height=100)
        target = st.select_slider(
            "Seleccionar Público Objetivo:", 
            options=["Socios Vitalicios (Formal)", "Prensa (Técnico)", "Redes (Viral)", "Barra/Tablón (Agresivo)"]
        )
        generar = st.button("✨ Procesar Estrategia")
    with col_ia2:
        st.subheader("2. Resultado Generado")
        if generar:
            with st.spinner("Analizando tono y reescribiendo..."):
                time.sleep(2)
                resultado = ""
                if target == "Socios Vitalicios (Formal)":
                    resultado = f"Estimada familia Roja:\n\nLa historia de nuestra institución nos exige responsabilidad y memoria. {idea_base}. Es un imperativo moral recuperar la gloria y la infraestructura que ustedes construyeron. Volvamos a las raíces."
                elif target == "Prensa (Técnico)":
                    resultado = f"DECLARACIÓN OFICIAL:\n\nDesde la agrupación sostenemos que {idea_base}. Esto es parte de un plan integral de saneamiento basado en los artículos 45 y 46 del estatuto vigente."
                elif target == "Redes (Viral)":
                    resultado = f"Basta de mentiras. 🛑\n\n{idea_base}. \n\nSi estás de acuerdo dale RT. #TodoRojo 👹"
                else: 
                    resultado = f"Escuchen bien todos:\n\n{idea_base}.\n\nAl que no le guste, que se vaya. ¡Aca se viene a alentar y a ganar! ¡VAMOS ROJO CARAJO!"
                st.success("✅ Mensaje Adaptado Exitosamente")
                st.code(resultado, language="text")

# 9. PESTAÑA DOMINACIÓN VISUAL (MAPA TÁCTICO)
with tab_mapa:
    st.header("📍 Rutas de Dominación Visual (Avellaneda)")
    st.markdown("Algoritmo de optimización de vía pública basado en **Tráfico + Peatones + Hinchas**.")
    col_map1, col_map2 = st.columns([1, 3])
    with col_map1:
        st.subheader("⚙️ Calibración")
        peso_trafico = st.slider("Importancia Tráfico (Autos)", 0, 10, 8)
        peso_peatones = st.slider("Importancia Peatones", 0, 10, 6)
        peso_hinchas = st.slider("Importancia Mundo Rojo", 0, 10, 10)
    with col_map2:
        puntos_estrategicos = [
            ("Sede Av. Mitre 470", -34.6624, -58.3649, 9, 10, 10),
            ("Estadio LDA - Bochini", -34.6702, -58.3711, 6, 8, 10),
            ("Alto Avellaneda (Ingreso)", -34.6755, -58.3665, 9, 10, 4),
            ("Estación Avellaneda (K. Kosteki)", -34.6566, -58.3813, 10, 10, 5),
            ("Mitre y Las Flores (Wilde)", -34.7001, -58.3215, 10, 10, 8),
            ("Av. Belgrano y Italia", -34.6631, -58.3622, 9, 7, 6),
            ("Bajada Pte. Pueyrredón", -34.6548, -58.3755, 10, 1, 3),
            ("Plaza Alsina", -34.6611, -58.3661, 7, 9, 7),
            ("Predio Wilde", -34.7045, -58.3031, 5, 4, 10),
            ("Crucecita (Mitre y Pavón)", -34.6690, -58.3580, 10, 5, 5),
            ("Hospital Fiorito", -34.6580, -58.3705, 7, 9, 4),
            ("Walmart/Parque Comercial", -34.6720, -58.3550, 8, 8, 3),
            ("Gerli (Puente)", -34.6850, -58.3650, 8, 3, 6),
            ("Villa Dominico (Parque)", -34.6900, -58.3400, 6, 8, 7),
            ("Av. Roca y Debenedetti", -34.6650, -58.3450, 8, 5, 4)
        ]
        m = folium.Map(location=[-34.6700, -58.3600], zoom_start=13, tiles="CartoDB dark_matter")
        ranking = []
        for nombre, lat, lon, tr, pe, hi in puntos_estrategicos:
            score = (tr * peso_trafico) + (pe * peso_peatones) + (hi * peso_hinchas)
            max_posible = (10 * peso_trafico) + (10 * peso_peatones) + (10 * peso_hinchas)
            porcentaje = int((score / max_posible) * 100)
            ranking.append({"Lugar": nombre, "Efectividad": porcentaje})
            color = "green"
            radius = 5
            if porcentaje > 80:
                color = "#e63946" 
                radius = 15
            elif porcentaje > 60:
                color = "orange"
                radius = 10
            html = f"""
            <div style='font-family:sans-serif; width:200px'>
                <h4 style='color:black; margin-bottom:5px'>{nombre}</h4>
                <b style='color:red; font-size:16px'>EFECTIVIDAD: {porcentaje}%</b><br>
                🚗 Tráfico: {tr}/10<br>
                🚶 Peatones: {pe}/10<br>
                👹 Mundo Rojo: {hi}/10<br>
            </div>
            """
            folium.CircleMarker(
                location=[lat, lon],
                radius=radius,
                popup=folium.Popup(html, max_width=250),
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7
            ).add_to(m)
        st_folium(m, width=800, height=500)
    st.subheader("🏆 Top Ubicaciones para Vía Pública")
    df_ranking = pd.DataFrame(ranking).sort_values(by="Efectividad", ascending=False)
    st.dataframe(df_ranking, column_config={"Efectividad": st.column_config.ProgressColumn("Nivel de Impacto", format="%d%%", min_value=0, max_value=100)}, hide_index=True, use_container_width=True)

# Footer
st.markdown("---")
st.caption("🔒 Rojo War Room v1.0 | Uso exclusivo Jefatura de Campaña")
