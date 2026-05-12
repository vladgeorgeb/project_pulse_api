from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.domain.enums import PaymentRecordStatus
from app.models.payment_record import PaymentRecord
from app.models.project import Project
from app.models.user import User
from app.repositories.payment_record import PaymentRecordRepository
from app.repositories.project import ProjectRepository
from app.repositories.workspace import WorkspaceRepository


class PaymentRecordService:
    __slots__ = ("db", "payment_records", "projects", "workspaces")

    def __init__(self, db: Session) -> None:
        self.db = db
        self.payment_records = PaymentRecordRepository(db)
        self.projects = ProjectRepository(db)
        self.workspaces = WorkspaceRepository(db)

    def list_payment_records_for_project(
        self,
        *,
        user: User,
        project_id: int,
    ) -> list[PaymentRecord]:
        project = self._project_for_user(user=user, project_id=project_id)
        return self.payment_records.list_for_project(project.id)

    def get_payment_record_for_project(
        self,
        *,
        user: User,
        project_id: int,
        payment_record_id: int,
    ) -> PaymentRecord:
        project = self._project_for_user(user=user, project_id=project_id)
        payment_record = self.payment_records.get_for_project(
            payment_record_id=payment_record_id,
            project_id=project.id,
        )
        if payment_record is None:
            raise NotFoundError("Payment record not found.")
        return payment_record

    def create_payment_record(
        self,
        *,
        user: User,
        project_id: int,
        amount_cents: int,
        currency: str,
        status: str,
        method: str | None,
        paid_at: datetime | None,
        due_date: date | None,
        period_start: date | None,
        period_end: date | None,
        notes: str | None,
        invoice_id: int | None,
    ) -> PaymentRecord:
        project = self._project_for_user(user=user, project_id=project_id)
        if (
            period_start is not None
            and period_end is not None
            and period_start > period_end
        ):
            raise ValidationError("period_start cannot be later than period_end.")
        if status == PaymentRecordStatus.PAID.value and paid_at is None:
            paid_at = datetime.now(UTC).replace(tzinfo=None)
        if status == PaymentRecordStatus.PENDING.value and due_date is None:
            raise ValidationError("pending payments require due_date.")

        now = datetime.now(UTC).replace(tzinfo=None)
        payment_record = PaymentRecord(
            project_id=project.id,
            amount_cents=amount_cents,
            currency=currency.strip().upper(),
            status=status,
            method=method.strip() if method else None,
            paid_at=paid_at,
            due_date=due_date,
            period_start=period_start,
            period_end=period_end,
            notes=notes.strip() if notes else None,
            invoice_id=invoice_id,
            created_at=now,
            updated_at=now,
        )
        self.payment_records.add(payment_record)
        self.db.commit()
        self.db.refresh(payment_record)
        return payment_record

    def update_payment_record(
        self,
        *,
        user: User,
        project_id: int,
        payment_record_id: int,
        amount_cents: int | None,
        amount_cents_provided: bool,
        currency: str | None,
        status: str | None,
        method: str | None,
        method_provided: bool,
        paid_at: datetime | None,
        paid_at_provided: bool,
        due_date: date | None,
        due_date_provided: bool,
        period_start: date | None,
        period_start_provided: bool,
        period_end: date | None,
        period_end_provided: bool,
        notes: str | None,
        notes_provided: bool,
        invoice_id: int | None,
        invoice_id_provided: bool,
    ) -> PaymentRecord:
        project = self._project_for_user(user=user, project_id=project_id)
        payment_record = self.payment_records.get_for_project(
            payment_record_id=payment_record_id,
            project_id=project.id,
        )
        if payment_record is None:
            raise NotFoundError("Payment record not found.")

        if amount_cents_provided:
            if amount_cents is None:
                raise ValidationError("amount_cents cannot be null.")
            payment_record.amount_cents = amount_cents
        if currency is not None:
            payment_record.currency = currency.strip().upper()
        if status is not None:
            payment_record.status = status
            if (
                status == PaymentRecordStatus.PAID.value
                and not paid_at_provided
                and payment_record.paid_at is None
            ):
                payment_record.paid_at = datetime.now(UTC).replace(tzinfo=None)
            elif status != PaymentRecordStatus.PAID.value and not paid_at_provided:
                payment_record.paid_at = None
        if method_provided:
            payment_record.method = method.strip() if method else None
        if paid_at_provided:
            payment_record.paid_at = paid_at
        if due_date_provided:
            payment_record.due_date = due_date
        if period_start_provided:
            payment_record.period_start = period_start
        if period_end_provided:
            payment_record.period_end = period_end
        if notes_provided:
            payment_record.notes = notes.strip() if notes else None
        if invoice_id_provided:
            payment_record.invoice_id = invoice_id

        if (
            payment_record.period_start is not None
            and payment_record.period_end is not None
            and payment_record.period_start > payment_record.period_end
        ):
            raise ValidationError("period_start cannot be later than period_end.")
        if (
            payment_record.status == PaymentRecordStatus.PENDING.value
            and payment_record.due_date is None
        ):
            raise ValidationError("pending payments require due_date.")
        if (
            payment_record.status == PaymentRecordStatus.PAID.value
            and payment_record.paid_at is None
        ):
            raise ValidationError("paid payments require paid_at.")

        payment_record.updated_at = datetime.now(UTC).replace(tzinfo=None)
        self.payment_records.save(payment_record)
        self.db.commit()
        self.db.refresh(payment_record)
        return payment_record

    def delete_payment_record(
        self,
        *,
        user: User,
        project_id: int,
        payment_record_id: int,
    ) -> None:
        project = self._project_for_user(user=user, project_id=project_id)
        payment_record = self.payment_records.get_for_project(
            payment_record_id=payment_record_id,
            project_id=project.id,
        )
        if payment_record is None:
            raise NotFoundError("Payment record not found.")
        self.payment_records.delete(payment_record)
        self.db.commit()

    def _project_for_user(self, *, user: User, project_id: int) -> Project:
        workspace = self.workspaces.get_by_user_id(user.id)
        if workspace is None:
            raise NotFoundError("Workspace not found.")
        project = self.projects.get_for_workspace(
            project_id=project_id,
            workspace_id=workspace.id,
        )
        if project is None:
            raise NotFoundError("Project not found.")
        return project
