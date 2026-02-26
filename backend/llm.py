from openai import OpenAI
import os
from prompt import SYSTEM_PROMPT

from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())

class BaseLLM:
    def __init__(self, model: str, api_key: str = None, base_url: str = None):
        self.api_key = api_key if api_key else os.getenv("OPENAI_API_KEY")
        self.model = model
        self.client = OpenAI(api_key=self.api_key, base_url=base_url)
    
    def get_response(self, prompt: str, **kwargs) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=1.0,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
        **kwargs)
        return response.choices[0].message.content
    
    def get_response_stream(self, prompt: str, **kwargs):
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=1.0,
            stream=True,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
        **kwargs
        )
        for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                yield content
    
class SiliconflowLLM(BaseLLM):
    def __init__(self, api_key: str = None, base_url: str = None, model: str = "Pro/deepseek-ai/DeepSeek-V3.2"):
        self.api_key = api_key if api_key else os.getenv("SILICONFLOW_API_KEY")
        self.base_url = base_url if base_url else "https://api.siliconflow.cn/v1"
        self.model = model
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        

if __name__ == "__main__":
    llm = SiliconflowLLM()
    prompt = "请简要介绍一下Transformer模型。"
    response = llm.get_response(prompt)
    print("Response:", response)

    response_stream = llm.get_response_stream(prompt)
    print("Streamed Response:", end=" ")
    for chunk in response_stream:
        print(chunk, end="", flush=True)

