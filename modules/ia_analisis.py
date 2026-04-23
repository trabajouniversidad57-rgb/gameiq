import pandas as pd
from google import genai
from dotenv import load_dotenv
import os
import streamlit as st

def obtener_api_key():
    """Obtiene la API Key con prioridad: Streamlit Secrets > OS Environ > .env"""
    try:
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass
    
    env_key = os.environ.get("GEMINI_API_KEY")
    if env_key:
        return env_key
        
    load_dotenv()
    return os.getenv("GEMINI_API_KEY")

# Inicialización del cliente
api_key = obtener_api_key()
client = genai.Client(api_key=api_key) if api_key else None

# Lista de modelos por orden de preferencia para 2026
POTENTIAL_MODELS = ["gemini-1.5-flash", "gemini-1.5-flash-latest", "gemini-2.0-flash", "gemini-pro"]

def call_gemini(prompt):
    """Intenta llamar a Gemini probando varios nombres de modelos si falla."""
    if not client:
        return "Error: Cliente no inicializado. Revisa tu GEMINI_API_KEY."
        
    last_error = ""
    for model_name in POTENTIAL_MODELS:
        try:
            response = client.models.generate_content(model=model_name, contents=prompt)
            return response.text
        except Exception as e:
            last_error = str(e)
            if "not found" in last_error.lower() or "not supported" in last_error.lower():
                continue # Probar el siguiente modelo
            else:
                break # Otro tipo de error (ej: cuota), no seguir probando
                
    return f"Error en Gemini (probados {POTENTIAL_MODELS}): {last_error}"

def analizar_genero(genero, df):
    if df.empty: return "No hay datos para analizar."
    df_gen = df[df['Genre'] == genero]
    ventas = df_gen['Global_Sales'].sum()
    metascore = df_gen['metascore'].mean()
    twitch = df_gen['total_hours'].sum()
    metascore = round(metascore, 1) if not pd.isna(metascore) else "N/A"
    
    prompt = f"Analiza en 3 oraciones la salud del género {genero}: ventas {ventas:.2f}M, metascore {metascore}, Twitch {twitch:,.0f}."
    return call_gemini(prompt)

def predecir_exito(genero, plataforma, anio, df):
    if df.empty: return "No hay datos para predecir."
    df_sim = df[(df['Genre'] == genero) & (df['Platform'] == plataforma)]
    if df_sim.empty: df_sim = df[df['Genre'] == genero]
    if df_sim.empty: return "Datos insuficientes."
        
    p25, p75 = df_sim['Global_Sales'].quantile([0.25, 0.75])
    prompt = f"Predice ventas para {genero} en {plataforma} ({anio}) basado en rango {p25:.2f}M-{p75:.2f}M. Máximo 2 oraciones."
    return call_gemini(prompt)

def detectar_tendencias(df_steam):
    if df_steam.empty: return "Sin datos de Steam."
    top_5 = df_steam['Primary_Genre'].value_counts().head(5)
    lista = ", ".join([f"{g} ({c})" for g, c in top_5.items()])
    prompt = f"Basado en estos géneros populares en Steam: {lista}, identifica una tendencia y da una recomendación indie en 3 oraciones."
    return call_gemini(prompt)

def generar_plan_capacitacion(genero, plataforma, nivel, horas, objetivos, df):
    df_gen = df[df['Genre'] == genero] if not df.empty else pd.DataFrame()
    ventas = df_gen['Global_Sales'].sum() if not df_gen.empty else 0
    metascore = df_gen['metascore'].mean() if not df_gen.empty else 0
    metascore = round(metascore, 1) if not pd.isna(metascore) else "N/A"

    prompt = f"""Plan de 4 semanas para jugador de {genero} en {plataforma}.
    Nivel: {nivel}, Horas: {horas}, Objetivos: {', '.join(objetivos)}.
    Contexto: {ventas:.2f}M ventas, {metascore} score.
    Incluye 4 semanas y perfil del jugador. Responde en español."""
    return call_gemini(prompt)

def analizar_oportunidad(genero, plataforma, score):
    prompt = f"Explica en 3 oraciones por qué {genero}+{plataforma} tiene oportunidad {score:.1f}/100. Sugiere un tipo de juego indie."
    return call_gemini(prompt)

def chat_coach(pregunta, contexto):
    prompt = f"CONTEXTO:\n{contexto}\n\nPREGUNTA: {pregunta}\n\nResponde en máximo 4 oraciones citando datos."
    return call_gemini(prompt)
