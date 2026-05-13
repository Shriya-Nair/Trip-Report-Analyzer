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
    .loading-header { background: linear-gradient(135deg, #1a73e8, #1557b0); }
    .unloading-header { background: linear-gradient(135deg, #34a853, #2d8f47); }
    .tat-column-body { padding: 15px 20px; }
    .tat-stage-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 15px;
        border-bottom: 1px solid #e8eaed;
        transition: background-color 0.2s;
    }
    .tat-stage-row:hover { background-color: #f8f9fa; }
    .tat-stage-row:last-child { border-bottom: none; }
    .stage-info { flex: 1; }
    .stage-name { font-weight: 600; color: #333; font-size: 0.9rem; }
    .stage-desc { font-size: 0.8rem; color: #666; margin-top: 2px; }
    .stage-time { text-align: right; }
    .stage-minutes { font-weight: 600; color: #333; font-size: 0.95rem; }
    .stage-hhmm { font-size: 0.85rem; color: #1a73e8; font-weight: 500; }
    .tat-total-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 15px 20px;
        background: #d4edda;
        border-top: 2px solid #c3e6cb;
        font-weight: 700;
    }
    .tat-total-label { font-size: 1rem; color: #155724; }
    .tat-total-time { text-align: right; }
    .tat-total-minutes { font-size: 1.1rem; color: #155724; font-weight: 700; }
    .tat-total-hhmm { font-size: 0.95rem; color: #1a73e8; font-weight: 600; }
    
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
    .grand-total-label { font-size: 1.3rem; font-weight: 700; color: #d32f2f; }
    .grand-total-time { text-align: right; }
    .grand-total-minutes { font-size: 1.4rem; font-weight: 700; color: #d32f2f; }
    .grand-total-hhmm { font-size: 1.6rem; font-weight: 700; color: #b71c1c; }
    .grand-total-formula { font-size: 0.85rem; color: #666; margin-top: 5px; text-align: center; }
    .filter-section {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        margin-bottom: 20px;
    }
    
    .summary-table {
        width: 100%;
        border-collapse: collapse;
        margin: 15px 0;
        font-size: 0.85rem;
    }
    .summary-table th {
        background: #1a73e8;
        color: white;
        padding: 10px 8px;
        text-align: center;
        font-weight: 600;
        border: 1px solid #1557b0;
        white-space: nowrap;
    }
    .summary-table td {
        padding: 8px 10px;
        text-align: center;
        border: 1px solid #e0e0e0;
        white-space: nowrap;
    }
    .summary-table tr:hover { background-color: #f8f9fa; }
    .summary-table .header-row th {
        background: #0d47a1;
        font-size: 0.85rem;
    }
    .summary-table .client-col {
        text-align: left;
        font-weight: 500;
        min-width: 200px;
    }
    .summary-table .plant-col {
        text-align: left;
        min-width: 150px;
    }
    .summary-table .loading-cell {
        background-color: #e3f2fd;
        font-weight: 500;
    }
    .summary-table .unloading-cell {
        background-color: #e8f5e9;
        font-weight: 500;
    }
    .summary-table .total-cell {
        background-color: #fce4ec;
        font-weight: 700;
    }
    .summary-table .grand-total-row {
        background-color: #f0f0f0 !important;
        font-weight: 700;
        border-top: 2px solid #d32f2f;
    }
    .summary-table .grand-total-row td {
        border-top: 2px solid #d32f2f;
        font-weight: 700;
    }
    .summary-table .grand-total-label {
        text-align: right;
        font-weight: 700;
        color: #d32f2f;
    }
</style>
""", unsafe_allow_html=True)


# ── Drill-Down Modal ──────────────────────────────────────────────────────────
@st.dialog("📋 Trip Details", width="large")
def show_trip_details(destination, trips_df):
    st.markdown(f"### 🚛 Trips to **{destination}**")
    total_qty = trips_df["Inv Qty"].sum() if "Inv Qty" in trips_df.columns else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Total Trips", len(trips_df))
    with col2:
        if "Trip Type" in trips_df.columns:
            st.metric("Loaded Trips", len(trips_df[trips_df["Trip Type"] == "Loaded"]))
    with col3:
        if "Plant" in trips_df.columns:
            st.metric("Plants Used", trips_df["Plant"].nunique())
    with col4: st.metric("Total Quantity", f"{total_qty:,.2f}")

    st.divider()
    st.subheader("📊 Detailed Trip List")
    display_cols = ["Trip No", "Start Date", "Trip Type", "Client", "Plant", "Inv Qty", "Source File"]
    available_cols = [col for col in display_cols if col in trips_df.columns]
    st.dataframe(trips_df[available_cols], use_container_width=True, height=400, hide_index=True)

    csv = trips_df[available_cols].to_csv(index=False).encode("utf-8")
    st.download_button(label="📥 Download CSV", data=csv, file_name=f"trips_to_{destination}.csv", mime="text/csv")


# ── Destination Name Fuzzy Helpers ────────────────────────────────────────────
def _normalize(name: str) -> str:
    import re
    name = str(name).lower().strip()
    name = re.sub(r"[^\w\s]", "", name)
    name = re.sub(r"\s+", " ", name)
    return name

def _similar(a: str, b: str, threshold: float = 0.82) -> bool:
    na, nb = _normalize(a), _normalize(b)
    if na == nb: return True
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
        if not placed: clusters.append([dest])
    alias_map = {}
    for cluster in clusters:
        canonical = max(cluster, key=len)
        for variant in cluster: alias_map[variant] = canonical
    return alias_map


# ── Deduplication ────────────────────────────────────────────────────────────
def deduplicate_trips(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    if "Trip No" not in df.columns: return df, pd.DataFrame()
    alias_map = _build_destination_alias_map(df["Destination"].fillna("Unknown"))
    df = df.copy()
    df["Destination"] = df["Destination"].map(lambda d: alias_map.get(d, d))
    duplicated_mask = df.duplicated(subset=["Trip No"], keep=False)
    unique_df = df[~duplicated_mask].copy()
    dup_df = df[duplicated_mask].copy()
    audit_records, merged_rows, merged_qtys = [], [], []

    for trip_no, group in dup_df.groupby("Trip No"):
        destinations = group["Destination"].dropna().unique().tolist()
        if len(destinations) == 1:
            summed_qty = float(group["Inv Qty"].sum())
            representative = group.iloc[0].copy()
            merged_rows.append(representative)
            merged_qtys.append(summed_qty)
            audit_records.append({
                "Trip No": trip_no, "Action": "MERGED – same destination",
                "Destinations Found": "; ".join(destinations),
                "Canonical Destination": destinations[0],
                "Original Qty Values": "; ".join(group["Inv Qty"].astype(str).tolist()),
                "Final Qty": summed_qty, "Rows Affected": len(group),
            })
        else:
            best_idx = group["Inv Qty"].idxmax()
            best_qty = float(group.loc[best_idx, "Inv Qty"])
            representative = group.loc[best_idx].copy()
            merged_rows.append(representative)
            merged_qtys.append(best_qty)
            audit_records.append({
                "Trip No": trip_no, "Action": "KEPT BEST LEG – different destinations",
                "Destinations Found": "; ".join(destinations),
                "Canonical Destination": representative["Destination"],
                "Original Qty Values": "; ".join(group["Inv Qty"].astype(str).tolist()),
                "Final Qty": best_qty, "Rows Affected": len(group),
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
            source_col = next((c for c in ["Source", "Source Place", "Plant", "Origin", "From"] if c in df.columns), None)
            if source_col: df["Plant"] = df[source_col].fillna("Unknown")
            else:
                df["Plant"] = "All Plants"
                messages.append(("info", f"📌 **{name}** has no Source/Plant column. Using 'All Plants'."))
            if "Inv Qty" not in df.columns:
                df["Inv Qty"] = 0.0
                messages.append(("info", f"📌 **{name}** has no 'Inv Qty' column. Using 0."))
            else: df["Inv Qty"] = pd.to_numeric(df["Inv Qty"], errors="coerce").fillna(0).astype(float)
            df["_source_file"] = name
            df["Source File"] = name
            frames.append(df)
        except Exception as e:
            messages.append(("error", f"Could not read **{name}**: {e}"))

    if not frames: return {"df": pd.DataFrame(), "audit_df": pd.DataFrame(), "messages": messages}
    combined = pd.concat(frames, ignore_index=True)
    combined["Start Date"] = pd.to_datetime(combined["Start Date"], dayfirst=True, errors="coerce")
    combined["Month"] = combined["Start Date"].dt.to_period("M").astype(str)
    combined["Trip Type"] = combined["Trip Type"].str.title()
    rows_before = len(combined)
    combined, audit_df = deduplicate_trips(combined)
    removed = rows_before - len(combined)
    if removed > 0: messages.append(("dedup", f"🔁 Deduplication removed **{removed:,}** duplicate row(s)."))
    return {"df": combined, "audit_df": audit_df, "messages": messages}


# ── TAT Processing Functions ─────────────────────────────────────────────────
@st.cache_data
def load_tat_file(tat_file_data):
    try:
        df_tat = pd.read_excel(BytesIO(tat_file_data), sheet_name=0)
        return df_tat, None
    except Exception as e:
        return pd.DataFrame(), str(e)


def minutes_to_hhmm(minutes: float) -> str:
    if pd.isna(minutes) or minutes < 0: return "00:00"
    total_minutes = int(round(minutes))
    hours = total_minutes // 60
    mins = total_minutes % 60
    return f"{hours:02d}:{mins:02d}"


def identify_tat_columns(df_tat: pd.DataFrame) -> dict:
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


def deduplicate_tat_data(df_tat: pd.DataFrame, tat_columns: dict) -> pd.DataFrame:
    """Deduplicate TAT data by Trip No AND Plant, averaging stage values."""
    if df_tat.empty or not tat_columns['trip_no_col']:
        return df_tat
    
    df = df_tat.copy()
    trip_no_col = tat_columns['trip_no_col']
    plant_col = tat_columns['plant_col']
    
    # FIX: Ensure Trip No is string and remove trailing .0 from float conversion
    df[trip_no_col] = df[trip_no_col].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
    if plant_col and plant_col in df.columns:
        df[plant_col] = df[plant_col].astype(str).str.strip()
    
    # Build group columns - Trip No + Plant
    group_cols = [trip_no_col]
    if plant_col and plant_col in df.columns:
        group_cols.append(plant_col)
    
    # Convert stage columns to numeric with fillna(0)
    stage_cols = ['stage1', 'stage2', 'stage3', 'stage4', 'stage5']
    numeric_cols = []
    for stage in stage_cols:
        col = tat_columns[stage]
        if col and col in df.columns:
            df[f"_{stage}_val"] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            numeric_cols.append(f"_{stage}_val")
    
    if not numeric_cols:
        return df_tat
    
    # Build aggregation: mean for numeric, first for others
    agg_dict = {col: 'mean' for col in numeric_cols}
    other_cols = [c for c in df.columns if c not in numeric_cols and c not in group_cols]
    for col in other_cols:
        agg_dict[col] = 'first'
    
    # Group by Trip No + Plant
    deduped = df.groupby(group_cols, as_index=False).agg(agg_dict)
    
    # Restore original column names for stages
    for stage in stage_cols:
        col = tat_columns[stage]
        if col and f"_{stage}_val" in deduped.columns:
            deduped[col] = deduped[f"_{stage}_val"]
    
    return deduped

def process_tat_data(df_tat: pd.DataFrame, filters: dict = None) -> tuple:
    if df_tat.empty: return 0, 0, 0, 0, 0, 0, pd.DataFrame()
    
    df_filtered = df_tat.copy()
    columns = identify_tat_columns(df_tat)
    
    # Apply filters
    if filters:
        if filters.get('trip_nos') and columns['trip_no_col']:
            trip_nos_str = [str(t).strip() for t in filters['trip_nos']]
            df_filtered[columns['trip_no_col']] = df_filtered[columns['trip_no_col']].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
            df_filtered = df_filtered[df_filtered[columns['trip_no_col']].isin(trip_nos_str)]
        
        # FIX B: Match ALL client variants
        if filters.get('client') and filters['client'] != "All Clients" and columns['client_col']:
            client_search = str(filters['client']).strip().upper()
            
            # Get all unique clients in data
            all_clients = df_filtered[columns['client_col']].dropna().unique()
            # Find all that match
            matching_clients = [c for c in all_clients if client_search in str(c).upper() or str(c).upper() in client_search]
            
            if matching_clients:
                df_filtered = df_filtered[df_filtered[columns['client_col']].isin(matching_clients)]
            else:
                # Fallback to contains
                mask = df_filtered[columns['client_col']].astype(str).str.upper().str.contains(client_search, na=False)
                df_filtered = df_filtered[mask]
        
        if filters.get('plant') and filters['plant'] != "All Plants" and columns['plant_col']:
            df_filtered = df_filtered[df_filtered[columns['plant_col']] == filters['plant']]
        if filters.get('destination') and filters['destination'] != "All Destinations" and columns['destination_col']:
            df_filtered = df_filtered[df_filtered[columns['destination_col']] == filters['destination']]
        if filters.get('date_range') and columns['date_col']:
            start_date, end_date = filters['date_range']
            if start_date and end_date:
                date_series = pd.to_datetime(df_filtered[columns['date_col']], errors='coerce')
                df_filtered = df_filtered[(date_series >= pd.Timestamp(start_date)) & (date_series <= pd.Timestamp(end_date))]
    
    if df_filtered.empty:
        return 0, 0, 0, 0, 0, 0, pd.DataFrame()
    
    df_deduped = deduplicate_tat_data(df_filtered, columns)
    
    if df_deduped.empty:
        return 0, 0, 0, 0, 0, 0, pd.DataFrame()
    
    total_records = len(df_deduped)
    
    averages = {}
    for stage in ["stage1", "stage2", "stage3", "stage4", "stage5"]:
        col = columns[stage]
        if col and col in df_deduped.columns:
            avg_val = pd.to_numeric(df_deduped[col], errors='coerce').fillna(0).mean()
            averages[stage] = avg_val if not pd.isna(avg_val) else 0
        else:
            averages[stage] = 0
    
    return (averages["stage1"], averages["stage2"], averages["stage3"],
            averages["stage4"], averages["stage5"], total_records, df_deduped)


def get_tat_filter_options(df_tat: pd.DataFrame) -> dict:
    columns = identify_tat_columns(df_tat)
    options = {}
    if columns['client_col']:
        clients = sorted(df_tat[columns['client_col']].dropna().unique().tolist())
        options['clients'] = ["All Clients"] + clients
    else: options['clients'] = ["All Clients"]
    if columns['plant_col']:
        plants = sorted(df_tat[columns['plant_col']].dropna().unique().tolist())
        options['plants'] = ["All Plants"] + plants
    else: options['plants'] = ["All Plants"]
    if columns['destination_col']:
        destinations = sorted(df_tat[columns['destination_col']].dropna().unique().tolist())
        options['destinations'] = ["All Destinations"] + destinations
    else: options['destinations'] = ["All Destinations"]
    if columns['date_col']:
        date_series = pd.to_datetime(df_tat[columns['date_col']], errors='coerce')
        options['min_date'] = date_series.min().date() if not pd.isna(date_series.min()) else None
        options['max_date'] = date_series.max().date() if not pd.isna(date_series.max()) else None
    else: options['min_date'], options['max_date'] = None, None
    return options, columns


def calculate_client_plant_tat_summary(df_tat, tat_columns):
    """Calculate Client | Plant | Loading TAT | Unloading TAT | Total TAT summary."""
    if df_tat.empty: return pd.DataFrame()
    
    # Deduplicate first
    df_deduped = deduplicate_tat_data(df_tat, tat_columns)
    
    if df_deduped.empty: return pd.DataFrame()
    
    # Calculate stage values with fillna(0) - FIX C: No filtering, keep all rows
    for stage in ["stage1", "stage2", "stage3", "stage4", "stage5"]:
        col = tat_columns[stage]
        if col and col in df_deduped.columns:
            df_deduped[f"_{stage}_val"] = pd.to_numeric(df_deduped[col], errors='coerce').fillna(0)
        else:
            df_deduped[f"_{stage}_val"] = 0
    
    df_deduped["_loading_tat"] = df_deduped["_stage1_val"] + df_deduped["_stage2_val"] + df_deduped["_stage3_val"]
    df_deduped["_unloading_tat"] = df_deduped["_stage4_val"] + df_deduped["_stage5_val"]
    df_deduped["_total_tat"] = df_deduped["_loading_tat"] + df_deduped["_unloading_tat"]
    
    # Determine grouping columns
    group_cols = []
    if tat_columns['client_col'] and tat_columns['client_col'] in df_deduped.columns:
        group_cols.append(tat_columns['client_col'])
    if tat_columns['plant_col'] and tat_columns['plant_col'] in df_deduped.columns:
        group_cols.append(tat_columns['plant_col'])
    
    if not group_cols:
        return pd.DataFrame()
    
    # Group by and aggregate - NO filtering, NO dropping rows
    summary = df_deduped.groupby(group_cols, as_index=False).agg(
        No_of_Trips=(group_cols[0], "count"),
        Stage1_Avg=("_stage1_val", "mean"),
        Stage2_Avg=("_stage2_val", "mean"),
        Stage3_Avg=("_stage3_val", "mean"),
        Stage4_Avg=("_stage4_val", "mean"),
        Stage5_Avg=("_stage5_val", "mean"),
        Loading_TAT=("_loading_tat", "mean"),
        Unloading_TAT=("_unloading_tat", "mean"),
        Total_TAT=("_total_tat", "mean"),
    )
    
    # Add HH:MM columns
    summary["Stage1_HHMM"] = summary["Stage1_Avg"].apply(minutes_to_hhmm)
    summary["Stage2_HHMM"] = summary["Stage2_Avg"].apply(minutes_to_hhmm)
    summary["Stage3_HHMM"] = summary["Stage3_Avg"].apply(minutes_to_hhmm)
    summary["Stage4_HHMM"] = summary["Stage4_Avg"].apply(minutes_to_hhmm)
    summary["Stage5_HHMM"] = summary["Stage5_Avg"].apply(minutes_to_hhmm)
    summary["Loading_TAT_HHMM"] = summary["Loading_TAT"].apply(minutes_to_hhmm)
    summary["Unloading_TAT_HHMM"] = summary["Unloading_TAT"].apply(minutes_to_hhmm)
    summary["Total_TAT_HHMM"] = summary["Total_TAT"].apply(minutes_to_hhmm)
    
    summary = summary.sort_values("Total_TAT")
    
    return summary


def get_plant_drilldown_data(df_tat, tat_columns, plant_value, client_value=None):
    """Get detailed trip-level data for a specific plant."""
    df = df_tat.copy()
    
    if tat_columns['plant_col'] and tat_columns['plant_col'] in df.columns:
        df = df[df[tat_columns['plant_col']] == plant_value]
    
    if client_value and tat_columns['client_col'] and tat_columns['client_col'] in df.columns:
        client_val = str(client_value).strip().upper()
        mask = df[tat_columns['client_col']].astype(str).str.upper().str.contains(client_val, na=False)
        df = df[mask]
    
    if df.empty:
        return pd.DataFrame()
    
    df = deduplicate_tat_data(df, tat_columns)
    
    for stage in ["stage1", "stage2", "stage3", "stage4", "stage5"]:
        col = tat_columns[stage]
        if col and col in df.columns:
            df[f"_{stage}_val"] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        else:
            df[f"_{stage}_val"] = 0
    
    df["Loading_TAT"] = df["_stage1_val"] + df["_stage2_val"] + df["_stage3_val"]
    df["Unloading_TAT"] = df["_stage4_val"] + df["_stage5_val"]
    df["Total_TAT"] = df["Loading_TAT"] + df["Unloading_TAT"]
    
    result_cols = {}
    if tat_columns['trip_no_col']:
        result_cols['Trip No'] = df[tat_columns['trip_no_col']]
    if tat_columns['client_col']:
        result_cols['Client'] = df[tat_columns['client_col']]
    if tat_columns['destination_col']:
        result_cols['Destination'] = df[tat_columns['destination_col']]
    
    result_cols.update({
        'DO Receipt (min)': df['_stage1_val'],
        'Gate In - Loading (min)': df['_stage2_val'],
        'Loading Exit (min)': df['_stage3_val'],
        'Gate In - Unloading (min)': df['_stage4_val'],
        'Unloading Exit (min)': df['_stage5_val'],
        'Loading TAT (min)': df['Loading_TAT'],
        'Unloading TAT (min)': df['Unloading_TAT'],
        'Total TAT (min)': df['Total_TAT'],
        'DO Receipt (HH:MM)': df['_stage1_val'].apply(minutes_to_hhmm),
        'Gate In - Loading (HH:MM)': df['_stage2_val'].apply(minutes_to_hhmm),
        'Loading Exit (HH:MM)': df['_stage3_val'].apply(minutes_to_hhmm),
        'Gate In - Unloading (HH:MM)': df['_stage4_val'].apply(minutes_to_hhmm),
        'Unloading Exit (HH:MM)': df['_stage5_val'].apply(minutes_to_hhmm),
        'Loading TAT (HH:MM)': df['Loading_TAT'].apply(minutes_to_hhmm),
        'Unloading TAT (HH:MM)': df['Unloading_TAT'].apply(minutes_to_hhmm),
        'Total TAT (HH:MM)': df['Total_TAT'].apply(minutes_to_hhmm),
    })
    
    return pd.DataFrame(result_cols)

def render_tat_report(df_tat, filters=None):
    st.subheader("📊 Turnaround Time (TAT) Analysis Report")
    
    filter_options, tat_columns = get_tat_filter_options(df_tat)
    
    # ── CRITICAL: Standardize ALL names and fix Trip No ──────────────────────
    if tat_columns['trip_no_col'] and tat_columns['trip_no_col'] in df_tat.columns:
        df_tat[tat_columns['trip_no_col']] = df_tat[tat_columns['trip_no_col']].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
    
    if tat_columns['plant_col'] and tat_columns['plant_col'] in df_tat.columns:
        df_tat[tat_columns['plant_col']] = df_tat[tat_columns['plant_col']].astype(str).str.upper().str.strip()
    if tat_columns['client_col'] and tat_columns['client_col'] in df_tat.columns:
        df_tat[tat_columns['client_col']] = df_tat[tat_columns['client_col']].astype(str).str.upper().str.strip()
    
    # Predefined client list (UPPERCASE)
    ALLOWED_CLIENTS = [
        "ARCELORMITTAL NIPPON STEEL INDIA LIMITED",
        "DALMIA CEMENT (BHARAT)LIMITED",
        "HINDUSTAN ZINC LIMITED",
        "JINDAL STEEL AND POWER LIMITED",
        "JSW STEEL LIMITED",
        "TATA STEEL LIMITED CHENNAI",
        "TATA STEEL LIMITED"
    ]
    
    # Find matching clients using CONTAINS for flexibility
    all_clients_in_data = sorted(df_tat[tat_columns['client_col']].dropna().unique().tolist()) if tat_columns['client_col'] else []
    available_clients = ["All Clients"]
    client_mapping = {}
    
    if all_clients_in_data:
        for allowed_client in ALLOWED_CLIENTS:
            for actual_client in all_clients_in_data:
                if allowed_client in actual_client or actual_client in allowed_client:
                    available_clients.append(allowed_client)
                    client_mapping[allowed_client] = actual_client
                    break
    
    # ── TAT Filters ──────────────────────────────────────────────────────────
    with st.expander("🔍 TAT Data Filters", expanded=True):
        st.markdown('<div class="filter-section">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if len(available_clients) > 1:
                selected_tat_client = st.selectbox("🏢 Client", available_clients, key="tat_client_filter")
            else:
                selected_tat_client = "All Clients"
                st.warning("⚠️ None of the specified clients found in TAT data")
        
        actual_client_name = client_mapping.get(selected_tat_client, selected_tat_client) if selected_tat_client != "All Clients" else "All Clients"
        
        # ── DIAGNOSTIC: Show what clients exist in data ──────────────────────
        with st.expander("🔧 Diagnostic: Client Data", expanded=False):
            st.write(f"**Selected client from dropdown:** {selected_tat_client}")
            st.write(f"**Mapped actual client name:** {actual_client_name}")
            st.write("**All unique clients in TAT data:**")
            st.write(all_clients_in_data)
            st.write("**Client mapping:**")
            st.write(client_mapping)
            
            # Show plant distribution for ALL clients that match the pattern
            if actual_client_name != "All Clients":
                st.write(f"**Plants for clients matching '{selected_tat_client}':**")
                client_val = str(selected_tat_client).strip().upper()
                for actual_cl in all_clients_in_data:
                    if client_val in actual_cl or actual_cl in client_val:
                        plant_count = df_tat[df_tat[tat_columns['client_col']] == actual_cl][tat_columns['plant_col']].value_counts()
                        st.write(f"  Client: **{actual_cl}** → Plants: {dict(plant_count)}")
        
        with col2:
            if tat_columns['plant_col']:
                temp_df = df_tat.copy()
                if actual_client_name != "All Clients" and tat_columns['client_col']:
                    # FIX: Match ALL client variants, not just the mapped one
                    client_search = str(selected_tat_client).strip().upper()
                    # Find ALL actual client names that contain this search term
                    matching_clients = [c for c in all_clients_in_data if client_search in c or c in client_search]
                    
                    if matching_clients:
                        # Use all matching clients, not just one
                        mask = temp_df[tat_columns['client_col']].isin(matching_clients)
                        temp_df = temp_df[mask]
                    else:
                        # Fallback to contains
                        mask = temp_df[tat_columns['client_col']].astype(str).str.upper().str.contains(client_search, na=False)
                        temp_df = temp_df[mask]
                
                filtered_plants = sorted(temp_df[tat_columns['plant_col']].dropna().unique().tolist())
                plant_options = ["All Plants"] + filtered_plants if filtered_plants else ["All Plants"]
                
                # Diagnostic
                with st.expander("🔧 Diagnostic: Plant Dropdown Data", expanded=False):
                    st.write(f"**Number of plants found for filter:** {len(filtered_plants)}")
                    st.write(f"**Plants:** {filtered_plants}")
                
                selected_tat_plant = st.selectbox("🏭 Plant/Source", plant_options, key="tat_plant_filter")
            else:
                selected_tat_plant = "All Plants"
        
        with col3:
            if tat_columns['destination_col']:
                temp_df = df_tat.copy()
                if actual_client_name != "All Clients" and tat_columns['client_col']:
                    client_search = str(selected_tat_client).strip().upper()
                    matching_clients = [c for c in all_clients_in_data if client_search in c or c in client_search]
                    
                    if matching_clients:
                        mask = temp_df[tat_columns['client_col']].isin(matching_clients)
                        temp_df = temp_df[mask]
                    else:
                        mask = temp_df[tat_columns['client_col']].astype(str).str.upper().str.contains(client_search, na=False)
                        temp_df = temp_df[mask]
                
                if selected_tat_plant != "All Plants" and tat_columns['plant_col']:
                    temp_df = temp_df[temp_df[tat_columns['plant_col']] == selected_tat_plant]
                
                filtered_destinations = sorted(temp_df[tat_columns['destination_col']].dropna().unique().tolist())
                destination_options = ["All Destinations"] + filtered_destinations if filtered_destinations else ["All Destinations"]
                
                selected_tat_destination = st.selectbox("📍 Destination", destination_options, key="tat_destination_filter")
            else:
                selected_tat_destination = "All Destinations"
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if filter_options['min_date'] and filter_options['max_date']:
                date_range = st.date_input("📅 Date Range", value=(filter_options['min_date'], filter_options['max_date']),
                                          min_value=filter_options['min_date'], max_value=filter_options['max_date'], key="tat_date_filter")
                start_date, end_date = (date_range[0], date_range[1]) if len(date_range) == 2 else (None, None)
            else:
                start_date, end_date = None, None
        
        with col2:
            use_trip_filter = st.checkbox("🔗 Filter by Trip Analysis selection",
                                         value=(filters is not None and filters.get('trip_nos') is not None), key="tat_trip_filter_checkbox")
        
        with col3:
            if st.button("🗑️ Clear TAT Filters", use_container_width=True, key="clear_tat_filters"):
                for key in ["tat_client_filter", "tat_plant_filter", "tat_destination_filter", "tat_trip_filter_checkbox"]:
                    if key in st.session_state: del st.session_state[key]
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # FIX: Use the actual selected client for filtering, but match ALL variants
    client_search_term = str(selected_tat_client).strip().upper() if selected_tat_client != "All Clients" else "All Clients"
    
    tat_filters = {
        'client': client_search_term,  # Pass the search term, not mapped name
        'plant': selected_tat_plant,
        'destination': selected_tat_destination if selected_tat_destination != "All Destinations" else "All Destinations",
        'date_range': (start_date, end_date) if 'start_date' in locals() else (None, None),
        'trip_nos': filters.get('trip_nos') if use_trip_filter and filters else None,
    }
    
    avg_stage1, avg_stage2, avg_stage3, avg_stage4, avg_stage5, total_records, filtered_tat_df = process_tat_data(df_tat, tat_filters)
    
    # ── DIAGNOSTIC: Show filtered results ────────────────────────────────────
    with st.expander("🔧 Diagnostic: After Filtering", expanded=False):
        st.write(f"**Total records after filtering:** {total_records}")
        if not filtered_tat_df.empty and tat_columns['plant_col']:
            plant_counts = filtered_tat_df[tat_columns['plant_col']].value_counts()
            st.write(f"**Plants in filtered data ({len(plant_counts)}):**")
            st.write(plant_counts)
        if not filtered_tat_df.empty and tat_columns['client_col']:
            client_counts = filtered_tat_df[tat_columns['client_col']].value_counts()
            st.write(f"**Clients in filtered data:**")
            st.write(client_counts)
        
    total_loading = avg_stage1 + avg_stage2 + avg_stage3
    total_unloading = avg_stage4 + avg_stage5
    total_tat = total_loading + total_unloading
    
    active_filters = []
    if tat_filters['client'] != "All Clients": active_filters.append(f"Client: **{selected_tat_client}**")
    if tat_filters['plant'] != "All Plants": active_filters.append(f"Plant: **{tat_filters['plant']}**")
    if tat_filters['destination'] != "All Destinations": active_filters.append(f"Destination: **{tat_filters['destination']}**")
    if tat_filters['date_range'][0] and tat_filters['date_range'][1]: active_filters.append(f"Date: **{tat_filters['date_range'][0]}** to **{tat_filters['date_range'][1]}**")
    if use_trip_filter and tat_filters['trip_nos']: active_filters.append(f"Trip Filter: **{len(tat_filters['trip_nos']):,}** trips")
    
    if active_filters: st.info(f"🔍 **Active Filters:** {' | '.join(active_filters)} | **Unique Trips:** {total_records:,}")
    else: st.info(f"📊 **All Records:** Showing all {total_records:,} unique TAT trips")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1: st.markdown(f'<div class="metric-card"><div class="metric-number">{minutes_to_hhmm(total_loading)}</div><div class="metric-label">⏱️ Avg Loading Time</div></div>', unsafe_allow_html=True)
    with col2: st.markdown(f'<div class="metric-card"><div class="metric-number">{minutes_to_hhmm(total_unloading)}</div><div class="metric-label">⏱️ Avg Unloading Time</div></div>', unsafe_allow_html=True)
    with col3: st.markdown(f'<div class="metric-card"><div class="metric-number">{total_records:,}</div><div class="metric-label">📋 Unique Trips Analyzed</div></div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("### 📈 Detailed TAT Breakdown")
    st.markdown('<div class="tat-container">', unsafe_allow_html=True)
    
    st.markdown('<div class="tat-column"><div class="tat-column-header loading-header">⏱️ LOADING PROCESS (S1+S2+S3)</div><div class="tat-column-body">', unsafe_allow_html=True)
    for stage_name, stage_desc, avg_val in [
        ("DO Receipt", "DO Receipt to Gate Entry", avg_stage1),
        ("Gate In", "Gate Entry to Loading Bay", avg_stage2),
        ("Loading Exit", "Loading Process & Exit", avg_stage3)
    ]:
        st.markdown(f'<div class="tat-stage-row"><div class="stage-info"><div class="stage-name">{stage_name}</div><div class="stage-desc">{stage_desc}</div></div><div class="stage-time"><div class="stage-minutes">{avg_val:.2f} min</div><div class="stage-hhmm">{minutes_to_hhmm(avg_val)}</div></div></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="tat-total-row"><div class="tat-total-label">✅ Total Loading TAT</div><div class="tat-total-time"><div class="tat-total-minutes">{total_loading:.2f} min</div><div class="tat-total-hhmm">{minutes_to_hhmm(total_loading)}</div></div></div>', unsafe_allow_html=True)
    st.markdown('</div></div>', unsafe_allow_html=True)
    
    st.markdown('<div class="tat-column"><div class="tat-column-header unloading-header">⏱️ UNLOADING PROCESS (S4+S5)</div><div class="tat-column-body">', unsafe_allow_html=True)
    for stage_name, stage_desc, avg_val in [
        ("Gate In", "Gate In for Unloading", avg_stage4),
        ("Unloading Exit", "Unloading Process", avg_stage5)
    ]:
        st.markdown(f'<div class="tat-stage-row"><div class="stage-info"><div class="stage-name">{stage_name}</div><div class="stage-desc">{stage_desc}</div></div><div class="stage-time"><div class="stage-minutes">{avg_val:.2f} min</div><div class="stage-hhmm">{minutes_to_hhmm(avg_val)}</div></div></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="tat-total-row"><div class="tat-total-label">✅ Total Unloading TAT</div><div class="tat-total-time"><div class="tat-total-minutes">{total_unloading:.2f} min</div><div class="tat-total-hhmm">{minutes_to_hhmm(total_unloading)}</div></div></div>', unsafe_allow_html=True)
    st.markdown('</div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    loading_hhmm = minutes_to_hhmm(total_loading)
    unloading_hhmm = minutes_to_hhmm(total_unloading)
    total_hhmm = minutes_to_hhmm(total_tat)
    
    st.markdown(f'''
    <div class="grand-total-container">
        <div class="grand-total-content">
            <div class="grand-total-label">🔴 TOTAL TAT (Loading + Unloading)</div>
            <div class="grand-total-time">
                <div class="grand-total-minutes">{total_tat:.2f} min</div>
                <div class="grand-total-hhmm">{total_hhmm}</div>
            </div>
        </div>
        <div class="grand-total-formula">
            Total Loading TAT ({loading_hhmm}) + Total Unloading TAT ({unloading_hhmm}) = <strong>{total_hhmm}</strong>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    if total_tat > 0 and not filtered_tat_df.empty:
        st.markdown("---")
        
        st.markdown("### 📊 Client / Plant TAT Summary")
        st.markdown("**LOADING TAT (S1+S2+S3) | UNLOADING TAT (S4+S5) | TOTAL TAT (Loading + Unloading)**")
        
        summary_df = calculate_client_plant_tat_summary(filtered_tat_df, tat_columns)
        
        if not summary_df.empty:
            has_client = tat_columns['client_col'] and tat_columns['client_col'] in summary_df.columns
            has_plant = tat_columns['plant_col'] and tat_columns['plant_col'] in summary_df.columns
            
            table_html = '<table class="summary-table"><thead>'
            table_html += '<tr class="header-row">'
            if has_client: 
                table_html += '<th rowspan="2" style="min-width:200px;">Client</th>'
            if has_plant: 
                table_html += '<th rowspan="2" style="min-width:150px;">Plant</th>'
            table_html += '<th rowspan="2">No. of<br>Trips</th>'
            table_html += '<th colspan="5" style="background:#1a73e8;">LOADING TAT (S1+S2+S3)</th>'
            table_html += '<th colspan="4" style="background:#34a853;">UNLOADING TAT (S4+S5)</th>'
            table_html += '<th colspan="2" style="background:#d32f2f;">TOTAL TAT<br>(Loading+Unloading)</th>'
            table_html += '</tr>'
            
            table_html += '<tr>'
            table_html += '<th>DO Receipt</th><th>Gate In</th><th>Loading Exit</th>'
            table_html += '<th>Total Loading<br>(min)</th><th>Total Loading<br>(HH:MM)</th>'
            table_html += '<th>Gate In</th><th>Unloading Exit</th>'
            table_html += '<th>Total Unloading<br>(min)</th><th>Total Unloading<br>(HH:MM)</th>'
            table_html += '<th>Total TAT<br>(min)</th><th>Total TAT<br>(HH:MM)</th>'
            table_html += '</tr>'
            table_html += '</thead><tbody>'
            
            for _, row in summary_df.iterrows():
                table_html += '<tr>'
                if has_client: 
                    table_html += f'<td class="client-col">{row[tat_columns["client_col"]]}</td>'
                if has_plant: 
                    table_html += f'<td class="plant-col">{row[tat_columns["plant_col"]]}</td>'
                table_html += f'<td>{int(row["No_of_Trips"])}</td>'
                table_html += f'<td class="loading-cell">{row["Stage1_Avg"]:.1f}<br><small>{row["Stage1_HHMM"]}</small></td>'
                table_html += f'<td class="loading-cell">{row["Stage2_Avg"]:.1f}<br><small>{row["Stage2_HHMM"]}</small></td>'
                table_html += f'<td class="loading-cell">{row["Stage3_Avg"]:.1f}<br><small>{row["Stage3_HHMM"]}</small></td>'
                table_html += f'<td class="loading-cell"><strong>{row["Loading_TAT"]:.1f}</strong></td>'
                table_html += f'<td class="loading-cell">{row["Loading_TAT_HHMM"]}</td>'
                table_html += f'<td class="unloading-cell">{row["Stage4_Avg"]:.1f}<br><small>{row["Stage4_HHMM"]}</small></td>'
                table_html += f'<td class="unloading-cell">{row["Stage5_Avg"]:.1f}<br><small>{row["Stage5_HHMM"]}</small></td>'
                table_html += f'<td class="unloading-cell"><strong>{row["Unloading_TAT"]:.1f}</strong></td>'
                table_html += f'<td class="unloading-cell">{row["Unloading_TAT_HHMM"]}</td>'
                table_html += f'<td class="total-cell"><strong>{row["Total_TAT"]:.1f}</strong></td>'
                table_html += f'<td class="total-cell">{row["Total_TAT_HHMM"]}</td>'
                table_html += '</tr>'
            
            total_trips_count = int(summary_df["No_of_Trips"].sum())
            weighted_s1 = (summary_df["Stage1_Avg"] * summary_df["No_of_Trips"]).sum() / total_trips_count if total_trips_count > 0 else 0
            weighted_s2 = (summary_df["Stage2_Avg"] * summary_df["No_of_Trips"]).sum() / total_trips_count if total_trips_count > 0 else 0
            weighted_s3 = (summary_df["Stage3_Avg"] * summary_df["No_of_Trips"]).sum() / total_trips_count if total_trips_count > 0 else 0
            weighted_s4 = (summary_df["Stage4_Avg"] * summary_df["No_of_Trips"]).sum() / total_trips_count if total_trips_count > 0 else 0
            weighted_s5 = (summary_df["Stage5_Avg"] * summary_df["No_of_Trips"]).sum() / total_trips_count if total_trips_count > 0 else 0
            weighted_load = weighted_s1 + weighted_s2 + weighted_s3
            weighted_unload = weighted_s4 + weighted_s5
            weighted_total = weighted_load + weighted_unload
            
            label_colspan = 0
            if has_client: label_colspan += 1
            if has_plant: label_colspan += 1
            
            table_html += '<tr class="grand-total-row">'
            table_html += f'<td colspan="{label_colspan}" class="grand-total-label">GRAND TOTAL - All Records</td>'
            table_html += f'<td><strong>{total_trips_count}</strong></td>'
            table_html += f'<td class="loading-cell">{weighted_s1:.1f}<br><small>{minutes_to_hhmm(weighted_s1)}</small></td>'
            table_html += f'<td class="loading-cell">{weighted_s2:.1f}<br><small>{minutes_to_hhmm(weighted_s2)}</small></td>'
            table_html += f'<td class="loading-cell">{weighted_s3:.1f}<br><small>{minutes_to_hhmm(weighted_s3)}</small></td>'
            table_html += f'<td class="loading-cell"><strong>{weighted_load:.1f}</strong></td>'
            table_html += f'<td class="loading-cell">{minutes_to_hhmm(weighted_load)}</td>'
            table_html += f'<td class="unloading-cell">{weighted_s4:.1f}<br><small>{minutes_to_hhmm(weighted_s4)}</small></td>'
            table_html += f'<td class="unloading-cell">{weighted_s5:.1f}<br><small>{minutes_to_hhmm(weighted_s5)}</small></td>'
            table_html += f'<td class="unloading-cell"><strong>{weighted_unload:.1f}</strong></td>'
            table_html += f'<td class="unloading-cell">{minutes_to_hhmm(weighted_unload)}</td>'
            table_html += f'<td class="total-cell"><strong>{weighted_total:.1f}</strong></td>'
            table_html += f'<td class="total-cell">{minutes_to_hhmm(weighted_total)}</td>'
            table_html += '</tr>'
            
            table_html += '</tbody></table>'
            st.markdown(table_html, unsafe_allow_html=True)
            
            csv_summary = summary_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Client/Plant TAT Summary (CSV)", data=csv_summary,
                             file_name="client_plant_tat_summary.csv", mime="text/csv")
            
            if has_plant:
                st.markdown("---")
                st.markdown("### 🔍 Plant-wise Detailed TAT Analysis")
                
                plants_in_summary = sorted(summary_df[tat_columns['plant_col']].unique().tolist())
                selected_drill_plant = st.selectbox(
                    "🏭 Select Plant for Detailed View",
                    options=plants_in_summary,
                    key="plant_drilldown_select"
                )
                
                if selected_drill_plant:
                    drilldown_df = get_plant_drilldown_data(
                        filtered_tat_df, tat_columns, selected_drill_plant,
                        client_value=actual_client_name if actual_client_name != "All Clients" else None
                    )
                    
                    if not drilldown_df.empty:
                        st.markdown(f"#### 📋 Trip Details for Plant: **{selected_drill_plant}**")
                        st.markdown(f"*Total unique trips: {len(drilldown_df)}*")
                        st.dataframe(drilldown_df, use_container_width=True, height=400, hide_index=True)
                        
                        csv_drilldown = drilldown_df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            f"📥 Download {selected_drill_plant} Trip Details (CSV)",
                            data=csv_drilldown,
                            file_name=f"plant_drilldown_{selected_drill_plant}.csv",
                            mime="text/csv"
                        )
                    else:
                        st.info(f"No trip details available for plant: {selected_drill_plant}")
        else:
            st.info("Client/Plant columns not available in TAT data for summary table.")


# ── Header ────────────────────────────────────────────────────────────────────
st.title("🚛 Trip Report and TAT Report Analyzer")
st.markdown("Upload one or more monthly trip reports to explore trips by client, plant, and destination.")
st.divider()

col1, col2 = st.columns(2)
with col1:
    st.markdown("### 📂 Trip Reports")
    uploaded_files = st.file_uploader("Upload Trip Report(s) (.xlsx)", type=["xlsx"], accept_multiple_files=True,
                                     help="You can upload multiple monthly reports at once.", key="trip_uploader")
with col2:
    st.markdown("### 📊 TAT Data")
    tat_file = st.file_uploader("Upload TAT Data File (.xlsx)", type=["xlsx"], accept_multiple_files=False,
                               help="Upload the Turnaround Time dataset for standalone analysis.", key="tat_uploader")

st.divider()

has_trip_data = uploaded_files is not None and len(uploaded_files) > 0
has_tat_data = tat_file is not None

if has_trip_data or has_tat_data:
    tab_labels = []
    if has_trip_data: tab_labels.append("🚛 Trip Analysis")
    if has_tat_data: tab_labels.append("📊 TAT Report")
    
    if len(tab_labels) == 2: tab1, tab2 = st.tabs(tab_labels)
    elif len(tab_labels) == 1:
        if tab_labels[0] == "🚛 Trip Analysis": tab1, tab2 = st.container(), None
        else: tab2, tab1 = st.container(), None
else: tab1, tab2 = st.container(), None

df, audit_df, filtered = pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

if has_trip_data:
    files_data = [(f.name, f.read()) for f in uploaded_files]
    result = load_files(files_data)
    df, audit_df = result["df"], result["audit_df"]
    
    for level, text in result["messages"]:
        if level == "warning": st.warning(text)
        elif level == "error": st.error(text)
        else: st.info(text)
    
    if df.empty and not has_tat_data:
        st.error("No valid data could be loaded. Please check your files.")
        st.stop()

df_tat = pd.DataFrame()
if has_tat_data:
    df_tat, tat_error = load_tat_file(tat_file.read())
    if tat_error:
        st.error(f"Could not read TAT file: {tat_error}")
        df_tat = pd.DataFrame()

# ── TAB 1: Trip Analysis ────────────────────────────────────────────────────
if has_trip_data and tab1 is not None:
    with (tab1 if tab2 is not None else st.container()):
        if not audit_df.empty:
            with st.expander(f"🔁 Deduplication Report — {len(audit_df)} trip(s) merged or resolved", expanded=False):
                st.markdown("""
**How duplicates were handled:**
- **Same destination variants** → names standardized, quantities summed.
- **Genuinely different destinations** → leg with highest invoice quantity kept.
""")
                st.dataframe(audit_df, use_container_width=True, hide_index=True)
                st.download_button("📥 Download Deduplication Audit Log (CSV)", data=audit_df.to_csv(index=False).encode("utf-8"),
                                  file_name="deduplication_audit.csv", mime="text/csv")
        
        total_trips_all = len(df)
        loaded_trips_all = len(df[df["Trip Type"] == "Loaded"])
        empty_trips_all = len(df[df["Trip Type"] == "Empty"])
        total_qty_all = df["Inv Qty"].sum()
        
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("Total Trips (All)", f"{total_trips_all:,}")
        with c2: st.metric("Loaded Trips", f"{loaded_trips_all:,}", delta=f"{loaded_trips_all/total_trips_all*100:.1f}%" if total_trips_all else "0%")
        with c3: st.metric("Empty Trips", f"{empty_trips_all:,}", delta=f"{empty_trips_all/total_trips_all*100:.1f}%" if total_trips_all else "0%")
        with c4: st.metric("Total Quantity", f"{total_qty_all:,.2f}")
        
        st.success(f"✅ Loaded **{len(df):,}** unique trip records from **{len(files_data)}** file(s).")
        st.info("💡 **Tip:** Click on any destination in the table to see detailed trip information!")
        
        st.subheader("🔍 Filter Your Data")
        clients = sorted(df["Client"].dropna().unique().tolist())
        regular_clients = [c for c in clients if not c.startswith("EMPTY TRIP")]
        empty_trip_opts = [c for c in clients if c.startswith("EMPTY TRIP")]
        client_options = regular_clients + empty_trip_opts
        
        col1, col2 = st.columns(2)
        with col1: selected_client = st.selectbox("🏢 Select Client", client_options, key="client_select_tab1")
        with col2:
            client_plants = sorted(df[df["Client"] == selected_client]["Plant"].dropna().unique().tolist())
            plant_options = ["All Plants"] + client_plants
            selected_plant_input = st.multiselect("🏭 Select Plant/Source", options=plant_options, default=[],
                                                  placeholder="Pick 'All Plants' to include all…", key="plant_select_tab1")
            selected_plants = client_plants if (not selected_plant_input or "All Plants" in selected_plant_input) else selected_plant_input
            if not selected_plants:
                st.warning("⚠️ No plants found for this client.")
                if not has_tat_data: st.stop()
        
        col3, col4, col5 = st.columns(3)
        with col3:
            months = sorted(df["Month"].dropna().unique().tolist(), reverse=True)
            selected_month = st.selectbox("📅 Select Month", ["All Months"] + months, key="month_select_tab1")
        with col4:
            trip_type_opts = ["All Types"] + sorted(df["Trip Type"].dropna().unique().tolist())
            selected_type = st.selectbox("🔄 Trip Type", trip_type_opts, key="type_select_tab1")
        with col5:
            if st.button("🗑️ Clear All Filters", use_container_width=True, key="clear_tab1"): st.rerun()
        
        st.divider()
        
        filtered = df[df["Client"] == selected_client].copy()
        if selected_plants: filtered = filtered[filtered["Plant"].isin(selected_plants)]
        if selected_month != "All Months": filtered = filtered[filtered["Month"] == selected_month]
        if selected_type != "All Types": filtered = filtered[filtered["Trip Type"] == selected_type]
        
        total_trips = len(filtered)
        loaded_trips = len(filtered[filtered["Trip Type"] == "Loaded"])
        empty_trips = len(filtered[filtered["Trip Type"] == "Empty"])
        unique_dest = filtered["Destination"].nunique()
        unique_plants = filtered["Plant"].nunique()
        total_qty = filtered["Inv Qty"].sum()
        
        st.caption(f"📌 **Selected Plants ({len(selected_plants)}):** {', '.join(selected_plants[:5])}{'...' if len(selected_plants) > 5 else ''}")
        
        def _card(col, val, label):
            with col: st.markdown(f'<div class="metric-card"><div class="metric-number">{val}</div><div class="metric-label">{label}</div></div>', unsafe_allow_html=True)
        
        if selected_client.startswith("EMPTY TRIP"):
            cols = st.columns(5)
            pairs = zip(cols, [f"{total_trips:,}", unique_dest, unique_plants, f"{total_qty:,.2f}"],
                       ["Total Empty Trips","Unique Destinations","Source Plants","Total Quantity"])
        else:
            cols = st.columns(6)
            pairs = zip(cols, [f"{total_trips:,}", loaded_trips, empty_trips, unique_dest, unique_plants, f"{total_qty:,.2f}"],
                       ["Total Trips","Loaded Trips","Empty Trips","Unique Destinations","Plants/Sources","Total Quantity"])
        for c, v, l in pairs: _card(c, v, l)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if selected_client.startswith("EMPTY TRIP"): st.subheader("📍 Empty Trip Destinations")
        else: st.subheader(f"📍 Trips to Each Destination — {selected_client}")
        st.caption("💡 **Click the 🔍 button** to see detailed trip information")
        
        if filtered.empty: st.info("No trips found for the selected filters.")
        else:
            agg_dict = {"Total_Trips": ("Trip No", "count"), "Total_Qty": ("Inv Qty", "sum"), "Plants": ("Plant", lambda x: x.nunique())}
            if "Trip Type" in filtered.columns and filtered["Trip Type"].nunique() > 1:
                agg_dict["Loaded_Trips"] = ("Trip Type", lambda x: (x == "Loaded").sum())
                agg_dict["Empty_Trips"] = ("Trip Type", lambda x: (x == "Empty").sum())
            
            dest_summary = (filtered.groupby("Destination").agg(**agg_dict).reset_index()
                           .sort_values("Total_Trips", ascending=False)
                           .rename(columns={"Total_Trips": "Total Trips", "Total_Qty": "Total Quantity",
                                           "Plants": "Plants Used", "Loaded_Trips": "Loaded Trips", "Empty_Trips": "Empty Trips"}))
            
            chart_type = st.radio("📊 Display Chart Type", ["Total Trips", "Total Quantity"], horizontal=True)
            
            if chart_type == "Total Trips":
                fig = px.bar(dest_summary.head(20), x="Destination", y="Total Trips", title="Top 20 Destinations by Trip Count",
                            color="Total Trips", color_continuous_scale="Blues", text="Total Trips")
            else:
                fig = px.bar(dest_summary.head(20), x="Destination", y="Total Quantity", title="Top 20 Destinations by Total Quantity",
                            color="Total Quantity", color_continuous_scale="Greens", text="Total Quantity")
                fig.update_traces(texttemplate="%{text:,.2f}")
            fig.update_traces(textposition="outside")
            fig.update_layout(xaxis_tickangle=-45, height=500)
            
            chart_col, table_col = st.columns([1, 1])
            with chart_col: st.plotly_chart(fig, use_container_width=True)
            with table_col:
                st.markdown("#### 📋 Destinations Summary")
                for idx, row in dest_summary.iterrows():
                    destination = row["Destination"]
                    c1, c2, c3, c4, c5 = st.columns([0.4, 0.15, 0.15, 0.2, 0.1])
                    with c1: st.write(f"**{destination}**")
                    with c2: st.write(f"{row['Total Trips']} trips")
                    with c3: st.write(f"📦 {row['Total Quantity']:,.2f}")
                    with c4:
                        if "Loaded Trips" in row: st.write(f"🟢 {row['Loaded Trips']} / 🔴 {row['Empty Trips']}")
                    with c5:
                        if st.button("🔍", key=f"drill_{destination}_{idx}"):
                            show_trip_details(destination, filtered[filtered["Destination"] == destination].copy())
            
            st.divider()
            export_buf = BytesIO()
            with pd.ExcelWriter(export_buf, engine="openpyxl") as writer:
                dest_summary.to_excel(writer, sheet_name="Destination Summary", index=False)
                filtered.to_excel(writer, sheet_name="Raw Trips", index=False)
                if not audit_df.empty: audit_df.to_excel(writer, sheet_name="Dedup Audit Log", index=False)
            export_buf.seek(0)
            st.download_button(label="⬇️ Download Summary as Excel", data=export_buf,
                             file_name=f"trip_summary.xlsx",
                             mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ── TAB 2: TAT Report ──────────────────────────────────────────────────────
if has_tat_data and tab2 is not None:
    with (tab2 if has_trip_data and has_tat_data else st.container()):
        if df_tat.empty: st.warning("⚠️ The TAT file could not be processed. Please check the file format and required columns.")
        else:
            trip_filter = None
            if has_trip_data and not filtered.empty and "Trip No" in filtered.columns:
                trip_filter = filtered["Trip No"].unique().tolist()
            render_tat_report(df_tat, {'trip_nos': trip_filter} if trip_filter else None)

# ── No data message ──────────────────────────────────────────────────────────
if not has_trip_data and not has_tat_data:
    st.markdown("""
    <div style="text-align:center; padding: 60px 20px; color: #888;">
        <div style="font-size:4rem;">📂</div>
        <h3 style="color:#555;">No file uploaded yet</h3>
        <p>Upload your files above to get started.</p>
    </div>
    """, unsafe_allow_html=True)
