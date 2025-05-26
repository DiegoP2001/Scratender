from dotenv import load_dotenv
import os

def load_env_variables():
    environment = os.environ.get("ENVIRONMENT", None)
    load_dotenv()