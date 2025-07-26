import streamlit as st
import json
import pandas as pd
import os

def load_data(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

def preprocess_data(data):
    distance_km = data['distance'] / 1000  # Convertire in km
    duration_sec = pd.to_timedelta(data['duration']).total_seconds()  # Convertire in secondi
    average_heart_rate = data['averageHeartRate']
    maximum_heart_rate = data['maximumHeartRate']
    calories_burned = data['kiloCalories']
    
    speed_avg_kmh = (distance_km / (duration_sec / 3600)) if duration_sec > 0 else 0
    pace_min_per_km = (duration_sec / distance_km) / 60 if distance_km > 0 else 0
    
    metrics = {
        'distance_km': distance_km,
        'duration_sec': duration_sec,
        'average_heart_rate': average_heart_rate,
        'maximum_heart_rate': maximum_heart_rate,
        'calories_burned': calories_burned,
        'speed_avg_kmh': speed_avg_kmh,
        'pace_min_per_km': pace_min_per_km
    }
    
    return metrics

def provide_feedback(metrics):
    feedback = []
    feedback.append(f"Hai percorso {metrics['distance_km']:.2f} km in {metrics['duration_sec'] / 60:.2f} minuti.")
    
    if metrics['average_heart_rate'] > 150:
        feedback.append("Attenzione: la tua frequenza cardiaca media è alta. Assicurati di recuperare adeguatamente.")
    elif metrics['average_heart_rate'] < 100:
        feedback.append("La tua frequenza cardiaca media è bassa. Potresti aumentare l'intensità dei tuoi allenamenti.")
    
    if metrics['speed_avg_kmh'] < 8:
        feedback.append("La tua velocità media è bassa. Considera di lavorare sulla tua resistenza.")
    else:
        feedback.append("Ottimo lavoro! La tua velocità media è buona.")
    
    if metrics['pace_min_per_km'] > 6:
        feedback.append("Il tuo passo medio è un po' lento. Prova a migliorare la tua velocità.")
    else:
        feedback.append("Il tuo passo medio è eccellente!")
    
    return feedback

# Streamlit App
st.title("Coach Virtuale per Allenamenti")

# Selezione del file JSON dalla cartella 'data'
data_folder = 'data'
json_files = [f for f in os.listdir(data_folder) if f.endswith('.json')]

selected_file = st.selectbox("Seleziona il tuo file JSON con i dati dell'allenamento", json_files)

if selected_file:
    file_path = os.path.join(data_folder, selected_file)
    
    # Carica i dati dal file JSON
    data = load_data(file_path)
    
    # Debug: Stampa i dati caricati
    st.write("Dati caricati:", data)
    
    # Preprocessa i dati
    metrics = preprocess_data(data)
    
    # Mostra le metriche
    st.subheader("Metriche dell'Allenamento")
    for key, value in metrics.items():
        st.write(f"{key}: {value:.2f}")
    
    # Fornisci feedback
    feedback = provide_feedback(metrics)
    st.subheader("Feedback")
    for line in feedback:
        st.write(line)


