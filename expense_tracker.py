import csv
import json
import os
import sys
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


def load_database() -> Dict[str, Any]:
    """Load or initialize the JSON database."""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                print("Warning: Database file is corrupted. Starting with an empty database.")
                return {}
    return {}


def save_database(data: Dict[str, Any]) -> None:
    """Save the database back to JSON."""
    with open(DB_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, sort_keys=True)


def normalize_username(raw: str) -> str:
    return raw.strip().title()


def current_month_key() -> str:
    return datetime.now().strftime("%Y-%m")


def ensure_user_month(db: Dict[str, Any], username: str, month: str) -> None:
    if username not in db:
        db[username] = {}
    if month not in db[username]:
        db[username][month] = {category: [] for category in ALLOWED_CATEGORIES}


def safe_parse_json(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None

    # Groq may return JSON embedded in text. Try to extract first JSON object.
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        return None

    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return None


def validate_expense_data(data: Any) -> Optional[Dict[str, Any]]:
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
    api_key = get_api_key()
    if not api_key:
        print("\nError: Groq API key is not configured. Set GROQ_API_KEY in your environment or .env file.")
        return None

    if Groq is None:
        print("\nError: The 'groq' Python package is not installed. Install requirements from requirements.txt.")
        return None

    prompt = (
        "You are a financial assistant. Extract the item name, price (as a float), "
        "and category from this expense description. Allowed categories: Food, Bills, Fun, Transit, Other. "
        "Return ONLY a valid JSON object with keys \"item\", \"price\", and \"category\". "
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
        return validate_expense_data(parsed)
    except Exception as exc:
        print(f"\n[AI parse error: {exc}]")
        return None


def prompt_manual_expense() -> Optional[Dict[str, Any]]:
    print("\nAI parsing failed. Please enter the expense manually.")
    item = input("Item name: ").strip()
    if not item:
        print("Item name cannot be empty.")
        return None

    price_input = input("Price: ").strip()
    try:
        price = float(price_input)
    except ValueError:
        print("Invalid price. Use numbers only.")
        return None

    category = input(f"Category ({', '.join(ALLOWED_CATEGORIES)}): ").strip().title() or "Other"
    if category not in ALLOWED_CATEGORIES:
        print("Unknown category, defaulting to Other.")
        category = "Other"

    note = input("Optional note: ").strip()
    return {"item": item, "price": price, "category": category, "note": note}


def add_expense(db: Dict[str, Any], username: str, month: str) -> None:
    raw = input("Describe your purchase: ").strip()
    if not raw:
        print("No input received.")
        return

    expense = analyze_expense_with_ai(raw)
    if expense is None:
        expense = prompt_manual_expense()
    if expense is None:
        print("Expense entry skipped.")
        return

    expense_record = {
        "item": expense["item"],
        "price": expense["price"],
        "category": expense["category"],
        "note": expense.get("note", ""),
        "timestamp": datetime.now().isoformat(sep=" ", timespec="seconds"),
    }

    db[username][month][expense_record["category"]].append(expense_record)
    save_database(db)
    print(f"✅ Added {expense_record['item']} for ${expense_record['price']:.2f} to {expense_record['category']}.\n")


def format_currency(value: float) -> str:
    return f"${value:.2f}"


def summarize_month(month_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    summary = {}
    total = 0.0
    item_count = 0

    for category, items in month_data.items():
        subtotal = sum(expense["price"] for expense in items)
        summary[category] = {
            "subtotal": subtotal,
            "count": len(items),
            "top_items": sorted(items, key=lambda e: e["price"], reverse=True)[:5],
        }
        total += subtotal
        item_count += len(items)

    return {"total": total, "item_count": item_count, "categories": summary}


def show_summary(db: Dict[str, Any], username: str, month: str) -> None:
    month_data = db.get(username, {}).get(month)
    if not month_data:
        print(f"No entries found for {month}.")
        return

    summary = summarize_month(month_data)
    print("\n" + "=" * 40)
    print(f"Summary for {username} — {month}")
    print("=" * 40)

    for category in ALLOWED_CATEGORIES:
        category_data = summary["categories"].get(category, {})
        if category_data and category_data["subtotal"] > 0:
            print(f"{category}: {format_currency(category_data['subtotal'])} ({category_data['count']} items)")

    print("-" * 40)
    print(f"TOTAL SPENT: {format_currency(summary['total'])}")
    print(f"TOTAL ITEMS: {summary['item_count']}")


def print_month_report(db: Dict[str, Any], username: str, month: str) -> None:
    month_data = db.get(username, {}).get(month)
    if not month_data:
        print(f"No data available for {month}.")
        return

    summary = summarize_month(month_data)
    print("\n" + "#" * 40)
    print(f"Monthly report for {username} — {month}")
    print("#" * 40)
    show_summary(db, username, month)

    print("\nTop 5 expenses across all categories:")
    all_expenses = [expense for items in month_data.values() for expense in items]
    for expense in sorted(all_expenses, key=lambda e: e["price"], reverse=True)[:5]:
        print(f"- {expense['item']} ({expense['category']}): {format_currency(expense['price'])} on {expense['timestamp']}")

    by_day = defaultdict(float)
    for expense in all_expenses:
        day = expense["timestamp"].split()[0]
        by_day[day] += expense["price"]

    if by_day:
        print("\nSpending by day:")
        for day in sorted(by_day):
            print(f"  {day}: {format_currency(by_day[day])}")


def export_to_csv(db: Dict[str, Any], username: str, month: str) -> None:
    month_data = db.get(username, {}).get(month)
    if not month_data:
        print(f"No data available for {month}. Nothing to export.")
        return

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

    print(f"Exported CSV to {export_name}")


def list_user_months(db: Dict[str, Any], username: str) -> None:
    months = sorted(db.get(username, {}) or [])
    if not months:
        print("No recorded months yet.")
        return
    print("Available months:")
    for month in months:
        print(f"- {month}")


def print_help() -> None:
    print("\nAvailable commands:")
    print("  add      - Add a new expense")
    print("  summary  - Show summary for current month")
    print("  report   - Show a detailed monthly report")
    print("  export   - Export current month to CSV")
    print("  months   - List available months")
    print("  switch   - Switch to a different month")
    print("  help     - Show this help text")
    print("  exit     - Exit the tracker")


def main() -> None:
    print("🤖 AI Expense Tracker")
    print("Tip: store GROQ_API_KEY in your environment or a .env file.")

    db = load_database()
    username = normalize_username(input("Enter your username: "))
    if not username:
        print("Username cannot be empty.")
        return

    month = current_month_key()
    ensure_user_month(db, username, month)
    save_database(db)

    if username not in db or not db[username]:
        print(f"Welcome, {username}! Your profile has been created.")
    else:
        print(f"Welcome back, {username}! Using month {month}.")

    print_help()

    while True:
        command = input(f"\n[{username} - {month}] Enter command: ").strip().lower()
        if command == "add":
            add_expense(db, username, month)
        elif command == "summary":
            show_summary(db, username, month)
        elif command == "report":
            print_month_report(db, username, month)
        elif command == "export":
            export_to_csv(db, username, month)
        elif command == "months":
            list_user_months(db, username)
        elif command == "switch":
            target = input("Enter month YYYY-MM to switch to: ").strip()
            if not target:
                print("No month entered.")
            else:
                ensure_user_month(db, username, target)
                month = target
                save_database(db)
                print(f"Switched to {month}.")
        elif command == "help":
            print_help()
        elif command in {"exit", "quit"}:
            print("Goodbye!")
            break
        else:
            print("Unknown command. Type 'help' for a list of commands.")


if __name__ == "__main__":
    main()
