from prompt import CHAT_SYSTEM_PROMPT

class ChatSession:
    def __init__(self, llm, context: str = "", history: list = None):
        self.llm = llm
        self.context = context
        self.history = history or []

    def _build_messages(self):
        messages = [{"role": "system", "content": CHAT_SYSTEM_PROMPT}]
        if self.context:
            messages.append({"role": "user", "content": f"以下是论文相关内容：\n{self.context}"})
            messages.append({"role": "assistant", "content": "好的，我已了解这篇论文的内容，请问有什么问题？"})
        messages.extend(self.history)
        return messages

    def send(self, user_message: str, **kwargs) -> str:
        self.history.append({"role": "user", "content": user_message})
        reply = self.llm.chat(self._build_messages(), **kwargs)
        self.history.append({"role": "assistant", "content": reply})
        return reply

    def send_stream(self, user_message: str, **kwargs):
        self.history.append({"role": "user", "content": user_message})
        chunks = []
        for chunk in self.llm.chat_stream(self._build_messages(), **kwargs):
            chunks.append(chunk)
            yield chunk
        self.history.append({"role": "assistant", "content": "".join(chunks)})

    def clear(self):
        self.history.clear()
