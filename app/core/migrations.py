from __future__ import annotations

from sqlalchemy import Engine, inspect, text


def ensure_project_billing_columns(engine: Engine) -> None:
    """Add phase-1 project billing columns for existing local SQLite databases."""
    inspector = inspect(engine)
    if not inspector.has_table("projects"):
        return

    existing_columns = {column["name"] for column in inspector.get_columns("projects")}
    statements = {
        "contract_type": (
            "ALTER TABLE projects ADD COLUMN contract_type VARCHAR(32) "
            "NOT NULL DEFAULT 'fixed_price'"
        ),
        "billing_status": (
            "ALTER TABLE projects ADD COLUMN billing_status VARCHAR(32) "
            "NOT NULL DEFAULT 'unpaid'"
        ),
        "billing_currency": (
            "ALTER TABLE projects ADD COLUMN billing_currency VARCHAR(3) "
            "NOT NULL DEFAULT 'USD'"
        ),
        "billing_cycle": (
            "ALTER TABLE projects ADD COLUMN billing_cycle VARCHAR(32) "
            "NOT NULL DEFAULT 'monthly'"
        ),
        "agreed_amount": "ALTER TABLE projects ADD COLUMN agreed_amount NUMERIC(12, 2)",
        "monthly_rate": "ALTER TABLE projects ADD COLUMN monthly_rate NUMERIC(12, 2)",
        "monthly_amount": (
            "ALTER TABLE projects ADD COLUMN monthly_amount NUMERIC(12, 2)"
        ),
        "payment_due_day": "ALTER TABLE projects ADD COLUMN payment_due_day INTEGER",
        "next_payment_due_date": (
            "ALTER TABLE projects ADD COLUMN next_payment_due_date DATE"
        ),
        "payment_status": (
            "ALTER TABLE projects ADD COLUMN payment_status VARCHAR(32) "
            "NOT NULL DEFAULT 'pending'"
        ),
        "paid_at": "ALTER TABLE projects ADD COLUMN paid_at DATETIME",
        "billing_notes": "ALTER TABLE projects ADD COLUMN billing_notes TEXT",
    }

    with engine.begin() as connection:
        added_columns: set[str] = set()
        for column_name, statement in statements.items():
            if column_name not in existing_columns:
                connection.execute(text(statement))
                added_columns.add(column_name)

        refreshed_columns = existing_columns | set(statements)
        if "monthly_amount" in added_columns and {
            "monthly_amount",
            "monthly_rate",
        }.issubset(refreshed_columns):
            connection.execute(
                text(
                    "UPDATE projects "
                    "SET monthly_amount = monthly_rate "
                    "WHERE monthly_amount IS NULL AND monthly_rate IS NOT NULL"
                )
            )
        if "payment_status" in added_columns and {
            "payment_status",
            "billing_status",
        }.issubset(refreshed_columns):
            connection.execute(
                text(
                    "UPDATE projects "
                    "SET payment_status = CASE "
                    "WHEN billing_status = 'paid' THEN 'paid' "
                    "WHEN billing_status = 'overdue' THEN 'overdue' "
                    "WHEN billing_status = 'not_billable' THEN 'not_started' "
                    "ELSE 'pending' END"
                )
            )
