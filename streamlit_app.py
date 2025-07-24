# app_streamlit_polar.py

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime
import json
import isodate
import os
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report

MODEL_PATH = "model/rf_model.pkl"
SCALER_PATH = "model/scaler.pkl"

os.makedirs("model", exist_ok=True)

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
st.set_page_config(page_title="Coach Virtuale con ML", layout="wide")
st.title("🤖 Coach Virtuale – Consigli Predittivi Personalizzati")

# File manager
st.sidebar.header("📂 Carica i tuoi allenamenti")
uploaded_files = st.sidebar.file_uploader("File JSON da Polar Flow", type="json", accept_multiple_files=True)
if uploaded_files:
    save_uploaded_files(uploaded_files)
    st.sidebar.success("File salvati correttamente. Ricarica la pagina per aggiornare.")

# Caricamento automatico
file_names = [f for f in os.listdir("data") if f.endswith(".json")]
data_files = [open(os.path.join("data", f), "rb") for f in file_names]
df = load_multiple_json_training_data(data_files) if data_files else pd.DataFrame()

if not df.empty:
    eta = st.sidebar.slider("Età atleta", 18, 80, 47)
    fc_max_teorica = 220 - eta
    soglia_fc = 0.9 * fc_max_teorica

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔍 Analisi personalizzata")
    giorno_scelto = st.sidebar.date_input("Seleziona una data", df.index[-1].date())

    df["Supera FC Max"] = df["Frequenza Cardiaca Massima"] > soglia_fc
    df["Efficienza"] = df["Velocità Media (km/h)"] / df["Frequenza Cardiaca Media"]
    df["Load"] = df["Durata (min)"] * df["Frequenza Cardiaca Media"]
    df.set_index("date", inplace=True)
    df["Load_7d"] = df["Load"].rolling("7D").mean()
    df["Load_28d"] = df["Load"].rolling("28D").mean()
    df["ACWR"] = df["Load_7d"] / df["Load_28d"]
    df = df.dropna()

    st.subheader("📊 Analisi Allenamenti e Rischio Predittivo")
    features = df[["Durata (min)", "Distanza (km)", "Frequenza Cardiaca Media", "Efficienza", "ACWR"]]
    labels = df["Supera FC Max"].astype(int)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(features)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_scaled, labels)

    df["Probabilità Infortunio"] = model.predict_proba(X_scaled)[:,1]
    st.line_chart(df["Probabilità Infortunio"], use_container_width=True)

    # Interazione utente: feedback per giorno selezionato
    if pd.to_datetime(giorno_scelto) in df.index:
        st.subheader(f"🧠 Consigli per il {giorno_scelto}")
        dati = df.loc[pd.to_datetime(giorno_scelto)]
        consigli = []
        if dati["Probabilità Infortunio"] > 0.7:
            consigli.append("⚠️ Alto rischio infortunio – considera un giorno di recupero o scarico.")
        elif dati["Probabilità Infortunio"] > 0.4:
            consigli.append("🔁 Attenzione: carico borderline. Idratazione, stretching e sonno adeguato consigliati.")
        else:
            consigli.append("✅ Ottimo stato di forma. Puoi pianificare un carico medio/alto.")

        if dati["ACWR"] > 1.5:
            consigli.append("📈 ACWR elevato – riduci intensità nei prossimi 2 giorni.")
        elif dati["ACWR"] < 0.8:
            consigli.append("📉 Carico insufficiente – potresti inserire una sessione più lunga o intensa.")

        for c in consigli:
            st.info(c)
    else:
        st.warning("Nessun dato disponibile per la data selezionata.")

    # Interazione aggiuntiva – Simulazione allenamento manuale
    st.markdown("---")
    st.subheader("📌 Simula un nuovo allenamento")
    with st.form("simulatore"):
        durata_sim = st.number_input("Durata (minuti)", min_value=10, max_value=300, value=60)
        distanza_sim = st.number_input("Distanza (km)", min_value=1.0, max_value=100.0, value=10.0)
        fc_avg_sim = st.number_input("Frequenza Cardiaca Media", min_value=60, max_value=220, value=130)
        eff_sim = st.number_input("Efficienza (velocità / FC)", min_value=0.01, max_value=1.0, value=0.05)
        acwr_sim = st.number_input("ACWR stimato", min_value=0.1, max_value=3.0, value=1.0)
        submitted = st.form_submit_button("Valuta Rischio")

    if submitted:
        input_data = pd.DataFrame([[durata_sim, distanza_sim, fc_avg_sim, eff_sim, acwr_sim]],
                                   columns=["Durata (min)", "Distanza (km)", "Frequenza Cardiaca Media", "Efficienza", "ACWR"])
        input_scaled = scaler.transform(input_data)
        prob = model.predict_proba(input_scaled)[0,1]

        st.metric(label="Probabilità di Infortunio Stimata", value=f"{prob*100:.1f}%")
        if prob > 0.7:
            st.error("⚠️ Alto rischio – ridurre l'intensità o pianificare recupero.")
        elif prob > 0.4:
            st.warning("⚠️ Moderato rischio – valuta stretching, riposo, sonno.")
        else:
            st.success("✅ Rischio basso – allenamento sostenibile.")
else:
    st.info("📥 Carica almeno un file JSON di allenamento per iniziare.")
