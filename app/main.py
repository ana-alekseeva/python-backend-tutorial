from fastapi import FastAPI

from app.routers import auth, chat

app = FastAPI(title="Chatbot API", version="0.1.0")


@app.get("/health", tags=["ops"], summary="Liveness probe")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(chat.router)
