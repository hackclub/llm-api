from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.middleware.cors import CORSMiddleware
from ollama import ChatGPTAssistant, get_time_millis
from models import ChatSession
from dotenv import load_dotenv
from sqlmodel import create_engine, SQLModel, Session, select
from jose import jwt
import os

load_dotenv()

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
PG_DATABASE_URL = os.environ["PG_DATABASE_URL"]
SPRIG_LLMAPI_SALT = os.environ["SPRIG_LLMAPI_SALT"]

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

def create_token(email: str) -> str:
    return jwt.encode({
        "email": email,
        "iat": get_time_millis(),
    }, key=SPRIG_LLMAPI_SALT)

def decode_token(token: str) -> any:
    return jwt.decode(token, SPRIG_LLMAPI_SALT)

@app.get("/")
def _hello_world():
    return "Hello World"

@app.post("/generate")
async def _generate_response(req: Request):
    id_token = req.headers.get("Authorization")
    body = await req.json()

    user_email = decode_token(id_token).get("email")
    session_id = body.get("session_id")
    message = body.get("message")

    with Session(pg_engine) as session:
        chat_session = session.exec(select(ChatSession).where(ChatSession.id == session_id)).first()

    if chat_session is not None and chat_session.has_ended:
        return { "success": False, "msg": "Session has ended" }

    model = ChatGPTAssistant(user_email=user_email, session_id=session_id, pg_engine=pg_engine, openai_api_key=OPENAI_API_KEY)
    response = {}

    prompt_response = model.chat_completion(message)
    code_blocks = model.get_code_blocks(prompt_response)

    response["raw"] = prompt_response
    response["codes"] = code_blocks

    return response | { "success": True }

@app.post("/end-session")
async def _end_chat_session(req: Request):
    body = await req.json()

    session_id = body.get("session_id")
    with Session(pg_engine) as session:
        chat_session = session.exec(select(ChatSession).where(ChatSession.id == session_id)).first()
        chat_session.has_ended = True

        session.add(chat_session)
        session.commit()
    return { "success": True }