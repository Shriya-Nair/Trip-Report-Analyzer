import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Trip Report Analyzer", page_icon="🚛", layout="wide")

# ── Styling ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #f5f7fa; }
    .stApp { font-family: 'Segoe UI', sans-serif; }
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 20px 24px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        text-align: center;
    }
    .metric-number { font-size: 2.2rem; font-weight: 700; color: #1a73e8; }
    .metric-label  { font-size: 0.85rem; color: #666; margin-top: 4px; }
    h1 { color: #1a1a2e; }
    .stDataFrame { border-radius: 10px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────────────────────────
st.title("🚛 Monthly Trip Report Analyzer")
st.markdown("Upload one or more monthly trip reports to explore trips by client, plant, and destination.")
st.divider()

# ── File Upload ───────────────────────────────────────────────────────────────
uploaded_files = st.file_uploader(
    "Upload Trip Report(s) (.xlsx)",
    type=["xlsx"],
    accept_multiple_files=True,
    help="You can upload multiple monthly reports at once."
)

REQUIRED_COLS = {"Client", "Destination", "Start Date", "Trip No"}


@st.cache_data
def load_files(files_data: list[tuple]) -> pd.DataFrame:
    frames = []
    for name, data in files_data:
        try:
            df = pd.read_excel(BytesIO(data), sheet_name=0)
            missing = REQUIRED_COLS - set(df.columns)
            if missing:
                st.warning(f"⚠️ **{name}** is missing columns: {missing}. Skipping.")
                continue
            
            # Check for Source column (can be named Source, Source Place, or Plant)
            source_col = None
            for col in ["Source", "Source Place", "Plant", "Origin", "From"]:
                if col in df.columns:
                    source_col = col
                    break
            
            if source_col:
                df["Plant"] = df[source_col].fillna("Unknown")
            else:
                df["Plant"] = "All Plants"
                st.info(f"📌 **{name}** doesn't have a Source/Plant column. Using 'All Plants' as default.")
            
            df["_source_file"] = name
            frames.append(df)
        except Exception as e:
            st.error(f"Could not read **{name}**: {e}")
    
    if not frames:
        return pd.DataFrame()
    combined = pd.concat(frames, ignore_index=True)

    # Parse dates
    combined["Start Date"] = pd.to_datetime(
        combined["Start Date"], dayfirst=True, errors="coerce"
    )
    combined["Month"] = combined["Start Date"].dt.to_period("M").astype(str)
    return combined


# ── Main Logic ────────────────────────────────────────────────────────────────
if uploaded_files:
    files_data = [(f.name, f.read()) for f in uploaded_files]
    df = load_files(files_data)

    if df.empty:
        st.error("No valid data could be loaded. Please check your files.")
        st.stop()

    st.success(f"✅ Loaded **{len(df):,}** trip records from **{len(files_data)}** file(s).")

    # ── Filters row ──────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

    with col1:
        clients = sorted(df["Client"].dropna().unique().tolist())
        selected_client = st.selectbox("🏢 Select Client", clients)
    
    # Filter plants based on selected client
    client_plants = df[df["Client"] == selected_client]["Plant"].dropna().unique().tolist()
    client_plants = sorted(client_plants)
    plant_options = ["All Plants"] + client_plants
    
    with col2:
        selected_plant = st.selectbox("🏭 Select Plant/Source", plant_options)

    months = sorted(df["Month"].dropna().unique().tolist(), reverse=True)
    month_options = ["All Months"] + months

    with col3:
        selected_month = st.selectbox("📅 Select Month", month_options)

    with col4:
        trip_types = ["All Types"] + sorted(df["Trip Type"].dropna().unique().tolist()) if "Trip Type" in df.columns else ["All Types"]
        selected_type = st.selectbox("🔄 Trip Type", trip_types)

    st.divider()

    # ── Filter data ──────────────────────────────────────────────────────────
    filtered = df[df["Client"] == selected_client].copy()
    
    if selected_plant != "All Plants":
        filtered = filtered[filtered["Plant"] == selected_plant]
    
    if selected_month != "All Months":
        filtered = filtered[filtered["Month"] == selected_month]
    
    if selected_type != "All Types" and "Trip Type" in filtered.columns:
        filtered = filtered[filtered["Trip Type"] == selected_type]

    # ── KPI Cards ────────────────────────────────────────────────────────────
    total_trips     = len(filtered)
    unique_dest     = filtered["Destination"].nunique()
    unique_plants   = filtered["Plant"].nunique()
    unique_months   = filtered["Month"].nunique()

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-number">{total_trips:,}</div>
            <div class="metric-label">Total Trips</div></div>""", unsafe_allow_html=True)
    with k2:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-number">{unique_dest}</div>
            <div class="metric-label">Unique Destinations</div></div>""", unsafe_allow_html=True)
    with k3:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-number">{unique_plants}</div>
            <div class="metric-label">Plants/Sources</div></div>""", unsafe_allow_html=True)
    with k4:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-number">{unique_months}</div>
            <div class="metric-label">Months Covered</div></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Destination Summary Table ─────────────────────────────────────────────
    st.subheader(f"📍 Trips to Each Destination — {selected_client}")
    if selected_plant != "All Plants":
        st.caption(f"🏭 Filtered by Plant: **{selected_plant}**")

    if filtered.empty:
        st.info("No trips found for the selected filters.")
    else:
        # Add plant breakdown in destination summary
        dest_summary = (
            filtered.groupby("Destination")
            .agg(
                Total_Trips=("Trip No", "count"),
                Plants=("Plant", lambda x: x.nunique()),
                **( {"Loaded_Trips": ("Trip Type", lambda x: (x == "Loaded").sum()),
                     "Empty_Trips":  ("Trip Type", lambda x: (x == "Empty").sum())}
                    if "Trip Type" in filtered.columns else {} )
            )
            .reset_index()
            .sort_values("Total_Trips", ascending=False)
            .rename(columns={"Destination": "Destination", "Total_Trips": "Total Trips", "Plants": "Plants Used"})
        )
        if "Loaded_Trips" in dest_summary.columns:
            dest_summary = dest_summary.rename(columns={"Loaded_Trips": "Loaded Trips", "Empty_Trips": "Empty Trips"})

        # Show bar chart and table
        chart_col, table_col = st.columns([1, 1])
        with chart_col:
            st.bar_chart(dest_summary.set_index("Destination")["Total Trips"], height=400)
        with table_col:
            st.dataframe(
                dest_summary,
                use_container_width=True,
                height=400,
                hide_index=True,
            )

        # ── Plant breakdown section ───────────────────────────────────────────
        if selected_plant == "All Plants" and unique_plants > 1:
            st.divider()
            st.subheader("🏭 Trip Distribution by Plant")
            
            plant_summary = (
                filtered.groupby("Plant")
                .agg(
                    Total_Trips=("Trip No", "count"),
                    Unique_Destinations=("Destination", "nunique")
                )
                .reset_index()
                .sort_values("Total_Trips", ascending=False)
            )
            
            col_pie, col_plant_table = st.columns([1, 1])
            with col_pie:
                st.bar_chart(plant_summary.set_index("Plant")["Total_Trips"], height=300)
            with col_plant_table:
                st.dataframe(
                    plant_summary,
                    use_container_width=True,
                    height=300,
                    hide_index=True,
                )

        # ── Download button ───────────────────────────────────────────────────
        st.divider()
        export_buf = BytesIO()
        with pd.ExcelWriter(export_buf, engine="openpyxl") as writer:
            dest_summary.to_excel(writer, sheet_name="Destination Summary", index=False)
            filtered.to_excel(writer, sheet_name="Raw Trips", index=False)
            
            # Add plant summary sheet if multiple plants
            if selected_plant == "All Plants" and unique_plants > 1:
                plant_summary.to_excel(writer, sheet_name="Plant Summary", index=False)
            
        export_buf.seek(0)

        plant_label = selected_plant.replace(" ", "_") if selected_plant != "All Plants" else "All_Plants"
        month_label = selected_month.replace(" ", "_") if selected_month != "All Months" else "All_Months"
        st.download_button(
            label="⬇️ Download Summary as Excel",
            data=export_buf,
            file_name=f"{selected_client}_{plant_label}_{month_label}_trip_summary.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        # ── Monthly trend (if All Months selected) ────────────────────────────
        if selected_month == "All Months" and unique_months > 1:
            st.divider()
            st.subheader("📈 Monthly Trip Trend")
            monthly = (
                filtered.groupby("Month")["Trip No"]
                .count()
                .reset_index()
                .rename(columns={"Trip No": "Trips"})
                .sort_values("Month")
            )
            st.line_chart(monthly.set_index("Month")["Trips"])
            
            # Optional: Plant-wise monthly trend
            if selected_plant == "All Plants" and unique_plants > 1:
                st.subheader("🏭 Monthly Trend by Plant")
                plant_monthly = (
                    filtered.groupby(["Month", "Plant"])["Trip No"]
                    .count()
                    .reset_index()
                    .rename(columns={"Trip No": "Trips"})
                    .sort_values("Month")
                )
                # Pivot for better visualization
                pivot_data = plant_monthly.pivot(index="Month", columns="Plant", values="Trips").fillna(0)
                st.line_chart(pivot_data)

else:
    # ── Empty state ───────────────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center; padding: 60px 20px; color: #888;">
        <div style="font-size:4rem;">📂</div>
        <h3 style="color:#555;">No file uploaded yet</h3>
        <p>Upload your monthly trip report(s) above to get started.</p>
        <p style="font-size:0.85rem; margin-top:10px;">Required columns: <code>Client</code>, <code>Destination</code>, <code>Start Date</code>, <code>Trip No</code><br>
        Optional: <code>Source</code>, <code>Source Place</code>, or <code>Plant</code> for plant-level filtering</p>
    </div>
    """, unsafe_allow_html=True)
