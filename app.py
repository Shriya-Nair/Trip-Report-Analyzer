import streamlit as st
import pandas as pd
from io import BytesIO
import plotly.express as px

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
        transition: transform 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.12);
    }
    .metric-number { font-size: 2.2rem; font-weight: 700; color: #1a73e8; }
    .metric-label  { font-size: 0.85rem; color: #666; margin-top: 4px; }
    h1 { color: #1a1a2e; }
    .stDataFrame { border-radius: 10px; overflow: hidden; }
    div[data-testid="stModal"] {
        background-color: rgba(0,0,0,0.5);
    }
    .stButton button {
        background: linear-gradient(90deg, #1a73e8, #0d47a1);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.3s;
    }
    .stButton button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(26,115,232,0.3);
    }
</style>
""", unsafe_allow_html=True)

# ── Drill-Down Modal Component ───────────────────────────────────────────────
@st.dialog("📋 Trip Details", width="large")
def show_trip_details(destination, trips_df):
    """
    Display detailed trip information in a modal dialog
    """
    st.markdown(f"### 🚛 Trips to **{destination}**")
    st.markdown(f"**Total Trips:** {len(trips_df)}")
    
    # Display key metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Trips", len(trips_df))
    with col2:
        if "Trip Type" in trips_df.columns:
            loaded = len(trips_df[trips_df["Trip Type"] == "Loaded"])
            st.metric("Loaded Trips", loaded)
    with col3:
        if "Plant" in trips_df.columns:
            plants = trips_df["Plant"].nunique()
            st.metric("Plants Used", plants)
    
    st.divider()
    
    # Show detailed table
    st.subheader("📊 Detailed Trip List")
    
    # Select columns to display
    display_cols = ["Trip No", "Start Date", "Trip Type", "Client", "Plant", "Source File"]
    available_cols = [col for col in display_cols if col in trips_df.columns]
    
    st.dataframe(
        trips_df[available_cols],
        use_container_width=True,
        height=400,
        hide_index=True,
        column_config={
            "Trip No": "Trip Number",
            "Start Date": st.column_config.DateColumn("Date"),
            "Trip Type": st.column_config.TextColumn("Type"),
            "Client": st.column_config.TextColumn("Client"),
            "Plant": st.column_config.TextColumn("Source Plant"),
            "Source File": st.column_config.TextColumn("Report Source")
        }
    )
    
    # Download button for this specific destination
    csv = trips_df[available_cols].to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download this destination's trips (CSV)",
        data=csv,
        file_name=f"trips_to_{destination}.csv",
        mime="text/csv",
    )

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

REQUIRED_COLS = {"Client", "Destination", "Start Date", "Trip No", "Trip Type"}

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
            
            # Handle empty trips: assign "EMPTY TRIP - NO CLIENT" as client for trips with no client
            df.loc[(df["Trip Type"].str.lower() == "empty") & (df["Client"].isna()), "Client"] = "EMPTY TRIP - NO CLIENT"
            df.loc[(df["Trip Type"].str.lower() == "empty") & (df["Client"] == ""), "Client"] = "EMPTY TRIP - NO CLIENT"
            
            # Check for Source column
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
            df["Source File"] = name  # For display
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
    
    # Standardize Trip Type
    combined["Trip Type"] = combined["Trip Type"].str.title()
    
    return combined

# ── Main Logic ────────────────────────────────────────────────────────────────
if uploaded_files:
    files_data = [(f.name, f.read()) for f in uploaded_files]
    df = load_files(files_data)

    if df.empty:
        st.error("No valid data could be loaded. Please check your files.")
        st.stop()

    # Show trip type distribution
    col1, col2, col3 = st.columns(3)
    total_trips_all = len(df)
    loaded_trips_all = len(df[df["Trip Type"] == "Loaded"])
    empty_trips_all = len(df[df["Trip Type"] == "Empty"])
    
    with col1:
        st.metric("Total Trips (All)", f"{total_trips_all:,}")
    with col2:
        st.metric("Loaded Trips", f"{loaded_trips_all:,}", 
                  delta=f"{(loaded_trips_all/total_trips_all*100):.1f}%" if total_trips_all > 0 else "0%")
    with col3:
        st.metric("Empty Trips", f"{empty_trips_all:,}",
                  delta=f"{(empty_trips_all/total_trips_all*100):.1f}%" if total_trips_all > 0 else "0%")
    
    st.success(f"✅ Loaded **{len(df):,}** trip records from **{len(files_data)}** file(s).")
    st.info("💡 **Tip:** Click on any destination in the table to see detailed trip information!")

    # ── Filters ─────────────────────────────────────────────────────────────
    st.subheader("🔍 Filter Your Data")
    
    # Get all clients including the special empty trip client
    clients = sorted(df["Client"].dropna().unique().tolist())
    regular_clients = [c for c in clients if not c.startswith("EMPTY TRIP")]
    empty_trip_option = [c for c in clients if c.startswith("EMPTY TRIP")]
    client_options = regular_clients + (empty_trip_option if empty_trip_option else [])
    
    # Create 2 columns for filters
    col1, col2 = st.columns(2)
    
    with col1:
        selected_client = st.selectbox("🏢 Select Client", client_options)
    
    with col2:
        # Get plants for selected client
        client_plants = df[df["Client"] == selected_client]["Plant"].dropna().unique().tolist()
        client_plants = sorted(client_plants) if client_plants else ["All Plants"]
        plant_options = ["All Plants"] + client_plants
        selected_plant = st.selectbox("🏭 Select Plant/Source", plant_options)
    
    # Second row of filters
    col3, col4, col5 = st.columns(3)
    
    with col3:
        months = sorted(df["Month"].dropna().unique().tolist(), reverse=True)
        month_options = ["All Months"] + months
        selected_month = st.selectbox("📅 Select Month", month_options)
    
    with col4:
        trip_type_options = ["All Types"] + sorted(df["Trip Type"].dropna().unique().tolist())
        selected_type = st.selectbox("🔄 Trip Type", trip_type_options)
    
    with col5:
        # Add a clear filters button
        if st.button("🗑️ Clear All Filters", use_container_width=True):
            st.rerun()

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
    total_trips = len(filtered)
    loaded_trips = len(filtered[filtered["Trip Type"] == "Loaded"]) if "Trip Type" in filtered.columns else 0
    empty_trips = len(filtered[filtered["Trip Type"] == "Empty"]) if "Trip Type" in filtered.columns else 0
    unique_dest = filtered["Destination"].nunique()
    unique_plants = filtered["Plant"].nunique()
    unique_months = filtered["Month"].nunique()

    # Show different KPIs based on whether this is empty trips or regular client
    if selected_client.startswith("EMPTY TRIP"):
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-number">{total_trips:,}</div>
                <div class="metric-label">Total Empty Trips</div></div>""", unsafe_allow_html=True)
        with k2:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-number">{unique_dest}</div>
                <div class="metric-label">Unique Destinations</div></div>""", unsafe_allow_html=True)
        with k3:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-number">{unique_plants}</div>
                <div class="metric-label">Source Plants</div></div>""", unsafe_allow_html=True)
        with k4:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-number">{unique_months}</div>
                <div class="metric-label">Months Covered</div></div>""", unsafe_allow_html=True)
    else:
        k1, k2, k3, k4, k5 = st.columns(5)
        with k1:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-number">{total_trips:,}</div>
                <div class="metric-label">Total Trips</div></div>""", unsafe_allow_html=True)
        with k2:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-number">{loaded_trips}</div>
                <div class="metric-label">Loaded Trips</div></div>""", unsafe_allow_html=True)
        with k3:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-number">{empty_trips}</div>
                <div class="metric-label">Empty Trips</div></div>""", unsafe_allow_html=True)
        with k4:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-number">{unique_dest}</div>
                <div class="metric-label">Unique Destinations</div></div>""", unsafe_allow_html=True)
        with k5:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-number">{unique_plants}</div>
                <div class="metric-label">Plants/Sources</div></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Destination Summary Table with Clickable Rows ─────────────────────────
    if selected_client.startswith("EMPTY TRIP"):
        st.subheader(f"📍 Empty Trip Destinations (No Client Association)")
        st.caption("💡 **Click on any destination row** to see detailed trip information")
    else:
        st.subheader(f"📍 Trips to Each Destination — {selected_client}")
        st.caption("💡 **Click on any destination row** to see detailed trip information")
    
    if selected_plant != "All Plants":
        st.caption(f"🏭 Filtered by Plant: **{selected_plant}**")

    if filtered.empty:
        st.info("No trips found for the selected filters.")
    else:
        # Build destination summary
        agg_dict = {
            "Total_Trips": ("Trip No", "count"),
            "Plants": ("Plant", lambda x: x.nunique())
        }
        
        if "Trip Type" in filtered.columns:
            if len(filtered["Trip Type"].unique()) > 1:
                agg_dict["Loaded_Trips"] = ("Trip Type", lambda x: (x == "Loaded").sum())
                agg_dict["Empty_Trips"] = ("Trip Type", lambda x: (x == "Empty").sum())
        
        dest_summary = (
            filtered.groupby("Destination")
            .agg(**agg_dict)
            .reset_index()
            .sort_values("Total_Trips", ascending=False)
            .rename(columns={"Destination": "Destination", "Total_Trips": "Total Trips", "Plants": "Plants Used"})
        )
        
        if "Loaded_Trips" in dest_summary.columns:
            dest_summary = dest_summary.rename(columns={"Loaded_Trips": "Loaded Trips", "Empty_Trips": "Empty Trips"})

        # Create interactive chart with plotly
        fig = px.bar(
            dest_summary.head(20), 
            x="Destination", 
            y="Total Trips",
            title="Top 20 Destinations by Trip Count",
            color="Total Trips",
            color_continuous_scale="Blues",
            text="Total Trips"
        )
        fig.update_traces(textposition='outside', hovertemplate='<b>%{x}</b><br>Trips: %{y}<extra></extra>')
        fig.update_layout(
            xaxis_tickangle=-45,
            height=500,
            clickmode='event+select'
        )
        
        # Display chart and table in columns
        chart_col, table_col = st.columns([1, 1])
        
        with chart_col:
            st.plotly_chart(fig, use_container_width=True)
        
        with table_col:
            st.markdown("#### 📋 Destinations Summary")
            st.info("💡 **Click the 🔍 button next to any destination** to see detailed trip information!")
            
            # Display table with clickable buttons
            for idx, row in dest_summary.iterrows():
                destination = row['Destination']
                col1, col2, col3, col4 = st.columns([0.5, 0.2, 0.2, 0.1])
                with col1:
                    st.write(f"**{destination}**")
                with col2:
                    st.write(f"{row['Total Trips']} trips")
                with col3:
                    if "Loaded Trips" in row:
                        st.write(f"🟢 {row['Loaded Trips']} / 🔴 {row['Empty Trips']}")
                with col4:
                    # Create a button for each destination
                    if st.button("🔍", key=f"drill_{destination}_{idx}", help=f"View details for {destination}"):
                        # Get trips for this destination
                        destination_trips = filtered[filtered["Destination"] == destination].copy()
                        show_trip_details(destination, destination_trips)

        # ── Empty Trip Analysis (when viewing empty trips) ─────────────────────
        if selected_client.startswith("EMPTY TRIP"):
            st.divider()
            st.subheader("🔄 Empty Trip Movement Analysis")
            
            empty_movement = (
                filtered.groupby(["Plant", "Destination"])
                .size()
                .reset_index(name="Number of Empty Trips")
                .sort_values("Number of Empty Trips", ascending=False)
                .head(20)
            )
            
            st.markdown("**Click on any row in the table below to see details**")
            movement_event = st.dataframe(
                empty_movement,
                use_container_width=True,
                hide_index=True,
                selection_mode="single-row",
                on_select="rerun",
                column_config={
                    "Plant": "Source Plant",
                    "Destination": "Destination",
                    "Number of Empty Trips": "Trip Count"
                }
            )
            
            if hasattr(movement_event, 'selection') and movement_event.selection and hasattr(movement_event.selection, 'rows') and movement_event.selection.rows:
                selected_row_idx = movement_event.selection.rows[0]
                selected_route = empty_movement.iloc[selected_row_idx]
                route_trips = filtered[
                    (filtered["Plant"] == selected_route["Plant"]) & 
                    (filtered["Destination"] == selected_route["Destination"])
                ].copy()
                show_trip_details(f"{selected_route['Plant']} → {selected_route['Destination']}", route_trips)

        # ── Download button ───────────────────────────────────────────────────
        st.divider()
        export_buf = BytesIO()
        with pd.ExcelWriter(export_buf, engine="openpyxl") as writer:
            dest_summary.to_excel(writer, sheet_name="Destination Summary", index=False)
            filtered.to_excel(writer, sheet_name="Raw Trips", index=False)
            
        export_buf.seek(0)

        plant_label = selected_plant.replace(" ", "_") if selected_plant != "All Plants" else "All_Plants"
        month_label = selected_month.replace(" ", "_") if selected_month != "All Months" else "All_Months"
        client_label = selected_client.replace(" ", "_").replace("-", "_")[:50]
        st.download_button(
            label="⬇️ Download Summary as Excel",
            data=export_buf,
            file_name=f"{client_label}_{plant_label}_{month_label}_trip_summary.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

else:
    # ── Empty state ───────────────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center; padding: 60px 20px; color: #888;">
        <div style="font-size:4rem;">📂</div>
        <h3 style="color:#555;">No file uploaded yet</h3>
        <p>Upload your monthly trip report(s) above to get started.</p>
        <p style="font-size:0.85rem; margin-top:10px;"><strong>Required columns:</strong> <code>Client</code>, <code>Destination</code>, <code>Start Date</code>, <code>Trip No</code>, <code>Trip Type</code><br>
        <strong>Features:</strong><br>
        • 🔍 <strong>Drill-down modal</strong> - Click on any destination to see detailed trip information<br>
        • 📊 <strong>Interactive charts</strong> - Click on bars to explore data<br>
        • 🎯 <strong>Clickable tables</strong> - Select rows to view detailed trip lists<br>
        <strong>Optional:</strong> <code>Source</code>, <code>Source Place</code>, or <code>Plant</code> for plant-level filtering</p>
    </div>
    """, unsafe_allow_html=True)
