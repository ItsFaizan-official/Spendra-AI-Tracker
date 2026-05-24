# AI Expense Tracker

A professional Python expense tracker with AI-assisted expense parsing, monthly reports, CSV export, and user profiles. Now featuring a beautiful Streamlit web interface!

## Features

- 🤖 **AI Parsing**: Natural-language expense descriptions using Groq
- 💻 **Web Interface**: Professional Streamlit UI with real-time updates
- 📊 **Data Visualization**: Beautiful charts and analytics (Plotly)
- 👥 **Multi-User Support**: Separate profiles for each user
- 📈 **Monthly Reports**: Detailed breakdowns and insights
- 📥 **CSV Export**: Export data for external analysis
- 💾 **JSON Storage**: Lightweight, file-based database
- 🔒 **Secure**: Environment variables for API key handling

## Setup

### 1. Create a Python environment

```bash
python -m venv .venv
.venv\Scripts\activate  # On Windows
# source .venv/bin/activate  # On macOS/Linux
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Groq API key

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_api_key_here
GROQ_MODEL_NAME=llama3-8b-8192
```

Or export the environment variables in your shell.

## Usage

### Streamlit Web App (Recommended)

```bash
streamlit run app.py
```

This opens the app in your browser at `http://localhost:8501` with:
- **Dashboard**: Overview with charts and metrics
- **Add Expense**: AI-powered or manual expense entry
- **Summary**: Detailed expense breakdown by category
- **Reports**: Monthly analytics and CSV export
- **Settings**: API configuration and data management

### Command-line Interface (Legacy)

```bash
python expense_tracker.py
```

Then follow the prompts with commands: `add`, `summary`, `report`, `export`, `months`, `switch`, and `exit`.

## Project Structure

- `app.py` — Streamlit web application
- `backend.py` — Core business logic and database operations
- `expense_tracker.py` — Legacy command-line interface
- `expenses_db.json` — JSON database (auto-created)
- `.env` — API configuration (create this file)

## File Formats

- **expenses_db.json**: User data storage with structure:
  ```json
  {
    "username": {
      "YYYY-MM": {
        "Food": [...],
        "Bills": [...],
        "Fun": [...],
        "Transit": [...],
        "Other": [...]
      }
    }
  }
  ```

- **CSV Export**: Named `export_<username>_<month>.csv` with columns:
  - timestamp
  - item
  - category
  - price
  - note

## Technology Stack

- **Frontend**: Streamlit
- **Visualization**: Plotly
- **AI**: Groq (LLM)
- **Backend**: Python
- **Storage**: JSON

## Requirements

See [requirements.txt](requirements.txt) for dependencies. Key packages:
- `groq` — LLM API client
- `python-dotenv` — Environment variable management
- `streamlit` — Web framework
- `plotly` — Data visualization

## Notes

- The database is saved in `expenses_db.json` (auto-created)
- If the AI fails to parse an entry, manual input is available
- All timestamps are in ISO format with seconds precision
- Data is persisted after every operation
