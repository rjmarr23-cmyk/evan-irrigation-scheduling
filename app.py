
import streamlit as st
import pandas as pd

st.title("Irrigation Decision Support Tool")

st.write("Upload soil moisture or weather data to help determine irrigation needs.")

# Upload CSV feature
uploaded_file = st.file_uploader("Upload irrigation data (CSV)", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.write("Data Preview")
    st.dataframe(df)

# Manual inputs
st.header("Manual Irrigation Inputs")

soil_moisture = st.slider("Soil Moisture (%)", 0, 100, 40)
temperature = st.slider("Temperature (°F)", 40, 110, 80)
rain_forecast = st.slider("Rain Forecast Next 24h (inches)", 0.0, 2.0, 0.0)

# Irrigation decision logic
st.header("Irrigation Recommendation")

if soil_moisture < 35 and rain_forecast < 0.25:
    decision = "Irrigation Recommended"
elif soil_moisture < 50 and temperature > 90:
    decision = "Consider Irrigation"
else:
    decision = "No Irrigation Needed"

st.subheader(decision)

st.write("Decision Factors")
st.write(f"Soil Moisture: {soil_moisture}%")
st.write(f"Temperature: {temperature}°F")
st.write(f"Rain Forecast: {rain_forecast} inches")
