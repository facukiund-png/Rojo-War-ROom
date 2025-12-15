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

# --- ESTILOS CSS ---
st.markdown("""
<style>
    .big-font { font-size:20px !important; font-weight: bold; }
    .stButton>button { width: 100%; border-radius: 5px; }
    div[data-testid="stMetricValue"] { font-size: 24px; color: #e63946; }
    
    /* TICKER */
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
        animation: ticker-animation 90s linear infinite;
        font-family: 'Arial', sans-serif;
        font-size: 18px;
        font-weight: bold;
        color: #ffffff;
    }
    @keyframes ticker-animation {
        0% { transform: translateX(100%); }
        100% { transform: translateX(-100%); }
    }
    
    /* PANELES */
    .right-panel {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 8px;
        border-left: 5px solid #e63946;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        height: 100%;
    }
    
    /* TARJETAS DOMO DE HIERRO */
    .defense-card { 
        background-color: #262730; 
        padding: 20px; 
        border-radius: 10px; 
        border-left: 5px solid #e63946; 
        margin-bottom: 15px; 
        color: white;
    }
    
    /* METRICAS POLITICAS */
    .pol-metric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
        text-align: center;
        font-weight: bold;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- MOTOR DE BÚSQUEDA (V6 - INTACTO) ---
@st.cache_data(ttl=60, show_spinner=False)
def buscar_noticias_rss(categoria="Todas", timestamp_force=0):
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
    elif categoria == "Oficialismo": # Query especial para Tablero Político
        queries = [f'"Independiente" AND (Grindetti OR Seoane OR "Néstor Grindetti" OR Oficialismo OR Gestión) {exclusion}']
    elif categoria == "Oposicion": # Query especial para Tablero Político
        queries = [f'"Independiente" AND (Doman OR Ducatenzeiler OR "Lista Roja" OR "Agrupación Independiente" OR Oposición) {exclusion}']

    noticias_totales = []
    links_vistos = set()

    for q in queries:
        encoded_query = urllib.parse.quote(q + " when:3d")
        rand_param = random.randint(1, 999999) 
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=es-419&gl=AR&ceid=AR:es-419&nocache={rand_param}"
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                if entry.link not in links_vistos:
                    titulo = entry.title.lower()
                    if "rivadavia" in titulo or "del valle" in titulo or "juventud" in titulo: continue
                    noticias_totales.append({
                        'titulo': entry.title,
                        'link': entry.link,
                        'fecha': entry.published,
                        'fecha_obj': entry.published_parsed, 
                        'fuente': entry.source.title if 'source' in entry else 'Google News'
                    })
                    links_vistos.add(entry.link)
        except: continue

    if not noticias_totales and categoria == "Todas": # Backup solo para general
        try:
            url_backup = "https://news.google.com/rss/search?q=%22Independiente+Avellaneda%22+when:1d&hl=es-419&gl=AR&ceid=AR:es-419"
            feed = feedparser.parse(url_backup)
            for entry in feed.entries:
                if entry.link not in links_vistos:
                    noticias_totales.append({'titulo': entry.title, 'link': entry.link, 'fecha': entry.published, 'fecha_obj': entry.published_parsed, 'fuente': 'Google News Backup'})
        except: pass

    noticias_totales.sort(key=lambda x: x['fecha_obj'] if x['fecha_obj'] else time.localtime(), reverse=True)
    return noticias_totales

def generar_link_whatsapp(texto):
    base_url = "https://wa.me/?text="
    encoded_text = urllib.parse.quote(texto)
    return base_url + encoded_text

# --- CABECERA ---
c_logo, c_title = st.columns([0.05, 0.95])
with c_logo:
    st.image("https://upload.wikimedia.org/wikipedia/commons/d/db/Club_Atl%C3%A9tico_Independiente_logo_%282008-present%29.png", width=50)
with c_title:
    st.markdown("### COMANDO ROJO | WAR ROOM")

# --- TICKER ---
noticias_ticker = buscar_noticias_rss("Todas", int(time.time()))
if noticias_ticker:
    textos_ticker = [f"👹 {n['titulo']}" for n in noticias_ticker[:10]]
    string_ticker = "   •   ".join(textos_ticker)
else:
    string_ticker = "🔴 Inicializando sistemas..."

st.markdown(f"""<div class="ticker-wrap"><div class="ticker-content">{string_ticker}</div></div>""", unsafe_allow_html=True)

# --- TABS ---
tab_alertas, tab_medios, tab_politica, tab_twitter, tab_clipping, tab_estrategia, tab_territorio, tab_ia, tab_mapa, tab_defensa = st.tabs([
    "🚨 ALERTAS", "📰 MEDIOS", "🗳️ POLÍTICA", "🐦 TWITTER", "📝 CLIPPING", "🧠 ESTRATEGIA", "🗺️ TERRITORIO", "🦎 DISCURSO", "📍 DOMINACIÓN", "🛡️ DEFENSA"
])

# 1. ALERTAS
with tab_alertas:
    col_main, col_right = st.columns([0.75, 0.25])
    with col_right:
        st.markdown('<div class="right-panel">', unsafe_allow_html=True)
        st.subheader("⚙️ Filtros")
        filtro_tema = st.radio("Ver noticias de:", ["Todas", "Fútbol Profesional", "Institución", "Economía"], key="filtro_alertas")
        st.divider()
        if st.button("🔄 ACTUALIZAR AHORA", type="primary"):
            st.cache_data.clear()
            st.rerun()
        st.caption(f"Última carga: {datetime.datetime.now().strftime('%H:%M')}")
        st.markdown('</div>', unsafe_allow_html=True)
    with col_main:
        st.subheader(f"🔥 Últimas Novedades: {filtro_tema}")
        feed_noticias = buscar_noticias_rss(filtro_tema, int(time.time()))
        if feed_noticias:
            for n in feed_noticias[:20]:
                with st.container(border=True):
                    c1, c2 = st.columns([0.05, 0.95])
                    with c1:
                        t = n['titulo'].lower()
                        if "inhibi" in t or "deuda" in t: st.write("💸")
                        elif "ganó" in t or "gol" in t: st.write("⚽")
                        else: st.write("📰")
                    with c2:
                        st.markdown(f"**[{n['titulo']}]({n['link']})**")
                        st.caption(f"📰 {n['fuente']}")
        else:
            st.info("No se encontraron noticias recientes.")

# 2. MEDIOS
with tab_medios:
    st.header("📰 Kiosco Digital")
    filtro_medios = st.radio("Fuente:", ["Nacionales", "Partidarios", "Mercado de Pases"], horizontal=True)
    query = ""
    if filtro_medios == "Nacionales": query = 'site:ole.com.ar OR site:tycsports.com OR site:infobae.com OR site:lanacion.com.ar'
    elif filtro_medios == "Partidarios": query = '(Infierno Rojo OR De la Cuna al Infierno OR Soy del Rojo OR LocoXelRojo)'
    else: query = '(Refuerzos OR Transferencias OR "Mercado de Pases")'
    encoded_query = urllib.parse.quote(f'"Independiente" AND {query} when:3d')
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=es-419&gl=AR&ceid=AR:es-419"
    try:
        feed = feedparser.parse(url)
        if feed.entries:
            for n in feed.entries[:10]:
                with st.expander(f"{n.title}"):
                    st.markdown(f"**[🔗 LEER NOTA]({n.link})**")
        else: st.info("Sin noticias recientes.")
    except: pass

# 3. POLÍTICA (MEJORADA - AHORA TRAE NOTICIAS REALES)
with tab_politica:
    st.header("🗳️ Tablero Político en Vivo")
    st.caption("Monitoreo automático de menciones de actores políticos del club.")
    
    col_pol_of, col_pol_op = st.columns(2)
    
    with col_pol_of:
        st.markdown("### 🎩 Oficialismo")
        st.markdown('<div class="pol-metric">Imagen Digital: 📉 Negativa</div>', unsafe_allow_html=True)
        news_oficial = buscar_noticias_rss("Oficialismo")
        if news_oficial:
            for n in news_oficial[:5]:
                st.markdown(f"• [{n['titulo']}]({n['link']})")
        else:
            st.info("Sin menciones recientes de Grindetti/Seoane.")

    with col_pol_op:
        st.markdown("### 🥊 Oposición")
        st.markdown('<div class="pol-metric">Actividad: 🟡 Media</div>', unsafe_allow_html=True)
        news_opo = buscar_noticias_rss("Oposicion")
        if news_opo:
            for n in news_opo[:5]:
                st.markdown(f"• [{n['titulo']}]({n['link']})")
        else:
            st.info("Sin menciones recientes de la oposición.")

    st.divider()
    st.subheader("📂 Dossier de Candidatos")
    perfil = st.selectbox("Ver Perfil:", ["Néstor G. (Presidente)", "Hugo M. (Ex-Pres)", "Fabián D. (Ex-Pres)"])
    if perfil == "Néstor G. (Presidente)":
        st.markdown("""
        * **Estado:** Licencia en Lanús. Actividad baja en el club.
        * **Puntos Débiles:** Ausencia, Inhibiciones, Resultados deportivos.
        * **Estrategia sugerida:** Atacar por el lado de "Club acéfalo".
        """)

# 4. TWITTER
with tab_twitter:
    st.header("🐦 Radar X")
    c1, c2 = st.columns(2)
    with c1: st.link_button("🔥 'Independiente' (En Vivo)", "https://twitter.com/search?q=Independiente&src=typed_query&f=live")
    with c2: st.link_button("🗳️ Menciones Candidato", "https://twitter.com/search?q=Gonzalo%20Marchese&src=typed_query&f=live")

# 5. CLIPPING
with tab_clipping:
    st.header("📝 Generador WhatsApp")
    txt = st.text_area("Texto/Link:")
    if txt and st.button("Generar Link"):
        st.success(generar_link_whatsapp(f"*INFORME CAI*\n\n{txt}"))

# 6. ESTRATEGIA
with tab_estrategia:
    st.header("🧠 Estrategia")
    st.success("Simulador activo (Datos protegidos).")

# 7. TERRITORIO
with tab_territorio:
    st.header("🗺️ Territorio")
    st.map(pd.DataFrame({'lat': [-34.6702], 'lon': [-58.3709]}))

# 8. DISCURSO
with tab_ia:
    st.header("🦎 Discurso Polimórfico")
    st.info("Sistema listo.")

# 9. DOMINACIÓN VISUAL (MEJORADA Y COMPLETA)
with tab_mapa:
    st.header("📍 Estrategia de Vía Pública")
    st.markdown("Algoritmo de optimización para cartelería y mesas.")

    c_map_controls, c_map_view = st.columns([1, 3])

    with c_map_controls:
        st.subheader("⚙️ Ponderación")
        w_trafico = st.slider("Peso Tráfico", 0, 10, 8)
        w_peaton = st.slider("Peso Peatones", 0, 10, 6)
        w_hinchas = st.slider("Peso Mundo Rojo", 0, 10, 10)
        st.info("Ajusta los sliders para recalcular los puntos calientes.")

    with c_map_view:
        # Puntos estratégicos con datos base
        puntos_base = [
            {"nombre": "Sede Av. Mitre", "lat": -34.6624, "lon": -58.3649, "tr": 9, "pe": 10, "hi": 10},
            {"nombre": "Estadio LDA", "lat": -34.6702, "lon": -58.3711, "tr": 6, "pe": 8, "hi": 10},
            {"nombre": "Alto Avellaneda", "lat": -34.6755, "lon": -58.3665, "tr": 9, "pe": 10, "hi": 4},
            {"nombre": "Estación Avellaneda", "lat": -34.6566, "lon": -58.3813, "tr": 10, "pe": 10, "hi": 5},
            {"nombre": "Wilde Centro (Mitre)", "lat": -34.7001, "lon": -58.3215, "tr": 10, "pe": 10, "hi": 8},
            {"nombre": "Predio Wilde", "lat": -34.7045, "lon": -58.3031, "tr": 5, "pe": 4, "hi": 10},
            {"nombre": "Bajada Pte Pueyrredón", "lat": -34.6548, "lon": -58.3755, "tr": 10, "pe": 2, "hi": 3},
        ]

        # Calcular Scores
        ranking = []
        m = folium.Map(location=[-34.6700, -58.3600], zoom_start=13, tiles="OpenStreetMap") # MAPA CLARO

        for p in puntos_base:
            score = (p['tr'] * w_trafico) + (p['pe'] * w_peaton) + (p['hi'] * w_hinchas)
            max_score = (10 * w_trafico) + (10 * w_peaton) + (10 * w_hinchas)
            porcentaje = int((score / max_score) * 100)
            ranking.append({"Ubicación": p['nombre'], "Impacto": porcentaje})
            
            # Color y Radio dinámico
            color = "green"
            radius = 100
            if porcentaje > 80: 
                color = "#b71c1c" # Rojo oscuro
                radius = 300
            elif porcentaje > 60:
                color = "orange"
                radius = 200

            folium.Circle(
                location=[p['lat'], p['lon']],
                radius=radius,
                color=color,
                fill=True,
                fill_opacity=0.4,
                popup=f"<b>{p['nombre']}</b><br>Impacto: {porcentaje}%"
            ).add_to(m)

        st_folium(m, width=900, height=500)
    
    st.subheader("🏆 Ranking de Efectividad")
    df_rank = pd.DataFrame(ranking).sort_values(by="Impacto", ascending=False)
    st.dataframe(df_rank, use_container_width=True, hide_index=True, column_config={"Impacto": st.column_config.ProgressColumn("Efectividad", format="%d%%", min_value=0, max_value=100)})

# 10. DEFENSA (DOMO DE HIERRO MEJORADO CON INPUT CUSTOM)
with tab_defensa:
    st.header("🛡️ DOMO DE HIERRO (Gestión de Crisis)")
    
    col_def1, col_def2 = st.columns([1, 1])
    
    with col_def1:
        st.subheader("🔥 Configuración del Ataque")
        
        # SELECTOR MEJORADO CON OPCIÓN "OTRO"
        ataque_seleccion = st.selectbox(
            "Seleccionar Ataque Recibido:", 
            ["Seleccionar...", 
             "'Son unos improvisados / Sin experiencia'", 
             "'Van a privatizar el club (SAD)'", 
             "'No explican cómo pagar la deuda'", 
             "✍️ OTRO (Escribir ataque personalizado...)"]
        )
        
        ataque_custom = ""
        if ataque_seleccion == "✍️ OTRO (Escribir ataque personalizado...)":
            ataque_custom = st.text_area("Escribe qué están diciendo:", "Ej: Dicen que vamos a vender el predio de Wilde...")
        
        tono = st.select_slider("Tono de Respuesta:", ["Institucional (Datos)", "Político (Firme)", "Agresivo (Chicana)"])
        
        btn_defender = st.button("🛡️ GENERAR ESCUDO")

    with col_def2:
        st.subheader("⚔️ Estrategia de Respuesta")
        
        if btn_defender:
            with st.spinner("Analizando puntos débiles del argumento rival..."):
                time.sleep(1.5)
                
                # LÓGICA DE RESPUESTA DINÁMICA
                dato_mata = ""
                chicana = ""
                salida = ""
                
                # 1. SI ES UN ATAQUE PRECARGADO
                if "improvisados" in ataque_seleccion:
                    dato_mata = "Nuestro equipo técnico suma +40 años de experiencia en gestión corporativa y deportiva."
                    chicana = "¿Experiencia es lo que tienen ellos? Experiencia en chocar el club tienen."
                    salida = "Prefiero la 'inexperiencia' de las manos limpias a la experiencia de los que fundieron al Rojo."
                elif "privatizar" in ataque_seleccion:
                    dato_mata = "Art. 1 del Estatuto: Asociación Civil sin Fines de Lucro. Es legalmente imposible sin Asamblea."
                    chicana = "Agitan el fantasma de las SAD para tapar que hoy el club ya está gerenciado por sus amigos."
                    salida = "Ni SAD, ni este desastre actual. Queremos un Club de los Socios, pero bien administrado."
                elif "deuda" in ataque_seleccion:
                    dato_mata = "Plan Fideicomiso 2.0 auditado + Renegociación de quirografarios con quita del 30%."
                    chicana = "Me causa gracia que pregunten cómo pagar los que generaron la deuda. ¿Dónde está la plata?"
                    salida = "Tenemos un plan serio. Lo que no vamos a hacer es seguir pateando cheques como hacen ahora."
                
                # 2. SI ES UN ATAQUE PERSONALIZADO (Lógica Genérica Inteligente)
                elif ataque_custom:
                    if tono == "Institucional (Datos)":
                        dato_mata = "Nuestros equipos legales y contables han auditado este tema. La propuesta es clara y está en la plataforma."
                        chicana = "No vamos a entrar en rumores infundados."
                        salida = "Invitamos al socio a leer nuestra plataforma completa en la web."
                    elif tono == "Agresivo (Chicana)":
                        dato_mata = "Es mentira. Siguiente pregunta."
                        chicana = f"Están nerviosos porque se les termina el kiosco. Ahora inventan que '{ataque_custom}'."
                        salida = "Que se preocupen por gobernar los días que les quedan."
                    else: # Político
                        dato_mata = "Es una operación de prensa clásica de campaña."
                        chicana = "Nos atacan porque crecemos."
                        salida = "Nosotros hablamos de propuestas, ellos de mentiras."

                # MOSTRAR TARJETAS
                if dato_mata:
                    st.markdown(f"""<div class="defense-card"><h4>📊 DATO MATA RELATO</h4><p>{dato_mata}</p></div>""", unsafe_allow_html=True)
                    st.markdown(f"""<div class="defense-card"><h4>🥊 LA CHICANA / CONTRA-GOLPE</h4><p>{chicana}</p></div>""", unsafe_allow_html=True)
                    st.markdown(f"""<div class="defense-card"><h4>🎩 SALIDA ELEGANTE</h4><p>{salida}</p></div>""", unsafe_allow_html=True)
                else:
                    st.warning("Selecciona un ataque para generar defensa.")

# Footer
st.markdown("---")
st.caption("🔒 Rojo War Room v5.0 | Uso exclusivo Jefatura de Campaña")
