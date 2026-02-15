# Chips Factory Production Report Generator

A Streamlit app for loading, analyzing, editing, and reporting on production data for a potato chips factory. It includes role-based access control, an audit log, exports, and an AI chatbot for data summaries.

## Project Structure

- [app.py](app.py) - App entry point and page routing.
- [auth.py](auth.py) - Authentication, session handling, and role checks.
- [data_loader.py](data_loader.py) - CSV loading and dataset management.
- [dashboard.py](dashboard.py) - KPI calculations, filters, and charts.
- [editor.py](editor.py) - Admin data editor with audit logging.
- [audit_logger.py](audit_logger.py) - Audit log persistence and viewer page.
- [reports.py](reports.py) - PDF and Word report generation.
- [export_utils.py](export_utils.py) - CSV export page.
- [chatbot.py](chatbot.py) - AI chatbot page using Gemini.
- [requirements.txt](requirements.txt) - Python dependencies.
- [users.json](users.json) - User accounts and roles.
- [audit_logs.csv](audit_logs.csv) - Edit audit trail (generated at runtime).
- [potato_chips_factory_30days_400rows.csv](potato_chips_factory_30days_400rows.csv) - Sample dataset.

## Modules, Libraries, and Functions

### app

- **Purpose**: Sets Streamlit config, initializes session state, and routes between pages based on user role.
- **Libraries used**:
  - `streamlit` - UI rendering and session state.
  - App modules: `auth`, `data_loader`, `dashboard`, `editor`, `audit_logger`, `reports`, `export_utils`, `chatbot`.
- **User-defined functions**: None in this module. Uses page functions imported from other modules.

### auth

- **Purpose**: User authentication, password hashing, and role authorization.
- **Libraries used**:
  - `streamlit` - UI and session state.
  - `json` - Read/write user data.
  - `hashlib` - SHA-256 password hashing.
- **User-defined functions**:
  - `load_users()` - Reads user records from `users.json`.
  - `save_users(users_data)` - Writes updated user records to `users.json`.
  - `hash_password(password)` - Hashes a plaintext password with SHA-256.
  - `authenticate()` - Renders login UI, verifies credentials, and sets session state.
  - `logout()` - Clears session state and returns user to login.
  - `check_role(required_role)` - Enforces role-based access for pages.

### data_loader

- **Purpose**: Load production CSVs and manage the active dataset.
- **Libraries used**:
  - `streamlit` - UI and session state.
  - `pandas` - CSV reading and preprocessing.
  - `json` - User metadata updates via `auth` helpers.
- **User-defined functions**:
  - `save_last_dataset(username, file_name)` - Stores last used dataset in user profile.
  - `load_data(file_path)` - Reads CSV, parses dates, and adds `Row_ID`.
  - `data_loader_page()` - UI for loading last, default, or uploaded datasets.

### dashboard

- **Purpose**: KPI calculations, filters, insight text, and interactive charts.
- **Libraries used**:
  - `streamlit` - UI rendering.
  - `pandas` - Data manipulation.
  - `plotly.express` - Charting.
  - `numpy` - Numeric support.
  - `datetime` - Date math for default ranges.
  - `auth.check_role` - Role enforcement.
- **User-defined functions**:
  - `calculate_kpis(df)` - Computes production KPIs used in dashboard and reports.
  - `custom_metric_card(container, label, value, full_value)` - Renders styled KPI cards.
  - `create_filters(df)` - Builds sidebar filters and returns filtered data.
  - `generate_insights(df)` - Produces narrative insights from filtered data.
  - `dashboard_page()` - Main dashboard UI and charts.

### editor

- **Purpose**: Admin-only data editing with audit logging.
- **Libraries used**:
  - `streamlit` - UI rendering.
  - `pandas` - Data handling.
  - `audit_logger.log_edit` - Audit trail for changes.
  - `auth.check_role` - Role enforcement.
- **User-defined functions**:
  - `editor_page()` - UI for editing the dataset and logging changes.

### audit_logger

- **Purpose**: Append edits to an audit CSV and display audit history.
- **Libraries used**:
  - `pandas` - CSV read/write.
  - `datetime` - Timestamping edits.
  - `streamlit` - UI and cache.
  - `os` - File existence/size checks.
- **User-defined functions**:
  - `log_edit(user, row_id, column, old_value, new_value)` - Appends a change record to audit logs.
  - `load_audit_logs()` - Reads and sorts audit log entries.
  - `audit_log_page()` - UI for viewing audit history.

### export_utils

- **Purpose**: Export the current dataset as a CSV download.
- **Libraries used**:
  - `streamlit` - UI rendering and download button.
  - `pandas` - Data handling.
  - `auth.check_role` - Role enforcement.
- **User-defined functions**:
  - `export_page()` - UI to export the loaded dataset as CSV.

### reports

- **Purpose**: Generate PDF and Word reports from filtered data.
- **Libraries used**:
  - `streamlit` - UI rendering.
  - `python-docx` - Word report creation.
  - `fpdf` - PDF report creation.
  - `pandas` - Data manipulation.
  - `plotly.express` - Imported but not used in current report generation.
  - `datetime` - Report timestamps.
  - `dashboard` helpers - `calculate_kpis`, `generate_insights`, `create_filters`.
  - `auth.check_role` - Role enforcement.
  - `io` - In-memory buffers for DOCX.
- **User-defined functions and classes**:
  - `PDF(FPDF)` - Custom PDF header/footer for reports.
  - `generate_pdf_report(df_filtered, kpis, insights)` - Builds PDF bytes.
  - `generate_docx_report(df_filtered, kpis, insights)` - Builds DOCX bytes.
  - `reports_page()` - UI for generating and downloading reports.

### chatbot

- **Purpose**: AI assistant that uploads the dataset to Gemini once, reuses that file across prompts, and supports follow-up questions using recent conversation context.
- **Libraries used**:
  - `streamlit` - UI rendering and chat interface.
  - `google.genai` - Gemini client and file upload.
  - `google.genai.errors` - API error handling.
  - `os` - File checks and metadata.
  - `auth.check_role`, `auth.load_users` - Role enforcement and last dataset lookup.
- **User-defined functions**:
  - `init_ai_client()` - Reads API key from secrets and creates the Gemini client.
  - `get_last_dataset_path()` - Finds the last-used dataset file for the logged-in user.
  - `read_dataset_text(file_path)` - Size-checks and reads dataset content (guardrail).
  - `ensure_dataset_file(client, file_path)` - Uploads dataset to Gemini once and reuses the cached file reference.
  - `build_conversation_context(messages, max_messages)` - Builds a short transcript from recent messages for follow-up context.
  - `chatbot_page()` - Chat UI, prompt handling, file attachment, and model invocation.

## Dependencies

See [requirements.txt](requirements.txt) for the full list. Core dependencies include:

- `streamlit`
- `pandas`
- `numpy`
- `plotly`
- `python-docx`
- `fpdf2`
- `google.genai`
- `tabulate`

## Notes

- The app expects a Streamlit secrets entry for the Gemini API key at `gemini.api_key`.
- The chatbot uploads the dataset once per session and reuses it for follow-up questions.
- `audit_logs.csv` is created automatically when edits occur.
- Role-based access controls hide or block certain pages.
