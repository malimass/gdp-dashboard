# app_streamlit_polar.py

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime
import json
import isodate

# Funzione per caricare più file JSON di allenamento
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

# Calcolo carico (robusto)
def compute_training_load(row):
    if row["Calorie"] > 0:
        return row["Calorie"]
    elif row["Durata"] > 0 and row["Frequenza Cardiaca Media"] > 0:
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

uploaded_files = st.sidebar.file_uploader("Carica uno o più file JSON da Polar Flow", type="json", accept_multiple_files=True)

if uploaded_files:
    df = load_multiple_json_training_data(uploaded_files)
    st.subheader("📋 Dati Allenamento Estratti")
    st.dataframe(df)

    if not df.empty:
        # Calcolo training load e analisi
        daily_loads, acwr = performance_analysis(df)

        st.subheader("📊 Analisi Predittiva – Coach Virtuale")
        st.line_chart(daily_loads.rename("Carico Giornaliero"))
        st.line_chart(acwr.rename("ACWR (Carico Acuto / Cronico)"))

        st.markdown("""
        ### Feedback:
        - ACWR > 1.5 = rischio infortunio
        - ACWR < 0.8 = carico troppo basso
        """)
    else:
        st.warning("Nessun dato valido da analizzare.")
else:
    st.info("Carica uno o più file JSON di allenamento esportati da Polar Flow per iniziare.")





