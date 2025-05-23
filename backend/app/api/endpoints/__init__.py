# Standard library imports
from typing import List

# Third-party imports
from fastapi import APIRouter

# Local application imports
from . import auth, leads

# Create a router for all endpoints
router = APIRouter()

# Include all endpoint routers
router.include_router(auth.router, tags=["auth"])
router.include_router(leads.router, tags=["leads"])

__all__: List[str] = ["router"]
