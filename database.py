import sqlite3
import logging
from datetime import datetime
from contextlib import contextmanager

logger = logging.getLogger(__name__)
DB_PATH = "database.db"

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def execute_query(query: str, params=(), fetch=None):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        if fetch == "one":
            row = cursor.fetchone()
            return dict(row) if row else None
        elif fetch == "all":
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        return cursor.lastrowid

def init_db():
    queries = [
        """CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            username TEXT,
            is_subscribed BOOLEAN DEFAULT 0,
            subscription_until DATETIME,
            balance REAL DEFAULT 0.0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_banned BOOLEAN DEFAULT 0
        )""",
        """CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            category TEXT,
            price REAL,
            stock_quantity INTEGER DEFAULT 1,
            file_id TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            type TEXT,
            status TEXT DEFAULT 'pending',
            invoice_id TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            processed BOOLEAN DEFAULT 0
        )""",
        """CREATE TABLE IF NOT EXISTS promo_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE,
            reward REAL,
            max_activations INTEGER,
            used_count INTEGER DEFAULT 0,
            created_by INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS user_promo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            promo_id INTEGER,
            activated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS admin_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT,
            user_id INTEGER,
            details TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS email_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            order_id TEXT,
            domain TEXT,
            email TEXT,
            price REAL,
            status TEXT DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""",
    ]
    for q in queries:
        execute_query(q)
    logger.info("Database initialized")

def get_user(user_id: int):
    return execute_query("SELECT * FROM users WHERE user_id = ?", (user_id,), fetch="one")

def create_user(user_id: int, username: str):
    execute_query(
        "INSERT OR IGNORE INTO users (user_id, username, created_at) VALUES (?, ?, ?)",
        (user_id, username, datetime.now().isoformat())
    )

def update_user_subscription(user_id: int, until: datetime):
    execute_query(
        "UPDATE users SET is_subscribed = 1, subscription_until = ? WHERE user_id = ?",
        (until.isoformat(), user_id)
    )

def check_subscription(user_id: int) -> bool:
    user = get_user(user_id)
    if not user:
        return False
    if not user.get("is_subscribed"):
        return False
    if not user.get("subscription_until"):
        return False
    try:
        until = datetime.fromisoformat(user["subscription_until"])
        return until > datetime.now()
    except Exception:
        return False

def get_user_balance(user_id: int) -> float:
    user = get_user(user_id)
    return user["balance"] if user else 0.0

def update_user_balance(user_id: int, amount: float):
    execute_query(
        "UPDATE users SET balance = balance + ? WHERE user_id = ?",
        (amount, user_id)
    )

def ban_user(user_id: int, is_banned: bool):
    execute_query(
        "UPDATE users SET is_banned = ? WHERE user_id = ?",
        (1 if is_banned else 0, user_id)
    )

def get_all_users():
    return execute_query("SELECT * FROM users", fetch="all")

def add_product(name: str, category: str, price: float, file_id: str):
    execute_query(
        "INSERT INTO products (name, category, price, file_id, created_at) VALUES (?, ?, ?, ?, ?)",
        (name, category, price, file_id, datetime.now().isoformat())
    )

def get_products():
    return execute_query("SELECT * FROM products WHERE stock_quantity > 0", fetch="all")

def get_product(product_id: int):
    return execute_query("SELECT * FROM products WHERE id = ?", (product_id,), fetch="one")

def delete_product(product_id: int):
    execute_query("DELETE FROM products WHERE id = ?", (product_id,))

def add_transaction(user_id: int, amount: float, trans_type: str, invoice_id: str):
    return execute_query(
        "INSERT INTO transactions (user_id, amount, type, invoice_id, created_at) VALUES (?, ?, ?, ?, ?)",
        (user_id, amount, trans_type, invoice_id, datetime.now().isoformat())
    )

def get_transaction(invoice_id: str):
    return execute_query("SELECT * FROM transactions WHERE invoice_id = ?", (invoice_id,), fetch="one")

def complete_transaction(invoice_id: str):
    execute_query(
        "UPDATE transactions SET status = 'completed', processed = 1 WHERE invoice_id = ?",
        (invoice_id,)
    )

def add_promo_code(code: str, reward: float, max_activations: int, created_by: int):
    execute_query(
        "INSERT INTO promo_codes (code, reward, max_activations, created_by, created_at) VALUES (?, ?, ?, ?, ?)",
        (code, reward, max_activations, created_by, datetime.now().isoformat())
    )

def get_promo_code(code: str):
    return execute_query("SELECT * FROM promo_codes WHERE code = ?", (code,), fetch="one")

def check_user_promo(user_id: int, promo_id: int) -> bool:
    result = execute_query(
        "SELECT * FROM user_promo WHERE user_id = ? AND promo_id = ?",
        (user_id, promo_id), fetch="one"
    )
    return result is not None

def activate_promo(user_id: int, promo_id: int):
    execute_query(
        "INSERT INTO user_promo (user_id, promo_id, activated_at) VALUES (?, ?, ?)",
        (user_id, promo_id, datetime.now().isoformat())
    )
    execute_query(
        "UPDATE promo_codes SET used_count = used_count + 1 WHERE id = ?",
        (promo_id,)
    )
    # Fetch updated record to check if max activations reached
    updated_promo = execute_query("SELECT * FROM promo_codes WHERE id = ?", (promo_id,), fetch="one")
    if updated_promo and updated_promo["used_count"] >= updated_promo["max_activations"]:
        execute_query("DELETE FROM promo_codes WHERE id = ?", (promo_id,))

def add_admin_log(action: str, user_id: int, details: str):
    execute_query(
        "INSERT INTO admin_logs (action, user_id, details, created_at) VALUES (?, ?, ?, ?)",
        (action, user_id, details, datetime.now().isoformat())
    )

def add_email_order(user_id: int, order_id: str, domain: str, email: str, price: float):
    execute_query(
        "INSERT INTO email_orders (user_id, order_id, domain, email, price, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, order_id, domain, email, price, datetime.now().isoformat())
    )

def get_email_order(order_id: str):
    return execute_query("SELECT * FROM email_orders WHERE order_id = ?", (order_id,), fetch="one")

def update_email_order_status(order_id: str, status: str):
    execute_query(
        "UPDATE email_orders SET status = ? WHERE order_id = ?",
        (status, order_id)
    )
