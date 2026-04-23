import pandas as pd
import numpy as np
import os

def calcular_oportunidades(df_master, df_steam):
    """Calcula el índice de oportunidad para desarrolladores indie."""
    if df_master.empty or df_steam.empty:
        return pd.DataFrame()

    # 1. Agrupar master_dataset por Género + Plataforma
    # Asegurar que existan las columnas necesarias
    cols_master = ['Genre', 'Platform', 'Global_Sales', 'metascore', 'total_hours']
    for col in cols_master:
        if col not in df_master.columns:
            df_master[col] = 0

    stats_master = df_master.groupby(['Genre', 'Platform']).agg({
        'Global_Sales': 'mean',
        'metascore': 'mean',
        'total_hours': 'mean'
    }).reset_index()

    # 2. Agrupar steam_top1000 por Género (Primary_Genre) para medir competencia
    # Mapeamos Primary_Genre a Genre si es posible, o asumimos que son comparables
    competencia = df_steam['Primary_Genre'].value_counts().reset_index()
    competencia.columns = ['Genre', 'frecuencia_steam']

    # 3. Merge
    df_op = pd.merge(stats_master, competencia, on='Genre', how='left')
    df_op['frecuencia_steam'] = df_op['frecuencia_steam'].fillna(0)

    # 4. Normalización (0-1) para los scores
    def normalize(series):
        if series.max() == series.min():
            return series * 0
        return (series - series.min()) / (series.max() - series.min())

    df_op['score_ventas'] = normalize(df_op['Global_Sales'])
    df_op['score_twitch'] = normalize(df_op['total_hours'])
    df_op['score_critica'] = normalize(df_op['metascore'].fillna(df_op['metascore'].mean()))
    df_op['score_competencia_inverso'] = 1 - normalize(df_op['frecuencia_steam'])

    # 5. Cálculo del Índice de Oportunidad
    # Pesos: Ventas (0.3), Twitch (0.25), Crítica (0.2), Competencia Inversa (0.25)
    df_op['indice_oportunidad'] = (
        (df_op['score_ventas'] * 0.3) +
        (df_op['score_twitch'] * 0.25) +
        (df_op['score_critica'] * 0.2) +
        (df_op['score_competencia_inverso'] * 0.25)
    ) * 100 # Escala 0-100

    # 6. Top 10
    top_10 = df_op.nlargest(10, 'indice_oportunidad').copy()
    
    # Renombrar para mayor claridad en el dashboard
    top_10 = top_10.rename(columns={
        'frecuencia_steam': 'Juegos en Steam 2024',
        'total_hours': 'Horas Twitch Promedio',
        'Global_Sales': 'Ventas Promedio (M)'
    })

    return top_10
