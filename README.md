# 🎮 GameIQ: Inteligencia de Mercado para Videojuegos

GameIQ es una plataforma de análisis avanzado diseñada para la industria del gaming. Combina datos históricos (1980-2016) con tendencias actuales de Steam (2024-2026) y modelos de IA para ofrecer una visión 360° del mercado.

## 🚀 Gaps que resuelve
1. **Falta de Contexto Histórico**: Conecta décadas de ventas con el mercado actual.
2. **Predicción Incierta**: Estima ventas de futuros lanzamientos usando Random Forest.
3. **Brecha Crítica-Comunidad**: Identifica discrepancias entre la prensa y los jugadores.
4. **Saturación de Géneros**: Detecta nichos con alto crecimiento y calidad.
5. **Accionabilidad con IA**: Transforma datos complejos en estrategias mediante Gemini AI.

## 🛠️ Instalación Local

1. Clonar el repositorio.
2. Crear un entorno virtual: `python -m venv gameiq_env`.
3. Instalar dependencias: `pip install -r requirements.txt`.
4. Configurar tu clave de API en un archivo `.env`:
   ```text
   GEMINI_API_KEY=tu_api_key_aqui
   ```
5. Ejecutar la aplicación: `streamlit run app.py`.

## 📊 Datos
**Nota**: Los datasets originales (`vgsales.csv`, `twitch_data.csv`, `metacritic_games.csv`) deben descargarse de **Kaggle** y procesarse siguiendo el pipeline de limpieza incluido en este proyecto.
