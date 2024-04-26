from fastapi import FastAPI
from fastapi.requests import Request
from ollama import OllamaAssitantModel, ChatGPTAssistant
from dotenv import load_dotenv
import os

load_dotenv()

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

app = FastAPI()

# TODO: setup CORS here

@app.get("/")
def _hello_world():
    return "Hello World"

@app.post("/generate")
async def _generate_response(req: Request):
    body = await req.json()
    if body.get("model") == "chatgpt":
        model = ChatGPTAssistant(OPENAI_API_KEY)
    else:
        model = OllamaAssitantModel(
            model=body.get("model"),
        )

    response = {}

    prompt_response = model.chat_completion(body.get("prompt"))
    code_blocks = model.get_code_blocks(prompt_response)

    response["raw"] = prompt_response
    response["codes"] = code_blocks

    return response