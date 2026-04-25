import pandas as pd
import requests
import os
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Cargar variables de entorno (para testing local)
load_dotenv()

def normalizar_nombre(nombre):
    if pd.isna(nombre): return ''
    n = str(nombre).lower()
    n = re.sub(r'[^a-z0-9\s]', '', n)
    return ' '.join(n.split())

def fetch_steamspy():
    print("Consultando SteamSpy (Top 100 en 2 semanas)...")
    try:
        url = "https://steamspy.com/api.php?request=top100in2weeks"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            games = []
            for appid, info in data.items():
                games.append({
                    'Name': info['name'],
                    'Platform': 'PC',
                    'Year': datetime.now().year, # SteamSpy no da el año exacto de lanzamiento en este endpoint fácilmente
                    'Genre': 'Action', # Placeholder, SteamSpy da tags pero no un género único compatible con VGSales
                    'Publisher': info['developer'],
                    'game_key': normalizar_nombre(info['name'])
                })
            return games
    except Exception as e:
        print(f"Error en SteamSpy: {e}")
    return []

def fetch_rawg(api_key):
    if not api_key:
        print("RAWG_API_KEY no configurada. Saltando...")
        return []
    
    print("Consultando RAWG (Lanzamientos recientes)...")
    try:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        url = f"https://api.rawg.io/api/games?key={api_key}&dates={start_date},{end_date}&ordering=-released&page_size=40"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            games = []
            for item in data.get('results', []):
                games.append({
                    'Name': item['name'],
                    'Platform': item['platforms'][0]['platform']['name'] if item.get('platforms') else 'Multi',
                    'Year': datetime.strptime(item['released'], '%Y-%m-%d').year if item.get('released') else datetime.now().year,
                    'Genre': item['genres'][0]['name'] if item.get('genres') else 'Misc',
                    'Publisher': 'Indie', # RAWG requiere otra llamada para publishers
                    'game_key': normalizar_nombre(item['name']),
                    'metascore': item.get('metacritic'),
                    'userscore': item.get('rating') * 20 if item.get('rating') else None # RAWG es 0-5
                })
            return games
    except Exception as e:
        print(f"Error en RAWG: {e}")
    return []

def fetch_igdb(client_id, client_secret):
    if not client_id or not client_secret:
        print("IGDB credentials no configuradas. Saltando...")
        return []

    print("Consultando IGDB (Juegos populares recientes)...")
    try:
        # 1. Obtener Token
        auth_url = f"https://id.twitch.tv/oauth2/token?client_id={client_id}&client_secret={client_secret}&grant_type=client_credentials"
        auth_res = requests.post(auth_url, timeout=10)
        token = auth_res.json().get('access_token')

        if not token: return []

        # 2. Consultar Juegos
        headers = {
            'Client-ID': client_id,
            'Authorization': f'Bearer {token}'
        }
        # Query: populares lanzados este año
        query = "fields name, first_release_date, genres.name, involved_companies.company.name, platforms.name, total_rating; where first_release_date > 1704067200; sort popularity desc; limit 50;"
        
        response = requests.post("https://api.igdb.com/v4/games", headers=headers, data=query, timeout=10)
        if response.status_code == 200:
            data = response.json()
            games = []
            for item in data:
                year = datetime.fromtimestamp(item['first_release_date']).year if 'first_release_date' in item else datetime.now().year
                games.append({
                    'Name': item['name'],
                    'Platform': item['platforms'][0]['name'] if item.get('platforms') else 'Multi',
                    'Year': year,
                    'Genre': item['genres'][0]['name'] if item.get('genres') else 'Misc',
                    'Publisher': item['involved_companies'][0]['company']['name'] if item.get('involved_companies') else 'Unknown',
                    'game_key': normalizar_nombre(item['name']),
                    'userscore': item.get('total_rating')
                })
            return games
    except Exception as e:
        print(f"Error en IGDB: {e}")
    return []

def main():
    master_path = 'gameiq/data/master_dataset.csv'
    
    if not os.path.exists(master_path):
        print(f"Error: {master_path} no existe.")
        return

    # Cargar dataset actual
    df = pd.read_csv(master_path)
    existentes = set(df['game_key'].tolist())
    last_rank = df['Rank'].max() if not df['Rank'].empty else 0

    # Fetch de APIs
    rawg_key = os.getenv('RAWG_API_KEY')
    igdb_id = os.getenv('IGDB_CLIENT_ID')
    igdb_secret = os.getenv('IGDB_CLIENT_SECRET')

    nuevos_candidatos = []
    nuevos_candidatos.extend(fetch_steamspy())
    nuevos_candidatos.extend(fetch_rawg(rawg_key))
    nuevos_candidatos.extend(fetch_igdb(igdb_id, igdb_secret))

    # Filtrar nuevos
    nuevas_filas = []
    vistos_en_esta_corrida = set()

    for g in nuevos_candidatos:
        key = g['game_key']
        if key and key not in existentes and key not in vistos_en_esta_corrida:
            last_rank += 1
            fila = {
                'Rank': last_rank,
                'Name': g['Name'],
                'Platform': g.get('Platform', 'Unknown'),
                'Year': g.get('Year', datetime.now().year),
                'Genre': g.get('Genre', 'Misc'),
                'Publisher': g.get('Publisher', 'Unknown'),
                'NA_Sales': 0.0,
                'EU_Sales': 0.0,
                'JP_Sales': 0.0,
                'Other_Sales': 0.0,
                'Global_Sales': 0.0,
                'game_key': key,
                'metascore': g.get('metascore'),
                'userscore': g.get('userscore'),
                'total_hours': 0.0
            }
            nuevas_filas.append(fila)
            vistos_en_esta_corrida.add(key)

    if nuevas_filas:
        df_nuevos = pd.DataFrame(nuevas_filas)
        df_final = pd.concat([df, df_nuevos], ignore_index=True)
        df_final.to_csv(master_path, index=False)
        print(f"SUCCESS: Se agregaron {len(nuevas_filas)} juegos nuevos al dataset.")
        
        # También actualizar el .db si existe (opcional, pero recomendado)
        try:
            import sqlite3
            db_path = 'gameiq/data/gameiq.db'
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                df_final.to_sql('games', conn, if_exists='replace', index=False)
                conn.close()
                print("Base de datos SQLite actualizada.")
        except Exception as e:
            print(f"No se pudo actualizar SQLite: {e}")
    else:
        print("WARNING: No se encontraron juegos nuevos para agregar esta semana.")

if __name__ == "__main__":
    main()
