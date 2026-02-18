# dashboard.py

import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from auth import check_role # Assuming 'auth.py' exists and provides this function
from datetime import datetime, timedelta

# --- Utility Functions ---

def calculate_kpis(df):
    """Calculates key performance indicators."""
    total_production = df['Actual_Production_Units'].sum()
    total_planned = df['Planned_Production_Units'].sum()
    total_raw_used = df['Raw_Material_Used_kg'].sum()
    total_waste = df['Waste_Weight_kg'].sum()
    total_downtime = df['Downtime_Minutes'].sum()
    total_run_time = df['Total_Time_Run_Minutes'].sum()
    
    # Calculations
    production_efficiency = (total_production / total_planned) if total_planned else 0
    # The formula for Yield Rate seems to be Material Efficiency, not true yield rate.
    # Yield Rate = (Total Output / Total Input)
    # If Raw Material Used is the input, and Total Waste is the loss, then:
    # Output = Raw_Material_Used - Waste
    yield_rate = (total_raw_used - total_waste) / total_raw_used if total_raw_used else 0
    utilization = total_run_time / (total_run_time + total_downtime) if (total_run_time + total_downtime) else 0

    return {
        "Total Production (Units)": f"{total_production:,.0f}",
        "Overall Efficiency": f"{production_efficiency:.2%}",
        "Raw Material Yield": f"{yield_rate:.2%}",
        "Total Waste (kg)": f"{total_waste:,.1f}",
        "Total Downtime (min)": f"{total_downtime:,.0f}",
        "Utilization Rate": f"{utilization:.2%}"
    }

def custom_metric_card(container, label, value, full_value):
    """
    Creates a Streamlit-styled card using markdown with a full-box hover tooltip.
    The 'title' attribute in HTML handles the tooltip display.
    
    NOTE: Simplified the HTML string to a single line inside the f-string 
    to prevent parsing issues when used inside st.columns.
    """
    hover_text = f"{label} | Full Value: {full_value}"
    
    # Using a single-line f-string for HTML to minimize potential parsing errors
    html_card = f"""
<div style="background-color: #3C3C3C; padding: 15px; border-radius: 10px; border: 1px solid #4D4D4D; box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2); height: 100%; cursor: help; margin-bottom: 10px;" title="{hover_text}">
    <p style="font-size: 13px; color: #ADADAD; margin: 0;">{label}</p>
    <h3 style="font-size: 24px; color: #F0F2F6; margin-top: 5px;">{value}</h3>
</div>
"""
    # The container (a column object) is explicitly used to render the markdown.
    # The crucial part is 'unsafe_allow_html=True'
    container.markdown(html_card, unsafe_allow_html=True)


def create_filters(df):
    """Creates sidebar filters and returns the filtered DataFrame."""
    st.sidebar.header("🔍 Report Filters")
    
    # Date Range Filter
    # Ensure 'Date' column is in datetime format before getting min/max
    df['Date'] = pd.to_datetime(df['Date'])
    min_date = df['Date'].min().date()
    max_date = df['Date'].max().date()
    
    # Set default date range to the last 7 days of the data, if possible
    default_end = max_date
    default_start = max_date - timedelta(days=6) if max_date - timedelta(days=6) >= min_date else min_date
    
    date_range = st.sidebar.date_input(
        "Date Range", 
        value=(default_start, default_end), 
        min_value=min_date, 
        max_value=max_date
    )
    
    # Apply date filter
    if len(date_range) == 2:
        start_date = pd.to_datetime(date_range[0])
        # Add a day to the end date to include all data on the final selected day
        end_date = pd.to_datetime(date_range[1]) + pd.Timedelta(days=1) 
        df_filtered = df[(df['Date'] >= start_date) & (df['Date'] < end_date)]
    else:
        df_filtered = df.copy()

    # Multi-select Filters - Use df_filtered to ensure filter options reflect date range
    shifts = df_filtered['Shift'].unique()
    selected_shifts = st.sidebar.multiselect("Select Shift(s)", options=shifts, default=shifts)

    products = df_filtered['Product_Name'].unique()
    selected_products = st.sidebar.multiselect("Select Product(s)", options=products, default=products)
    
    operators = df_filtered['Machine_Operator_ID'].unique()
    selected_operators = st.sidebar.multiselect("Select Operator(s)", options=operators, default=operators)
    
    # Handling potential NaNs in 'Downtime_Reason' before getting unique
    downtime_reasons = df_filtered['Downtime_Reason'].astype(str).unique()
    selected_reasons = st.sidebar.multiselect("Select Downtime Reason(s)", options=downtime_reasons, default=downtime_reasons)

    df_filtered = df_filtered[
        df_filtered['Shift'].isin(selected_shifts) &
        df_filtered['Product_Name'].isin(selected_products) &
        df_filtered['Machine_Operator_ID'].isin(selected_operators) &
        df_filtered['Downtime_Reason'].astype(str).isin(selected_reasons) # Match dtype here
    ]
    
    st.sidebar.info(f"Filtered Data: {len(df_filtered)} rows.")
    
    return df_filtered

def generate_insights(df):
    """Generates textual production intelligence insights."""
    if df.empty:
        return "No data available to generate insights."

    summary = []
    
    # Weekly comparison 
    # Use the full date range covered by the filter for comparison, not just resampling the filtered view
    # For simplicity, we'll keep the current implementation that compares the last two *complete* weeks in the filtered data.
    df_weekly = df.set_index('Date').resample('W').agg({'Actual_Production_Units': 'sum'})
    if len(df_weekly) >= 2:
        last_week_prod = df_weekly['Actual_Production_Units'].iloc[-1]
        prev_week_prod = df_weekly['Actual_Production_Units'].iloc[-2]
        
        # Avoid division by zero
        if prev_week_prod != 0:
            change = (last_week_prod - prev_week_prod) / prev_week_prod * 100
            trend = "increased" if change >= 0 else "decreased"
            summary.append(f"Production Trend: Total output has **{trend} by {abs(change):.1f}%** compared to the previous reporting period.")
        else:
            summary.append("Production Trend: Comparison to previous period is not possible (zero production).")
    else:
        summary.append("Production Trend: Only one or less weeks of data available in the current filter selection for trend analysis.")

    # Best/Worst Product
    prod_summary = df.groupby('Product_Name')['Actual_Production_Units'].sum().sort_values(ascending=False)
    # Check if prod_summary is empty (shouldn't be if df is not empty, but good practice)
    if not prod_summary.empty:
        best_product = prod_summary.index[0]
        worst_product = prod_summary.index[-1]
        summary.append(f"Highest Volume: **{best_product}** is the highest produced product.")
    
    # Top Downtime Reason
    downtime_summary = df.groupby('Downtime_Reason')['Downtime_Minutes'].sum().sort_values(ascending=False)
    if not downtime_summary.empty:
        top_downtime = downtime_summary.index[0]
        top_downtime_mins = downtime_summary.iloc[0]
        summary.append(f"Actionable Insight: The primary cause of stoppages is **{top_downtime}**, accounting for **{top_downtime_mins:,.0f} minutes** of downtime.")

    return " | ".join(summary)


def dashboard_page():
    """Main Streamlit dashboard and visualization page."""
    
    st.title("📊 Weekly Production Dashboard")
    st.markdown("---")
    
    # Add a global CSS block for consistent styling if needed
    st.markdown("""
    <style>
    /* General styles for the entire app if necessary, e.g. wider columns */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
        padding-left: 5%;
        padding-right: 5%;
    }
    </style>
    """, unsafe_allow_html=True)
    
    if not check_role('Viewer'): # Assuming Viewer is the lowest level
        st.error("You do not have the required role to view this dashboard.")
        return
        
    if 'df' not in st.session_state or st.session_state['df'].empty:
        st.warning("No dataset loaded. Please load data on the 'Load & Manage Dataset' page.")
        return

    # --- 1. Filtering ---
    df_filtered = create_filters(st.session_state['df'])
    
    if df_filtered.empty:
        st.warning("No data matches the current filter criteria.")
        return

    # --- 2. Production Intelligence / Textual Summary ---
    st.header("📈 Production Intelligence Summary")
    insights = generate_insights(df_filtered)
    st.markdown(f"**{insights}**")
    st.markdown("---")


    # --- 3. KPIs Card View ---
    kpis = calculate_kpis(df_filtered)
    
    st.header("🔑 Key Performance Indicators")
    
    # Define columns first, then pass each column container to the custom card function
    cols = st.columns(6)
    
    # 1. Total Production
    custom_metric_card(
        cols[0],
        label="Total Production (Units)",
        value=kpis["Total Production (Units)"],
        full_value=kpis["Total Production (Units)"]
    )

    # 2. Overall Efficiency 
    custom_metric_card(
        cols[1],
        label="Overall Efficiency", 
        value=kpis["Overall Efficiency"],
        full_value=kpis["Overall Efficiency"]
    )

    # 3. Raw Material Yield
    custom_metric_card(
        cols[2],
        label="Raw Material Yield", 
        value=kpis["Raw Material Yield"],
        full_value=kpis["Raw Material Yield"]
    )

    # 4. Total Waste (kg)
    custom_metric_card(
        cols[3],
        label="Total Waste (kg)", 
        value=kpis["Total Waste (kg)"],
        full_value=kpis["Total Waste (kg)"]
    )

    # 5. Total Downtime (min)
    custom_metric_card(
        cols[4],
        label="Total Downtime (min)", 
        value=kpis["Total Downtime (min)"],
        full_value=kpis["Total Downtime (min)"]
    )

    # 6. Utilization Rate
    custom_metric_card(
        cols[5],
        label="Utilization Rate", 
        value=kpis["Utilization Rate"],
        full_value=kpis["Utilization Rate"]
    )
    
    st.markdown("---")

    # --- 4. Interactive Charts ---
    st.header("Interactive Visualizations")
    
    tab1, tab2, tab3 = st.tabs(["Production Over Time", "Product & Shift Breakdown", "Downtime Analysis"])

    with tab1:
        st.subheader("Production & Downtime Over Time")
        df_daily = df_filtered.groupby('Date').agg({
            'Actual_Production_Units': 'sum',
            'Downtime_Minutes': 'sum'
        }).reset_index()
        
        fig = px.line(
            df_daily, 
            x='Date', 
            y='Actual_Production_Units', 
            title='Daily Total Production (Units)', 
            labels={'Actual_Production_Units': 'Production Units'},
            template='plotly_dark'
        )
        st.plotly_chart(fig, width='stretch')
        
        fig2 = px.bar(
            df_daily, 
            x='Date', 
            y='Downtime_Minutes', 
            title='Daily Total Downtime (Minutes)',
            labels={'Downtime_Minutes': 'Downtime (min)'},
            template='plotly_dark'
        )
        st.plotly_chart(fig2, width='stretch')

    with tab2:
        st.subheader("Product & Shift Production Breakdown")
        df_prod_shift = df_filtered.groupby(['Product_Name', 'Shift'])['Actual_Production_Units'].sum().reset_index()
        
        fig_bar = px.bar(
            df_prod_shift,
            x='Product_Name',
            y='Actual_Production_Units',
            color='Shift',
            title='Total Production by Product and Shift',
            labels={'Actual_Production_Units': 'Units', 'Product_Name': 'Product'},
            template='plotly_dark'
        )
        st.plotly_chart(fig_bar, width='stretch')
        
    with tab3:
        st.subheader("Downtime Reason Distribution")
        df_downtime = df_filtered.groupby('Downtime_Reason')['Downtime_Minutes'].sum().reset_index()
        
        fig_pie = px.pie(
            df_downtime,
            names='Downtime_Reason',
            values='Downtime_Minutes',
            title='Distribution of Total Downtime Minutes by Reason',
            template='plotly_dark'
        )
        st.plotly_chart(fig_pie, width='stretch')
        
    # --- 5. Data Table (Analyst/Admin only can see the full table) ---
    if check_role('Analyst'):
        st.markdown("---")
        st.header("Raw Filtered Data Table")
        st.dataframe(df_filtered.drop(columns=['Row_ID'], errors='ignore'), width='stretch')

# Note: You need to ensure 'auth.py' exists and st.session_state['df'] is populated
# with a DataFrame containing the expected columns.