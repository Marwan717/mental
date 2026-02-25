import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime
import plotly.express as px

st.set_page_config(page_title="Performance Mood OS", layout="wide")

# ---------------- DATABASE ----------------
conn = sqlite3.connect("mood_data.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS checkins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    mood INTEGER,
    stress INTEGER,
    sleep REAL,
    focus INTEGER,
    workload INTEGER,
    notes TEXT
)
""")
conn.commit()

# ---------------- FUNCTIONS ----------------

def calculate_performance_index(mood, stress, sleep, focus):
    return round((mood*0.3 + focus*0.3 + sleep*0.2 + (10-stress)*0.2), 2)

def burnout_risk(df):
    if len(df) < 5:
        return "Low"

    recent = df.tail(5)
    avg_stress = recent["stress"].mean()
    avg_sleep = recent["sleep"].mean()
    avg_focus = recent["focus"].mean()

    if avg_stress > 7 and avg_sleep < 6 and avg_focus < 5:
        return "High"
    elif avg_stress > 6 and avg_sleep < 6.5:
        return "Moderate"
    else:
        return "Low"

def ai_insight(df):
    if len(df) < 3:
        return "Log more data to unlock insights."

    trend = df.tail(7)

    sleep_focus_corr = trend["sleep"].corr(trend["focus"])
    stress_mood_corr = trend["stress"].corr(trend["mood"])

    insights = []

    if sleep_focus_corr > 0.5:
        insights.append("Sleep strongly improves focus. Protect sleep.")
    if stress_mood_corr < -0.5:
        insights.append("Stress is heavily impacting mood.")
    if trend["workload"].mean() > 7:
        insights.append("High workload detected. Monitor recovery.")

    if not insights:
        insights.append("Stable performance. Maintain routines.")

    return " | ".join(insights)

# ---------------- UI ----------------

st.title("🔥 Performance Mood OS")
st.markdown("Track. Analyze. Optimize.")

tab1, tab2, tab3 = st.tabs(["Daily Check-In", "Analytics Dashboard", "Data Export"])

# ---------------- CHECK-IN ----------------

with tab1:
    st.subheader("Daily Performance Check-In")

    mood = st.slider("Mood (1 = Low, 10 = Elite)", 1, 10, 7)
    stress = st.slider("Stress (1 = Calm, 10 = Overloaded)", 1, 10, 5)
    sleep = st.slider("Sleep Hours", 0.0, 12.0, 7.0, 0.5)
    focus = st.slider("Focus Level", 1, 10, 7)
    workload = st.slider("Workload Intensity", 1, 10, 6)
    notes = st.text_area("Optional Notes")

    if st.button("Submit Check-In"):
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO checkins (date, mood, stress, sleep, focus, workload, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (date, mood, stress, sleep, focus, workload, notes))
        conn.commit()

        performance = calculate_performance_index(mood, stress, sleep, focus)

        st.success("Check-In Saved")
        st.metric("Performance Index", performance)

# ---------------- ANALYTICS ----------------

with tab2:
    st.subheader("Performance Analytics")

    df = pd.read_sql_query("SELECT * FROM checkins", conn)

    if len(df) > 0:
        df["date"] = pd.to_datetime(df["date"])
        df["performance"] = df.apply(
            lambda x: calculate_performance_index(
                x["mood"], x["stress"], x["sleep"], x["focus"]
            ),
            axis=1,
        )

        col1, col2, col3 = st.columns(3)

        col1.metric("Average Performance", round(df["performance"].mean(), 2))
        col2.metric("Burnout Risk", burnout_risk(df))
        col3.metric("Entries Logged", len(df))

        fig1 = px.line(df, x="date", y="performance", title="Performance Trend")
        st.plotly_chart(fig1, use_container_width=True)

        fig2 = px.scatter(df, x="sleep", y="focus", title="Sleep vs Focus")
        st.plotly_chart(fig2, use_container_width=True)

        fig3 = px.scatter(df, x="stress", y="mood", title="Stress vs Mood")
        st.plotly_chart(fig3, use_container_width=True)

        st.subheader("AI Performance Insight")
        st.info(ai_insight(df))

    else:
        st.warning("No data yet. Log your first check-in.")

# ---------------- EXPORT ----------------

with tab3:
    st.subheader("Export Data")

    df = pd.read_sql_query("SELECT * FROM checkins", conn)

    if len(df) > 0:
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "performance_data.csv", "text/csv")
    else:
        st.warning("No data available to export.")
