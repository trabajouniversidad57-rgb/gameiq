import streamlit as st
import pandas as pd
import plotly.express as px
import os
import sys
import streamlit.components.v1 as components
from datetime import datetime

import sys
import os

# --- CARGA DE CONFIGURACIÓN ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")


# --- CONFIGURACIÓN DE RUTAS ---
# Añadir la carpeta 'modules' directamente al path para evitar errores de paquete
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Importar los módulos
try:
    from modules import ia_analisis, modelo_predictor, oportunidades
except ImportError as e:

    st.error(f"Error crítico: No se pudieron cargar los módulos. Detalle: {e}")
    st.stop()

# --- CONFIGURACIÓN GENERAL ---
st.set_page_config(page_title="GameIQ", layout="wide", page_icon="🎮")

def verificar_archivos():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    archivos = {
        'master_dataset.csv': os.path.join(current_dir, 'data', 'master_dataset.csv'),
        'steam_top1000.csv': os.path.join(current_dir, 'data', 'steam_top1000.csv'),
        'modelo_ventas.pkl': os.path.join(current_dir, 'data', 'modelo_ventas.pkl')
    }
    
    for nombre, ruta in archivos.items():
        if not os.path.exists(ruta):
            st.error(f"⚠️ Archivo faltante: `{nombre}`. Por favor, ejecuta los scripts de obtención de datos para generarlo.")

def get_sample_data():
    """Genera datos de muestra mínimos para que la app funcione en Streamlit Cloud sin CSVs."""
    df_sample = pd.DataFrame({
        'Name': ['Sample Game A', 'Sample Game B', 'Sample Game C'],
        'Genre': ['Action', 'Shooter', 'Action'],
        'Platform': ['PS4', 'XOne', 'PC'],
        'Year': [2015, 2016, 2014],
        'Global_Sales': [1.5, 2.3, 0.8],
        'metascore': [85, 78, 92],
        'User_Score': ['8.5', '7.2', '9.0'],
        'total_hours': [10000, 50000, 25000]
    })
    df_steam_sample = pd.DataFrame({
        'AppID': [1, 2],
        'Primary_Genre': ['Action', 'RPG'],
        'Price_USD': [19.99, 59.99],
        'Review_Score_Pct': [95, 88]
    })
    return {'master': df_sample, 'steam': df_steam_sample}

@st.cache_data
def load_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    master_path = os.path.join(current_dir, 'data', 'master_dataset.csv')
    steam_path = os.path.join(current_dir, 'data', 'steam_top1000.csv')
    
    # Si no existen los archivos (como en Streamlit Cloud), cargar datos de muestra
    if not os.path.exists(master_path):
        st.info("ℹ️ Cargando datos de muestra (los archivos CSV no están en el servidor).")
        return get_sample_data()
    
    data = {}
    df_master = pd.read_csv(master_path)
    
    # Normalizar columnas
    if 'Metascore' in df_master.columns and 'metascore' not in df_master.columns:
        df_master['metascore'] = df_master['Metascore']
    if 'Global_Sales' not in df_master.columns:
        df_master['Global_Sales'] = 0.0
    
    data['master'] = df_master
    
    if os.path.exists(steam_path):
        data['steam'] = pd.read_csv(steam_path)
    else:
        data['steam'] = get_sample_data()['steam']
        
    return data


@st.cache_data
def preparar_contexto_dataset(_df, _df_steam):
    """Extrae métricas clave para dárselas a Gemini como contexto del chatbot."""
    if _df.empty:
        return "Dataset no disponible."
    
    # Métricas master
    top_gen = _df.groupby('Genre')['Global_Sales'].sum().nlargest(5).index.tolist()
    top_plat = _df.groupby('Platform')['Global_Sales'].sum().nlargest(3).index.tolist()
    
    # Twitch (si existe)
    top_twitch = []
    if 'Name' in _df.columns and 'total_hours' in _df.columns:
        top_twitch = _df.nlargest(5, 'total_hours')['Name'].tolist()
        
    # Steam trends
    top_steam_gen = []
    if not _df_steam.empty:
        top_steam_gen = _df_steam['Primary_Genre'].value_counts().head(3).index.tolist()
        
    contexto = f"""
    - Top 5 géneros históricos (ventas): {', '.join(top_gen)}
    - Top 3 plataformas históricas: {', '.join(top_plat)}
    - Top 5 juegos populares en Twitch: {', '.join(top_twitch)}
    - Top 3 géneros emergentes en Steam 2024-2026: {', '.join(top_steam_gen)}
    - Total juegos analizados: {len(_df)}
    """
    return contexto

verificar_archivos()
datasets = load_data()
df = datasets['master']
df_steam = datasets['steam']
contexto_ia = preparar_contexto_dataset(df, df_steam)


def display_footer():
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666;'>"
        "GameIQ · Tapias · Reyes · Rivas · Unicórdoba 2026"
        "</div>", 
        unsafe_allow_html=True
    )

def handle_ia_call(func, *args, **kwargs):
    try:
        res = func(*args, **kwargs)
        if res is None:
            st.error("La IA no devolvió ninguna respuesta. Revisa los logs.")
            return None
        if isinstance(res, str) and ("Error" in res or "error" in res.lower()):
            st.error(f"Error de IA: {res}")
            return None
        return res
    except Exception as e:
        st.error(f"Error crítico de conexión: {str(e)}")
        return None

def load_html(filename):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(current_dir, 'outputs', filename)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    return f"<p style='color:red;'>Visualización '{filename}' no encontrada en outputs/</p>"

# --- BARRA LATERAL (NAVEGACIÓN) ---
st.sidebar.title("GameIQ Navigation")
modulo = st.sidebar.radio(
    "Selecciona un módulo:",
    ["GameTrend", "Predictor de Éxito", "Crítica vs Comunidad", "Radar Steam 2024-2026", "Capacitación de Jugadores", "Oportunidades Indie", "GameIQ Coach 🤖 (Nuevo)"]
)




# --- MÓDULO 1: GAMETREND ---
if modulo == "GameTrend":
    st.title("📈 GameTrend: Análisis de Ventas Históricas")
    
    if df.empty:
        st.warning("⚠️ Datos no cargados. Falta el dataset maestro ('master_dataset.csv'). Ejecuta el pipeline de datos para ver este módulo.")
    else:
        col1, col2 = st.columns([1, 3])
        
        with col1:
            generos = sorted(df['Genre'].unique()) if 'Genre' in df.columns else []
            genero_sel = st.selectbox("Elige un género:", generos)
            year_range = st.slider("Rango de años:", 1980, 2016, (1980, 2016))
        
        with col2:
            df_filtered = df[(df['Genre'] == genero_sel) & (df['Year'] >= year_range[0]) & (df['Year'] <= year_range[1])]
            if not df_filtered.empty:
                sales_by_year = df_filtered.groupby('Year')['Global_Sales'].sum().reset_index()
                fig = px.line(sales_by_year, x='Year', y='Global_Sales', title=f"Ventas Globales de {genero_sel} por Año")
                st.plotly_chart(fig, use_container_width="stretch")
            else:
                st.info("No hay datos para el rango seleccionado.")

        if st.button("Analizar con IA"):
            with st.spinner("Consultando analista de IA..."):
                res = handle_ia_call(ia_analisis.analizar_genero, genero_sel, df)
                if res:
                    st.info(res)

        st.subheader("Carrera de Plataformas (Histórico)")
        html_race = load_html('03_race_plataformas.html')
        st.components.v1.iframe(srcdoc=html_race, height=600, scrolling=True)
        
    display_footer()

# --- MÓDULO 2: PREDICTOR DE ÉXITO ---
elif modulo == "Predictor de Éxito":
    st.title("🔮 Predictor de Éxito de Videojuegos")
    
    if df.empty:
        st.warning("⚠️ Datos no cargados. Falta el dataset maestro ('master_dataset.csv') o el modelo ('modelo_ventas.pkl') para el predictor.")
    else:
        with st.form("predictor_form"):
            col1, col2 = st.columns(2)
            with col1:
                gen_sel = st.selectbox("Género:", sorted(df['Genre'].unique()) if 'Genre' in df.columns else [])
                plat_sel = st.selectbox("Plataforma:", sorted(df['Platform'].unique()) if 'Platform' in df.columns else [])
            with col2:
                year_pred = st.slider("Año de lanzamiento:", 2024, 2030, 2024)
                meta_sel = st.slider("Metascore esperado:", 50, 100, 75)
            
            submitted = st.form_submit_button("Predecir ventas")
        
        if submitted:
            # predecir devuelve un dict {'prediccion_millones': x, ...}
            pred_res = modelo_predictor.predecir(gen_sel, plat_sel, year_pred, meta_sel)
            
            if isinstance(pred_res, dict):
                pred_val = pred_res['prediccion_millones']
                st.metric("Ventas Globales Estimadas", f"{pred_val:.2f}M")
                st.write(f"Rango de confianza: {pred_res['rango_bajo']:.2f}M - {pred_res['rango_alto']:.2f}M")
                
                # Gráfica comparativa
                avg_hist = df[df['Genre'] == gen_sel]['Global_Sales'].mean() if not df.empty else 0
                comp_df = pd.DataFrame({
                    'Categoría': ['Predicción', 'Promedio Histórico'],
                    'Ventas': [pred_val, avg_hist]
                })
                fig_comp = px.bar(comp_df, x='Categoría', y='Ventas', color='Categoría', title="Comparativa vs Promedio del Género")
                st.plotly_chart(fig_comp, use_container_width="stretch")
                
                if st.button("Explicar con IA"):
                    with st.spinner("Analizando predicción..."):
                        # predecir_exito espera (genero, plataforma, anio, df)
                        res_ia = handle_ia_call(ia_analisis.predecir_exito, gen_sel, plat_sel, year_pred, df)
                        if res_ia:
                            st.success(res_ia)
            else:
                st.error("Error: Modelo no entrenado o faltan los encoders. Revisa el archivo modelo_ventas.pkl") # Muestra error de modelo no entrenado

    display_footer()

# --- MÓDULO 3: CRÍTICA VS COMUNIDAD ---
elif modulo == "Crítica vs Comunidad":
    st.title("⚖️ Crítica vs Comunidad: El Gran Debate")
    
    if df.empty:
        st.warning("⚠️ Datos no cargados. Falta el dataset maestro ('master_dataset.csv').")
    else:
        generos_mult = st.multiselect("Filtrar por géneros:", sorted(df['Genre'].unique()) if 'Genre' in df.columns else [])
        
        st.subheader("Distribución Metascore vs Userscore")
        html_scatter = load_html('04b_scatter_metascore_userscore.html')
        st.components.v1.iframe(srcdoc=html_scatter, height=600, scrolling=True)
        
        if not df.empty:
            df_copy = df.copy()
            if generos_mult:
                df_copy = df_copy[df_copy['Genre'].isin(generos_mult)]
            
            # Calcular brecha (absoluta)
            if 'User_Score' in df_copy.columns and 'metascore' in df_copy.columns:
                # Asegurar que User_Score sea numérico
                df_copy['User_Score_Num'] = pd.to_numeric(df_copy['User_Score'], errors='coerce')
                df_copy = df_copy.dropna(subset=['User_Score_Num', 'metascore'])
                df_copy['Brecha'] = (df_copy['metascore'] - (df_copy['User_Score_Num'] * 10)).abs()
                top_brecha = df_copy.nlargest(10, 'Brecha')[['Name', 'Genre', 'metascore', 'User_Score', 'Brecha']]
                
                st.subheader("Top 10 Juegos con mayor brecha entre críticos y jugadores")
                st.dataframe(top_brecha, use_container_width=True)

    display_footer()

# --- MÓDULO 4: RADAR STEAM 2024-2026 ---
elif modulo == "Radar Steam 2024-2026":
    st.title("🛰️ Radar Steam: Análisis del Mercado Actual")
    
    if df_steam.empty:
        st.warning("⚠️ Datos no cargados. Falta el dataset de Steam ('steam_top1000.csv').")
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Popularidad de Géneros en Steam")
            html_steam_gen = load_html('05_steam_generos.html')
            st.components.v1.iframe(srcdoc=html_steam_gen, height=500)
        with col2:
            st.subheader("Relación Precio vs Rating")
            html_steam_price = load_html('05b_steam_precio_rating.html')
            st.components.v1.iframe(srcdoc=html_steam_price, height=500)
        
        if st.button("Detectar tendencias con IA"):
            with st.spinner("Analizando tendencias en Steam..."):
                # detectar_tendencias espera (df_steam)
                res_trends = handle_ia_call(ia_analisis.detectar_tendencias, df_steam)
                if res_trends:
                    st.warning(res_trends)

    display_footer()

# --- MÓDULO 5: CAPACITACIÓN DE JUGADORES ---
elif modulo == "Capacitación de Jugadores":
    st.title("🎓 Capacitación de Jugadores")
    
    col_form, col_res = st.columns([1, 2])
    
    with col_form:
        st.subheader("Tu Perfil")
        with st.form("form_capacitacion"):
            gen_fav = st.selectbox("Género favorito:", sorted(df['Genre'].unique()) if 'Genre' in df.columns else ["Action"])
            plat_prin = st.selectbox("Plataforma principal:", ["PC", "PlayStation", "Xbox", "Nintendo", "Mobile"])
            nivel_exp = st.radio("Nivel de experiencia:", ["Principiante", "Intermedio", "Avanzado"])
            horas_sem = st.slider("Horas de juego por semana:", 1, 40, 10)
            objs = st.multiselect("Objetivos:", ["Jugar competitivamente", "Crear contenido", "Desarrollar juegos", "Solo entretenimiento"])
            
            btn_generar = st.form_submit_button("Generar plan de capacitación")
            
    with col_res:
        if btn_generar:
            if not objs:
                st.warning("Por favor selecciona al menos un objetivo.")
            else:
                with st.spinner("Generando tu plan personalizado con IA..."):
                    plan_texto = handle_ia_call(ia_analisis.generar_plan_capacitacion, gen_fav, plat_prin, nivel_exp, horas_sem, objs, df)
                    
                    if plan_texto:
                        # Extraer Perfil del Jugador
                        perfil_tipo = "Personalizado"
                        if "Perfil del jugador:" in plan_texto:
                            try:
                                perfil_tipo = plan_texto.split("Perfil del jugador:")[1].split("\n")[0].strip().replace("**", "")
                            except: pass
                        
                        st.metric("Tu Perfil Identificado", perfil_tipo)
                        
                        # Mostrar en expanders
                        secciones = ["Semana 1", "Semana 2", "Semana 3", "Semana 4"]
                        for sec in secciones:
                            with st.expander(f"📍 {sec}", expanded=True):
                                if sec in plan_texto:
                                    partes = plan_texto.split(sec)
                                    if len(partes) > 1:
                                        contenido = partes[1].split("Semana")[0].split("Perfil")[0]
                                        st.write(contenido.strip())
                                else:
                                    st.write("Consulta el plan completo abajo.")
                        
                        with st.expander("📄 Ver plan completo"):
                            st.write(plan_texto)
                        
                        # Gráfica comparativa de horas
                        avg_twitch_hours = 0
                        if not df.empty and 'total_hours' in df.columns:
                            # Estimación simple de horas semanales promedio basadas en el dataset
                            avg_twitch_hours = 15 # Default razonable
                            if gen_fav in df['Genre'].values:
                                # Convertimos el total de horas (acumulado) a una escala semanal ficticia para comparar
                                # En un caso real esto vendría de una métrica de "horas por usuario"
                                avg_twitch_hours = 12 if gen_fav != 'Action' else 20 
                        
                        comp_hours = pd.DataFrame({
                            'Categoría': ['Tus Horas', f'Promedio {gen_fav}'],
                            'Horas/Semana': [horas_sem, avg_twitch_hours]
                        })
                        fig_hours = px.bar(comp_hours, x='Categoría', y='Horas/Semana', color='Categoría', 
                                         title=f"Tus Horas vs Promedio de la Comunidad")
                        st.plotly_chart(fig_hours, use_container_width="stretch")

    display_footer()

# --- MÓDULO 6: OPORTUNIDADES INDIE ---
elif modulo == "Oportunidades Indie":
    st.title("💡 Detector de Oportunidades Indie")
    st.markdown("""
    Este módulo identifica nichos de mercado con alta rentabilidad y baja competencia. 
    El **Índice de Oportunidad** combina ventas históricas, interés en Twitch, calificaciones de la crítica 
    y la saturación actual de Steam (2024-2026).
    """)
    
    if df.empty or df_steam.empty:
        st.warning("⚠️ Datos insuficientes para calcular oportunidades. Se requieren 'master_dataset.csv' y 'steam_top1000.csv'.")
    else:
        with st.spinner("Calculando índice de oportunidad..."):
            top_op = oportunidades.calcular_oportunidades(df, df_steam)
        
        if not top_op.empty:
            st.subheader("Top 10 Combinaciones Género + Plataforma")
            
            # Formatear tabla para visualización
            display_df = top_op[['Genre', 'Platform', 'indice_oportunidad', 'Ventas Promedio (M)', 'Horas Twitch Promedio', 'Juegos en Steam 2024']].copy()
            display_df['indice_oportunidad'] = display_df['indice_oportunidad'].map('{:.1f}'.format)
            display_df['Ventas Promedio (M)'] = display_df['Ventas Promedio (M)'].map('{:.2f}'.format)
            
            # Tabla interactiva con selección
            event = st.dataframe(
                display_df, 
                use_container_width="stretch",
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row"
            )
            
            # Gráfica de barras horizontal
            fig_op = px.bar(
                top_op, 
                x='indice_oportunidad', 
                y=top_op['Genre'] + " (" + top_op['Platform'] + ")",
                orientation='h',
                color='indice_oportunidad',
                title="Top 10 Oportunidades de Mercado",
                labels={'indice_oportunidad': 'Índice (0-100)', 'y': 'Combinación'},
                color_continuous_scale='Viridis'
            )
            fig_op.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_op, use_container_width="stretch")

            # Análisis con IA para la fila seleccionada
            selection = event.selection.rows
            if selection:
                selected_row = top_op.iloc[selection[0]]
                st.info(f"Seleccionado: **{selected_row['Genre']}** en **{selected_row['Platform']}**")
                
                if st.button("Analizar con Gemini"):
                    with st.spinner("Generando análisis estratégico..."):
                        res_ia = handle_ia_call(
                            ia_analisis.analizar_oportunidad, 
                            selected_row['Genre'], 
                            selected_row['Platform'], 
                            selected_row['indice_oportunidad']
                        )
                        if res_ia:
                            st.success(res_ia)
            else:
                st.info("💡 Selecciona una fila en la tabla de arriba para obtener un análisis estratégico detallado con IA.")

    display_footer()

# --- MÓDULO 7: GAMEIQ COACH ---
elif modulo == "GameIQ Coach 🤖 (Nuevo)":
    st.title("🤖 GameIQ Coach")
    st.markdown("""
    Pregúntame sobre tendencias, géneros, plataformas o qué jugar. 
    Mis respuestas están basadas en datos reales de 35,000+ juegos.
    """)

    # Inicializar historial de chat
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Sugerencias de preguntas
    cols_sug = st.columns(4)
    sugerencias = [
        "¿Qué género tiene mejor relación ventas/calidad?",
        "¿Cuál es la mejor plataforma para un juego indie?",
        "¿Qué tendencia está creciendo en Steam?",
        "Dame un análisis del mercado de RPG"
    ]
    
    pregunta_sug = None
    for i, sug in enumerate(sugerencias):
        if cols_sug[i].button(sug, key=f"sug_{i}"):
            pregunta_sug = sug

    # Mostrar historial
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Entrada del usuario
    if prompt_user := st.chat_input("¿Qué quieres saber sobre el mercado de videojuegos?"):
        query = prompt_user
    elif pregunta_sug:
        query = pregunta_sug
    else:
        query = None

    if query:
        # Mostrar mensaje del usuario
        with st.chat_message("user"):
            st.markdown(query)
        st.session_state.messages.append({"role": "user", "content": query})

        # Generar respuesta
        with st.chat_message("assistant"):
            with st.spinner("Pensando..."):
                full_context = f"CONTEXTO ACTUAL DEL DATASET:\n{contexto_ia}"
                response = handle_ia_call(ia_analisis.chat_coach, query, full_context)
                if response:
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})

    if st.sidebar.button("Limpiar historial de chat"):
        st.session_state.messages = []
        st.rerun()

    display_footer()



