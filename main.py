from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.middleware.cors import CORSMiddleware
import redis
from ollama import OllamaAssitantModel, ChatGPTAssistant
from dotenv import load_dotenv
import os

load_dotenv()

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
REDIS_HOST = os.environ["REDIS_HOST"]
REDIS_PORT = os.environ["REDIS_PORT"]
REDIS_DB_NUMBER = os.environ["REDIS_DB_NUMBER"]

app = FastAPI()
redis_pool = redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB_NUMBER)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://sprig.hackclub.com",
        "http://localhost:3000",
        "https://sprig-git-sprig-ai.hackclub.dev",
        "https://sprig.hackclub.com",
        "*.hackclub.com",
        "*.hackclub.dev",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/")
def _hello_world():
    return "Hello World"

@app.post("/generate")
async def _generate_response(req: Request):
    body = await req.json()

    session_id = body.get("session_id")
    message = body.get("message")

    model = ChatGPTAssistant(session_id=session_id, redis_pool=redis_pool, openai_api_key=OPENAI_API_KEY)
    response = {}

    prompt_response = model.chat_completion(message)
    code_blocks = model.get_code_blocks(prompt_response)

    response["raw"] = prompt_response
    response["codes"] = code_blocks

    return response