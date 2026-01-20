from fastapi import FastAPI, Request, HTTPException, status
import asyncio
from ollama_mcp_kun_kosci.aikun import AIKun
from pydantic import BaseModel
from typing import Optional


class PromptRequest(BaseModel):
    prompt: str
    session: Optional[str] = None


app = FastAPI()
assistant = None
ollama_lock = asyncio.Lock()


async def init_server(ollama_url: str, ollama_model: str, mcps: dict):
    global assistant
    assistant = AIKun(ollama_url, ollama_model)
    await assistant.load_mcps(mcps)


@app.post("/chat")
async def chat(request: PromptRequest):
    if not assistant:
        raise HTTPException(status_code=500, detail="Assistant not initialized")
    async with ollama_lock:
        try:
            response = await assistant.query(request.prompt)
            return {"response": response['message']}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
