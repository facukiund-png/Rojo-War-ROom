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
    initial_sidebar_state="collapsed"
)

# --- ESTILOS CSS (Ticker, Paneles, Métricas) ---
st.markdown("""
<style>
    .big-font { font-size:20px !important; font-weight: bold; }
    .stButton>button { width: 100%; border-radius: 5px; }
    div[data-testid="stMetricValue"] { font-size: 24px; color: #e63946; }
    
    /* TICKER (Cinta de Noticias) */
    .ticker-wrap {
        width: 100%;
        background-color: #b71c1c; 
        padding: 8px; 
        overflow: hidden;
        white-space: nowrap;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        margin-bottom: 20px;
        border-bottom: 3px solid #7f1d1d;
    }
    .ticker-content {
        display: inline-block;
        white-space: nowrap;
        animation: ticker-animation 90s linear infinite; /* Velocidad media */
        font-family: 'Arial', sans-serif;
        font-size: 18px;
        font-weight: bold;
        color: #ffffff;
    }
    @keyframes ticker-animation {
        0% { transform: translateX(100%); }
        100% { transform: translateX(-100%); }
    }
    
    /* PANEL DERECHO DE FILTROS */
    .right-panel {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 8px;
        border-left: 5px solid #e63946;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        height: 100%;
    }
    
    /* TARJETAS DE DEFENSA */
    .defense-card { 
        background-color: #262730; 
        padding: 15px; 
        border-radius: 10px; 
        border-left: 5px solid #e63946; 
        margin-bottom: 10px; 
    }
</style>
""", unsafe_allow_html=True)

# --- MOTOR DE BÚSQUEDA DE NOTICIAS (V6 - BLINDADO) ---

@st.cache_data(ttl=60, show_spinner=False)
def buscar_noticias_rss(categoria="Todas", timestamp_force=0):
    
    # LISTA NEGRA (Filtrar homónimos)
    exclusion = (
        '-Rivadavia -Mendoza -Chivilcoy -Neuquen -Petrolero -Jujuy -Tandil -Trelew -Oliva '
        '-"Del Valle" -Medellin -"Santa Fe" -Bogota -Ecuador -Bolivia -Spain -España '
        '-Diputados -Senadores -"Partido Independiente" -Cine -Música -Regional -Amateur -Federal '
        '-"Juventud Independiente" -Alicante -Siguatepeque -Panama'
    )
    
    contexto_rojo = '(Avellaneda OR "El Rojo" OR "Rey de Copas" OR "CAI" OR "Libertadores de América" OR "Diablos Rojos" OR Bochini)'

    queries = []
    
    if categoria == "Todas":
        queries = [
            f'"Club Atlético Independiente" {exclusion}', 
            f'"Independiente" AND {contexto_rojo} {exclusion}',
            f'"Independiente" AND (Vaccari OR Grindetti OR "Mercado de Pases") {exclusion}'
        ]
    elif categoria == "Fútbol Profesional":
        queries = [
            f'"Independiente" AND (Vaccari OR Formación OR "11 titular" OR Partido OR Gol OR "Liga Profesional") {exclusion}',
            f'"Independiente" AND (Refuerzos OR "Mercado de Pases" OR Transferencia) {exclusion}'
        ]
    elif categoria == "Institución":
        queries = [
            f'"Independiente" AND (Grindetti OR Seoane OR "Comisión Directiva" OR Asamblea OR Balance OR Elecciones OR Sede) {exclusion}'
        ]
    elif categoria == "Economía":
        queries = [
            f'"Independiente" AND (Inhibición OR Deuda OR Embargo OR FIFA OR TAS OR Dólares OR Banco OR Cheques OR Juicio) {exclusion}'
        ]

    noticias_totales = []
    links_vistos = set()

    for q in queries:
        encoded_query = urllib.parse.quote(q + " when:3d")
        rand_param = random.randint(1, 999999) # Anti-cache
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=es-419&gl=AR&ceid=AR:es-419&nocache={rand_param}"
        
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                if entry.link not in links_vistos:
                    # Filtro extra de seguridad en Python
                    titulo = entry.title.lower()
                    if "rivadavia" in titulo or "del valle" in titulo or "juventud" in titulo:
                        continue
                        
                    noticias_totales.append({
                        'titulo': entry.title,
                        'link': entry.link,
                        'fecha': entry.published,
                        'fecha_obj': entry.published_parsed, 
                        'fuente': entry.source.title if 'source' in entry else 'Google News'
                    })
                    links_vistos.add(entry.link)
        except:
            continue

    # Backup si falla todo
    if not noticias_totales:
        try:
            url_backup = "https://news.google.com/rss/search?q=%22Independiente+Avellaneda%22+when:1d&hl=es-419&gl=AR&ceid=AR:es-419"
            feed = feedparser.parse(url_backup)
            for entry in feed.entries:
                if entry.link not in links_vistos:
                    noticias_totales.append({
                        'titulo': entry.title,
                        'link': entry.link,
                        'fecha': entry.published,
                        'fecha_obj': entry.published_parsed, 
                        'fuente': 'Google News Backup'
                    })
        except:
            pass

    # Ordenar por fecha
    noticias_totales.sort(key=lambda x: x['fecha_obj'] if x['fecha_obj'] else time.localtime(), reverse=True)
    
    return noticias_totales

def generar_link_whatsapp(texto):
    base_url = "https://wa.me/?text="
    encoded_text = urllib.parse.quote(texto)
    return base_url + encoded_text

# --- CABECERA Y TÍTULO ---
c_logo, c_title = st.columns([0.05, 0.95])
with c_logo:
    st.image("https://upload.wikimedia.org/wikipedia/commons/d/db/Club_Atl%C3%A9tico_Independiente_logo_%282008-present%29.png", width=50)
with c_title:
    st.markdown("### COMANDO ROJO | WAR ROOM")

# --- TICKER DE NOTICIAS ---
noticias_ticker = buscar_noticias_rss("Todas", int(time.time()))
if noticias_ticker:
    textos_ticker = [f"👹 {n['titulo']}" for n in noticias_ticker[:10]]
    string_ticker = "   •   ".join(textos_ticker)
else:
    string_ticker = "🔴 Inicializando sistemas de inteligencia... Conectando con satélite..."

st.markdown(f"""
<div class="ticker-wrap">
    <div class="ticker-content">
        {string_ticker}
    </div>
</div>
""", unsafe_allow_html=True)

# --- PESTAÑAS (TODAS RESTAURADAS) ---
tab_alertas, tab_medios, tab_politica, tab_twitter, tab_clipping, tab_estrategia, tab_territorio, tab_ia, tab_mapa, tab_defensa = st.tabs([
    "🚨 ALERTAS", "📰 MEDIOS", "🗳️ POLÍTICA", "🐦 TWITTER", "📝 CLIPPING", "🧠 ESTRATEGIA", "🗺️ TERRITORIO", "🦎 DISCURSO", "📍 DOMINACIÓN", "🛡️ DEFENSA"
])

# 1. PESTAÑA ALERTAS (NOTICIAS)
with tab_alertas:
    col_main, col_right = st.columns([0.75, 0.25])
    
    # --- PANEL DERECHO (FILTROS) ---
    with col_right:
        st.markdown('<div class="right-panel">', unsafe_allow_html=True)
        st.subheader("⚙️ Filtros")
        filtro_tema = st.radio(
            "Ver noticias de:",
            ["Todas", "Fútbol Profesional", "Institución", "Economía"],
            key="filtro_alertas"
        )
        st.divider()
        if st.button("🔄 ACTUALIZAR AHORA", type="primary"):
            st.cache_data.clear()
            st.rerun()
        st.caption(f"Última carga: {datetime.datetime.now().strftime('%H:%M')}")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- PANEL IZQUIERDO (NOTICIAS) ---
    with col_main:
        st.subheader(f"🔥 Últimas Novedades: {filtro_tema}")
        feed_noticias = buscar_noticias_rss(filtro_tema, int(time.time()))
        
        if feed_noticias:
            for n in feed_noticias[:20]:
                with st.container(border=True):
                    c1, c2 = st.columns([0.05, 0.95])
                    with c1:
                        # Iconos
                        t = n['titulo'].lower()
                        if "inhibi" in t or "deuda" in t: st.write("💸")
                        elif "ganó" in t or "gol" in t: st.write("⚽")
                        elif "grindetti" in t: st.write("👔")
                        else: st.write("📰")
                    with c2:
                        st.markdown(f"**[{n['titulo']}]({n['link']})**")
                        # Tiempo relativo
                        try:
                            fecha_dt = datetime.datetime(*n['fecha_obj'][:6])
                            ahora = datetime.datetime.now()
                            diff = ahora - fecha_dt
                            if diff.days == 0: hace = f"Hace {diff.seconds // 3600}h"
                            else: hace = f"Hace {diff.days}d"
                        except: hace = "Reciente"
                        st.caption(f"🕒 {hace} | {n['fuente']}")
        else:
            st.info("No se encontraron noticias recientes. Intenta el botón 'Actualizar Ahora'.")

# 2. PESTAÑA MEDIOS
with tab_medios:
    st.header("📰 Kiosco Digital")
    filtro_medios = st.radio("Fuente:", ["Nacionales", "Partidarios", "Mercado de Pases"], horizontal=True)
    
    query = ""
    if filtro_medios == "Nacionales":
        query = 'site:ole.com.ar OR site:tycsports.com OR site:infobae.com OR site:lanacion.com.ar'
    elif filtro_medios == "Partidarios":
        query = '(Infierno Rojo OR De la Cuna al Infierno OR Soy del Rojo OR LocoXelRojo)'
    else:
        query = '(Refuerzos OR Transferencias OR "Mercado de Pases")'
    
    encoded_query = urllib.parse.quote(f'"Independiente" AND {query} when:3d')
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=es-419&gl=AR&ceid=AR:es-419"
    
    try:
        feed = feedparser.parse(url)
        if feed.entries:
            for n in feed.entries[:10]:
                with st.expander(f"{n.title}"):
                    st.markdown(f"**[🔗 LEER NOTA]({n.link})**")
        else:
            st.info("Sin noticias recientes.")
    except:
        pass

# 3. PESTAÑA POLÍTICA
with tab_politica:
    st.header("🗳️ Tablero Político")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🕵️ Oficialismo")
        st.info("Monitoreando declaraciones de Grindetti y Seoane...")
        # (Aquí podrías agregar una búsqueda RSS específica de Grindetti si quisieras)
    with c2:
        st.subheader("🥊 Oposición")
        st.info("Monitoreando movimientos de Doman, Ducatenzeiler y Listas opositoras...")
    
    st.divider()
    st.subheader("📂 Archivos X (Dossier)")
    perfil = st.selectbox("Seleccionar Perfil:", ["Néstor G. (Presidente)", "Hugo M. (Ex-Pres)", "Fabián D. (Ex-Pres)"])
    if perfil == "Néstor G. (Presidente)":
        with st.expander("Ver Ficha Técnica", expanded=True):
            st.markdown("""
            - **Cargo:** Presidente (En licencia en Lanús).
            - **Fortaleza:** Vínculos políticos nacionales.
            - **Debilidad:** Ausencia en el día a día del club.
            - **Amenaza Electoral:** ALTA.
            """)
            st.progress(80, text="Nivel de Influencia")

# 4. PESTAÑA TWITTER
with tab_twitter:
    st.header("🐦 Radar X (En Vivo)")
    st.info("Accesos directos a búsquedas filtradas.")
    c_t1, c_t2 = st.columns(2)
    with c_t1:
        st.link_button("🔥 'Independiente' (Live)", "https://twitter.com/search?q=Independiente&src=typed_query&f=live")
        st.link_button("📈 '#TodoRojo' (Populares)", "https://twitter.com/search?q=%23TodoRojo%20min_faves%3A50&src=typed_query&f=live")
    with c_t2:
        st.link_button("🗳️ Menciones Candidato", "https://twitter.com/search?q=Gonzalo%20Marchese&src=typed_query&f=live")
        st.link_button("🥊 Menciones Grindetti", "https://twitter.com/search?q=Grindetti%20Independiente&src=typed_query&f=live")

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

# 6. PESTAÑA ESTRATEGIA (RESTITUIDA)
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

# 7. PESTAÑA TERRITORIO (RESTITUIDA)
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

# 8. PESTAÑA DISCURSO (RESTITUIDA)
with tab_ia:
    st.header("🦎 Discurso Polimórfico")
    st.info("Herramienta de adaptación de tono estratégico.")

    col_ia1, col_ia2 = st.columns([1, 1])

    with col_ia1:
        st.subheader("1. Configuración")
        idea_base = st.text_area("Escribe la idea central:", "Tenemos que sacar a los que le hacen mal al club", height=100)
        target = st.select_slider("Público:", options=["Vitalicios (Formal)", "Prensa (Técnico)", "Redes (Viral)", "Barra (Agresivo)"])
        generar = st.button("✨ Procesar")

    with col_ia2:
        st.subheader("2. Resultado")
        if generar:
            with st.spinner("Reescribiendo..."):
                time.sleep(1)
                resultado = ""
                if target == "Vitalicios (Formal)":
                    resultado = f"Estimada familia Roja: La historia nos exige responsabilidad. {idea_base}. Es un imperativo moral."
                elif target == "Prensa (Técnico)":
                    resultado = f"DECLARACIÓN OFICIAL: Sostenemos que {idea_base}. Esto se basa en los estatutos vigentes."
                elif target == "Redes (Viral)":
                    resultado = f"Basta de mentiras. 🛑 {idea_base}. Si estás de acuerdo dale RT. #TodoRojo 👹"
                else: 
                    resultado = f"Escuchen bien: {idea_base}. ¡El club es de los hinchas! ¡VAMOS ROJO!"
                st.code(resultado, language="text")

# 9. PESTAÑA DOMINACIÓN VISUAL (RESTITUIDA Y CORREGIDA)
with tab_mapa:
    st.header("📍 Rutas de Dominación Visual")
    st.markdown("Algoritmo de optimización de vía pública.")
    
    # Mapa OpenStreetMap (para evitar el error de pantalla negra)
    m = folium.Map(location=[-34.6700, -58.3600], zoom_start=13, tiles="OpenStreetMap")
    
    puntos = [
        ("Sede Mitre", -34.6624, -58.3649),
        ("Estadio LDA", -34.6702, -58.3711),
        ("Alto Avellaneda", -34.6755, -58.3665),
        ("Wilde Centro", -34.7001, -58.3215)
    ]
    
    for nombre, lat, lon in puntos:
        folium.Marker(
            [lat, lon], 
            popup=nombre, 
            icon=folium.Icon(color="red", icon="info-sign")
        ).add_to(m)

    st_folium(m, width=900, height=500)

# 10. PESTAÑA DEFENSA (EL DOMO DE HIERRO RESTITUIDO)
with tab_defensa:
    st.header("🛡️ DOMO DE HIERRO")
    col_def1, col_def2 = st.columns([1, 1])
    
    with col_def1:
        st.subheader("🔥 Ataque Recibido")
        ataque = st.selectbox("Tipo de Ataque:", 
                              ["'Son unos improvisados'", 
                               "'Van a privatizar el club'", 
                               "'No explican cómo pagar la deuda'"])
        defender = st.button("🛡️ ACTIVAR RESPUESTA")

    with col_def2:
        st.subheader("⚔️ Argumentario")
        if defender:
            if ataque == "'Son unos improvisados'":
                dato = "Nuestro equipo suma 40 años de gestión empresarial."
            elif ataque == "'Van a privatizar el club'":
                dato = "El Estatuto blinda al club como Asociación Civil. Es mentira."
            else:
                dato = "Plan Fideicomiso 2.0 + Renegociación auditada."
            
            st.markdown(f"""
            <div class="defense-card">
                <h3 style="color:white; margin:0;">📊 DATO REAL</h3>
                <p style="color:#cccccc;">"{dato}"</p>
            </div>
            """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.caption("🔒 Rojo War Room vFINAL | Uso exclusivo Jefatura de Campaña")
