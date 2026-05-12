"""add project payment records

Revision ID: 20260511_0002
Revises: 20260511_0001
Create Date: 2026-05-11
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20260511_0002"
down_revision = "20260511_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "payment_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("invoice_id", sa.Integer(), nullable=True),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "currency", sa.String(length=3), server_default="USD", nullable=False
        ),
        sa.Column(
            "status",
            sa.String(length=32),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("method", sa.String(length=80), nullable=True),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("period_start", sa.Date(), nullable=True),
        sa.Column("period_end", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_payment_records_due_date"),
        "payment_records",
        ["due_date"],
        unique=False,
    )
    op.create_index(
        op.f("ix_payment_records_id"), "payment_records", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_payment_records_invoice_id"),
        "payment_records",
        ["invoice_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_payment_records_project_id"),
        "payment_records",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_payment_records_status"),
        "payment_records",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_payment_records_status"), table_name="payment_records")
    op.drop_index(op.f("ix_payment_records_project_id"), table_name="payment_records")
    op.drop_index(op.f("ix_payment_records_invoice_id"), table_name="payment_records")
    op.drop_index(op.f("ix_payment_records_id"), table_name="payment_records")
    op.drop_index(op.f("ix_payment_records_due_date"), table_name="payment_records")
    op.drop_table("payment_records")
