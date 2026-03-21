from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_actor, require_case_site_access
from app.schemas.auth import AuthenticatedActor
from app.schemas.trial import TrialMatchResponse
from app.services.trial_matching import match_case_to_trials
from app.store.memory_store import CASE_STORE

router = APIRouter()


@router.get("/match/{case_id}", response_model=TrialMatchResponse)
def match_trials(case_id: str, actor: AuthenticatedActor = Depends(get_current_actor)) -> TrialMatchResponse:
    case = CASE_STORE.get_case(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    require_case_site_access(actor, case.site)
    result = match_case_to_trials(case_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return result
