from app.models.plan import Plan
from app.repositories.plan_repo import PlanRepository
from app.schemas.plan import PlanCreate, PlanUpdate


class PlanService:
    def __init__(self, plan_repo: PlanRepository):
        self.plan_repo = plan_repo

    def create_plan(self, data: PlanCreate) -> Plan:
        plan = Plan(
            name=data.name,
            description=data.description,
            price=data.price,
            currency=data.currency,
            billing_cycle=data.billing_cycle,
            is_active=data.is_active,
        )
        return self.plan_repo.create(plan)

    def get_plan(self, plan_id: int) -> Plan | None:
        return self.plan_repo.get_by_id(plan_id)

    def list_plans(self, include_inactive: bool = False) -> list[Plan]:
        return self.plan_repo.get_all(include_inactive=include_inactive)

    def update_plan(self, plan: Plan, data: PlanUpdate) -> Plan:
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(plan, field, value)
        return self.plan_repo.update(plan)
