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



# Interfaccia Streamlit
st.set_page_config(page_title="Polar Training Dashboard", layout="wide")
st.title("📊 Polar Training Analyzer")

# Caricamento file JSON
uploaded_files = st.file_uploader("📁 Carica uno o più file JSON esportati da Polar Flow", type="json", accept_multiple_files=True)

# Salvataggio e caricamento dati
if uploaded_files:
    save_uploaded_files(uploaded_files)
    df = load_multiple_json_training_data(uploaded_files)

    if not df.empty:
        st.subheader("📅 Allenamenti Caricati")
        styled_df = df.style.applymap(lambda v: 'background-color: #ffcccc' if isinstance(v, (int, float)) and v > 160, subset=["Frequenza Cardiaca Massima"])
        styled_df = styled_df.applymap(lambda v: 'background-color: #fff3cd' if isinstance(v, (int, float)) and v < 10, subset=["Tempo in Zona 2"])
        st.dataframe(styled_df, use_container_width=True)

        # Analisi Zone Cardiache
        st.subheader("🫀 Distribuzione Zone Cardiache (Z1–Z3)")
        zona1 = df["Tempo in Zona 1"].sum()
        zona2 = df["Tempo in Zona 2"].sum()
        zona3 = df["Tempo in Zona 3"].sum()
        zone_labels = ["Zona 1 (bassa intensità)", "Zona 2 (aerobica)", "Zona 3 (soglia)"]
        zone_values = [zona1, zona2, zona3]
        fig, ax = plt.subplots()
        ax.pie(zone_values, labels=zone_labels, autopct="%1.1f%%", startangle=90)
        ax.axis("equal")
        st.pyplot(fig)

        total_zone_time = sum(zone_values)
        if zona2 / total_zone_time < 0.4:
            st.warning("⚠️ Trascorri poco tempo in Zona 2: potresti non allenare abbastanza la resistenza aerobica.")
        elif zona2 / total_zone_time > 0.6:
            st.success("✅ Ottimo: buona quota di lavoro in zona aerobica.")
        else:
            st.info("ℹ️ Zona 2 nel range medio. Potresti alternare con sedute più intense o leggere.")

        # Confronto Velocità Media vs Tempo in Zona 2
        st.subheader("⚖️ Velocità Media vs Tempo in Zona 2")
        fig2, ax2 = plt.subplots()
        ax2.scatter(df["Velocità Media (km/h)"], df["Tempo in Zona 2"], alpha=0.7, color="green")
        ax2.set_xlabel("Velocità Media (km/h)")
        ax2.set_ylabel("Tempo in Zona 2 (min)")
        ax2.set_title("Relazione tra velocità e tempo aerobico")
        st.pyplot(fig2)

        correlation = df[["Velocità Media (km/h)", "Tempo in Zona 2"]].corr().iloc[0, 1]
        if correlation > 0.5:
            st.success(f"✅ Forte correlazione positiva ({correlation:.2f}) tra velocità e tempo in Zona 2")
        elif correlation < -0.5:
            st.warning(f"⚠️ Correlazione negativa ({correlation:.2f}): più vai veloce, meno lavori in zona aerobica")
        else:
            st.info(f"ℹ️ Correlazione debole ({correlation:.2f}) tra velocità e tempo in Zona 2")
else:
    st.info("Carica almeno un file JSON per iniziare l'analisi.")










