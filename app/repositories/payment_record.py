from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.payment_record import PaymentRecord


class PaymentRecordRepository:
    __slots__ = ("db",)

    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, payment_record: PaymentRecord) -> PaymentRecord:
        self.db.add(payment_record)
        self.db.flush()
        return payment_record

    def list_for_project(self, project_id: int) -> list[PaymentRecord]:
        stmt = (
            select(PaymentRecord)
            .where(PaymentRecord.project_id == project_id)
            .order_by(
                PaymentRecord.due_date.is_(None),
                PaymentRecord.due_date,
                PaymentRecord.id,
            )
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_for_project(
        self,
        *,
        payment_record_id: int,
        project_id: int,
    ) -> PaymentRecord | None:
        stmt = select(PaymentRecord).where(
            PaymentRecord.id == payment_record_id,
            PaymentRecord.project_id == project_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def save(self, payment_record: PaymentRecord) -> PaymentRecord:
        self.db.add(payment_record)
        self.db.flush()
        return payment_record

    def delete(self, payment_record: PaymentRecord) -> None:
        self.db.delete(payment_record)
        self.db.flush()
