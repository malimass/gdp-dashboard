# app_streamlit_polar.py

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime
import json
import isodate
import os

# Funzione per salvare i file caricati nella cartella data/
def save_uploaded_files(uploaded_files, folder="data"):
    os.makedirs(folder, exist_ok=True)
    for uploaded_file in uploaded_files:
        file_path = os.path.join(folder, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

# Funzione per gestire eliminazione file
def delete_file(file_name, folder="data"):
    file_path = os.path.join(folder, file_name)
    if os.path.exists(file_path):
        os.remove(file_path)

# Funzione per caricare più file JSON di allenamento da caricamento manuale
@st.cache_data
def load_multiple_json_training_data(uploaded_files):
    records = []
    for uploaded_file in uploaded_files:
        try:
            data = json.load(uploaded_file)
            exercise = data.get("exercises", [{}])[0]
            duration_iso = exercise.get("duration", "PT0S")
            duration_seconds = isodate.parse_duration(duration_iso).total_seconds()

            # Estrazione e annotazione dettagliata dei campi JSON
            record = {
                "date": pd.to_datetime(exercise.get("startTime")),  # Data e ora di inizio
                "Durata": duration_seconds / 60,  # Durata in minuti
                "Distanza (km)": exercise.get("distance", 0) / 1000,  # Distanza in km
                "Calorie": exercise.get("kiloCalories", 0),  # Calorie consumate
                "Frequenza Cardiaca Media": exercise.get("heartRate", {}).get("avg", 0),
                "Frequenza Cardiaca Massima": exercise.get("heartRate", {}).get("max", 0),
                "Velocità Media (km/h)": exercise.get("speed", {}).get("avg", 0),
                "Velocità Massima (km/h)": exercise.get("speed", {}).get("max", 0),
                "Tempo in Zona 1": isodate.parse_duration(next((z.get("inZone", "PT0S") for z in exercise.get("zones", {}).get("heart_rate", []) if z.get("zoneIndex") == 1), "PT0S")).total_seconds() / 60,
                "Tempo in Zona 2": isodate.parse_duration(next((z.get("inZone", "PT0S") for z in exercise.get("zones", {}).get("heart_rate", []) if z.get("zoneIndex") == 2), "PT0S")).total_seconds() / 60,
                "Tempo in Zona 3": isodate.parse_duration(next((z.get("inZone", "PT0S") for z in exercise.get("zones", {}).get("heart_rate", []) if z.get("zoneIndex") == 3), "PT0S")).total_seconds() / 60,
                "Sport": exercise.get("sport", "N/D")
            }
            records.append(record)
        except Exception as e:
            st.warning(f"Errore nel file {uploaded_file.name}: {e}")
    df = pd.DataFrame(records)
    df = df.dropna(subset=["date"]).sort_values("date")
    return df

# Impostazioni base dell'app
st.set_page_config(page_title="Polar Training Dashboard", layout="wide")
st.title("📊 Polar Training Dashboard")

# File manager: carica ed elimina file
st.sidebar.header("📂 Gestione File")
with st.sidebar:
    uploaded_files = st.file_uploader("Carica file JSON", type="json", accept_multiple_files=True)
    if uploaded_files:
        save_uploaded_files(uploaded_files)
        st.success("File salvati correttamente. Ricaricare la pagina per aggiornare i dati.")

    existing_files = [f for f in os.listdir("data") if f.endswith(".json")]
    file_to_delete = st.selectbox("Seleziona file da eliminare", options=[""] + existing_files)
    if file_to_delete and st.button("Elimina File"):
        delete_file(file_to_delete)
        st.success(f"File '{file_to_delete}' eliminato. Ricaricare la pagina per aggiornare i dati.")

# Caricamento automatico dei file dalla cartella 'data'
file_names = [f for f in os.listdir("data") if f.endswith(".json")]
data_files = [open(os.path.join("data", f), "rb") for f in file_names]
df = load_multiple_json_training_data(data_files) if data_files else pd.DataFrame()






