# app_streamlit_polar.py

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime
from io import BytesIO
from urllib.parse import urlparse

# Simulazione funzione di estrazione da Polar Flow (da implementare con scraping o API privato se disponibile)
def extract_data_from_polar_link(link):
    # ATTENZIONE: Polar non fornisce API pubbliche per link condivisi.
    # Qui si simula l'importazione di dati esportati (es. CSV/TCX scaricato dall'utente)
    # Per l'esempio, carichiamo un file CSV fittizio
    df = pd.read_csv("sample_polar_data.csv", parse_dates=["datetime"])
    df["date"] = df["datetime"].dt.date
    return df

# Calcolo indice personalizzato di carico (es. TRIMP semplificato)
def compute_training_load(row):
    return row["duration_min"] * row["intensity"]  # esempio: durata * intensità relativa

# Analisi predittiva semplificata (placeholder)
def performance_analysis(df):
    # esempio: calo prestazioni, FC a riposo, rapporto carico cronico/acuto
    daily_loads = df.groupby("date")["training_load"].sum()
    short_term = daily_loads.rolling(window=3).mean()
    long_term = daily_loads.rolling(window=7).mean()
    acwr = short_term / long_term
    return daily_loads, acwr

# Sidebar - Caricamento Link
st.sidebar.title("Carica il link Polar Flow")
link_input = st.sidebar.text_input("Incolla qui il link condiviso", "https://flow.polar.com/shared2/7e97c154516c580b2a4278763df0b9f0")

if link_input:
    st.title("Polar Flow Analyzer – Preparatore Virtuale")

    # Estrarre i dati (in realtà dovresti caricare da file esportato)
    st.info("⚠️ I link Polar condivisi non permettono accesso diretto ai dati. Caricamento simulato da file CSV.")
    df = extract_data_from_polar_link(link_input)

    # Calcola metriche
    df["duration_min"] = df["duration_sec"] / 60
    df["training_load"] = df.apply(compute_training_load, axis=1)

    # Sezione calendario
    st.subheader("Calendario Allenamenti")
    dates = df["date"].unique()
    selected_date = st.selectbox("Seleziona una data", sorted(dates, reverse=True))

    daily_data = df[df["date"] == selected_date]
    st.write(f"## Dettagli allenamento del {selected_date}")
    st.dataframe(daily_data)

    # Grafici del giorno selezionato
    fig, ax = plt.subplots()
    ax.plot(daily_data["datetime"], daily_data["heart_rate"], label="Frequenza Cardiaca")
    ax.set_ylabel("bpm")
    ax.set_xlabel("Tempo")
    st.pyplot(fig)

    # Sezione Analisi Predittiva (tipo "coach virtuale")
    st.subheader("Analisi Predittiva: Coach Virtuale")
    load_series, acwr_series = performance_analysis(df)

    st.line_chart(load_series.rename("Training Load Giornaliero"))
    st.line_chart(acwr_series.rename("Rapporto Carico Acuto/Cronico (ACWR)"))

    st.markdown("""
    ### Feedback Coach:
    - Se ACWR > 1.5: Rischio infortunio alto – considera recupero.
    - Se ACWR < 0.8: Carico insufficiente – attenzione a sotto-allenamento.
    - Trend decrescente del passo medio? ⚠️ Possibile accumulo di fatica.
    """)

else:
    st.title("Benvenuto nella tua App di Analisi Allenamenti Polar")
    st.markdown("Carica un link condiviso da Polar Flow per analizzare i tuoi dati di allenamento.")
    st.markdown("Per funzionare completamente, assicurati di avere un file CSV esportato da Polar Flow.")
