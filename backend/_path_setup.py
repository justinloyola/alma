"""This module must be imported first to set up the Python path."""

import sys
from pathlib import Path

# Add the backend directory to the Python path at the very beginning
sys.path.insert(0, str(Path(__file__).parent))
