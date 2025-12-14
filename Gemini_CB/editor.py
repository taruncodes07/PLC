# editor.py

import streamlit as st
import pandas as pd
from audit_logger import log_edit
from auth import check_role

def editor_page():
    """Streamlit page for Admin-level data editing."""
    st.title("✏️ Data Editor (Admin Only)")
    st.markdown("---")
    
    if not check_role('Admin'):
        st.error("Access Denied: You must be an Admin to edit data.")
        return

    if 'df' not in st.session_state or st.session_state['df'].empty:
        st.warning("No dataset loaded. Please load data on the 'Load & Manage Dataset' page.")
        return

    df_original = st.session_state['df'].copy()
    
    st.info("Edit values directly in the table below. Changes are logged and saved only when you click 'Apply Changes'.")
    
    # Only allow editing of production data columns, exclude the Row_ID (index 0)
    editable_cols = df_original.columns.tolist()[1:] 
    
    edited_df = st.data_editor(
        df_original,
        key="data_editor",
        num_rows="dynamic",
        use_container_width=True,
        column_order=df_original.columns.tolist(),
        disabled= ['Row_ID', 'Date', 'Shift', 'Product_ID', 'Supervisor_ID', 'Machine_Operator_ID'] # Disable key identifiers
    )

    if st.button("Apply Changes and Save", type="primary"):
        user = st.session_state['user_info']['username']
        
        # Find differences and log them
        changes_found = False
        for row_index, row in edited_df.iterrows():
            for col in editable_cols:
                old_value = df_original.loc[row_index, col]
                new_value = row[col]
                
                if str(old_value) != str(new_value):
                    log_edit(
                        user=user,
                        row_id=row['Row_ID'], # Use the stable Row_ID for logging
                        column=col,
                        old_value=old_value,
                        new_value=new_value
                    )
                    changes_found = True

        if changes_found:
            st.session_state['df'] = edited_df.copy()
            st.success(f"Changes applied and {user}'s edits have been logged in audit_logs.csv.")
            st.rerun()
        else:
            st.info("No actual changes detected.")