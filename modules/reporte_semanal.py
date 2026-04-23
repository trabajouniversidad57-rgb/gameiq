import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta

def main():
    # 1. Carga data/steam_top1000.csv
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, 'data', 'steam_top1000.csv')
    
    if not os.path.exists(data_path):
        print(f"Error: No se encontró el archivo en {data_path}")
        return

    df = pd.read_csv(data_path)
    total_juegos = len(df)

    # Convertir Release_Date a datetime ignorando errores para que queden NaT
    df['Release_Date'] = pd.to_datetime(df['Release_Date'], errors='coerce', format='mixed')

    # 2. Calcula top 5 géneros con más juegos (con count y rating promedio)
    genre_stats = df.groupby('Primary_Genre').agg(
        cantidad=('AppID', 'count'),
        rating_promedio=('Review_Score_Pct', 'mean')
    ).reset_index()
    
    top_5 = genre_stats.nlargest(5, 'cantidad')

    # 3. Calcula si cada género creció más del 20% comparado con el período anterior
    # Usamos la fecha máxima disponible como referencia "actual" si hay fechas, 
    # si no usamos now() - pero el dataset tiene fechas del 2026.
    max_date = df['Release_Date'].max()
    
    if pd.notna(max_date):
        current_start = max_date - timedelta(days=7)
        prev_start = max_date - timedelta(days=14)

        df_current = df[(df['Release_Date'] > current_start) & (df['Release_Date'] <= max_date)]
        df_prev = df[(df['Release_Date'] > prev_start) & (df['Release_Date'] <= current_start)]

        current_counts = df_current['Primary_Genre'].value_counts()
        prev_counts = df_prev['Primary_Genre'].value_counts()
    else:
        current_counts = {}
        prev_counts = {}

    top_generos_list = []
    for _, row in top_5.iterrows():
        gen = row['Primary_Genre']
        cant = int(row['cantidad'])
        rating = round(float(row['rating_promedio']), 2)
        
        c_count = current_counts.get(gen, 0)
        p_count = prev_counts.get(gen, 0)
        
        alerta = False
        if p_count > 0:
            growth = (c_count - p_count) / p_count
            if growth > 0.20:
                alerta = True
        elif p_count == 0 and c_count > 0:
             # Creció de 0 a algo, por lo tanto creció más del 20%
             alerta = True
             
        top_generos_list.append({
            "genero": gen,
            "cantidad": cant,
            "rating_promedio": rating,
            "alerta_crecimiento": alerta
        })

    # 4. Determina la franja de precio dominante
    conditions = [
        (df['Price_USD'] < 15),
        (df['Price_USD'] >= 15) & (df['Price_USD'] <= 30),
        (df['Price_USD'] > 30)
    ]
    choices = ['low', 'mid', 'high']
    df['price_tier'] = np.select(conditions, choices, default='unknown')
    
    # Excluir 'unknown' o NA si existen, y contar
    tiers = df['price_tier'].value_counts()
    if 'unknown' in tiers and len(tiers) > 1:
        tiers = tiers.drop('unknown')
        
    precio_dominante = tiers.index[0] if not tiers.empty else 'unknown'

    # Género emergente: fuera del top 5, con mejor rating promedio (mínimo 2 juegos)
    top_5_names = top_5['Primary_Genre'].tolist()
    other_genres = genre_stats[(~genre_stats['Primary_Genre'].isin(top_5_names)) & (genre_stats['cantidad'] >= 2)]
    if not other_genres.empty:
        genero_emergente = other_genres.nlargest(1, 'rating_promedio')['Primary_Genre'].iloc[0]
    else:
        genero_emergente = None

    # 5. Genera y guarda data/reporte_semanal.json
    reporte = {
        "fecha": datetime.now().strftime("%Y-%m-%d"),
        "top_generos": top_generos_list,
        "precio_dominante": precio_dominante,
        "total_juegos_analizados": total_juegos,
        "genero_emergente": genero_emergente
    }

    out_path = os.path.join(base_dir, 'data', 'reporte_semanal.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(reporte, f, indent=2, ensure_ascii=False)

    # 6. Imprime el JSON generado en consola
    print(json.dumps(reporte, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()

# CONFIGURACIÓN N8N:
# Nodo Execute Command: python modules/reporte_semanal.py
# Nodo HTTP Request (Gemini API): POST https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=YOUR_API_KEY
# Extraer respuesta de Gemini: {{ $json.candidates[0].content.parts[0].text }}

