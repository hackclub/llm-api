from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.middleware.cors import CORSMiddleware
from ollama import ChatGPTAssistant
from models import ChatSession
from dotenv import load_dotenv
from sqlmodel import create_engine, SQLModel
import os

load_dotenv()

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
PG_DATABASE_URL = os.environ["PG_DATABASE_URL"]

app = FastAPI()
pg_engine = create_engine(PG_DATABASE_URL)

# create all tables
SQLModel.metadata.create_all(pg_engine)

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

    ChatSession(id=session_id)
    model = ChatGPTAssistant(session_id=session_id, pg_engine=pg_engine, openai_api_key=OPENAI_API_KEY)
    response = {}

    prompt_response = model.chat_completion(message)
    code_blocks = model.get_code_blocks(prompt_response)

    response["raw"] = prompt_response
    response["codes"] = code_blocks

    return response