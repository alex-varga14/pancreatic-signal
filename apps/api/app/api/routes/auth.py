from fastapi import APIRouter, Depends

from app.auth import get_current_actor
from app.schemas.auth import AuthenticatedActor

router = APIRouter()


@router.get("/me", response_model=AuthenticatedActor)
def get_auth_me(actor: AuthenticatedActor = Depends(get_current_actor)) -> AuthenticatedActor:
    return actor
