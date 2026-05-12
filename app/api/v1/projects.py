from __future__ import annotations

from datetime import date
from math import ceil
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.serializers import to_project_response
from app.core.database import get_db
from app.core.exceptions import (
    BusinessRuleError,
    NotFoundError,
    ValidationError,
)
from app.domain.enums import Priority, ProjectStatus
from app.models.user import User
from app.schemas.payment_record import (
    PaymentRecordCreateRequest,
    PaymentRecordResponse,
    PaymentRecordUpdateRequest,
)
from app.schemas.project import (
    ProjectActionResponse,
    ProjectCreateRequest,
    ProjectListResponse,
    ProjectQueryParams,
    ProjectResponse,
    ProjectUpdateRequest,
    TaskCompleteRequest,
    TaskCreateRequest,
    TaskResponse,
    TaskUpdateRequest,
)
from app.services.payment_record_service import PaymentRecordService
from app.services.project_service import ProjectService
from app.services.task_service import TaskService

router = APIRouter(tags=["projects"])


@router.get("/projects", response_model=ProjectListResponse)
def list_projects(
    status_filter: ProjectStatus | None = Query(default=None, alias="status"),
    priority: Priority | None = Query(default=None),
    client_name: str | None = Query(default=None),
    search: str | None = Query(default=None),
    due_before: date | None = Query(default=None),
    due_after: date | None = Query(default=None),
    overdue_only: bool = Query(default=False),
    include_archived: bool = Query(default=False),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort_by: Literal[
        "id",
        "title",
        "client_name",
        "status",
        "priority",
        "contract_type",
        "deadline",
        "created_at",
        "updated_at",
    ] = Query(default="priority"),
    sort_dir: Literal["asc", "desc"] = Query(default="asc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectListResponse:
    try:
        params = ProjectQueryParams(
            status=status_filter,
            priority=priority,
            client_name=client_name,
            search=search,
            due_before=due_before,
            due_after=due_after,
            overdue_only=overdue_only,
            include_archived=include_archived,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )
    except PydanticValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc

    service = ProjectService(db)
    project_page = service.paginate_projects_for_user(
        user=current_user,
        status=params.status.value if params.status is not None else None,
        priority=params.priority.value if params.priority is not None else None,
        client_name=params.client_name,
        search=params.search,
        due_before=params.due_before,
        due_after=params.due_after,
        overdue_only=params.overdue_only,
        include_archived=params.include_archived,
        page=params.page,
        page_size=params.page_size,
        sort_by=params.sort_by,
        sort_dir=params.sort_dir,
    )
    return ProjectListResponse(
        items=[to_project_response(project) for project in project_page.items],
        total=project_page.total,
        page=params.page,
        page_size=params.page_size,
        total_pages=(
            ceil(project_page.total / params.page_size) if project_page.total > 0 else 0
        ),
    )


@router.post(
    "/projects",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_project(
    payload: ProjectCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectResponse:
    service = ProjectService(db)
    try:
        project = service.create_project(
            user=current_user,
            title=payload.title,
            client_name=payload.client_name,
            description=payload.description,
            status=payload.status.value,
            priority=payload.priority.value,
            contract_type=payload.contract_type.value,
            billing_currency=payload.billing_currency,
            hourly_rate_cents=payload.hourly_rate_cents,
            expected_hours_per_week=payload.expected_hours_per_week,
            monthly_rate_cents=payload.monthly_rate_cents,
            fixed_price_cents=payload.fixed_price_cents,
            start_date=payload.start_date,
            estimated_end_date=payload.estimated_end_date,
            billing_notes=payload.billing_notes,
            deadline=payload.deadline,
            payment_cadence=payload.payment_cadence.value,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return to_project_response(project)


@router.get("/projects/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectResponse:
    service = ProjectService(db)
    try:
        project = service.get_project_for_user(user=current_user, project_id=project_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return to_project_response(project)


@router.get(
    "/projects/{project_id}/payments",
    response_model=list[PaymentRecordResponse],
)
def list_project_payment_records(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[PaymentRecordResponse]:
    service = PaymentRecordService(db)
    try:
        payment_records = service.list_payment_records_for_project(
            user=current_user,
            project_id=project_id,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return [
        PaymentRecordResponse.model_validate(payment_record)
        for payment_record in payment_records
    ]


@router.post(
    "/projects/{project_id}/payments",
    response_model=PaymentRecordResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_project_payment_record(
    project_id: int,
    payload: PaymentRecordCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PaymentRecordResponse:
    service = PaymentRecordService(db)
    try:
        payment_record = service.create_payment_record(
            user=current_user,
            project_id=project_id,
            amount_cents=payload.amount_cents,
            currency=payload.currency,
            status=payload.status.value,
            method=payload.method.value if payload.method is not None else None,
            paid_at=payload.paid_at,
            due_date=payload.due_date,
            period_start=payload.period_start,
            period_end=payload.period_end,
            notes=payload.notes,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return PaymentRecordResponse.model_validate(payment_record)


@router.get(
    "/projects/{project_id}/payments/{payment_record_id}",
    response_model=PaymentRecordResponse,
)
def get_project_payment_record(
    project_id: int,
    payment_record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PaymentRecordResponse:
    service = PaymentRecordService(db)
    try:
        payment_record = service.get_payment_record_for_project(
            user=current_user,
            project_id=project_id,
            payment_record_id=payment_record_id,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return PaymentRecordResponse.model_validate(payment_record)


@router.put(
    "/projects/{project_id}/payments/{payment_record_id}",
    response_model=PaymentRecordResponse,
)
def update_project_payment_record(
    project_id: int,
    payment_record_id: int,
    payload: PaymentRecordUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PaymentRecordResponse:
    service = PaymentRecordService(db)
    try:
        payment_record = service.update_payment_record(
            user=current_user,
            project_id=project_id,
            payment_record_id=payment_record_id,
            amount_cents=payload.amount_cents,
            amount_cents_provided="amount_cents" in payload.model_fields_set,
            currency=payload.currency,
            status=payload.status.value if payload.status is not None else None,
            method=payload.method.value if payload.method is not None else None,
            method_provided="method" in payload.model_fields_set,
            paid_at=payload.paid_at,
            paid_at_provided="paid_at" in payload.model_fields_set,
            due_date=payload.due_date,
            due_date_provided="due_date" in payload.model_fields_set,
            period_start=payload.period_start,
            period_start_provided="period_start" in payload.model_fields_set,
            period_end=payload.period_end,
            period_end_provided="period_end" in payload.model_fields_set,
            notes=payload.notes,
            notes_provided="notes" in payload.model_fields_set,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return PaymentRecordResponse.model_validate(payment_record)


@router.delete(
    "/projects/{project_id}/payments/{payment_record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_project_payment_record(
    project_id: int,
    payment_record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    service = PaymentRecordService(db)
    try:
        service.delete_payment_record(
            user=current_user,
            project_id=project_id,
            payment_record_id=payment_record_id,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/projects/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    payload: ProjectUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectResponse:
    service = ProjectService(db)
    try:
        project = service.update_project(
            user=current_user,
            project_id=project_id,
            title=payload.title,
            client_name=payload.client_name,
            description=payload.description,
            status=payload.status.value if payload.status is not None else None,
            priority=payload.priority.value if payload.priority is not None else None,
            hourly_rate_cents=payload.hourly_rate_cents,
            contract_type=(
                payload.contract_type.value
                if payload.contract_type is not None
                else None
            ),
            billing_currency=payload.billing_currency,
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
            archived=payload.archived,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except BusinessRuleError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return to_project_response(project)


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    service = ProjectService(db)
    try:
        service.delete_project(user=current_user, project_id=project_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "/projects/{project_id}/complete",
    response_model=ProjectActionResponse,
)
def complete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectActionResponse:
    service = ProjectService(db)
    try:
        project = service.complete_project(user=current_user, project_id=project_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except BusinessRuleError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return ProjectActionResponse(
        message="Project completed successfully.",
        project=to_project_response(project),
    )


@router.post(
    "/projects/{project_id}/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_task(
    project_id: int,
    payload: TaskCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskResponse:
    service = TaskService(db)
    try:
        task = service.create_task(
            user=current_user,
            project_id=project_id,
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
    return TaskResponse.model_validate(task)


@router.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    payload: TaskUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskResponse:
    service = TaskService(db)
    try:
        task = service.update_task(
            user=current_user,
            task_id=task_id,
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
    return TaskResponse.model_validate(task)


@router.post("/tasks/{task_id}/complete", response_model=TaskResponse)
def complete_task(
    task_id: int,
    payload: TaskCompleteRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskResponse:
    service = TaskService(db)
    try:
        task = service.complete_task(
            user=current_user,
            task_id=task_id,
            actual_minutes=payload.actual_minutes if payload is not None else None,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (BusinessRuleError, ValidationError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return TaskResponse.model_validate(task)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    service = TaskService(db)
    try:
        service.delete_task(user=current_user, task_id=task_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
