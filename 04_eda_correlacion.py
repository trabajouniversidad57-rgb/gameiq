import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# Rutas relativas al script
base_dir = os.path.dirname(os.path.abspath(__file__))
input_path = os.path.join(base_dir, 'data', 'master_dataset.csv')
output_dir = os.path.join(base_dir, 'outputs')
os.makedirs(output_dir, exist_ok=True)

# 1. Cargar y filtrar
df = pd.read_csv(input_path)
df_ana = df.dropna(subset=['metascore', 'Global_Sales']).copy()

# 2. Calcular Correlación de Pearson
r = df_ana['metascore'].corr(df_ana['Global_Sales'])

# 3. Interpretación automática
if r > 0.5:
    interp = "fuerte"
elif r > 0.3:
    interp = "moderada"
else:
    interp = "débil"

print(f"Correlación Metascore vs Ventas Globales: {r:.3f}")
print(f"Interpretación: La correlación es {interp}.")

# 4. Scatter Plot con Plotly
fig1 = px.scatter(
    df_ana, 
    x='metascore', 
    y='Global_Sales',
    color='Genre',
    hover_name='Name',
    title=f'Correlación Metascore vs Ventas Globales (r = {r:.3f})',
    opacity=0.6,
    labels={'metascore': 'Metascore', 'Global_Sales': 'Ventas Globales (Millones)'}
)
fig1.update_layout(template='plotly_dark')
fig1.write_html(os.path.join(output_dir, '01_correlacion_ventas_critica.html'))

# 5. Box Plot por rango de Metascore
bins = [0, 59, 74, 89, 100]
labels = ['0-59 (Bajo)', '60-74 (Medio)', '75-89 (Alto)', '90-100 (Excelente)']
df_ana['score_range'] = pd.cut(df_ana['metascore'], bins=bins, labels=labels)

fig2 = px.box(
    df_ana,
    x='score_range',
    y='Global_Sales',
    color='score_range',
    title='Distribución de Ventas por Rango de Metascore',
    points='outliers', # Mostrar outliers
    labels={'score_range': 'Rango de Puntuación', 'Global_Sales': 'Ventas Globales (Millones)'}
)
# Ajustar el eje Y para ver mejor las cajas (limitado por outliers extremos)
fig2.update_yaxes(range=[-0.5, 15]) 
fig2.update_layout(template='plotly_dark')
fig2.write_html(os.path.join(output_dir, '01b_ventas_por_rango_score.html'))

print(f"\nGráficas guardadas en {output_dir}")
