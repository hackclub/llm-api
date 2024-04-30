from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.middleware.cors import CORSMiddleware
import redis
from ollama import OllamaAssitantModel, ChatGPTAssistant
from dotenv import load_dotenv
import os

load_dotenv()

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

app = FastAPI()
redis_pool = redis.ConectionPool(host="localhost", port=6060, db=0)

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
    model_version = body.get("model")

    message = body.get("message")

    messages = body.get("messages")

    # print(model_version)
    # print(messages)

    if body.get("model") == "chatgpt":
        model = ChatGPTAssistant(session_id=session_id, redis_pool=redis_pool, openai_api_key=OPENAI_API_KEY)
    else:
        model = OllamaAssitantModel(
            session_id=session_id,
            redis_pool=redis_pool,
            model=model_version,
        )

    response = {}

    prompt_response = model.chat_completion(messages)
    code_blocks = model.get_code_blocks(prompt_response)

    response["raw"] = prompt_response
    response["codes"] = code_blocks

    return response