import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'smartstock-supermarket-secret-key-2026-prod-jwt')
    
    # Database Configuration:
    # Priority:
    # 1. DATABASE_URL / MYSQL_URL (if provided, e.g. mysql+pymysql://user:pass@host/db or postgresql://)
    # 2. Vercel serverless environment -> /tmp/smartstock.db (ephemeral writeable directory)
    # 3. Local SQLite file in project directory -> smartstock.db
    
    _db_url = os.environ.get('DATABASE_URL') or os.environ.get('MYSQL_URL')
    
    if _db_url:
        # Fix postgres URI scheme if needed (postgres:// -> postgresql://)
        if _db_url.startswith("postgres://"):
            _db_url = _db_url.replace("postgres://", "postgresql://", 1)
        SQLALCHEMY_DATABASE_URI = _db_url
    elif os.environ.get('VERCEL') or os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
        SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/smartstock.db'
    else:
        # Check if MySQL environment credentials are provided
        mysql_user = os.environ.get('MYSQL_USER')
        mysql_password = os.environ.get('MYSQL_PASSWORD')
        mysql_host = os.environ.get('MYSQL_HOST', 'localhost')
        mysql_port = os.environ.get('MYSQL_PORT', '3306')
        mysql_db = os.environ.get('MYSQL_DATABASE', 'smartstock')
        
        if mysql_user and mysql_password:
            SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_db}"
        else:
            SQLALCHEMY_DATABASE_URI = f"sqlite:///{BASE_DIR / 'smartstock.db'}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 280,
        'pool_pre_ping': True,
    } if 'mysql' in SQLALCHEMY_DATABASE_URI else {}

    # Supermarket Store Information
    STORE_NAME = "SmartStock Supermarket"
    STORE_TAGLINE = "Fresh • Reliable • Everyday Value"
    STORE_ADDRESS = "Plot 42, Commercial Avenue, Sector 18, Gurugram, HR 122008"
    STORE_PHONE = "+91 98765 43210"
    STORE_EMAIL = "billing@smartstock.in"
    STORE_GSTIN = "07AAAAA0000A1Z5"
    STORE_CURRENCY = "₹"
    DEFAULT_TAX_RATE = 5.0  # 5% standard grocery GST
