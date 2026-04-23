import pandas as pd
from google import genai
from dotenv import load_dotenv
import os
import streamlit as st

def obtener_api_key():
    """Obtiene la API Key con prioridad: Streamlit Secrets > OS Environ > .env"""
    # 1. Intentar con Streamlit Secrets (Cloud)
    try:
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass
    
    # 2. Intentar con variables de entorno (Docker / Heroku / etc)
    env_key = os.environ.get("GEMINI_API_KEY")
    if env_key:
        return env_key
        
    # 3. Intentar cargando desde archivo .env (Local)
    load_dotenv()
    return os.getenv("GEMINI_API_KEY")

# Inicialización robusta del cliente
api_key = obtener_api_key()
client = genai.Client(api_key=api_key) if api_key else None
MODEL_NAME = "gemini-1.5-flash"

def check_api_config():
    if not api_key or client is None:
        return "Error: No se encontró la GEMINI_API_KEY. Configúrala en los Secrets de Streamlit o en un archivo .env."
    return None

def analizar_genero(genero, df):
    """Analiza la salud histórica de un género basándose en métricas reales."""
    err = check_api_config()
    if err: return err
    if df.empty: return "No hay datos para analizar."
        
    df_gen = df[df['Genre'] == genero]
    ventas = df_gen['Global_Sales'].sum()
    metascore = df_gen['metascore'].mean()
    twitch = df_gen['total_hours'].sum()
    metascore = round(metascore, 1) if not pd.isna(metascore) else "N/A"
    
    prompt = f"Analiza en 3 oraciones la salud del género {genero}: ventas {ventas:.2f}M, metascore {metascore}, Twitch {twitch:,.0f}."

    try:
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        return response.text
    except Exception as e:
        return f"Error en Gemini: {str(e)}"

def predecir_exito(genero, plataforma, anio, df):
    """Predice el éxito de un lanzamiento basado en el rango histórico."""
    err = check_api_config()
    if err: return err
    if df.empty: return "No hay datos para predecir."
        
    df_sim = df[(df['Genre'] == genero) & (df['Platform'] == plataforma)]
    if df_sim.empty: df_sim = df[df['Genre'] == genero]
    if df_sim.empty: return "Datos insuficientes."
        
    p25, p75 = df_sim['Global_Sales'].quantile([0.25, 0.75])
    prompt = f"Predice ventas para {genero} en {plataforma} ({anio}) basado en rango {p25:.2f}M-{p75:.2f}M. Máximo 2 oraciones."

    try:
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        return response.text
    except Exception as e:
        return f"Error en Gemini: {str(e)}"

def detectar_tendencias(df_steam):
    """Identifica tendencias actuales basadas en el top 1000 de Steam."""
    err = check_api_config()
    if err: return err
    if df_steam.empty: return "Sin datos de Steam."
        
    top_5 = df_steam['Primary_Genre'].value_counts().head(5)
    lista = ", ".join([f"{g} ({c})" for g, c in top_5.items()])
    prompt = f"Basado en estos géneros populares en Steam: {lista}, identifica una tendencia y da una recomendación indie en 3 oraciones."

    try:
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        return response.text
    except Exception as e:
        return f"Error en Gemini: {str(e)}"

def generar_plan_capacitacion(genero, plataforma, nivel, horas, objetivos, df):
    """Genera un plan de capacitación personalizado usando Gemini."""
    err = check_api_config()
    if err: return err

    df_gen = df[df['Genre'] == genero] if not df.empty else pd.DataFrame()
    ventas = df_gen['Global_Sales'].sum() if not df_gen.empty else 0
    metascore = df_gen['metascore'].mean() if not df_gen.empty else 0
    metascore = round(metascore, 1) if not pd.isna(metascore) else "N/A"

    prompt = f"""Plan de 4 semanas para jugador de {genero} en {plataforma}.
    Nivel: {nivel}, Horas: {horas}, Objetivos: {', '.join(objetivos)}.
    Contexto: {ventas:.2f}M ventas, {metascore} score.
    Incluye 4 semanas y perfil del jugador. Responde en español."""

    try:
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        return response.text
    except Exception as e:
        return f"Error en Gemini: {str(e)}"

def analizar_oportunidad(genero, plataforma, score):
    """Genera una explicación estratégica de una oportunidad de mercado."""
    err = check_api_config()
    if err: return err

    prompt = f"Explica en 3 oraciones por qué {genero}+{plataforma} tiene oportunidad {score:.1f}/100. Sugiere un tipo de juego indie."

    try:
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        return response.text
    except Exception as e:
        return f"Error en Gemini: {str(e)}"

def chat_coach(pregunta, contexto):
    """Chatbot con contexto del dataset."""
    err = check_api_config()
    if err: return err

    prompt = f"CONTEXTO:\n{contexto}\n\nPREGUNTA: {pregunta}\n\nResponde en máximo 4 oraciones citando datos."

    try:
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        return response.text
    except Exception as e:
        return f"Error en el chat: {str(e)}"
