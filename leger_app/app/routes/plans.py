from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.repositories.plan_repo import PlanRepository
from app.schemas.plan import PlanCreate, PlanResponse, PlanUpdate
from app.services.plan_service import PlanService

router = APIRouter(tags=["Plans"])


def get_plan_service(db: Session = Depends(get_db)) -> PlanService:
    return PlanService(PlanRepository(db))


@router.post("/plans", response_model=PlanResponse, status_code=201)
def create_plan(data: PlanCreate, service: PlanService = Depends(get_plan_service)):
    return service.create_plan(data)


@router.get("/plans", response_model=list[PlanResponse])
def list_plans(
    include_inactive: bool = False,
    service: PlanService = Depends(get_plan_service),
):
    return service.list_plans(include_inactive=include_inactive)


@router.get("/plans/{plan_id}", response_model=PlanResponse)
def get_plan(plan_id: int, service: PlanService = Depends(get_plan_service)):
    plan = service.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


@router.patch("/plans/{plan_id}", response_model=PlanResponse)
def update_plan(
    plan_id: int,
    data: PlanUpdate,
    service: PlanService = Depends(get_plan_service),
):
    plan = service.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return service.update_plan(plan, data)
