import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="IoT Graph Test",
    layout="wide"
)

st.title("🏭 IoT Fault Diagnosis Dashboard")

st.success("Streamlit is working!")

data = pd.DataFrame({
    "Temperature": [50, 52, 55, 53, 58, 62, 65, 61, 59, 63],
    "Vibration": [1.5, 1.7, 1.8, 2.0, 2.2, 2.8, 3.5, 3.0, 2.6, 3.2],
    "Current": [5.5, 5.7, 5.9, 6.0, 6.2, 6.8, 7.5, 7.0, 6.5, 7.2],
    "Pressure": [2.5, 2.5, 2.4, 2.6, 2.5, 2.4, 2.3, 2.5, 2.6, 2.4],
    "RPM": [1450, 1455, 1460, 1448, 1452, 1435, 1400, 1420, 1440, 1410]
})

st.subheader("🌡️ Temperature")
st.line_chart(data["Temperature"])

st.subheader("〰️ Vibration")
st.line_chart(data["Vibration"])

st.subheader("⚡ Current")
st.line_chart(data["Current"])

st.subheader("💨 Pressure")
st.line_chart(data["Pressure"])

st.subheader("⚙️ RPM")
st.line_chart(data["RPM"])

st.subheader("Raw Data")
st.dataframe(data)
