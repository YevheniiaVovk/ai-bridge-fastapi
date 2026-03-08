import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


from db import Base, engine, get_user_requests, add_request_data
from gemini_client import get_answer_from_gemini


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class ChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000)

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    logger.info("Database initialized.")
    yield

app = FastAPI(title="AI Bridge API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/requests")
def get_my_requests(request: Request):
    user_ip_address = request.client.host
    return get_user_requests(ip_address=user_ip_address)

@app.post("/requests")
async def send_prompt(chat_data: ChatRequest, request: Request):
    user_ip_address = request.client.host
    prompt = chat_data.prompt
    try:
        answer = get_answer_from_gemini(prompt)
        add_request_data(ip_address=user_ip_address, prompt=prompt, response=answer)
        return {"answer": answer}
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")