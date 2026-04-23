import pandas as pd
from google import genai
from groq import Groq
from dotenv import load_dotenv
import os
import streamlit as st
from tenacity import retry, stop_after_attempt, wait_exponential

def obtener_api_key(key_name="GROQ_API_KEY"):
    """Obtiene la API Key con prioridad: Streamlit Secrets > OS Environ > .env"""
    try:
        if key_name in st.secrets:
            return st.secrets[key_name]
    except Exception:
        pass
    
    env_key = os.environ.get(key_name)
    if env_key:
        return env_key
        
    load_dotenv()
    return os.getenv(key_name)

# Inicialización de Groq (Motor Principal)
groq_key = obtener_api_key("GROQ_API_KEY")
client_groq = Groq(api_key=groq_key) if groq_key else None
GROQ_MODEL = "llama-3.3-70b-versatile"

@retry(
    wait=wait_exponential(multiplier=1, min=2, max=6), 
    stop=stop_after_attempt(3),
    reraise=True
)
def _execute_groq_call(prompt):
    """Ejecución de la llamada a Groq con Llama 3."""
    if not client_groq:
        return "Error: No se encontró GROQ_API_KEY. Configúrala en Secrets o .env"
    
    completion = client_groq.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return completion.choices[0].message.content

def call_gemini(prompt):
    """
    Función de compatibilidad que ahora utiliza Groq como motor principal.
    Mantiene el nombre para evitar romper el resto de la aplicación.
    """
    try:
        return _execute_groq_call(prompt)
    except Exception as e:
        return f"Error en Groq (Llama 3): {str(e)}"

@st.cache_data
def analizar_genero(genero, df):
    if df.empty: return "No hay datos para analizar."
    
    df_gen = df[df['Genre'] == genero]
    ventas = df_gen['Global_Sales'].sum()
    metascore = df_gen['metascore'].mean()
    twitch = df_gen['total_hours'].sum() if 'total_hours' in df_gen.columns else 0
    metascore = round(metascore, 1) if not pd.isna(metascore) else "N/A"
    
    prompt = f"Analiza en 3 oraciones la salud del género {genero}: ventas {ventas:.2f}M, metascore {metascore}, Twitch {twitch:,.0f}."
    return call_gemini(prompt)

@st.cache_data
def predecir_exito(genero, plataforma, anio, df):
    if df.empty: return "No hay datos para predecir."
    
    df_sim = df[(df['Genre'] == genero) & (df['Platform'] == plataforma)]
    if df_sim.empty: df_sim = df[df['Genre'] == genero]
    if df_sim.empty: return "Datos insuficientes."
        
    p25, p75 = df_sim['Global_Sales'].quantile([0.25, 0.75])
    prompt = f"Predice ventas para {genero} en {plataforma} ({anio}) basado en rango {p25:.2f}M-{p75:.2f}M. Máximo 2 oraciones."
    return call_gemini(prompt)

@st.cache_data
def detectar_tendencias(df_steam):
    if df_steam.empty: return "Sin datos de Steam."
    
    top_5 = df_steam['Primary_Genre'].value_counts().head(5)
    lista = ", ".join([f"{g} ({c})" for g, c in top_5.items()])
    prompt = f"Basado en estos géneros populares en Steam: {lista}, identifica una tendencia y da una recomendación indie en 3 oraciones."
    return call_gemini(prompt)

@st.cache_data
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

@st.cache_data
def analizar_oportunidad(genero, plataforma, score):
    prompt = f"Explica en 3 oraciones por qué {genero}+{plataforma} tiene oportunidad {score:.1f}/100. Sugiere un tipo de juego indie."
    return call_gemini(prompt)

@st.cache_data
def chat_coach(pregunta, contexto):
    prompt = f"CONTEXTO:\n{contexto}\n\nPREGUNTA: {pregunta}\n\nResponde en máximo 4 oraciones citando datos."
    return call_gemini(prompt)
