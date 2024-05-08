from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.middleware.cors import CORSMiddleware
from ollama import ChatGPTAssistant
from models import ChatSession
from dotenv import load_dotenv
from sqlmodel import create_engine, SQLModel, Session, select
import statsd
import os
import time

load_dotenv()

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
PG_DATABASE_URL = os.environ["PG_DATABASE_URL"]
GRAPHITE_HOST = os.environ["GRAPHITE_HOST"]
GRAPHITE_HOST_PORT = os.environ["GRAPHITE_HOST_PORT"]

app = FastAPI()
pg_engine = create_engine(PG_DATABASE_URL)
metrics = statsd.StatsClient(host=GRAPHITE_HOST, port=GRAPHITE_HOST_PORT, prefix="production.llmapi")

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
    metrics.incr("generate")

    # time it starts handing a request
    start_time = time.time()
    body = await req.json()

    user_email = body.get("email")
    session_id = body.get("session_id")
    message = body.get("message")

    with Session(pg_engine) as session:
        chat_session = session.exec(select(ChatSession).where(ChatSession.id == session_id)).first()

    if chat_session is not None and chat_session.has_ended:
        return { "success": False, "msg": "Session has ended" }

    model = ChatGPTAssistant(metrics=metrics, user_email=user_email, session_id=session_id, pg_engine=pg_engine, openai_api_key=OPENAI_API_KEY)
    response = {}

    prompt_response = model.chat_completion(message)
    code_blocks = model.get_code_blocks(prompt_response)

    response["raw"] = prompt_response
    response["codes"] = code_blocks

    total_time = time.time() - start_time

    # log time it took to handle request
    metrics.timing("generate_response.timed", total_time)

    response_out = response | { "success": True }
    return response_out

@app.post("/end-session")
async def _end_chat_session(req: Request):
    body = await req.json()

    session_id = body.get("session_id")
    with Session(pg_engine) as session:
        chat_session = session.exec(select(ChatSession).where(ChatSession.id == session_id)).first()
        if chat_session is not None:
            chat_session.has_ended = True

            session.add(chat_session)
            session.commit()
    return { "success": True }
   
