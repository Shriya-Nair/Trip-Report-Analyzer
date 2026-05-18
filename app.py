import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
import plotly.express as px
import plotly.graph_objects as go
from difflib import SequenceMatcher
from datetime import datetime
import re
from typing import Dict, List, Tuple, Optional, Any
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="Trip & TAT Analytics Suite | Logistics Performance Dashboard",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===================================================================================
# PROFESSIONAL STYLING - Sophisticated Industry-Standard Design
# ===================================================================================

st.markdown("""
<style>
    /* Import modern fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    * { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }
    
    .main { 
        background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
    }
    
    .stApp { 
        font-family: 'Inter', sans-serif;
    }
    
    /* Glass-morphism cards */
    .metric-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(255,255,255,0.85) 100%);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 24px 20px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.06), 0 2px 8px rgba(0, 0, 0, 0.04);
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.8);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px 20px 0 0;
    }
    
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.1), 0 4px 12px rgba(0, 0, 0, 0.06);
    }
    
    .metric-number { 
        font-size: 2.4rem; 
        font-weight: 800; 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        line-height: 1.2;
    }
    
    .metric-label { 
        font-size: 0.85rem; 
        color: #6b7280; 
        margin-top: 8px; 
        font-weight: 500;
        letter-spacing: 0.025em;
    }
    
    /* Filter sections */
    .filter-section {
        background: linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(255,255,255,0.9) 100%);
        backdrop-filter: blur(10px);
        padding: 24px;
        border-radius: 20px;
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06), 0 1px 4px rgba(0, 0, 0, 0.04);
        margin-bottom: 24px;
        border: 1px solid rgba(255, 255, 255, 0.8);
    }
    
    /* TAT Stage Rows */
    .tat-stage-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 14px 16px;
        border-bottom: 1px solid #f0f0f0;
        transition: all 0.2s ease;
        border-radius: 8px;
        margin: 4px 0;
    }
    
    .tat-stage-row:hover {
        background: linear-gradient(90deg, #f8f9ff 0%, #f0f4ff 100%);
        transform: translateX(4px);
    }
    
    .tat-total-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px 20px;
        margin-top: 8px;
        background: linear-gradient(135deg, #e8f0fe 0%, #dbe4ff 100%);
        border-radius: 12px;
        border: 1px solid #b8c9ff;
    }
    
    .grand-total-container {
        background: linear-gradient(135deg, #fff5f5 0%, #ffe0e0 100%);
        border-radius: 20px;
        padding: 28px 32px;
        margin: 24px 0;
        border: 2px solid #ffcdd2;
        box-shadow: 0 8px 32px rgba(255, 82, 82, 0.1);
        position: relative;
        overflow: hidden;
    }
    
    .grand-total-container::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,82,82,0.05) 0%, transparent 50%);
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); opacity: 0.5; }
        50% { transform: scale(1.1); opacity: 0.3; }
        100% { transform: scale(1); opacity: 0.5; }
    }
    
    /* Buttons styling */
    .stButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.6rem 1.4rem;
        font-weight: 600;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        letter-spacing: 0.025em;
        box-shadow: 0 4px 16px rgba(102, 126, 234, 0.3);
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    }
    
    /* Table styling */
    .stDataFrame {
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #f8f9ff 0%, #e8ecf1 100%);
        border-radius: 12px;
        font-weight: 600;
        border: 1px solid #e0e4e8;
    }
    
    /* Title styling */
    h1 {
        font-weight: 800;
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 2.5rem;
        letter-spacing: -0.025em;
    }
    
    h2, h3 {
        font-weight: 700;
        letter-spacing: -0.015em;
    }
    
    /* Destination table styling */
    .dest-row {
        display: flex;
        align-items: center;
        padding: 12px 16px;
        margin: 6px 0;
        background: white;
        border-radius: 12px;
        border: 1px solid #e8eaed;
        transition: all 0.2s ease;
    }
    
    .dest-row:hover {
        background: linear-gradient(90deg, #f8f9ff 0%, #f0f4ff 100%);
        border-color: #667eea;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.1);
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: linear-gradient(135deg, rgba(255,255,255,0.9) 0%, rgba(248,249,255,0.9) 100%);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 8px;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 12px;
        padding: 10px 20px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        box-shadow: 0 4px 16px rgba(102, 126, 234, 0.3);
    }
    
    /* Chart containers */
    .js-plotly-plot {
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    }
    
    section[data-testid="stSidebar"] * {
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# ===================================================================================
# CONSTANTS & CONFIGURATION
# ===================================================================================

PREDEFINED_CLIENTS = [
    "ARCELORMITTAL NIPPON STEEL INDIA LIMITED",
    "Dalmia Cement (Bharat)Limited",
    "Hindustan Zinc Limited",
    "Jindal Steel and Power Limited",
    "JSW Steel Limited",
    "TATA STEEL LIMITED CHENNAI",
    "TATA STEEL LIMITED"
]

COLUMN_MAPPING_CONFIG = {
    "trip_report": {
        "trip_no": ["Trip No", "Trip Number", "TripID", "Trip Id", "Trip_No"],
        "client": ["Client", "Customer Name", "Customer", "Client Name"],
        "plant": ["Plant", "Source", "Origin", "Source Plant", "From", "Source Place"],
        "destination": ["Destination", "Delivery Location", "Unloading Point", "To"],
        "trip_type": ["Trip Type", "Trip Category", "Type"],
        "inv_qty": ["Inv Qty", "Invoice Quantity", "Quantity", "Qty"],
        "date": ["Start Date", "Trip Date", "Date", "Transaction Date"]
    },
    "tat_data": {
        "trip_no": ["Trip No", "Trip Number", "TripID", "Trip Id"],
        "client": ["Client", "Customer Name", "Customer"],
        "plant": ["Plant", "Source Plant", "Origin Plant", "Source", "Source Place", "Origin"],
        "destination": ["Destination", "Unloading Point"],
        "do_receipt": ["Actual DO Receipt (Mins)", "DO Receipt (Mins)", "DO Receipt"],
        "gate_in_load": ["Actual Gate In(Mins)", "Gate In (Mins)", "Gate In"],
        "loaded_exit": ["Actual Loaded Exit(Mins)", "Loaded Exit (Mins)", "Loaded Exit"],
        "gate_in_unload": ["Actual Gate In for Unloading(Mins)", "Gate In Unloading"],
        "unloaded": ["Actual Unloaded (Mins)", "Unloaded (Mins)"],
        "date": ["Date", "Transaction Date"]
    }
}

# ===================================================================================
# HELPER FUNCTIONS
# ===================================================================================

def minutes_to_hhmm(minutes: float) -> str:
    if pd.isna(minutes) or minutes < 0:
        return "00:00"
    hours = int(minutes // 60)
    mins = int(minutes % 60)
    return f"{hours:02d}:{mins:02d}"

def normalize_text(series: pd.Series) -> pd.Series:
    return (series
        .astype(str)
        .str.upper()
        .str.strip()
        .str.replace(r'\s+', ' ', regex=True)
        .str.replace(r'[^\w\s-]', '', regex=True)
        .replace('NAN', 'UNKNOWN')
        .replace('', 'UNKNOWN')
    )

def clean_trip_no(series: pd.Series) -> pd.Series:
    """Clean and standardize Trip No for deduplication"""
    return (series
        .astype(str)
        .str.strip()
        .str.upper()
        .str.replace(r'\.0$', '', regex=True)
        .str.replace(r'^0+', '', regex=True)
    )

def detect_columns(df: pd.DataFrame, data_type: str) -> Dict[str, str]:
    detected = {}
    config = COLUMN_MAPPING_CONFIG[data_type]
    
    for target, possibilities in config.items():
        found = None
        for col in df.columns:
            col_normalized = col.lower().strip()
            for poss in possibilities:
                if poss.lower() == col_normalized:
                    found = col
                    break
            if found:
                break
        detected[target] = found
    
    return detected

def validate_date_parsing(df: pd.DataFrame, date_col: str) -> Tuple[pd.Series, List[str]]:
    if date_col not in df.columns:
        return pd.Series([pd.NaT] * len(df)), ["Date column not found"]
    
    errors = []
    date_series = pd.Series([pd.NaT] * len(df))
    
    formats = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y', '%d.%m.%Y']
    
    for fmt in formats:
        try:
            parsed = pd.to_datetime(df[date_col], format=fmt, errors='coerce')
            if parsed.notna().sum() > date_series.notna().sum():
                date_series = parsed
        except:
            continue
    
    if date_series.isna().all():
        date_series = pd.to_datetime(df[date_col], errors='coerce')
    
    error_count = date_series.isna().sum()
    if error_count > 0:
        errors.append(f"{error_count} dates could not be parsed")
    
    return date_series, errors

# ===================================================================================
# DESTINATION NAME FUZZY MATCHING HELPERS
# ===================================================================================

def _normalize_name(name: str) -> str:
    name = str(name).lower().strip()
    name = re.sub(r"[^\w\s]", "", name)
    name = re.sub(r"\s+", " ", name)
    return name

def _similar(a: str, b: str, threshold: float = 0.82) -> bool:
    na, nb = _normalize_name(a), _normalize_name(b)
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

# ===================================================================================
# DEDUPLICATION FUNCTION - With Aggregation
# ===================================================================================

def deduplicate_trip_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    DEDUPLICATION WITH AGGREGATION: Group by Trip No and aggregate.
    Sums inv_qty to preserve cargo quantities, keeps first value for all other columns.
    Also handles destination name standardization.
    """
    df = df.copy()
    
    if 'trip_no' not in df.columns:
        st.warning("No 'trip_no' column found for deduplication")
        return df, pd.DataFrame()
    
    # Apply destination alias mapping
    if 'destination' in df.columns:
        alias_map = _build_destination_alias_map(df['destination'].fillna('Unknown'))
        df['destination'] = df['destination'].map(lambda d: alias_map.get(d, d))
    
    original_count = len(df)
    original_unique = df['trip_no'].nunique()
    
    # Clean and normalize Trip No for comparison
    df['trip_no_clean'] = clean_trip_no(df['trip_no'])
    
    # Find duplicates
    duplicate_mask = df.duplicated(subset=['trip_no_clean'], keep=False)
    
    # Build aggregation dictionary
    agg_dict = {}
    for col in df.columns:
        if col == 'trip_no_clean':
            continue
        elif col == 'inv_qty':
            agg_dict[col] = 'sum'
        else:
            agg_dict[col] = 'first'
    
    # Group by cleaned trip number and aggregate
    deduplicated_df = df.groupby('trip_no_clean', as_index=False).agg(agg_dict)
    
    new_count = len(deduplicated_df)
    new_unique = deduplicated_df['trip_no_clean'].nunique()
    removed_count = original_count - new_count
    
    # Create audit log
    audit_records = []
    
    if removed_count > 0:
        duplicate_trips = df[duplicate_mask]
        
        for trip_no_clean, group in duplicate_trips.groupby('trip_no_clean'):
            original_trip_no = group['trip_no'].iloc[0]
            destinations = group['destination'].dropna().unique().tolist() if 'destination' in group.columns else []
            total_qty_before = group['inv_qty'].sum() if 'inv_qty' in group.columns else 0
            merged_row = deduplicated_df[deduplicated_df['trip_no_clean'] == trip_no_clean]
            qty_after = merged_row['inv_qty'].iloc[0] if 'inv_qty' in merged_row.columns and not merged_row.empty else 0
            
            audit_records.append({
                'Trip_No': original_trip_no,
                'Total_Occurrences': len(group),
                'Destinations': '; '.join(destinations) if destinations else 'N/A',
                'Rows_Kept': 1,
                'Rows_Removed': len(group) - 1,
                'Qty_Total': total_qty_before,
                'Qty_Merged': qty_after
            })
    
    # Drop temporary column
    deduplicated_df = deduplicated_df.drop(columns=['trip_no_clean'])
    
    audit_df = pd.DataFrame(audit_records) if audit_records else pd.DataFrame()
    
    # Store dedup stats for display
    st.session_state.dedup_stats = {
        'original_rows': original_count,
        'original_unique_trips': original_unique,
        'new_rows': new_count,
        'new_unique_trips': new_unique,
        'rows_removed': removed_count
    }
    
    return deduplicated_df, audit_df

# ===================================================================================
# CLIENT-PLANT ASSOCIATION
# ===================================================================================

class ClientPlantAssociation:
    def __init__(self):
        self.client_plant_map = {}
        self.plant_client_map = {}
        self.association_df = pd.DataFrame()
    
    def build_from_tat_data(self, tat_df: pd.DataFrame):
        if tat_df.empty:
            return
        
        df = tat_df.copy()
        
        if 'client' not in df.columns or 'plant' not in df.columns:
            return
        
        associations = df[['client', 'plant']].drop_duplicates()
        
        for _, row in associations.iterrows():
            client = row['client']
            plant = row['plant']
            
            if client not in self.client_plant_map:
                self.client_plant_map[client] = set()
            self.client_plant_map[client].add(plant)
            
            if plant not in self.plant_client_map:
                self.plant_client_map[plant] = set()
            self.plant_client_map[plant].add(client)
        
        self.association_df = associations.copy()
        self.association_df.columns = ['Client', 'Plant (from TAT Source)']
        
        trip_counts = df.groupby(['client', 'plant']).size().reset_index(name='Trip Count')
        self.association_df = self.association_df.merge(
            trip_counts, 
            left_on=['Client', 'Plant (from TAT Source)'], 
            right_on=['client', 'plant'], 
            how='left'
        )
        self.association_df = self.association_df.drop(columns=['client', 'plant'])
    
    def get_plants_for_client(self, client: str) -> List[str]:
        if client in self.client_plant_map:
            return sorted(list(self.client_plant_map[client]))
        return []
    
    def render_association_summary(self):
        if self.association_df.empty:
            st.info("No client-plant associations found.")
            return
        
        st.markdown("### 🔗 Client-Plant Associations (from TAT Source Column)")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Clients", len(self.client_plant_map))
        with col2:
            st.metric("Total Plants/Sources", len(self.plant_client_map))
        with col3:
            st.metric("Client-Plant Pairs", len(self.association_df))
        
        with st.expander("📋 View All Client-Plant Associations", expanded=False):
            st.dataframe(self.association_df, use_container_width=True, hide_index=True)

# ===================================================================================
# DATA LOADING FUNCTIONS
# ===================================================================================

def load_trip_reports(files_data: List[Tuple[str, bytes]]) -> Dict[str, Any]:
    messages = []
    all_frames = []
    
    for filename, data in files_data:
        try:
            df = pd.read_excel(BytesIO(data), sheet_name=0)
            detected_cols = detect_columns(df, "trip_report")
            
            required = ['trip_no', 'client', 'destination']
            missing = [r for r in required if not detected_cols.get(r)]
            
            if missing:
                messages.append({
                    "type": "warning",
                    "text": f"⚠️ **{filename}** missing columns: {missing}. Skipping."
                })
                continue
            
            rename_map = {v: k for k, v in detected_cols.items() if v}
            df = df.rename(columns=rename_map)
            
            # ── REMOVE ONGOING TRIPS ──────────────────────────────────────────
            rows_before_status_filter = len(df)
            
            # Check for Trip Status column (try multiple possible names)
            status_col = None
            for possible_col in ['Trip Status', 'Status', 'trip_status', 'TripStatus']:
                if possible_col in df.columns:
                    status_col = possible_col
                    break
            
            if status_col:
                # Filter out ongoing trips
                df = df[
                    ~df[status_col].astype(str).str.upper().str.strip().isin([
                        'ONGOING', 'IN PROGRESS', 'IN-PROGRESS', 'PENDING', 
                        'NOT COMPLETED', 'ACTIVE', 'RUNNING'
                    ])
                ]
                rows_removed = rows_before_status_filter - len(df)
                if rows_removed > 0:
                    messages.append({
                        "type": "info", 
                        "text": f"🔧 **{filename}**: Removed {rows_removed:,} ongoing/in-progress trips"
                    })
            else:
                # No status column found, just note it
                messages.append({
                    "type": "info",
                    "text": f"ℹ️ **{filename}**: No 'Trip Status' column found, skipping ongoing trip filter"
                })
            # ───────────────────────────────────────────────────────────────────
            
            if detected_cols.get('date'):
                df['date_parsed'], date_errors = validate_date_parsing(df, 'date')
                if date_errors:
                    messages.append({"type": "info", "text": f"📅 **{filename}**: {date_errors[0]}"})
            else:
                df['date_parsed'] = pd.NaT
            
            if 'inv_qty' not in df.columns:
                df['inv_qty'] = 0.0
            else:
                df['inv_qty'] = pd.to_numeric(df['inv_qty'], errors='coerce').fillna(0)
            
            if 'trip_type' not in df.columns:
                df['trip_type'] = 'Loaded'
            else:
                df['trip_type'] = df['trip_type'].astype(str).str.title()
            
            if 'plant' not in df.columns:
                df['plant'] = 'UNKNOWN_PLANT'
            else:
                df['plant'] = normalize_text(df['plant'])
            
            df['client'] = normalize_text(df['client'])
            df['destination'] = normalize_text(df['destination'])
            df['trip_no'] = clean_trip_no(df['trip_no'])
            
            empty_mask = df['trip_type'].str.lower() == 'empty'
            df.loc[empty_mask & (df['client'] == 'UNKNOWN'), 'client'] = 'EMPTY_TRIP'
            
            df['_source_file'] = filename
            df['Source File'] = filename
            all_frames.append(df)
            
            messages.append({
                "type": "success",
                "text": f"✅ Loaded **{filename}**: {len(df):,} records (after filtering)"
            })
            
        except Exception as e:
            messages.append({"type": "error", "text": f"❌ Could not read **{filename}**: {str(e)}"})
    
    if not all_frames:
        return {"df": pd.DataFrame(), "audit_df": pd.DataFrame(), "messages": messages}
    
    combined = pd.concat(all_frames, ignore_index=True)
    
    rows_before = len(combined)
    unique_before = combined['trip_no'].nunique()
    
    # Apply deduplication
    combined, audit_df = deduplicate_trip_data(combined)
    
    rows_after = len(combined)
    unique_after = combined['trip_no'].nunique()
    
    combined['month'] = combined['date_parsed'].dt.to_period('M').astype(str)
    
    messages.append({
        "type": "success",
        "text": f"📊 Deduplication: {rows_before:,} → {rows_after:,} records ({rows_before - rows_after:,} duplicates removed)"
    })
    
    messages.append({
        "type": "info",
        "text": f"📊 Unique Trip Nos: {unique_before:,} → {unique_after:,}"
    })
    
    return {"df": combined, "audit_df": audit_df, "messages": messages}

def load_tat_data(file_data: bytes) -> Tuple[pd.DataFrame, Dict, List[str], ClientPlantAssociation]:
    try:
        df = pd.read_excel(BytesIO(file_data), sheet_name=0)
        detected_cols = detect_columns(df, "tat_data")
        
        messages = []
        
        required = ['trip_no', 'client']
        missing = [r for r in required if not detected_cols.get(r)]
        
        if missing:
            return pd.DataFrame(), detected_cols, [f"Missing required columns: {missing}"], ClientPlantAssociation()
        
        rename_map = {v: k for k, v in detected_cols.items() if v}
        df = df.rename(columns=rename_map)
        
        df['client'] = normalize_text(df['client'])
        df['trip_no'] = clean_trip_no(df['trip_no'])
        
        if 'plant' in df.columns:
            df['plant'] = normalize_text(df['plant'])
        else:
            df['plant'] = 'UNKNOWN_SOURCE'
        
        if 'destination' in df.columns:
            df['destination'] = normalize_text(df['destination'])
        else:
            df['destination'] = 'UNKNOWN'
        
        if detected_cols.get('date'):
            df['date_parsed'], date_errors = validate_date_parsing(df, 'date')
            if date_errors:
                messages.append(date_errors[0])
        else:
            df['date_parsed'] = pd.NaT
        
        # TAT DEDUPLICATION: Keep only first occurrence of each trip
        rows_before = len(df)
        df = df.drop_duplicates(subset=['trip_no'], keep='first')
        rows_after = len(df)
        
        if rows_before > rows_after:
            messages.append(f"TAT Dedup: {rows_before:,} → {rows_after:,} records ({rows_before - rows_after:,} duplicates removed)")
        
        stage_columns = ['do_receipt', 'gate_in_load', 'loaded_exit', 
                        'gate_in_unload', 'unloaded']
        
        for stage in stage_columns:
            if stage in df.columns:
                df[stage] = pd.to_numeric(df[stage], errors='coerce')
            else:
                df[stage] = np.nan
        
        df['loading_tat'] = df['do_receipt'] + df['gate_in_load'] + df['loaded_exit']
        df['unloading_tat'] = df['gate_in_unload'] + df['unloaded']
        df['total_tat'] = df['loading_tat'] + df['unloading_tat']
        
        association = ClientPlantAssociation()
        association.build_from_tat_data(df)
        
        return df, detected_cols, messages, association
        
    except Exception as e:
        return pd.DataFrame(), {}, [f"Error: {str(e)}"], ClientPlantAssociation()

# ===================================================================================
# TAT PROCESSING FUNCTIONS
# ===================================================================================

def apply_tat_filters(df: pd.DataFrame, filters: Dict) -> pd.DataFrame:
    if df.empty:
        return df
    
    df_filtered = df.copy()
    
    if filters.get('trip_nos'):
        trip_nos_norm = [clean_trip_no(pd.Series([t]))[0] for t in filters['trip_nos']]
        df_filtered = df_filtered[df_filtered['trip_no'].isin(trip_nos_norm)]
    
    if filters.get('client_names') and len(filters['client_names']) > 0:
        client_norm = [normalize_text(pd.Series([c]))[0] for c in filters['client_names']]
        df_filtered = df_filtered[df_filtered['client'].isin(client_norm)]
    
    if filters.get('plant') and filters['plant'] not in ['All Plants/Sources', None]:
        plant_norm = normalize_text(pd.Series([filters['plant']]))[0]
        df_filtered = df_filtered[df_filtered['plant'] == plant_norm]
    
    if filters.get('destination') and filters['destination'] not in ['All Destinations', None]:
        dest_norm = normalize_text(pd.Series([filters['destination']]))[0]
        df_filtered = df_filtered[df_filtered['destination'] == dest_norm]
    
    if filters.get('date_range'):
        start_date, end_date = filters['date_range']
        if start_date and end_date:
            df_filtered = df_filtered[
                (df_filtered['date_parsed'] >= pd.Timestamp(start_date)) &
                (df_filtered['date_parsed'] <= pd.Timestamp(end_date))
            ]
    
    return df_filtered

def calculate_tat_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    
    summary = df.groupby(['client', 'plant'], as_index=False).agg(
        total_trips=('client', 'count'),
        s1_mean=('do_receipt', lambda x: x.mean(skipna=True)),
        s2_mean=('gate_in_load', lambda x: x.mean(skipna=True)),
        s3_mean=('loaded_exit', lambda x: x.mean(skipna=True)),
        s4_mean=('gate_in_unload', lambda x: x.mean(skipna=True)),
        s5_mean=('unloaded', lambda x: x.mean(skipna=True)),
        loading_tat_mean=('loading_tat', lambda x: x.mean(skipna=True)),
        unloading_tat_mean=('unloading_tat', lambda x: x.mean(skipna=True)),
        total_tat_mean=('total_tat', lambda x: x.mean(skipna=True)),
    )
    
    # Add HH:MM formatted columns
    summary['S1_HHMM'] = summary['s1_mean'].apply(minutes_to_hhmm)
    summary['S2_HHMM'] = summary['s2_mean'].apply(minutes_to_hhmm)
    summary['S3_HHMM'] = summary['s3_mean'].apply(minutes_to_hhmm)
    summary['S4_HHMM'] = summary['s4_mean'].apply(minutes_to_hhmm)
    summary['S5_HHMM'] = summary['s5_mean'].apply(minutes_to_hhmm)
    summary['loading_tat_hhmm'] = summary['loading_tat_mean'].apply(minutes_to_hhmm)
    summary['unloading_tat_hhmm'] = summary['unloading_tat_mean'].apply(minutes_to_hhmm)
    summary['total_tat_hhmm'] = summary['total_tat_mean'].apply(minutes_to_hhmm)
    
    # Round numeric columns
    for col in ['s1_mean', 's2_mean', 's3_mean', 's4_mean', 's5_mean',
                'loading_tat_mean', 'unloading_tat_mean', 'total_tat_mean']:
        summary[col] = summary[col].round(1)
    
    return summary.sort_values('total_tat_mean')

def get_plant_drilldown(df: pd.DataFrame, plant: str, client: str = None) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    
    plant_norm = normalize_text(pd.Series([plant]))[0]
    df_filtered = df[df['plant'] == plant_norm]
    
    if client and client != 'All Clients':
        client_norm = normalize_text(pd.Series([client]))[0]
        df_filtered = df_filtered[df_filtered['client'] == client_norm]
    
    if df_filtered.empty:
        return pd.DataFrame()
    
    display_cols = ['trip_no', 'client', 'plant', 'destination', 'date_parsed']
    display_cols += ['do_receipt', 'gate_in_load', 'loaded_exit', 
                    'gate_in_unload', 'unloaded']
    display_cols += ['loading_tat', 'unloading_tat', 'total_tat']
    
    result = df_filtered[display_cols].copy()
    
    for col in ['do_receipt', 'gate_in_load', 'loaded_exit',
                'gate_in_unload', 'unloaded', 'loading_tat', 'unloading_tat', 'total_tat']:
        if col in result.columns:
            result[f'{col}_hhmm'] = result[col].apply(minutes_to_hhmm)
    
    result = result.rename(columns={'plant': 'Plant/Source (from TAT)'})
    
    return result

# ===================================================================================
# UI COMPONENTS
# ===================================================================================

def render_metric_card(value: str, label: str):
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-number">{value}</div>
            <div class="metric-label">{label}</div>
        </div>
    """, unsafe_allow_html=True)

# ===================================================================================
# DESTINATION DRILL-DOWN MODAL
# ===================================================================================

@st.dialog("📋 Trip Details", width="large")
def show_trip_details(destination, trips_df):
    st.markdown(f"### 🚛 Trips to **{destination}**")
    
    total_qty = trips_df['inv_qty'].sum() if 'inv_qty' in trips_df.columns else 0
    plants_used = trips_df['plant'].nunique() if 'plant' in trips_df.columns else 0
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Trips", len(trips_df))
    with col2:
        if 'trip_type' in trips_df.columns:
            loaded_count = len(trips_df[trips_df['trip_type'] == 'Loaded'])
            st.metric("Loaded Trips", loaded_count)
        else:
            st.metric("Loaded Trips", "N/A")
    with col3:
        st.metric("Plants Used", plants_used)
    with col4:
        st.metric("Total Quantity", f"{total_qty:,.2f}")
    
    st.divider()
    st.subheader("📊 Detailed Trip List")
    
    display_cols = ['trip_no', 'date_parsed', 'trip_type', 'client', 'plant', 'inv_qty', 'Source File']
    available_cols = [col for col in display_cols if col in trips_df.columns]
    
    # Rename columns for display
    display_df = trips_df[available_cols].copy()
    display_df.columns = [col.replace('_', ' ').title() for col in display_df.columns]
    
    st.dataframe(display_df, use_container_width=True, height=400, hide_index=True)
    
    csv = display_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download CSV", 
        data=csv, 
        file_name=f"trips_to_{destination}.csv", 
        mime="text/csv"
    )

# ===================================================================================
# TAT REPORT
# ===================================================================================

def render_tat_report(tat_df: pd.DataFrame, association: ClientPlantAssociation, trip_filters: Dict = None):
    st.subheader("📊 Turnaround Time (TAT) Analysis")
    
    if tat_df.empty:
        st.warning("No TAT data available.")
        return
    
    association.render_association_summary()
    st.markdown("---")
    
    # Get available clients (only predefined ones that exist in data)
    all_clients_in_data = tat_df['client'].dropna().unique().tolist()
    available_clients = []
    
    for predefined in PREDEFINED_CLIENTS:
        predefined_norm = normalize_text(pd.Series([predefined]))[0]
        if predefined_norm in all_clients_in_data:
            available_clients.append(predefined)
    
    with st.expander("🔍 Filter TAT Data", expanded=True):
        st.markdown('<div class="filter-section">', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            selected_client = st.selectbox("🏢 Client", ["All Clients"] + available_clients, key="tat_client")
        
        with col2:
            if selected_client != "All Clients":
                client_norm = normalize_text(pd.Series([selected_client]))[0]
                associated_plants = association.get_plants_for_client(client_norm)
                plant_options = ["All Plants/Sources"] + associated_plants if associated_plants else ["All Plants/Sources"]
            else:
                all_plants = sorted(tat_df['plant'].dropna().unique().tolist())
                plant_options = ["All Plants/Sources"] + all_plants
            
            selected_plant = st.selectbox("🏭 Plant/Source", plant_options, key="tat_plant")
        
        with col3:
            temp_df = tat_df
            if selected_client != "All Clients":
                client_norm = normalize_text(pd.Series([selected_client]))[0]
                temp_df = temp_df[temp_df['client'] == client_norm]
            if selected_plant != "All Plants/Sources":
                plant_norm = normalize_text(pd.Series([selected_plant]))[0]
                temp_df = temp_df[temp_df['plant'] == plant_norm]
            
            dest_options = ["All Destinations"] + sorted(temp_df['destination'].dropna().unique().tolist())
            selected_dest = st.selectbox("📍 Destination", dest_options, key="tat_dest")
        
        col1, col2 = st.columns(2)
        
        with col1:
            min_date = tat_df['date_parsed'].min().date() if tat_df['date_parsed'].notna().any() else None
            max_date = tat_df['date_parsed'].max().date() if tat_df['date_parsed'].notna().any() else None
            
            if min_date and max_date:
                date_range = st.date_input("📅 Date Range", value=(min_date, max_date), key="tat_date")
            else:
                date_range = (None, None)
        
        with col2:
            link_trips = st.checkbox("🔗 Link with Trip Analysis", value=trip_filters is not None)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    filters = {
        'client_names': [selected_client] if selected_client != "All Clients" else [],
        'plant': selected_plant,
        'destination': selected_dest,
        'date_range': date_range if len(date_range) == 2 else (None, None),
        'trip_nos': trip_filters.get('trip_nos') if link_trips and trip_filters else None
    }
    
    filtered_df = apply_tat_filters(tat_df, filters)
    
    if filtered_df.empty:
        st.info("No data matches the selected filters.")
        return
    
    loading_mean = filtered_df['loading_tat'].mean(skipna=True)
    unloading_mean = filtered_df['unloading_tat'].mean(skipna=True)
    total_mean = filtered_df['total_tat'].mean(skipna=True)
    
    st.markdown("### Key Metrics")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        render_metric_card(minutes_to_hhmm(loading_mean), "Avg Loading TAT")
    with col2:
        render_metric_card(minutes_to_hhmm(unloading_mean), "Avg Unloading TAT")
    with col3:
        render_metric_card(f"{len(filtered_df):,}", "Total Trips")
    
    st.markdown("---")
    st.markdown("### 📈 Detailed TAT Breakdown")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### ⏱️ LOADING PROCESS")
        stages = [
            ("DO Receipt", filtered_df['do_receipt'].mean(skipna=True)),
            ("Gate In", filtered_df['gate_in_load'].mean(skipna=True)),
            ("Loading Exit", filtered_df['loaded_exit'].mean(skipna=True))
        ]
        
        for name, val in stages:
            st.markdown(f"""
                <div class="tat-stage-row">
                    <div class="stage-info"><div class="stage-name">{name}</div></div>
                    <div class="stage-time">
                        <div class="stage-minutes">{val:.1f} min</div>
                        <div class="stage-hhmm">{minutes_to_hhmm(val)}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown(f"""
            <div class="tat-total-row">
                <div class="tat-total-label">✅ Total Loading TAT</div>
                <div class="stage-time">
                    <div class="stage-minutes">{loading_mean:.1f} min</div>
                    <div class="stage-hhmm">{minutes_to_hhmm(loading_mean)}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("#### ⏱️ UNLOADING PROCESS")
        stages = [
            ("Gate In", filtered_df['gate_in_unload'].mean(skipna=True)),
            ("Unloading Exit", filtered_df['unloaded'].mean(skipna=True))
        ]
        
        for name, val in stages:
            st.markdown(f"""
                <div class="tat-stage-row">
                    <div class="stage-info"><div class="stage-name">{name}</div></div>
                    <div class="stage-time">
                        <div class="stage-minutes">{val:.1f} min</div>
                        <div class="stage-hhmm">{minutes_to_hhmm(val)}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown(f"""
            <div class="tat-total-row">
                <div class="tat-total-label">✅ Total Unloading TAT</div>
                <div class="stage-time">
                    <div class="stage-minutes">{unloading_mean:.1f} min</div>
                    <div class="stage-hhmm">{minutes_to_hhmm(unloading_mean)}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown(f"""
        <div class="grand-total-container">
            <div style="display: flex; justify-content: space-between;">
                <div style="font-weight: 700; color: #c5221f;">🔴 TOTAL TAT</div>
                <div>
                    <span style="font-size: 1.4rem; font-weight: 700; color: #c5221f;">{total_mean:.1f} min</span>
                    <span style="font-size: 1.2rem; font-weight: 700; color: #a50e0e;"> ({minutes_to_hhmm(total_mean)})</span>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 📊 Client / Plant TAT Summary")
    st.markdown("**LOADING TAT (S1+S2+S3) | UNLOADING TAT (S4+S5) | TOTAL TAT (Loading + Unloading)**")
    
    summary_df = calculate_tat_summary(filtered_df)
    
    if not summary_df.empty:
        # ── BUILD HTML TABLE WITH ALL 5 STAGES ──────────────────────────────
        table_html = '''
        <style>
            .tat-summary-table {
                width: 100%;
                border-collapse: collapse;
                font-size: 0.78rem;
                margin: 16px 0;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            }
            .tat-summary-table thead th {
                background: linear-gradient(135deg, #1a73e8 0%, #1557b0 100%);
                color: white;
                padding: 10px 6px;
                text-align: center;
                font-weight: 600;
                border: 1px solid #1557b0;
                white-space: nowrap;
                font-size: 0.72rem;
                letter-spacing: 0.02em;
            }
            .tat-summary-table thead th.header-loading {
                background: linear-gradient(135deg, #1a73e8 0%, #1557b0 100%);
                border-color: #1557b0;
            }
            .tat-summary-table thead th.header-unloading {
                background: linear-gradient(135deg, #34a853 0%, #2d8f47 100%);
                border-color: #2d8f47;
            }
            .tat-summary-table thead th.header-total {
                background: linear-gradient(135deg, #d32f2f 0%, #b71c1c 100%);
                border-color: #b71c1c;
            }
            .tat-summary-table tbody td {
                padding: 8px 6px;
                text-align: center;
                border: 1px solid #e0e4e8;
                white-space: nowrap;
                background: white;
                vertical-align: middle;
                font-size: 0.76rem;
            }
            .tat-summary-table tbody tr:hover td {
                background: #f8f9ff;
            }
            .tat-summary-table .client-col {
                text-align: left;
                font-weight: 600;
                color: #1a1a2e;
                min-width: 200px;
            }
            .tat-summary-table .plant-col {
                text-align: left;
                color: #555;
                min-width: 140px;
            }
            .tat-summary-table .trips-col {
                font-weight: 700;
                color: #1a73e8;
            }
            .tat-summary-table .loading-cell {
                background: #e8f0fe !important;
            }
            .tat-summary-table .unloading-cell {
                background: #e8f5e9 !important;
            }
            .tat-summary-table .total-cell {
                background: #fce4ec !important;
                font-weight: 700;
            }
            .tat-summary-table .stage-min {
                font-weight: 600;
                color: #333;
                font-size: 0.8rem;
            }
            .tat-summary-table .stage-hhmm {
                font-size: 0.72rem;
                color: #667eea;
                font-weight: 600;
            }
            .tat-summary-table .grand-total-row td {
                background: #f5f5f5 !important;
                font-weight: 700;
                border-top: 3px solid #d32f2f;
                font-size: 0.8rem;
            }
            .tat-summary-table .grand-total-label {
                text-align: right !important;
                color: #d32f2f;
                font-size: 0.85rem;
                font-weight: 700;
            }
            .tat-summary-table .loading-total-col {
                background: #d2e3fc !important;
                font-weight: 700;
            }
            .tat-summary-table .unloading-total-col {
                background: #c8e6c9 !important;
                font-weight: 700;
            }
            .tat-summary-table .total-total-col {
                background: #ffcdd2 !important;
                font-weight: 700;
            }
        </style>
        <table class="tat-summary-table">
        <thead>
            <tr>
                <th rowspan="2" style="min-width:180px;">Client</th>
                <th rowspan="2" style="min-width:130px;">Plant</th>
                <th rowspan="2" style="min-width:55px;">Trips</th>
                <th colspan="2" class="header-loading">DO Receipt<br>(S1)</th>
                <th colspan="2" class="header-loading">Gate In Load<br>(S2)</th>
                <th colspan="2" class="header-loading">Loaded Exit<br>(S3)</th>
                <th colspan="2" class="header-loading">Total Loading<br>(S1+S2+S3)</th>
                <th colspan="2" class="header-unloading">Gate In Unload<br>(S4)</th>
                <th colspan="2" class="header-unloading">Unloaded<br>(S5)</th>
                <th colspan="2" class="header-unloading">Total Unloading<br>(S4+S5)</th>
                <th colspan="2" class="header-total">TOTAL TAT<br>(Loading+Unloading)</th>
            </tr>
            <tr>
                <th class="header-loading">min</th>
                <th class="header-loading">HH:MM</th>
                <th class="header-loading">min</th>
                <th class="header-loading">HH:MM</th>
                <th class="header-loading">min</th>
                <th class="header-loading">HH:MM</th>
                <th class="header-loading">min</th>
                <th class="header-loading">HH:MM</th>
                <th class="header-unloading">min</th>
                <th class="header-unloading">HH:MM</th>
                <th class="header-unloading">min</th>
                <th class="header-unloading">HH:MM</th>
                <th class="header-unloading">min</th>
                <th class="header-unloading">HH:MM</th>
                <th class="header-total">min</th>
                <th class="header-total">HH:MM</th>
            </tr>
        </thead>
        <tbody>
        '''
        
        # Data rows
        for _, row in summary_df.iterrows():
            table_html += '<tr>'
            table_html += f'<td class="client-col">{row["client"]}</td>'
            table_html += f'<td class="plant-col">{row["plant"]}</td>'
            table_html += f'<td class="trips-col">{int(row["total_trips"])}</td>'
            
            # S1 - DO Receipt
            table_html += f'<td class="loading-cell"><span class="stage-min">{row["s1_mean"]:.1f}</span></td>'
            table_html += f'<td class="loading-cell"><span class="stage-hhmm">{row["S1_HHMM"]}</span></td>'
            
            # S2 - Gate In Load
            table_html += f'<td class="loading-cell"><span class="stage-min">{row["s2_mean"]:.1f}</span></td>'
            table_html += f'<td class="loading-cell"><span class="stage-hhmm">{row["S2_HHMM"]}</span></td>'
            
            # S3 - Loaded Exit
            table_html += f'<td class="loading-cell"><span class="stage-min">{row["s3_mean"]:.1f}</span></td>'
            table_html += f'<td class="loading-cell"><span class="stage-hhmm">{row["S3_HHMM"]}</span></td>'

            # Total Loading
            table_html += f'<td class="loading-total-col"><span class="stage-min">{row["loading_tat_mean"]:.1f}</span></td>'
            table_html += f'<td class="loading-total-col"><span class="stage-hhmm">{row["loading_tat_hhmm"]}</span></td>'
            
            # S4 - Gate In Unload
            table_html += f'<td class="unloading-cell"><span class="stage-min">{row["s4_mean"]:.1f}</span></td>'
            table_html += f'<td class="unloading-cell"><span class="stage-hhmm">{row["S4_HHMM"]}</span></td>'
            
            # S5 - Unloaded
            table_html += f'<td class="unloading-cell"><span class="stage-min">{row["s5_mean"]:.1f}</span></td>'
            table_html += f'<td class="unloading-cell"><span class="stage-hhmm">{row["S5_HHMM"]}</span></td>'
            
            # Total Unloading
            table_html += f'<td class="unloading-total-col"><span class="stage-min">{row["unloading_tat_mean"]:.1f}</span></td>'
            table_html += f'<td class="unloading-total-col"><span class="stage-hhmm">{row["unloading_tat_hhmm"]}</span></td>'
            
            # Total TAT
            table_html += f'<td class="total-total-col"><span class="stage-min">{row["total_tat_mean"]:.1f}</span></td>'
            table_html += f'<td class="total-total-col"><span class="stage-hhmm">{row["total_tat_hhmm"]}</span></td>'
            
            table_html += '</tr>'
        
        # ── GRAND TOTAL ROW ──────────────────────────────────────────────────
        total_trips_count = int(summary_df["total_trips"].sum())
        
        if total_trips_count > 0:
            weighted_s1 = (summary_df["s1_mean"] * summary_df["total_trips"]).sum() / total_trips_count
            weighted_s2 = (summary_df["s2_mean"] * summary_df["total_trips"]).sum() / total_trips_count
            weighted_s3 = (summary_df["s3_mean"] * summary_df["total_trips"]).sum() / total_trips_count
            weighted_s4 = (summary_df["s4_mean"] * summary_df["total_trips"]).sum() / total_trips_count
            weighted_s5 = (summary_df["s5_mean"] * summary_df["total_trips"]).sum() / total_trips_count
            weighted_load = weighted_s1 + weighted_s2 + weighted_s3
            weighted_unload = weighted_s4 + weighted_s5
            weighted_total = weighted_load + weighted_unload
        else:
            weighted_s1 = weighted_s2 = weighted_s3 = weighted_s4 = weighted_s5 = 0
            weighted_load = weighted_unload = weighted_total = 0
        
        table_html += '<tr class="grand-total-row">'
        table_html += f'<td colspan="3" class="grand-total-label">GRAND TOTAL - All Records</td>'
        table_html += f'<td class="loading-cell"><span class="stage-min">{weighted_s1:.1f}</span></td>'
        table_html += f'<td class="loading-cell"><span class="stage-hhmm">{minutes_to_hhmm(weighted_s1)}</span></td>'
        table_html += f'<td class="loading-cell"><span class="stage-min">{weighted_s2:.1f}</span></td>'
        table_html += f'<td class="loading-cell"><span class="stage-hhmm">{minutes_to_hhmm(weighted_s2)}</span></td>'
        table_html += f'<td class="loading-cell"><span class="stage-min">{weighted_s3:.1f}</span></td>'
        table_html += f'<td class="loading-cell"><span class="stage-hhmm">{minutes_to_hhmm(weighted_s3)}</span></td>'
        table_html += f'<td class="loading-total-col"><span class="stage-min">{weighted_load:.1f}</span></td>'
        table_html += f'<td class="loading-total-col"><span class="stage-hhmm">{minutes_to_hhmm(weighted_load)}</span></td>'
        table_html += f'<td class="unloading-cell"><span class="stage-min">{weighted_s4:.1f}</span></td>'
        table_html += f'<td class="unloading-cell"><span class="stage-hhmm">{minutes_to_hhmm(weighted_s4)}</span></td>'
        table_html += f'<td class="unloading-cell"><span class="stage-min">{weighted_s5:.1f}</span></td>'
        table_html += f'<td class="unloading-cell"><span class="stage-hhmm">{minutes_to_hhmm(weighted_s5)}</span></td>'
        table_html += f'<td class="unloading-total-col"><span class="stage-min">{weighted_unload:.1f}</span></td>'
        table_html += f'<td class="unloading-total-col"><span class="stage-hhmm">{minutes_to_hhmm(weighted_unload)}</span></td>'
        table_html += f'<td class="total-total-col"><span class="stage-min">{weighted_total:.1f}</span></td>'
        table_html += f'<td class="total-total-col"><span class="stage-hhmm">{minutes_to_hhmm(weighted_total)}</span></td>'
        table_html += '</tr>'
        
        table_html += '</tbody></table>'
        
        st.markdown(table_html, unsafe_allow_html=True)
        
        # ── DOWNLOAD BUTTON ──────────────────────────────────────────────────
        download_df = summary_df[[
            'client', 'plant', 'total_trips',
            's1_mean', 's2_mean', 's3_mean', 'loading_tat_mean', 's4_mean', 's5_mean', 'unloading_tat_mean', 'total_tat_mean'
        ]].copy()
        
        download_df.columns = [
            'Client', 'Plant', 'Trips',
            'DO Receipt (min)', 'Gate In Load (min)', 'Loaded Exit (min)', 'Total Loading (min)', 
            'Gate In Unload (min)', 'Unloaded (min)',
            'Total Unloading (min)', 'Total TAT (min)'
        ]
        
        csv_summary = download_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Download Client/Plant TAT Summary (CSV)", 
            data=csv_summary,
            file_name="client_plant_tat_summary.csv", 
            mime="text/csv"
        )
    else:
        st.info("No data available for the summary table.")

# ===================================================================================
# TRIP ANALYSIS TAB - With Destination Drill-Down
# ===================================================================================

def render_trip_analysis(trip_df: pd.DataFrame):
    st.subheader("🚛 Trip Analysis")
    
    if trip_df.empty:
        st.warning("No trip data available.")
        return
    
    # Show deduplication stats if available
    if hasattr(st.session_state, 'dedup_stats'):
        stats = st.session_state.dedup_stats
        st.info(f"📊 Data after deduplication: {stats['new_rows']:,} unique trips from {stats['original_rows']:,} original records")
    
    all_clients_in_data = trip_df['client'].dropna().unique().tolist()
    available_clients = []
    
    for predefined in PREDEFINED_CLIENTS:
        predefined_norm = normalize_text(pd.Series([predefined]))[0]
        if predefined_norm in all_clients_in_data:
            available_clients.append(predefined)
    
    # Also add EMPTY_TRIP if present
    if 'EMPTY_TRIP' in all_clients_in_data:
        available_clients.append('EMPTY_TRIP')
    
    with st.expander("🔍 Filter Trip Data", expanded=True):
        st.markdown('<div class="filter-section">', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
        
        with col1:
            selected_client = st.selectbox("🏢 Client", available_clients, key="trip_client")
        
        with col2:
            client_norm = normalize_text(pd.Series([selected_client]))[0] if selected_client != 'EMPTY_TRIP' else 'EMPTY_TRIP'
            client_plants = sorted(trip_df[trip_df['client'] == client_norm]['plant'].dropna().unique().tolist())
            selected_plants = st.multiselect("🏭 Plant", client_plants, default=client_plants)
        
        with col3:
            months = sorted(trip_df['month'].dropna().unique().tolist(), reverse=True)
            selected_month = st.selectbox("📅 Month", ["All Months"] + months)
        
        with col4:
            trip_types = sorted(trip_df['trip_type'].dropna().unique().tolist())
            selected_type = st.selectbox("🔄 Trip Type", ["All Types"] + trip_types)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    client_norm = normalize_text(pd.Series([selected_client]))[0] if selected_client != 'EMPTY_TRIP' else 'EMPTY_TRIP'
    filtered = trip_df[trip_df['client'] == client_norm].copy()
    
    if selected_plants:
        filtered = filtered[filtered['plant'].isin([normalize_text(pd.Series([p]))[0] for p in selected_plants])]
    if selected_month != "All Months":
        filtered = filtered[filtered['month'] == selected_month]
    if selected_type != "All Types":
        filtered = filtered[filtered['trip_type'] == selected_type]
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        render_metric_card(f"{len(filtered):,}", "Total Trips")
    with col2:
        loaded = len(filtered[filtered['trip_type'] == 'Loaded'])
        render_metric_card(f"{loaded:,}", "Loaded Trips")
    with col3:
        empty = len(filtered[filtered['trip_type'] == 'Empty'])
        render_metric_card(f"{empty:,}", "Empty Trips")
    with col4:
        render_metric_card(f"{filtered['destination'].nunique():,}", "Unique Destinations")
    with col5:
        render_metric_card(f"{filtered['inv_qty'].sum():,.0f}", "Total Quantity")
    
    st.markdown("---")
    st.markdown("### 📍 Destination Analysis")
    st.caption("💡 **Click the 🔍 button** next to any destination to see detailed trip information")
    
    # Build destination summary
    agg_dict = {
        'Total_Trips': ('trip_no', 'count'),
        'Total_Qty': ('inv_qty', 'sum'),
        'Plants': ('plant', lambda x: x.nunique())
    }
    
    if 'trip_type' in filtered.columns and filtered['trip_type'].nunique() > 1:
        agg_dict['Loaded_Trips'] = ('trip_type', lambda x: (x == 'Loaded').sum())
        agg_dict['Empty_Trips'] = ('trip_type', lambda x: (x == 'Empty').sum())
    
    dest_summary = (filtered.groupby('destination')
                   .agg(**agg_dict)
                   .reset_index()
                   .sort_values('Total_Trips', ascending=False))
    
    # Chart and Table Layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        chart_type = st.radio("📊 Chart Type", ["Total Trips", "Total Quantity"], horizontal=True)
        
        if chart_type == "Total Trips":
            fig = px.bar(dest_summary.head(20), x='destination', y='Total_Trips', 
                        title='Top 20 Destinations by Trip Count',
                        color='Total_Trips', color_continuous_scale='Blues', 
                        text='Total_Trips')
        else:
            fig = px.bar(dest_summary.head(20), x='destination', y='Total_Qty',
                        title='Top 20 Destinations by Total Quantity',
                        color='Total_Qty', color_continuous_scale='Greens',
                        text='Total_Qty')
            fig.update_traces(texttemplate="%{text:,.2f}")
        
        fig.update_traces(textposition="outside")
        fig.update_layout(
            xaxis_tickangle=-45, 
            height=500,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_family='Inter'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### 📋 Destinations Summary")
        st.markdown('<div style="max-height: 500px; overflow-y: auto;">', unsafe_allow_html=True)
        
        for idx, row in dest_summary.iterrows():
            destination = row['destination']
            
            st.markdown(f"""
            <div class="dest-row">
                <div style="flex: 1;">
                    <div style="font-weight: 600; color: #1a1a2e;">{destination}</div>
                    <div style="font-size: 0.85rem; color: #666;">
                        {row['Total_Trips']} trips | 📦 {row['Total_Qty']:,.2f}
                    </div>
                </div>
                <div style="display: flex; gap: 10px; align-items: center;">
                    {'<span style="color: #34a853;">🟢 '+str(int(row["Loaded_Trips"]))+'</span> <span style="color: #ea4335;">🔴 '+str(int(row["Empty_Trips"]))+'</span>' if "Loaded_Trips" in row else ''}
                    <span style="color: #667eea;">🏭 {row["Plants"]}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🔍 View Details", key=f"drill_{idx}_{destination}"):
                show_trip_details(destination, filtered[filtered['destination'] == destination].copy())
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Export options
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        export_buf = BytesIO()
        with pd.ExcelWriter(export_buf, engine="openpyxl") as writer:
            dest_summary.to_excel(writer, sheet_name="Destination Summary", index=False)
            filtered.to_excel(writer, sheet_name="Raw Trips", index=False)
        export_buf.seek(0)
        st.download_button(
            label="⬇️ Download Summary as Excel",
            data=export_buf,
            file_name=f"trip_summary.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    with col2:
        csv_data = filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Filtered Data (CSV)",
            data=csv_data,
            file_name="filtered_trips.csv",
            mime="text/csv"
        )

# ===================================================================================
# MAIN APPLICATION
# ===================================================================================

def main():
    # Sidebar
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 20px 0;">
            <div style="font-size: 3rem;">🚛</div>
            <h2 style="color: white; font-weight: 700;">Analytics Suite</h2>
            <p style="color: #a0aec0; font-size: 0.9rem;">Logistics Performance Dashboard</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        st.markdown("""
        <div style="color: #a0aec0; font-size: 0.85rem;">
            <h4 style="color: white;">📋 Quick Guide</h4>
            <ul>
                <li>Upload Trip Reports for destination analysis</li>
                <li>Upload TAT Data for turnaround time metrics</li>
                <li>Click 🔍 to drill into destinations</li>
                <li>Use filters to narrow down results</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    st.title("🚛 Trip & TAT Analytics Suite")
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🚛 Trip Reports")
        trip_files = st.file_uploader(
            "Upload Excel files", type=["xlsx", "xls"],
            accept_multiple_files=True, key="trip_upload"
        )
    
    with col2:
        st.markdown("#### 📊 TAT Data")
        tat_file = st.file_uploader(
            "Upload Excel file", type=["xlsx", "xls"],
            accept_multiple_files=False, key="tat_upload"
        )
    
    if 'trip_df' not in st.session_state:
        st.session_state.trip_df = pd.DataFrame()
    if 'tat_df' not in st.session_state:
        st.session_state.tat_df = pd.DataFrame()
    if 'association' not in st.session_state:
        st.session_state.association = ClientPlantAssociation()
    
    if trip_files:
        files_data = [(f.name, f.getvalue()) for f in trip_files]
        result = load_trip_reports(files_data)
        
        st.session_state.trip_df = result['df']
        
        for msg in result['messages']:
            if msg['type'] == 'success':
                st.success(msg['text'])
            elif msg['type'] == 'warning':
                st.warning(msg['text'])
            elif msg['type'] == 'error':
                st.error(msg['text'])
            else:
                st.info(msg['text'])
        
        if not result['audit_df'].empty:
            with st.expander("🔁 Deduplication Audit Log"):
                st.dataframe(result['audit_df'], use_container_width=True, hide_index=True)
    
    if tat_file:
        st.session_state.tat_df, _, tat_messages, st.session_state.association = load_tat_data(tat_file.getvalue())
        
        for msg in tat_messages:
            st.info(f"ℹ️ {msg}")
        
        if not st.session_state.tat_df.empty:
            st.success(f"✅ TAT Data loaded: {len(st.session_state.tat_df):,} records")
    
    st.markdown("---")
    
    if not st.session_state.trip_df.empty or not st.session_state.tat_df.empty:
        tab1, tab2 = st.tabs(["🚛 Trip Analysis", "📊 TAT Report"])
        
        with tab1:
            if not st.session_state.trip_df.empty:
                render_trip_analysis(st.session_state.trip_df)
            else:
                st.info("Upload trip report files to see analysis")
        
        with tab2:
            if not st.session_state.tat_df.empty:
                trip_filters = None
                if not st.session_state.trip_df.empty:
                    trip_filters = {'trip_nos': st.session_state.trip_df['trip_no'].unique().tolist()}
                render_tat_report(st.session_state.tat_df, st.session_state.association, trip_filters)
            else:
                st.info("Upload TAT data file to see analysis")
    else:
        st.markdown("""
        <div style="text-align:center; padding: 60px 20px;">
            <div style="font-size:4rem;">📂</div>
            <h3 style="color:#555;">No file uploaded yet</h3>
            <p style="color: #888;">Upload your files above to get started:</p>
            <div style="display: flex; justify-content: center; gap: 40px; margin-top: 30px; flex-wrap: wrap;">
                <div class="metric-card" style="max-width: 300px;">
                    <h4>🚛 Trip Analysis</h4>
                    <p style="font-size:0.85rem; color: #666;">Upload monthly trip reports (.xlsx)</p>
                </div>
                <div class="metric-card" style="max-width: 300px;">
                    <h4>📊 TAT Analysis</h4>
                    <p style="font-size:0.85rem; color: #666;">Upload TAT data file (.xlsx)</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
