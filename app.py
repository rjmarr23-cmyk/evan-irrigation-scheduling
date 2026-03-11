import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="Irrigation Planning Dashboard",
    page_icon="🌱",
    layout="wide"
)

# ---------------------------
# Page styling (different look)
# ---------------------------
st.markdown("""
<style>
.main {
    background-color: #f6f8f7;
}
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
}
.hero-box {
    background: linear-gradient(135deg, #1f6f5f, #3aa17e);
    padding: 1.4rem 1.6rem;
    border-radius: 18px;
    color: white;
    margin-bottom: 1rem;
}
.metric-card {
    background: white;
    padding: 1rem;
    border-radius: 16px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    border-left: 6px solid #2e8b57;
}
.section-card {
    background: white;
    padding: 1rem 1.1rem;
    border-radius: 16px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.05);
    margin-bottom: 1rem;
}
.small-note {
    font-size: 0.9rem;
    color: #4f4f4f;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero-box">
    <h1 style="margin-bottom:0.2rem;">🌱 Irrigation Planning Dashboard</h1>
    <p style="margin-top:0; font-size:1.05rem;">
        Upload weather data, review ET and precipitation trends, and get a daily irrigation recommendation.
    </p>
</div>
""", unsafe_allow_html=True)

# ---------------------------
# Load data
# ---------------------------
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.subheader("Data Source")

uploaded_file = st.file_uploader("Upload your irrigation CSV file", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.success("CSV uploaded successfully.")
else:
    st.info("No CSV uploaded yet. Upload a file to run the dashboard.")
    st.stop()

st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------
# Validate expected columns
# ---------------------------
required_columns = [
    "Year", "Month", "Date", "Time",
    "Temperature_High_F", "Temperature_Low_F",
    "Precipitation_inches", "ET_inches"
]

missing_cols = [col for col in required_columns if col not in df.columns]
if missing_cols:
    st.error(f"Your CSV is missing these required columns: {missing_cols}")
    st.stop()

# ---------------------------
# Clean and reorganize data
# ---------------------------
df = df.copy()

df["Date_String"] = (
    df["Year"].astype(str) + "-" +
    df["Month"].astype(str) + "-" +
    df["Date"].astype(str)
)

df["Date_YMD"] = pd.to_datetime(df["Date_String"], format="%Y-%m-%d", errors="coerce")

if df["Date_YMD"].isna().any():
    st.error("Some dates could not be read correctly. Check the Year, Month, and Date columns.")
    st.stop()

df["Month_Name"] = df["Date_YMD"].dt.strftime("%B")
df["Day"] = df["Date_YMD"].dt.day
df["Temp_Avg"] = (df["Temperature_High_F"] + df["Temperature_Low_F"]) / 2
df["Precip_Cum"] = df["Precipitation_inches"].cumsum()
df["ET_Cum"] = df["ET_inches"].cumsum()

drop_cols = [col for col in ["Date_String", "Time"] if col in df.columns]
df.drop(columns=drop_cols, inplace=True)

# ---------------------------
# Custom irrigation logic
# Same function, different appearance
# ---------------------------
management_allowed_depletion = 1.0
max_irrigation_per_event = 1.0

df["Irrigation_daily"] = 0.0
df["Irrigation_Cum"] = 0.0

current_deficit = 0.0

for i in range(len(df)):
    daily_et = df.loc[df.index[i], "ET_inches"]
    daily_precip = df.loc[df.index[i], "Precipitation_inches"]

    current_deficit += daily_et - daily_precip

    if current_deficit > management_allowed_depletion:
        irrigation_amount_needed = current_deficit
        applied_irrigation = min(irrigation_amount_needed, max_irrigation_per_event)

        df.loc[df.index[i], "Irrigation_daily"] = applied_irrigation
        current_deficit -= applied_irrigation

        if current_deficit < 0:
            current_deficit = 0.0

    if i > 0:
        df.loc[df.index[i], "Irrigation_Cum"] = (
            df.loc[df.index[i - 1], "Irrigation_Cum"] +
            df.loc[df.index[i], "Irrigation_daily"]
        )
    else:
        df.loc[df.index[i], "Irrigation_Cum"] = df.loc[df.index[i], "Irrigation_daily"]

df["Irrig_Precip_Cum"] = df["Precip_Cum"] + df["Irrigation_Cum"]

# ---------------------------
# Sidebar controls
# ---------------------------
st.sidebar.header("Dashboard Controls")

selected_month = st.sidebar.selectbox(
    "Choose month",
    df["Month_Name"].dropna().unique()
)

filtered_df = df[df["Month_Name"] == selected_month].copy()

selected_day = st.sidebar.selectbox(
    "Choose day",
    filtered_df["Day"].dropna().unique()
)

selected_day_data = filtered_df[filtered_df["Day"] == selected_day].iloc[0]

# ---------------------------
# Top summary cards
# ---------------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("Selected Date", f"{selected_month} {selected_day}")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("Daily ET (in)", f"{selected_day_data['ET_inches']:.2f}")
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("Daily Precip. (in)", f"{selected_day_data['Precipitation_inches']:.2f}")
    st.markdown('</div>', unsafe_allow_html=True)

with col4:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("Irrigation Rec. (in)", f"{selected_day_data['Irrigation_daily']:.2f}")
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------
# Recommendation panel
# ---------------------------
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.subheader("Irrigation Recommendation")

if selected_day_data["Irrigation_daily"] > 0:
    st.success(
        f"Apply **{selected_day_data['Irrigation_daily']:.2f} inches** of irrigation on "
        f"**{selected_month} {selected_day}**."
    )
else:
    st.info(
        f"No irrigation is recommended on **{selected_month} {selected_day}** based on the current deficit rule."
    )

st.markdown(
    f"""
    <div class="small-note">
    Decision inputs for the selected day:
    <br>- ET: <b>{selected_day_data['ET_inches']:.2f}</b> in
    <br>- Precipitation: <b>{selected_day_data['Precipitation_inches']:.2f}</b> in
    <br>- Avg Temp: <b>{selected_day_data['Temp_Avg']:.2f}</b> °F
    </div>
    """,
    unsafe_allow_html=True
)
st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------
# Charts
# ---------------------------
tab1, tab2, tab3 = st.tabs(["Weather Trend", "Irrigation vs ET", "Data Table"])

with tab1:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Daily and Cumulative Precipitation + ET")

    fig1, ax1 = plt.subplots(figsize=(11, 5))

    ax1.bar(df.index, df["Precipitation_inches"], label="Daily precipitation")
    ax1.plot(df.index, df["Precip_Cum"], label="Cumulative precipitation")
    ax1.set_xlabel("Day of Year Index")
    ax1.set_ylabel("Precipitation (inches)")
    ax1.set_ylim(0, 60)
    ax1.set_xlim(0, max(len(df), 10))
    ax1.grid(True, alpha=0.3)

    ax2 = ax1.twinx()
    ax2.plot(df.index, df["ET_Cum"], label="Cumulative ET")
    ax2.plot(df.index, df["ET_inches"], label="Daily ET")
    ax2.set_ylabel("ET (inches)")
    ax2.set_ylim(0, 60)
    ax2.set_xlim(0, max(len(df), 10))

    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    fig1.legend(handles1 + handles2, labels1 + labels2, loc="upper left", bbox_to_anchor=(0.08, 0.94))

    st.pyplot(fig1)
    st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Cumulative Water Supply vs ET")

    fig2, ax21 = plt.subplots(figsize=(11, 5))

    ax21.plot(df.index, df["Irrig_Precip_Cum"], label="Precipitation + Irrigation")
    ax21.bar(df.index, df["Irrigation_daily"], label="Daily irrigation")
    ax21.bar(df.index, df["Precipitation_inches"], label="Daily precipitation")
    ax21.set_xlabel("Day of Year Index")
    ax21.set_ylabel("Water Applied / Received (inches)")
    ax21.set_ylim(0, 60)
    ax21.set_xlim(0, max(len(df), 10))
    ax21.grid(True, alpha=0.3)

    ax22 = ax21.twinx()
    ax22.plot(df.index, df["ET_Cum"], label="Cumulative ET")
    ax22.set_ylabel("ET (inches)")
    ax22.set_ylim(0, 60)
    ax22.set_xlim(0, max(len(df), 10))

    handles21, labels21 = ax21.get_legend_handles_labels()
    handles22, labels22 = ax22.get_legend_handles_labels()
    fig2.legend(handles21 + handles22, labels21 + labels22, loc="upper left", bbox_to_anchor=(0.08, 0.94))

    st.pyplot(fig2)
    st.markdown('</div>', unsafe_allow_html=True)

with tab3:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Processed Dataset")

    display_cols = [
        "Date_YMD", "Month_Name", "Day", "Temperature_High_F", "Temperature_Low_F",
        "Temp_Avg", "Precipitation_inches", "ET_inches",
        "Irrigation_daily", "Irrigation_Cum", "Precip_Cum", "ET_Cum", "Irrig_Precip_Cum"
    ]

    existing_display_cols = [col for col in display_cols if col in df.columns]
    st.dataframe(df[existing_display_cols], use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
