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

# Funzione per processare dati di esercizi fitness
def process_fitness_data(df):
    """Processa specificamente i dati di esercizi fitness"""
    
    # Converti le date se presenti
    if 'startTime' in df.columns:
        df['startTime'] = pd.to_datetime(df['startTime'])
        df['date'] = df['startTime'].dt.date
        df['hour'] = df['startTime'].dt.hour
        df['day_of_week'] = df['startTime'].dt.day_name()
    
    # Converti la durata da formato PT in minuti
    if 'duration' in df.columns:
        def parse_duration(duration_str):
            try:
                if 'PT' in duration_str and 'S' in duration_str:
                    seconds = float(duration_str.replace('PT', '').replace('S', ''))
                    return seconds / 60  # Converti in minuti
                return None
            except:
                return None
        
        df['duration_minutes'] = df['duration'].apply(parse_duration)
    
    # Calcola velocità media in km/h se non presente
    if 'distance' in df.columns and 'duration_minutes' in df.columns:
        df['speed_kmh'] = (df['distance'] / 1000) / (df['duration_minutes'] / 60)
    
    return df

# Funzione per creare grafici automatici ottimizzati per fitness data
def create_automatic_charts(df, filename):
    charts = []
    
    # Processa i dati fitness
    df = process_fitness_data(df.copy())
    
    # Escludi la colonna source_file dall'analisi
    data_cols = [col for col in df.columns if col != 'source_file']
    
    if len(data_cols) == 0:
        return charts
    
    # Grafici specifici per dati fitness
    
    # 1. Distribuzione sport
    if 'sport' in df.columns:
        value_counts = df['sport'].value_counts()
        fig = px.pie(
            values=value_counts.values,
            names=value_counts.index,
            title='Distribuzione Tipi di Sport'
        )
        charts.append(('pie', fig))
    
    # 2. Andamento nel tempo - Distanza
    if 'startTime' in df.columns and 'distance' in df.columns:
        fig = px.scatter(
            df,
            x='startTime',
            y='distance',
            title='Distanza nel Tempo',
            labels={'distance': 'Distanza (m)', 'startTime': 'Data'},
            color='sport' if 'sport' in df.columns else None
        )
        fig.update_traces(mode='markers+lines')
        charts.append(('timeline', fig))
    
    # 3. Calorie vs Durata
    if 'kiloCalories' in df.columns and 'duration_minutes' in df.columns:
        fig = px.scatter(
            df,
            x='duration_minutes',
            y='kiloCalories',
            title='Calorie vs Durata',
            labels={'duration_minutes': 'Durata (min)', 'kiloCalories': 'Calorie'},
            color='sport' if 'sport' in df.columns else None,
            size='distance' if 'distance' in df.columns else None
        )
        charts.append(('scatter', fig))
    
    # 4. Frequenza cardiaca media
    if 'heartRate.avg' in df.columns:
        fig = px.histogram(
            df,
            x='heartRate.avg',
            title='Distribuzione Frequenza Cardiaca Media',
            labels={'heartRate.avg': 'BPM Medio'},
            nbins=20
        )
        charts.append(('histogram', fig))
    
    # 5. Allenamenti per giorno della settimana
    if 'day_of_week' in df.columns:
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_counts = df['day_of_week'].value_counts()
        day_counts = day_counts.reindex(day_order, fill_value=0)
        
        fig = px.bar(
            x=day_counts.index,
            y=day_counts.values,
            title='Allenamenti per Giorno della Settimana',
            labels={'x': 'Giorno', 'y': 'Numero Allenamenti'}
        )
        charts.append(('bar', fig))
    
    # 6. Velocità media vs Distanza
    if 'speed_kmh' in df.columns and 'distance' in df.columns:
        fig = px.scatter(
            df,
            x='distance',
            y='speed_kmh',
            title='Velocità vs Distanza',
            labels={'distance': 'Distanza (m)', 'speed_kmh': 'Velocità (km/h)'},
            color='sport' if 'sport' in df.columns else None
        )
        charts.append(('scatter', fig))
    
    # 7. Box plot delle altitudini se disponibili
    if 'altitude.min' in df.columns and 'altitude.max' in df.columns and 'altitude.avg' in df.columns:
        altitude_data = []
        for _, row in df.iterrows():
            altitude_data.extend([
                {'type': 'Min', 'altitude': row['altitude.min']},
                {'type': 'Avg', 'altitude': row['altitude.avg']},
                {'type': 'Max', 'altitude': row['altitude.max']}
            ])
        
        altitude_df = pd.DataFrame(altitude_data)
        fig = px.box(
            altitude_df,
            x='type',
            y='altitude',
            title='Distribuzione Altitudine (Min/Avg/Max)',
            labels={'altitude': 'Altitudine (m)', 'type': 'Tipo'}
        )
        charts.append(('box', fig))
    
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
            
            # Processa i dati fitness per metriche aggiuntive
            df_processed = process_fitness_data(df.copy())
            
            # Mostra informazioni sul dataset con metriche fitness
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Allenamenti", len(df))
            with col2:
                if 'distance' in df.columns:
                    total_distance = df['distance'].sum() / 1000  # Converti in km
                    st.metric("Distanza Totale", f"{total_distance:.1f} km")
                else:
                    st.metric("Colonne", len(df.columns) - 1)
            with col3:
                if 'kiloCalories' in df.columns:
                    total_calories = df['kiloCalories'].sum()
                    st.metric("Calorie Totali", f"{total_calories:,.0f}")
                else:
                    st.metric("Memoria", f"{df.memory_usage().sum() / 1024:.1f} KB")
            with col4:
                if 'duration_minutes' in df_processed.columns:
                    total_time = df_processed['duration_minutes'].sum()
                    hours = int(total_time // 60)
                    minutes = int(total_time % 60)
                    st.metric("Tempo Totale", f"{hours}h {minutes}m")
                else:
                    st.metric("Memoria", f"{df.memory_usage().sum() / 1024:.1f} KB")
            
            # Mostra anteprima dei dati
            st.subheader("📋 Anteprima Dati")
            st.dataframe(df.drop(columns=['source_file']), use_container_width=True)
            
            # Statistiche descrittive fitness-specific
            st.subheader("📈 Statistiche degli Allenamenti")
            
            # Crea un summary personalizzato per i dati fitness
            fitness_stats = {}
            
            if 'distance' in df.columns:
                fitness_stats['Distanza (km)'] = [
                    df['distance'].min() / 1000,
                    df['distance'].mean() / 1000,
                    df['distance'].max() / 1000,
                    df['distance'].std() / 1000
                ]
            
            if 'duration_minutes' in df_processed.columns:
                fitness_stats['Durata (min)'] = [
                    df_processed['duration_minutes'].min(),
                    df_processed['duration_minutes'].mean(),
                    df_processed['duration_minutes'].max(),
                    df_processed['duration_minutes'].std()
                ]
            
            if 'kiloCalories' in df.columns:
                fitness_stats['Calorie'] = [
                    df['kiloCalories'].min(),
                    df['kiloCalories'].mean(),
                    df['kiloCalories'].max(),
                    df['kiloCalories'].std()
                ]
            
            if 'heartRate.avg' in df.columns:
                fitness_stats['FC Media (BPM)'] = [
                    df['heartRate.avg'].min(),
                    df['heartRate.avg'].mean(),
                    df['heartRate.avg'].max(),
                    df['heartRate.avg'].std()
                ]
            
            if 'speed_kmh' in df_processed.columns:
                fitness_stats['Velocità (km/h)'] = [
                    df_processed['speed_kmh'].min(),
                    df_processed['speed_kmh'].mean(),
                    df_processed['speed_kmh'].max(),
                    df_processed['speed_kmh'].std()
                ]
            
            if fitness_stats:
                fitness_df = pd.DataFrame(
                    fitness_stats,
                    index=['Min', 'Media', 'Max', 'Deviazione Std']
                )
                st.dataframe(fitness_df.round(2), use_container_width=True)
            
            # Statistiche descrittive generali per altre colonne
            numeric_data = df.select_dtypes(include=[np.number])
            if not numeric_data.empty:
                with st.expander("📊 Statistiche Complete"):
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
        **Dati Fitness/Allenamenti:**
        ```json
        {
          "exercises": [
            {
              "startTime": "2025-07-21T04:53:40.000",
              "distance": 7545.60009765625,
              "sport": "OTHER_OUTDOOR",
              "kiloCalories": 722,
              "heartRate": {
                "min": 62, "avg": 110, "max": 138
              }
            }
          ]
        }
        ```
        """)
    
    with col2:
        st.markdown("""
        **Formato Oggetto Semplice:**
        ```json
        {
            "vendite": [100, 150, 200, 175],
            "mesi": ["Gen", "Feb", "Mar", "Apr"],
            "regioni": ["Nord", "Sud", "Centro", "Isole"]
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
