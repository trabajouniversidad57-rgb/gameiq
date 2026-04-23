import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import pickle
import os

# Rutas dinámicas para evitar errores dependiendo desde dónde se ejecuta
current_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(os.path.dirname(current_dir), 'data')
model_path = os.path.join(data_dir, 'modelo_ventas.pkl')
encoder_path = os.path.join(data_dir, 'encoders.pkl')

def entrenar_modelo():
    print("Cargando datos para entrenamiento...")
    df = pd.read_csv(os.path.join(data_dir, 'master_dataset.csv'))
    
    # 1. Filtrar
    df_ml = df.dropna(subset=['metascore', 'Global_Sales']).copy()
    
    # 2. Features y Target
    features = ['Genre', 'Platform', 'Year', 'metascore']
    X = df_ml[features].copy()
    y = df_ml['Global_Sales']
    
    # 3. Encoders
    le_genre = LabelEncoder()
    le_platform = LabelEncoder()
    
    X['Genre'] = le_genre.fit_transform(X['Genre'])
    X['Platform'] = le_platform.fit_transform(X['Platform'])
    
    # 4. Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 5. Entrenar
    print("Entrenando RandomForestRegressor...")
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # 6. Métricas
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    
    print("\n--- Métricas del Modelo ---")
    print(f"R2 Score: {r2:.4f}")
    print(f"MAE: {mae:.4f}M")
    print(f"RMSE: {rmse:.4f}M")
    
    # 7. Guardar
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    
    encoders = {'Genre': le_genre, 'Platform': le_platform, 'MAE': mae}
    with open(encoder_path, 'wb') as f:
        pickle.dump(encoders, f)
    
    print(f"\nModelo y encoders guardados en {data_dir}")
    return model, encoders

def predecir(genero, plataforma, anio, metascore_estimado=75):
    if not os.path.exists(model_path) or not os.path.exists(encoder_path):
        return "Error: Modelo no entrenado."
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    with open(encoder_path, 'rb') as f:
        encoders = pickle.load(f)
    
    le_g = encoders['Genre']
    le_p = encoders['Platform']
    mae = encoders.get('MAE', 0.5) # Default MAE si no existe
    
    try:
        g_encoded = le_g.transform([genero])[0]
    except ValueError:
        g_encoded = le_g.transform([le_g.classes_[0]])[0] # Fallback al primero
        
    try:
        p_encoded = le_p.transform([plataforma])[0]
    except ValueError:
        p_encoded = le_p.transform([le_p.classes_[0]])[0] # Fallback al primero
    
    input_data = pd.DataFrame([[g_encoded, p_encoded, anio, metascore_estimado]], 
                             columns=['Genre', 'Platform', 'Year', 'metascore'])
    
    pred = model.predict(input_data)[0]
    
    return {
        'prediccion_millones': round(pred, 2),
        'rango_bajo': round(max(0, pred - mae), 2),
        'rango_alto': round(pred + mae, 2)
    }

if __name__ == "__main__":
    # Entrenar si no existe o forzar entrenamiento
    entrenar_modelo()
    
    # Prueba
    print("\nPrueba de Predicción:")
    resultado = predecir("Action", "PS4", 2024, 85)
    print(f"Entrada: Action, PS4, 2024, Score: 85")
    print(f"Resultado: {resultado}")
