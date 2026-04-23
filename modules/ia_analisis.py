import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv
import os

import streamlit as st

# Intentar cargar la key desde Streamlit Secrets (Cloud) o .env (Local)
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=api_key)


# Configurar el modelo
model = genai.GenerativeModel("gemini-2.0-flash")

def check_api_config():
    if not api_key:
        return "Error: No se encontró la GEMINI_API_KEY en los secretos ni en el .env."
    return None

def analizar_genero(genero, df):
    """Analiza la salud histórica de un género basándose en métricas reales."""
    err = check_api_config()
    if err: return err

    if df.empty:
        return "No hay datos para analizar."
        
    # Filtrar datos por género
    df_gen = df[df['Genre'] == genero]
    
    ventas_totales = df_gen['Global_Sales'].sum()
    metascore_avg = df_gen['metascore'].mean()
    twitch_hours = df_gen['total_hours'].sum()
    
    # Manejar posibles NaNs
    metascore_avg = round(metascore_avg, 1) if not pd.isna(metascore_avg) else "N/A"
    
    prompt = f"""Eres un analista senior de la industria del videojuego. 
En exactamente 3 oraciones analiza la salud histórica del género {genero} basándote en estos datos: 
ventas {ventas_totales:.2f}M copias, metascore promedio {metascore_avg}, horas en Twitch {twitch_hours:,.0f}. 
Sé específico y accionable."""

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error al conectar con Gemini: {str(e)}"

def predecir_exito(genero, plataforma, anio, df):
    """Predice el éxito de un lanzamiento basado en el rango histórico."""
    err = check_api_config()
    if err: return err

    if df.empty:
        return "No hay datos para predecir."
        
    # Filtrar por género y plataforma
    df_sim = df[(df['Genre'] == genero) & (df['Platform'] == plataforma)]
    
    if df_sim.empty:
        # Fallback si no hay combinación exacta: filtrar solo por género
        df_sim = df[df['Genre'] == genero]
        
    if df_sim.empty:
        return "No hay datos suficientes para este género."
        
    p25 = df_sim['Global_Sales'].quantile(0.25)
    p75 = df_sim['Global_Sales'].quantile(0.75)
    
    prompt = f"""¿Cuánto podría vender un juego de {genero} para {plataforma} lanzado en {anio}? 
Basándote en el rango histórico de {p25:.2f}M a {p75:.2f}M copias, da un estimado razonado en 2 oraciones."""

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error al conectar con Gemini: {str(e)}"

def detectar_tendencias(df_steam):
    """Identifica tendencias actuales basadas en el top 1000 de Steam."""
    err = check_api_config()
    if err: return err

    if df_steam.empty:
        return "No hay datos de Steam para detectar tendencias."
        
    top_5 = df_steam['Primary_Genre'].value_counts().head(5)
    lista_generos = ", ".join([f"{g} ({c} juegos)" for g, c in top_5.items()])
    
    prompt = f"""Basándote en estos 5 géneros más populares en Steam 2024-2026: {lista_generos}. 
¿Qué tendencia identificas? ¿Qué recomiendas a un desarrollador indie que va a lanzar un juego? 
Responde en 3 oraciones concretas."""

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error al conectar con Gemini: {str(e)}"

if __name__ == "__main__":
    # Rutas de datos
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(os.path.dirname(current_dir), 'data')
    master_path = os.path.join(data_dir, 'master_dataset.csv')
    steam_path = os.path.join(data_dir, 'steam_top1000.csv')
    
    if os.path.exists(master_path) and os.path.exists(steam_path):
        print("Cargando datos para prueba de IA...")
        df_m = pd.read_csv(master_path)
        df_s = pd.read_csv(steam_path)
        
        # Normalizar para pruebas locales
        if 'Metascore' in df_m.columns and 'metascore' not in df_m.columns:
            df_m['metascore'] = df_m['Metascore']
        if 'Global_Sales' not in df_m.columns:
            df_m['Global_Sales'] = 0.0
            
        print("\n1. Probando: analizar_genero('Action')")
        print("-" * 30)
        print(analizar_genero('Action', df_m))
        
        print("\n2. Probando: predecir_exito('Shooter', 'PS4', 2025, df_m)")
        print("-" * 30)
        print(predecir_exito('Shooter', 'PS4', 2025, df_m))
        
        print("\n3. Probando: detectar_tendencias(df_steam)")
        print("-" * 30)
        print(detectar_tendencias(df_s))
    else:
        print(f"Error: No se encontraron los archivos de datos en {data_dir}")
