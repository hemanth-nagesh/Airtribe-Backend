from sqlalchemy.orm import Session

from app.models.plan import Plan


class PlanRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, plan: Plan) -> Plan:
        self.db.add(plan)
        self.db.flush()
        return plan

    def get_by_id(self, plan_id: int) -> Plan | None:
        return self.db.query(Plan).filter(Plan.id == plan_id).first()

    def get_all(self, include_inactive: bool = False) -> list[Plan]:
        query = self.db.query(Plan)
        if not include_inactive:
            query = query.filter(Plan.is_active.is_(True))
        return query.all()

    def update(self, plan: Plan) -> Plan:
        self.db.flush()
        return plan
