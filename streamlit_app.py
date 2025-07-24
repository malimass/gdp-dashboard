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

            # Estrazione e annotazione dettagliata dei campi JSON
            record = {
                "date": pd.to_datetime(exercise.get("startTime")),  # Data e ora di inizio
                "Durata": duration_seconds / 60,  # Durata in minuti
                "Distanza (km)": exercise.get("distance", 0) / 1000,  # Distanza in km
                "Calorie": exercise.get("kiloCalories", 0),  # Calorie consumate
                "Frequenza Cardiaca Media": exercise.get("heartRate", {}).get("avg", 0),  # FC media
                "Frequenza Cardiaca Massima": exercise.get("heartRate", {}).get("max", 0),  # FC massima
                "Velocità Media (km/h)": exercise.get("speed", {}).get("avg", 0),  # Velocità media
                "Velocità Massima (km/h)": exercise.get("speed", {}).get("max", 0),  # Velocità max
                # Tempo in zona cardiaca 1 (bassa intensità)
                "Tempo in Zona 1": isodate.parse_duration(next((z.get("inZone", "PT0S") for z in exercise.get("zones", {}).get("heart_rate", []) if z.get("zoneIndex") == 1), "PT0S")).total_seconds() / 60,
                # Tempo in zona cardiaca 2 (aerobica)
                "Tempo in Zona 2": isodate.parse_duration(next((z.get("inZone", "PT0S") for z in exercise.get("zones", {}).get("heart_rate", []) if z.get("zoneIndex") == 2), "PT0S")).total_seconds() / 60,
                # Tempo in zona cardiaca 3 (soglia)
                "Tempo in Zona 3": isodate.parse_duration(next((z.get("inZone", "PT0S") for z in exercise.get("zones", {}).get("heart_rate", []) if z.get("zoneIndex") == 3), "PT0S")).total_seconds() / 60,
                "Sport": exercise.get("sport", "N/D")  # Tipo di sport
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

# Caricamento automatico dei file dalla cartella 'data'
file_names = [f for f in os.listdir("data") if f.endswith(".json")]
data_files = [open(os.path.join("data", f), "rb") for f in file_names]
df = load_multiple_json_training_data(data_files) if data_files else pd.DataFrame()

# Visualizzazione base se ci sono dati
if not df.empty:
    st.subheader("📅 Sessioni di Allenamento")
    st.dataframe(df)

    st.subheader("📈 Grafico: FC Media e Durata")
    st.line_chart(df.set_index("date")[["Frequenza Cardiaca Media", "Durata"]])

    st.subheader("⚙️ Analisi Approfondita")

    # Analisi del rischio infortuni basato su ACWR (Acute:Chronic Workload Ratio)
    df["Carico Allenamento"] = df["Durata"] * df["Frequenza Cardiaca Media"]
    df = df.set_index("date")
    weekly_load = df["Carico Allenamento"].resample("W").sum()
    chronic_load = weekly_load.rolling(window=4).mean()
    monthly_load = df["Carico Allenamento"].resample("M").sum()
    monthly_chronic = monthly_load.rolling(window=2).mean()
    acwr_monthly = monthly_load / monthly_chronic
    acwr = weekly_load / chronic_load

    st.subheader("📊 Andamento ACWR settimanale")
    st.line_chart(acwr)

    st.subheader("📆 Andamento ACWR mensile")
    st.line_chart(acwr_monthly)

    latest_acwr = acwr.dropna().iloc[-1] if not acwr.dropna().empty else None
    if latest_acwr:
        if latest_acwr > 1.5:
            st.error(f"🚨 ACWR = {latest_acwr:.2f} → Alto rischio infortunio. Riduci il carico.")
        elif latest_acwr < 0.8:
            st.warning(f"⚠️ ACWR = {latest_acwr:.2f} → Carico troppo basso, potenziale calo di performance.")

    # Analisi zona cardiaca
    st.subheader("🧠 Tempo in Zona Cardiaca (minuti)")
    zona_df = df[["Tempo in Zona 1", "Tempo in Zona 2", "Tempo in Zona 3"]]
    st.area_chart(zona_df)

    # Confronto Velocità Media vs Tempo in Zona 2
    st.subheader("📉 Confronto: Velocità Media vs Tempo in Zona 2")
    fig, ax1 = plt.subplots()
    ax2 = ax1.twinx()
    df[["Velocità Media (km/h)"]].plot(ax=ax1, color="tab:blue", label="Velocità Media")
    df[["Tempo in Zona 2"]].plot(ax=ax2, color="tab:red", label="Tempo in Zona 2 (min)")
    ax1.set_ylabel("Velocità Media (km/h)", color="tab:blue")
    ax2.set_ylabel("Tempo in Zona 2 (min)", color="tab:red")
    st.pyplot(fig)

    # Punteggio settimanale
    st.subheader("🏅 Punteggio Settimanale Allenamento")
    def calculate_score(row):
        score = 0
        if row["Frequenza Cardiaca Media"] >= 100: score += 1
        if row["Durata"] >= 60: score += 1
        if row["Tempo in Zona 2"] >= 20: score += 1
        if row["Velocità Media (km/h)"] >= 5.5: score += 1
        return score

    df["Punteggio"] = df.apply(calculate_score, axis=1)
    weekly_score = df[["Punteggio"]].resample("W").mean()
    monthly_score = df[["Punteggio"]].resample("M").mean()
    st.subheader("📅 Media Settimanale")
    st.bar_chart(weekly_score)

    st.subheader("📆 Media Mensile")
    st.bar_chart(monthly_score)

else:
    st.info("⚠️ Nessun file JSON trovato nella cartella `data/`. Carica dei file per iniziare.")


