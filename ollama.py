from openai import OpenAI
import requests
from typing import List
import json
import redis
import pickle

class LLMAssistant:
    def __init__(self, session_id: str, redis_pool: redis.ConnectionPool):
        self.sprig_docs = self.load_sprig_docs()
        self.model_version = "gpt-3.5-turbo"
        self.session_id = session_id
        self.redis_connection = redis.Redis(connection_pool=redis_pool)
        
        # create a new system prompt and messages iff the session passed does not exist yet
        # this to avoid overriding the messages in an existing session
        if (self.redis_connection.get(self.session_id) is None):
            # system prompt
            chat_messages = [
                {
                    "role": "system",
                    "content": "Here is the sprig documentation" + "\n\n" + self.sprig_docs + "\n\n With the help of the documentation, you have become an expert in JavaScript and understand Sprig. With the help of this documentation, answer prompts in a concise way.",
                },
            ]
            # add the initial message items to the sprig doc
            self.redis_connection.set("session_id", pickle.dumps(chat_messages))

    @staticmethod
    def build_code_prompt(self, code: str, error_logs: str = ""):
        prompt = (
            "Here is a piece of code: "
            + f"\n ```\n{code} \n```"
            + "\n it is showing me these errors"
            + f"\n```\n{error_logs} \n ```"
            + "\n identify the issue in the code and suggest a fix. write the full code with the issue fixed."
        )
        return prompt

    @staticmethod
    def load_sprig_docs() -> str:
        sprig_docs_url = (
            "https://raw.githubusercontent.com/hackclub/sprig/main/docs/docs.md"
        )
        return str(requests.get(sprig_docs_url).content)

    """
    The response returned by ChatGPT contains code wrapped in blocks by backticks
    with the language specified at the end of the opening three backticks
    ```js
    ```

    This function takes advantage of this information to split the completion text
    by three backticks.

    If we start counting from 1, the code within the backticks will always fall
    at even number indices.

    So, we can get only the text at those indices knowing that it's a block of code from the completion.

    We then slice away the text upto the first new line as they're usually the language specifier.

    """

    def get_code_blocks(self, source: str, delimiter: str = "```") -> List[str]:
        results = []
        for i, x in enumerate(source.split(delimiter)):
            if (i + 1) % 2 != 0:
                continue
            # remove the dangling language specifier
            first_newline = x.find("\n")
            results.append(x[first_newline + 1 :])
        return results

    # this method should be overriden in the implementation
    def get_completion(self, messages) -> str:
        return ""

    def chat_completion(self, message: str):
        messages_raw = self.redis_connection.get(self.session_id)
        messages = pickle.loads(messages_raw)

        completion = self.get_completion(messages + [{
            "role": "user",
            "content": message
        }])

        if "gpt" in self.model_version:
            completion = completion.choices.pop().message.content

        messages += [
            {
                "role": "user",
                "content": message
            },
            {
                "role": "assistant",
                "content": completion
            }
        ]

        self.redis_connection.set(self.session_id, pickle.dumps(messages))

        return completion


class ChatGPTAssistant(LLMAssistant):
    def __init__(self, session_id: str, redis_pool: redis.ConnectionPool, openai_api_key: str, model: str = "gpt-3.5-turbo"):
        super().__init__(session_id=session_id, redis_pool=redis_pool)
        self.openai_client = OpenAI(api_key=openai_api_key)
        self.model_version = model

    def get_completion(self, messages):
        # print("open ai client", self.openai_client)
        return self.openai_client.chat.completions.create(
            model=self.model_version, messages=messages
        )


class OllamaAssitantModel(LLMAssistant):
    def __init__(
        self,
        session_id: str, redis_pool: redis.ConnectionPool,
        model: str = "llama2",
        ctx_window: int = 4096,
        OLLAMA_SERVE_URL: str = "http://127.0.0.1:11434",
    ):
        super().__init__(session_id=session_id, redis_pool=redis_pool)
        self.generate_endpoint = f"{OLLAMA_SERVE_URL}/api/generate"
        self.chat_endpoint = f"{OLLAMA_SERVE_URL}/api/chat"
        self.model_version = model
        self.ctx_window = ctx_window

    def generate_response(self, prompt: str):
        body = {
            "model": self.model_version,
            "prompt": prompt,
            "options": {
                "num_ctx": self.ctx_window,
            },
        }
        # ollama will return to use a stream of set of responses from the model
        responses = requests.post(self.generate_endpoint, data=json.dumps(body)).content
        responses = responses.decode("utf-8")

        # here we transform the response into a single string for further processing
        response_bulk = [
            json.loads(response_str).get("response")
            for response_str in responses.splitlines()
        ]
        response_bulk = "".join(response_bulk)

        return response_bulk

    def get_completion(self, messages):
        body = {
            "model": self.model_version,
            "messages": messages,
            "options": {
                "num_ctx": self.ctx_window,
            },
        }
        responses = requests.post(self.chat_endpoint, data=json.dumps(body)).content
        responses = responses.decode("utf-8")

        # print(responses)
        response_bulk = [
            json.loads(response_str).get("message").get("content")
            for response_str in responses.splitlines()
        ]
        response_bulk = "".join(response_bulk)

        return response_bulk
