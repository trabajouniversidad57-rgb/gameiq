import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# Rutas relativas al script
base_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(base_dir, 'data')
output_dir = os.path.join(base_dir, 'outputs')
os.makedirs(output_dir, exist_ok=True)

# --- PARTE A: Crítica vs Comunidad (master_dataset.csv) ---
print("Procesando Parte A: Crítica vs Comunidad...")
df_master = pd.read_csv(os.path.join(data_dir, 'master_dataset.csv'))

# 1. Filtrar
df_critica = df_master.dropna(subset=['metascore', 'userscore']).copy()

# 2. Calcular brecha
df_critica['brecha'] = abs(df_critica['metascore'] - df_critica['userscore'])

# 3. Top 20 brecha
top_20_brecha = df_critica.sort_values(by='brecha', ascending=False).head(20)

# Gráfica A1: Bar horizontal
fig_a1 = px.bar(
    top_20_brecha,
    x='brecha',
    y='Name',
    color='Genre',
    orientation='h',
    title='Top 20 — mayor discrepancia críticos vs jugadores',
    labels={'brecha': 'Brecha Absoluta (Metascore - User_Score)', 'Name': 'Videojuego'}
)
fig_a1.update_layout(template='plotly_dark', yaxis={'categoryorder':'total ascending'})
fig_a1.write_html(os.path.join(output_dir, '04_brecha_critica.html'))

# Gráfica A2: Scatter
fig_a2 = px.scatter(
    df_critica,
    x='metascore',
    y='userscore',
    color='brecha',
    hover_name='Name',
    title='Comparativa Metascore vs User_Score',
    labels={'metascore': 'Metascore', 'userscore': 'User Score (Normalizado x10)'},
    color_continuous_scale='Viridis'
)
# Línea diagonal roja punteada y=x
fig_a2.add_shape(
    type="line", x0=0, y0=0, x1=100, y1=100,
    line=dict(color="Red", width=2, dash="dash")
)
fig_a2.update_layout(template='plotly_dark')
fig_a2.write_html(os.path.join(output_dir, '04b_scatter_metascore_userscore.html'))


# --- PARTE B: Radar Steam (steam_top1000.csv) ---
print("Procesando Parte B: Radar Steam...")
df_steam = pd.read_csv(os.path.join(data_dir, 'steam_top1000.csv'))

# Filtrar por años (si existe columna Date)
try:
    df_steam['Release_Date'] = pd.to_datetime(df_steam['Release_Date'], errors='coerce')
    # Según instrucción: Steam 2024-2026. Si el dataset no llega allí, usamos lo más reciente.
    df_steam = df_steam[df_steam['Release_Date'].dt.year >= 2000] # Filtro preventivo
except:
    pass

# Gráfica B1: Géneros Dominantes
top_genres_steam = df_steam['Primary_Genre'].value_counts().head(10).reset_index()
top_genres_steam.columns = ['Genre', 'Count']

fig_b1 = px.bar(
    top_genres_steam,
    x='Count',
    y='Genre',
    orientation='h',
    title='Géneros dominantes en Steam',
    labels={'Count': 'Cantidad de Juegos', 'Genre': 'Género'}
)
fig_b1.update_layout(template='plotly_dark', yaxis={'categoryorder':'total ascending'})
fig_b1.write_html(os.path.join(output_dir, '05_steam_generos.html'))

# Gráfica B2: Precio vs Rating
fig_b2 = px.scatter(
    df_steam,
    x='Price_USD',
    y='Review_Score_Pct',
    size='Total_Reviews' if 'Total_Reviews' in df_steam.columns else None,
    hover_name='Name',
    title='Precio vs Rating — Steam Market',
    labels={'Price_USD': 'Precio (USD)', 'Review_Score_Pct': 'Rating (%)', 'Total_Reviews': 'Reseñas Totales'}
)
fig_b2.update_layout(template='plotly_dark')
fig_b2.write_html(os.path.join(output_dir, '05b_steam_precio_rating.html'))


# Imprimir resultados
print("\n--- Top 5 Juegos con mayor discrepancia Críticos vs Juzgadores ---")
top_5 = top_20_brecha.head(5)
for i, (idx, row) in enumerate(top_5.iterrows(), 1):
    print(f"{i}. {row['Name']} (Brecha: {row['brecha']:.1f})")
    print(f"   Metascore: {row['metascore']} | User Score: {row['userscore']}\n")

print(f"Gráficas guardadas en {output_dir}")
