import streamlit as st
import pandas as pd
import plotly.express as px
from scipy.stats import chi2_contingency
import os

# --- PAGE SETUP ---
st.set_page_config(page_title="Chi-Town Sentinel", layout="wide", page_icon="🛡️")
st.title("🛡️ Chicago Crime Analysis (2015-2024)")

# --- DATA LOADING (Option B: Google Drive) ---
@st.cache_data(show_spinner="Connecting to Sentinel Data Stream (2015-2025)...")
def load_data():
    file_id = "1TIKj3UxtW1HUFBeDri3kh-keu5d8ETrK"
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    
    try:
        # Load the full 10-year dataset
        df = pd.read_csv(url, low_memory=False)
        
        # Unified processing from generate_5_charts.py & correlation.ipynb
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df['Year'] = df['Date'].dt.year
        df['Hour'] = df['Date'].dt.hour
        
        # Feature Engineering for Correlation Analysis
        df["Time_Period"] = df["Hour"].apply(
            lambda x: "Early Morning (0-6)" if 0<=x<6 else 
                      "Morning (6-12)" if 6<=x<12 else 
                      "Afternoon (12-18)" if 12<=x<18 else "Night (18-24)"
        )
        return df
    except Exception as e:
        st.error(f"Connection Failed: {e}")
        return None

df = load_data()

if df is not None:
    # --- SIDEBAR FILTERS ---
    st.sidebar.header("Sentinel Controls")
    year_range = st.sidebar.slider("Select Analysis Period", 2015, 2025, (2015, 2025))
    f_df = df[(df['Year'] >= year_range[0]) & (df['Year'] <= year_range[1])]

    # --- TABS ---
    tab1, tab2, tab3 = st.tabs(["📅 Temporal Trends", "🗺️ Spatial Study", "📊 Correlations"])

    with tab1:
        st.header("Temporal Trends (Including COVID-19 Impact)")
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Crime Volume by Year")
            y_counts = f_df['Year'].value_counts().sort_index().reset_index()
            st.plotly_chart(px.bar(y_counts, x='Year', y='count', color='count', color_continuous_scale='Blues'), use_container_width=True)
        with c2:
            st.subheader("Top 15 Police Districts")
            d_counts = f_df['District'].value_counts().head(15).reset_index()
            st.plotly_chart(px.bar(d_counts, x='count', y='District', orientation='h', color_discrete_sequence=['navy']), use_container_width=True)

    with tab2:
        st.header("Geospatial Hotspots")
        # Sampling 15k points to prevent browser crashes with 10 years of data
        map_df = f_df.dropna(subset=['Latitude', 'Longitude']).sample(min(15000, len(f_df)))
        st.plotly_chart(px.scatter_mapbox(map_df, lat="Latitude", lon="Longitude", color="Primary Type",
                                          zoom=10, mapbox_style="carto-positron", height=600), use_container_width=True)

    with tab3:
        st.header("Arrest Efficiency & Significance")
        # Logic from correlation.ipynb
        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("Arrest Rate by Time Period")
            a_rate = f_df.groupby("Time_Period")["Arrest"].mean().reset_index()
            a_rate["Arrest %"] = a_rate["Arrest"] * 100
            st.plotly_chart(px.bar(a_rate, x="Time_Period", y="Arrest %", text_auto='.1f'), use_container_width=True)
        with col_b:
            st.subheader("Crime vs. Time Heatmap")
            ct = pd.crosstab(f_df["Primary Type"].head(10), f_df["Time_Period"])
            st.plotly_chart(px.imshow(ct, text_auto=True, color_continuous_scale='YlOrRd'), use_container_width=True)

else:
    st.info("Searching for file...  ensure terminal is in the correct folder.")

