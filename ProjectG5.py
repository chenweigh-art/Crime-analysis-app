import streamlit as st
import pandas as pd
import plotly.express as px
from scipy.stats import chi2_contingency

# --- PAGE SETUP ---
st.set_page_config(page_title="Chi-Town Sentinel", layout="wide")
st.title("🛡️ Chi-Town Sentinel: 10-Year Public Safety Analysis (2015-2025)")

# --- DATA LOADING (Google Drive Link) ---
@st.cache_data
def load_data():
    file_id = "1TIKj3UxtW1HUFBeDri3kh-keu5d8ETrK"
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    
    try:
        # low_memory=False handles the large 10-year dataset efficiently
        df = pd.read_csv(url, low_memory=False)
        
        # Unified Processing from generate_5_charts.py & correlation.ipynb
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df['Year'] = df['Date'].dt.year
        df['Month'] = df['Date'].dt.month
        df['Hour'] = df['Date'].dt.hour
        
        # Time Period Feature (Required for Correlation Analysis)
        df["Time_Period"] = df["Hour"].apply(
            lambda x: "Early Morning (0-6)" if 0<=x<6 else 
                      "Morning (6-12)" if 6<=x<12 else 
                      "Afternoon (12-18)" if 12<=x<18 else "Night (18-24)"
        )
        return df
    except Exception as e:
        st.error(f"Cloud Connection Error: {e}")
        return None

df = load_data()

if df is not None:
    # --- SIDEBAR NAVIGATION ---
    st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/9/9b/Flag_of_Chicago%2C_Illinois.svg", width=100)
    st.sidebar.header("Sentinel Controls")
    year_filter = st.sidebar.slider("Analysis Period", 2015, 2025, (2015, 2025))
    
    filtered_df = df[(df['Year'] >= year_filter[0]) & (df['Year'] <= year_filter[1])]

    # --- MAIN TABS ---
    tab1, tab2, tab3 = st.tabs(["📅 Temporal Trends", "🗺️ Spatial Study", "📊 Statistical Correlations"])

    # TAB 1: From generate_5_charts.py
    with tab1:
        st.header("Temporal Crime Dynamics")
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Yearly Impact (Incl. COVID-19 Era)")
            y_counts = filtered_df['Year'].value_counts().sort_index().reset_index()
            st.plotly_chart(px.bar(y_counts, x='Year', y='count', color='count', color_continuous_scale='Blues'), use_container_width=True)
        with c2:
            st.subheader("Top 15 Police Districts")
            d_counts = filtered_df['District'].value_counts().head(15).reset_index()
            st.plotly_chart(px.bar(d_counts, x='count', y='District', orientation='h', color_discrete_sequence=['navy']), use_container_width=True)

    # TAB 2: Geospatial Hotspots
    with tab2:
        st.header("Geospatial Hotspots")
        # Sampling 20k points for better cloud performance
        map_df = filtered_df.dropna(subset=['Latitude', 'Longitude']).sample(min(20000, len(filtered_df)))
        fig_map = px.scatter_mapbox(map_df, lat="Latitude", lon="Longitude", color="Primary Type",
                                    zoom=10, mapbox_style="carto-positron", height=700)
        st.plotly_chart(fig_map, use_container_width=True)

    # TAB 3: From correlation.ipynb
    with tab3:
        st.header("Arrest Rates & Statistical Significance")
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.subheader("Arrest Efficiency by Time Period")
            arrest_rate = filtered_df.groupby("Time_Period")["Arrest"].mean().reset_index()
            arrest_rate["Arrest %"] = arrest_rate["Arrest"] * 100
            st.plotly_chart(px.bar(arrest_rate, x="Time_Period", y="Arrest %", text_auto='.1f', color="Arrest %"), use_container_width=True)
            
        with col_b:
            st.subheader("Crime Type vs. Time (Heatmap)")
            ct_time = pd.crosstab(filtered_df["Primary Type"].head(10), filtered_df["Time_Period"])
            st.plotly_chart(px.imshow(ct_time, text_auto=True, color_continuous_scale='YlOrRd'), use_container_width=True)
            
        # Pearson Correlation Matrix
        st.subheader("Crime Co-occurrence Matrix (Pearson)")
        # Group by Community Area and Hour as per your notebook logic
        corr_matrix_data = filtered_df.groupby(["Community Area", "Hour", "Primary Type"]).size().unstack(fill_value=0)
        st.plotly_chart(px.imshow(corr_matrix_data.corr(), text_auto=".2f", color_continuous_scale='RdBu_r'), use_container_width=True)

else:
    st.warning("Connecting to secure data stream... please wait.")
