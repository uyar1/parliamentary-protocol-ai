from fastapi import FastAPI
from src.Api.api_lmdeploy import Router
import uvicorn

app = FastAPI()

# Router-Instanz erstellen und hinzufügen
api_router = Router()
app.include_router(api_router.router)

@app.get("/")
async def root():
    return {"message": "API läuft erfolgreich!"}


