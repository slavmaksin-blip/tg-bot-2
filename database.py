import aiosqlite
import logging
from datetime import datetime, timedelta, timezone
from config import DB_PATH

logger = logging.getLogger(__name__)


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                is_subscribed BOOLEAN DEFAULT FALSE,
                subscription_until DATETIME,
                balance REAL DEFAULT 0.0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_banned BOOLEAN DEFAULT FALSE
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price REAL NOT NULL,
                stock_quantity INTEGER DEFAULT 0,
                file_id TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                type TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                invoice_id TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                processed BOOLEAN DEFAULT FALSE
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS promo_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                reward REAL NOT NULL,
                max_activations INTEGER NOT NULL,
                used_count INTEGER DEFAULT 0,
                created_by INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS admin_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                user_id INTEGER,
                details TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_promo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                promo_id INTEGER NOT NULL,
                UNIQUE(user_id, promo_id)
            )
        """)
        await db.commit()
    logger.info("Database initialized successfully.")


# ─── Users ───────────────────────────────────────────────────────────────────

async def get_user(user_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def create_or_update_user(user_id: int, username: str | None) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (user_id, username)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET username = excluded.username
        """, (user_id, username))
        await db.commit()


async def is_user_banned(user_id: int) -> bool:
    user = await get_user(user_id)
    return bool(user and user["is_banned"])


async def ban_user(user_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET is_banned = TRUE WHERE user_id = ?", (user_id,)
        )
        await db.commit()


async def unban_user(user_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET is_banned = FALSE WHERE user_id = ?", (user_id,)
        )
        await db.commit()


async def get_user_balance(user_id: int) -> float:
    user = await get_user(user_id)
    return float(user["balance"]) if user else 0.0


async def update_balance(user_id: int, amount: float) -> float:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET balance = balance + ? WHERE user_id = ?",
            (amount, user_id)
        )
        await db.commit()
    return await get_user_balance(user_id)


async def set_balance(user_id: int, balance: float) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET balance = ? WHERE user_id = ?",
            (balance, user_id)
        )
        await db.commit()


async def has_active_subscription(user_id: int) -> bool:
    user = await get_user(user_id)
    if not user:
        return False
    if user["subscription_until"]:
        expiry = datetime.fromisoformat(user["subscription_until"])
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        return expiry > datetime.now(timezone.utc)
    return False


async def add_subscription(user_id: int, days: int) -> datetime:
    user = await get_user(user_id)
    now = datetime.now(timezone.utc)
    if user and user["subscription_until"]:
        try:
            current = datetime.fromisoformat(user["subscription_until"])
            if current.tzinfo is None:
                current = current.replace(tzinfo=timezone.utc)
            base = current if current > now else now
        except (ValueError, TypeError):
            base = now
    else:
        base = now
    new_expiry = base + timedelta(days=days)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET subscription_until = ?, is_subscribed = TRUE WHERE user_id = ?",
            (new_expiry.isoformat(), user_id)
        )
        await db.commit()
    return new_expiry


async def get_all_users_not_banned() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE is_banned = FALSE"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def get_all_users_balances() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT user_id, username, balance, subscription_until FROM users ORDER BY balance DESC"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


# ─── Products ────────────────────────────────────────────────────────────────

async def get_categories() -> list[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT DISTINCT category FROM products WHERE stock_quantity > 0"
        ) as cursor:
            rows = await cursor.fetchall()
            return [r[0] for r in rows]


async def get_products_by_category(category: str) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT name, category, price,
                   COUNT(*) AS stock_quantity
            FROM products
            WHERE category = ? AND stock_quantity > 0
            GROUP BY name, category, price
            """,
            (category,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def get_all_products_grouped() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT name, category, price,
                   COUNT(*) AS stock_quantity
            FROM products
            WHERE stock_quantity > 0
            GROUP BY name, category, price
            ORDER BY category, name
            """
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def get_product_stock(name: str, category: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM products WHERE name = ? AND category = ? AND stock_quantity > 0",
            (name, category)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0


async def get_product_price(name: str, category: str) -> float | None:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT price FROM products WHERE name = ? AND category = ? LIMIT 1",
            (name, category)
        ) as cursor:
            row = await cursor.fetchone()
            return float(row[0]) if row else None


async def purchase_product_items(name: str, category: str, quantity: int) -> list[str]:
    """Returns list of file_ids for purchased items and removes them from DB."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT id, file_id FROM products
            WHERE name = ? AND category = ? AND stock_quantity > 0
            LIMIT ?
            """,
            (name, category, quantity)
        ) as cursor:
            rows = await cursor.fetchall()

        if len(rows) < quantity:
            return []

        ids = [r["id"] for r in rows]
        file_ids = [r["file_id"] for r in rows]

        placeholders = ",".join("?" * len(ids))
        await db.execute(
            f"DELETE FROM products WHERE id IN ({placeholders})", ids
        )
        await db.commit()
        return file_ids


async def add_product(name: str, category: str, price: float, file_id: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO products (name, category, price, stock_quantity, file_id)
            VALUES (?, ?, ?, 1, ?)
            """,
            (name, category, price, file_id)
        )
        await db.commit()


# ─── Transactions ─────────────────────────────────────────────────────────────

async def create_transaction(
    user_id: int,
    amount: float,
    tx_type: str,
    invoice_id: str | None = None
) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO transactions (user_id, amount, type, status, invoice_id)
            VALUES (?, ?, ?, 'pending', ?)
            """,
            (user_id, amount, tx_type, invoice_id)
        )
        await db.commit()
        return cursor.lastrowid


async def get_transaction_by_invoice(invoice_id: str) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM transactions WHERE invoice_id = ?", (invoice_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def mark_transaction_processed(invoice_id: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            UPDATE transactions
            SET status = 'completed', processed = TRUE
            WHERE invoice_id = ?
            """,
            (invoice_id,)
        )
        await db.commit()


async def is_transaction_processed(invoice_id: str) -> bool:
    tx = await get_transaction_by_invoice(invoice_id)
    return bool(tx and tx["processed"])


# ─── Promo Codes ─────────────────────────────────────────────────────────────

async def get_promo_code(code: str) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM promo_codes WHERE code = ?", (code,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def has_user_used_promo(user_id: int, promo_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id FROM user_promo WHERE user_id = ? AND promo_id = ?",
            (user_id, promo_id)
        ) as cursor:
            row = await cursor.fetchone()
            return row is not None


async def use_promo_code(user_id: int, promo_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO user_promo (user_id, promo_id) VALUES (?, ?)",
            (user_id, promo_id)
        )
        await db.execute(
            "UPDATE promo_codes SET used_count = used_count + 1 WHERE id = ?",
            (promo_id,)
        )
        await db.commit()


async def delete_promo_if_exhausted(promo_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT used_count, max_activations FROM promo_codes WHERE id = ?",
            (promo_id,)
        ) as cursor:
            row = await cursor.fetchone()
        if row and row[0] >= row[1]:
            await db.execute("DELETE FROM promo_codes WHERE id = ?", (promo_id,))
            await db.execute("DELETE FROM user_promo WHERE promo_id = ?", (promo_id,))
            await db.commit()


async def create_promo_code(
    code: str, reward: float, max_activations: int, created_by: int
) -> bool:
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                """
                INSERT INTO promo_codes (code, reward, max_activations, created_by)
                VALUES (?, ?, ?, ?)
                """,
                (code, reward, max_activations, created_by)
            )
            await db.commit()
        return True
    except aiosqlite.IntegrityError:
        return False


# ─── Admin Logs ──────────────────────────────────────────────────────────────

async def add_admin_log(action: str, user_id: int | None = None, details: str | None = None) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO admin_logs (action, user_id, details) VALUES (?, ?, ?)",
            (action, user_id, details)
        )
        await db.commit()
