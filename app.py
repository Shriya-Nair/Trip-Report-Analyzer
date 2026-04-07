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
    .dedup-info {
        background: #fff8e1;
        border-left: 4px solid #f59e0b;
        border-radius: 6px;
        padding: 12px 16px;
        margin: 8px 0;
        font-size: 0.88rem;
        color: #78350f;
    }
</style>
""", unsafe_allow_html=True)

# ── Drill-Down Modal Component ───────────────────────────────────────────────
@st.dialog("📋 Trip Details", width="large")
def show_trip_details(destination, trips_df):
    st.markdown(f"### 🚛 Trips to **{destination}**")
    st.markdown(f"**Total Trips:** {len(trips_df)}")

    total_qty = trips_df["Inv Qty"].sum() if "Inv Qty" in trips_df.columns else 0

    col1, col2, col3, col4 = st.columns(4)
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
    with col4:
        if total_qty > 0:
            st.metric("Total Quantity", f"{total_qty:,.2f}")

    st.divider()

    st.subheader("📊 Detailed Trip List")
    display_cols = ["Trip No", "Start Date", "Trip Type", "Client", "Plant", "Inv Qty", "Source File", "_dedup_note"]
    available_cols = [col for col in display_cols if col in trips_df.columns]

    col_config = {
        "Trip No": "Trip Number",
        "Start Date": st.column_config.DateColumn("Date"),
        "Trip Type": st.column_config.TextColumn("Type"),
        "Client": st.column_config.TextColumn("Client"),
        "Plant": st.column_config.TextColumn("Source Plant"),
        "Inv Qty": st.column_config.NumberColumn("Quantity", format="%.2f"),
        "Source File": st.column_config.TextColumn("Report Source"),
        "_dedup_note": st.column_config.TextColumn("Dedup Note"),
    }

    st.dataframe(
        trips_df[available_cols],
        use_container_width=True,
        height=400,
        hide_index=True,
        column_config=col_config,
    )

    csv = trips_df[available_cols].to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download this destination's trips (CSV)",
        data=csv,
        file_name=f"trips_to_{destination}.csv",
        mime="text/csv",
    )


# ── Destination Name Similarity ───────────────────────────────────────────────
def _normalize(name: str) -> str:
    """Lowercase, strip punctuation/extra spaces for fuzzy matching."""
    import re
    name = str(name).lower().strip()
    name = re.sub(r"[^\w\s]", "", name)
    name = re.sub(r"\s+", " ", name)
    return name


def _similar(a: str, b: str, threshold: float = 0.82) -> bool:
    """Return True if two destination names are likely the same place."""
    na, nb = _normalize(a), _normalize(b)
    if na == nb:
        return True
    ratio = SequenceMatcher(None, na, nb).ratio()
    return ratio >= threshold


def _canonical_destination(destinations: pd.Series) -> str:
    """
    Given multiple destination strings for the same Trip No,
    pick the canonical (most common / longest) name.
    """
    counts = destinations.value_counts()
    # prefer the most frequent; tie-break by longest (most descriptive)
    top_count = counts.iloc[0]
    candidates = counts[counts == top_count].index.tolist()
    return max(candidates, key=len)


def _build_destination_alias_map(all_destinations: pd.Series, threshold: float = 0.82) -> dict:
    """
    Cluster all unique destination names by similarity.
    Returns {variant_name: canonical_name}.
    """
    unique_dests = all_destinations.dropna().unique().tolist()
    alias_map: dict[str, str] = {}
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

    for cluster in clusters:
        # canonical = longest name in the cluster (most descriptive)
        canonical = max(cluster, key=len)
        for variant in cluster:
            alias_map[variant] = canonical

    return alias_map


# ── Core Deduplication Logic ──────────────────────────────────────────────────
def deduplicate_trips(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Deduplicate rows by Trip No.

    Rules:
    1. If all rows for a Trip No share the same destination → sum Inv Qty, keep one row.
    2. If destinations look like name-variants of the same place (fuzzy match) →
       standardize to canonical name, sum Inv Qty, keep one row.
    3. If destinations are genuinely different → keep the row with the highest
       Inv Qty (assumed to be the actual loaded leg); log the dropped rows.

    Returns:
        (deduped_df, audit_df) where audit_df records every merge/drop action.
    """
    if "Trip No" not in df.columns:
        return df, pd.DataFrame()

    # First build a global alias map across all destinations in this dataset
    alias_map = _build_destination_alias_map(df["Destination"].fillna("Unknown"))

    # Apply alias map to standardize names before grouping
    df = df.copy()
    df["Destination"] = df["Destination"].map(lambda d: alias_map.get(d, d))

    duplicated_mask = df.duplicated(subset=["Trip No"], keep=False)
    unique_df = df[~duplicated_mask].copy()
    dup_df = df[duplicated_mask].copy()

    if dup_df.empty:
        unique_df["_dedup_note"] = ""
        return unique_df, pd.DataFrame()

    audit_records = []
    merged_rows = []

    for trip_no, group in dup_df.groupby("Trip No"):
        destinations = group["Destination"].dropna().unique().tolist()

        # ── Case A: all destinations identical (or already aliased to same) ──
        if len(destinations) == 1:
            representative = group.iloc[0].copy()
            representative["Inv Qty"] = group["Inv Qty"].sum()
            representative["_dedup_note"] = (
                f"Merged {len(group)} rows (same destination, summed qty)"
            )
            merged_rows.append(representative)
            audit_records.append({
                "Trip No": trip_no,
                "Action": "MERGED – same destination",
                "Destinations Found": "; ".join(destinations),
                "Canonical Destination": destinations[0],
                "Original Qty Values": "; ".join(group["Inv Qty"].astype(str).tolist()),
                "Final Qty": group["Inv Qty"].sum(),
                "Rows Affected": len(group),
            })

        # ── Case B: genuinely different destinations ──────────────────────────
        else:
            # Pick the row with the highest Inv Qty as the authoritative trip leg
            best_idx = group["Inv Qty"].idxmax()
            representative = group.loc[best_idx].copy()
            representative["_dedup_note"] = (
                f"Kept highest-qty leg ({representative['Destination']}) "
                f"from {len(group)} rows with different destinations"
            )
            merged_rows.append(representative)

            dropped_rows = group[group.index != best_idx]
            for _, dropped in dropped_rows.iterrows():
                audit_records.append({
                    "Trip No": trip_no,
                    "Action": "KEPT BEST LEG – different destinations",
                    "Destinations Found": "; ".join(destinations),
                    "Canonical Destination": representative["Destination"],
                    "Original Qty Values": "; ".join(group["Inv Qty"].astype(str).tolist()),
                    "Final Qty": representative["Inv Qty"],
                    "Rows Affected": len(group),
                })

    merged_df = pd.DataFrame(merged_rows)
    unique_df["_dedup_note"] = ""

    final_df = pd.concat([unique_df, merged_df], ignore_index=True)
    audit_df = pd.DataFrame(audit_records) if audit_records else pd.DataFrame()

    return final_df, audit_df


# ── Header ───────────────────────────────────────────────────────────────────
st.title("🚛 Monthly Trip Report Analyzer")
st.markdown("Upload one or more monthly trip reports to explore trips by client, plant, and destination.")
st.divider()

# ── File Upload ───────────────────────────────────────────────────────────────
uploaded_files = st.file_uploader(
    "Upload Trip Report(s) (.xlsx)",
    type=["xlsx"],
    accept_multiple_files=True,
    help="You can upload multiple monthly reports at once.",
)

REQUIRED_COLS = {"Client", "Destination", "Start Date", "Trip No", "Trip Type"}


@st.cache_data
def load_files(files_data: list[tuple]) -> tuple[pd.DataFrame, pd.DataFrame]:
    frames = []
    for name, data in files_data:
        try:
            df = pd.read_excel(BytesIO(data), sheet_name=0)
            missing = REQUIRED_COLS - set(df.columns)
            if missing:
                st.warning(f"⚠️ **{name}** is missing columns: {missing}. Skipping.")
                continue

            df.loc[(df["Trip Type"].str.lower() == "empty") & (df["Client"].isna()), "Client"] = "EMPTY TRIP - NO CLIENT"
            df.loc[(df["Trip Type"].str.lower() == "empty") & (df["Client"] == ""), "Client"] = "EMPTY TRIP - NO CLIENT"

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

            if "Inv Qty" not in df.columns:
                df["Inv Qty"] = 0.0
                st.info(f"📌 **{name}** doesn't have 'Inv Qty' column. Using 0 as default quantity.")
            else:
                df["Inv Qty"] = pd.to_numeric(df["Inv Qty"], errors="coerce").fillna(0).astype(float)

            df["_source_file"] = name
            df["Source File"] = name
            frames.append(df)
        except Exception as e:
            st.error(f"Could not read **{name}**: {e}")

    if not frames:
        return pd.DataFrame(), pd.DataFrame()

    combined = pd.concat(frames, ignore_index=True)

    combined["Start Date"] = pd.to_datetime(combined["Start Date"], dayfirst=True, errors="coerce")
    combined["Month"] = combined["Start Date"].dt.to_period("M").astype(str)
    combined["Trip Type"] = combined["Trip Type"].str.title()

    # ── DEDUPLICATION ─────────────────────────────────────────────────────────
    rows_before = len(combined)
    combined, audit_df = deduplicate_trips(combined)
    rows_after = len(combined)
    removed = rows_before - rows_after

    if removed > 0:
        st.toast(f"🔁 Deduplication removed {removed:,} duplicate row(s). See the Deduplication Report below.", icon="ℹ️")

    return combined, audit_df


# ── Main Logic ────────────────────────────────────────────────────────────────
if uploaded_files:
    files_data = [(f.name, f.read()) for f in uploaded_files]
    result = load_files(files_data)

    if isinstance(result, tuple):
        df, audit_df = result
    else:
        df, audit_df = result, pd.DataFrame()

    if df.empty:
        st.error("No valid data could be loaded. Please check your files.")
        st.stop()

    # ── Deduplication Summary Banner ──────────────────────────────────────────
    if not audit_df.empty:
        with st.expander(f"🔁 Deduplication Report — {len(audit_df)} trip(s) were merged or resolved", expanded=False):
            st.markdown("""
**How duplicates were handled:**
- **Same destination variants** (e.g. `PUNE` vs `Pune`) → names standardized to a single canonical form, quantities summed.
- **Genuinely different destinations** → the trip leg with the highest invoice quantity was kept as the authoritative record; others were dropped.
- All original values are logged below for full traceability.
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
            csv_audit = audit_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Download Deduplication Audit Log (CSV)",
                data=csv_audit,
                file_name="deduplication_audit.csv",
                mime="text/csv",
            )

    # ── Top-level metrics ─────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    total_trips_all = len(df)
    loaded_trips_all = len(df[df["Trip Type"] == "Loaded"])
    empty_trips_all = len(df[df["Trip Type"] == "Empty"])
    total_qty_all = df["Inv Qty"].sum() if "Inv Qty" in df.columns else 0

    with col1:
        st.metric("Total Trips (All)", f"{total_trips_all:,}")
    with col2:
        st.metric("Loaded Trips", f"{loaded_trips_all:,}",
                  delta=f"{(loaded_trips_all/total_trips_all*100):.1f}%" if total_trips_all > 0 else "0%")
    with col3:
        st.metric("Empty Trips", f"{empty_trips_all:,}",
                  delta=f"{(empty_trips_all/total_trips_all*100):.1f}%" if total_trips_all > 0 else "0%")
    with col4:
        st.metric("Total Quantity", f"{total_qty_all:,.2f}")

    st.success(f"✅ Loaded **{len(df):,}** unique trip records from **{len(files_data)}** file(s).")
    st.info("💡 **Tip:** Click on any destination in the table to see detailed trip information!")

    # ── Filters ──────────────────────────────────────────────────────────────
    st.subheader("🔍 Filter Your Data")

    clients = sorted(df["Client"].dropna().unique().tolist())
    regular_clients = [c for c in clients if not c.startswith("EMPTY TRIP")]
    empty_trip_option = [c for c in clients if c.startswith("EMPTY TRIP")]
    client_options = regular_clients + (empty_trip_option if empty_trip_option else [])

    col1, col2 = st.columns(2)
    with col1:
        selected_client = st.selectbox("🏢 Select Client", client_options)
    with col2:
        client_plants = sorted(df[df["Client"] == selected_client]["Plant"].dropna().unique().tolist())
        selected_plants = st.multiselect(
            "🏭 Select Plant/Source (Multiple allowed)",
            options=client_plants,
            default=client_plants,
            help="You can select multiple plants to analyze together",
        )
        if not selected_plants:
            st.warning("⚠️ Please select at least one plant")
            st.stop()

    col3, col4, col5 = st.columns(3)
    with col3:
        months = sorted(df["Month"].dropna().unique().tolist(), reverse=True)
        selected_month = st.selectbox("📅 Select Month", ["All Months"] + months)
    with col4:
        trip_type_options = ["All Types"] + sorted(df["Trip Type"].dropna().unique().tolist())
        selected_type = st.selectbox("🔄 Trip Type", trip_type_options)
    with col5:
        if st.button("🗑️ Clear All Filters", use_container_width=True):
            st.rerun()

    st.divider()

    # ── Apply filters ─────────────────────────────────────────────────────────
    filtered = df[df["Client"] == selected_client].copy()
    filtered = filtered[filtered["Plant"].isin(selected_plants)]
    if selected_month != "All Months":
        filtered = filtered[filtered["Month"] == selected_month]
    if selected_type != "All Types" and "Trip Type" in filtered.columns:
        filtered = filtered[filtered["Trip Type"] == selected_type]

    # ── KPI Cards ─────────────────────────────────────────────────────────────
    total_trips = len(filtered)
    loaded_trips = len(filtered[filtered["Trip Type"] == "Loaded"]) if "Trip Type" in filtered.columns else 0
    empty_trips = len(filtered[filtered["Trip Type"] == "Empty"]) if "Trip Type" in filtered.columns else 0
    unique_dest = filtered["Destination"].nunique()
    unique_plants = filtered["Plant"].nunique()
    unique_months = filtered["Month"].nunique()
    total_qty = filtered["Inv Qty"].sum() if "Inv Qty" in filtered.columns else 0

    st.caption(f"📌 **Selected Plants ({len(selected_plants)}):** {', '.join(selected_plants[:5])}{'...' if len(selected_plants) > 5 else ''}")

    if selected_client.startswith("EMPTY TRIP"):
        k1, k2, k3, k4, k5 = st.columns(5)
        cards = [
            (k1, total_trips, "Total Empty Trips"),
            (k2, unique_dest, "Unique Destinations"),
            (k3, unique_plants, "Source Plants"),
            (k4, unique_months, "Months Covered"),
            (k5, f"{total_qty:,.2f}", "Total Quantity"),
        ]
    else:
        k1, k2, k3, k4, k5, k6 = st.columns(6)
        cards = [
            (k1, f"{total_trips:,}", "Total Trips"),
            (k2, loaded_trips, "Loaded Trips"),
            (k3, empty_trips, "Empty Trips"),
            (k4, unique_dest, "Unique Destinations"),
            (k5, unique_plants, "Plants/Sources"),
            (k6, f"{total_qty:,.2f}", "Total Quantity"),
        ]

    for col, val, label in cards:
        with col:
            st.markdown(
                f'<div class="metric-card"><div class="metric-number">{val}</div>'
                f'<div class="metric-label">{label}</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Destination Summary Table ─────────────────────────────────────────────
    if selected_client.startswith("EMPTY TRIP"):
        st.subheader("📍 Empty Trip Destinations (No Client Association)")
    else:
        st.subheader(f"📍 Trips to Each Destination — {selected_client}")
    st.caption("💡 **Click on any destination row** to see detailed trip information")

    if filtered.empty:
        st.info("No trips found for the selected filters.")
    else:
        agg_dict = {
            "Total_Trips": ("Trip No", "count"),
            "Total_Qty": ("Inv Qty", "sum"),
            "Plants": ("Plant", lambda x: x.nunique()),
        }

        if "Trip Type" in filtered.columns and len(filtered["Trip Type"].unique()) > 1:
            agg_dict["Loaded_Trips"] = ("Trip Type", lambda x: (x == "Loaded").sum())
            agg_dict["Empty_Trips"] = ("Trip Type", lambda x: (x == "Empty").sum())
            agg_dict["Loaded_Qty"] = (
                "Inv Qty",
                lambda x: x[filtered.loc[x.index, "Trip Type"] == "Loaded"].sum(),
            )
            agg_dict["Empty_Qty"] = (
                "Inv Qty",
                lambda x: x[filtered.loc[x.index, "Trip Type"] == "Empty"].sum(),
            )

        dest_summary = (
            filtered.groupby("Destination")
            .agg(**agg_dict)
            .reset_index()
            .sort_values("Total_Trips", ascending=False)
            .rename(columns={
                "Total_Trips": "Total Trips",
                "Total_Qty": "Total Quantity",
                "Plants": "Plants Used",
                "Loaded_Trips": "Loaded Trips",
                "Empty_Trips": "Empty Trips",
                "Loaded_Qty": "Loaded Quantity",
                "Empty_Qty": "Empty Quantity",
            })
        )

        chart_type = st.radio("📊 Display Chart Type", ["Total Trips", "Total Quantity"], horizontal=True)

        if chart_type == "Total Trips":
            fig = px.bar(
                dest_summary.head(20), x="Destination", y="Total Trips",
                title="Top 20 Destinations by Trip Count",
                color="Total Trips", color_continuous_scale="Blues", text="Total Trips",
            )
            fig.update_traces(textposition="outside")
        else:
            fig = px.bar(
                dest_summary.head(20), x="Destination", y="Total Quantity",
                title="Top 20 Destinations by Total Quantity",
                color="Total Quantity", color_continuous_scale="Greens", text="Total Quantity",
            )
            fig.update_traces(texttemplate="%{text:,.2f}", textposition="outside")

        fig.update_traces(hovertemplate="<b>%{x}</b><br>%{y:,.2f}<extra></extra>")
        fig.update_layout(xaxis_tickangle=-45, height=500, clickmode="event+select")

        chart_col, table_col = st.columns([1, 1])

        with chart_col:
            st.plotly_chart(fig, use_container_width=True)

        with table_col:
            st.markdown("#### 📋 Destinations Summary")
            st.info("💡 **Click the 🔍 button next to any destination** to see detailed trip information!")

            for idx, row in dest_summary.iterrows():
                destination = row["Destination"]
                col1, col2, col3, col4, col5 = st.columns([0.4, 0.15, 0.15, 0.2, 0.1])
                with col1:
                    st.write(f"**{destination}**")
                with col2:
                    st.write(f"{row['Total Trips']} trips")
                with col3:
                    st.write(f"📦 {row['Total Quantity']:,.2f}")
                with col4:
                    if "Loaded Trips" in row:
                        st.write(f"🟢 {row['Loaded Trips']} / 🔴 {row['Empty Trips']}")
                with col5:
                    if st.button("🔍", key=f"drill_{destination}_{idx}", help=f"View details for {destination}"):
                        destination_trips = filtered[filtered["Destination"] == destination].copy()
                        show_trip_details(destination, destination_trips)

        # ── Plant Summary ─────────────────────────────────────────────────────
        if len(selected_plants) > 1 and unique_plants > 1:
            st.divider()
            st.subheader("🏭 Trip Distribution by Plant with Quantity")

            plant_summary = (
                filtered.groupby("Plant")
                .agg(
                    Total_Trips=("Trip No", "count"),
                    Total_Qty=("Inv Qty", "sum"),
                    Loaded_Trips=("Trip Type", lambda x: (x == "Loaded").sum()),
                    Empty_Trips=("Trip Type", lambda x: (x == "Empty").sum()),
                    Unique_Destinations=("Destination", "nunique"),
                )
                .reset_index()
                .sort_values("Total_Trips", ascending=False)
            )

            col_pie, col_plant_table = st.columns([1, 1])
            with col_pie:
                qty_fig = px.bar(
                    plant_summary, x="Plant", y="Total_Qty",
                    title="Total Quantity by Plant",
                    color="Total_Qty", color_continuous_scale="Greens", text="Total_Qty",
                )
                qty_fig.update_traces(texttemplate="%{text:,.2f}", textposition="outside")
                qty_fig.update_layout(xaxis_tickangle=-45, height=350)
                st.plotly_chart(qty_fig, use_container_width=True)

            with col_plant_table:
                st.dataframe(
                    plant_summary,
                    use_container_width=True,
                    height=350,
                    hide_index=True,
                    column_config={
                        "Plant": "Source Plant",
                        "Total_Trips": "Total Trips",
                        "Total_Qty": st.column_config.NumberColumn("Total Quantity", format="%.2f"),
                        "Loaded_Trips": "Loaded",
                        "Empty_Trips": "Empty",
                        "Unique_Destinations": "Destinations",
                    },
                )

        # ── Empty Trip Movement ───────────────────────────────────────────────
        if selected_client.startswith("EMPTY TRIP"):
            st.divider()
            st.subheader("🔄 Empty Trip Movement Analysis")

            empty_movement = (
                filtered.groupby(["Plant", "Destination"])
                .agg(
                    Number_of_Empty_Trips=("Trip No", "count"),
                    Total_Quantity=("Inv Qty", "sum"),
                )
                .reset_index()
                .sort_values("Number_of_Empty_Trips", ascending=False)
                .head(20)
            )

            st.dataframe(
                empty_movement,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Plant": "Source Plant",
                    "Destination": "Destination",
                    "Number_of_Empty_Trips": "Trip Count",
                    "Total_Quantity": st.column_config.NumberColumn("Total Quantity", format="%.2f"),
                },
            )

        # ── Download ──────────────────────────────────────────────────────────
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

        plants_label = f"{len(selected_plants)}_plants" if len(selected_plants) > 1 else selected_plants[0].replace(" ", "_")
        month_label = selected_month.replace(" ", "_") if selected_month != "All Months" else "All_Months"
        client_label = selected_client.replace(" ", "_").replace("-", "_")[:50]
        st.download_button(
            label="⬇️ Download Summary as Excel",
            data=export_buf,
            file_name=f"{client_label}_{plants_label}_{month_label}_trip_summary.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

else:
    st.markdown("""
    <div style="text-align:center; padding: 60px 20px; color: #888;">
        <div style="font-size:4rem;">📂</div>
        <h3 style="color:#555;">No file uploaded yet</h3>
        <p>Upload your monthly trip report(s) above to get started.</p>
        <p style="font-size:0.85rem; margin-top:10px;"><strong>Required columns:</strong> <code>Client</code>, <code>Destination</code>, <code>Start Date</code>, <code>Trip No</code>, <code>Trip Type</code><br>
        <strong>Optional columns:</strong> <code>Inv Qty</code> — for quantity analysis (supports decimals)<br>
        <strong>Features:</strong><br>
        • 🔁 <strong>Smart Deduplication</strong> — duplicate Trip Nos are auto-merged; fuzzy name matching resolves destination variants<br>
        • 🏭 <strong>Multi-Plant Selection</strong> — select multiple plants to analyze together<br>
        • 📦 <strong>Decimal Precision</strong> — shows exact quantities with 2 decimal places<br>
        • 🔍 <strong>Drill-down modal</strong> — click on any destination to see detailed trip information<br>
        • 📊 <strong>Interactive charts</strong> — toggle between Trip Count and Quantity views<br>
        <strong>Optional:</strong> <code>Source</code>, <code>Source Place</code>, or <code>Plant</code> for plant-level filtering</p>
    </div>
    """, unsafe_allow_html=True)
