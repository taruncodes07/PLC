# audit_logger.py

import pandas as pd
from datetime import datetime
import streamlit as st
import os

AUDIT_LOG_FILE = 'audit_logs.csv'
# Define the exact column names expected for the audit log file
AUDIT_COLS = ['user', 'timestamp', 'row_id', 'column_name', 'old_value', 'new_value']

def log_edit(user, row_id, column, old_value, new_value):
    """Logs a single data edit to the audit log CSV."""
    
    # Skip logging if no change occurred
    if str(old_value) == str(new_value):
        return

    new_log = pd.DataFrame([{
        'user': user,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'row_id': row_id,
        'column_name': column,
        'old_value': old_value,
        'new_value': new_value
    }])
    
    try:
        # Determine if the header needs to be written
        write_header = not os.path.exists(AUDIT_LOG_FILE) or os.path.getsize(AUDIT_LOG_FILE) == 0
        
        # Append to CSV. If the file is new/empty, write the header.
        new_log.to_csv(AUDIT_LOG_FILE, mode='a', header=write_header, index=False)
             
    except Exception as e:
        st.error(f"Error writing to audit log: {e}")

@st.cache_data(ttl=60)
def load_audit_logs():
    """Loads the entire audit log file, explicitly setting column names if necessary."""
    try:
        # 1. Check if the file is empty or non-existent
        if not os.path.exists(AUDIT_LOG_FILE) or os.path.getsize(AUDIT_LOG_FILE) == 0:
            return pd.DataFrame(columns=AUDIT_COLS)

        # 2. Read the CSV using the defined column names
        # Use header=0 to read the existing header, ensuring columns match AUDIT_COLS
        df_log = pd.read_csv(AUDIT_LOG_FILE, header=0)
        
        if not df_log.empty:
            # 3. Perform conversion and sorting only if the DataFrame has rows
            df_log['timestamp'] = pd.to_datetime(df_log['timestamp'])
            df_log = df_log.sort_values('timestamp', ascending=False)
            
        return df_log
        
    except FileNotFoundError:
        # Should not happen if the log_edit function is working, but included for robustness
        st.warning(f"Audit log file not found. Creating a new one at {AUDIT_LOG_FILE}.")
        df_empty = pd.DataFrame(columns=AUDIT_COLS)
        df_empty.to_csv(AUDIT_LOG_FILE, index=False)
        return df_empty
    except Exception as e:
        # Catch any unexpected reading errors (e.g., corrupted file)
        st.error(f"Error loading audit logs: {e}")
        return pd.DataFrame(columns=AUDIT_COLS)

def audit_log_page():
    """Streamlit page to display the audit history."""
    st.title("🛡️ Audit Logs History")
    st.markdown("---")
    
    # Force cache refresh for the latest log data
    df_log = load_audit_logs.clear() # Clear cache
    df_log = load_audit_logs()       # Load fresh data
    
    if df_log.empty:
        st.info("No audit logs found yet.")
    else:
        st.info(f"Displaying {len(df_log)} audit entries.")
        st.dataframe(df_log, width='stretch')