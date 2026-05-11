from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.core.database import get_db
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.user import User
from app.schemas.admin import (
    AdminProjectCreateRequest,
    AdminProjectResponse,
    AdminProjectUpdateRequest,
    AdminTaskCreateRequest,
    AdminTaskResponse,
    AdminTaskUpdateRequest,
    AdminUserCreateRequest,
    AdminUserResponse,
    AdminUserUpdateRequest,
    AdminWorkspaceCreateRequest,
    AdminWorkspaceResponse,
    AdminWorkspaceUpdateRequest,
)
from app.services.admin_service import AdminService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[AdminUserResponse])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> list[AdminUserResponse]:
    return [
        AdminUserResponse.model_validate(user) for user in AdminService(db).list_users()
    ]


@router.get("/users/{user_id}", response_model=AdminUserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> AdminUserResponse:
    service = AdminService(db)
    try:
        user = service.get_user(user_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AdminUserResponse.model_validate(user)


@router.post(
    "/users",
    response_model=AdminUserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    payload: AdminUserCreateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> AdminUserResponse:
    service = AdminService(db)
    try:
        user = service.create_user(
            email=payload.email,
            password=payload.password,
            is_admin=payload.is_admin,
        )
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return AdminUserResponse.model_validate(user)


@router.put("/users/{user_id}", response_model=AdminUserResponse)
def update_user(
    user_id: int,
    payload: AdminUserUpdateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> AdminUserResponse:
    service = AdminService(db)
    try:
        user = service.update_user(
            user_id=user_id,
            email=payload.email,
            password=payload.password,
            is_admin=payload.is_admin,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return AdminUserResponse.model_validate(user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> None:
    service = AdminService(db)
    try:
        service.delete_user(user_id=user_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/workspaces", response_model=list[AdminWorkspaceResponse])
def list_workspaces(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> list[AdminWorkspaceResponse]:
    return [
        AdminWorkspaceResponse.model_validate(workspace)
        for workspace in AdminService(db).list_workspaces()
    ]


@router.get("/workspaces/{workspace_id}", response_model=AdminWorkspaceResponse)
def get_workspace(
    workspace_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> AdminWorkspaceResponse:
    service = AdminService(db)
    try:
        workspace = service.get_workspace(workspace_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AdminWorkspaceResponse.model_validate(workspace)


@router.post(
    "/workspaces",
    response_model=AdminWorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_workspace(
    payload: AdminWorkspaceCreateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> AdminWorkspaceResponse:
    service = AdminService(db)
    try:
        workspace = service.create_workspace(
            user_id=payload.user_id,
            name=payload.name,
            company_name=payload.company_name,
            monthly_capacity_hours=payload.monthly_capacity_hours,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return AdminWorkspaceResponse.model_validate(workspace)


@router.put("/workspaces/{workspace_id}", response_model=AdminWorkspaceResponse)
def update_workspace(
    workspace_id: int,
    payload: AdminWorkspaceUpdateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> AdminWorkspaceResponse:
    service = AdminService(db)
    try:
        workspace = service.update_workspace(
            workspace_id=workspace_id,
            user_id=payload.user_id,
            name=payload.name,
            company_name=payload.company_name,
            monthly_capacity_hours=payload.monthly_capacity_hours,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return AdminWorkspaceResponse.model_validate(workspace)


@router.delete("/workspaces/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workspace(
    workspace_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> None:
    service = AdminService(db)
    try:
        service.delete_workspace(workspace_id=workspace_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/projects", response_model=list[AdminProjectResponse])
def list_projects(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> list[AdminProjectResponse]:
    return [
        AdminProjectResponse.model_validate(project)
        for project in AdminService(db).list_projects()
    ]


@router.get("/projects/{project_id}", response_model=AdminProjectResponse)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> AdminProjectResponse:
    service = AdminService(db)
    try:
        project = service.get_project(project_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AdminProjectResponse.model_validate(project)


@router.post(
    "/projects",
    response_model=AdminProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_project(
    payload: AdminProjectCreateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> AdminProjectResponse:
    service = AdminService(db)
    try:
        project = service.create_project(
            workspace_id=payload.workspace_id,
            title=payload.title,
            client_name=payload.client_name,
            description=payload.description,
            status=payload.status.value,
            priority=payload.priority.value,
            budget_cents=payload.budget_cents,
            hourly_rate_cents=payload.hourly_rate_cents,
            contract_type=payload.contract_type.value,
            billing_cycle=payload.billing_cycle.value,
            billing_status=payload.billing_status.value,
            payment_status=payload.payment_status.value,
            billing_currency=payload.billing_currency,
            agreed_amount=payload.agreed_amount,
            monthly_rate=payload.monthly_rate,
            monthly_amount=payload.monthly_amount,
            payment_due_day=payload.payment_due_day,
            next_payment_due_date=payload.next_payment_due_date,
            paid_at=payload.paid_at,
            billing_notes=payload.billing_notes,
            deadline=payload.deadline,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return AdminProjectResponse.model_validate(project)


@router.put("/projects/{project_id}", response_model=AdminProjectResponse)
def update_project(
    project_id: int,
    payload: AdminProjectUpdateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> AdminProjectResponse:
    service = AdminService(db)
    try:
        project = service.update_project(
            project_id=project_id,
            workspace_id=payload.workspace_id,
            title=payload.title,
            client_name=payload.client_name,
            description=payload.description,
            status=payload.status.value if payload.status is not None else None,
            priority=payload.priority.value if payload.priority is not None else None,
            budget_cents=payload.budget_cents,
            hourly_rate_cents=payload.hourly_rate_cents,
            contract_type=(
                payload.contract_type.value
                if payload.contract_type is not None
                else None
            ),
            billing_cycle=(
                payload.billing_cycle.value
                if payload.billing_cycle is not None
                else None
            ),
            billing_status=(
                payload.billing_status.value
                if payload.billing_status is not None
                else None
            ),
            payment_status=(
                payload.payment_status.value
                if payload.payment_status is not None
                and "payment_status" in payload.model_fields_set
                else None
            ),
            billing_currency=payload.billing_currency,
            agreed_amount=payload.agreed_amount,
            agreed_amount_provided="agreed_amount" in payload.model_fields_set,
            monthly_rate=payload.monthly_rate,
            monthly_rate_provided="monthly_rate" in payload.model_fields_set,
            monthly_amount=payload.monthly_amount,
            monthly_amount_provided="monthly_amount" in payload.model_fields_set,
            payment_due_day=payload.payment_due_day,
            payment_due_day_provided="payment_due_day" in payload.model_fields_set,
            next_payment_due_date=payload.next_payment_due_date,
            next_payment_due_date_provided=(
                "next_payment_due_date" in payload.model_fields_set
            ),
            paid_at=payload.paid_at,
            paid_at_provided="paid_at" in payload.model_fields_set,
            billing_notes=payload.billing_notes,
            billing_notes_provided="billing_notes" in payload.model_fields_set,
            deadline=payload.deadline,
            archived=payload.archived,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return AdminProjectResponse.model_validate(project)


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> None:
    service = AdminService(db)
    try:
        service.delete_project(project_id=project_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/tasks", response_model=list[AdminTaskResponse])
def list_tasks(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> list[AdminTaskResponse]:
    return [
        AdminTaskResponse.model_validate(task) for task in AdminService(db).list_tasks()
    ]


@router.get("/tasks/{task_id}", response_model=AdminTaskResponse)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> AdminTaskResponse:
    service = AdminService(db)
    try:
        task = service.get_task(task_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AdminTaskResponse.model_validate(task)


@router.post(
    "/tasks",
    response_model=AdminTaskResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_task(
    payload: AdminTaskCreateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> AdminTaskResponse:
    service = AdminService(db)
    try:
        task = service.create_task(
            project_id=payload.project_id,
            title=payload.title,
            description=payload.description,
            status=payload.status.value,
            priority=payload.priority.value,
            estimated_minutes=payload.estimated_minutes,
            actual_minutes=payload.actual_minutes,
            due_date=payload.due_date,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AdminTaskResponse.model_validate(task)


@router.put("/tasks/{task_id}", response_model=AdminTaskResponse)
def update_task(
    task_id: int,
    payload: AdminTaskUpdateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> AdminTaskResponse:
    service = AdminService(db)
    try:
        task = service.update_task(
            task_id=task_id,
            project_id=payload.project_id,
            title=payload.title,
            description=payload.description,
            status=payload.status.value if payload.status is not None else None,
            priority=payload.priority.value if payload.priority is not None else None,
            estimated_minutes=payload.estimated_minutes,
            actual_minutes=payload.actual_minutes,
            due_date=payload.due_date,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AdminTaskResponse.model_validate(task)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> None:
    service = AdminService(db)
    try:
        service.delete_task(task_id=task_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
