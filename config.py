import os
from pathlib import Path
from dotenv import load_dotenv

# Get the project root directory
project_root = Path(__file__).parent

# Load .env file from project root
env_path = project_root / '.env'
load_dotenv(dotenv_path=env_path)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")

# Debug: print to verify (remove after testing)
print(f"GROQ_API_KEY loaded: {bool(GROQ_API_KEY)}")
print(f"MODEL_NAME: {MODEL_NAME}")