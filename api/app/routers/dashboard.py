from fastapi import APIRouter, Depends

from app.core.deps import SessionUser, get_session
from app.services.dashboard import get_dashboard_data

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/")
def dashboard(s: SessionUser = Depends(get_session)):
    return get_dashboard_data(s.db)
