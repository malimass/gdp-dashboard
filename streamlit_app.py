import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import json
from datetime import datetime

st.title("Analisi Allenamenti per Preparatore Atletico")

uploaded_files = st.sidebar.file_uploader(
    "Carica uno o più file JSON degli allenamenti:",
    type="json",
    accept_multiple_files=True
)

def extract_data_from_json(file):
    try:
        data = json.load(file)
        start_time = pd.to_datetime(data.get('start_time', data.get('start_time_local', '')))
        distance_km = float(data.get('distance', 0)) / 1000
        duration_sec = float(data.get('elapsed_time', 0))
        duration_hr = round(duration_sec / 3600, 2)
        heart_rate = data.get('average_heartrate', None)
        calories = data.get('calories', None)

        return {
            'Data': start_time,
            'Distanza (km)': round(distance_km, 2),
            'Durata (h)': duration_hr,
            'FC media': heart_rate,
            'Calorie': calories
        }
    except Exception as e:
        st.warning(f"Errore nel file {file.name}: {e}")
        return None

if uploaded_files:
    allenamenti = []
    for file in uploaded_files:
        dati = extract_data_from_json(file)
        if dati:
            allenamenti.append(dati)

    df = pd.DataFrame(allenamenti)
    df = df.dropna(subset=['Data'])
    df = df.sort_values("Data")

    # Selezione intervallo date
    st.sidebar.header("Filtra per data")
    min_date = df["Data"].min().date()
    max_date = df["Data"].max().date()
    date_range = st.sidebar.date_input("Intervallo date", [min_date, max_date], min_value=min_date, max_value=max_date)

    if len(date_range) == 2:
        df = df[(df["Data"] >= pd.to_datetime(date_range[0])) & (df["Data"] <= pd.to_datetime(date_range[1]))]

    # Grafici
    st.subheader("Andamento della Distanza")
    fig1, ax1 = plt.subplots()
    ax1.plot(df["Data"], df["Distanza (km)"], marker='o')
    ax1.set_ylabel("Distanza (km)")
    ax1.tick_params(axis='x', rotation=45)
    ax1.grid(True)
    st.pyplot(fig1)

    st.subheader("Frequenza Cardiaca Media")
    fig2, ax2 = plt.subplots()
    ax2.plot(df["Data"], df["FC media"], marker='x', color='orange')
    ax2.set_ylabel("FC media (bpm)")
    ax2.tick_params(axis='x', rotation=45)
    ax2.grid(True)
    st.pyplot(fig2)

    st.subheader("Calorie Bruciate")
    fig3, ax3 = plt.subplots()
    ax3.bar(df["Data"], df["Calorie"], color='green')
    ax3.set_ylabel("Calorie")
    ax3.tick_params(axis='x', rotation=45)
    st.pyplot(fig3)

else:
    st.info("Carica i file JSON per vedere l'analisi.")




