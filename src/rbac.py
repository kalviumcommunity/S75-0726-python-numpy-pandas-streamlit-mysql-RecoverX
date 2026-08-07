
import hashlib

from src.db import execute_query


ROLE_LABELS = {
    "FINANCE_MANAGER": "Finance Manager",
    "PAYMENTS_ANALYST": "Payments Analyst",
    "RISK_OPS": "Risk Ops",
}

PAGE_KEYS = [
    "dashboard",
    "csv_import",
    "payment_lifecycle",
    "failure_analysis",
    "retry_analytics",
    "revenue_recovery",
    "alerts_crud",
]

ROLE_PERMISSIONS = {
    "FINANCE_MANAGER": {
        "dashboard": True,
        "csv_import": True,
        "payment_lifecycle": True,
        "failure_analysis": True,
        "retry_analytics": True,
        "revenue_recovery": True,
        "alerts_crud": True,
    },
    "PAYMENTS_ANALYST": {
        "dashboard": True,
        "csv_import": True,
        "payment_lifecycle": True,
        "failure_analysis": True,
        "retry_analytics": True,
        "revenue_recovery": True,
        "alerts_crud": False,
    },
    "RISK_OPS": {
        "dashboard": False,
        "csv_import": False,
        "payment_lifecycle": False,
        "failure_analysis": True,
        "retry_analytics": False,
        "revenue_recovery": False,
        "alerts_crud": True,
    },
}


def hash_password(password: str) -> str:
    """
    Hash a password for storage in the users.password_hash column.

    Uses a single sha256 round (kept simple to match generate_test_data.py
    seed hashes and avoid extra dependencies when bcrypt/argon2 are not
    installed). For production usage, replace with bcrypt or argon2.
    """
    if password is None:
        password = ""
    return hashlib.sha256(str(password).encode("utf-8")).hexdigest()


def verify_user(username: str, password: str):
    """
    Look up the user by username (case-insensitive comparison via SQL)
    and return the user dict if the password matches; otherwise return None.

    User dict keys: user_id, username, role, email, created_at.
    """
    if not username or password is None:
        return None

    query = """
    SELECT user_id, username, password_hash, role, email, created_at
    FROM users
    WHERE username = %s
    LIMIT 1;
    """
    rows = execute_query(query, (str(username),), fetch=True)
    if not rows:
        return None

    user = rows[0]
    stored_hash = user.get("password_hash", "")
    provided_hash = hash_password(password)

    if provided_hash != stored_hash:
        return None

    return {
        "user_id": user.get("user_id"),
        "username": user.get("username"),
        "role": user.get("role"),
        "email": user.get("email"),
        "created_at": user.get("created_at"),
    }


def get_user_permissions(role: str) -> dict:
    """
    Return a dict of page_key -> bool for the given role.

    Roles: FINANCE_MANAGER, PAYMENTS_ANALYST, RISK_OPS.
    Unknown/None role returns an all-False permission block.
    """
    if role is None:
        return {page: False for page in PAGE_KEYS}
    role_up = str(role).upper()
    if role_up not in ROLE_PERMISSIONS:
        return {page: False for page in PAGE_KEYS}
    return dict(ROLE_PERMISSIONS[role_up])


def role_label(role: str) -> str:
    if role is None:
        return "Guest"
    return ROLE_LABELS.get(str(role).upper(), str(role))
