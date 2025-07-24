# app_streamlit_polar.py

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime
from io import BytesIO
import requests
from bs4 import BeautifulSoup

# Funzione per estrarre dati da link condiviso Polar (scraping HTML limitato)
def extract_data_from_polar_link(https://flow.polar.com/shared2/7e97c154516c580b2a4278763df0b9f0):
    resp = requests.get(link)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # Esempio semplice di estrazione: cerchiamo dati nella pagina HTML condivisa
    summary_box = soup.select_one("div.shared-exercise-header")
    metrics = soup.select("div.shared-exercise-basic-data-row")

    try:
        date_text = summary_box.select_one("h2").text.strip()
    except:
        date_text = ""

    data = {"date": date_text}
    for metric in metrics:
        try:
            label = metric.select_one(".label").text.strip()
            value = metric.select_one(".value").text.strip()
            data[label] = value
        except:
            continue

    # Converti a DataFrame
    df = pd.DataFrame([data])
    df["date"] = pd.to_datetime(df["date"], errors='coerce')
    return df

# Calcolo carico (esempio semplificato)
def compute_training_load(row):
    if "Durata" in row and isinstance(row["Durata"], str):
        t = row["Durata"].split(":")
        try:
            duration_min = int(t[0]) * 60 + int(t[1])
        except:
            duration_min = 0
    else:
        duration_min = 0
    return duration_min * 1  # intensità arbitraria

# Analisi predittiva semplificata
def performance_analysis(df):
    df["training_load"] = df.apply(compute_training_load, axis=1)
    df.set_index("date", inplace=True)
    daily_loads = df["training_load"]
    short_term = daily_loads.rolling(window=3).mean()
    long_term = daily_loads.rolling(window=7).mean()
    acwr = short_term / long_term
    return daily_loads, acwr

# UI Streamlit
st.sidebar.title("Carica il link Polar Flow")
link_input = st.sidebar.text_input("Incolla qui il link condiviso", "https://flow.polar.com/shared2/7e97c154516c580b2a4278763df0b9f0")

if link_input:
    st.title("Polar Flow Analyzer – Preparatore Virtuale")
    st.info("I dati vengono estratti automaticamente dalla pagina Polar Flow condivisa")

    df = extract_data_from_polar_link(link_input)
    st.write("## Dati Allenamento Estratti")
    st.dataframe(df)

    # Calcolo training load e analisi
    daily_loads, acwr = performance_analysis(df)

    st.subheader("Analisi Predittiva – Coach Virtuale")
    st.line_chart(daily_loads.rename("Carico Giornaliero"))
    st.line_chart(acwr.rename("ACWR (Carico Acuto / Cronico)"))

    st.markdown("""
    ### Feedback:
    - ACWR > 1.5 = rischio infortunio
    - ACWR < 0.8 = carico troppo basso
    """)
else:
    st.title("Benvenuto nella tua App di Analisi Allenamenti Polar")
    st.markdown("Carica un link condiviso da Polar Flow per analizzare i tuoi dati di allenamento.")
