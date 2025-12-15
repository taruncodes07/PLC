# chatbot.py

import streamlit as st
import pandas as pd
from auth import check_role
from google import genai
from google.genai.errors import APIError
import io

# --- 1. Model Initialization ---

# Using gemini-2.5-flash for better availability and cost-efficiency
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

# --- 2. Data Condensation Function (UNCHANGED) ---

def condense_dataframe_for_ai(df):
    """
    Analyzes the entire DataFrame and generates a comprehensive text summary
    for the AI model's context.
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

    st.info(f"Using **{AI_MODEL}**. Ask for summaries, suggestions, or feel free to chat casually!")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state["messages"] = [{"role": "model", "content": "Hello! I am your AI Production Analyst. I have the data summary ready. How can I help you?"}]

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Accept user input
    if prompt := st.chat_input("Enter your question..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message immediately
        with st.chat_message("user"):
            st.markdown(prompt)

        # --- NEW LOGIC: DETERMINE IF DATA CONTEXT IS NEEDED ---
        
        # Keywords suggesting a data query
        data_keywords = ['summary', 'kpi', 'waste', 'downtime', 'product', 'efficiency', 'suggest', 'data']
        
        is_data_query = any(word in prompt.lower() for word in data_keywords)

        if is_data_query:
            # Load full context for analytical questions
            data_summary_context = condense_dataframe_for_ai(st.session_state['df'])
            
            system_instruction = (
                "You are an expert Senior Production Data Analyst. Your primary task is to use the provided "
                "comprehensive manufacturing data summary to answer the user's analytical question. "
                "Analyze the KPIs, breakdowns, and suggest actionable improvements. "
                "The data is a summary of all loaded records."
            )
            full_prompt = (
                f"{system_instruction}\n\n"
                f"--- FULL DATASET SUMMARY FOR ANALYSIS:\n{data_summary_context}\n\n"
                f"--- USER QUESTION: {prompt}"
            )
        else:
            # Simple conversational prompt (no data context needed)
            full_prompt = prompt
            system_instruction = "You are a friendly, conversational AI assistant. Do not mention manufacturing or production data unless the user asks specifically about it."

        # --- Generate model response ---
        
        with st.chat_message("model"):
            with st.spinner(f"Processing {'data analysis' if is_data_query else 'response'}..."):
                try:
                    response = client.models.generate_content(
                        model=AI_MODEL,
                        contents=full_prompt,
                        config={'temperature': 0.7 if not is_data_query else 0.0}
                    )
                    
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "model", "content": response.text})
                
                except APIError as e:
                    error_message = f"AI API Error: Could not process request. Details: {e}. Please try again."
                    st.error(error_message)
                    st.session_state.messages.append({"role": "model", "content": error_message})
                except Exception as e:
                    error_message = f"An unexpected error occurred: {e}"
                    st.error(error_message)
                    st.session_state.messages.append({"role": "model", "content": error_message})
                    