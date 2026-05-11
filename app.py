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
    /* TAT Report Table Styling */
    .tat-table {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Segoe UI', sans-serif;
        font-size: 0.9rem;
    }
    .tat-table th {
        background-color: #1a73e8;
        color: white;
        padding: 12px;
        text-align: left;
        font-weight: 600;
    }
    .tat-table td {
        padding: 10px 12px;
        border-bottom: 1px solid #e0e0e0;
    }
    .tat-table tr:hover {
        background-color: #f8f9fa;
    }
    .loading-row {
        background-color: #d4edda !important;
        font-weight: 700;
    }
    .unloading-row {
        background-color: #d4edda !important;
        font-weight: 700;
    }
    .total-row {
        background-color: #f0f0f0 !important;
        font-weight: 700;
        color: #d32f2f;
        font-size: 1.1rem;
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
    """
    Returns (deduped_df, audit_df). No Streamlit calls inside.
    Rules:
      1. Same Trip No + same destination  → sum Inv Qty, keep one row.
      2. Same Trip No + similar destinations (fuzzy) → canonicalize, sum qty.
      3. Same Trip No + genuinely different destinations → keep highest-qty leg.
    """
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


# ── Cached loader — ZERO st.* calls inside ───────────────────────────────────
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
        "stage1": ["Actual DO Receipt (Mins)", "DO Receipt (Mins)", "Actual DO Receipt"],
        "stage2": ["Actual Gate In(Mins)", "Gate In (Mins)", "Actual Gate In"],
        "stage3": ["Actual Loaded Exit(Mins)", "Loaded Exit (Mins)", "Actual Loaded Exit"],
        "stage4": ["Actual Gate In for Unloading(Mins)", "Gate In for Unloading (Mins)", "Actual Gate In for Unloading"],
        "stage5": ["Actual Unloaded (Mins)", "Unloaded (Mins)", "Actual Unloaded"],
        "date_col": ["Date", "Start Date", "Trip Date", "Transaction Date"],
        "destination_col": ["Destination", "To", "Delivery Location", "Unloading Point"],
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
    filters: dict with keys 'client', 'plant', 'trip_nos', 'date_range'
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
    st.subheader("📊 TAT Analysis Report")
    
    # Get filter options
    filter_options, tat_columns = get_tat_filter_options(df_tat)
    
    # ── TAT Filters ──────────────────────────────────────────────────────────
    with st.expander("🔍 TAT Data Filters", expanded=True):
        st.markdown('<div class="filter-section">', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
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
        
        with col2:
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
        
        # Trip filter option
        use_trip_filter = st.checkbox(
            "🔗 Filter by Trip Analysis selection",
            value=(filters is not None and filters.get('trip_nos') is not None),
            key="tat_trip_filter_checkbox",
            help="Filter TAT data to only include trips from the current Trip Analysis selection"
        )
        
        # Clear filters button
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("🗑️ Clear TAT Filters", key="clear_tat_filters"):
                st.session_state.tat_client_filter = "All Clients"
                st.session_state.tat_plant_filter = "All Plants"
                st.session_state.tat_trip_filter_checkbox = False
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Build filter dictionary
    tat_filters = {
        'client': selected_tat_client if 'selected_tat_client' in locals() else "All Clients",
        'plant': selected_tat_plant if 'selected_tat_plant' in locals() else "All Plants",
        'date_range': (start_date, end_date) if 'start_date' in locals() else (None, None),
        'trip_nos': filters.get('trip_nos') if use_trip_filter and filters else None
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
    
    # Detailed TAT Table
    st.markdown("### 📈 Detailed TAT Breakdown")
    
    # Prepare table data
    table_data = [
        {
            "Stage": "Stage 1",
            "Description": "DO Receipt to Gate Entry",
            "Average Time (Minutes)": f"{avg_stage1:.2f}",
            "Average Time (HH:MM)": minutes_to_hhmm(avg_stage1),
            "Type": "loading"
        },
        {
            "Stage": "Stage 2",
            "Description": "Gate Entry to Loading Bay",
            "Average Time (Minutes)": f"{avg_stage2:.2f}",
            "Average Time (HH:MM)": minutes_to_hhmm(avg_stage2),
            "Type": "loading"
        },
        {
            "Stage": "Stage 3",
            "Description": "Loading Process & Exit",
            "Average Time (Minutes)": f"{avg_stage3:.2f}",
            "Average Time (HH:MM)": minutes_to_hhmm(avg_stage3),
            "Type": "loading"
        },
        {
            "Stage": "Stage 4",
            "Description": "Unloading Waiting Time",
            "Average Time (Minutes)": f"{avg_stage4:.2f}",
            "Average Time (HH:MM)": minutes_to_hhmm(avg_stage4),
            "Type": "unloading"
        },
        {
            "Stage": "Stage 5",
            "Description": "Unloading Process",
            "Average Time (Minutes)": f"{avg_stage5:.2f}",
            "Average Time (HH:MM)": minutes_to_hhmm(avg_stage5),
            "Type": "unloading"
        },
    ]
    
    # Render table using custom HTML
    table_html = '<table class="tat-table"><thead><tr>'
    table_html += '<th>Stage</th><th>Description</th><th>Average Time (Minutes)</th><th>Average Time (HH:MM)</th>'
    table_html += '</tr></thead><tbody>'
    
    for row in table_data:
        table_html += '<tr>'
        table_html += f'<td>{row["Stage"]}</td>'
        table_html += f'<td>{row["Description"]}</td>'
        table_html += f'<td>{row["Average Time (Minutes)"]}</td>'
        table_html += f'<td>{row["Average Time (HH:MM)"]}</td>'
        table_html += '</tr>'
    
    # Add Total Loading row (green background)
    table_html += '<tr class="loading-row">'
    table_html += '<td colspan="2"><strong>⏱️ Total time for Loading</strong></td>'
    table_html += f'<td><strong>{total_loading:.2f}</strong></td>'
    table_html += f'<td><strong>{minutes_to_hhmm(total_loading)}</strong></td>'
    table_html += '</tr>'
    
    # Add Total Unloading row (green background)
    table_html += '<tr class="unloading-row">'
    table_html += '<td colspan="2"><strong>⏱️ Total time for Unloading</strong></td>'
    table_html += f'<td><strong>{total_unloading:.2f}</strong></td>'
    table_html += f'<td><strong>{minutes_to_hhmm(total_unloading)}</strong></td>'
    table_html += '</tr>'
    
    # Add Grand Total row (grey background, red text)
    table_html += '<tr class="total-row">'
    table_html += '<td colspan="2"><strong>⏱️ TOTAL TAT</strong></td>'
    table_html += f'<td><strong>{total_tat:.2f}</strong></td>'
    table_html += f'<td><strong>{minutes_to_hhmm(total_tat)}</strong></td>'
    table_html += '</tr>'
    
    table_html += '</tbody></table>'
    
    st.markdown(table_html, unsafe_allow_html=True)
    
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
        
        # Client/Plant breakdown if those columns exist
        tat_columns = identify_tat_columns(df_tat)
        
        if tat_columns['client_col'] or tat_columns['plant_col']:
            with st.expander("📋 TAT by Client & Plant", expanded=False):
                tab_client, tab_plant = st.tabs(["By Client", "By Plant"])
                
                with tab_client:
                    if tat_columns['client_col'] and tat_columns['client_col'] in filtered_tat_df.columns:
                        client_tat = filtered_tat_df.groupby(tat_columns['client_col']).agg(
                            Records=('Trip No' if 'Trip No' in filtered_tat_df.columns else filtered_tat_df.columns[0], 'count'),
                            Avg_Loading=(tat_columns['stage3'], lambda x: pd.to_numeric(x, errors='coerce').mean()),
                            Avg_Unloading=(tat_columns['stage5'], lambda x: pd.to_numeric(x, errors='coerce').mean())
                        ).reset_index()
                        client_tat.columns = ['Client', 'Records', 'Avg Loading (min)', 'Avg Unloading (min)']
                        client_tat['Total TAT (min)'] = client_tat['Avg Loading (min)'] + client_tat['Avg Unloading (min)']
                        
                        st.dataframe(
                            client_tat.sort_values('Records', ascending=False),
                            use_container_width=True,
                            hide_index=True
                        )
                    else:
                        st.info("Client column not available in TAT data")
                
                with tab_plant:
                    if tat_columns['plant_col'] and tat_columns['plant_col'] in filtered_tat_df.columns:
                        plant_tat = filtered_tat_df.groupby(tat_columns['plant_col']).agg(
                            Records=('Trip No' if 'Trip No' in filtered_tat_df.columns else filtered_tat_df.columns[0], 'count'),
                            Avg_Loading=(tat_columns['stage3'], lambda x: pd.to_numeric(x, errors='coerce').mean()),
                            Avg_Unloading=(tat_columns['stage5'], lambda x: pd.to_numeric(x, errors='coerce').mean())
                        ).reset_index()
                        plant_tat.columns = ['Plant', 'Records', 'Avg Loading (min)', 'Avg Unloading (min)']
                        plant_tat['Total TAT (min)'] = plant_tat['Avg Loading (min)'] + plant_tat['Avg Unloading (min)']
                        
                        st.dataframe(
                            plant_tat.sort_values('Records', ascending=False),
                            use_container_width=True,
                            hide_index=True
                        )
                    else:
                        st.info("Plant column not available in TAT data")
        
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
        help="Upload the TATound Time dataset for standalone analysis.",
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

    # Render messages
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
        # ── Deduplication Report ──────────────────────────────────────────────
        if not audit_df.empty:
            with st.expander(
                f"🔁 Deduplication Report — {len(audit_df)} trip(s) merged or resolved",
                expanded=False,
            ):
                st.markdown("""
**How duplicates were handled:**
- **Same destination variants** (e.g. `PUNE` vs `Pune`) → names standardized, quantities summed.
- **Genuinely different destinations** → leg with highest invoice quantity kept; others dropped.
- Full original values logged below for traceability.
""")
                st.dataframe(
                    audit_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Trip No": "Trip No",
                        "Action": st.column_config.TextColumn("Action Taken"),
                        "Destinations Found": "All Destinations Found",
                        "Canonical Destination": "Resolved Destination",
                        "Original Qty Values": "Original Qty Values",
                        "Final Qty": st.column_config.NumberColumn("Final Qty", format="%.2f"),
                        "Rows Affected": "Rows Merged",
                    },
                )
                st.download_button(
                    "📥 Download Deduplication Audit Log (CSV)",
                    data=audit_df.to_csv(index=False).encode("utf-8"),
                    file_name="deduplication_audit.csv",
                    mime="text/csv",
                )

        # ── Top-level metrics ─────────────────────────────────────────────────
        total_trips_all  = len(df)
        loaded_trips_all = len(df[df["Trip Type"] == "Loaded"])
        empty_trips_all  = len(df[df["Trip Type"] == "Empty"])
        total_qty_all    = df["Inv Qty"].sum()

        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("Total Trips (All)", f"{total_trips_all:,}")
        with c2: st.metric("Loaded Trips", f"{loaded_trips_all:,}",
                           delta=f"{loaded_trips_all/total_trips_all*100:.1f}%" if total_trips_all else "0%")
        with c3: st.metric("Empty Trips", f"{empty_trips_all:,}",
                           delta=f"{empty_trips_all/total_trips_all*100:.1f}%" if total_trips_all else "0%")
        with c4: st.metric("Total Quantity", f"{total_qty_all:,.2f}")

        st.success(f"✅ Loaded **{len(df):,}** unique trip records from **{len(files_data)}** file(s).")
        st.info("💡 **Tip:** Click on any destination in the table to see detailed trip information!")

        # ── Filters ───────────────────────────────────────────────────────────
        st.subheader("🔍 Filter Your Data")

        clients         = sorted(df["Client"].dropna().unique().tolist())
        regular_clients = [c for c in clients if not c.startswith("EMPTY TRIP")]
        empty_trip_opts = [c for c in clients if c.startswith("EMPTY TRIP")]
        client_options  = regular_clients + empty_trip_opts

        col1, col2 = st.columns(2)
        with col1:
            selected_client = st.selectbox("🏢 Select Client", client_options, key="client_select_tab1")
        with col2:
            client_plants = sorted(df[df["Client"] == selected_client]["Plant"].dropna().unique().tolist())
            ALL_PLANTS_LABEL = "All Plants"
            plant_options = [ALL_PLANTS_LABEL] + client_plants
            selected_plant_input = st.multiselect(
                "🏭 Select Plant/Source",
                options=plant_options,
                default=[],
                placeholder="Pick 'All Plants' to include all…",
                help="Select specific plants, or leave empty / choose 'All Plants' to include everything.",
                key="plant_select_tab1"
            )
            if not selected_plant_input or ALL_PLANTS_LABEL in selected_plant_input:
                selected_plants = client_plants
            else:
                selected_plants = selected_plant_input
            if not selected_plants:
                st.warning("⚠️ No plants found for this client.")
                if not has_tat_data:
                    st.stop()

        col3, col4, col5 = st.columns(3)
        with col3:
            months         = sorted(df["Month"].dropna().unique().tolist(), reverse=True)
            selected_month = st.selectbox("📅 Select Month", ["All Months"] + months, key="month_select_tab1")
        with col4:
            trip_type_opts = ["All Types"] + sorted(df["Trip Type"].dropna().unique().tolist())
            selected_type  = st.selectbox("🔄 Trip Type", trip_type_opts, key="type_select_tab1")
        with col5:
            if st.button("🗑️ Clear All Filters", use_container_width=True, key="clear_tab1"):
                st.rerun()

        st.divider()

        # ── Apply filters ─────────────────────────────────────────────────────
        if not selected_plants:
            filtered = df[df["Client"] == selected_client].copy()
        else:
            filtered = df[df["Client"] == selected_client].copy()
            filtered = filtered[filtered["Plant"].isin(selected_plants)]
        if selected_month != "All Months":
            filtered = filtered[filtered["Month"] == selected_month]
        if selected_type != "All Types":
            filtered = filtered[filtered["Trip Type"] == selected_type]

        # Rest of Trip Analysis code remains the same...
        # ── KPI Cards ─────────────────────────────────────────────────────────
        total_trips   = len(filtered)
        loaded_trips  = len(filtered[filtered["Trip Type"] == "Loaded"])
        empty_trips   = len(filtered[filtered["Trip Type"] == "Empty"])
        unique_dest   = filtered["Destination"].nunique()
        unique_plants = filtered["Plant"].nunique()
        unique_months = filtered["Month"].nunique()
        total_qty     = filtered["Inv Qty"].sum()

        st.caption(
            f"📌 **Selected Plants ({len(selected_plants)}):** "
            f"{', '.join(selected_plants[:5])}{'...' if len(selected_plants) > 5 else ''}"
        )

        def _card(col, val, label):
            with col:
                st.markdown(
                    f'<div class="metric-card"><div class="metric-number">{val}</div>'
                    f'<div class="metric-label">{label}</div></div>',
                    unsafe_allow_html=True,
                )

        if selected_client.startswith("EMPTY TRIP"):
            cols = st.columns(5)
            pairs = zip(cols,
                        [f"{total_trips:,}", unique_dest, unique_plants, unique_months, f"{total_qty:,.2f}"],
                        ["Total Empty Trips","Unique Destinations","Source Plants","Months Covered","Total Quantity"])
        else:
            cols = st.columns(6)
            pairs = zip(cols,
                        [f"{total_trips:,}", loaded_trips, empty_trips, unique_dest, unique_plants, f"{total_qty:,.2f}"],
                        ["Total Trips","Loaded Trips","Empty Trips","Unique Destinations","Plants/Sources","Total Quantity"])

        for c, v, l in pairs:
            _card(c, v, l)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Destination Summary ───────────────────────────────────────────────
        if selected_client.startswith("EMPTY TRIP"):
            st.subheader("📍 Empty Trip Destinations")
        else:
            st.subheader(f"📍 Trips to Each Destination — {selected_client}")
        st.caption("💡 **Click the 🔍 button** next to any destination to see detailed trip information")

        if filtered.empty:
            st.info("No trips found for the selected filters.")
        else:
            agg_dict = {
                "Total_Trips": ("Trip No", "count"),
                "Total_Qty":   ("Inv Qty", "sum"),
                "Plants":      ("Plant",   lambda x: x.nunique()),
            }
            if "Trip Type" in filtered.columns and filtered["Trip Type"].nunique() > 1:
                agg_dict["Loaded_Trips"] = ("Trip Type", lambda x: (x == "Loaded").sum())
                agg_dict["Empty_Trips"]  = ("Trip Type", lambda x: (x == "Empty").sum())

            dest_summary = (
                filtered.groupby("Destination").agg(**agg_dict).reset_index()
                .sort_values("Total_Trips", ascending=False)
                .rename(columns={
                    "Total_Trips": "Total Trips", "Total_Qty": "Total Quantity",
                    "Plants": "Plants Used", "Loaded_Trips": "Loaded Trips",
                    "Empty_Trips": "Empty Trips",
                })
            )

            chart_type = st.radio("📊 Display Chart Type", ["Total Trips", "Total Quantity"], horizontal=True)

            if chart_type == "Total Trips":
                fig = px.bar(dest_summary.head(20), x="Destination", y="Total Trips",
                             title="Top 20 Destinations by Trip Count",
                             color="Total Trips", color_continuous_scale="Blues", text="Total Trips")
                fig.update_traces(textposition="outside")
            else:
                fig = px.bar(dest_summary.head(20), x="Destination", y="Total Quantity",
                             title="Top 20 Destinations by Total Quantity",
                             color="Total Quantity", color_continuous_scale="Greens", text="Total Quantity")
                fig.update_traces(texttemplate="%{text:,.2f}", textposition="outside")

            fig.update_traces(hovertemplate="<b>%{x}</b><br>%{y:,.2f}<extra></extra>")
            fig.update_layout(xaxis_tickangle=-45, height=500)

            chart_col, table_col = st.columns([1, 1])
            with chart_col:
                st.plotly_chart(fig, use_container_width=True)

            with table_col:
                st.markdown("#### 📋 Destinations Summary")
                st.info("💡 Click **🔍** to drill into any destination")
                for idx, row in dest_summary.iterrows():
                    destination = row["Destination"]
                    c1, c2, c3, c4, c5 = st.columns([0.4, 0.15, 0.15, 0.2, 0.1])
                    with c1: st.write(f"**{destination}**")
                    with c2: st.write(f"{row['Total Trips']} trips")
                    with c3: st.write(f"📦 {row['Total Quantity']:,.2f}")
                    with c4:
                        if "Loaded Trips" in row:
                            st.write(f"🟢 {row['Loaded Trips']} / 🔴 {row['Empty Trips']}")
                    with c5:
                        if st.button("🔍", key=f"drill_{destination}_{idx}", help=f"View details for {destination}"):
                            show_trip_details(destination, filtered[filtered["Destination"] == destination].copy())

            # ── Plant Summary ─────────────────────────────────────────────────
            if len(selected_plants) > 1 and unique_plants > 1:
                st.divider()
                st.subheader("🏭 Trip Distribution by Plant")

                plant_summary = (
                    filtered.groupby("Plant")
                    .agg(
                        Total_Trips=("Trip No", "count"),
                        Total_Qty=("Inv Qty", "sum"),
                        Loaded_Trips=("Trip Type", lambda x: (x == "Loaded").sum()),
                        Empty_Trips=("Trip Type",  lambda x: (x == "Empty").sum()),
                        Unique_Destinations=("Destination", "nunique"),
                    )
                    .reset_index()
                    .sort_values("Total_Trips", ascending=False)
                )

                pc, pt = st.columns(2)
                with pc:
                    qf = px.bar(plant_summary, x="Plant", y="Total_Qty",
                                title="Total Quantity by Plant",
                                color="Total_Qty", color_continuous_scale="Greens", text="Total_Qty")
                    qf.update_traces(texttemplate="%{text:,.2f}", textposition="outside")
                    qf.update_layout(xaxis_tickangle=-45, height=350)
                    st.plotly_chart(qf, use_container_width=True)
                with pt:
                    st.dataframe(
                        plant_summary, use_container_width=True, height=350, hide_index=True,
                        column_config={
                            "Plant": "Source Plant",
                            "Total_Trips": "Total Trips",
                            "Total_Qty": st.column_config.NumberColumn("Total Quantity", format="%.2f"),
                            "Loaded_Trips": "Loaded", "Empty_Trips": "Empty",
                            "Unique_Destinations": "Destinations",
                        },
                    )

            # ── Empty Trip Movement ───────────────────────────────────────────
            if selected_client.startswith("EMPTY TRIP"):
                st.divider()
                st.subheader("🔄 Empty Trip Movement Analysis")
                empty_movement = (
                    filtered.groupby(["Plant", "Destination"])
                    .agg(Number_of_Empty_Trips=("Trip No", "count"), Total_Quantity=("Inv Qty", "sum"))
                    .reset_index()
                    .sort_values("Number_of_Empty_Trips", ascending=False)
                    .head(20)
                )
                st.dataframe(
                    empty_movement, use_container_width=True, hide_index=True,
                    column_config={
                        "Plant": "Source Plant", "Destination": "Destination",
                        "Number_of_Empty_Trips": "Trip Count",
                        "Total_Quantity": st.column_config.NumberColumn("Total Quantity", format="%.2f"),
                    },
                )

            # ── Download ──────────────────────────────────────────────────────
            st.divider()
            export_buf = BytesIO()
            with pd.ExcelWriter(export_buf, engine="openpyxl") as writer:
                dest_summary.to_excel(writer, sheet_name="Destination Summary", index=False)
                filtered.to_excel(writer, sheet_name="Raw Trips", index=False)
                if len(selected_plants) > 1 and unique_plants > 1:
                    plant_summary.to_excel(writer, sheet_name="Plant Summary", index=False)
                if selected_client.startswith("EMPTY TRIP"):
                    empty_movement.to_excel(writer, sheet_name="Empty Trip Movement", index=False)
                if not audit_df.empty:
                    audit_df.to_excel(writer, sheet_name="Dedup Audit Log", index=False)
            export_buf.seek(0)

            plants_label = (
                f"{len(selected_plants)}_plants" if len(selected_plants) > 1
                else selected_plants[0].replace(" ", "_")
            )
            month_label  = selected_month.replace(" ", "_") if selected_month != "All Months" else "All_Months"
            client_label = selected_client.replace(" ", "_").replace("-", "_")[:50]
            st.download_button(
                label="⬇️ Download Summary as Excel",
                data=export_buf,
                file_name=f"{client_label}_{plants_label}_{month_label}_trip_summary.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

# ── TAB 2: TAT Report ──────────────────────────────────────────────────────
if has_tat_data and tab2 is not None:
    with (tab2 if has_trip_data and has_tat_data else st.container()):
        if df_tat.empty:
            st.warning("⚠️ The TAT file could not be processed. Please check the file format and required columns.")
        else:
            # Prepare trip filter from Trip Analysis if available
            trip_filter = None
            if has_trip_data and not filtered.empty and "Trip No" in filtered.columns:
                trip_filter = filtered["Trip No"].unique().tolist()
            
            # Render the TAT report with trip filter option
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
        • ⏱️ <strong>TAT Analysis</strong> — standalone with client/plant/date filters<br>
        • 📊 <strong>Interactive charts</strong> — toggle between Trip Count and Quantity views
        </p>
    </div>
    """, unsafe_allow_html=True)
