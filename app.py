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
    page_title="Trip & TAT Analytics Suite  | Logistics Performance Dashboard",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===================================================================================
# PROFESSIONAL STYLING
# ===================================================================================

st.markdown("""
<style>
    .main { background-color: #f0f2f6; }
    .stApp { font-family: 'Segoe UI', Roboto, sans-serif; }
    
    /* Metric Cards */
    .metric-card {
        background: white;
        border-radius: 16px;
        padding: 20px 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        text-align: center;
        transition: all 0.2s ease;
        border: 1px solid #e8eaed;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.12);
    }
    .metric-number { font-size: 2rem; font-weight: 700; color: #1a73e8; line-height: 1.2; }
    .metric-label { font-size: 0.8rem; color: #5f6368; margin-top: 8px; letter-spacing: 0.3px; }
    .metric-unit { font-size: 0.8rem; color: #5f6368; margin-top: 4px; }
    
    /* Status Cards */
    .status-success { background: #e6f4ea; border-left: 4px solid #34a853; }
    .status-warning { background: #fef7e0; border-left: 4px solid #fbbc04; }
    .status-error { background: #fce8e6; border-left: 4px solid #ea4335; }
    .status-info { background: #e8f0fe; border-left: 4px solid #1a73e8; }
    
    /* Typography */
    h1 { color: #202124; font-weight: 600; font-size: 1.8rem; }
    h2 { color: #202124; font-weight: 500; font-size: 1.4rem; }
    h3 { color: #3c4043; font-weight: 500; font-size: 1.2rem; }
    
    /* Data Display */
    .stDataFrame { border-radius: 12px; overflow: hidden; }
    
    /* Buttons */
    .stButton > button {
        background: #1a73e8;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background: #1557b0;
        transform: translateY(-1px);
        box-shadow: 0 2px 8px rgba(26,115,232,0.3);
    }
    
    /* TAT Containers */
    .tat-container {
        display: flex;
        gap: 24px;
        margin: 20px 0;
        flex-wrap: wrap;
    }
    .tat-column {
        flex: 1;
        min-width: 320px;
        background: white;
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        border: 1px solid #e8eaed;
    }
    .tat-column-header {
        padding: 16px 20px;
        font-weight: 600;
        font-size: 1rem;
        color: white;
        text-align: center;
    }
    .loading-header { background: linear-gradient(135deg, #1a73e8, #0d47a1); }
    .unloading-header { background: linear-gradient(135deg, #34a853, #1b5e20); }
    .tat-column-body { padding: 16px 20px; }
    
    .tat-stage-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 0;
        border-bottom: 1px solid #e8eaed;
    }
    .tat-stage-row:last-child { border-bottom: none; }
    .stage-info { flex: 1; }
    .stage-name { font-weight: 600; color: #202124; font-size: 0.9rem; }
    .stage-desc { font-size: 0.75rem; color: #5f6368; margin-top: 2px; }
    .stage-time { text-align: right; }
    .stage-minutes { font-weight: 600; color: #202124; font-size: 0.9rem; }
    .stage-hhmm { font-size: 0.8rem; color: #1a73e8; font-weight: 500; }
    
    .tat-total-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 0;
        margin-top: 8px;
        background: #e8f0fe;
        border-radius: 8px;
        padding: 12px 16px;
    }
    .tat-total-label { font-weight: 700; color: #1a73e8; }
    .tat-total-minutes { font-weight: 700; color: #1a73e8; font-size: 1rem; }
    .tat-total-hhmm { font-size: 0.85rem; color: #1557b0; font-weight: 600; }
    
    .grand-total-container {
        background: linear-gradient(135deg, #fce8e6, #fcd9d6);
        border-radius: 16px;
        padding: 20px 24px;
        margin: 20px 0;
        border: 1px solid #f5c6cb;
    }
    .grand-total-label { font-size: 1.2rem; font-weight: 700; color: #c5221f; }
    .grand-total-minutes { font-size: 1.4rem; font-weight: 700; color: #c5221f; }
    .grand-total-hhmm { font-size: 1.6rem; font-weight: 700; color: #a50e0e; }
    
    /* Filter Section */
    .filter-section {
        background: white;
        padding: 20px;
        border-radius: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        margin-bottom: 20px;
        border: 1px solid #e8eaed;
    }
    
    /* Summary Table */
    .dataframe-container {
        overflow-x: auto;
        border-radius: 12px;
        border: 1px solid #e8eaed;
        background: white;
    }
    
    /* Client-Plant Association Card */
    .association-card {
        background: white;
        border-radius: 12px;
        padding: 16px;
        margin: 10px 0;
        border-left: 4px solid #1a73e8;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    .association-client { font-weight: 700; color: #1a73e8; font-size: 1rem; }
    .association-plant { color: #34a853; font-weight: 500; }
    .association-count { color: #5f6368; font-size: 0.8rem; }
</style>
""", unsafe_allow_html=True)

# ===================================================================================
# CONSTANTS & CONFIGURATION
# ===================================================================================

# Predefined client list for filtering
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
        "client": ["Client", "Customer Name", "Customer", "Client Name", "Customer"],
        "plant": ["Plant", "Source", "Origin", "Source Plant", "From", "Source Place"],
        "destination": ["Destination", "Delivery Location", "Unloading Point", "To", "Drop Location"],
        "trip_type": ["Trip Type", "Trip Category", "Type"],
        "inv_qty": ["Inv Qty", "Invoice Quantity", "Quantity", "Qty", "Inv_Qty"],
        "date": ["Start Date", "Trip Date", "Date", "Transaction Date"]
    },
    "tat_data": {
        "trip_no": ["Trip No", "Trip Number", "TripID", "Trip Id"],
        "client": ["Client", "Customer Name", "Customer", "Client Name"],
        "plant": ["Plant", "Source Plant", "Origin Plant", "Source", "Source Place", "Origin"],
        "destination": ["Destination", "Unloading Point", "Delivery Location"],
        "stage_do_receipt": ["Actual DO Receipt (Mins)", "DO Receipt (Mins)", "Actual DO Receipt", "DO Receipt"],
        "stage_gate_in_load": ["Actual Gate In(Mins)", "Gate In (Mins)", "Actual Gate In", "Gate In"],
        "stage_loaded_exit": ["Actual Loaded Exit(Mins)", "Loaded Exit (Mins)", "Actual Loaded Exit", "Loaded Exit"],
        "stage_gate_in_unload": ["Actual Gate In for Unloading(Mins)", "Gate In for Unloading (Mins)", "Gate In Unloading"],
        "stage_unloaded": ["Actual Unloaded (Mins)", "Unloaded (Mins)", "Actual Unloaded"],
        "date": ["Date", "Transaction Date", "Trip Date"]
    }
}

# ===================================================================================
# HELPER FUNCTIONS
# ===================================================================================

def minutes_to_hhmm(minutes: float) -> str:
    """Convert minutes to HH:MM format with proper null handling."""
    if pd.isna(minutes) or minutes < 0:
        return "00:00"
    hours = int(minutes // 60)
    mins = int(minutes % 60)
    return f"{hours:02d}:{mins:02d}"

def normalize_text(series: pd.Series) -> pd.Series:
    """Standardize text for consistent matching."""
    return (series
        .astype(str)
        .str.upper()
        .str.strip()
        .str.replace(r'\s+', ' ', regex=True)
        .str.replace(r'[^\w\s-]', '', regex=True)
        .replace('NAN', 'UNKNOWN')
        .replace('', 'UNKNOWN')
    )

def detect_columns(df: pd.DataFrame, data_type: str) -> Dict[str, str]:
    """Dynamically detect column names based on configuration."""
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
    """Robust date parsing with multiple format detection."""
    if date_col not in df.columns:
        return pd.Series([pd.NaT] * len(df)), ["Date column not found"]
    
    errors = []
    date_series = pd.Series([pd.NaT] * len(df))
    
    # Try different date formats
    formats = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y', '%d.%m.%Y', '%Y/%m/%d']
    
    for fmt in formats:
        try:
            parsed = pd.to_datetime(df[date_col], format=fmt, errors='coerce')
            if parsed.notna().sum() > date_series.notna().sum():
                date_series = parsed
        except:
            continue
    
    # If still failing, let pandas auto-detect
    if date_series.isna().all():
        date_series = pd.to_datetime(df[date_col], errors='coerce')
    
    error_count = date_series.isna().sum()
    if error_count > 0:
        errors.append(f"{error_count} dates could not be parsed")
    
    return date_series, errors

# ===================================================================================
# CLIENT-PLANT ASSOCIATION (Critical for TAT Source Column)
# ===================================================================================

class ClientPlantAssociation:
    """Manages the association between clients and plants from TAT Source column."""
    
    def __init__(self):
        self.client_plant_map = {}  # client -> set of plants
        self.plant_client_map = {}  # plant -> set of clients
        self.association_df = pd.DataFrame()
    
    def build_from_tat_data(self, tat_df: pd.DataFrame):
        """Build client-plant associations from TAT data using Source/Plant column."""
        if tat_df.empty:
            return
        
        df = tat_df.copy()
        
        # Ensure client and plant columns exist
        if 'client' not in df.columns or 'plant' not in df.columns:
            return
        
        # Get unique client-plant pairs
        associations = df[['client', 'plant']].drop_duplicates()
        
        # Build maps
        for _, row in associations.iterrows():
            client = row['client']
            plant = row['plant']
            
            if client not in self.client_plant_map:
                self.client_plant_map[client] = set()
            self.client_plant_map[client].add(plant)
            
            if plant not in self.plant_client_map:
                self.plant_client_map[plant] = set()
            self.plant_client_map[plant].add(client)
        
        # Create association dataframe
        self.association_df = associations.copy()
        self.association_df.columns = ['Client', 'Plant (from TAT Source)']
        
        # Add trip counts
        trip_counts = df.groupby(['client', 'plant']).size().reset_index(name='Trip Count')
        self.association_df = self.association_df.merge(trip_counts, left_on=['Client', 'Plant (from TAT Source)'], 
                                                         right_on=['client', 'plant'], how='left')
        self.association_df = self.association_df.drop(columns=['client', 'plant'])
        self.association_df = self.association_df.sort_values(['Client', 'Trip Count'], ascending=[True, False])
    
    def get_plants_for_client(self, client: str) -> List[str]:
        """Get all plants associated with a specific client."""
        if client in self.client_plant_map:
            return sorted(list(self.client_plant_map[client]))
        return []
    
    def get_clients_for_plant(self, plant: str) -> List[str]:
        """Get all clients associated with a specific plant."""
        if plant in self.plant_client_map:
            return sorted(list(self.plant_client_map[plant]))
        return []
    
    def is_valid_association(self, client: str, plant: str) -> bool:
        """Check if a client-plant pair is valid based on TAT data."""
        return plant in self.client_plant_map.get(client, set())
    
    def render_association_summary(self):
        """Display the client-plant association summary."""
        if self.association_df.empty:
            st.info("No client-plant associations found. Upload TAT data with Source/Plant column.")
            return
        
        st.markdown("### 🔗 Client-Plant Associations (from TAT Source Column)")
        st.caption("These associations are automatically derived from your TAT data. Plants are linked to clients based on actual trip records.")
        
        # Summary stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Clients", len(self.client_plant_map))
        with col2:
            st.metric("Total Plants/Sources", len(self.plant_client_map))
        with col3:
            total_associations = len(self.association_df)
            st.metric("Client-Plant Pairs", total_associations)
        
        # Display association table
        with st.expander("📋 View All Client-Plant Associations", expanded=False):
            st.dataframe(
                self.association_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Client": st.column_config.TextColumn("Client", width="medium"),
                    "Plant (from TAT Source)": st.column_config.TextColumn("Plant/Source", width="medium"),
                    "Trip Count": st.column_config.NumberColumn("Number of Trips", format="%d")
                }
            )
        
        return self.association_df

# ===================================================================================
# DATA LOADING & DEDUPLICATION
# ===================================================================================

def load_trip_reports(files_data: List[Tuple[str, bytes]]) -> Dict[str, Any]:
    """Load and process multiple trip report files with deduplication."""
    messages = []
    all_frames = []
    
    for filename, data in files_data:
        try:
            df = pd.read_excel(BytesIO(data), sheet_name=0)
            detected_cols = detect_columns(df, "trip_report")
            
            # Validate required columns
            required = ['trip_no', 'client', 'destination']
            missing = [r for r in required if not detected_cols.get(r)]
            
            if missing:
                messages.append({
                    "type": "warning",
                    "text": f"⚠️ **{filename}** missing columns: {missing}. Skipping."
                })
                continue
            
            # Rename columns to standard names
            rename_map = {v: k for k, v in detected_cols.items() if v}
            df = df.rename(columns=rename_map)
            
            # Handle date column
            if detected_cols.get('date'):
                df['date_parsed'], date_errors = validate_date_parsing(df, 'date')
                if date_errors:
                    messages.append({
                        "type": "info",
                        "text": f"📅 **{filename}**: {date_errors[0]}"
                    })
            else:
                df['date_parsed'] = pd.NaT
            
            # Handle invoice quantity
            if 'inv_qty' not in df.columns:
                df['inv_qty'] = 0.0
            else:
                df['inv_qty'] = pd.to_numeric(df['inv_qty'], errors='coerce').fillna(0)
            
            # Handle trip type
            if 'trip_type' not in df.columns:
                df['trip_type'] = 'Loaded'
            else:
                df['trip_type'] = df['trip_type'].astype(str).str.title()
            
            # Handle plant/source
            if 'plant' not in df.columns:
                df['plant'] = 'UNKNOWN_PLANT'
            else:
                df['plant'] = normalize_text(df['plant'])
            
            # Normalize text columns
            df['client'] = normalize_text(df['client'])
            df['destination'] = normalize_text(df['destination'])
            df['trip_no'] = normalize_text(df['trip_no'])
            
            # Mark empty trips
            empty_mask = df['trip_type'].str.lower() == 'empty'
            df.loc[empty_mask & (df['client'] == 'UNKNOWN'), 'client'] = 'EMPTY_TRIP'
            
            df['_source_file'] = filename
            all_frames.append(df)
            
            messages.append({
                "type": "success",
                "text": f"✅ Loaded **{filename}**: {len(df):,} records"
            })
            
        except Exception as e:
            messages.append({
                "type": "error",
                "text": f"❌ Could not read **{filename}**: {str(e)}"
            })
    
    if not all_frames:
        return {"df": pd.DataFrame(), "audit_df": pd.DataFrame(), "messages": messages}
    
    # Combine all files
    combined = pd.concat(all_frames, ignore_index=True)
    
    # Create month column
    combined['month'] = combined['date_parsed'].dt.to_period('M').astype(str)
    
    # Apply deduplication
    combined, audit_df = deduplicate_trip_data_v2(combined)
    
    messages.append({
        "type": "success",
        "text": f"📊 Total unique trips after deduplication: {len(combined):,}"
    })
    
    return {"df": combined, "audit_df": audit_df, "messages": messages}

def deduplicate_trip_data_v2(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Enhanced deduplication that validates consistency before merging.
    Groups by Trip No, sums quantities, validates consistency.
    """
    df = df.copy()
    
    if 'trip_no' not in df.columns:
        return df, pd.DataFrame()
    
    # Find duplicates
    dup_mask = df.duplicated(subset=['trip_no'], keep=False)
    unique_df = df[~dup_mask].copy()
    dup_df = df[dup_mask].copy()
    
    if dup_df.empty:
        return df, pd.DataFrame()
    
    audit_records = []
    merged_records = []
    
    for trip_no, group in dup_df.groupby('trip_no'):
        validation_issues = []
        
        # Validate client consistency
        if group['client'].nunique() > 1:
            validation_issues.append(f"multi_client:{'|'.join(group['client'].unique())}")
        
        # Validate destination consistency
        if group['destination'].nunique() > 1:
            validation_issues.append(f"multi_dest:{'|'.join(group['destination'].unique())}")
        
        # Validate plant consistency
        if group['plant'].nunique() > 1:
            validation_issues.append(f"multi_plant:{'|'.join(group['plant'].unique())}")
        
        # Create merged record
        merged = {
            'trip_no': trip_no,
            'client': group['client'].mode()[0] if not group['client'].mode().empty else group['client'].iloc[0],
            'destination': group['destination'].mode()[0] if not group['destination'].mode().empty else group['destination'].iloc[0],
            'plant': group['plant'].mode()[0] if not group['plant'].mode().empty else group['plant'].iloc[0],
            'inv_qty': group['inv_qty'].sum(),
            'trip_type': 'Loaded' if group['inv_qty'].sum() > 0 else group['trip_type'].mode()[0],
            'date_parsed': group['date_parsed'].min() if group['date_parsed'].notna().any() else pd.NaT,
            '_source_file': group['_source_file'].iloc[0],
            '_validation_issues': '; '.join(validation_issues) if validation_issues else 'OK'
        }
        
        merged_records.append(merged)
        audit_records.append({
            'trip_no': trip_no,
            'original_rows': len(group),
            'inv_qty_summed': group['inv_qty'].sum(),
            'validation_issues': merged['_validation_issues']
        })
    
    # Combine unique and merged
    merged_df = pd.DataFrame(merged_records)
    final_df = pd.concat([unique_df, merged_df], ignore_index=True)
    
    # Ensure all columns are present
    for col in unique_df.columns:
        if col not in final_df.columns:
            final_df[col] = None
    
    audit_df = pd.DataFrame(audit_records) if audit_records else pd.DataFrame()
    
    return final_df[unique_df.columns], audit_df

def load_tat_data(file_data: bytes) -> Tuple[pd.DataFrame, Dict, List[str], ClientPlantAssociation]:
    """Load TAT data with dynamic column detection and build client-plant associations."""
    try:
        df = pd.read_excel(BytesIO(file_data), sheet_name=0)
        detected_cols = detect_columns(df, "tat_data")
        
        messages = []
        
        # Check for required columns
        required = ['trip_no', 'client']
        missing = [r for r in required if not detected_cols.get(r)]
        
        if missing:
            return pd.DataFrame(), detected_cols, [f"Missing required columns: {missing}"], ClientPlantAssociation()
        
        # Rename columns
        rename_map = {v: k for k, v in detected_cols.items() if v}
        df = df.rename(columns=rename_map)
        
        # Normalize text columns
        df['client'] = normalize_text(df['client'])
        df['trip_no'] = normalize_text(df['trip_no'])
        
        # CRITICAL: Handle Plant/Source column from TAT report
        if 'plant' in df.columns:
            df['plant'] = normalize_text(df['plant'])
            messages.append(f"✅ Found Plant/Source column: '{detected_cols.get('plant', 'plant')}'")
        else:
            df['plant'] = 'UNKNOWN_SOURCE'
            messages.append("⚠️ No Plant/Source column found. Using 'UNKNOWN_SOURCE'")
        
        if 'destination' in df.columns:
            df['destination'] = normalize_text(df['destination'])
        else:
            df['destination'] = 'UNKNOWN'
        
        # Handle date column
        if detected_cols.get('date'):
            df['date_parsed'], date_errors = validate_date_parsing(df, 'date')
            if date_errors:
                messages.append(date_errors[0])
        else:
            df['date_parsed'] = pd.NaT
        
        # Convert stage columns to numeric (keep NaN for missing data)
        stage_columns = ['stage_do_receipt', 'stage_gate_in_load', 'stage_loaded_exit', 
                        'stage_gate_in_unload', 'stage_unloaded']
        
        for stage in stage_columns:
            if stage in df.columns:
                df[stage] = pd.to_numeric(df[stage], errors='coerce')
            else:
                df[stage] = np.nan
        
        # Calculate TAT metrics (only where data exists)
        df['loading_tat'] = df['stage_do_receipt'] + df['stage_gate_in_load'] + df['stage_loaded_exit']
        df['unloading_tat'] = df['stage_gate_in_unload'] + df['stage_unloaded']
        df['total_tat'] = df['loading_tat'] + df['unloading_tat']
        
        # Build client-plant associations from TAT data
        association = ClientPlantAssociation()
        association.build_from_tat_data(df)
        
        messages.append(f"📊 Built {len(association.association_df)} client-plant associations")
        
        return df, detected_cols, messages, association
        
    except Exception as e:
        return pd.DataFrame(), {}, [f"Error loading TAT file: {str(e)}"], ClientPlantAssociation()

# ===================================================================================
# CLIENT MAPPING (Trip Report ↔ TAT Data)
# ===================================================================================

def create_client_mapping(trip_df: pd.DataFrame, tat_df: pd.DataFrame, threshold: float = 0.85) -> Dict[str, str]:
    """Create fuzzy mapping between client names in Trip Report and TAT data."""
    if trip_df.empty or tat_df.empty:
        return {}
    
    trip_clients = trip_df['client'].dropna().unique().tolist()
    tat_clients = tat_df['client'].dropna().unique().tolist()
    
    mapping = {}
    
    for trip_client in trip_clients:
        if trip_client in ['EMPTY_TRIP', 'UNKNOWN']:
            mapping[trip_client] = trip_client
            continue
        
        # Try exact match first
        if trip_client in tat_clients:
            mapping[trip_client] = trip_client
            continue
        
        # Try fuzzy match
        best_match = None
        best_score = 0
        
        for tat_client in tat_clients:
            score = SequenceMatcher(None, trip_client, tat_client).ratio()
            if score > best_score and score >= threshold:
                best_score = score
                best_match = tat_client
        
        if best_match:
            mapping[trip_client] = best_match
        else:
            mapping[trip_client] = trip_client
    
    return mapping

# ===================================================================================
# TAT PROCESSING & FILTERING (With Client-Plant Association)
# ===================================================================================

def apply_tat_filters(df: pd.DataFrame, filters: Dict, association: ClientPlantAssociation) -> pd.DataFrame:
    """Apply filters to TAT data with client-plant association validation."""
    if df.empty:
        return df
    
    df_filtered = df.copy()
    
    # Filter by trip numbers (from Trip Report)
    if filters.get('trip_nos'):
        trip_nos_norm = [normalize_text(pd.Series([t]))[0] for t in filters['trip_nos']]
        df_filtered = df_filtered[df_filtered['trip_no'].isin(trip_nos_norm)]
    
    # Filter by client
    if filters.get('client_names') and len(filters['client_names']) > 0:
        client_norm = [normalize_text(pd.Series([c]))[0] for c in filters['client_names']]
        df_filtered = df_filtered[df_filtered['client'].isin(client_norm)]
    
    # Filter by plant - if "All Plants" selected, include ALL plants for that client
    if filters.get('plant') and filters['plant'] not in ['All Plants', 'ALL_PLANTS', 'ALL_SOURCES', 'All Plants/Sources', None]:
        plant_norm = normalize_text(pd.Series([filters['plant']]))[0]
        df_filtered = df_filtered[df_filtered['plant'] == plant_norm]
    # If "All Plants/Sources" is selected, keep all plants (no filter)
    
    # Filter by destination
    if filters.get('destination') and filters['destination'] not in ['All Destinations', None]:
        dest_norm = normalize_text(pd.Series([filters['destination']]))[0]
        df_filtered = df_filtered[df_filtered['destination'] == dest_norm]
    
    # Filter by date range
    if filters.get('date_range'):
        start_date, end_date = filters['date_range']
        if start_date and end_date:
            df_filtered = df_filtered[
                (df_filtered['date_parsed'] >= pd.Timestamp(start_date)) &
                (df_filtered['date_parsed'] <= pd.Timestamp(end_date))
            ]
    
    return df_filtered

def calculate_tat_summary(df: pd.DataFrame, association: ClientPlantAssociation = None) -> pd.DataFrame:
    """
    Calculate Client | Plant (from TAT Source) | Loading TAT | Unloading TAT | Total TAT summary.
    Uses the actual Source/Plant column from TAT data.
    """
    if df.empty:
        return pd.DataFrame()
    
    df_work = df.copy()
    
    # Group by client and plant (Source column from TAT)
    group_cols = ['client', 'plant']
    
    summary = df_work.groupby(group_cols, as_index=False).agg(
        total_trips=('client', 'count'),
        # Loading TAT
        loading_tat_mean=('loading_tat', lambda x: x.mean(skipna=True)),
        loading_tat_median=('loading_tat', lambda x: x.median(skipna=True)),
        loading_tat_p95=('loading_tat', lambda x: x.quantile(0.95) if len(x.dropna()) > 0 else np.nan),
        # Unloading TAT
        unloading_tat_mean=('unloading_tat', lambda x: x.mean(skipna=True)),
        unloading_tat_median=('unloading_tat', lambda x: x.median(skipna=True)),
        # Total TAT
        total_tat_mean=('total_tat', lambda x: x.mean(skipna=True)),
        total_tat_median=('total_tat', lambda x: x.median(skipna=True)),
        # Individual stages
        stage1_mean=('stage_do_receipt', lambda x: x.mean(skipna=True)),
        stage2_mean=('stage_gate_in_load', lambda x: x.mean(skipna=True)),
        stage3_mean=('stage_loaded_exit', lambda x: x.mean(skipna=True)),
        stage4_mean=('stage_gate_in_unload', lambda x: x.mean(skipna=True)),
        stage5_mean=('stage_unloaded', lambda x: x.mean(skipna=True)),
    )
    
    # Add formatted columns
    summary['loading_tat_hhmm'] = summary['loading_tat_mean'].apply(minutes_to_hhmm)
    summary['unloading_tat_hhmm'] = summary['unloading_tat_mean'].apply(minutes_to_hhmm)
    summary['total_tat_hhmm'] = summary['total_tat_mean'].apply(minutes_to_hhmm)
    
    summary['stage1_hhmm'] = summary['stage1_mean'].apply(minutes_to_hhmm)
    summary['stage2_hhmm'] = summary['stage2_mean'].apply(minutes_to_hhmm)
    summary['stage3_hhmm'] = summary['stage3_mean'].apply(minutes_to_hhmm)
    summary['stage4_hhmm'] = summary['stage4_mean'].apply(minutes_to_hhmm)
    summary['stage5_hhmm'] = summary['stage5_mean'].apply(minutes_to_hhmm)
    
    return summary.sort_values('total_tat_mean')

def get_plant_drilldown(df: pd.DataFrame, plant: str, client: str = None) -> pd.DataFrame:
    """Get detailed trip-level data for a specific plant (Source from TAT)."""
    if df.empty:
        return pd.DataFrame()
    
    plant_norm = normalize_text(pd.Series([plant]))[0]
    df_filtered = df[df['plant'] == plant_norm]
    
    if client and client != 'All Clients':
        client_norm = normalize_text(pd.Series([client]))[0]
        df_filtered = df_filtered[df_filtered['client'] == client_norm]
    
    if df_filtered.empty:
        return pd.DataFrame()
    
    # Prepare display columns - FIXED: define display_cols before using it
    display_cols = ['trip_no', 'client', 'plant', 'destination', 'date_parsed']
    display_cols += ['stage_do_receipt', 'stage_gate_in_load', 'stage_loaded_exit', 
                    'stage_gate_in_unload', 'stage_unloaded']
    display_cols += ['loading_tat', 'unloading_tat', 'total_tat']
    
    result = df_filtered[display_cols].copy()
    
    # Add formatted columns
    for col in ['stage_do_receipt', 'stage_gate_in_load', 'stage_loaded_exit',
                'stage_gate_in_unload', 'stage_unloaded', 'loading_tat', 'unloading_tat', 'total_tat']:
        if col in result.columns:
            result[f'{col}_hhmm'] = result[col].apply(minutes_to_hhmm)
    
    # Rename plant to clarify it's from TAT Source
    result = result.rename(columns={'plant': 'Plant/Source (from TAT)'})
    
    return result

# ===================================================================================
# UI COMPONENTS
# ===================================================================================

def render_metric_card(value: str, label: str, unit: str = ""):
    """Render a styled metric card."""
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-number">{value}</div>
            <div class="metric-label">{label}</div>
            {f'<div class="metric-unit">{unit}</div>' if unit else ''}
        </div>
    """, unsafe_allow_html=True)

def render_tat_report(tat_df: pd.DataFrame, association: ClientPlantAssociation, trip_filters: Dict = None):
    """Render the TAT analysis report with client-plant associations."""
    st.subheader("📊 Turnaround Time (TAT) Analysis")
    st.caption("Plant/Source column represents the **Source/Origin** from your TAT data")
    
    if tat_df.empty:
        st.warning("No TAT data available for analysis.")
        return
    
    # Display client-plant associations
    association.render_association_summary()
    st.markdown("---")
    
    # Get filter options - use predefined clients that exist in data
    all_clients_in_data = tat_df['client'].dropna().unique().tolist()
    
    # Filter predefined clients to only those present in data
    available_clients = [c for c in PREDEFINED_CLIENTS if normalize_text(pd.Series([c]))[0] in all_clients_in_data]
    
    # Add any other clients from data not in predefined list
    for client in all_clients_in_data:
        client_normalized = client
        found = False
        for predefined in PREDEFINED_CLIENTS:
            if normalize_text(pd.Series([predefined]))[0] == client_normalized:
                found = True
                break
        if not found and client not in ['UNKNOWN', 'EMPTY_TRIP']:
            available_clients.append(client)
    
    available_clients = sorted(available_clients)
    
    # Filter UI
    with st.expander("🔍 Filter TAT Data", expanded=True):
        st.markdown('<div class="filter-section">', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            selected_client = st.selectbox("🏢 Client", ["All Clients"] + available_clients, key="tat_client")
        
        with col2:
            # Get plants based on selected client
            if selected_client != "All Clients":
                # Get plants associated with selected client
                associated_plants = association.get_plants_for_client(selected_client)
                if associated_plants:
                    plant_options = ["All Plants/Sources"] + associated_plants
                else:
                    # Fallback to all plants from data for this client
                    client_plants = tat_df[tat_df['client'] == normalize_text(pd.Series([selected_client]))[0]]['plant'].dropna().unique().tolist()
                    plant_options = ["All Plants/Sources"] + sorted(client_plants)
            else:
                all_plants = sorted(tat_df['plant'].dropna().unique().tolist())
                plant_options = ["All Plants/Sources"] + all_plants
            
            selected_plant = st.selectbox("🏭 Plant/Source (from TAT)", plant_options, key="tat_plant")
        
        with col3:
            # Filter destinations based on selections
            temp_df = tat_df
            if selected_client != "All Clients":
                client_norm = normalize_text(pd.Series([selected_client]))[0]
                temp_df = temp_df[temp_df['client'] == client_norm]
            if selected_plant != "All Plants/Sources":
                plant_norm = normalize_text(pd.Series([selected_plant]))[0]
                temp_df = temp_df[temp_df['plant'] == plant_norm]
            filtered_dests = temp_df['destination'].dropna().unique().tolist()
            dest_options = ["All Destinations"] + sorted(filtered_dests)
            selected_dest = st.selectbox("📍 Destination", dest_options, key="tat_dest")
        
        col1, col2 = st.columns(2)
        
        with col1:
            min_date = tat_df['date_parsed'].min().date() if tat_df['date_parsed'].notna().any() else None
            max_date = tat_df['date_parsed'].max().date() if tat_df['date_parsed'].notna().any() else None
            
            if min_date and max_date:
                date_range = st.date_input(
                    "📅 Date Range",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date,
                    key="tat_date"
                )
            else:
                date_range = (None, None)
        
        with col2:
            link_trips = st.checkbox("🔗 Link with Trip Analysis", value=trip_filters is not None)
            if link_trips and trip_filters:
                st.caption(f"✅ Linked to {len(trip_filters.get('trip_nos', [])):,} trips from Trip Report")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Build filters
    filters = {
        'client_names': [selected_client] if selected_client != "All Clients" else [],
        'plant': selected_plant,
        'destination': selected_dest,
        'date_range': date_range if len(date_range) == 2 else (None, None),
        'trip_nos': trip_filters.get('trip_nos') if link_trips and trip_filters else None
    }
    
    # Apply filters
    filtered_df = apply_tat_filters(tat_df, filters, association)
    
    if filtered_df.empty:
        st.info("No data matches the selected filters. Try adjusting your criteria.")
        return
    
    # Calculate metrics
    total_trips = len(filtered_df)
    loading_mean = filtered_df['loading_tat'].mean(skipna=True)
    unloading_mean = filtered_df['unloading_tat'].mean(skipna=True)
    total_mean = filtered_df['total_tat'].mean(skipna=True)
    
    # Display metrics
    st.markdown("### Key Metrics")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        render_metric_card(minutes_to_hhmm(loading_mean), "Avg Loading TAT", "S1+S2+S3")
    with col2:
        render_metric_card(minutes_to_hhmm(unloading_mean), "Avg Unloading TAT", "S4+S5")
    with col3:
        render_metric_card(f"{total_trips:,}", "Total Trips Analyzed", "")
    
    st.markdown("---")
    
    # Detailed TAT Breakdown
    st.markdown("### 📈 Detailed TAT Breakdown")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### ⏱️ LOADING PROCESS")
        stages = [
            ("DO Receipt", "DO to Gate Entry", filtered_df['stage_do_receipt'].mean(skipna=True)),
            ("Gate In", "Gate to Loading Bay", filtered_df['stage_gate_in_load'].mean(skipna=True)),
            ("Loading Exit", "Loading to Exit", filtered_df['stage_loaded_exit'].mean(skipna=True))
        ]
        
        for name, desc, val in stages:
            st.markdown(f"""
                <div class="tat-stage-row">
                    <div class="stage-info">
                        <div class="stage-name">{name}</div>
                        <div class="stage-desc">{desc}</div>
                    </div>
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
            ("Gate In", "Gate for Unloading", filtered_df['stage_gate_in_unload'].mean(skipna=True)),
            ("Unloading Exit", "Unloading to Exit", filtered_df['stage_unloaded'].mean(skipna=True))
        ]
        
        for name, desc, val in stages:
            st.markdown(f"""
                <div class="tat-stage-row">
                    <div class="stage-info">
                        <div class="stage-name">{name}</div>
                        <div class="stage-desc">{desc}</div>
                    </div>
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
    
    # Grand Total
    st.markdown(f"""
        <div class="grand-total-container">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div class="grand-total-label">🔴 TOTAL TAT (Loading + Unloading)</div>
                <div class="grand-total-time">
                    <div class="grand-total-minutes">{total_mean:.1f} min</div>
                    <div class="grand-total-hhmm">{minutes_to_hhmm(total_mean)}</div>
                </div>
            </div>
            <div style="font-size: 0.75rem; color: #666; margin-top: 12px; text-align: center;">
                Loading TAT ({minutes_to_hhmm(loading_mean)}) + Unloading TAT ({minutes_to_hhmm(unloading_mean)}) = {minutes_to_hhmm(total_mean)}
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Client/Plant Summary Table (Using TAT Source column as Plant)
    st.markdown("### 📊 Client / Plant/Source (from TAT) TAT Summary")
    st.caption("The **Plant/Source** column represents the actual **Source/Origin** from your TAT data file")
    
    summary_df = calculate_tat_summary(filtered_df, association)
    
    if not summary_df.empty:
        # Display as dataframe with styling
        display_df = summary_df[[
            'client', 'plant', 'total_trips',
            'loading_tat_mean', 'loading_tat_hhmm',
            'unloading_tat_mean', 'unloading_tat_hhmm',
            'total_tat_mean', 'total_tat_hhmm'
        ]].copy()
        
        display_df.columns = [
            'Client', 'Plant/Source (from TAT)', 'Trips',
            'Loading TAT (min)', 'Loading TAT', 
            'Unloading TAT (min)', 'Unloading TAT',
            'Total TAT (min)', 'Total TAT'
        ]
        
        # Format the dataframe
        display_df['Loading TAT'] = display_df['Loading TAT'].apply(lambda x: f"{x}")
        display_df['Unloading TAT'] = display_df['Unloading TAT'].apply(lambda x: f"{x}")
        display_df['Total TAT'] = display_df['Total TAT'].apply(lambda x: f"{x}")
        display_df['Loading TAT (min)'] = display_df['Loading TAT (min)'].round(1)
        display_df['Unloading TAT (min)'] = display_df['Unloading TAT (min)'].round(1)
        display_df['Total TAT (min)'] = display_df['Total TAT (min)'].round(1)
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Export
        csv = display_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Summary CSV", csv, "tat_summary.csv", "text/csv")
        
        # Plant Drill-down
        st.markdown("---")
        st.markdown("### 🔍 Plant/Source Details")
        st.caption("Drill down into individual trip details for any Plant/Source from your TAT data")
        
        plant_options = summary_df['plant'].unique().tolist()
        selected_plant_drill = st.selectbox("Select Plant/Source for Trip Details", plant_options)
        
        if selected_plant_drill:
            drill_df = get_plant_drilldown(filtered_df, selected_plant_drill, selected_client if selected_client != "All Clients" else None)
            
            if not drill_df.empty:
                st.markdown(f"#### 📋 Trip Details for Plant/Source: **{selected_plant_drill}**")
                st.dataframe(drill_df, use_container_width=True, hide_index=True)
                
                csv_drill = drill_df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download Trip Details CSV", csv_drill, f"plant_source_{selected_plant_drill}_trips.csv", "text/csv")

# ===================================================================================
# TRIP ANALYSIS TAB
# ===================================================================================

def render_trip_analysis(trip_df: pd.DataFrame):
    """Render the trip analysis tab."""
    st.subheader("🚛 Trip Analysis")
    
    if trip_df.empty:
        st.warning("No trip data available.")
        return
    
    # Get clients from data that match predefined list
    all_clients_in_data = trip_df['client'].dropna().unique().tolist()
    
    # Filter predefined clients to only those present in data
    available_clients = []
    for predefined in PREDEFINED_CLIENTS:
        predefined_norm = normalize_text(pd.Series([predefined]))[0]
        if predefined_norm in all_clients_in_data:
            available_clients.append(predefined)
    
    # Add any other clients not in predefined
    for client in all_clients_in_data:
        if client not in [normalize_text(pd.Series([c]))[0] for c in available_clients] and client not in ['UNKNOWN', 'EMPTY_TRIP']:
            # Try to find original name
            available_clients.append(client)
    
    available_clients = sorted(available_clients)
    
    # Filter UI
    with st.expander("🔍 Filter Trip Data", expanded=True):
        selected_client = st.selectbox("🏢 Client", available_clients, key="trip_client")
        
        col1, col2 = st.columns(2)
        
        with col1:
            client_norm = normalize_text(pd.Series([selected_client]))[0]
            client_plants = sorted(trip_df[trip_df['client'] == client_norm]['plant'].dropna().unique().tolist())
            selected_plants = st.multiselect("🏭 Plant (from Trip Report)", client_plants, default=client_plants)
        
        with col2:
            months = sorted(trip_df['month'].dropna().unique().tolist(), reverse=True)
            selected_month = st.selectbox("📅 Month", ["All Months"] + months)
        
        trip_types = sorted(trip_df['trip_type'].dropna().unique().tolist())
        selected_type = st.selectbox("🔄 Trip Type", ["All Types"] + trip_types)
    
    # Apply filters
    client_norm = normalize_text(pd.Series([selected_client]))[0]
    filtered = trip_df[trip_df['client'] == client_norm].copy()
    
    if selected_plants:
        filtered = filtered[filtered['plant'].isin([normalize_text(pd.Series([p]))[0] for p in selected_plants])]
    if selected_month != "All Months":
        filtered = filtered[filtered['month'] == selected_month]
    if selected_type != "All Types":
        filtered = filtered[filtered['trip_type'] == selected_type]
    
    # Metrics
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
        total_qty = filtered['inv_qty'].sum()
        render_metric_card(f"{total_qty:,.0f}", "Total Quantity")
    
    # Destination Analysis
    st.markdown("---")
    st.markdown("### 📍 Destination Analysis")
    
    dest_summary = filtered.groupby('destination').agg(
        total_trips=('trip_no', 'count'),
        total_qty=('inv_qty', 'sum'),
        plants_used=('plant', 'nunique')
    ).reset_index().sort_values('total_trips', ascending=False).head(20)
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.bar(dest_summary, x='destination', y='total_trips', 
                     title='Top Destinations by Trip Count',
                     color='total_trips', color_continuous_scale='Blues')
        fig.update_layout(xaxis_tickangle=-45, height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.bar(dest_summary, x='destination', y='total_qty',
                     title='Top Destinations by Quantity',
                     color='total_qty', color_continuous_scale='Greens')
        fig.update_layout(xaxis_tickangle=-45, height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # Export
    st.markdown("---")
    export_data = filtered[[
        'trip_no', 'client', 'plant', 'destination', 'trip_type', 'inv_qty', 'date_parsed'
    ]].copy()
    
    csv = export_data.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Trip Data CSV", csv, f"trips_{selected_client}.csv", "text/csv")

# ===================================================================================
# MAIN APPLICATION
# ===================================================================================

def main():
    st.title("🚛 Trip & TAT Analytics Suite v2")
    st.caption("Advanced Logistics Performance Dashboard with Client-Plant Association from TAT Source Column")
    
    st.markdown("---")
    
    # File Upload Section
    st.markdown("### 📂 Data Upload")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🚛 Trip Reports")
        trip_files = st.file_uploader(
            "Upload Excel files", type=["xlsx", "xls"],
            accept_multiple_files=True, key="trip_upload",
            help="Upload monthly trip reports containing trip details, quantities, and delivery information."
        )
    
    with col2:
        st.markdown("#### 📊 TAT Data")
        tat_file = st.file_uploader(
            "Upload Excel file", type=["xlsx", "xls"],
            accept_multiple_files=False, key="tat_upload",
            help="Upload Turnaround Time dataset. The Source/Plant column will be used for client-plant association."
        )
    
    # Initialize session state
    if 'trip_df' not in st.session_state:
        st.session_state.trip_df = pd.DataFrame()
    if 'tat_df' not in st.session_state:
        st.session_state.tat_df = pd.DataFrame()
    if 'client_mapping' not in st.session_state:
        st.session_state.client_mapping = {}
    if 'association' not in st.session_state:
        st.session_state.association = ClientPlantAssociation()
    
    # Process Trip Reports
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
    
    # Process TAT Data
    if tat_file:
        st.session_state.tat_df, detected_cols, tat_messages, st.session_state.association = load_tat_data(tat_file.getvalue())
        
        for msg in tat_messages:
            if "✅" in msg or "📊" in msg:
                st.success(msg)
            elif "⚠️" in msg:
                st.warning(msg)
            else:
                st.info(f"ℹ️ {msg}")
        
        if not st.session_state.tat_df.empty:
            st.success(f"✅ TAT Data loaded: {len(st.session_state.tat_df):,} records")
    
    st.markdown("---")
    
    # Create client mapping if both datasets exist
    if not st.session_state.trip_df.empty and not st.session_state.tat_df.empty:
        st.session_state.client_mapping = create_client_mapping(
            st.session_state.trip_df, st.session_state.tat_df
        )
        
        if st.session_state.client_mapping:
            matched = sum(1 for k, v in st.session_state.client_mapping.items() if k == v)
            fuzzy = len(st.session_state.client_mapping) - matched
            st.success(f"🔗 Client mapping created: {matched} exact matches, {fuzzy} fuzzy matches")
    
    # Tabs for analysis
    if not st.session_state.trip_df.empty or not st.session_state.tat_df.empty:
        tab1, tab2 = st.tabs(["🚛 Trip Analysis", "📊 TAT Report"])
        
        with tab1:
            if not st.session_state.trip_df.empty:
                render_trip_analysis(st.session_state.trip_df)
            else:
                st.info("Upload trip report files to see analysis")
        
        with tab2:
            if not st.session_state.tat_df.empty:
                # Pass trip numbers if available
                trip_filters = None
                if not st.session_state.trip_df.empty:
                    trip_filters = {'trip_nos': st.session_state.trip_df['trip_no'].unique().tolist()}
                render_tat_report(st.session_state.tat_df, st.session_state.association, trip_filters)
            else:
                st.info("Upload TAT data file to see analysis")
    else:
        st.info("👈 Upload your data files to begin analysis")
        
        # Help section
        with st.expander("📖 How to Use - Client-Plant Association Feature"):
            st.markdown(f"""
            ### Predefined Clients:
            {', '.join(PREDEFINED_CLIENTS)}
            
            ### How Client-Plant Association Works:
            
            1. **TAT Data Source Column**: The dashboard automatically detects and uses the **Source/Plant** column from your TAT data
            2. **Automatic Association**: Each client is automatically associated with the plants/sources that appear in their TAT records
            3. **"All Plants" Selection**: When "All Plants/Sources" is selected, ALL plants associated with the selected client are included
            4. **Smart Filtering**: Plant options are filtered based on the selected client using actual data
            
            ### Required Columns:
            
            **Trip Report Files:**
            - Must contain: Trip No, Client, Destination
            - Optional: Plant, Inv Qty, Trip Type, Start Date
            
            **TAT Data File:**
            - Must contain: Trip No, Client
            - Must contain: **Source/Plant** column (any of: Plant, Source, Source Plant, Origin)
            - TAT stage columns (values in minutes)
            
            ### Features:
            - Automatic column detection
            - Fuzzy client name matching
            - Client-Plant association visualization
            - Export capabilities for all tables
            """)

if __name__ == "__main__":
    main()
