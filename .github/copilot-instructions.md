# Copilot Instructions for GDP Dashboard

## Project Overview
This is a **Streamlit-based data visualization dashboard** for displaying GDP data. It's a single-page application that loads and displays datasets from Excel files in a web interface.

**Technology Stack:**
- Framework: Streamlit (Python web framework for data apps)
- Data Processing: Pandas
- Data Format: Excel files (.xlsx) and CSV files (.csv)

## Architecture & Data Flow

### Core Application Structure
- **`streamlit_app.py`** - Single main application file that:
  - Configures page metadata (title, favicon) using `st.set_page_config()`
  - Loads Excel files via `pd.read_excel()` with error handling
  - Displays the dataframe using `st.dataframe()` for interactive viewing
  - Uses `@st.cache_data` decorator for performance optimization

### Data Sources
- **Primary:** `contri.xlsx` (loaded at runtime, must be in project root)
- **Alternative:** CSV files in `data/` directory (gdp_data.csv, Renegades_Contri.xlsx)
- Note: Current app references `contri.xlsx` - ensure this file exists in the root directory when running

## Developer Workflows

### Running the Application
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```
Streamlit auto-reloads on file changes; accessible at `http://localhost:8501`

### Adding New Data Sources
1. Place Excel or CSV files in project root (for `contri.xlsx` pattern) or `data/` directory
2. Modify `file_path` variable or create new loader functions
3. Use `@st.cache_data` decorator to optimize data loading performance

### Handling Data Errors
The app implements error handling for missing/corrupted files:
- `FileNotFoundError` → User-friendly error message
- Generic exceptions → Caught and displayed via `st.error()`

## Key Patterns & Conventions

### Performance Optimization
```python
@st.cache_data
def load_data(path):
    # Cache prevents re-running on every page refresh
```
Use this for expensive operations (file I/O, API calls, computations).

### UI Components
- `st.set_page_config()` - Set page title and favicon (emoji or URL)
- `st.write()` - Display text
- `st.dataframe()` - Interactive table display (sortable, searchable)
- `st.error()` - Display error messages to users

### Error Handling Pattern
Always wrap file operations in try/except blocks and provide user-facing error messages via `st.error()` rather than raising exceptions.

## Integration Points & External Dependencies

### Dependencies (from `requirements.txt`)
- **streamlit** - Web framework (specific version not pinned; uses latest)
- **pandas** - Data manipulation and Excel reading (`pd.read_excel()`)

### File I/O
- Expects Excel files in project root by default
- Uses `pathlib.Path` for path handling (though not currently utilized in main logic)

## Common Tasks for AI Agents

### Extending the Dashboard
- Add new data visualizations: Use `st.chart_data()`, `st.bar_chart()`, `st.line_chart()`
- Filter data: Use Streamlit widgets (`st.selectbox()`, `st.slider()`) and pandas filtering
- Multi-page apps: Create additional .py files in a `pages/` directory with Streamlit's multi-page feature

### Debugging Tips
- Check that `contri.xlsx` exists in the project root before running
- Use `streamlit run --logger.level=debug` for verbose logging
- Verify Excel file format is compatible with pandas (`.xlsx` not `.xls`)

### Adding Features
1. **Interactive filters** - Use `st.sidebar` for filter controls
2. **Multiple sheets** - `pd.read_excel(path, sheet_name='SheetName')`
3. **Data export** - Use `st.download_button()` for CSV/Excel downloads
