from fastapi import APIRouter

# Create a router for all endpoints
router = APIRouter()

# Import and include all endpoint routers here
from . import leads

# Include the leads router (prefix is already defined in leads.py)
router.include_router(leads.router)
