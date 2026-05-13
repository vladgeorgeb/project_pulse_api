from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.core.database import get_db
from app.core.exceptions import (
    BusinessRuleError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.core.observability import log_business_event
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
from app.schemas.feedback import AdminFeedbackResponse
from app.services.admin_service import AdminService
from app.services.feedback_service import FeedbackService

router = APIRouter(prefix="/admin")


def log_admin_internal_endpoint_used(
    request: Request,
    current_admin: User = Depends(get_current_admin),
) -> User:
    log_business_event(
        "admin_internal_endpoint_used",
        request=request,
        user_id=current_admin.id,
        method=request.method,
        path=request.url.path,
    )
    return current_admin


@router.get(
    "/feedback",
    response_model=list[AdminFeedbackResponse],
    tags=["admin-feedback"],
    summary="List feedback submissions (public admin v1 surface)",
)
def list_feedback(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> list[AdminFeedbackResponse]:
    return [
        AdminFeedbackResponse.model_validate(feedback)
        for feedback in FeedbackService(db).list_feedback()
    ]


@router.get(
    "/users",
    response_model=list[AdminUserResponse],
    tags=["admin-internal"],
    summary="List users (operator/internal)",
)
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(log_admin_internal_endpoint_used),
) -> list[AdminUserResponse]:
    return [
        AdminUserResponse.model_validate(user) for user in AdminService(db).list_users()
    ]


@router.get(
    "/users/{user_id}",
    response_model=AdminUserResponse,
    tags=["admin-internal"],
    summary="Get user by id (operator/internal)",
)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(log_admin_internal_endpoint_used),
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
    tags=["admin-internal"],
    summary="Create user (operator/internal)",
)
def create_user(
    payload: AdminUserCreateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(log_admin_internal_endpoint_used),
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


@router.put(
    "/users/{user_id}",
    response_model=AdminUserResponse,
    tags=["admin-internal"],
    summary="Update user (operator/internal)",
)
def update_user(
    user_id: int,
    payload: AdminUserUpdateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(log_admin_internal_endpoint_used),
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


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["admin-internal"],
    summary="Delete user (operator/internal)",
)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(log_admin_internal_endpoint_used),
) -> None:
    service = AdminService(db)
    try:
        service.delete_user(user_id=user_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get(
    "/workspaces",
    response_model=list[AdminWorkspaceResponse],
    tags=["admin-internal"],
    summary="List workspaces (operator/internal)",
)
def list_workspaces(
    db: Session = Depends(get_db),
    _: User = Depends(log_admin_internal_endpoint_used),
) -> list[AdminWorkspaceResponse]:
    return [
        AdminWorkspaceResponse.model_validate(workspace)
        for workspace in AdminService(db).list_workspaces()
    ]


@router.get(
    "/workspaces/{workspace_id}",
    response_model=AdminWorkspaceResponse,
    tags=["admin-internal"],
    summary="Get workspace by id (operator/internal)",
)
def get_workspace(
    workspace_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(log_admin_internal_endpoint_used),
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
    tags=["admin-internal"],
    summary="Create workspace (operator/internal)",
)
def create_workspace(
    payload: AdminWorkspaceCreateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(log_admin_internal_endpoint_used),
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


@router.put(
    "/workspaces/{workspace_id}",
    response_model=AdminWorkspaceResponse,
    tags=["admin-internal"],
    summary="Update workspace (operator/internal)",
)
def update_workspace(
    workspace_id: int,
    payload: AdminWorkspaceUpdateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(log_admin_internal_endpoint_used),
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


@router.delete(
    "/workspaces/{workspace_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["admin-internal"],
    summary="Delete workspace (operator/internal)",
)
def delete_workspace(
    workspace_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(log_admin_internal_endpoint_used),
) -> None:
    service = AdminService(db)
    try:
        service.delete_workspace(workspace_id=workspace_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get(
    "/projects",
    response_model=list[AdminProjectResponse],
    tags=["admin-internal"],
    summary="List projects (operator/internal)",
)
def list_projects(
    db: Session = Depends(get_db),
    _: User = Depends(log_admin_internal_endpoint_used),
) -> list[AdminProjectResponse]:
    return [
        AdminProjectResponse.model_validate(project)
        for project in AdminService(db).list_projects()
    ]


@router.get(
    "/projects/{project_id}",
    response_model=AdminProjectResponse,
    tags=["admin-internal"],
    summary="Get project by id (operator/internal)",
)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(log_admin_internal_endpoint_used),
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
    tags=["admin-internal"],
    summary="Create project (operator/internal)",
)
def create_project(
    payload: AdminProjectCreateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(log_admin_internal_endpoint_used),
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
            hourly_rate_cents=payload.hourly_rate_cents,
            expected_hours_per_week=payload.expected_hours_per_week,
            monthly_rate_cents=payload.monthly_rate_cents,
            fixed_price_cents=payload.fixed_price_cents,
            contract_type=payload.contract_type.value,
            billing_currency=payload.billing_currency,
            start_date=payload.start_date,
            estimated_end_date=payload.estimated_end_date,
            payment_cadence=payload.payment_cadence.value,
            billing_notes=payload.billing_notes,
            deadline=payload.deadline,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except BusinessRuleError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return AdminProjectResponse.model_validate(project)


@router.put(
    "/projects/{project_id}",
    response_model=AdminProjectResponse,
    tags=["admin-internal"],
    summary="Update project (operator/internal)",
)
def update_project(
    project_id: int,
    payload: AdminProjectUpdateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(log_admin_internal_endpoint_used),
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
            hourly_rate_cents=payload.hourly_rate_cents,
            expected_hours_per_week=payload.expected_hours_per_week,
            expected_hours_per_week_provided=(
                "expected_hours_per_week" in payload.model_fields_set
            ),
            monthly_rate_cents=payload.monthly_rate_cents,
            monthly_rate_cents_provided=(
                "monthly_rate_cents" in payload.model_fields_set
            ),
            fixed_price_cents=payload.fixed_price_cents,
            fixed_price_cents_provided=(
                "fixed_price_cents" in payload.model_fields_set
            ),
            contract_type=(
                payload.contract_type.value
                if payload.contract_type is not None
                else None
            ),
            billing_currency=payload.billing_currency,
            start_date=payload.start_date,
            start_date_provided=("start_date" in payload.model_fields_set),
            estimated_end_date=payload.estimated_end_date,
            estimated_end_date_provided=(
                "estimated_end_date" in payload.model_fields_set
            ),
            payment_cadence=(
                payload.payment_cadence.value
                if payload.payment_cadence is not None
                else None
            ),
            billing_notes=payload.billing_notes,
            billing_notes_provided="billing_notes" in payload.model_fields_set,
            deadline=payload.deadline,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except BusinessRuleError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return AdminProjectResponse.model_validate(project)


@router.delete(
    "/projects/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["admin-internal"],
    summary="Delete project (operator/internal)",
)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(log_admin_internal_endpoint_used),
) -> None:
    service = AdminService(db)
    try:
        service.delete_project(project_id=project_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get(
    "/tasks",
    response_model=list[AdminTaskResponse],
    tags=["admin-internal"],
    summary="List tasks (operator/internal)",
)
def list_tasks(
    db: Session = Depends(get_db),
    _: User = Depends(log_admin_internal_endpoint_used),
) -> list[AdminTaskResponse]:
    return [
        AdminTaskResponse.model_validate(task) for task in AdminService(db).list_tasks()
    ]


@router.get(
    "/tasks/{task_id}",
    response_model=AdminTaskResponse,
    tags=["admin-internal"],
    summary="Get task by id (operator/internal)",
)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(log_admin_internal_endpoint_used),
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
    tags=["admin-internal"],
    summary="Create task (operator/internal)",
)
def create_task(
    payload: AdminTaskCreateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(log_admin_internal_endpoint_used),
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


@router.put(
    "/tasks/{task_id}",
    response_model=AdminTaskResponse,
    tags=["admin-internal"],
    summary="Update task (operator/internal)",
)
def update_task(
    task_id: int,
    payload: AdminTaskUpdateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(log_admin_internal_endpoint_used),
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
    except (BusinessRuleError, ValidationError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return AdminTaskResponse.model_validate(task)


@router.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["admin-internal"],
    summary="Delete task (operator/internal)",
)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(log_admin_internal_endpoint_used),
) -> None:
    service = AdminService(db)
    try:
        service.delete_task(task_id=task_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
