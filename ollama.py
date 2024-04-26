from openai import OpenAI
import requests
from typing import List
import json

class LLMAssistant:
    def __init__(self, system_prompt: str | None = None):
        self.sprig_docs = self.load_sprig_docs()
        self.model_version = "gpt-3.5-turbo"
        self.chat_messages = [
            {
                "role": "system",
                "content": system_prompt
                if system_prompt is not None
                else "You are an expert programmer that helps to write Python code based on the user request, with concise explanations. Don't be too verbose.",
            },
            {
                "role": "user",
                "content": "Here is the sprig documentation" + "\n\n" + self.sprig_docs,
            },
        ]

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

    def chat_completion(self, messages: List):
        completion = self.get_completion(messages)

        if "gpt" in self.model_version:
            # print("completion", completion)
            completion = completion.choices.pop().message.content

        return completion


class ChatGPTAssistant(LLMAssistant):
    def __init__(self, openai_api_key: str, model: str = "gpt-3.5-turbo"):
        super().__init__()
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
        model: str = "llama2",
        ctx_window: int = 4096,
        OLLAMA_SERVE_URL: str = "http://127.0.0.1:11434",
    ):
        super().__init__()
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
