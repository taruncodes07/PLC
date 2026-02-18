# reports.py

import streamlit as st
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION_START
from docx.shared import RGBColor
import pandas as pd
from fpdf import FPDF
import plotly.express as px
# NOTE: The dashboard module needs to be imported here to use its functions
from dashboard import calculate_kpis, generate_insights, create_filters 
from auth import check_role
import io
from datetime import datetime

# --- PDF Generation (using FPDF) ---

class PDF(FPDF):
    """Custom PDF class for report generation."""
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.set_fill_color(30, 30, 30) # Dark background feel
        self.set_text_color(255, 255, 255)
        self.rect(0, 0, self.w, 15, 'F')
        self.cell(0, 10, 'Production Report', 0, 1, 'C')
        self.set_text_color(150, 150, 150)
        self.set_font('Arial', '', 10)
        self.cell(0, 5, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 0, 1, 'C')
        self.ln(5)
        self.set_text_color(0, 0, 0) # Reset to black for content

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_pdf_report(df_filtered, kpis, insights):
    """Generates the PDF report content."""
    
    pdf = PDF()
    pdf.add_page()
    
    # Title Page/Summary
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'I. Executive Summary', 0, 1, 'L')
    pdf.set_font('Arial', '', 10)
    
    # Insights (Replacing formatting for text-only PDF)
    insight_text = insights.replace(" | ", "\n- ").replace("**", "")
    pdf.multi_cell(0, 5, insight_text + "\n\n", 0, 'L')

    # KPIs
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'II. Key Performance Indicators', 0, 1, 'L')
    pdf.set_font('Arial', '', 10)
    
    col_width = pdf.w / 3.5
    for i, (k, v) in enumerate(kpis.items()):
        if i % 2 == 0:
            pdf.ln(5)
            
        pdf.cell(col_width, 6, f"{k}:", 0, 0, 'L')
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(col_width, 6, v, 0, 0, 'L')
        pdf.set_font('Arial', '', 10)

    # Tables - Top 5 Downtime Reasons
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'III. Top 5 Downtime Reasons', 0, 1, 'L')
    
    df_top_dt = df_filtered.groupby('Downtime_Reason')['Downtime_Minutes'].sum().sort_values(ascending=False).head(5).reset_index()
    
    # Table headers
    pdf.set_fill_color(220, 220, 220)
    pdf.set_font('Arial', 'B', 10)
    col_widths = [pdf.w * 0.4, pdf.w * 0.3]
    pdf.cell(col_widths[0], 7, 'Downtime Reason', 1, 0, 'C', 1)
    pdf.cell(col_widths[1], 7, 'Total Minutes', 1, 1, 'C', 1)
    
    # Table rows
    pdf.set_font('Arial', '', 10)
    for index, row in df_top_dt.iterrows():
        pdf.cell(col_widths[0], 6, row['Downtime_Reason'], 1, 0, 'L')
        pdf.cell(col_widths[1], 6, f"{row['Downtime_Minutes']:,.0f}", 1, 1, 'R')

    pdf_output = pdf.output()
    if isinstance(pdf_output, (bytes, bytearray)):
        return bytes(pdf_output)
    return pdf_output.encode('latin-1')

# --- DOCX Generation (using python-docx) ---

def generate_docx_report(df_filtered, kpis, insights):
    """Generates the DOCX report content."""
    
    document = Document()
    
    # Set Default Font/Size
    style = document.styles['Normal']
    font = style.font
    font.name = 'Arial'
    font.size = Pt(11)
    
    # Title Page
    document.add_heading('Weekly Production Report', 0)
    document.add_paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    document.add_paragraph(f"Data Period: {df_filtered['Date'].min().strftime('%Y-%m-%d')} to {df_filtered['Date'].max().strftime('%Y-%m-%d')}")
    
    # I. Executive Summary
    document.add_section(WD_SECTION_START.NEW_PAGE)
    document.add_heading('I. Executive Summary', level=1)
    
    # Add Insights as a bulleted list
    p = document.add_paragraph()
    for insight in insights.replace("**", "").split(" | "):
        p.add_run(f'• {insight.strip()}').bold = True
        p = document.add_paragraph()
    
    # II. KPIs
    document.add_heading('II. Key Performance Indicators', level=1)
    table = document.add_table(rows=len(kpis.items()) // 2 + 1, cols=4)
    table.style = 'Medium Shading 1 Accent 1'
    
    # Add KPI data to the table
    kpi_list = list(kpis.items())
    for i in range(len(kpi_list) // 2):
        row = table.rows[i].cells
        
        # KPI 1
        row[0].text = kpi_list[i*2][0]
        row[1].text = kpi_list[i*2][1]
        
        # KPI 2
        row[2].text = kpi_list[i*2 + 1][0]
        row[3].text = kpi_list[i*2 + 1][1]

    # Handle odd number of KPIs
    if len(kpi_list) % 2 != 0:
        row = table.rows[-1].cells
        row[0].text = kpi_list[-1][0]
        row[1].text = kpi_list[-1][1]
        row[2].text = ''
        row[3].text = ''

    # III. Downtime Analysis Table
    document.add_heading('III. Top Downtime Reasons', level=1)
    df_downtime = df_filtered.groupby('Downtime_Reason')['Downtime_Minutes'].sum().sort_values(ascending=False).head(5).reset_index()
    
    table_dt = document.add_table(df_downtime.shape[0] + 1, df_downtime.shape[1])
    table_dt.style = 'Light Grid'
    
    # Add header row
    for j, col in enumerate(df_downtime.columns):
        table_dt.cell(0, j).text = col.replace('_', ' ').title()
    
    # Add data rows
    for i, row in df_downtime.iterrows():
        for j, col in enumerate(df_downtime.columns):
            table_dt.cell(i+1, j).text = f"{row[col]:,.0f}" if 'Minutes' in col else str(row[col])

    # Save to a BytesIO object
    buffer = io.BytesIO()
    document.save(buffer)
    buffer.seek(0)
    return buffer.read()


def reports_page():
    """Streamlit page for generating and exporting reports."""
    st.title("📄 Export Reports (PDF / Word)")
    st.markdown("---")
    
    if not check_role('Analyst'):
        st.error("Access Denied: You must be an Analyst or Admin to generate reports.")
        return

    if 'df' not in st.session_state or st.session_state['df'].empty:
        st.warning("No dataset loaded. Please load data first.")
        return
        
    st.info("The reports will be generated based on the current filters applied in the Dashboard.")
    
    # Get filtered data, KPIs, and Insights
    # NOTE: Need to suppress filter creation in reports page
    df_filtered = create_filters(st.session_state['df'].copy()) 

    kpis = calculate_kpis(df_filtered)
    insights = generate_insights(df_filtered)

    file_name = st.text_input("Report File Name (e.g., Weekly_Report_2025-12)", "Weekly_Report")
    export_type = st.selectbox("Select Export Type", ["PDF", "Word (.docx)"])
    
    if st.button("Generate & Download Report", type="primary"):
        if not file_name:
            st.error("Please enter a file name.")
            return

        if export_type == "PDF":
            with st.spinner("Generating PDF Report..."):
                pdf_bytes = generate_pdf_report(df_filtered, kpis, insights)
                st.download_button(
                    label="Download PDF",
                    data=pdf_bytes,
                    file_name=f"{file_name}.pdf",
                    mime="application/pdf"
                )
                st.success("PDF generated successfully.")

        elif export_type == "Word (.docx)":
            with st.spinner("Generating Word Report..."):
                docx_bytes = generate_docx_report(df_filtered, kpis, insights)
                st.download_button(
                    label="Download DOCX",
                    data=docx_bytes,
                    file_name=f"{file_name}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
                st.success("Word report generated successfully.")