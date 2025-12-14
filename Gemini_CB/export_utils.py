# export_utils.py

import streamlit as st
import pandas as pd
from auth import check_role

def export_page():
    """Streamlit page for exporting the current dataset."""
    st.title("📤 Export Current Database")
    st.markdown("---")
    
    if not check_role('Analyst'):
        st.error("Access Denied: You must be an Analyst or Admin to export data.")
        return

    if 'df' not in st.session_state or st.session_state['df'].empty:
        st.warning("No dataset loaded to export.")
        return
        
    df_export = st.session_state['df'].copy()
    
    # Remove internal Row_ID column before export
    if 'Row_ID' in df_export.columns:
        df_export = df_export.drop(columns=['Row_ID'])

    st.info("Exporting the **currently loaded and potentially edited** dataset as CSV.")
    
    file_name = st.text_input("Output File Name", "production_data_updated")
    
    if st.button("Download CSV", type="primary"):
        if not file_name:
            st.error("Please enter a file name.")
            return
            
        csv_data = df_export.to_csv(index=False).encode('utf-8')
        
        st.download_button(
            label="Click to Download",
            data=csv_data,
            file_name=f'{file_name}.csv',
            mime='text/csv',
        )
        st.success("CSV file ready for download.")