
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(layout="wide")

st.title("Unified Smart Irrigation Dashboard - Treatments T1 to T4")

# --- Sidebar ---
st.sidebar.title("Select Treatment")
treatment = st.sidebar.selectbox("Choose a treatment:", ["T1 - Control", "T2 - Soil Moisture + Weather", "T3 - NDVI + Weather", "T4 - NDVI + Soil + Weather"])

# --- Upload File ---
uploaded_file = st.file_uploader("Upload your treatment-specific dataset (.csv)", type="csv")

# --- Common Parameters ---
st.sidebar.markdown("---")
kc = st.sidebar.number_input("Crop Coefficient (Kc)", value=1.15)
fc = st.sidebar.number_input("Field Capacity [%]", value=38.0)
moisture_threshold = 0.70 * fc

# --- Logic Per Treatment ---
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, parse_dates=['timestamp'])

    if treatment == "T1 - Control":
        st.info("T1 is the control group — no irrigation logic applied. Displaying data only.")
        st.dataframe(df)

    elif treatment == "T2 - Soil Moisture + Weather":
        rain_threshold = st.sidebar.number_input("Rain Threshold (mm)", value=2.0)
        st.subheader("T2 Irrigation Logic")

        def t2_logic(row):
            if row['soil_moisture'] < moisture_threshold:
                if row['forecast_rain'] < rain_threshold:
                    etc = row['ET0'] * kc
                    irrigation = max(0, etc - row['forecast_rain'])
                    return pd.Series([True, etc, irrigation])
            return pd.Series([False, 0, 0])

        df[['irrigate', 'ETc', 'irrigation_mm']] = df.apply(t2_logic, axis=1)

    elif treatment == "T3 - NDVI + Weather":
        ndvi_threshold = st.sidebar.number_input("NDVI Stress Threshold", value=0.65)
        rain_threshold = st.sidebar.number_input("Rain Threshold (mm)", value=2.0)
        et0_threshold = st.sidebar.number_input("ET0 Threshold (mm)", value=3.5)
        st.subheader("T3 Irrigation Logic")

        def t3_logic(row):
            if row['NDVI'] < ndvi_threshold and row['ET0'] > et0_threshold and row['forecast_rain'] < rain_threshold:
                etc = row['ET0'] * kc
                irrigation = max(0, etc - row['forecast_rain'])
                return pd.Series([True, etc, irrigation])
            return pd.Series([False, 0, 0])

        df[['irrigate', 'ETc', 'irrigation_mm']] = df.apply(t3_logic, axis=1)

    elif treatment == "T4 - NDVI + Soil + Weather":
        ndvi_threshold = st.sidebar.number_input("NDVI Stress Threshold", value=0.65)
        rain_threshold = st.sidebar.number_input("Rain Threshold (mm)", value=2.0)
        et0_threshold = st.sidebar.number_input("ET0 Threshold (mm)", value=3.5)
        st.subheader("T4 Irrigation Logic")

        def t4_logic(row):
            if (
                row['NDVI'] < ndvi_threshold and
                row['soil_moisture'] < moisture_threshold and
                row['ET0'] > et0_threshold and
                row['forecast_rain'] < rain_threshold
            ):
                etc = row['ET0'] * kc
                irrigation = max(0, etc - row['forecast_rain'])
                return pd.Series([True, etc, irrigation])
            return pd.Series([False, 0, 0])

        df[['irrigate', 'ETc', 'irrigation_mm']] = df.apply(t4_logic, axis=1)

    # --- Show Results ---
    if treatment != "T1 - Control":
        st.success("Irrigation schedule calculated.")
        st.dataframe(df)

        # Plot
        st.subheader("📈 Visualization")
        fig, ax = plt.subplots(figsize=(12, 6))
        if 'NDVI' in df.columns:
            sns.lineplot(data=df, x='timestamp', y='NDVI', label='NDVI', marker='o', ax=ax)
        if 'soil_moisture' in df.columns:
            sns.lineplot(data=df, x='timestamp', y='soil_moisture', label='Soil Moisture', marker='x', ax=ax)
        if 'ET0' in df.columns:
            sns.lineplot(data=df, x='timestamp', y='ET0', label='ET0', marker='s', ax=ax)
        if 'forecast_rain' in df.columns:
            sns.lineplot(data=df, x='timestamp', y='forecast_rain', label='Rain Forecast', marker='^', ax=ax)
        if 'irrigation_mm' in df.columns:
            sns.lineplot(data=df, x='timestamp', y='irrigation_mm', label='Irrigation (mm)', marker='D', ax=ax)
        ax.set_title("Irrigation Scheduling Data")
        ax.set_xlabel("Date")
        ax.set_ylabel("Values")
        ax.legend()
        ax.grid(True)
        st.pyplot(fig)

        # Download
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Schedule", csv, f"{treatment.replace(' ', '_')}_schedule.csv", "text/csv")
else:
    st.info("Please upload your dataset to proceed.")
