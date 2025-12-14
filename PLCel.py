import streamlit as st
import pandas as pd
import json
import plotly.express as px
import time

# --- 1. CONFIGURATION AND STYLING ---
st.set_page_config(
    page_title="Weekly Production Report",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject custom CSS for Dark UI and smooth animations
# The transition property on the main content container and
# the dark background colors provide the modern feel.
st.markdown("""
<style>
    /* General Dark Mode Colors */
    .stApp {
        background-color: #1e1e1e; /* Deep dark background */
        color: #f0f0f0; /* Light text */
    }
    
    /* Customizing Streamlit's Main Container for Smoothness */
    .stApp > div:first-child {
        transition: opacity 0.5s ease-in-out;
    }
    
    /* Sidebar styling */
    .css-1d391kg { /* Targetting the sidebar container */
        background-color: #2c2c2c; 
        transition: background-color 0.3s;
    }

    /* Primary button styling */
    .stButton>button {
        background-color: #007bff; /* Blue accent for buttons */
        color: white;
        border-radius: 8px;
        transition: all 0.3s ease; /* Smooth transition for hover/focus */
    }
    .stButton>button:hover {
        background-color: #0056b3;
        transform: scale(1.02); /* Simple hover animation */
    }
    
    /* Header/Title styling */
    h1, h2, h3 {
        color: #8c9eff; /* Lighter accent color for titles */
    }
</style>
""", unsafe_allow_html=True)


# --- 2. DUMMY DATASET (JSON Structure) ---
# In a real app, this function would load data from a database (e.g., SQL, MongoDB)
# based on the authenticated user's company ID.

DUMMY_DATA_JSON = """
{
    "company_a_id": "A123",
    "report_week": "2025-W49",
    "production_units": [
        {"product": "Widget-X", "target": 1200, "actual": 1150, "rework_count": 50, "defect_rate": 0.04},
        {"product": "Gadget-Y", "target": 800, "actual": 820, "rework_count": 15, "defect_rate": 0.018},
        {"product": "Thing-Z", "target": 500, "actual": 480, "rework_count": 30, "defect_rate": 0.06},
        {"product": "Module-A", "target": 1500, "actual": 1490, "rework_count": 10, "defect_rate": 0.006}
    ],
    "machine_downtime_hours": [
        {"machine": "CNC-01", "downtime": 5.2, "reason": "Maintenance"},
        {"machine": "Press-02", "downtime": 1.5, "reason": "Operator Error"},
        {"machine": "Assembly-03", "downtime": 0.5, "reason": "Material Shortage"},
        {"machine": "CNC-01", "downtime": 2.0, "reason": "Tool Change"}
    ]
}
"""

@st.cache_data
def load_data(company_id):
    """Simulates loading data from a database based on company ID."""
    # In a real application, you would use company_id to query your database.
    
    # Simulate a brief loading animation/delay
    with st.spinner(f"Loading data for **{company_id}**..."):
        time.sleep(1.0) # Smooth animation effect
        
    data = json.loads(DUMMY_DATA_JSON)
    production_df = pd.DataFrame(data['production_units'])
    downtime_df = pd.DataFrame(data['machine_downtime_hours'])
    
    return production_df, downtime_df, data['report_week']


# --- 3. VISUALIZATION FUNCTIONS (Interactive Plots) ---

def show_production_vs_target(df):
    """Bar Chart: Actual vs. Target Production."""
    st.subheader("🎯 Production vs. Target (Units)")
    
    # Create a long-form DataFrame for Plotly
    df_long = pd.melt(df, id_vars=['product'], value_vars=['target', 'actual'], 
                      var_name='Metric', value_name='Units')
    
    # Plotly Bar Chart (Interactive) - Uses a dark theme
    fig = px.bar(
        df_long, 
        x='product', 
        y='Units', 
        color='Metric', 
        barmode='group',
        text='Units',
        color_discrete_map={'target': '#FFD700', 'actual': '#17BECF'}, # Gold/Cyan for contrast
        title='Actual vs. Target Production by Product',
        height=400,
        template='plotly_dark' # **Modern Dark Theme**
    )
    fig.update_traces(textposition='outside')
    fig.update_layout(xaxis_title="Product", yaxis_title="Units Produced")
    st.plotly_chart(fig, use_container_width=True)

def show_rework_distribution(df):
    """Pie Chart: Distribution of Rework/Defects."""
    st.subheader("♻️ Rework Count Distribution")
    
    # Plotly Pie Chart (Interactive)
    fig = px.pie(
        df, 
        names='product', 
        values='rework_count', 
        title='Percentage of Rework Count by Product',
        hole=0.4, # Donut chart for modern look
        color_discrete_sequence=px.colors.qualitative.Pastel,
        template='plotly_dark' # **Modern Dark Theme**
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)

def show_downtime_breakdown(df):
    """Interactive Scatter Plot/Table for Downtime."""
    st.subheader("⏱️ Machine Downtime Analysis")
    
    # Aggregate downtime by reason for a bar chart
    downtime_summary = df.groupby('reason')['downtime'].sum().reset_index()
    
    fig = px.bar(
        downtime_summary,
        x='reason',
        y='downtime',
        color='reason',
        text='downtime',
        title='Total Downtime (Hours) by Reason',
        template='plotly_dark'
    )
    fig.update_traces(textposition='outside')
    st.plotly_chart(fig, use_container_width=True)
    
    # Interactive Table for Raw Data
    with st.expander("Show detailed downtime log"):
        st.dataframe(df, use_container_width=True, hide_index=True)


# --- 4. AUTHENTICATION LOGIC ---

def authenticate_user():
    """Simple hardcoded authentication for demonstration."""
    
    st.sidebar.title("🔒 User Login")
    
    # Placeholder for database/API login
    username = st.sidebar.text_input("Username (Hint: admin)", value="admin")
    password = st.sidebar.text_input("Password (Hint: pass123)", type="password", value="pass123")
    login_button = st.sidebar.button("Login")

    # Hardcoded credentials for demo
    VALID_USERS = {"admin": "pass123", "manager": "securepwd"}
    
    if login_button:
        if username in VALID_USERS and VALID_USERS[username] == password:
            st.session_state['authenticated'] = True
            st.session_state['username'] = username
            st.session_state['company_id'] = "A123" # Simulate loading company ID
            st.sidebar.success(f"Welcome, {username}!")
            # Use st.rerun() to immediately load the main content after successful login
            st.rerun() 
        else:
            st.sidebar.error("❌ Invalid Username or Password")
            st.session_state['authenticated'] = False

# --- 5. MAIN APP LAYOUT ---

def main_app():
    """Main dashboard layout after successful authentication."""
    
    # 1. Load Data
    production_df, downtime_df, report_week = load_data(st.session_state['company_id'])
    
    # 2. Header and Key Metrics
    st.title(f"📈 Weekly Production Report: {report_week}")
    
    # Key Metrics (Kicker Cards) - Use columns for a clean layout
    total_actual = production_df['actual'].sum()
    total_target = production_df['target'].sum()
    total_rework = production_df['rework_count'].sum()
    
    kpi1, kpi2, kpi3 = st.columns(3)

    # KPI 1: Total Production (Using a slight animation with `st.metric`)
    with kpi1:
        st.metric(
            label="Total Actual Production", 
            value=f"{total_actual:,}", 
            delta=f"{total_actual - total_target:,} vs. Target", 
            delta_color="normal"
        )

    # KPI 2: Overall Achievement Rate
    with kpi2:
        achievement_rate = (total_actual / total_target) * 100
        st.metric(
            label="Overall Achievement Rate",
            value=f"{achievement_rate:.1f}%",
            delta_color="inverse" # Highlight red if below 100%
        )

    # KPI 3: Total Rework
    with kpi3:
        st.metric(
            label="Total Rework Count",
            value=f"{total_rework:,}",
            delta=f"Total downtime: {downtime_df['downtime'].sum():.1f} hrs"
        )

    st.markdown("---") # Separator

    # 3. Data Visualizations
    col_chart, col_pie = st.columns([2, 1])
    
    with col_chart:
        show_production_vs_target(production_df)
        
    with col_pie:
        show_rework_distribution(production_df)

    st.markdown("---") # Separator
    
    show_downtime_breakdown(downtime_df)

# --- 6. EXECUTION FLOW ---

# Initialize session state for authentication if it doesn't exist
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if st.session_state['authenticated']:
    main_app()
else:
    st.title("Welcome to the Weekly Production Report System")
    st.info("Please log in on the sidebar to view your company's data.")
    authenticate_user()