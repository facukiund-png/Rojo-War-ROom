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
</style>
""", unsafe_allow_html=True)

# --- FUNCIONES AUXILIARES ---

@st.cache_data(ttl=300) 
def buscar_noticias_rss(query):
    """Busca noticias en Google News via RSS gratis"""
    encoded_query = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=es-419&gl=AR&ceid=AR:es-419"
    try:
        feed = feedparser.parse(url)
        noticias = []
        if feed.entries:
            for entry in feed.entries[:10]:
                noticias.append({
                    'titulo': entry.title,
                    'link': entry.link,
                    'fecha': entry.published,
                    'fuente': entry.source.title if 'source' in entry else 'Google News'
                })
        return noticias
    except:
        return []

def generar_link_whatsapp(texto):
    """Crea un link para compartir en WhatsApp"""
    base_url = "https://wa.me/?text="
    encoded_text = urllib.parse.quote(texto)
    return base_url + encoded_text

# --- SIDEBAR (Barra Lateral) ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/d/db/Club_Atl%C3%A9tico_Independiente_logo_%282008-present%29.png", width=100)
    st.title("COMANDO ROJO")
    st.caption("Revolución Independiente - 2025")
    
    if st.button("🔄 ACTUALIZAR DATOS"):
        st.cache_data.clear()
        st.rerun()

    st.divider()
    
    st.subheader("📆 Próximos Partidos")
    partidos = pd.DataFrame({
        "Rival": ["Racing (V)", "River (L)", "Belgrano (V)"],
        "Fecha": ["Dom 15/12", "Dom 22/12", "Mie 25/12"],
        "Torneo": ["Liga", "Liga", "Copa"]
    })
    st.table(partidos)
    
    st.divider()
    
    st.subheader("🏆 Ranking Militancia")
    st.markdown("""
    🥇 **Juan P.** (Wilde) - 15 Socios<br>
    🥈 **Marta G.** (Sede) - 12 Socios<br>
    🥉 **Tito R.** (Domínico) - 8 Socios
    """, unsafe_allow_html=True)

# --- CUERPO PRINCIPAL (PESTAÑAS) ---
# CAMBIO REALIZADO AQUÍ: "🦎 DISCURSO POLIMÓRFICO" en lugar de IA
tab_alertas, tab_medios, tab_politica, tab_twitter, tab_clipping, tab_estrategia, tab_territorio, tab_ia = st.tabs([
    "🚨 ALERTAS", "📰 MEDIOS", "🗳️ POLÍTICA", "🐦 TWITTER", "📝 CLIPPING", "🧠 ESTRATEGIA", "🗺️ TERRITORIO", "🦎 DISCURSO POLIMÓRFICO"
])

# 1. PESTAÑA ALERTAS URGENTES
with tab_alertas:
    st.header("🚨 Radar de Crisis (Último Momento)")
    col1, col2 = st.columns([3, 1])
    with col1:
        # Buscamos palabras peligrosas
        palabras_clave = "Independiente AND (Inhibición OR Embargo OR FIFA OR TAS OR Renuncia OR Escándalo OR Barras OR Incidentes)"
        noticias_urgentes = buscar_noticias_rss(palabras_clave)
        
        if noticias_urgentes:
            for n in noticias_urgentes:
                with st.container(border=True):
                    st.markdown(f"#### 🔴 {n['titulo']}")
                    st.caption(f"{n['fecha']} | Fuente: {n['fuente']}")
                    st.markdown(f"[Leer Noticia]({n['link']})")
        else:
            st.success("✅ No se detectan alertas graves en las últimas horas.")
            
    with col2:
        st.warning("⚠️ ESTADO DE ALERTA")
        st.metric(label="Nivel de Riesgo", value="MEDIO", delta="Inhibiciones")
        st.info("Monitoreando: FIFA, TAS, Juicios, Seguridad.")

# 2. PESTAÑA MEDIOS
with tab_medios:
    st.header("📰 Kiosco Digital")
    filtro_medios = st.radio("Fuente:", ["Nacionales", "Partidarios", "Mercado de Pases"], horizontal=True)
    
    query = ""
    if filtro_medios == "Nacionales":
        query = "Independiente Avellaneda site:ole.com.ar OR site:tycsports.com OR site:infobae.com"
    elif filtro_medios == "Partidarios":
        query = "Independiente (Infierno Rojo OR De la Cuna al Infierno OR Soy del Rojo OR LocoXelRojo)"
    else:
        query = "Independiente Refuerzos Transferencias Vaccari"
        
    noticias = buscar_noticias_rss(query)
    
    if noticias:
        for n in noticias:
            with st.expander(f"{n['titulo']}"):
                st.write(f"Fuente: {n['fuente']}")
                st.markdown(f"**[🔗 LEER NOTA COMPLETA]({n['link']})**")
                # Botón simple de copiado manual
                st.code(f"{n['titulo']} - {n['link']}")
    else:
        st.info("No se encontraron noticias recientes en esta categoría.")

# 3. PESTAÑA POLÍTICA
with tab_politica:
    col_p1, col_p2 = st.columns(2)
    
    with col_p1:
        st.subheader("🕵️ Oficialismo")
        q_oficial = "Néstor Grindetti OR Daniel Seoane OR Comisión Directiva Independiente"
        noticias_oficial = buscar_noticias_rss(q_oficial)
        if noticias_oficial:
            for n in noticias_oficial[:5]:
                st.markdown(f"• [{n['titulo']}]({n['link']})")
        else:
            st.write("Sin novedades recientes.")
            
    with col_p2:
        st.subheader("🥊 Oposición")
        q_opo = "Andrés Ducatenzeiler OR Fabián Doman OR Lista Roja OR Agrupación Independiente"
        noticias_opo = buscar_noticias_rss(q_opo)
        if noticias_opo:
            for n in noticias_opo[:5]:
                st.markdown(f"• [{n['titulo']}]({n['link']})")
        else:
            st.write("Sin novedades recientes.")
            
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
        # El input del usuario
        idea_base = st.text_area("Escribe la idea central (cruda):", "Tenemos que sacar a los que le hacen mal al club y arreglar la cancha", height=100)
        
        # El selector de público
        target = st.select_slider(
            "Seleccionar Público Objetivo:", 
            options=["Socios Vitalicios (Formal)", "Prensa (Técnico)", "Redes (Viral)", "Barra/Tablón (Agresivo)"]
        )

        generar = st.button("✨ Procesar Estrategia")

    with col_ia2:
        st.subheader("2. Resultado Generado")
        
        if generar:
            with st.spinner("Analizando tono y reescribiendo..."):
                time.sleep(2) # Simulamos que piensa
                
                # Lógica de Transformación de Texto
                resultado = ""
                
                if target == "Socios Vitalicios (Formal)":
                    resultado = f"Estimada familia Roja:\n\nLa historia de nuestra institución nos exige responsabilidad y memoria. {idea_base}. Es un imperativo moral recuperar la gloria y la infraestructura que ustedes, con tanto esfuerzo, ayudaron a construir. Volvamos a las raíces."
                
                elif target == "Prensa (Técnico)":
                    resultado = f"DECLARACIÓN OFICIAL:\n\nDesde la agrupación sostenemos que {idea_base}. Esto es parte de un plan integral de saneamiento basado en los artículos 45 y 46 del estatuto vigente. Los números avalan nuestra postura de renovación inmediata."
                
                elif target == "Redes (Viral)":
                    resultado = f"Basta de mentiras. 🛑\n\n{idea_base}. \n\nSi estás de acuerdo dale RT. Se les terminó la joda a los de siempre. \n\n#TodoRojo 👹 #RevolucionIndependiente"
                
                else: # Barra / Agresivo
                    resultado = f"Escuchen bien todos:\n\n{idea_base}.\n\nAl que no le guste, que se vaya. El club es de los hinchas, no de los de traje. ¡Aca se viene a alentar y a ganar! ¡VAMOS ROJO CARAJO!"

                # Mostrar el resultado
                st.success("✅ Mensaje Adaptado Exitosamente")
                st.code(resultado, language="text")
                
                st.caption("Copia el texto de arriba y envíalo.")

    st.divider()
    st.markdown("### 💡 Tips de uso:")
    st.markdown("""
    * Usar **Vitalicios** para mails y cartas formales.
    * Usar **Barra** para arengas de cancha o reuniones tensas.
    * Usar **Redes** para Twitter e Instagram.
    """)

# Footer
st.markdown("---")
st.caption("🔒 Rojo War Room v1.0 | Uso exclusivo Jefatura de Campaña")
