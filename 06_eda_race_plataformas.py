import pandas as pd
import plotly.express as px
import os

# Rutas
input_path = 'gameiq/data/master_dataset.csv'
output_dir = 'gameiq/outputs'
os.makedirs(output_dir, exist_ok=True)

# 1. Cargar datos
df = pd.read_csv(input_path)

# Filtrar hasta 2016 como solicitó el usuario en pasos anteriores
df = df[df['Year'] <= 2016]

# 2. Preparar datos para Bar Chart Race (Guerra de Consolas)
# Agrupar por Año y Plataforma
df_agg = df.groupby(['Year', 'Platform'])['Global_Sales'].sum().reset_index()

# Filtrar las 15 plataformas más exitosas históricamente
top_15_platforms = df.groupby('Platform')['Global_Sales'].sum().nlargest(15).index.tolist()
df_race = df_agg[df_agg['Platform'].isin(top_15_platforms)].copy()

# Para que la animación sea fluida, necesitamos que cada año tenga todas las plataformas
years = sorted(df_race['Year'].unique())
all_combinations = pd.MultiIndex.from_product([years, top_15_platforms], names=['Year', 'Platform']).to_frame(index=False)
df_race = pd.merge(all_combinations, df_race, on=['Year', 'Platform'], how='left').fillna(0)

# Calcular ventas acumuladas
df_race = df_race.sort_values(['Platform', 'Year'])
df_race['Cumulative_Sales'] = df_race.groupby('Platform')['Global_Sales'].cumsum()

# 3. Crear Bar Chart Race Animado
fig1 = px.bar(
    df_race,
    x="Cumulative_Sales",
    y="Platform",
    color="Platform",
    animation_frame="Year",
    orientation='h',
    range_x=[0, df_race['Cumulative_Sales'].max() * 1.1],
    title="Guerra de consolas — ventas acumuladas por año (1980-2016)",
    labels={'Cumulative_Sales': 'Ventas Acumuladas (Millones)', 'Platform': 'Plataforma'},
    # Ordenar por valor en cada frame
    category_orders={"Platform": df.groupby('Platform')['Global_Sales'].sum().sort_values(ascending=False).index.tolist()}
)

# Ajustar velocidad y estética
fig1.layout.updatemenus[0].buttons[0].args[1]['frame']['duration'] = 600
fig1.layout.updatemenus[0].buttons[0].args[1]['transition']['duration'] = 400
fig1.update_layout(template='plotly_dark', showlegend=False)
fig1.update_yaxes(autorange="reversed") # Mostrar el líder arriba

fig1.write_html(os.path.join(output_dir, '03_race_plataformas.html'))

# 4. Ciclo de Vida: Top 8 plataformas
top_8_platforms = df.groupby('Platform')['Global_Sales'].sum().nlargest(8).index.tolist()
df_life = df_agg[df_agg['Platform'].isin(top_8_platforms)]

fig2 = px.line(
    df_life,
    x='Year',
    y='Global_Sales',
    color='Platform',
    title='Ciclo de Vida de las TOP 8 Plataformas (Ventas Anuales)',
    labels={'Global_Sales': 'Ventas Anuales (Millones)', 'Year': 'Año'},
    markers=True
)
fig2.update_layout(template='plotly_dark')
fig2.write_html(os.path.join(output_dir, '03b_ciclo_vida_plataformas.html'))

print(f"Dataset de carrera preparado con {len(df_race)} registros.")
print(f"Gráficas generadas exitosamente en {output_dir}")
