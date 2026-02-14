import streamlit as st
import pandas as pd
import plotly.express as px
from scipy.stats import chi2_contingency

# --- PAGE SETUP ---
st.set_page_config(page_title="Chicago Crime Dashboard", layout="wide")
st.title("🛡️ Chicago Crime Analysis (2015-2024)")

# --- DATA LOADING ---
@st.cache_data
def load_data():
    # Direct download link created from your File ID
    file_id = "1TIKj3UxtW1HUFBeDri3kh-keu5d8ETrK"
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    
    try:
        # Loading full dataset (low_memory=False handles mixed types)
        df = pd.read_csv(url, low_memory=False)
        
        # Date Processing (Logic from generate_5_charts.py)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df['Year'] = df['Date'].dt.year
        df['Month'] = df['Date'].dt.month
        df['Hour'] = df['Date'].dt.hour
        df['DayOfWeek'] = df['Date'].dt.day_name()
        
        # Time Period Categorization (Logic from correlation.ipynb)
        df["Time_Period"] = df["Hour"].apply(
            lambda x: "Early Morning" if 0<=x<6 else "Morning" if 6<=x<12 else 
                      "Afternoon" if 12<=x<18 else "Night"
        )
        return df
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        return None

df = load_data()

if df is not None:
    # --- SIDEBAR FILTERS ---
    st.sidebar.header("Navigation & Filters")
    year_range = st.sidebar.slider("Select Year Range", 2015, 2025, (2015, 2025))
    filtered_df = df[(df['Year'] >= year_range[0]) & (df['Year'] <= year_range[1])]

    # --- TABS FOR ALL EDA ---
    tab1, tab2, tab3 = st.tabs(["📅 Temporal & Districts", "🗺️ Spatial Study", "📊 Correlation & Arrests"])

    with tab1:
        st.header("Temporal Trends & District Breakdown")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Crime Count by Year")
            y_counts = filtered_df['Year'].value_counts().sort_index().reset_index()
            st.plotly_chart(px.bar(y_counts, x='Year', y='count', color_discrete_sequence=['steelblue']), use_container_width=True)
        with col2:
            st.subheader("Top 15 Districts")
            d_counts = filtered_df['District'].value_counts().head(15).reset_index()
            st.plotly_chart(px.bar(d_counts, x='count', y='District', orientation='h', color_discrete_sequence=['navy']), use_container_width=True)

    with tab2:
        st.header("Spatial Mapping")
        # Sampling 15k points for Cloud performance
        map_df = filtered_df.dropna(subset=['Latitude', 'Longitude']).sample(min(15000, len(filtered_df)))
        fig_map = px.scatter_mapbox(map_df, lat="Latitude", lon="Longitude", color="Primary Type",
                                    zoom=10, mapbox_style="carto-positron", height=700)
        st.plotly_chart(fig_map, use_container_width=True)

    with tab3:
        st.header("Statistical Correlation")
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.subheader("Arrest Rate by Time Period")
            arrest_rate = filtered_df.groupby("Time_Period")["Arrest"].mean().reset_index()
            arrest_rate["Arrest %"] = arrest_rate["Arrest"] * 100
            st.plotly_chart(px.bar(arrest_rate, x="Time_Period", y="Arrest %", text_auto='.1f'), use_container_width=True)
            
        with col_b:
            st.subheader("Crime Type vs. Time (Chi-Square)")
            ct_time = pd.crosstab(filtered_df["Primary Type"].head(10), filtered_df["Time_Period"])
            st.plotly_chart(px.imshow(ct_time, text_auto=True, color_continuous_scale='YlOrRd'), use_container_width=True)

else:
    st.info("Awaiting data from Google Drive...")

