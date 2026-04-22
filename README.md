# 🎮 GameIQ: Dashboard de Inteligencia de Mercado Gaming

GameIQ es una plataforma avanzada de análisis de datos para la industria de los videojuegos. El sistema integra datos históricos (1980-2016) con tendencias actuales de Steam (2024-2026), modelos de Machine Learning para predicción de ventas y un motor de Inteligencia Artificial (Ollama) para análisis de sentimiento y estrategia.

## 🚀 Gaps que resuelve
1. **Falta de Contexto Histórico**: Conecta el pasado de la industria con el presente de Steam.
2. **Predicción Incierta**: Utiliza Random Forest para estimar ventas de futuros lanzamientos.
3. **Brecha Crítica-Comunidad**: Identifica juegos donde la prensa y los jugadores no están de acuerdo.
4. **Análisis de Géneros Saturados**: Detecta qué géneros están creciendo realmente frente a los que solo tienen volumen.
5. **Accionabilidad Basada en IA**: Traduce números complejos en recomendaciones estratégicas para desarrolladores indies.

## 🛠️ Instalación Local

1. Clonar el repositorio:
   ```bash
   git clone <tu-repo-url>
   cd gameiq
   ```

2. Crear y activar entorno virtual:
   ```bash
   python -m venv gameiq_env
   source gameiq_env/bin/activate  # En Linux/Mac
   .\gameiq_env\Scripts\Activate.ps1  # En Windows
   ```

3. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

4. **Importante**: Tener instalado [Ollama](https://ollama.com/) y descargar el modelo llama3:
   ```bash
   ollama pull llama3
   ```

## 💻 Ejecución

Para lanzar el dashboard interactivo:
```bash
streamlit run app.py
```

---
**Desarrollado por:** Tapias · Reyes · Rivas | **Unicórdoba 2026**
