# Standard library imports
from typing import List

# Third-party imports
from fastapi import APIRouter

# Local application imports
from . import leads

# Create a router for all endpoints
router = APIRouter()

# Include the leads router (prefix is already defined in leads.py)
router.include_router(leads.router)

__all__: List[str] = ["router"]
