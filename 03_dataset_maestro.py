import pandas as pd
import sqlite3
import os

data_dir = 'gameiq/data'

print("Cargando datasets limpios...")
vgsales = pd.read_csv(os.path.join(data_dir, 'vgsales_clean.csv'))
metacritic = pd.read_csv(os.path.join(data_dir, 'metacritic_clean.csv'))
twitch = pd.read_csv(os.path.join(data_dir, 'twitch_clean.csv'))

# Renombrar columnas de Twitch para que coincidan con el requerimiento
twitch = twitch.rename(columns={'Hours_watched': 'total_hours'})

print("Realizando Joins (Left Join)...")
# 1. Join VGSales + Metacritic
master = pd.merge(vgsales, metacritic[['game_key', 'metascore', 'userscore']], 
                 on='game_key', how='left')

# 2. Join Resultado + Twitch
master = pd.merge(master, twitch[['game_key', 'total_hours']], 
                 on='game_key', how='left')

# Guardar en CSV
master_csv_path = os.path.join(data_dir, 'master_dataset.csv')
master.to_csv(master_csv_path, index=False)

# Guardar en SQLite
db_path = os.path.join(data_dir, 'gameiq.db')
conn = sqlite3.connect(db_path)
master.to_sql('games', conn, if_exists='replace', index=False)
conn.close()

# Estadísticas
total_filas = len(master)
con_metascore = master['metascore'].notnull().sum()
con_twitch = master['total_hours'].notnull().sum()

print("\n--- Estadísticas del Dataset Maestro ---")
print(f"Total de filas: {total_filas}")
print(f"Filas con Metascore disponible: {con_metascore}")
print(f"Filas con datos de Twitch: {con_twitch}")

print("\nPrimeras 5 filas (Columnas Seleccionadas):")
cols_to_show = ['Name', 'Platform', 'Year', 'Genre', 'Global_Sales', 'metascore', 'userscore', 'total_hours']
# Asegurar que existan las columnas antes de mostrar
show_df = master[cols_to_show].head(5)
print(show_df.to_string(index=False))

print(f"\nDataset guardado en {master_csv_path} y {db_path} (tabla 'games')")
