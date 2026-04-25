import pandas as pd
import json
import os
from datetime import datetime

def generar_reporte():
    # Rutas de archivos
    steam_path = 'gameiq/data/steam_top1000.csv'
    master_path = 'gameiq/data/master_dataset.csv'
    output_path = 'gameiq/data/reporte_semanal.json'

    # 1. Cargar datos
    if not os.path.exists(steam_path) or not os.path.exists(master_path):
        print(f"Error: No se encontraron los archivos en {steam_path} o {master_path}")
        return

    df_steam = pd.read_csv(steam_path)
    df_master = pd.read_csv(master_path)

    # 2. Calcular métricas
    
    # top_5_generos_steam: los 5 géneros con más juegos en Steam (con count y rating promedio)
    top_5_steam_df = df_steam.groupby('Primary_Genre').agg(
        count=('AppID', 'count'),
        avg_rating=('Review_Score_Pct', 'mean')
    ).sort_values(by='count', ascending=False).head(5)
    
    top_5_generos_steam = []
    for genre, row in top_5_steam_df.iterrows():
        top_5_generos_steam.append({
            "genero": genre,
            "cantidad": int(row['count']),
            "rating_promedio": round(float(row['avg_rating']), 2)
        })

    # top_3_ventas_historicas: los 3 géneros con más ventas históricas globales (de VGSales)
    top_3_ventas_df = df_master.groupby('Genre')['Global_Sales'].sum().sort_values(ascending=False).head(3)
    top_3_ventas_historicas = top_3_ventas_df.index.tolist()

    # alerta_crecimiento: cualquier género que aparezca en top_5_steam pero NO esté en top_3_ventas
    steam_genres = [g['genero'] for g in top_5_generos_steam]
    generos_emergentes = [g for g in steam_genres if g not in top_3_ventas_historicas]
    
    alerta = len(generos_emergentes) > 0

    # precio_promedio_steam: precio promedio del top 1000 Steam
    precio_promedio = round(df_steam['Price_USD'].mean(), 2)

    # total_analizados: número total de juegos procesados esta semana
    total_analizados = len(df_steam)

    # 3. Construir texto_para_gemini
    top_5_str = ", ".join([f"{g['genero']} ({g['cantidad']} juegos, {g['rating_promedio']}% rating)" for g in top_5_generos_steam])
    top_3_hist_str = ", ".join(top_3_ventas_historicas)
    emergentes_str = ", ".join(generos_emergentes) if generos_emergentes else 'ninguno'

    texto_para_gemini = f"""Eres un analista senior de videojuegos. Analiza estos datos de mercado de esta semana:
TOP 5 géneros en Steam 2024-2026: {top_5_str}
TOP 3 géneros históricos por ventas: {top_3_hist_str}
Géneros emergentes detectados: {emergentes_str}
Precio promedio del mercado: ${precio_promedio}

Dame un briefing ejecutivo de exactamente 3 párrafos:
1. ¿Qué está pasando en el mercado esta semana?
2. ¿Qué oportunidad o riesgo ves para desarrolladores?
3. ¿Qué recomendarías a un streamer de videojuegos esta semana?
Sé específico y usa los datos."""

    # 4. Estructura JSON
    reporte = {
        "fecha": datetime.now().strftime("%Y-%m-%d"),
        "top_generos": top_5_generos_steam,
        "generos_emergentes": generos_emergentes,
        "precio_promedio": precio_promedio,
        "total_analizados": total_analizados,
        "texto_para_gemini": texto_para_gemini,
        "alerta": alerta
    }

    # Guardar reporte
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(reporte, f, indent=2, ensure_ascii=False)

    # 5. Resumen en consola
    print("=== RESUMEN REPORTE SEMANAL GAMEIQ ===")
    print(f"Fecha: {reporte['fecha']}")
    print(f"Total juegos analizados: {total_analizados}")
    print(f"Precio promedio: ${precio_promedio}")
    print(f"Géneros emergentes: {emergentes_str}")
    print(f"Alerta activa: {alerta}")
    print(f"Reporte guardado en: {output_path}")
    print("=======================================")

if __name__ == "__main__":
    generar_reporte()

"""
Configuración n8n sugerida:
1. Schedule Trigger: Every Week (Monday 08:00 AM)
2. Execute Command: python gameiq/modules/reporte_semanal.py (Asegúrate de estar en el directorio raíz o ajustar la ruta)
3. Leer Archivo (Read File): gameiq/data/reporte_semanal.json
4. HTTP Request (Gemini):
   - Method: POST
   - URL: https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={{$vars.GEMINI_API_KEY}}
   - Body Parameters:
     {
       "contents": [{
         "parts": [{
           "text": "{{ $json.texto_para_gemini }}"
         }]
       }]
     }
5. Extract Text Expression: {{ $json.candidates[0].content.parts[0].text }}
6. IF Node: {{ $json.alerta }} is true
7. Telegram/Slack Node: Enviar mensaje con el análisis extraído.
"""
