from __future__ import annotations

from decimal import Decimal

from app.domain.enums import ContractType
from app.domain.project_rules import calculate_progress_percent
from app.models.project import Project
from app.models.workspace import Workspace
from app.schemas.payment_record import PaymentRecordResponse
from app.schemas.project import ProjectResponse, TaskResponse
from app.schemas.workspace import WorkspaceResponse


def _expected_weekly_income_cents(project: Project) -> int | None:
    if project.contract_type != ContractType.HOURLY.value:
        return None
    if project.hourly_rate_cents is None or project.expected_hours_per_week is None:
        return None
    return int(
        (Decimal(project.hourly_rate_cents) * project.expected_hours_per_week).quantize(
            Decimal("1")
        )
    )


def _expected_monthly_income_cents(project: Project) -> int | None:
    weekly = _expected_weekly_income_cents(project)
    if weekly is None:
        return None
    return int((Decimal(weekly) * Decimal("4.33")).quantize(Decimal("1")))


def _expected_total_contract_value_cents(project: Project) -> int | None:
    if project.contract_type == ContractType.FIXED_PRICE.value:
        return project.fixed_price_cents
    if project.start_date is None or project.estimated_end_date is None:
        return None
    days = (project.estimated_end_date - project.start_date).days + 1
    if days <= 0:
        return None
    if project.contract_type == ContractType.MONTHLY_RETAINER.value:
        if project.monthly_rate_cents is None:
            return None
        months = Decimal(days) / Decimal("30.44")
        return int(
            (Decimal(project.monthly_rate_cents) * months).quantize(Decimal("1"))
        )
    if project.contract_type == ContractType.HOURLY.value:
        monthly = _expected_monthly_income_cents(project)
        if monthly is None:
            return None
        months = Decimal(days) / Decimal("30.44")
        return int((Decimal(monthly) * months).quantize(Decimal("1")))
    return None


def to_project_response(project: Project) -> ProjectResponse:
    tasks = list(project.tasks)
    return ProjectResponse(
        id=project.id,
        workspace_id=project.workspace_id,
        title=project.title,
        client_name=project.client_name,
        description=project.description,
        status=project.status,
        priority=project.priority,
        contract_type=project.contract_type,
        billing_currency=project.billing_currency,
        hourly_rate_cents=project.hourly_rate_cents,
        expected_hours_per_week=project.expected_hours_per_week,
        monthly_rate_cents=project.monthly_rate_cents,
        fixed_price_cents=project.fixed_price_cents,
        start_date=project.start_date,
        estimated_end_date=project.estimated_end_date,
        deadline=project.deadline,
        payment_cadence=project.payment_cadence,
        billing_notes=project.billing_notes,
        created_at=project.created_at,
        updated_at=project.updated_at,
        progress_percent=calculate_progress_percent(task.status for task in tasks),
        estimated_hours=round(sum(task.estimated_minutes for task in tasks) / 60, 2),
        actual_hours=round(sum(task.actual_minutes for task in tasks) / 60, 2),
        expected_weekly_income_cents=_expected_weekly_income_cents(project),
        expected_monthly_income_cents=_expected_monthly_income_cents(project),
        expected_total_contract_value_cents=_expected_total_contract_value_cents(
            project
        ),
        payment_records=[
            PaymentRecordResponse.model_validate(payment_record)
            for payment_record in project.payment_records
        ],
        tasks=[TaskResponse.model_validate(task) for task in tasks],
    )


def to_workspace_response(workspace: Workspace) -> WorkspaceResponse:
    return WorkspaceResponse(
        id=workspace.id,
        user_id=workspace.user_id,
        name=workspace.name,
        company_name=workspace.company_name,
        monthly_capacity_hours=workspace.monthly_capacity_hours,
        projects=[to_project_response(project) for project in workspace.projects],
    )
