"""
Authenticated metrics routes for Prometheus scraping.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status

from ..auth import get_current_user, user_has_role
from ..metrics import metrics_endpoint
from ..models import User

router = APIRouter(tags=["monitoring"])


@router.get("/metrics")
async def get_metrics(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """
    Prometheus metrics endpoint (admin-only).
    """
    if not user_has_role(current_user, {"admin"}):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required for metrics access"
        )

    return await metrics_endpoint(request)
