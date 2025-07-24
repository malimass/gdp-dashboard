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

            record = {
                "date": pd.to_datetime(exercise.get("startTime")),
                "Durata": duration_seconds / 60,
                "Distanza (km)": exercise.get("distance", 0) / 1000,
                "Calorie": exercise.get("kiloCalories", 0),
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

# Resto del codice invariato...










