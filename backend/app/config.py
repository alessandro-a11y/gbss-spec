import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./watchers.db")
API_KEY = os.getenv("API_KEY", "troque-isso")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")