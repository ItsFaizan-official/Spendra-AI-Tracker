
<div align="center">

# 💠 Spendra Enterprise

[![Typing SVG](https://readme-typing-svg.demolab.com?font=Inter&weight=700&size=24&pause=1000&color=C084FC&center=true&vCenter=true&width=500&lines=AI-Powered+Expense+Tracking;Real-Time+Financial+Telemetry;Secure+Data+Infrastructure)](https://git.io/typing-svg)

An enterprise-grade Python expense tracker featuring neural-network parsing, real-time visualization matrices, and secure data infrastructure built on Streamlit.

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-239120?style=for-the-badge&logo=plotly&logoColor=white)
![JSON](https://img.shields.io/badge/JSON-000000?style=for-the-badge&logo=json&logoColor=white)

</div>

---

## ✨ Core Features

* 🤖 **Neural Expense Parsing**: Natural-language processing instantly categorizes and logs unstructured expense data using the Groq API.
* 💻 **Dynamic Web Interface**: Professional Streamlit UI with real-time updates and interactive SaaS layouts.
* 📊 **Live Telemetry**: Interactive Plotly infrastructure mapping your fiscal trajectory instantly.
* 👥 **Multi-User Architecture**: Secure, separate profiles for each departmental user.
* 📥 **Secure Data Egress**: Generate compliant CSV payloads for external auditing software.
* 💾 **Lightweight Storage**: Encrypted, file-based JSON database infrastructure.

---

## 🚀 Quick Start Guide

### 1. Initialize Environment
```bash
# Create a virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate  

# Activate (macOS/Linux)
source .venv/bin/activate 

```

### 2. Install Dependencies

```bash
pip install -r requirements.txt

```

### 3. Configure Neural Engine

Create a `.env` file in the project root to authenticate your API:

```env
GROQ_API_KEY=your_api_key_here
GROQ_MODEL_NAME=llama3-8b-8192

```

### 4. Launch Application

```bash
streamlit run app.py

```

*The infrastructure will deploy locally at `http://localhost:8501`.*

---

## 📂 System Architecture

* `app.py` — Streamlit web application & UI layer
* `backend.py` — Core business logic and database operations
* `expense_tracker.py` — Legacy command-line interface
* `expenses_db.json` — Persistent JSON volume (auto-generated)
* `.env` — API configuration and environment variables

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

**CSV Export Structure:**
Artifacts are named `export_<username>_<month>.csv` containing:
`timestamp` | `item` | `category` | `price` | `note`

---

## 🖥️ Legacy CLI Interface

If you need to bypass the UI and access the raw terminal infrastructure:

```bash
python expense_tracker.py

```

*Available terminal commands: `add`, `summary`, `report`, `export`, `months`, `switch`, and `exit`.*

---

## 👤 Lead Architect

**Mohammad Faizan Khan** *Enterprise Systems & AI Engineer | Professional IT Trainer*

---

*Note: The database is persisted automatically after every operation. All temporal data is stamped in ISO format with precise seconds resolution.*

