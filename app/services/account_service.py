from __future__ import annotations

from collections import OrderedDict
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.api.serializers import to_project_response
from app.core.exceptions import AuthenticationError, NotFoundError, ValidationError
from app.core.security import verify_password
from app.models.project import Project
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.account import (
    AccountExportAccount,
    AccountExportBillingData,
    AccountExportBusinessProfile,
    AccountExportClient,
    AccountExportResponse,
)
from app.schemas.project import PaymentRecordResponse, TaskResponse


class AccountService:
    __slots__ = ("db", "users")

    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)

    def export_user_data(self, *, user: User) -> AccountExportResponse:
        hydrated_user = self.users.get_with_owned_data(user.id)
        if hydrated_user is None:
            raise NotFoundError("User not found.")

        workspace = hydrated_user.workspace
        projects = list(workspace.projects) if workspace is not None else []
        tasks = [task for project in projects for task in project.tasks]
        payment_records = [
            payment_record
            for project in projects
            for payment_record in project.payment_records
        ]

        return AccountExportResponse(
            exported_at=datetime.now(UTC),
            account=AccountExportAccount(
                id=hydrated_user.id,
                email=hydrated_user.email,
                is_admin=hydrated_user.is_admin,
                email_verified=hydrated_user.email_verified,
                email_verified_at=hydrated_user.email_verified_at,
            ),
            business_profile=(
                AccountExportBusinessProfile(
                    workspace_id=workspace.id,
                    workspace_name=workspace.name,
                    company_name=workspace.company_name,
                    monthly_capacity_hours=workspace.monthly_capacity_hours,
                )
                if workspace is not None
                else None
            ),
            clients=self._clients_from_projects(projects),
            projects=[to_project_response(project) for project in projects],
            tasks=[TaskResponse.model_validate(task) for task in tasks],
            billing=AccountExportBillingData(
                payment_records=[
                    PaymentRecordResponse.model_validate(payment_record)
                    for payment_record in payment_records
                ]
            ),
        )

    def delete_own_account(
        self,
        *,
        user: User,
        password: str,
        confirm_admin_self_deletion: bool,
    ) -> None:
        hydrated_user = self.users.get_with_owned_data(user.id)
        if hydrated_user is None:
            raise NotFoundError("User not found.")

        if not verify_password(password, hydrated_user.password_hash):
            raise AuthenticationError("Password confirmation failed.")
        if hydrated_user.is_admin and not confirm_admin_self_deletion:
            raise ValidationError(
                "Admin self-deletion requires confirm_admin_self_deletion=true."
            )

        self.users.detach_feedback(hydrated_user.id)
        self.users.delete(hydrated_user)
        self.db.commit()

    def _clients_from_projects(
        self, projects: list[Project]
    ) -> list[AccountExportClient]:
        clients: OrderedDict[str, list[int]] = OrderedDict()
        for project in projects:
            clients.setdefault(project.client_name, []).append(project.id)
        return [
            AccountExportClient(name=client_name, project_ids=project_ids)
            for client_name, project_ids in clients.items()
        ]
