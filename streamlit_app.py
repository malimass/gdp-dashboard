import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# Configurazione pagina
st.set_page_config(
    page_title="Analizzatore Dati JSON",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Analizzatore Dati JSON")
st.markdown("Carica i tuoi file JSON e visualizza i dati attraverso grafici interattivi")

# Sidebar per il caricamento file
with st.sidebar:
    st.header("🔧 Configurazione")
    
    # Caricamento file
    uploaded_files = st.file_uploader(
        "Carica file JSON",
        type=['json'],
        accept_multiple_files=True,
        help="Seleziona uno o più file JSON da analizzare"
    )
    
    if uploaded_files:
        st.success(f"Caricati {len(uploaded_files)} file")

# Funzione per caricare e processare JSON
@st.cache_data
def load_json_data(uploaded_file):
    try:
        content = uploaded_file.read()
        data = json.loads(content)
        return data, None
    except json.JSONDecodeError as e:
        return None, f"Errore nel parsing JSON: {str(e)}"
    except Exception as e:
        return None, f"Errore generico: {str(e)}"

# Funzione per convertire JSON in DataFrame
def json_to_dataframe(data, filename):
    try:
        if isinstance(data, list):
            # Se è una lista di oggetti
            if all(isinstance(item, dict) for item in data):
                df = pd.json_normalize(data)
            else:
                # Lista di valori semplici
                df = pd.DataFrame(data, columns=[f'value_{filename}'])
        elif isinstance(data, dict):
            # Se è un dizionario, prova a normalizzarlo
            df = pd.json_normalize(data)
            if df.shape[1] == 0:
                # Se la normalizzazione non ha funzionato, crea un DataFrame dalle chiavi-valori
                df = pd.DataFrame(list(data.items()), columns=['chiave', 'valore'])
        else:
            # Valore singolo
            df = pd.DataFrame([data], columns=[f'value_{filename}'])
        
        # Aggiungi colonna con il nome del file
        df['source_file'] = filename
        return df
    except Exception as e:
        st.error(f"Errore nella conversione del file {filename}: {str(e)}")
        return pd.DataFrame()

# Funzione per creare grafici automatici
def create_automatic_charts(df, filename):
    charts = []
    
    # Escludi la colonna source_file dall'analisi
    data_cols = [col for col in df.columns if col != 'source_file']
    
    if len(data_cols) == 0:
        return charts
    
    # Identifica colonne numeriche e categoriche
    numeric_cols = df[data_cols].select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df[data_cols].select_dtypes(include=['object', 'category']).columns.tolist()
    
    # Grafico a barre per colonne categoriche con conteggi
    for col in categorical_cols:
        if df[col].nunique() <= 20:  # Solo se ci sono meno di 20 valori unici
            value_counts = df[col].value_counts()
            fig = px.bar(
                x=value_counts.index,
                y=value_counts.values,
                title=f'Distribuzione di {col}',
                labels={'x': col, 'y': 'Frequenza'}
            )
            fig.update_layout(xaxis_tickangle=-45)
            charts.append(('bar', fig))
    
    # Istogrammi per colonne numeriche
    for col in numeric_cols:
        fig = px.histogram(
            df, 
            x=col, 
            title=f'Distribuzione di {col}',
            nbins=30
        )
        charts.append(('histogram', fig))
    
    # Scatter plot se ci sono almeno 2 colonne numeriche
    if len(numeric_cols) >= 2:
        fig = px.scatter(
            df,
            x=numeric_cols[0],
            y=numeric_cols[1],
            title=f'Relazione tra {numeric_cols[0]} e {numeric_cols[1]}',
            color=categorical_cols[0] if categorical_cols else None
        )
        charts.append(('scatter', fig))
    
    # Line chart per dati temporali o sequenziali
    if len(numeric_cols) >= 1:
        # Crea un indice sequenziale
        df_indexed = df.copy()
        df_indexed['index'] = range(len(df_indexed))
        
        fig = px.line(
            df_indexed,
            x='index',
            y=numeric_cols[0],
            title=f'Andamento di {numeric_cols[0]}'
        )
        charts.append(('line', fig))
    
    return charts

# Main interface
if uploaded_files:
    # Tabs per ogni file
    tabs = st.tabs([f"📄 {file.name}" for file in uploaded_files])
    
    for tab, uploaded_file in zip(tabs, uploaded_files):
        with tab:
            # Carica i dati
            data, error = load_json_data(uploaded_file)
            
            if error:
                st.error(error)
                continue
            
            # Mostra struttura JSON
            with st.expander("🔍 Visualizza JSON grezzo"):
                st.json(data)
            
            # Converti in DataFrame
            df = json_to_dataframe(data, uploaded_file.name)
            
            if df.empty:
                st.warning("Impossibile convertire i dati in un formato tabulare")
                continue
            
            # Mostra informazioni sul dataset
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Righe", len(df))
            with col2:
                st.metric("Colonne", len(df.columns) - 1)  # -1 per escludere source_file
            with col3:
                st.metric("Memoria", f"{df.memory_usage().sum() / 1024:.1f} KB")
            
            # Mostra anteprima dei dati
            st.subheader("📋 Anteprima Dati")
            st.dataframe(df.drop(columns=['source_file']), use_container_width=True)
            
            # Statistiche descrittive
            numeric_data = df.select_dtypes(include=[np.number])
            if not numeric_data.empty:
                st.subheader("📈 Statistiche Descrittive")
                st.dataframe(numeric_data.describe(), use_container_width=True)
            
            # Grafici automatici
            st.subheader("📊 Visualizzazioni")
            charts = create_automatic_charts(df, uploaded_file.name)
            
            if charts:
                chart_cols = st.columns(2)
                for i, (chart_type, fig) in enumerate(charts):
                    with chart_cols[i % 2]:
                        st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Nessun grafico automatico disponibile per questo dataset")
            
            # Sezione per grafici personalizzati
            st.subheader("🎨 Grafici Personalizzati")
            
            # Selezione colonne per grafici personalizzati
            available_cols = [col for col in df.columns if col != 'source_file']
            
            if len(available_cols) > 0:
                custom_chart_type = st.selectbox(
                    "Tipo di grafico",
                    ["Scatter Plot", "Line Chart", "Bar Chart", "Box Plot", "Heatmap"],
                    key=f"chart_type_{uploaded_file.name}"
                )
                
                if custom_chart_type == "Scatter Plot" and len(available_cols) >= 2:
                    col1, col2 = st.columns(2)
                    with col1:
                        x_col = st.selectbox("Asse X", available_cols, key=f"x_{uploaded_file.name}")
                    with col2:
                        y_col = st.selectbox("Asse Y", available_cols, key=f"y_{uploaded_file.name}")
                    
                    if st.button(f"Crea Scatter Plot", key=f"scatter_{uploaded_file.name}"):
                        fig = px.scatter(df, x=x_col, y=y_col, title=f"{x_col} vs {y_col}")
                        st.plotly_chart(fig, use_container_width=True)
                
                elif custom_chart_type == "Line Chart":
                    col_to_plot = st.selectbox("Colonna da visualizzare", available_cols, key=f"line_{uploaded_file.name}")
                    if st.button(f"Crea Line Chart", key=f"line_btn_{uploaded_file.name}"):
                        df_plot = df.copy()
                        df_plot['index'] = range(len(df_plot))
                        fig = px.line(df_plot, x='index', y=col_to_plot, title=f"Andamento di {col_to_plot}")
                        st.plotly_chart(fig, use_container_width=True)
                
                elif custom_chart_type == "Bar Chart":
                    col_to_plot = st.selectbox("Colonna da visualizzare", available_cols, key=f"bar_{uploaded_file.name}")
                    if st.button(f"Crea Bar Chart", key=f"bar_btn_{uploaded_file.name}"):
                        if df[col_to_plot].dtype in ['object', 'category']:
                            value_counts = df[col_to_plot].value_counts()
                            fig = px.bar(x=value_counts.index, y=value_counts.values, 
                                       title=f"Distribuzione di {col_to_plot}")
                        else:
                            fig = px.bar(df, y=col_to_plot, title=f"Valori di {col_to_plot}")
                        st.plotly_chart(fig, use_container_width=True)

else:
    # Pagina di benvenuto
    st.info("👆 Carica uno o più file JSON dalla sidebar per iniziare l'analisi")
    
    # Mostra esempi di utilizzo
    st.subheader("💡 Esempi di Utilizzo")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Formato Array di Oggetti:**
        ```json
        [
            {"nome": "Mario", "età": 30, "città": "Roma"},
            {"nome": "Lucia", "età": 25, "città": "Milano"}
        ]
        ```
        """)
    
    with col2:
        st.markdown("""
        **Formato Oggetto Semplice:**
        ```json
        {
            "vendite": [100, 150, 200, 175],
            "mesi": ["Gen", "Feb", "Mar", "Apr"]
        }
        ```
        """)
    
    st.subheader("🚀 Funzionalità")
    st.markdown("""
    - **Caricamento multiplo**: Carica più file JSON contemporaneamente
    - **Visualizzazione automatica**: Grafici generati automaticamente basati sui tipi di dati
    - **Analisi esplorativa**: Statistiche descrittive e anteprima dati
    - **Grafici personalizzati**: Crea visualizzazioni specifiche per le tue esigenze
    - **Supporto formati**: Array di oggetti, oggetti singoli, array di valori
    """)
