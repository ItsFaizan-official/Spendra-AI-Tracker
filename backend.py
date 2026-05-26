"""Backend logic for expense tracker - JSON storage and AI parsing."""
import csv
import json
import os
import re
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from groq import Groq
except ImportError:
    Groq = None

DB_FILE = "expenses_db.json"
ENV_FILE = ".env"
DEFAULT_MODEL = "llama3-8b-8192"
ALLOWED_CATEGORIES = ["Food", "Bills", "Fun", "Transit", "Other"]
LOGIN_HISTORY_KEY = "_login_history"
USER_PROFILE_KEY = "_profile"
METADATA_KEYS = {LOGIN_HISTORY_KEY}
USER_METADATA_KEYS = {USER_PROFILE_KEY}


def load_dotenv(path: str = ENV_FILE) -> None:
    """Load environment variables from a .env file if present."""
    if not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as env_file:
        for line in env_file:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def get_api_key() -> Optional[str]:
    """Return the Groq API key from environment variables."""
    load_dotenv()
    return os.environ.get("GROQ_API_KEY")


def get_model_name() -> str:
    """Return the model name to use, defaulting to DEFAULT_MODEL."""
    load_dotenv()
    return os.environ.get("GROQ_MODEL_NAME", DEFAULT_MODEL)


def initialize_db_metadata(db: Dict[str, Any]) -> None:
    """Initialize database metadata sections if missing."""
    if LOGIN_HISTORY_KEY not in db:
        db[LOGIN_HISTORY_KEY] = []


def load_database() -> Dict[str, Any]:
    """Load or initialize the JSON database."""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as file:
            try:
                db = json.load(file)
            except json.JSONDecodeError:
                db = {}
    else:
        db = {}

    initialize_db_metadata(db)
    return db


def save_database(data: Dict[str, Any]) -> None:
    """Save the database back to JSON."""
    with open(DB_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, sort_keys=True)


def normalize_username(raw: str) -> str:
    """Normalize username to title case."""
    return raw.strip().title()


def current_month_key() -> str:
    """Get current month in YYYY-MM format."""
    return datetime.now().strftime("%Y-%m")


def ensure_user_profile(db: Dict[str, Any], username: str) -> None:
    """Ensure the user's profile metadata exists."""
    if username not in db:
        db[username] = {}
    if USER_PROFILE_KEY not in db[username]:
        db[username][USER_PROFILE_KEY] = {
            "created_at": datetime.now().isoformat(sep=" ", timespec="seconds"),
            "last_login": datetime.now().isoformat(sep=" ", timespec="seconds"),
            "login_count": 0,
        }


def update_user_profile_login(db: Dict[str, Any], username: str) -> None:
    """Update the user's profile metadata on login."""
    ensure_user_profile(db, username)
    profile = db[username][USER_PROFILE_KEY]
    profile["last_login"] = datetime.now().isoformat(sep=" ", timespec="seconds")
    profile["login_count"] = profile.get("login_count", 0) + 1


def record_login_event(db: Dict[str, Any], username: str, is_new_user: bool) -> None:
    """Record a login event for audit history."""
    initialize_db_metadata(db)
    update_user_profile_login(db, username)
    db[LOGIN_HISTORY_KEY].append({
        "timestamp": datetime.now().isoformat(sep=" ", timespec="seconds"),
        "username": username,
        "is_new_user": bool(is_new_user),
    })


def get_login_history(db: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return the login audit history."""
    return list(db.get(LOGIN_HISTORY_KEY, []))


def get_all_users(db: Dict[str, Any]) -> List[str]:
    """Return all registered usernames, excluding metadata keys."""
    return sorted([key for key in db.keys() if key not in METADATA_KEYS])


def ensure_user_month(db: Dict[str, Any], username: str, month: str) -> None:
    """Ensure user and month structure exist in database."""
    if username not in db:
        db[username] = {}
    if month not in db[username]:
        db[username][month] = {category: [] for category in ALLOWED_CATEGORIES}


def safe_parse_json(text: str) -> Optional[Dict[str, Any]]:
    """Extract and parse JSON from text."""
    if not text:
        return None

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        return None

    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return None


def extract_expense_from_text(text: str) -> Optional[Dict[str, Any]]:
    """Fallback parser for simple expense descriptions."""
    if not text:
        return None

    price_match = re.search(r"\$?\s*(\d+[\.,]?\d{0,2})", text)
    if not price_match:
        return None

    price_text = price_match.group(1).replace(",", ".")
    try:
        price = float(price_text)
    except ValueError:
        return None

    # Guess category from keywords
    lower = text.lower()
    category_keywords = {
        "Food": ["coffee", "lunch", "dinner", "breakfast", "restaurant", "meal", "snack", "burger", "pizza"],
        "Bills": ["rent", "electricity", "water", "internet", "subscription", "phone", "bill", "insurance"],
        "Fun": ["movie", "game", "concert", "party", "drink", "shopping", "spa", "travel"],
        "Transit": ["uber", "taxi", "bus", "train", "metro", "gas", "fuel", "ride", "flight"],
    }

    category = "Other"
    for cat, keywords in category_keywords.items():
        if any(word in lower for word in keywords):
            category = cat
            break

    # Build item name by removing the price token
    item = re.sub(r"\$?\s*%s" % re.escape(price_match.group(0)), "", text, flags=re.IGNORECASE).strip()
    item = re.sub(r"for|at|on|to|from|spent|paid", "", item, flags=re.IGNORECASE).strip(" -_,.")
    if not item:
        item = "Expense"

    return {
        "item": item,
        "price": price,
        "category": category,
        "note": "",
    }


def validate_expense_data(data: Any) -> Optional[Dict[str, Any]]:
    """Validate and clean expense data."""
    if not isinstance(data, dict):
        return None

    item = data.get("item")
    price = data.get("price")
    category = data.get("category")
    note = data.get("note") if isinstance(data.get("note"), str) else ""

    if not item or not isinstance(item, str):
        return None

    try:
        price = float(price)
    except (TypeError, ValueError):
        return None

    category = category.strip().title() if isinstance(category, str) else "Other"
    if category not in ALLOWED_CATEGORIES:
        category = "Other"

    return {"item": item.strip(), "price": price, "category": category, "note": note.strip()}


def analyze_expense_with_ai(user_input: str) -> Optional[Dict[str, Any]]:
    """Parse expense description using Groq AI, with a local fallback."""
    api_key = get_api_key()
    if api_key and Groq is not None:
        prompt = (
            "You are a financial assistant. Extract the item name, price (as a float), "
            "category, and note (optional) from this expense description. Allowed categories: Food, Bills, Fun, Transit, Other. "
            "Return ONLY a valid JSON object with keys \"item\", \"price\", \"category\", and optionally \"note\". "
            "Do not add extra text. Example: {\"item\": \"coffee\", \"price\": 4.50, \"category\": \"Food\"}."
        )

        try:
            client = Groq(api_key=api_key)
            response = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": user_input},
                ],
                model=get_model_name(),
                temperature=0.0,
            )
            content = response.choices[0].message.content
            parsed = safe_parse_json(content)
            data = validate_expense_data(parsed)
            if data:
                return data
        except Exception:
            pass

    # Local fallback parser if AI fails or API is unavailable
    fallback = extract_expense_from_text(user_input)
    return validate_expense_data(fallback)


def add_expense_record(
    db: Dict[str, Any], 
    username: str, 
    month: str, 
    item: str, 
    price: float, 
    category: str, 
    note: str = ""
) -> bool:
    """Add an expense record to the database."""
    ensure_user_month(db, username, month)
    
    expense_record = {
        "item": item,
        "price": float(price),
        "category": category,
        "note": note,
        "timestamp": datetime.now().isoformat(sep=" ", timespec="seconds"),
    }

    db[username][month][category].append(expense_record)
    save_database(db)
    return True


def get_month_summary(month_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """Calculate summary for a month."""
    summary = {}
    total = 0.0
    item_count = 0

    for category, items in month_data.items():
        subtotal = sum(expense["price"] for expense in items)
        summary[category] = {
            "subtotal": subtotal,
            "count": len(items),
            "items": items,
        }
        total += subtotal
        item_count += len(items)

    return {"total": total, "item_count": item_count, "categories": summary}


def get_user_months(db: Dict[str, Any], username: str) -> List[str]:
    """Get list of months for a user, excluding profile metadata."""
    return sorted([
        key for key in (db.get(username, {}) or {}).keys()
        if key not in USER_METADATA_KEYS
    ])


def export_to_csv(db: Dict[str, Any], username: str, month: str) -> Optional[str]:
    """Export month data to CSV and return filename."""
    month_data = db.get(username, {}).get(month)
    if not month_data:
        return None

    export_name = f"export_{username}_{month}.csv".replace(" ", "_")
    with open(export_name, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=["timestamp", "item", "category", "price", "note"])
        writer.writeheader()
        for category in ALLOWED_CATEGORIES:
            for expense in month_data.get(category, []):
                writer.writerow({
                    "timestamp": expense["timestamp"],
                    "item": expense["item"],
                    "category": expense["category"],
                    "price": f"{expense['price']:.2f}",
                    "note": expense.get("note", ""),
                })

    return export_name


def format_currency(value: float) -> str:
    """Format value as currency string."""
    return f"${value:.2f}"


def get_all_expenses(month_data: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """Get all expenses across all categories for a month."""
    return [expense for items in month_data.values() for expense in items]


def get_spending_by_day(expenses: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calculate spending by day."""
    by_day = defaultdict(float)
    for expense in expenses:
        day = expense["timestamp"].split()[0]
        by_day[day] += expense["price"]
    return dict(sorted(by_day.items()))
