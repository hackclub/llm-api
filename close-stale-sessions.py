import requests
import os
from dotenv import load_dotenv


# load environment variables
load_dotenv()

SERVICE_URL = os.getenv["LLM_SERVICE_URL"]

# fire and forget
requests.get(f"{SERVICE_URL}/end-stale-sessions")