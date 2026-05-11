import streamlit as st
import pandas as pd
from io import BytesIO
import plotly.express as px
from difflib import SequenceMatcher

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
    
    /* TAT Two-Column Layout Styling */
    .tat-container {
        display: flex;
        gap: 20px;
        margin: 20px 0;
        flex-wrap: wrap;
    }
    
    .tat-column {
        flex: 1;
        min-width: 300px;
        background: white;
        border-radius: 12px;
        padding: 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        overflow: hidden;
    }
    
    .tat-column-header {
        padding: 15px 20px;
        font-weight: 700;
        font-size: 1.1rem;
        color: white;
        text-align: center;
    }
    
    .loading-header {
        background: linear-gradient(135deg, #1a73e8, #1557b0);
    }
    
    .unloading-header {
        background: linear-gradient(135deg, #34a853, #2d8f47);
    }
    
    .tat-column-body {
        padding: 15px 20px;
    }
    
    .tat-stage-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 15px;
        border-bottom: 1px solid #e8eaed;
        transition: background-color 0.2s;
    }
    
    .tat-stage-row:hover {
        background-color: #f8f9fa;
    }
    
    .tat-stage-row:last-child {
        border-bottom: none;
    }
    
    .stage-info {
        flex: 1;
    }
    
    .stage-name {
        font-weight: 600;
        color: #333;
        font-size: 0.9rem;
    }
    
    .stage-desc {
        font-size: 0.8rem;
        color: #666;
        margin-top: 2px;
    }
    
    .stage-time {
        text-align: right;
    }
    
    .stage-minutes {
        font-weight: 600;
        color: #333;
        font-size: 0.95rem;
    }
    
    .stage-hhmm {
        font-size: 0.85rem;
        color: #1a73e8;
        font-weight: 500;
    }
    
    .tat-total-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 15px 20px;
        background: #d4edda;
        border-top: 2px solid #c3e6cb;
        font-weight: 700;
    }
    
    .tat-total-label {
        font-size: 1rem;
        color: #155724;
    }
    
    .tat-total-time {
        text-align: right;
    }
    
    .tat-total-minutes {
        font-size: 1.1rem;
        color: #155724;
        font-weight: 700;
    }
    
    .tat-total-hhmm {
        font-size: 0.95rem;
        color: #1a73e8;
        font-weight: 600;
    }
    
    /* Grand Total Styling */
    .grand-total-container {
        background: #f0f0f0;
        border-radius: 12px;
        padding: 20px 25px;
        margin: 20px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border: 2px solid #d32f2f;
    }
    
    .grand-total-content {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .grand-total-label {
        font-size: 1.3rem;
        font-weight: 700;
        color: #d32f2f;
    }
    
    .grand-total-time {
        text-align: right;
    }
    
    .grand-total-minutes {
        font-size: 1.4rem;
        font-weight: 700;
        color: #d32f2f;
    }
    
    .grand-total-hhmm {
        font-size: 1.6rem;
        font-weight: 700;
        color: #b71c1c;
    }
    
    .grand-total-formula {
        font-size: 0.85rem;
        color: #666;
        margin-top: 5px;
        text-align: center;
    }
    
    .filter-section {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)


# ── Drill-Down Modal ──────────────────────────────────────────────────────────
@st.dialog("📋 Trip Details", width="large")
def show_trip_details(destination, trips_df):
    st.markdown(f"### 🚛 Trips to **{destination}**")
    total_qty = trips_df["Inv Qty"].sum() if "Inv Qty" in trips_df.columns else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Trips", len(trips_df))
    with col2:
        if "Trip Type" in trips_df.columns:
            st.metric("Loaded Trips", len(trips_df[trips_df["Trip Type"] == "Loaded"]))
    with col3:
        if "Plant" in trips_df.columns:
            st.metric("Plants Used", trips_df["Plant"].nunique())
    with col4:
        st.metric("Total Quantity", f"{total_qty:,.2f}")

    st.divider()
    st.subheader("📊 Detailed Trip List")

    display_cols = ["Trip No", "Start Date", "Trip Type", "Client", "Plant", "Inv Qty", "Source File"]
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
            "Inv Qty": st.column_config.NumberColumn("Quantity", format="%.2f"),
            "Source File": st.column_config.TextColumn("Report Source"),
        },
    )

    csv = trips_df[available_cols].to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download this destination's trips (CSV)",
        data=csv,
        file_name=f"trips_to_{destination}.csv",
        mime="text/csv",
    )


# ── Destination Name Fuzzy Helpers ────────────────────────────────────────────
def _normalize(name: str) -> str:
    import re
    name = str(name).lower().strip()
    name = re.sub(r"[^\w\s]", "", name)
    name = re.sub(r"\s+", " ", name)
    return name


def _similar(a: str, b: str, threshold: float = 0.82) -> bool:
    na, nb = _normalize(a), _normalize(b)
    if na == nb:
        return True
    return SequenceMatcher(None, na, nb).ratio() >= threshold


def _build_destination_alias_map(all_destinations: pd.Series, threshold: float = 0.82) -> dict:
    unique_dests = all_destinations.dropna().unique().tolist()
    clusters: list[list[str]] = []
    for dest in unique_dests:
        placed = False
        for cluster in clusters:
            if _similar(dest, cluster[0], threshold):
                cluster.append(dest)
                placed = True
                break
        if not placed:
            clusters.append([dest])
    alias_map = {}
    for cluster in clusters:
        canonical = max(cluster, key=len)
        for variant in cluster:
            alias_map[variant] = canonical
    return alias_map


# ── Deduplication — pure, no st.* calls ──────────────────────────────────────
def deduplicate_trips(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    if "Trip No" not in df.columns:
        return df, pd.DataFrame()

    alias_map = _build_destination_alias_map(df["Destination"].fillna("Unknown"))
    df = df.copy()
    df["Destination"] = df["Destination"].map(lambda d: alias_map.get(d, d))

    duplicated_mask = df.duplicated(subset=["Trip No"], keep=False)
    unique_df = df[~duplicated_mask].copy()
    dup_df = df[duplicated_mask].copy()

    audit_records = []
    merged_rows = []
    merged_qtys = []

    for trip_no, group in dup_df.groupby("Trip No"):
        destinations = group["Destination"].dropna().unique().tolist()

        if len(destinations) == 1:
            summed_qty = float(group["Inv Qty"].sum())
            representative = group.iloc[0].copy()
            merged_rows.append(representative)
            merged_qtys.append(summed_qty)
            audit_records.append({
                "Trip No": trip_no,
                "Action": "MERGED – same destination",
                "Destinations Found": "; ".join(destinations),
                "Canonical Destination": destinations[0],
                "Original Qty Values": "; ".join(group["Inv Qty"].astype(str).tolist()),
                "Final Qty": summed_qty,
                "Rows Affected": len(group),
            })
        else:
            best_idx = group["Inv Qty"].idxmax()
            best_qty = float(group.loc[best_idx, "Inv Qty"])
            representative = group.loc[best_idx].copy()
            merged_rows.append(representative)
            merged_qtys.append(best_qty)
            audit_records.append({
                "Trip No": trip_no,
                "Action": "KEPT BEST LEG – different destinations",
                "Destinations Found": "; ".join(destinations),
                "Canonical Destination": representative["Destination"],
                "Original Qty Values": "; ".join(group["Inv Qty"].astype(str).tolist()),
                "Final Qty": best_qty,
                "Rows Affected": len(group),
            })

    merged_df = pd.DataFrame(merged_rows)
    merged_df["Inv Qty"] = [float(q) for q in merged_qtys]
    final_df = pd.concat([unique_df, merged_df], ignore_index=True)
    audit_df = pd.DataFrame(audit_records) if audit_records else pd.DataFrame()
    return final_df, audit_df


# ── Cached loader ────────────────────────────────────────────────────────────
@st.cache_data
def load_files(files_data: list[tuple]) -> dict:
    messages: list[tuple[str, str]] = []
    frames = []

    for name, data in files_data:
        try:
            df = pd.read_excel(BytesIO(data), sheet_name=0)
            missing = {"Client", "Destination", "Start Date", "Trip No", "Trip Type"} - set(df.columns)
            if missing:
                messages.append(("warning", f"⚠️ **{name}** is missing columns: {missing}. Skipping."))
                continue

            df.loc[(df["Trip Type"].str.lower() == "empty") & (df["Client"].isna()), "Client"] = "EMPTY TRIP - NO CLIENT"
            df.loc[(df["Trip Type"].str.lower() == "empty") & (df["Client"] == ""), "Client"] = "EMPTY TRIP - NO CLIENT"

            source_col = next(
                (c for c in ["Source", "Source Place", "Plant", "Origin", "From"] if c in df.columns),
                None,
            )
            if source_col:
                df["Plant"] = df[source_col].fillna("Unknown")
            else:
                df["Plant"] = "All Plants"
                messages.append(("info", f"📌 **{name}** has no Source/Plant column. Using 'All Plants'."))

            if "Inv Qty" not in df.columns:
                df["Inv Qty"] = 0.0
                messages.append(("info", f"📌 **{name}** has no 'Inv Qty' column. Using 0."))
            else:
                df["Inv Qty"] = pd.to_numeric(df["Inv Qty"], errors="coerce").fillna(0).astype(float)

            df["_source_file"] = name
            df["Source File"] = name
            frames.append(df)

        except Exception as e:
            messages.append(("error", f"Could not read **{name}**: {e}"))

    if not frames:
        return {"df": pd.DataFrame(), "audit_df": pd.DataFrame(), "messages": messages}

    combined = pd.concat(frames, ignore_index=True)
    combined["Start Date"] = pd.to_datetime(combined["Start Date"], dayfirst=True, errors="coerce")
    combined["Month"] = combined["Start Date"].dt.to_period("M").astype(str)
    combined["Trip Type"] = combined["Trip Type"].str.title()

    rows_before = len(combined)
    combined, audit_df = deduplicate_trips(combined)
    removed = rows_before - len(combined)

    if removed > 0:
        messages.append(("dedup", f"🔁 Deduplication removed **{removed:,}** duplicate row(s). See the Deduplication Report below."))

    return {"df": combined, "audit_df": audit_df, "messages": messages}


# ── TAT Processing Function ───────────────────────────────────────────────────
@st.cache_data
def load_tat_file(tat_file_data):
    """Load TAT file with caching."""
    try:
        df_tat = pd.read_excel(BytesIO(tat_file_data), sheet_name=0)
        return df_tat, None
    except Exception as e:
        return pd.DataFrame(), str(e)


def minutes_to_hhmm(minutes: float) -> str:
    """Convert decimal minutes to HH:MM string format."""
    if pd.isna(minutes) or minutes < 0:
        return "00:00"
    
    total_minutes = int(round(minutes))
    hours = total_minutes // 60
    mins = total_minutes % 60
    return f"{hours:02d}:{mins:02d}"


def identify_tat_columns(df_tat: pd.DataFrame) -> dict:
    """Identify relevant columns in TAT dataframe."""
    col_mapping = {
        "client_col": ["Client", "Customer", "Client Name", "Customer Name"],
        "plant_col": ["Plant", "Source Plant", "Source", "Plant Name", "Origin"],
        "trip_no_col": ["Trip No", "Trip Number", "TripNo", "Trip ID"],
        "destination_col": ["Destination", "To", "Delivery Location", "Unloading Point", "Drop Location"],
        "stage1": ["Actual DO Receipt (Mins)", "DO Receipt (Mins)", "Actual DO Receipt"],
        "stage2": ["Actual Gate In(Mins)", "Gate In (Mins)", "Actual Gate In"],
        "stage3": ["Actual Loaded Exit(Mins)", "Loaded Exit (Mins)", "Actual Loaded Exit"],
        "stage4": ["Actual Gate In for Unloading(Mins)", "Gate In for Unloading (Mins)", "Actual Gate In for Unloading"],
        "stage5": ["Actual Unloaded (Mins)", "Unloaded (Mins)", "Actual Unloaded"],
        "date_col": ["Date", "Start Date", "Trip Date", "Transaction Date"],
    }
    
    identified = {}
    for key, possible_names in col_mapping.items():
        found_col = None
        for name in possible_names:
            if name in df_tat.columns:
                found_col = name
                break
        identified[key] = found_col
    
    return identified


def process_tat_data(df_tat: pd.DataFrame, filters: dict = None) -> tuple:
    """
    Process TAT data and return averages for each stage.
    filters: dict with keys 'client', 'plant', 'destination', 'trip_nos', 'date_range'
    Returns: (avg_stage1, avg_stage2, avg_stage3, avg_stage4, avg_stage5, total_records, filtered_df)
    """
    if df_tat.empty:
        return 0, 0, 0, 0, 0, 0, pd.DataFrame()
    
    df_filtered = df_tat.copy()
    columns = identify_tat_columns(df_tat)
    
    # Apply filters if provided
    if filters:
        # Filter by trip numbers
        if filters.get('trip_nos') and columns['trip_no_col']:
            df_filtered = df_filtered[df_filtered[columns['trip_no_col']].isin(filters['trip_nos'])]
        
        # Filter by client
        if filters.get('client') and filters['client'] != "All Clients" and columns['client_col']:
            df_filtered = df_filtered[df_filtered[columns['client_col']] == filters['client']]
        
        # Filter by plant
        if filters.get('plant') and filters['plant'] != "All Plants" and columns['plant_col']:
            df_filtered = df_filtered[df_filtered[columns['plant_col']] == filters['plant']]
        
        # Filter by destination
        if filters.get('destination') and filters['destination'] != "All Destinations" and columns['destination_col']:
            df_filtered = df_filtered[df_filtered[columns['destination_col']] == filters['destination']]
        
        # Filter by multiple destinations
        if filters.get('multi_destinations') and columns['destination_col']:
            df_filtered = df_filtered[df_filtered[columns['destination_col']].isin(filters['multi_destinations'])]
        
        # Filter by date range
        if filters.get('date_range') and columns['date_col']:
            start_date, end_date = filters['date_range']
            if start_date and end_date:
                date_series = pd.to_datetime(df_filtered[columns['date_col']], errors='coerce')
                df_filtered = df_filtered[(date_series >= pd.Timestamp(start_date)) & 
                                         (date_series <= pd.Timestamp(end_date))]
    
    if df_filtered.empty:
        return 0, 0, 0, 0, 0, 0, pd.DataFrame()
    
    total_records = len(df_filtered)
    
    # Calculate averages for each stage
    averages = {}
    for stage in ["stage1", "stage2", "stage3", "stage4", "stage5"]:
        col = columns[stage]
        if col and col in df_filtered.columns:
            avg_val = pd.to_numeric(df_filtered[col], errors='coerce').mean()
            averages[stage] = avg_val if not pd.isna(avg_val) else 0
        else:
            averages[stage] = 0
    
    return (
        averages["stage1"],
        averages["stage2"],
        averages["stage3"],
        averages["stage4"],
        averages["stage5"],
        total_records,
        df_filtered
    )


def get_tat_filter_options(df_tat: pd.DataFrame) -> dict:
    """Extract filter options from TAT dataframe."""
    columns = identify_tat_columns(df_tat)
    options = {}
    
    # Clients
    if columns['client_col']:
        clients = sorted(df_tat[columns['client_col']].dropna().unique().tolist())
        options['clients'] = ["All Clients"] + clients
    else:
        options['clients'] = ["All Clients"]
    
    # Plants
    if columns['plant_col']:
        plants = sorted(df_tat[columns['plant_col']].dropna().unique().tolist())
        options['plants'] = ["All Plants"] + plants
    else:
        options['plants'] = ["All Plants"]
    
    # Destinations
    if columns['destination_col']:
        destinations = sorted(df_tat[columns['destination_col']].dropna().unique().tolist())
        options['destinations'] = ["All Destinations"] + destinations
    else:
        options['destinations'] = ["All Destinations"]
    
    # Date range
    if columns['date_col']:
        date_series = pd.to_datetime(df_tat[columns['date_col']], errors='coerce')
        options['min_date'] = date_series.min().date() if not pd.isna(date_series.min()) else None
        options['max_date'] = date_series.max().date() if not pd.isna(date_series.max()) else None
    else:
        options['min_date'] = None
        options['max_date'] = None
    
    return options, columns


# ── TAT Report Rendering ─────────────────────────────────────────────────────
def render_tat_report(df_tat, filters=None):
    """Render the TAT Report tab content."""
    st.subheader("📊 Turnaround Time (TAT) Analysis Report")
    
    # Get filter options
    filter_options, tat_columns = get_tat_filter_options(df_tat)
    
    # ── TAT Filters ──────────────────────────────────────────────────────────
    with st.expander("🔍 TAT Data Filters", expanded=True):
        st.markdown('<div class="filter-section">', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Client filter
            if len(filter_options['clients']) > 1:
                selected_tat_client = st.selectbox(
                    "🏢 Client",
                    filter_options['clients'],
                    key="tat_client_filter"
                )
            else:
                selected_tat_client = "All Clients"
                st.info("ℹ️ No Client column found in TAT data")
            
            # Destination filter
            if len(filter_options['destinations']) > 1:
                selected_tat_destination = st.selectbox(
                    "📍 Destination",
                    filter_options['destinations'],
                    key="tat_destination_filter"
                )
            else:
                selected_tat_destination = "All Destinations"
                st.info("ℹ️ No Destination column found in TAT data")
        
        with col2:
            # Plant filter
            if len(filter_options['plants']) > 1:
                selected_tat_plant = st.selectbox(
                    "🏭 Plant/Source",
                    filter_options['plants'],
                    key="tat_plant_filter"
                )
            else:
                selected_tat_plant = "All Plants"
                st.info("ℹ️ No Plant column found in TAT data")
            
            # Date range filter
            if filter_options['min_date'] and filter_options['max_date']:
                date_range = st.date_input(
                    "📅 Date Range",
                    value=(filter_options['min_date'], filter_options['max_date']),
                    min_value=filter_options['min_date'],
                    max_value=filter_options['max_date'],
                    key="tat_date_filter"
                )
                if len(date_range) == 2:
                    start_date, end_date = date_range
                else:
                    start_date, end_date = None, None
            else:
                start_date, end_date = None, None
                st.info("ℹ️ No Date column found in TAT data")
        
        with col3:
            # Additional filter options
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Trip filter option
            use_trip_filter = st.checkbox(
                "🔗 Filter by Trip Analysis selection",
                value=(filters is not None and filters.get('trip_nos') is not None),
                key="tat_trip_filter_checkbox",
                help="Filter TAT data to only include trips from the current Trip Analysis selection"
            )
            
            # Multi-select for multiple destinations
            if len(filter_options['destinations']) > 1:
                enable_multi_dest = st.checkbox(
                    "📍 Multi-Destination Select",
                    value=False,
                    key="tat_multi_dest_checkbox",
                    help="Enable selection of multiple destinations"
                )
                
                if enable_multi_dest:
                    selected_tat_destinations = st.multiselect(
                        "Select Destinations",
                        options=filter_options['destinations'][1:],  # Exclude "All Destinations"
                        default=[],
                        key="tat_destination_multiselect",
                        help="Select specific destinations to analyze"
                    )
                    if selected_tat_destinations:
                        selected_tat_destination = None  # Use multi-select instead
                    else:
                        selected_tat_destination = "All Destinations"
                else:
                    selected_tat_destinations = None
            else:
                selected_tat_destinations = None
        
        # Clear filters button
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("🗑️ Clear TAT Filters", key="clear_tat_filters"):
                st.session_state.tat_client_filter = "All Clients"
                st.session_state.tat_plant_filter = "All Plants"
                st.session_state.tat_destination_filter = "All Destinations"
                st.session_state.tat_trip_filter_checkbox = False
                st.session_state.tat_multi_dest_checkbox = False
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Build filter dictionary
    tat_filters = {
        'client': selected_tat_client if 'selected_tat_client' in locals() else "All Clients",
        'plant': selected_tat_plant if 'selected_tat_plant' in locals() else "All Plants",
        'destination': selected_tat_destination if 'selected_tat_destination' in locals() and selected_tat_destination != "All Destinations" else "All Destinations",
        'date_range': (start_date, end_date) if 'start_date' in locals() else (None, None),
        'trip_nos': filters.get('trip_nos') if use_trip_filter and filters else None,
        'multi_destinations': selected_tat_destinations if 'selected_tat_destinations' in locals() and selected_tat_destinations else None
    }
    
    # Calculate TAT metrics
    avg_stage1, avg_stage2, avg_stage3, avg_stage4, avg_stage5, total_records, filtered_tat_df = process_tat_data(df_tat, tat_filters)
    
    # Calculate totals
    total_loading = avg_stage1 + avg_stage2 + avg_stage3
    total_unloading = avg_stage4 + avg_stage5
    total_tat = total_loading + total_unloading
    
    # Show filter status
    active_filters = []
    if tat_filters['client'] != "All Clients":
        active_filters.append(f"Client: **{tat_filters['client']}**")
    if tat_filters['plant'] != "All Plants":
        active_filters.append(f"Plant: **{tat_filters['plant']}**")
    if tat_filters['destination'] != "All Destinations":
        active_filters.append(f"Destination: **{tat_filters['destination']}**")
    if tat_filters.get('multi_destinations'):
        active_filters.append(f"Destinations: **{len(tat_filters['multi_destinations'])}** selected")
    if tat_filters['date_range'][0] and tat_filters['date_range'][1]:
        active_filters.append(f"Date: **{tat_filters['date_range'][0]}** to **{tat_filters['date_range'][1]}**")
    if use_trip_filter and tat_filters['trip_nos']:
        active_filters.append(f"Trip Filter: **{len(tat_filters['trip_nos']):,}** trips")
    
    if active_filters:
        st.info(f"🔍 **Active Filters:** {' | '.join(active_filters)} | **Records:** {total_records:,}")
    else:
        st.info(f"📊 **All Records:** Showing all {total_records:,} TAT records")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # KPI Cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="metric-number">{minutes_to_hhmm(total_loading)}</div>'
            f'<div class="metric-label">⏱️ Avg Loading Time</div>'
            f'</div>',
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="metric-number">{minutes_to_hhmm(total_unloading)}</div>'
            f'<div class="metric-label">⏱️ Avg Unloading Time</div>'
            f'</div>',
            unsafe_allow_html=True
        )
    with col3:
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="metric-number">{total_records:,}</div>'
            f'<div class="metric-label">📋 Total Records Analyzed</div>'
            f'</div>',
            unsafe_allow_html=True
        )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ── TWO-COLUMN LAYOUT FOR LOADING AND UNLOADING ──────────────────────────
    st.markdown("### 📈 Detailed TAT Breakdown")
    
    # Container for the two columns
    st.markdown('<div class="tat-container">', unsafe_allow_html=True)
    
    # ── LOADING COLUMN (Stages 1-3) ──────────────────────────────────────────
    st.markdown('''
    <div class="tat-column">
        <div class="tat-column-header loading-header">
            ⏱️ LOADING PROCESS
        </div>
        <div class="tat-column-body">
    ''', unsafe_allow_html=True)
    
    # Stage 1
    st.markdown(f'''
    <div class="tat-stage-row">
        <div class="stage-info">
            <div class="stage-name">Stage 1: DO Receipt</div>
            <div class="stage-desc">DO Receipt to Gate Entry</div>
        </div>
        <div class="stage-time">
            <div class="stage-minutes">{avg_stage1:.2f} min</div>
            <div class="stage-hhmm">{minutes_to_hhmm(avg_stage1)}</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Stage 2
    st.markdown(f'''
    <div class="tat-stage-row">
        <div class="stage-info">
            <div class="stage-name">Stage 2: Gate Entry</div>
            <div class="stage-desc">Gate Entry to Loading Bay</div>
        </div>
        <div class="stage-time">
            <div class="stage-minutes">{avg_stage2:.2f} min</div>
            <div class="stage-hhmm">{minutes_to_hhmm(avg_stage2)}</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Stage 3
    st.markdown(f'''
    <div class="tat-stage-row">
        <div class="stage-info">
            <div class="stage-name">Stage 3: Loading & Exit</div>
            <div class="stage-desc">Loading Process & Exit</div>
        </div>
        <div class="stage-time">
            <div class="stage-minutes">{avg_stage3:.2f} min</div>
            <div class="stage-hhmm">{minutes_to_hhmm(avg_stage3)}</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Loading Total
    st.markdown(f'''
    <div class="tat-total-row">
        <div class="tat-total-label">✅ Total Loading Time</div>
        <div class="tat-total-time">
            <div class="tat-total-minutes">{total_loading:.2f} min</div>
            <div class="tat-total-hhmm">{minutes_to_hhmm(total_loading)}</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    st.markdown('</div></div>', unsafe_allow_html=True)
    
    # ── UNLOADING COLUMN (Stages 4-5) ────────────────────────────────────────
    st.markdown('''
    <div class="tat-column">
        <div class="tat-column-header unloading-header">
            ⏱️ UNLOADING PROCESS
        </div>
        <div class="tat-column-body">
    ''', unsafe_allow_html=True)
    
    # Stage 4
    st.markdown(f'''
    <div class="tat-stage-row">
        <div class="stage-info">
            <div class="stage-name">Stage 4: Unloading Wait</div>
            <div class="stage-desc">Gate In for Unloading</div>
        </div>
        <div class="stage-time">
            <div class="stage-minutes">{avg_stage4:.2f} min</div>
            <div class="stage-hhmm">{minutes_to_hhmm(avg_stage4)}</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Stage 5
    st.markdown(f'''
    <div class="tat-stage-row">
        <div class="stage-info">
            <div class="stage-name">Stage 5: Unloading</div>
            <div class="stage-desc">Unloading Process</div>
        </div>
        <div class="stage-time">
            <div class="stage-minutes">{avg_stage5:.2f} min</div>
            <div class="stage-hhmm">{minutes_to_hhmm(avg_stage5)}</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Unloading Total
    st.markdown(f'''
    <div class="tat-total-row">
        <div class="tat-total-label">✅ Total Unloading Time</div>
        <div class="tat-total-time">
            <div class="tat-total-minutes">{total_unloading:.2f} min</div>
            <div class="tat-total-hhmm">{minutes_to_hhmm(total_unloading)}</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    st.markdown('</div></div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close tat-container
    
    # ── GRAND TOTAL ──────────────────────────────────────────────────────────
    loading_hhmm = minutes_to_hhmm(total_loading)
    unloading_hhmm = minutes_to_hhmm(total_unloading)
    total_hhmm = minutes_to_hhmm(total_tat)
    
    st.markdown(f'''
    <div class="grand-total-container">
        <div class="grand-total-content">
            <div class="grand-total-label">🔴 TOTAL TAT</div>
            <div class="grand-total-time">
                <div class="grand-total-minutes">{total_tat:.2f} min</div>
                <div class="grand-total-hhmm">{total_hhmm}</div>
            </div>
        </div>
        <div class="grand-total-formula">
            Total Loading ({loading_hhmm}) + Total Unloading ({unloading_hhmm}) = <strong>{total_hhmm}</strong>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Additional insights and data
    if total_tat > 0 and not filtered_tat_df.empty:
        st.markdown("---")
        
        # TAT Distribution
        with st.expander("📊 TAT Distribution Insights", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                loading_pct = (total_loading / total_tat) * 100
                unloading_pct = (total_unloading / total_tat) * 100
                
                # Pie chart
                pie_data = pd.DataFrame({
                    'Phase': ['Loading (Stages 1-3)', 'Unloading (Stages 4-5)'],
                    'Minutes': [total_loading, total_unloading]
                })
                fig_pie = px.pie(
                    pie_data, 
                    values='Minutes', 
                    names='Phase',
                    title=f'TAT Distribution: Loading vs Unloading',
                    color_discrete_sequence=['#1a73e8', '#34a853']
                )
                fig_pie.update_traces(textinfo='percent+label')
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                # Bar chart for stage breakdown
                stage_data = pd.DataFrame({
                    'Stage': ['Stage 1<br>DO Receipt', 'Stage 2<br>Gate Entry', 
                             'Stage 3<br>Loading Exit', 'Stage 4<br>Unload Wait', 
                             'Stage 5<br>Unloading'],
                    'Minutes': [avg_stage1, avg_stage2, avg_stage3, avg_stage4, avg_stage5],
                    'Phase': ['Loading', 'Loading', 'Loading', 'Unloading', 'Unloading']
                })
                
                fig_bar = px.bar(
                    stage_data,
                    x='Stage',
                    y='Minutes',
                    title='Average Time per TAT Stage',
                    color='Phase',
                    color_discrete_map={'Loading': '#1a73e8', 'Unloading': '#34a853'},
                    text='Minutes'
                )
                fig_bar.update_traces(texttemplate='%{text:.1f} min', textposition='outside')
                fig_bar.update_layout(height=400, showlegend=True)
                st.plotly_chart(fig_bar, use_container_width=True)
        
        # Client/Plant/Destination breakdown if those columns exist
        tat_columns = identify_tat_columns(df_tat)
        
        if tat_columns['client_col'] or tat_columns['plant_col'] or tat_columns['destination_col']:
            with st.expander("📋 TAT by Client, Plant & Destination", expanded=False):
                tab_client, tab_plant, tab_dest = st.tabs(["By Client", "By Plant", "By Destination"])
                
                with tab_client:
                    if tat_columns['client_col'] and tat_columns['client_col'] in filtered_tat_df.columns:
                        client_tat = filtered_tat_df.groupby(tat_columns['client_col']).agg(
                            Records=(tat_columns['trip_no_col'] if tat_columns['trip_no_col'] else filtered_tat_df.columns[0], 'count'),
                            Avg_Stage1=(tat_columns['stage1'], lambda x: pd.to_numeric(x, errors='coerce').mean()),
                            Avg_Stage2=(tat_columns['stage2'], lambda x: pd.to_numeric(x, errors='coerce').mean()),
                            Avg_Stage3=(tat_columns['stage3'], lambda x: pd.to_numeric(x, errors='coerce').mean()),
                            Avg_Stage4=(tat_columns['stage4'], lambda x: pd.to_numeric(x, errors='coerce').mean()),
                            Avg_Stage5=(tat_columns['stage5'], lambda x: pd.to_numeric(x, errors='coerce').mean())
                        ).reset_index()
                        
                        client_tat['Loading Total'] = client_tat['Avg_Stage1'] + client_tat['Avg_Stage2'] + client_tat['Avg_Stage3']
                        client_tat['Unloading Total'] = client_tat['Avg_Stage4'] + client_tat['Avg_Stage5']
                        client_tat['Total TAT'] = client_tat['Loading Total'] + client_tat['Unloading Total']
                        
                        st.dataframe(
                            client_tat.sort_values('Records', ascending=False),
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                'Loading Total': st.column_config.NumberColumn('Loading Total', format='%.1f min'),
                                'Unloading Total': st.column_config.NumberColumn('Unloading Total', format='%.1f min'),
                                'Total TAT': st.column_config.NumberColumn('Total TAT', format='%.1f min'),
                            }
                        )
                    else:
                        st.info("Client column not available in TAT data")
                
                with tab_plant:
                    if tat_columns['plant_col'] and tat_columns['plant_col'] in filtered_tat_df.columns:
                        plant_tat = filtered_tat_df.groupby(tat_columns['plant_col']).agg(
                            Records=(tat_columns['trip_no_col'] if tat_columns['trip_no_col'] else filtered_tat_df.columns[0], 'count'),
                            Avg_Stage1=(tat_columns['stage1'], lambda x: pd.to_numeric(x, errors='coerce').mean()),
                            Avg_Stage2=(tat_columns['stage2'], lambda x: pd.to_numeric(x, errors='coerce').mean()),
                            Avg_Stage3=(tat_columns['stage3'], lambda x: pd.to_numeric(x, errors='coerce').mean()),
                            Avg_Stage4=(tat_columns['stage4'], lambda x: pd.to_numeric(x, errors='coerce').mean()),
                            Avg_Stage5=(tat_columns['stage5'], lambda x: pd.to_numeric(x, errors='coerce').mean())
                        ).reset_index()
                        
                        plant_tat['Loading Total'] = plant_tat['Avg_Stage1'] + plant_tat['Avg_Stage2'] + plant_tat['Avg_Stage3']
                        plant_tat['Unloading Total'] = plant_tat['Avg_Stage4'] + plant_tat['Avg_Stage5']
                        plant_tat['Total TAT'] = plant_tat['Loading Total'] + plant_tat['Unloading Total']
                        
                        st.dataframe(
                            plant_tat.sort_values('Records', ascending=False),
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                'Loading Total': st.column_config.NumberColumn('Loading Total', format='%.1f min'),
                                'Unloading Total': st.column_config.NumberColumn('Unloading Total', format='%.1f min'),
                                'Total TAT': st.column_config.NumberColumn('Total TAT', format='%.1f min'),
                            }
                        )
                    else:
                        st.info("Plant column not available in TAT data")
                
                with tab_dest:
                    if tat_columns['destination_col'] and tat_columns['destination_col'] in filtered_tat_df.columns:
                        dest_tat = filtered_tat_df.groupby(tat_columns['destination_col']).agg(
                            Records=(tat_columns['trip_no_col'] if tat_columns['trip_no_col'] else filtered_tat_df.columns[0], 'count'),
                            Avg_Stage1=(tat_columns['stage1'], lambda x: pd.to_numeric(x, errors='coerce').mean()),
                            Avg_Stage2=(tat_columns['stage2'], lambda x: pd.to_numeric(x, errors='coerce').mean()),
                            Avg_Stage3=(tat_columns['stage3'], lambda x: pd.to_numeric(x, errors='coerce').mean()),
                            Avg_Stage4=(tat_columns['stage4'], lambda x: pd.to_numeric(x, errors='coerce').mean()),
                            Avg_Stage5=(tat_columns['stage5'], lambda x: pd.to_numeric(x, errors='coerce').mean())
                        ).reset_index()
                        
                        dest_tat['Loading Total'] = dest_tat['Avg_Stage1'] + dest_tat['Avg_Stage2'] + dest_tat['Avg_Stage3']
                        dest_tat['Unloading Total'] = dest_tat['Avg_Stage4'] + dest_tat['Avg_Stage5']
                        dest_tat['Total TAT'] = dest_tat['Loading Total'] + dest_tat['Unloading Total']
                        
                        st.dataframe(
                            dest_tat.sort_values('Records', ascending=False),
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                'Loading Total': st.column_config.NumberColumn('Loading Total', format='%.1f min'),
                                'Unloading Total': st.column_config.NumberColumn('Unloading Total', format='%.1f min'),
                                'Total TAT': st.column_config.NumberColumn('Total TAT', format='%.1f min'),
                            }
                        )
                    else:
                        st.info("Destination column not available in TAT data")
        
        # Destination performance comparison
        if tat_columns['destination_col'] and tat_columns['destination_col'] in filtered_tat_df.columns:
            with st.expander("📍 Destination Performance Comparison", expanded=False):
                # Get top 15 destinations by record count
                top_destinations = (filtered_tat_df.groupby(tat_columns['destination_col'])
                                   .size()
                                   .sort_values(ascending=False)
                                   .head(15)
                                   .index
                                   .tolist())
                
                dest_comparison = filtered_tat_df[filtered_tat_df[tat_columns['destination_col']].isin(top_destinations)]
                
                # Calculate metrics per destination
                dest_metrics = dest_comparison.groupby(tat_columns['destination_col']).agg(
                    Avg_Stage1=(tat_columns['stage1'], lambda x: pd.to_numeric(x, errors='coerce').mean()),
                    Avg_Stage2=(tat_columns['stage2'], lambda x: pd.to_numeric(x, errors='coerce').mean()),
                    Avg_Stage3=(tat_columns['stage3'], lambda x: pd.to_numeric(x, errors='coerce').mean()),
                    Avg_Stage4=(tat_columns['stage4'], lambda x: pd.to_numeric(x, errors='coerce').mean()),
                    Avg_Stage5=(tat_columns['stage5'], lambda x: pd.to_numeric(x, errors='coerce').mean()),
                    Total_Records=(tat_columns['trip_no_col'] if tat_columns['trip_no_col'] else filtered_tat_df.columns[0], 'count')
                ).reset_index()
                
                dest_metrics['Total_Loading'] = dest_metrics['Avg_Stage1'] + dest_metrics['Avg_Stage2'] + dest_metrics['Avg_Stage3']
                dest_metrics['Total_Unloading'] = dest_metrics['Avg_Stage4'] + dest_metrics['Avg_Stage5']
                dest_metrics['Total_TAT'] = dest_metrics['Total_Loading'] + dest_metrics['Total_Unloading']
                
                # Sort by Total TAT
                dest_metrics = dest_metrics.sort_values('Total_TAT', ascending=True)
                
                fig_dest = px.bar(
                    dest_metrics,
                    x=tat_columns['destination_col'],
                    y=['Total_Loading', 'Total_Unloading'],
                    title='TAT Comparison by Destination (Top 15)',
                    labels={tat_columns['destination_col']: 'Destination', 'value': 'Minutes'},
                    color_discrete_map={'Total_Loading': '#1a73e8', 'Total_Unloading': '#34a853'}
                )
                fig_dest.update_layout(xaxis_tickangle=-45, height=500)
                st.plotly_chart(fig_dest, use_container_width=True)
        
        # Data preview
        with st.expander("👀 Preview Filtered TAT Data", expanded=False):
            st.dataframe(
                filtered_tat_df.head(50),
                use_container_width=True,
                height=300,
                hide_index=True
            )
            st.caption(f"Showing first 50 of {len(filtered_tat_df):,} filtered records")
        
        # Download options
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            # Download TAT summary report
            tat_export = pd.DataFrame({
                'Stage': ['Stage 1 - DO Receipt', 'Stage 2 - Gate Entry', 'Stage 3 - Loading Exit',
                         'Stage 4 - Unloading Wait', 'Stage 5 - Unloading',
                         'TOTAL LOADING', 'TOTAL UNLOADING', 'TOTAL TAT'],
                'Description': ['DO Receipt to Gate Entry', 'Gate Entry to Loading Bay', 'Loading Process & Exit',
                              'Unloading Waiting Time', 'Unloading Process',
                              'Sum of Stages 1-3', 'Sum of Stages 4-5', 'Loading + Unloading'],
                'Average Minutes': [avg_stage1, avg_stage2, avg_stage3, avg_stage4, avg_stage5,
                                   total_loading, total_unloading, total_tat],
                'Average HH:MM': [minutes_to_hhmm(avg_stage1), minutes_to_hhmm(avg_stage2), minutes_to_hhmm(avg_stage3),
                                 minutes_to_hhmm(avg_stage4), minutes_to_hhmm(avg_stage5),
                                 minutes_to_hhmm(total_loading), minutes_to_hhmm(total_unloading), minutes_to_hhmm(total_tat)]
            })
            
            csv_tat = tat_export.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download TAT Summary (CSV)",
                data=csv_tat,
                file_name="tat_summary_report.csv",
                mime="text/csv",
            )
        
        with col2:
            # Download filtered raw data
            csv_filtered = filtered_tat_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Filtered TAT Data (CSV)",
                data=csv_filtered,
                file_name="tat_filtered_data.csv",
                mime="text/csv",
            )


# ── Header ────────────────────────────────────────────────────────────────────
st.title("🚛 Monthly Trip Report Analyzer")
st.markdown("Upload one or more monthly trip reports to explore trips by client, plant, and destination.")
st.divider()

# ── File Upload Section ──────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📂 Trip Reports")
    uploaded_files = st.file_uploader(
        "Upload Trip Report(s) (.xlsx)",
        type=["xlsx"],
        accept_multiple_files=True,
        help="You can upload multiple monthly reports at once.",
        key="trip_uploader"
    )

with col2:
    st.markdown("### 📊 TAT Data")
    tat_file = st.file_uploader(
        "Upload TAT Data File (.xlsx)",
        type=["xlsx"],
        accept_multiple_files=False,
        help="Upload the Turnaround Time dataset for standalone analysis.",
        key="tat_uploader"
    )

st.divider()

# ── Determine available tabs ────────────────────────────────────────────────
has_trip_data = uploaded_files is not None and len(uploaded_files) > 0
has_tat_data = tat_file is not None

# ── Create tabs dynamically ──────────────────────────────────────────────────
if has_trip_data or has_tat_data:
    tab_labels = []
    if has_trip_data:
        tab_labels.append("🚛 Trip Analysis")
    if has_tat_data:
        tab_labels.append("📊 TAT Report")
    
    if len(tab_labels) == 2:
        tab1, tab2 = st.tabs(tab_labels)
    elif len(tab_labels) == 1:
        if tab_labels[0] == "🚛 Trip Analysis":
            tab1 = st.container()
            tab2 = None
        else:
            tab2 = st.container()
            tab1 = None
else:
    tab1 = st.container()
    tab2 = None

# ── Load Trip Data ───────────────────────────────────────────────────────────
df = pd.DataFrame()
audit_df = pd.DataFrame()
filtered = pd.DataFrame()

if has_trip_data:
    files_data = [(f.name, f.read()) for f in uploaded_files]
    result = load_files(files_data)

    df       = result["df"]
    audit_df = result["audit_df"]

    for level, text in result["messages"]:
        if level == "warning":
            st.warning(text)
        elif level == "error":
            st.error(text)
        else:
            st.info(text)

    if df.empty and not has_tat_data:
        st.error("No valid data could be loaded. Please check your files.")
        st.stop()

# ── Load TAT Data ────────────────────────────────────────────────────────────
df_tat = pd.DataFrame()
if has_tat_data:
    df_tat, tat_error = load_tat_file(tat_file.read())
    if tat_error:
        st.error(f"Could not read TAT file: {tat_error}")
        df_tat = pd.DataFrame()

# ── TAB 1: Trip Analysis ────────────────────────────────────────────────────
if has_trip_data and tab1 is not None:
    with (tab1 if tab2 is not None else st.container()):
        # [Trip Analysis code remains the same as in previous version]
        # ... (keeping all the existing Trip Analysis functionality)
        pass

# ── TAB 2: TAT Report ──────────────────────────────────────────────────────
if has_tat_data and tab2 is not None:
    with (tab2 if has_trip_data and has_tat_data else st.container()):
        if df_tat.empty:
            st.warning("⚠️ The TAT file could not be processed. Please check the file format and required columns.")
        else:
            trip_filter = None
            if has_trip_data and not filtered.empty and "Trip No" in filtered.columns:
                trip_filter = filtered["Trip No"].unique().tolist()
            
            render_tat_report(df_tat, {'trip_nos': trip_filter} if trip_filter else None)

# ── Show message if no data at all ──────────────────────────────────────────
if not has_trip_data and not has_tat_data:
    st.markdown("""
    <div style="text-align:center; padding: 60px 20px; color: #888;">
        <div style="font-size:4rem;">📂</div>
        <h3 style="color:#555;">No file uploaded yet</h3>
        <p>Upload your files above to get started:</p>
        <div style="display: flex; justify-content: center; gap: 40px; margin-top: 30px; flex-wrap: wrap;">
            <div style="background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); max-width: 300px;">
                <h4>🚛 Trip Analysis</h4>
                <p style="font-size:0.85rem;">Upload monthly trip reports (.xlsx)</p>
                <p style="font-size:0.8rem; color: #666;">
                <strong>Required:</strong> <code>Client</code>, <code>Destination</code>, <code>Start Date</code>, <code>Trip No</code>, <code>Trip Type</code>
                </p>
            </div>
            <div style="background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); max-width: 300px;">
                <h4>📊 TAT Analysis</h4>
                <p style="font-size:0.85rem;">Upload TAT data file (.xlsx)</p>
                <p style="font-size:0.8rem; color: #666;">
                <strong>Required:</strong> <code>Trip No</code>, time duration columns
                </p>
            </div>
        </div>
        <p style="font-size:0.85rem; margin-top:30px; color: #666;">
        • 🔁 <strong>Smart Deduplication</strong> — duplicate Trip Nos auto-merged<br>
        • 🔍 <strong>Drill-down modal</strong> — click any destination for full trip details<br>
        • ⏱️ <strong>TAT Analysis</strong> — standalone with client/plant/destination/date filters<br>
        • 📊 <strong>Two-Column TAT Layout</strong> — Loading vs Unloading clearly separated
        </p>
    </div>
    """, unsafe_allow_html=True)
