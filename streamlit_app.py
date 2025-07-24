import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Titolo app
st.title("Monitoraggio Allenamenti Massimo Malivindi")

# Dati inseriti manualmente in un DataFrame (puoi sostituirli con caricamento CSV)
dati = [
    ["28-05-2025", 0.0, 106, 976],
    ["30-05-2025", 0.0, 110, 364],
    ["01-06-2025", 0.0, 113, 383],
    ["04-06-2025", 0.0, 112, 368],
    ["20-06-2025", 9.14, 124, 1479],
    ["22-06-2025", 9.14, 137, 1130],
    ["23-06-2025", 18.08, 115, 2010],
    ["25-06-2025", 7.76, 125, 827],
    ["27-06-2025", 10.31, 115, 940],
    ["02-07-2025", 19.02, 122, 1291],
    ["04-07-2025", 7.16, 118, 658],
    ["06-07-2025", 11.88, 114, 1509],
    ["08-07-2025", 18.79, 112, 1686],
    ["10-07-2025", 7.18, 112, 750],
    ["11-07-2025", 8.41, 118, 814],
    ["13-07-2025", 20.04, 112, 2320],
    ["15-07-2025", 18.39, 90, 1552],
    ["17-07-2025", 12.34, 103, 1016],
    ["20-07-2025", 22.69, 122, 2668],
    ["21-07-2025", 7.54, 110, 722]
]

# Creazione del DataFrame
df = pd.DataFrame(dati, columns=["Data", "Distanza (km)", "FC media", "Calorie"])
df["Data"] = pd.to_datetime(df["Data"], format="%d-%m-%Y")
df = df.sort_values("Data")

# Visualizzazione tabella dati
st.subheader("Tabella riepilogativa")
st.dataframe(df)

# Grafico distanza
st.subheader("Andamento della Distanza Percorsa")
fig1, ax1 = plt.subplots()
ax1.plot(df["Data"], df["Distanza (km)"], marker='o')
ax1.set_ylabel("Distanza (km)")
ax1.set_xlabel("Data")
ax1.grid(True)
st.pyplot(fig1)

# Grafico frequenza cardiaca
st.subheader("Andamento della Frequenza Cardiaca Media")
fig2, ax2 = plt.subplots()
ax2.plot(df["Data"], df["FC media"], color='orange', marker='x')
ax2.set_ylabel("Frequenza Cardiaca Media (bpm)")
ax2.set_xlabel("Data")
ax2.grid(True)
st.pyplot(fig2)

# Grafico calorie
st.subheader("Andamento Calorie Bruciate")
fig3, ax3 = plt.subplots()
ax3.bar(df["Data"], df["Calorie"], color='green')
ax3.set_ylabel("Calorie")
ax3.set_xlabel("Data")
ax3.tick_params(axis='x', rotation=45)
st.pyplot(fig3)

