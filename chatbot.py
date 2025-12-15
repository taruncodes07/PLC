# chatbot.py

import streamlit as st
import pandas as pd
from auth import check_role
from google import genai
from google.genai.errors import APIError
import io

# --- 1. Model Initialization ---

# Use a more powerful model for deep, complex database analysis
AI_MODEL = 'gemini-2.5-flash' 

def init_ai_client():
    """Initializes the Gemini client, retrieving API key from Streamlit secrets."""
    try:
        # Streamlit Cloud/secrets integration
        api_key = st.secrets["gemini"]["api_key"]
        if not api_key:
             st.error("Gemini API Key not found. Please set it in .streamlit/secrets.toml.")
             return None
        
        # Use an external environment variable or secure method for production deployment
        client = genai.Client(api_key=api_key)
        return client
    except KeyError:
        st.error("Gemini API Key not found. Please set it in .streamlit/secrets.toml.")
        return None
    except Exception as e:
        st.error(f"Error initializing Gemini client: {e}")
        return None

# --- 2. Data Condensation Function (NEW) ---

def condense_dataframe_for_ai(df):
    """
    Analyzes the entire DataFrame and generates a comprehensive text summary
    for the AI model's context. This is crucial for analyzing large datasets.
    """
    summary = ["--- FULL DATASET SUMMARY ---"]
    
    # 1. Overall KPIs
    total_production = df['Actual_Production_Units'].sum()
    total_downtime = df['Downtime_Minutes'].sum()
    total_waste = df['Waste_Weight_kg'].sum()
    
    summary.append(f"Total Production (Units): {total_production:,.0f}")
    summary.append(f"Total Downtime (Minutes): {total_downtime:,.0f}")
    summary.append(f"Total Waste (kg): {total_waste:,.1f}")
    
    # Calculate Efficiency (requires Planned Units, assume column exists)
    if 'Planned_Production_Units' in df.columns and df['Planned_Production_Units'].sum() > 0:
         efficiency = df['Actual_Production_Units'].sum() / df['Planned_Production_Units'].sum()
         summary.append(f"Overall Efficiency: {efficiency:.2%}")
    
    summary.append("\n2. Production by Product (Top 5):")
    prod_by_product = df.groupby('Product_Name')['Actual_Production_Units'].sum().nlargest(5).to_markdown()
    summary.append(prod_by_product)
    
    summary.append("\n3. Downtime Breakdown by Reason:")
    downtime_by_reason = df.groupby('Downtime_Reason')['Downtime_Minutes'].sum().nlargest(5).to_markdown()
    summary.append(downtime_by_reason)
    
    summary.append("\n4. Waste Analysis by Shift:")
    waste_by_shift = df.groupby('Shift')['Waste_Weight_kg'].sum().to_markdown()
    summary.append(waste_by_shift)
    
    # 5. Date Range
    start_date = df['Date'].min().strftime('%Y-%m-%d')
    end_date = df['Date'].max().strftime('%Y-%m-%d')
    summary.append(f"\nData Period: {start_date} to {end_date} ({len(df)} total records).")
    
    return "\n".join(summary)


# --- 3. Chatbot Page Function ---

def chatbot_page():
    """Streamlit page for the AI Production Analyst Chatbot."""
    st.title("🤖 AI Production Analyst Chatbot")
    st.markdown("---")

    if not check_role('Analyst'):
        st.error("Access Denied: You must be an Analyst or Admin to use the AI Chatbot.")
        return

    # Check for dataset presence
    if 'df' not in st.session_state or st.session_state['df'].empty:
        st.warning("No dataset loaded. Please load production data on the 'Load & Manage Dataset' page first.")
        return

    client = init_ai_client()
    if not client:
        return

    st.info(f"Using **{AI_MODEL}** to analyze the complete loaded dataset ({len(st.session_state['df'])} records). Ask for summaries, suggestions, or trend analysis.")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state["messages"] = [{"role": "model", "content": "Hello! I am your AI Production Analyst. I have loaded the full dataset summary and am ready for your questions."}]

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Accept user input
    if prompt := st.chat_input("Enter your question about the data..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message immediately
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate condensed data summary from the ENTIRE dataframe
        data_summary_context = condense_dataframe_for_ai(st.session_state['df'])
        
        # System instruction to define the AI's role and context
        system_instruction = (
            "You are an expert Senior Production Data Analyst. Your task is to analyze the provided "
            "comprehensive summary of the manufacturing data. Do not mention the raw tables. "
            "Analyze the overall KPIs, product breakdowns, downtime analysis, and waste figures to "
            "answer the user's question. Provide actionable, high-level manufacturing suggestions "
            "based on the worst performing areas (e.g., highest downtime reason or highest waste shift). "
            "The data is a summary of all loaded records, not just a sample."
        )

        # Construct the final prompt with the data context
        full_prompt = (
            f"{system_instruction}\n\n"
            f"--- FULL DATASET SUMMARY FOR ANALYSIS:\n{data_summary_context}\n\n"
            f"--- USER QUESTION: {prompt}"
        )
        
        # Generate model response
        with st.chat_message("model"):
            with st.spinner(f"Sending full summary to {AI_MODEL} for deep analysis..."):
                try:
                    response = client.models.generate_content(
                        model=AI_MODEL,
                        contents=full_prompt,
                        # Setting temperature to 0 for factual, analytical responses
                        config={'temperature': 0.0}
                    )
                    
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "model", "content": response.text})
                
                except APIError as e:
                    error_message = f"AI API Error: Could not process request. Details: {e}. Please verify your API Key and Model access."
                    st.error(error_message)
                    st.session_state.messages.append({"role": "model", "content": error_message})
                except Exception as e:
                    error_message = f"An unexpected error occurred: {e}"
                    st.error(error_message)
                    st.session_state.messages.append({"role": "model", "content": error_message})