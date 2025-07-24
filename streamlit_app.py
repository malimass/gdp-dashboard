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

            distanza = round(exercise.get("distance", 0) / 1000, 2)

            record = {
                "date": pd.to_datetime(exercise.get("startTime")),
                "Durata (min)": round(duration_seconds / 60, 2),
                "Distanza (km)": distanza,
                "Calorie": exercise.get("kiloCalories", 0),
                "Frequenza Cardiaca Media": exercise.get("heartRate", {}).get("avg", 0),
                "Frequenza Cardiaca Massima": exercise.get("heartRate", {}).get("max", 0),
                "Velocità Media (km/h)": round(exercise.get("speed", {}).get("avg", 0), 2),
                "Velocità Massima (km/h)": round(exercise.get("speed", {}).get("max", 0), 2),
                "Tempo in Zona 1 (min)": isodate.parse_duration(next((z.get("inZone", "PT0S") for z in exercise.get("zones", {}).get("heart_rate", []) if z.get("zoneIndex") == 1), "PT0S")).total_seconds() / 60,
                "Tempo in Zona 2 (min)": isodate.parse_duration(next((z.get("inZone", "PT0S") for z in exercise.get("zones", {}).get("heart_rate", []) if z.get("zoneIndex") == 2), "PT0S")).total_seconds() / 60,
                "Tempo in Zona 3 (min)": isodate.parse_duration(next((z.get("inZone", "PT0S") for z in exercise.get("zones", {}).get("heart_rate", []) if z.get("zoneIndex") == 3), "PT0S")).total_seconds() / 60,
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
    file_to_delete = st.selectbox("Seleziona file da eliminare", options=["" ] + existing_files)
    if file_to_delete and st.button("Elimina File"):
        delete_file(file_to_delete)
        st.success(f"File '{file_to_delete}' eliminato. Ricaricare la pagina per aggiornare i dati.")

# Caricamento automatico dei file dalla cartella 'data'
file_names = [f for f in os.listdir("data") if f.endswith(".json")]
data_files = [open(os.path.join("data", f), "rb") for f in file_names]
df = load_multiple_json_training_data(data_files) if data_files else pd.DataFrame()

# Se ci sono dati, calcola soglia FC max e crea grafici
if not df.empty:
    eta = st.sidebar.slider("Inserisci la tua età", 18, 80, 47)
    fc_max_teorica = 220 - eta
    soglia_critica = 0.9 * fc_max_teorica

    st.subheader("📉 Evoluzione del Rischio Infortuni")
    df["Supera FC Max"] = df["Frequenza Cardiaca Massima"] > soglia_critica
    df["date"] = pd.to_datetime(df.index)
    df.set_index("date", inplace=True)

    if pd.api.types.is_datetime64_any_dtype(df.index):
        rischio_settimanale = df["Supera FC Max"].resample("W").sum()
        fig_rischio, ax_rischio = plt.subplots(figsize=(10, 4))
        bars = ax_rischio.bar(rischio_settimanale.index.strftime('%d %b'), rischio_settimanale, color="crimson")
        ax_rischio.set_ylabel("Allenamenti a rischio")
        ax_rischio.set_xlabel("Settimane")
        ax_rischio.set_title("🧠 Allenamenti sopra soglia FC Max per settimana")
        ax_rischio.set_ylim(0, max(rischio_settimanale.max() + 1, 1))
        ax_rischio.grid(True, linestyle='--', alpha=0.5)
        for bar in bars:
            yval = bar.get_height()
            ax_rischio.text(bar.get_x() + bar.get_width()/2, yval + 0.1, int(yval), ha='center', va='bottom', fontsize=8)
        st.pyplot(fig_rischio)

    st.subheader("📈 Andamento della Frequenza Cardiaca Massima nel tempo")
    fig_fc, ax_fc = plt.subplots(figsize=(10, 4))
    df["Frequenza Cardiaca Massima"].plot(ax=ax_fc, color="darkblue", marker="o", linestyle="-")
    ax_fc.set_ylabel("FC Massima (bpm)")
    ax_fc.set_xlabel("Data")
    ax_fc.set_title("📊 Frequenza Cardiaca Massima nel tempo")
    ax_fc.grid(True, linestyle='--', alpha=0.5)
    st.pyplot(fig_fc)

else:
    st.info("Nessun dato disponibile. Carica uno o più file JSON validi.")





