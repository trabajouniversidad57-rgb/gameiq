# Hallazgos del Análisis Exploratorio de Datos (EDA)

Este documento resume los descubrimientos clave realizados durante la fase de análisis del proyecto GameIQ, utilizando los datasets integrados de ventas, críticas y streaming.

## Hallazgo 1: Correlación Débil entre Crítica y Ventas
- **Dato encontrado**: El coeficiente de correlación de Pearson es **0.226**.
- **Lo que significa**: Existe una relación positiva pero débil entre la puntuación de Metacritic y el éxito comercial. Esto significa que una buena crítica ayuda, pero factores como el marketing, la franquicia y el género tienen un peso mucho mayor en el volumen de ventas finales.
- **Gráfica de soporte**: outputs/01_correlacion_ventas_critica.html
- **Dataset fuente**: master_dataset.csv
- **Gap que resuelve**: Gap 1 (Impacto de la crítica en el éxito comercial)

## Hallazgo 2: Dominio Sostenido del Género Acción
- **Dato encontrado**: El género **Action** dominó los 2000s con **858.91M** en ventas y los 2010s con **673.49M**.
- **Lo que significa**: El género de acción ha logrado mantenerse como el motor económico de la industria durante más de dos décadas consecutivas. La transición hacia experiencias más cinemáticas y dinámicas ha resonado consistentemente con la audiencia global.
- **Gráfica de soporte**: outputs/02_generos_por_decada.html
- **Dataset fuente**: master_dataset.csv
- **Gap que resuelve**: Gap 2 (Evolución histórica de géneros dominantes)

## Hallazgo 3: El Hito Histórico de PlayStation 2
- **Dato encontrado**: La plataforma **PS2** alcanzó el pico más alto de ventas anuales en **2004** con **211.78M** de unidades de software vinculadas.
- **Lo que significa**: La PS2 representa la era de mayor consolidación de una sola plataforma en la historia, estableciendo un estándar de adopción masiva que difícilmente se ha repetido con la misma intensidad por sus sucesoras.
- **Gráfica de soporte**: outputs/03_race_plataformas.html
- **Dataset fuente**: master_dataset.csv
- **Gap que resuelve**: Gap 3 (Competencia y ciclos de vida de consolas)

## Hallazgo 4: Polarización Extrema en Títulos Deportivos
- **Dato encontrado**: El juego **World Series Baseball 2K3** presenta la mayor brecha crítica/usuario con **89.0 puntos** de diferencia.
- **Lo que significa**: Existe un segmento de juegos, mayoritariamente deportivos o de simulación, donde los criterios técnicos de la prensa especializada divergen totalmente de la experiencia o expectativas de la comunidad. Esta desconexión representa un riesgo de marca para los desarrolladores.
- **Gráfica de soporte**: outputs/04_brecha_critica.html
- **Dataset fuente**: master_dataset.csv
- **Gap que resuelve**: Gap 4 (Consenso entre prensa especializada y jugadores)

## Hallazgo 5: La Hegemonía de la Acción en el Mercado Moderno de PC
- **Dato encontrado**: El género **Action** es el más frecuente en Steam con **579 juegos** registrados en el top 1000.
- **Lo que significa**: La tendencia histórica de dominio de la acción observada en consolas se ha trasladado con éxito al ecosistema de PC (Steam), consolidándose como el género más rentable y con mayor volumen de lanzamientos competitivos actuales.
- **Gráfica de soporte**: outputs/05_steam_generos.html
- **Dataset fuente**: steam_top1000.csv
- **Gap que resuelve**: Gap 5 (Contexto histórico vs tendencias actuales del mercado PC)
