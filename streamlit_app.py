import streamlit as st
import json
import pandas as pd

def load_data(files):
    all_data = []
    for file in files:
        data = json.load(file)
        all_data.append(data)
    return all_data

def preprocess_data(data_list):
    metrics_list = []
    
    for data in data_list:
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
        
        metrics_list.append(metrics)
    
    return metrics_list

def aggregate_metrics(metrics_list):
    # Aggrega le metriche per fornire un'analisi complessiva
    total_distance = sum(metric['distance_km'] for metric in metrics_list)
    total_duration = sum(metric['duration_sec'] for metric in metrics_list)
    total_calories = sum(metric['calories_burned'] for metric in metrics_list)
    
    average_heart_rate = sum(metric['average_heart_rate'] for metric in metrics_list) / len(metrics_list)
    average_speed = (total_distance / (total_duration / 3600)) if total_duration > 0 else 0
    average_pace = (total_duration / total_distance) / 60 if total_distance > 0 else 0
    
    aggregated_metrics = {
        'total_distance_km': total_distance,
        'total_duration_sec': total_duration,
        'average_heart_rate': average_heart_rate,
        'total_calories_burned': total_calories,
        'average_speed_kmh': average_speed,
        'average_pace_min_per_km': average_pace
    }
    
    return aggregated_metrics

def provide_feedback(aggregated_metrics):
    feedback = []
    feedback.append(f"Hai percorso un totale di {aggregated_metrics['total_distance_km']:.2f} km in {aggregated_metrics['total_duration_sec'] / 60:.2f} minuti.")
    
    if aggregated_metrics['average_heart_rate'] > 150:
        feedback.append("Attenzione: la tua frequenza cardiaca media è alta. Assicurati di recuperare adeguatamente.")
    elif aggregated_metrics['average_heart_rate'] < 100:
        feedback.append("La tua frequenza cardiaca media è bassa. Potresti aumentare l'intensità dei tuoi allenamenti.")
    
    if aggregated_metrics['average_speed_kmh'] < 8:
        feedback.append("La tua velocità media è bassa. Considera di lavorare sulla tua resistenza.")
    else:
        feedback.append("Ottimo lavoro! La tua velocità media è buona.")
    
    if aggregated_metrics['average_pace_min_per_km'] > 6:
        feedback.append("Il tuo passo medio è un po' lento. Prova a migliorare la tua velocità.")
    else:
        feedback.append("Il tuo passo medio è eccellente!")
    
    return feedback

# Streamlit App
st.title("Coach Virtuale per Allenamenti")

# Caricamento di file JSON multipli
uploaded_files = st.file_uploader("Carica i tuoi file JSON con i dati degli allenamenti", type="json", accept_multiple_files=True)

if uploaded_files:
    # Carica i dati dai file JSON
    data_list = load_data(uploaded_files)
    
    # Preprocessa i dati
    metrics_list = preprocess_data(data_list)
    
    # Aggrega le metriche
    aggregated_metrics = aggregate_metrics(metrics_list)
    
    # Mostra le metriche aggregate
    st.subheader("Metriche Totali degli Allenamenti")
    for key, value in aggregated_metrics.items():
        st.write(f"{key}: {value:.2f}")
    
    # Fornisci feedback
    feedback = provide_feedback(aggregated_metrics)
    st.subheader("Feedback")
    for line in feedback:
        st.write(line)



