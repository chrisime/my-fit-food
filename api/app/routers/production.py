from fastapi import APIRouter, Depends

from app.core.deps import SessionUser, get_session
from app.schemas.stock import ProductionCreate, ProductionOut, StockMovementOut
from app.services.stock import create_production as service_create
from app.ws.manager import notify_clients

router = APIRouter(prefix="/production", tags=["production"])


@router.post("/", response_model=ProductionOut | StockMovementOut, status_code=201)
def create_production(body: ProductionCreate, s: SessionUser = Depends(get_session)):
    result = service_create(s.db, s.user.id, body)
    notify_clients("stock_updated", {"product_id": body.product_id})
    return result
