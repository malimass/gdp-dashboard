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
                "Sport": exercise.get("sport", "N/D")
            }
            records.append(record)
        except Exception as e:
            st.warning(f"Errore nel file {uploaded_file.name}: {e}")
    df = pd.DataFrame(records)
    df = df.dropna(subset=["date"]).sort_values("date")
    return df

# Funzione per caricare file JSON da cartella predefinita (per il coach)
@st.cache_data
def load_json_from_folder(folder_path="data"):
    records = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):
            try:
                with open(os.path.join(folder_path, filename)) as f:
                    data = json.load(f)
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
                        "Sport": exercise.get("sport", "N/D")
                    }
                    records.append(record)
            except Exception as e:
                st.warning(f"Errore nel file {filename}: {e}")
    df = pd.DataFrame(records)
    df = df.dropna(subset=["date"]).sort_values("date")
    return df

# Calcolo carico (robusto)
def compute_training_load(row):
    # Calcola il training load usando sempre Durata × FC Media
    if row["Durata"] > 0 and row["Frequenza Cardiaca Media"] > 0:
        return row["Durata"] * (row["Frequenza Cardiaca Media"] / 100)
    return 0

# Analisi predittiva semplificata
def performance_analysis(df):
    df["training_load"] = df.apply(compute_training_load, axis=1)
    df.set_index("date", inplace=True)
    df = df.resample("D").sum()  # aggregazione giornaliera
    daily_loads = df["training_load"]
    short_term = daily_loads.rolling(window=3, min_periods=1).mean()
    long_term = daily_loads.rolling(window=7, min_periods=1).mean()
    acwr = short_term / long_term
    return daily_loads, acwr

# UI Streamlit
st.title("Polar Flow Analyzer – Preparatore Virtuale")

# Caricamento automatico sempre dalla cartella data/
df = load_json_from_folder("data")
st.success("I dati vengono caricati dalla cartella condivisa `/data`")

# Se si caricano file, vengono salvati e usati al volo
uploaded_files = st.sidebar.file_uploader("Carica uno o più file JSON da Polar Flow", type="json", accept_multiple_files=True)
if uploaded_files:
    save_uploaded_files(uploaded_files, "data")
    df = load_multiple_json_training_data(uploaded_files)
    uploaded_files = st.sidebar.file_uploader("Carica uno o più file JSON da Polar Flow", type="json", accept_multiple_files=True)
    if uploaded_files:
        save_uploaded_files(uploaded_files, "data")
        df = load_multiple_json_training_data(uploaded_files)
    else:
        df = pd.DataFrame()

if not df.empty:
    st.subheader("📋 Dati Allenamento Estratti")
    st.dataframe(df)

    # Calcolo training load e analisi
    daily_loads, acwr = performance_analysis(df)

    st.subheader("📊 Coach Virtuale")
    st.line_chart(daily_loads.rename("Carico Giornaliero"))
    st.line_chart(acwr.rename("ACWR (Carico Acuto / Cronico)"))

    st.markdown("""
    ### Analisi Rischio:
    - ACWR > 1.5 = rischio infortunio
    - ACWR < 0.8 = carico troppo basso
    """)
else:
    st.info("Carica file JSON o usa la modalità ?coach_mode=true per lettura automatica da cartella.")
