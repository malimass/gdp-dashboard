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

    # Calcolo punteggio
    def calculate_score(row):
        score = 0
        if row["Frequenza Cardiaca Media"] >= 100: score += 1
        if row["Durata"] >= 60: score += 1
        if row["Tempo in Zona 2"] >= 20: score += 1
        if row["Velocità Media (km/h)"] >= 5.5: score += 1
        return score

    df["Punteggio"] = df.apply(calculate_score, axis=1)

    # Classifica Top 5 Allenamenti
    st.subheader("🥇 Top 5 Allenamenti per Punteggio")
    top5 = df.sort_values("Punteggio", ascending=False).head(5)[["Durata", "Frequenza Cardiaca Media", "Tempo in Zona 2", "Velocità Media (km/h)", "Punteggio"]]
    st.dataframe(top5.style.format({"Durata": "{:.1f}", "Frequenza Cardiaca Media": "{:.0f}", "Tempo in Zona 2": "{:.1f}", "Velocità Media (km/h)": "{:.2f}", "Punteggio": "{:.0f}"}))
    st.subheader("📅 Sessioni di Allenamento")
    st.dataframe(df)

    st.subheader("📈 Grafico: FC Media e Durata")
    fig, ax = plt.subplots()
    ax.plot(df.index, df["Frequenza Cardiaca Media"], label='FC Media (bpm)', color='crimson', marker='o')
    ax.set_ylabel("FC Media (bpm)", color='crimson')
    ax.set_xlabel("Data")
    ax2 = ax.twinx()
    ax2.plot(df.index, df["Durata"], label='Durata (min)', color='blue', marker='x')
    ax2.set_ylabel("Durata (min)", color='blue')
    fig.autofmt_xdate()
    ax.set_title("Frequenza Cardiaca Media e Durata Allenamento")
    ax.legend(loc='upper left')
    ax2.legend(loc='upper right')
    st.pyplot(fig)

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

    st.subheader("📊 Andamento ACWR Settimanale")
    fig1, ax1 = plt.subplots()
    ax1.plot(acwr.index, acwr, marker='o', color='orange', label='ACWR Settimanale')
    ax1.axhline(1.5, color='red', linestyle='--', linewidth=1, label='Soglia Alto Rischio')
    ax1.axhline(0.8, color='blue', linestyle='--', linewidth=1, label='Soglia Basso Carico')
    ax1.set_ylabel("ACWR")
    ax1.set_xlabel("Settimana")
    ax1.set_title("Andamento ACWR Settimanale")
    ax1.legend()
    ax1.grid(True)
    st.pyplot(fig1)

    st.subheader("📆 Andamento ACWR Mensile")
    fig2, ax2 = plt.subplots()
    ax2.plot(acwr_monthly.index, acwr_monthly, marker='o', color='green', label='ACWR Mensile')
    ax2.axhline(1.5, color='red', linestyle='--', linewidth=1, label='Soglia Alto Rischio')
    ax2.axhline(0.8, color='blue', linestyle='--', linewidth=1, label='Soglia Basso Carico')
    ax2.set_ylabel("ACWR")
    ax2.set_xlabel("Mese")
    ax2.set_title("Andamento ACWR Mensile")
    ax2.legend()
    ax2.grid(True)
    st.pyplot(fig2)

    latest_acwr = acwr.dropna().iloc[-1] if not acwr.dropna().empty else None
    if latest_acwr:
        if latest_acwr > 1.5:
            st.error(f"🚨 ACWR = {latest_acwr:.2f} → Alto rischio infortunio. Riduci il carico.")
        elif latest_acwr < 0.8:
            st.warning(f"⚠️ ACWR = {latest_acwr:.2f} → Carico troppo basso, potenziale calo di performance.")

    # Analisi zona cardiaca
    st.subheader("🧠 Tempo in Zona Cardiaca (minuti)")
    zona_df = df[["Tempo in Zona 1", "Tempo in Zona 2", "Tempo in Zona 3"]]
    fig, ax = plt.subplots()
    zona_df.plot.area(ax=ax, stacked=True, colormap='Set2')
    ax.set_ylabel("Minuti")
    ax.set_xlabel("Data")
    ax.set_title("Tempo Trascorso nelle Zone Cardiache")
    ax.legend(title="Zona FC")
    ax.grid(True)
    st.pyplot(fig)

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
    fig3, ax3 = plt.subplots()
    ax3.bar(weekly_score.index, weekly_score["Punteggio"], color='skyblue')
    ax3.set_ylabel("Punteggio Medio")
    ax3.set_title("Punteggio Medio Settimanale")
    ax3.grid(True)
    st.pyplot(fig3)

    st.subheader("📆 Media Mensile")
    fig4, ax4 = plt.subplots()
    ax4.bar(monthly_score.index, monthly_score["Punteggio"], color='lightgreen')
    ax4.set_ylabel("Punteggio Medio")
    ax4.set_title("Punteggio Medio Mensile")
    ax4.grid(True)
    st.pyplot(fig4)

    # Osservazioni automatiche del coach
    st.subheader("🗣️ Osservazioni del Coach")
    avg_score = df["Punteggio"].mean()
    total_minutes = df["Durata"].sum()
    zone2_avg = df["Tempo in Zona 2"].mean()
    if avg_score >= 3.5:
        st.success("✅ Ottima costanza! Il carico di allenamento è efficace.")
    elif avg_score >= 2.5:
        st.info("📈 Buon andamento. Puoi spingere un po’ di più nelle prossime settimane.")
    else:
        st.warning("⚠️ Attenzione: il punteggio medio è basso. Valuta maggiore intensità o costanza.")

    if total_minutes < 300:
        st.warning("📉 Il volume totale settimanale è basso. Rischio di regressione della performance.")
    if zone2_avg < 20:
        st.warning("🫀 Poco tempo nella Zona 2. Lavora di più sulla resistenza aerobica.")

else:
    st.info("⚠️ Nessun file JSON trovato nella cartella `data/`. Carica dei file per iniziare.")





