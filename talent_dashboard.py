# talent_dashboard_final.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# ---------- PAGE SETUP ----------
st.set_page_config(page_title="TMI Dashboard", layout="wide")
st.title("🎯 Talent Match Intelligence Dashboard")

# ---------- LOAD DATA ----------
@st.cache_data
def load_data():
    return pd.read_csv("df_final_fix.csv")

try:
    df = load_data()
except FileNotFoundError:
    st.error("❌ File `df_final_fix.csv` not found. Please place it in the same directory as this script.")
    st.stop()

# ---------- INPUT ----------
st.sidebar.header("Job Filter")
job_input = st.sidebar.text_input("Enter Job Position (e.g. Data Analyst):", "").strip()

if not job_input:
    st.info("📝 Please enter a Job Position in the sidebar to begin the analysis.")
    st.stop()

# Case-insensitive filter
mask = df["position_name"].str.lower() == job_input.lower()
df_filtered = df[mask]

if df_filtered.empty:
    st.error(f"❌ Position '{job_input}' not found in the dataset.")
    st.stop()

st.success(f"✅ Found {len(df_filtered)} employees with position **{job_input.title()}**")

# ---------- FEATURE ENGINEERING ----------
# Match tv_ and bench_ columns safely
tv_cols = [c for c in df.columns if c.startswith("tv_")]
bench_cols = [f"bench_{c.replace('tv_', '')}" for c in tv_cols if f"bench_{c.replace('tv_', '')}" in df.columns]
pairs = [(tv, f"bench_{tv.replace('tv_', '')}") for tv in tv_cols if f"bench_{tv.replace('tv_', '')}" in df.columns]

# Compute average TV gap
def compute_gap(row):
    diffs = []
    for tv, bench in pairs:
        if pd.notna(row[tv]) and pd.notna(row[bench]):
            diffs.append(row[tv] - row[bench])
    return np.mean(diffs) if diffs else np.nan

if pairs:
    df_filtered["gap_tv"] = df_filtered.apply(compute_gap, axis=1)
else:
    st.warning("⚠️ No matching tv_ and bench_ column pairs found.")
    df_filtered["gap_tv"] = np.nan

# Compute TGV average
tgv_cols = [c for c in df.columns if c.startswith("tgv_")]
if tgv_cols:
    df_filtered["tgv_avg"] = df_filtered[tgv_cols].mean(axis=1)
else:
    df_filtered["tgv_avg"] = np.nan
    st.warning("⚠️ No tgv_ columns found in the dataset.")

# ---------- VISUAL 1: MATCH RATE DISTRIBUTION ----------
st.subheader(f"📊 Distribution of Final Match Rate — {job_input.title()}")
fig = px.histogram(
    df_filtered,
    x="final_match_rate",
    nbins=20,
    color_discrete_sequence=["#3A86FF"],
    title="Distribution of Final Match Rate (%)"
)
fig.update_layout(xaxis_title="Final Match Rate", yaxis_title="Number of Employees")
st.plotly_chart(fig, use_container_width=True)

# ---------- VISUAL 2: BOX PLOT BY GRADE ----------
if "grade_name" in df_filtered.columns:
    st.subheader("📦 Match Rate Distribution by Grade")
    fig2 = px.box(
        df_filtered,
        x="grade_name",
        y="final_match_rate",
        color="grade_name",
        color_discrete_sequence=px.colors.qualitative.Pastel,
        title="Boxplot of Final Match Rate per Grade"
    )
    fig2.update_layout(xaxis_title="Grade", yaxis_title="Final Match Rate (%)", showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)

# ---------- TABLES: TOP & BOTTOM PERFORMERS ----------
st.subheader("🏆 Top & Bottom Performers")

top10 = df_filtered.sort_values("final_match_rate", ascending=False).head(10)
bottom10 = df_filtered.sort_values("final_match_rate", ascending=True).head(10)

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🔝 Top 10 Performers")
    if top10.empty:
        st.write("No data available for this position.")
    else:
        st.dataframe(
            top10[["fullname", "gap_tv", "tgv_avg", "final_match_rate"]]
            .rename(columns={
                "fullname": "Name",
                "gap_tv": "Avg TV Gap",
                "tgv_avg": "Avg TGV",
                "final_match_rate": "Final Match Rate (%)"
            })
            .style.format({
                "Avg TV Gap": "{:.2f}",
                "Avg TGV": "{:.2f}",
                "Final Match Rate (%)": "{:.2f}"
            }),
            use_container_width=True,
            height=320
        )

with col2:
    st.markdown("### 🔻 Bottom 10 Performers")
    if bottom10.empty:
        st.write("No data available for this position.")
    else:
        st.dataframe(
            bottom10[["fullname", "gap_tv", "tgv_avg", "final_match_rate"]]
            .rename(columns={
                "fullname": "Name",
                "gap_tv": "Avg TV Gap",
                "tgv_avg": "Avg TGV",
                "final_match_rate": "Final Match Rate (%)"
            })
            .style.format({
                "Avg TV Gap": "{:.2f}",
                "Avg TGV": "{:.2f}",
                "Final Match Rate (%)": "{:.2f}"
            }),
            use_container_width=True,
            height=320
        )

# ---------- VISUAL 3: RADAR CHART ----------
if tgv_cols:
    st.subheader("🧭 Average TGV Profile (Talent Group Variable)")
    tgv_means = df_filtered[tgv_cols].mean()
    fig3 = go.Figure()
    fig3.add_trace(go.Scatterpolar(
        r=tgv_means.values,
        theta=tgv_means.index,
        fill='toself',
        name='Average TGV'
    ))
    fig3.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=False,
        title=f"Average TGV Scores — {job_input.title()}"
    )
    st.plotly_chart(fig3, use_container_width=True)

# ---------- SUMMARY INSIGHTS ----------
st.subheader("💡 Summary Insights")

avg_rate = df_filtered["final_match_rate"].mean()
std_rate = df_filtered["final_match_rate"].std()

if not top10.empty and not bottom10.empty:
    best = top10.iloc[0]
    worst = bottom10.iloc[0]
    st.markdown(f"""
    **Average Match Rate:** {avg_rate:.2f}%  
    **Standard Deviation:** {std_rate:.2f}  
    **Top Performer:** {best['fullname']} ({best['final_match_rate']:.2f}%)  
    **Lowest Performer:** {worst['fullname']} ({worst['final_match_rate']:.2f}%)
    """)
else:
    st.write(f"**Average Match Rate:** {avg_rate:.2f}%  \n**Standard Deviation:** {std_rate:.2f}")
    