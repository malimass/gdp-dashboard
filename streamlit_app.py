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
    if row["Durata"] > 0 and row["Frequenza Cardiaca Media"] > 0:
        return row["Durata"] * (row["Frequenza Cardiaca Media"] / 100)
    return 0

# Analisi predittiva semplificata

def performance_analysis(df):
    df["training_load"] = df.apply(compute_training_load, axis=1)
    df["FC Relativa (% max)"] = 100 * df["Frequenza Cardiaca Media"] / df["Frequenza Cardiaca Massima"].replace(0, np.nan)
    df["Efficienza cardiaca (km/bpm)"] = df["Distanza (km)"] / df["Frequenza Cardiaca Media"].replace(0, np.nan)
    df.set_index("date", inplace=True)
    df_daily = df.resample("D").sum()
    df_weekly = df.resample("W-MON").sum()
    daily_loads = df_daily["training_load"]
    short_term = daily_loads.rolling(window=3, min_periods=1).mean()
    long_term = daily_loads.rolling(window=7, min_periods=1).mean()
    acwr = short_term / long_term
    return df, df_daily, df_weekly, daily_loads, acwr

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

if not df.empty:
    st.subheader("📋 Dati Allenamento Estratti")
st.markdown("""
**Colonne principali:**
- **Durata**: in minuti
- **Distanza (km)**: distanza totale della sessione
- **FC Media / Massima**: valori della frequenza cardiaca (in bpm)
- **Calorie**: stima delle kcal bruciate
- **Sport**: attività eseguita (es. running, cycling)
""")
    st.dataframe(df)

    # Calcolo training load e analisi
    df_raw, df_daily, df_weekly, daily_loads, acwr = performance_analysis(df)

    st.subheader("📊 Analisi Predittiva – Coach Virtuale")
st.markdown("""
**Legenda grafici:**
- **Carico Giornaliero**: indica quanto stress fisiologico hai accumulato in un singolo giorno (minuti x FC media).
- **ACWR (Acute:Chronic Workload Ratio)**: rapporto tra carico acuto (3 giorni) e cronico (7 giorni). Valori ideali: **0.8–1.3**. Oltre 1.5 = rischio infortuni.
""")
    st.line_chart(daily_loads.rename("Carico Giornaliero"))
    st.line_chart(acwr.rename("ACWR (Carico Acuto / Cronico)"))

    # Feedback automatico
    latest_acwr = acwr.iloc[-1] if not acwr.empty else 0
    if latest_acwr > 1.5:
        st.error(f"⚠️ Rischio infortunio alto: ACWR = {latest_acwr:.2f}. Stai caricando troppo rispetto alla tua media settimanale.")
    elif latest_acwr < 0.8:
        st.info(f"ℹ️ Carico basso: ACWR = {latest_acwr:.2f}. Potresti perdere forma fisica.")
    elif latest_acwr >= 0.8 and latest_acwr <= 1.3:
        st.success(f"✅ Carico ottimale: ACWR = {latest_acwr:.2f}. Continua così!")
    else:
        st.warning(f"⚠️ ACWR = {latest_acwr:.2f}. Attenzione: possibile instabilità nel carico.")

    # Analisi settimanale
    st.subheader("📅 Carico Settimanale")
st.markdown("""
**Training Load Settimanale:**
Mostra il carico totale per ogni settimana (lunedì–domenica). Utile per verificare sovraccarichi o settimane troppo leggere.
""")
    st.bar_chart(df_weekly["training_load"].rename("Training Load Settimanale"))

    # Esportazione dati
    st.download_button("📥 Scarica dati allenamento in CSV", df.to_csv().encode(), file_name="report_allenamento.csv")

else:
    st.info("Carica file JSON o usa la modalità ?coach_mode=true per lettura automatica da cartella.")


