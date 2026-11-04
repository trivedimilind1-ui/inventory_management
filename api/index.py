import sys
import os
from pathlib import Path

# Add project root to Python module path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app import app

# WSGI handler for Vercel Serverless
handler = app
