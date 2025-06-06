
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="Demo KPI Dashboard",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="expanded"
)

st.title("📈 Forecast Error KPI Dashboard")

# Sidebar for file upload
st.sidebar.image("logo_daki.png")
st.sidebar.header("Upload your Excel data")
# Mostrar el logo de Daki en la barra lateral



uploaded_file = st.sidebar.file_uploader("Choose an .xlsx file", type=["xlsx"])

if uploaded_file:
    df_full = pd.read_excel(uploaded_file, sheet_name="Datos y Métricas")
else:
    st.sidebar.info(
        "Upload the **demo_forecast_kpis_completo.xlsx** file "
        "or your own file with the same sheet structure."
    )
    st.stop()

# ---- KPI CALCULATIONS ----
overall_metrics = {
    "MAPE (%)": df_full["MAPE"].mean(skipna=True) * 100,
    "MAE": df_full["Error Absoluto"].mean(),
    "RMSE": np.sqrt(df_full["RMSE"].mean()),
    "WMAPE (%)": df_full["WMAPE"].mean(skipna=True) * 100,
    "SMAPE (%)": df_full["SMAPE"].mean(skipna=True) * 100,
    "MAE Naive": df_full["Error Naive"].mean(),
    "MASE": (df_full["Error Absoluto"].mean() /
             df_full["Error Naive"].mean())
}

# ---- METRIC CARDS ----
metric_cols = st.columns(len(overall_metrics))
for col, (metric, value) in zip(metric_cols, overall_metrics.items()):
    fmt = f"{value:.2f}"
    col.metric(metric, fmt)

st.markdown("---")

# ---- GROUP ANALYSIS ----
st.header("KPIs by Category and Region")
group_df = df_full.groupby(["Categoría", "Región"]).agg(
    MAPE_pct=("MAPE", lambda x: x.mean(skipna=True) * 100),
    MAE=("Error Absoluto", "mean"),
    RMSE=("RMSE", lambda x: np.sqrt(np.mean(x))),
    WMAPE_pct=("WMAPE", lambda x: x.mean(skipna=True) * 100),
    SMAPE_pct=("SMAPE", lambda x: x.mean(skipna=True) * 100),
    MASE=("Error Absoluto", "mean")
).reset_index()

# Interactive heatmap for MAPE
heatmap = group_df.pivot(
    index="Categoría",
    columns="Región",
    values="MAPE_pct"
)

fig_heat = px.imshow(
    heatmap,
    text_auto=".2f",
    aspect="auto",
    color_continuous_scale="RdYlGn_r",
    title="MAPE (%) Heatmap by Category & Region"
)
st.plotly_chart(fig_heat, use_container_width=True)

# ---- WMAPE per SKU bar chart ----
st.header("Top 15 SKUs by WMAPE")
top_skus = df_full.groupby("SKU")["WMAPE"].mean().sort_values(ascending=False).head(15).reset_index()
fig_bar = px.bar(
    top_skus,
    x="SKU",
    y="WMAPE",
    title="Top 15 SKUs with Highest WMAPE",
    labels={"WMAPE": "Average WMAPE"},
    text=top_skus["WMAPE"].apply(lambda x: f"{x*100:.1f}%")
)
fig_bar.update_traces(textposition='outside')
fig_bar.update_yaxes(tickformat=".0%")
st.plotly_chart(fig_bar, use_container_width=True)

# ---- Alerts Table ----
st.header("🚨 Alerts – High WMAPE (>50%)")
alerts_df = df_full[df_full["Alerta Error Alto"]].copy()
if alerts_df.empty:
    st.success("Great! No high error alerts 🎉")
else:
    alerts_df["WMAPE (%)"] = alerts_df["WMAPE"] * 100
    show_cols = ["Fecha", "SKU", "Categoría", "Región", "Valor Real", "Pronóstico", "WMAPE (%)"]
    st.dataframe(alerts_df[show_cols].style.background_gradient(cmap="Reds"))
