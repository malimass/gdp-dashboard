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

# Visualizzazione dei dati elaborati
if not df.empty:
    st.subheader("📈 Riepilogo Allenamenti")
    st.dataframe(df)

    df.set_index("date", inplace=True)
    weekly = df.resample("W").sum(numeric_only=True)
    monthly = df.resample("M").sum(numeric_only=True)

    st.subheader("📆 Analisi Settimanale e Mensile")
    st.bar_chart(weekly["Distanza (km)"])
    st.bar_chart(monthly["Distanza (km)"])

    pred_sett = weekly["Distanza (km)"].rolling(window=3).mean().iloc[-1]
    pred_mese = monthly["Distanza (km)"].rolling(window=2).mean().iloc[-1]
    st.subheader("🔮 Previsione Kilometri Futura")
    st.success(f"📅 Previsto per la prossima settimana: {pred_sett:.1f} km")
    st.success(f"🗓️ Previsto per il prossimo mese: {pred_mese:.1f} km")

    st.subheader("📊 Analisi Prestazioni e Zone")
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Velocità Media e Tempo in Zona 2**")
        plt.figure(figsize=(10,4))
        plt.scatter(df["Velocità Media (km/h)"], df["Tempo in Zona 2 (min)"], alpha=0.7, c=df["Frequenza Cardiaca Media"], cmap="coolwarm")
        plt.xlabel("Velocità Media (km/h)")
        plt.ylabel("Tempo in Zona 2 (min)")
        plt.colorbar(label="Frequenza Cardiaca Media")
        st.pyplot(plt)

    with col2:
        st.write("**Frequenza Cardiaca Max e Calorie**")
        plt.figure(figsize=(10,4))
        plt.scatter(df["Frequenza Cardiaca Massima"], df["Calorie"], alpha=0.7)
        plt.xlabel("FC Max")
        plt.ylabel("Calorie")
        st.pyplot(plt)

    st.subheader("⚠️ Rischio Infortuni e Suggerimenti")
    eta = st.sidebar.slider("Inserisci la tua età", 18, 80, 47)
    fc_max_teorica = 220 - eta
    soglia_critica = 0.9 * fc_max_teorica
    rischiosi = df[df["Frequenza Cardiaca Massima"] > soglia_critica]
    if not rischiosi.empty:
        st.warning(f"🚨 {len(rischiosi)} allenamenti hanno superato il 90% della FC Max teorica ({soglia_critica:.0f} bpm)")
        st.dataframe(rischiosi[["Durata (min)", "Frequenza Cardiaca Massima", "Distanza (km)", "Calorie"]])
    else:
        st.success("✅ Nessun allenamento ha superato soglia critica di FC Max.")

    st.subheader("📋 Suggerimenti del Coach Virtuale")
    suggerimenti = []
    if df["Tempo in Zona 3 (min)"].mean() > 10:
        suggerimenti.append("🔄 Riduci il tempo in Zona 3 per evitare affaticamento eccessivo.")
    if df["Frequenza Cardiaca Media"].mean() > 130:
        suggerimenti.append("🧘 Prova ad alternare allenamenti leggeri per migliorare il recupero.")
    if df["Velocità Media (km/h)"].mean() < 5:
        suggerimenti.append("🏃 Lavora sulla cadenza per aumentare la velocità media gradualmente.")
    if suggerimenti:
        for s in suggerimenti:
            st.info(s)
    else:
        st.success("💪 Ottimo andamento! Continua così!")

    # 🔁 Evoluzione del rischio infortuni nel tempo
    st.subheader("📉 Evoluzione del Rischio Infortuni")
    df["Supera FC Max"] = df["Frequenza Cardiaca Massima"] > soglia_critica
    rischio_settimanale = df.resample("W")["Supera FC Max"].sum()
    fig_rischio, ax_rischio = plt.subplots()
    rischio_settimanale.plot(kind="bar", ax=ax_rischio, color="crimson")
    ax_rischio.set_ylabel("Allenamenti a rischio")
    ax_rischio.set_title("N° allenamenti sopra soglia FC Max per settimana")
    st.pyplot(fig_rischio)

    # 📥 Esportazione riepilogo settimanale
    st.subheader("🧾 Esporta riepilogo settimanale")
    export_sett = weekly[["Distanza (km)", "Durata (min)", "Calorie"]].copy()
    export_sett["Rischi FC"] = df.resample("W")["Supera FC Max"].sum()
    csv_export = export_sett.to_csv().encode("utf-8")
    st.download_button("📤 Scarica riepilogo settimanale (CSV)", data=csv_export, file_name="riepilogo_settimanale.csv", mime="text/csv")

    # 📈 Nuovo grafico: Calorie vs Tempo in Zona 2
    st.subheader("🔥 Calorie vs Tempo in Zona 2")
    fig_z2, ax_z2 = plt.subplots()
    ax_z2.scatter(df["Tempo in Zona 2 (min)"], df["Calorie"], color="darkorange", alpha=0.7)
    ax_z2.set_xlabel("Tempo in Zona 2 (min)")
    ax_z2.set_ylabel("Calorie")
    ax_z2.set_title("Relazione tra Tempo in Zona 2 e Calorie bruciate")
    st.pyplot(fig_z2)

    # 🧠 Intelligenza suggerimenti evoluti
    st.subheader("📋 Diagnosi automatica dell'allenamento")
    diagnosi = []
    if weekly["Distanza (km)"].mean() > 80:
        diagnosi.append("📈 Il volume settimanale è elevato: attenzione al recupero.")
    if (df["Tempo in Zona 3 (min)"].mean() > 15) and (df["Frequenza Cardiaca Massima"].mean() > soglia_critica):
        diagnosi.append("🚨 Segni di sovraccarico. Considera una settimana di scarico.")
    if pred_sett < weekly["Distanza (km)"].iloc[-1]:
        diagnosi.append("📉 Il trend settimanale è in calo. Valuta intensità e motivazione.")
    for d in diagnosi:
        st.warning(d)
    if not diagnosi:
        st.success("✅ Nessuna anomalia evidente nei trend recenti.")

else:
    st.info("Nessun dato disponibile. Carica uno o più file JSON validi.")



