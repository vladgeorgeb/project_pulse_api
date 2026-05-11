from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.project import ProjectResponse


class WorkspaceUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    company_name: str = Field(min_length=1, max_length=100)
    monthly_capacity_hours: int = Field(gt=0, le=744)


class WorkspaceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    company_name: str
    monthly_capacity_hours: int
    projects: list[ProjectResponse]
