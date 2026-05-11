from __future__ import annotations

from app.domain.project_rules import calculate_progress_percent
from app.models.project import Project
from app.models.workspace import Workspace
from app.schemas.project import ProjectResponse, TaskResponse
from app.schemas.workspace import WorkspaceResponse


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
        budget_cents=project.budget_cents,
        hourly_rate_cents=project.hourly_rate_cents,
        contract_type=project.contract_type,
        billing_cycle=project.billing_cycle,
        billing_status=project.billing_status,
        payment_status=project.payment_status,
        billing_currency=project.billing_currency,
        currency=project.billing_currency,
        agreed_amount=project.agreed_amount,
        monthly_rate=project.monthly_rate,
        monthly_amount=project.monthly_amount,
        payment_due_day=project.payment_due_day,
        next_payment_due_date=project.next_payment_due_date,
        paid_at=project.paid_at,
        billing_notes=project.billing_notes,
        deadline=project.deadline,
        archived=project.archived,
        created_at=project.created_at,
        updated_at=project.updated_at,
        progress_percent=calculate_progress_percent(task.status for task in tasks),
        estimated_hours=round(sum(task.estimated_minutes for task in tasks) / 60, 2),
        actual_hours=round(sum(task.actual_minutes for task in tasks) / 60, 2),
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
