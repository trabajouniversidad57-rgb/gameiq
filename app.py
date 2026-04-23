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
    from modules import ia_analisis, modelo_predictor
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

@st.cache_data
def load_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    master_path = os.path.join(current_dir, 'data', 'master_dataset.csv')
    steam_path = os.path.join(current_dir, 'data', 'steam_top1000.csv')
    
    data = {}
    
    # Intento de cargar datos maestros
    if not os.path.exists(master_path):
        data['master'] = pd.DataFrame()
    else:
        df_master = pd.read_csv(master_path)
        
        # Normalizar columnas para el módulo de IA (ia_analisis espera 'metascore' y 'Global_Sales')
        if 'Metascore' in df_master.columns and 'metascore' not in df_master.columns:
            df_master['metascore'] = df_master['Metascore']
        if 'Global_Sales' not in df_master.columns:
            df_master['Global_Sales'] = 0.0
            
        data['master'] = df_master
    
    # Intento de cargar datos de Steam
    if os.path.exists(steam_path):
        data['steam'] = pd.read_csv(steam_path)
    else:
        data['steam'] = pd.DataFrame()
        
    return data

verificar_archivos()
datasets = load_data()
df = datasets['master']
df_steam = datasets['steam']

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
        if isinstance(res, str) and ("Error" in res or "error" in res.lower()):
            st.error("Error al conectar con Gemini. Verifica la API key.")
            return None
        return res
    except Exception:
        st.error("Error al conectar con Gemini. Verifica la API key.")
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
    ["GameTrend", "Predictor de Éxito", "Crítica vs Comunidad", "Radar Steam 2024-2026"]
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
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay datos para el rango seleccionado.")

        if st.button("Analizar con IA"):
            with st.spinner("Consultando analista de IA..."):
                res = handle_ia_call(ia_analisis.analizar_genero, genero_sel, df)
                if res:
                    st.info(res)

        st.subheader("Carrera de Plataformas (Histórico)")
        html_race = load_html('03_race_plataformas.html')
        components.html(html_race, height=600, scrolling=True)
        
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
                st.plotly_chart(fig_comp, use_container_width=True)
                
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
        components.html(html_scatter, height=600, scrolling=True)
        
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
            components.html(html_steam_gen, height=500)
        with col2:
            st.subheader("Relación Precio vs Rating")
            html_steam_price = load_html('05b_steam_precio_rating.html')
            components.html(html_steam_price, height=500)
        
        if st.button("Detectar tendencias con IA"):
            with st.spinner("Analizando tendencias en Steam..."):
                # detectar_tendencias espera (df_steam)
                res_trends = handle_ia_call(ia_analisis.detectar_tendencias, df_steam)
                if res_trends:
                    st.warning(res_trends)

    display_footer()
