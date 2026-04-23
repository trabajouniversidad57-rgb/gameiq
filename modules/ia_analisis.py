import pandas as pd
from google import genai
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

# Inicializar el cliente de la nueva SDK (google-genai)
client = None
if api_key:
    client = genai.Client(api_key=api_key)

MODEL_NAME = "gemini-1.5-flash" # Modelo estándar para 2026

def check_api_config():
    if not api_key or client is None:
        return "Error: No se encontró la GEMINI_API_KEY en los secretos ni en el .env."
    return None

def analizar_genero(genero, df):
    """Analiza la salud histórica de un género basándose en métricas reales."""
    err = check_api_config()
    if err: return err

    if df.empty:
        return "No hay datos para analizar."
        
    df_gen = df[df['Genre'] == genero]
    ventas_totales = df_gen['Global_Sales'].sum()
    metascore_avg = df_gen['metascore'].mean()
    twitch_hours = df_gen['total_hours'].sum()
    
    metascore_avg = round(metascore_avg, 1) if not pd.isna(metascore_avg) else "N/A"
    
    prompt = f"""Eres un analista senior de la industria del videojuego. 
En exactamente 3 oraciones analiza la salud histórica del género {genero} basándote en estos datos: 
ventas {ventas_totales:.2f}M copias, metascore promedio {metascore_avg}, horas en Twitch {twitch_hours:,.0f}. 
Sé específico y accionable."""

    try:
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        return response.text
    except Exception as e:
        return f"Error al conectar con Gemini: {str(e)}"

def predecir_exito(genero, plataforma, anio, df):
    """Predice el éxito de un lanzamiento basado en el rango histórico."""
    err = check_api_config()
    if err: return err

    if df.empty:
        return "No hay datos para predecir."
        
    df_sim = df[(df['Genre'] == genero) & (df['Platform'] == plataforma)]
    if df_sim.empty:
        df_sim = df[df['Genre'] == genero]
        
    if df_sim.empty:
        return "No hay datos suficientes para este género."
        
    p25 = df_sim['Global_Sales'].quantile(0.25)
    p75 = df_sim['Global_Sales'].quantile(0.75)
    
    prompt = f"""¿Cuánto podría vender un juego de {genero} para {plataforma} lanzado en {anio}? 
Basándote en el rango histórico de {p25:.2f}M a {p75:.2f}M copias, da un estimado razonado en 2 oraciones."""

    try:
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
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
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        return response.text
    except Exception as e:
        return f"Error al conectar con Gemini: {str(e)}"

def generar_plan_capacitacion(genero, plataforma, nivel, horas, objetivos, df):
    """Genera un plan de capacitación personalizado usando Gemini."""
    err = check_api_config()
    if err: return err

    df_gen = df[df['Genre'] == genero] if not df.empty else pd.DataFrame()
    ventas = df_gen['Global_Sales'].sum() if not df_gen.empty else 0
    metascore = df_gen['metascore'].mean() if not df_gen.empty else 0
    metascore = round(metascore, 1) if not pd.isna(metascore) else "N/A"

    prompt = f"""Eres un experto en gamificación y educación. Basándote en estos datos de un jugador:
- Género favorito: {genero} (datos históricos: {ventas:.2f}M copias vendidas, metascore promedio: {metascore})
- Plataforma: {plataforma}
- Nivel de experiencia: {nivel}
- Horas semanales de juego: {horas}
- Objetivos: {", ".join(objetivos)}

Crea un plan de capacitación de 4 semanas con:
- Semana 1: Fundamentos (qué aprender, 2 recursos específicos)
- Semana 2: Práctica guiada (ejercicios concretos)
- Semana 3: Aplicación (proyectos pequeños)
- Semana 4: Evaluación (cómo medir el progreso)
- Perfil del jugador: tipo (Competitivo/Casual/Creativo/Estratega) con justificación basada en los datos

Sé específico, usa ejemplos de juegos reales del género seleccionado. Responde en español."""

    try:
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        return response.text
    except Exception as e:
        return f"Error al generar el plan: {str(e)}"

def analizar_oportunidad(genero, plataforma, score):
    """Genera una explicación estratégica de una oportunidad de mercado."""
    err = check_api_config()
    if err: return err

    prompt = f"""Explica en 3 oraciones por qué la combinación {genero}+{plataforma} tiene una oportunidad de mercado con índice {score:.1f}/100. 
Qué tipo de juego específico podría funcionar bien aquí. Sé directo y accionable para un desarrollador indie. Responde en español."""

    try:
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        return response.text
    except Exception as e:
        return f"Error al analizar oportunidad: {str(e)}"

def chat_coach(pregunta, contexto):
    """Chatbot con contexto del dataset."""
    err = check_api_config()
    if err: return err

    prompt = f"""CONTEXTO DEL DATASET GAMEIQ:
{contexto}

EL USUARIO PREGUNTA: {pregunta}

INSTRUCCIONES: Responde en máximo 4 oraciones, citando datos específicos del contexto cuando sea relevante. Sé conciso, útil y responde en español."""

    try:
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        return response.text
    except Exception as e:
        return f"Error en el chat: {str(e)}"

if __name__ == "__main__":
    # Prueba local
    print("Iniciando prueba de IA con el nuevo SDK...")
    res = analizar_genero('Action', pd.DataFrame({'Genre':['Action'], 'Global_Sales':[10], 'metascore':[80], 'total_hours':[100]}))
    print(res)
