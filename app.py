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
    initial_sidebar_state="collapsed" # Ocultamos la barra nativa izquierda
)

# Estilo CSS personalizado
st.markdown("""
<style>
    .big-font { font-size:20px !important; font-weight: bold; }
    .stButton>button { width: 100%; border-radius: 5px; }
    div[data-testid="stMetricValue"] { font-size: 24px; color: #e63946; }
    
    /* ESTILO DEL TICKER MEJORADO (MÁS FINO Y ELEGANTE) */
    .ticker-wrap {
        width: 100%;
        overflow: hidden;
        background-color: #b71c1c; 
        padding: 6px; /* Más fino */
        white-space: nowrap;
        box-sizing: border-box;
        border-bottom: 3px solid #7f1d1d;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        margin-bottom: 15px;
    }
    .ticker {
        display: inline-block;
        white-space: nowrap;
        animation: ticker 120s linear infinite; /* MUCHO MÁS LENTO */
    }
    .ticker-item {
        display: inline-block;
        padding: 0 4rem;
        font-size: 16px; 
        font-weight: 600;
        color: #f1f1f1 !important; 
        font-family: 'Verdana', sans-serif;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    @keyframes ticker {
        0% { transform: translate3d(0, 0, 0); }
        100% { transform: translate3d(-100%, 0, 0); }
    }
    
    /* ESTILO PANEL DERECHO (SIMULANDO SIDEBAR) */
    .right-panel {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #e63946;
        height: 100%;
    }
</style>
""", unsafe_allow_html=True)

# --- FUNCIONES AUXILIARES (MOTOR DE BÚSQUEDA BLINDADO) ---

@st.cache_data(ttl=300) 
def buscar_noticias_rss(categoria="Todas"):
    """
    Motor V4: Búsqueda Multi-Hilo con Exclusión Agresiva de Homónimos.
    """
    
    # 1. LISTA NEGRA (EXCLUSIÓN DE HOMÓNIMOS DEL INTERIOR/EXTERIOR)
    # Esto elimina Independiente Rivadavia, del Valle, Santa Fe, etc.
    exclusion = (
        '-Rivadavia -Mendoza -Chivilcoy -Neuquen -Petrolero -Jujuy -Tandil -Trelew -Oliva '
        '-"Del Valle" -Medellin -"Santa Fe" -Bogota -Ecuador -Bolivia -Spain -España '
        '-Diputados -Senadores -"Partido Independiente" -Cine -Música'
    )

    # 2. LISTA BLANCA (TÉRMINOS QUE CONFIRMAN QUE ES EL ROJO)
    contexto_rojo = '(Avellaneda OR "El Rojo" OR "Rey de Copas" OR "CAI" OR "Libertadores de América" OR "Diablos Rojos" OR Bochini)'

    # 3. GENERACIÓN DE QUERIES SEGÚN CATEGORÍA
    queries = []
    
    if categoria == "Todas":
        # Estrategia: Disparar a todo lo que se mueva y filtrar después
        queries = [
            f'"Club Atlético Independiente" {exclusion}', # Nombre completo
            f'"Independiente" AND {contexto_rojo} {exclusion}', # Nombre corto + Contexto
            f'"Independiente" AND (Vaccari OR Grindetti OR "Mercado de Pases") {exclusion}' # Coyuntura
        ]
        
    elif categoria == "Fútbol Profesional":
        queries = [
            f'"Independiente" AND (Vaccari OR Formación OR "11 titular" OR Partido OR Gol OR "Liga Profesional" OR "Copa Argentina") {exclusion}',
            f'"Independiente" AND (Refuerzos OR "Mercado de Pases" OR Transferencia) {exclusion}'
        ]

    elif categoria == "Institución/Política":
        queries = [
            f'"Independiente" AND (Grindetti OR Seoane OR "Comisión Directiva" OR Asamblea OR Balance OR Elecciones OR Sede OR "Av Mitre") {exclusion}'
        ]

    elif categoria == "Economía/Judicial":
        queries = [
            f'"Independiente" AND (Inhibición OR Deuda OR Embargo OR FIFA OR TAS OR Dólares OR Banco OR Cheques OR Juicio) {exclusion}'
        ]

    elif categoria == "Inferiores/Otros Deportes":
        queries = [
            f'"Independiente" AND (Reserva OR Selectivo OR Inferiores OR Futsal OR Basquet OR "Fútbol Femenino" OR Wilde OR Domínico) {exclusion}'
        ]

    # 4. EJECUCIÓN Y FUSIÓN DE RESULTADOS
    noticias_totales = []
    links_vistos = set()

    for q in queries:
        # Pedimos noticias de los últimos 3 días para tener volumen, luego ordenamos
        encoded_query = urllib.parse.quote(q + " when:3d")
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=es-419&gl=AR&ceid=AR:es-419"
        
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                if entry.link not in links_vistos:
                    # Filtro final de seguridad: Si dice "Rivadavia" en el título, lo matamos (por si Google falló)
                    if "Rivadavia" in entry.title or "Del Valle" in entry.title:
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

    # 5. ORDENAMIENTO (Más nuevo primero)
    noticias_totales.sort(key=lambda x: x['fecha_obj'], reverse=True)
    
    return noticias_totales

def generar_link_whatsapp(texto):
    base_url = "https://wa.me/?text="
    encoded_text = urllib.parse.quote(texto)
    return base_url + encoded_text

# --- HEADER (CABECERA) ---
c_logo, c_title = st.columns([0.05, 0.95])
with c_logo:
    st.image("https://upload.wikimedia.org/wikipedia/commons/d/db/Club_Atl%C3%A9tico_Independiente_logo_%282008-present%29.png", width=50)
with c_title:
    st.markdown("### COMANDO ROJO | WAR ROOM")

# --- TICKER DE NOTICIAS ---
noticias_ticker = buscar_noticias_rss("Todas")
if noticias_ticker:
    textos_ticker = [f"🔴 {n['titulo']} ({n['fuente']})" for n in noticias_ticker[:10]]
    string_ticker = "   •   ".join(textos_ticker)
else:
    string_ticker = "🔴 Conectando satélite... Escaneando red..."

st.markdown(f"""
<div class="ticker-wrap">
    <div class="ticker">
        <div class="ticker-item">{string_ticker}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- PESTAÑAS PRINCIPALES ---
tab_alertas, tab_medios, tab_politica, tab_twitter, tab_clipping, tab_estrategia, tab_territorio, tab_ia, tab_mapa = st.tabs([
    "🚨 ALERTAS", "📰 MEDIOS", "🗳️ POLÍTICA", "🐦 TWITTER", "📝 CLIPPING", "🧠 ESTRATEGIA", "🗺️ TERRITORIO", "🦎 DISCURSO", "📍 DOMINACIÓN"
])

# 1. PESTAÑA ALERTAS (LAYOUT PERSONALIZADO CON BARRA DERECHA)
with tab_alertas:
    # DEFINIMOS COLUMNAS: IZQUIERDA (CONTENIDO 80%) | DERECHA (FILTROS 20%)
    col_main, col_sidebar = st.columns([0.8, 0.2])
    
    # --- BARRA LATERAL DERECHA (FILTROS) ---
    with col_sidebar:
        st.markdown('<div class="right-panel">', unsafe_allow_html=True)
        st.subheader("⚙️ Filtros")
        
        filtro_tema = st.radio(
            "Categoría:",
            ["Todas", "Fútbol Profesional", "Institución/Política", "Economía/Judicial", "Inferiores/Otros Deportes"],
            key="filtro_alertas"
        )
        
        st.divider()
        
        if st.button("🔄 Actualizar", type="primary"):
            st.cache_data.clear()
            st.rerun()
            
        st.divider()
        st.caption("Próximos Partidos:")
        st.caption("🆚 Racing (V)")
        st.caption("📅 15/12")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- CONTENIDO PRINCIPAL IZQUIERDA ---
    with col_main:
        st.subheader(f"🔥 Últimas Novedades: {filtro_tema}")
        
        # Ejecutamos búsqueda
        feed_noticias = buscar_noticias_rss(filtro_tema)
        
        if feed_noticias:
            st.success(f"Se encontraron {len(feed_noticias)} noticias verificadas.")
            
            for n in feed_noticias[:25]: # Mostramos las 25 más recientes
                with st.container(border=True):
                    c1, c2 = st.columns([0.05, 0.95])
                    with c1:
                        # Iconografía contextual
                        t = n['titulo'].lower()
                        if "inhibi" in t or "deuda" in t:
                            st.write("💸")
                        elif "ganó" in t or "gol" in t:
                            st.write("⚽")
                        elif "lesión" in t:
                            st.write("🚑")
                        elif "grindetti" in t or "vaccari" in t:
                            st.write("👔")
                        else:
                            st.write("📰")
                    with c2:
                        st.markdown(f"**[{n['titulo']}]({n['link']})**")
                        
                        # Cálculo de tiempo relativo
                        try:
                            fecha_dt = datetime.datetime(*n['fecha_obj'][:6])
                            ahora = datetime.datetime.now()
                            diff = ahora - fecha_dt
                            if diff.days == 0:
                                hace = f"Hace {diff.seconds // 3600} horas"
                            else:
                                hace = f"Hace {diff.days} días"
                        except:
                            hace = "Reciente"
                            
                        st.caption(f"🕒 {hace} | Fuente: {n['fuente']}")
        else:
            st.warning("No se encontraron noticias recientes. El filtro anti-homónimos puede haber eliminado resultados irrelevantes.")

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
    
    # Búsqueda específica
    encoded_query = urllib.parse.quote(f'"Independiente" AND {query} when:3d')
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=es-419&gl=AR&ceid=AR:es-419"
    
    try:
        feed = feedparser.parse(url)
        if feed.entries:
            for n in feed.entries[:15]:
                with st.expander(f"{n.title}"):
                    st.write(f"Fuente: {n.source.title if 'source' in n else 'Google'}")
                    st.markdown(f"**[🔗 LEER NOTA COMPLETA]({n.link})**")
        else:
            st.info("Sin noticias recientes en esta sección.")
    except:
        st.error("Error conectando con el proveedor de noticias.")

# 3. PESTAÑA POLÍTICA
with tab_politica:
    st.header("🗳️ Termómetro Político")
    c_pol1, c_pol2 = st.columns(2)
    with c_pol1:
        st.subheader("Oficialismo (Grindetti/Seoane)")
        # Lógica simplificada para ejemplo, en prod usar buscar_noticias_rss con query específica
        st.info("Monitoreando declaraciones del oficialismo...")
    with c_pol2:
        st.subheader("Oposición")
        st.info("Monitoreando movimientos de agrupaciones opositoras...")
        
    st.divider()
    st.subheader("📂 Archivos X (Dossier)")
    perfil = st.selectbox("Seleccionar Perfil:", ["Néstor G. (Presidente)", "Hugo M. (Ex-Pres)", "Fabián D. (Ex-Pres)"])
    if perfil == "Néstor G. (Presidente)":
        st.markdown("**Ficha:** Presidente en licencia (Lanús). Fortaleza política, debilidad de gestión diaria.")

# 4. PESTAÑA TWITTER
with tab_twitter:
    st.header("🐦 Radar X (En Vivo)")
    st.info("Accesos directos a búsquedas filtradas en X.")
    c_t1, c_t2 = st.columns(2)
    with c_t1:
        st.link_button("🔥 'Independiente' (Live)", "https://twitter.com/search?q=Independiente&src=typed_query&f=live")
    with c_t2:
        st.link_button("🗳️ Menciones Candidato", "https://twitter.com/search?q=Gonzalo%20Marchese&src=typed_query&f=live")

# 5. PESTAÑA CLIPPING
with tab_clipping:
    st.header("📝 Generador de Mensajes")
    texto = st.text_area("Pegar noticia:", height=100)
    if texto:
        st.code(f"*⚠️ URGENTE*\n\n{texto}\n\n_War Room CAI_", language="markdown")
        st.button("📲 WhatsApp Link")

# 6. PESTAÑA ESTRATEGIA
with tab_estrategia:
    st.header("🧠 Estrategia Electoral")
    st.success("Simulador de Votos activo. Datos protegidos.")

# 7. PESTAÑA TERRITORIO
with tab_territorio:
    st.header("🗺️ Mapa de Calor")
    # Mapa simulado
    st.map(pd.DataFrame({'lat': [-34.6702], 'lon': [-58.3709]}))

# 8. PESTAÑA DISCURSO
with tab_ia:
    st.header("🦎 Discurso Polimórfico")
    st.info("Módulo de adaptación de mensaje activo.")

# 9. PESTAÑA DOMINACIÓN
with tab_mapa:
    st.header("📍 Dominación Visual")
    # Mapa Folium
    m = folium.Map(location=[-34.6700, -58.3600], zoom_start=13, tiles="CartoDB dark_matter")
    st_folium(m, width=800, height=400)

# Footer
st.markdown("---")
st.caption("🔒 Rojo War Room v3.0 | Uso exclusivo Jefatura de Campaña")
