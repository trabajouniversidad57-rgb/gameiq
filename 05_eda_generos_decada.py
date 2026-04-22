import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# Rutas
input_path = 'gameiq/data/master_dataset.csv'
output_dir = 'gameiq/outputs'
os.makedirs(output_dir, exist_ok=True)

# 1. Cargar datos
df = pd.read_csv(input_path)

# 2. Crear columna Década
df['Decada'] = (df['Year'] // 10 * 10).astype(int).astype(str) + "s"

# 3. Gráfica de barras apiladas: Dominio de géneros por década
# Filtrar años razonables (1980-2016 según instrucción)
df_decada = df[df['Year'] <= 2016].copy()
decada_genre = df_decada.groupby(['Decada', 'Genre'])['Global_Sales'].sum().reset_index()

fig1 = px.bar(
    decada_genre, 
    x='Decada', 
    y='Global_Sales', 
    color='Genre',
    title='Dominio de géneros por década (1980-2016)',
    labels={'Global_Sales': 'Ventas Totales (Millones)', 'Decada': 'Década'},
    category_orders={"Decada": ["1980s", "1990s", "2000s", "2010s"]}
)
fig1.update_layout(template='plotly_dark', barmode='stack')
fig1.write_html(os.path.join(output_dir, '02_generos_por_decada.html'))

# 4. Evolución anual de los TOP 5 géneros históricos
top_5_genres = df.groupby('Genre')['Global_Sales'].sum().nlargest(5).index.tolist()

# Datos anuales para los top 5
df_top5 = df[df['Genre'].isin(top_5_genres)].copy()
annual_trends = df_top5.groupby(['Year', 'Genre']).agg({
    'Global_Sales': 'sum',
    'total_hours': 'sum'
}).reset_index()

# Crear gráfica de líneas (ventas)
fig2 = px.line(
    annual_trends,
    x='Year',
    y='Global_Sales',
    color='Genre',
    title='Evolución anual de Ventas: Top 5 Géneros Históricos',
    labels={'Global_Sales': 'Ventas Globales (Millones)', 'Year': 'Año'}
)

# Añadir datos de Twitch (horas vistas) como puntos o líneas adicionales si existen
# Como el rango de escala es muy diferente, añadiremos una nota o usaremos un eje secundario
# Para simplicidad y claridad, haremos una gráfica combinada o simplemente mostraremos ventas
# La instrucción pide "cruzando datos... donde existan"

# Filtrar donde hay datos de Twitch
twitch_data = annual_trends[annual_trends['total_hours'] > 0]
if not twitch_data.empty:
    for genre in top_5_genres:
        genre_data = twitch_data[twitch_data['Genre'] == genre]
        if not genre_data.empty:
             fig2.add_trace(go.Scatter(
                x=genre_data['Year'], 
                y=genre_data['Global_Sales'], # Usamos el mismo eje Y pero marcamos presencia en Twitch
                mode='markers',
                name=f'{genre} (Streaming)',
                marker=dict(size=12, symbol='star', line=dict(width=2, color='white')),
                hovertemplate=f"Género: {genre}<br>Año: %{{x}}<br>Total Horas Twitch: {genre_data['total_hours'].iloc[0]:,.0f}"
            ))

fig2.update_layout(template='plotly_dark')
fig2.write_html(os.path.join(output_dir, '02b_evolucion_top_generos.html'))

# 5. Imprimir TOP 3 géneros por década
print("\n--- Top 3 Géneros por Década (Ventas Globales) ---")
for decada in sorted(decada_genre['Decada'].unique()):
    top_3 = decada_genre[decada_genre['Decada'] == decada].nlargest(3, 'Global_Sales')
    print(f"\n{decada}:")
    for i, (idx, row) in enumerate(top_3.iterrows(), 1):
        print(f"  {i}. {row['Genre']} - {row['Global_Sales']:.2f}M")

print(f"\nGráficas guardadas en {output_dir}")
