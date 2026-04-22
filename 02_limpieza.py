import pandas as pd
import re
import os

def normalizar_nombre(nombre):
    if pd.isna(nombre): return ''
    n = str(nombre).lower()
    n = re.sub(r'[^a-z0-9\s]', '', n)
    return ' '.join(n.split())

def load_csv(path):
    try:
        return pd.read_csv(path, encoding='utf-8')
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding='latin-1')

data_dir = 'gameiq/data'

# 1. VGSales.csv
print("Limpiando VGSales.csv...")
vgsales = load_csv(os.path.join(data_dir, 'VGSales.csv'))
vgsales = vgsales.dropna(subset=['Year'])
vgsales['Year'] = vgsales['Year'].astype(int)
vgsales['Publisher'] = vgsales['Publisher'].fillna('Desconocido')
vgsales['game_key'] = vgsales['Name'].apply(normalizar_nombre)
vgsales.to_csv(os.path.join(data_dir, 'vgsales_clean.csv'), index=False)
count_vgsales = len(vgsales)

# 2. Twitch_game_data.csv
print("Limpiando Twitch_game_data.csv...")
twitch = load_csv(os.path.join(data_dir, 'Twitch_game_data.csv'))
twitch['game_key'] = twitch['Game'].apply(normalizar_nombre)
# Drop keys that are empty strings
twitch = twitch[twitch['game_key'] != '']
tw_agg = twitch.groupby('game_key').agg({
    'Hours_watched': 'sum',
    'Streamers': 'sum',
    'Peak_viewers': 'max'
}).reset_index()
tw_agg.to_csv(os.path.join(data_dir, 'twitch_clean.csv'), index=False)
count_twitch = len(tw_agg)

# 3. metacritic.csv
print("Limpiando metacritic.csv...")
meta = load_csv(os.path.join(data_dir, 'metacritic.csv'))

# Mapping user requested names to actual column names
# Prompt says 'Name', but exploration says 'title'
# Prompt says 'Metascore', exploration says 'metascore'
# Prompt says 'User_Score', exploration says 'userscore'

meta['game_key'] = meta['title'].apply(normalizar_nombre)
meta['metascore'] = pd.to_numeric(meta['metascore'], errors='coerce')

if 'userscore' in meta.columns:
    meta['userscore'] = pd.to_numeric(meta['userscore'], errors='coerce')
    # No multiplicamos por 10 porque el dataset original ya está en escala 0-100

meta = meta.dropna(subset=['metascore'])
meta_clean = meta.drop_duplicates(subset=['game_key'], keep='first')
meta_clean.to_csv(os.path.join(data_dir, 'metacritic_clean.csv'), index=False)
count_meta = len(meta_clean)

print("\n--- Resumen de Limpieza ---")
print(f"vgsales_clean.csv: {count_vgsales} filas")
print(f"twitch_clean.csv: {count_twitch} filas")
print(f"metacritic_clean.csv: {count_meta} filas")
